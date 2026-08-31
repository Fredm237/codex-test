"""Sonde externe minimale des blockers critiques de production FILON."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


MAX_RESPONSE_BYTES = 1024 * 1024
MIN_ERROR_RATE_SAMPLES = 100
CRITICAL_5XX_RATIO = 0.05


class CriticalMonitorError(RuntimeError):
    """Échec neutre : aucun corps de réponse n'est propagé dans les logs."""


@dataclass(frozen=True)
class CriticalMonitorResult:
    status: str
    checks: tuple[str, ...]


def _mapping(value: Any, *, code: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise CriticalMonitorError(code)
    return value


def _count(value: Any, *, code: str) -> int:
    if type(value) is not int or value < 0:
        raise CriticalMonitorError(code)
    return value


def evaluate_critical_state(
    *,
    live: Mapping[str, Any],
    ready: Mapping[str, Any],
    health: Mapping[str, Any],
    pulse: Mapping[str, Any],
    metrics: Mapping[str, Any],
) -> CriticalMonitorResult:
    """Évalue uniquement les conditions qui rendent Phase 1 dangereuse."""

    checks: list[str] = []
    if live.get("alive") is not True:
        raise CriticalMonitorError("api_down")
    checks.append("api_live")

    database = _mapping(ready.get("database"), code="database_probe_invalid")
    schema = _mapping(ready.get("schema"), code="schema_probe_invalid")
    if ready.get("ready") is not True or database.get("status") != "ok":
        raise CriticalMonitorError("database_unhealthy")
    if schema.get("status") != "ok":
        raise CriticalMonitorError("schema_not_ready")
    checks.extend(("postgres_ready", "schema_ready"))

    dependencies = _mapping(
        health.get("dependencies"),
        code="dependency_probe_invalid",
    )
    redis = _mapping(dependencies.get("redis"), code="redis_probe_invalid")
    if health.get("status") != "ok":
        raise CriticalMonitorError("service_degraded")
    if redis.get("status") != "ok":
        raise CriticalMonitorError("redis_unhealthy")
    checks.append("redis_ready")

    sync = _mapping(pulse.get("sync"), code="catalog_sync_probe_invalid")
    if pulse.get("live") is not True:
        raise CriticalMonitorError("catalog_readings_missing")
    if sync.get("status") not in {"fresh", "syncing"}:
        raise CriticalMonitorError("catalog_stale")
    checks.append("catalog_fresh_or_syncing")

    overall = _mapping(metrics.get("overall"), code="metrics_probe_invalid")
    status_groups = _mapping(
        overall.get("status_groups"),
        code="status_groups_invalid",
    )
    requests = _count(overall.get("requests"), code="request_count_invalid")
    server_errors = _count(status_groups.get("5xx", 0), code="error_count_invalid")
    if (
        requests >= MIN_ERROR_RATE_SAMPLES
        and server_errors / requests >= CRITICAL_5XX_RATIO
    ):
        raise CriticalMonitorError("critical_5xx_rate")
    checks.append("critical_5xx_rate_clear")

    return CriticalMonitorResult(status="ok", checks=tuple(checks))


def _safe_base_url(value: str) -> str:
    parsed = urlsplit(value)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
    ):
        raise CriticalMonitorError("invalid_base_url")
    return value.rstrip("/")


def _fetch_json(base_url: str, path: str, *, timeout: float) -> Mapping[str, Any]:
    request = Request(
        f"{base_url}{path}",
        headers={"Accept": "application/json", "User-Agent": "filon-critical-monitor/1"},
    )
    try:
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 - URL validée
            if response.status != 200:
                raise CriticalMonitorError("probe_http_error")
            payload = response.read(MAX_RESPONSE_BYTES + 1)
    except CriticalMonitorError:
        raise
    except Exception as exc:
        raise CriticalMonitorError("probe_unreachable") from exc
    if len(payload) > MAX_RESPONSE_BYTES:
        raise CriticalMonitorError("probe_response_too_large")
    try:
        decoded = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CriticalMonitorError("probe_json_invalid") from exc
    return _mapping(decoded, code="probe_payload_invalid")


def run(base_url: str, *, timeout: float = 10.0) -> CriticalMonitorResult:
    safe_base_url = _safe_base_url(base_url)
    payloads = {
        "live": _fetch_json(safe_base_url, "/health/live", timeout=timeout),
        "ready": _fetch_json(safe_base_url, "/health/ready", timeout=timeout),
        "health": _fetch_json(safe_base_url, "/health", timeout=timeout),
        "pulse": _fetch_json(safe_base_url, "/api/catalog/pulse", timeout=timeout),
        "metrics": _fetch_json(safe_base_url, "/health/metrics", timeout=timeout),
    }
    return evaluate_critical_state(**payloads)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args(argv)
    try:
        result = run(args.base_url, timeout=args.timeout)
    except CriticalMonitorError as exc:
        print(
            json.dumps(
                {"status": "critical", "reason_code": str(exc)},
                separators=(",", ":"),
                sort_keys=True,
            )
        )
        return 1
    print(
        json.dumps(
            {"status": result.status, "checks": list(result.checks)},
            separators=(",", ":"),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
