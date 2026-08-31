"""Vérifie une activation Prometheus et produit un reçu sans secret.

Le reçu ne contient ni URL, ni token, ni nom de réplica. Il prouve que la
version attendue répond, que chaque cible du cluster est récemment scrappée et
que les onze recording rules ont à la fois un état sain et une série active.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlsplit

import httpx

from observability.tools.target_inventory import (
    MAX_TARGET_GROUPS,
    TargetInventoryError,
    atomic_write,
    canonical_payload,
    inventory_fingerprint,
    normalize_inventory,
)


PROMETHEUS_VERSION = "3.13.2"
RULE_GROUP = "filon-rollups-v1"
EXPECTED_RECORDS = frozenset(
    {
        "filon:http_request_rate5m",
        "filon:http_5xx_ratio5m",
        "filon:recommendation_rate5m",
        "filon:recommendation_abstention_ratio5m",
        "filon:assistant_timeout_ratio5m",
        "filon:pipeline_execution_rate5m",
        "filon:pipeline_error_ratio5m",
        "filon:decision_rate5m",
        "filon:buy_card_rate5m",
        "filon:missing_dimension_rate5m",
        "filon:decision_exclusion_rate5m",
    }
)
MAX_RESPONSE_BYTES = 2 * 1024 * 1024

FetchJson = Callable[[str, Optional[Mapping[str, str]]], dict[str, Any]]


class PrometheusVerificationError(ValueError):
    """Échec de preuve dont le message ne reprend aucune valeur distante."""


def _closed_label(value: object, *, name: str) -> str:
    # Le compilateur reste l’autorité de la grammaire. Cette validation par
    # réutilisation évite qu’un sélecteur PromQL puisse être injecté.
    try:
        compiled = normalize_inventory(
            [
                {
                    "targets": ["proof.internal.example:443"],
                    "labels": {
                        "environment": value if name == "environment" else "proof",
                        "cluster": value if name == "cluster" else "proof",
                        "replica": "proof",
                    },
                }
            ],
            expected_replicas=1,
        )
    except TargetInventoryError as exc:
        raise PrometheusVerificationError(f"{name} label is invalid") from exc
    return str(compiled[0]["labels"][name])


def _positive_count(value: object) -> int:
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 1 <= value <= MAX_TARGET_GROUPS
    ):
        raise PrometheusVerificationError("expected replica count is invalid")
    return value


def _aware_time(value: object) -> datetime:
    if not isinstance(value, str):
        raise PrometheusVerificationError("target scrape timestamp is missing")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise PrometheusVerificationError("target scrape timestamp is invalid") from exc
    if parsed.utcoffset() is None:
        raise PrometheusVerificationError("target scrape timestamp has no timezone")
    return parsed.astimezone(timezone.utc)


def _api_data(payload: object, *, endpoint: str) -> Any:
    if not isinstance(payload, dict) or payload.get("status") != "success":
        raise PrometheusVerificationError(f"{endpoint} did not return success")
    if "data" not in payload:
        raise PrometheusVerificationError(f"{endpoint} response has no data")
    return payload["data"]


def _verify_build(fetch: FetchJson) -> str:
    data = _api_data(
        fetch("/api/v1/status/buildinfo", None),
        endpoint="build information",
    )
    if not isinstance(data, dict) or data.get("version") != PROMETHEUS_VERSION:
        raise PrometheusVerificationError("Prometheus version does not match the pack")
    return PROMETHEUS_VERSION


def _verify_rules(fetch: FetchJson) -> list[str]:
    data = _api_data(
        fetch("/api/v1/rules", {"type": "record"}),
        endpoint="recording rules",
    )
    groups = data.get("groups") if isinstance(data, dict) else None
    if not isinstance(groups, list):
        raise PrometheusVerificationError("recording rule groups are invalid")
    selected = [
        group
        for group in groups
        if isinstance(group, dict) and group.get("name") == RULE_GROUP
    ]
    if len(selected) != 1:
        raise PrometheusVerificationError("canonical recording rule group is not unique")
    rules = selected[0].get("rules")
    if not isinstance(rules, list):
        raise PrometheusVerificationError("canonical recording rules are invalid")
    names: set[str] = set()
    for rule in rules:
        if not isinstance(rule, dict):
            raise PrometheusVerificationError("canonical recording rule is invalid")
        name = rule.get("name")
        if (
            rule.get("type") != "recording"
            or rule.get("health") != "ok"
            or rule.get("lastError") not in (None, "")
            or not isinstance(name, str)
        ):
            raise PrometheusVerificationError("canonical recording rule is unhealthy")
        names.add(name)
    if names != EXPECTED_RECORDS or len(rules) != len(EXPECTED_RECORDS):
        raise PrometheusVerificationError("canonical recording rule roster differs")
    return sorted(names)


def _verify_scrapes(
    fetch: FetchJson,
    *,
    environment: str,
    cluster: str,
    expected_replicas: int,
    now: datetime,
    max_scrape_age_seconds: int,
) -> str:
    data = _api_data(
        fetch("/api/v1/targets", {"state": "active"}),
        endpoint="active targets",
    )
    targets = data.get("activeTargets") if isinstance(data, dict) else None
    if not isinstance(targets, list):
        raise PrometheusVerificationError("active target roster is invalid")
    matching: list[dict[str, Any]] = []
    for target in targets:
        if not isinstance(target, dict):
            continue
        labels = target.get("labels")
        if not isinstance(labels, dict):
            continue
        if (
            labels.get("job") == "filon-backend"
            and labels.get("environment") == environment
            and labels.get("cluster") == cluster
        ):
            matching.append(target)
    if len(matching) != expected_replicas:
        raise PrometheusVerificationError("active target count differs from platform count")

    identities: list[str] = []
    proof_groups: list[dict[str, Any]] = []
    replica_names: set[str] = set()
    instances: set[str] = set()
    for target in matching:
        labels = target["labels"]
        replica = labels.get("replica")
        instance = labels.get("instance")
        if (
            not isinstance(replica, str)
            or not replica
            or not isinstance(instance, str)
            or not instance
        ):
            raise PrometheusVerificationError("active target identity is incomplete")
        if replica in replica_names or instance in instances:
            raise PrometheusVerificationError("active target identity is duplicated")
        replica_names.add(replica)
        instances.add(instance)
        if target.get("health") != "up" or target.get("lastError") not in (None, ""):
            raise PrometheusVerificationError("an active target is not healthy")
        scraped_at = _aware_time(target.get("lastScrape"))
        age = (now - scraped_at).total_seconds()
        if age < -10 or age > max_scrape_age_seconds:
            raise PrometheusVerificationError("an active target scrape is not recent")
        scrape_url = target.get("scrapeUrl")
        if not isinstance(scrape_url, str):
            raise PrometheusVerificationError("active target scrape URL is missing")
        parsed = urlsplit(scrape_url)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path != "/health/metrics/openmetrics"
            or parsed.query
            or parsed.fragment
        ):
            raise PrometheusVerificationError("active target scrape transport is invalid")
        if parsed.netloc != instance:
            raise PrometheusVerificationError("active target identity differs from scrape URL")
        proof_groups.append(
            {
                "targets": [instance],
                "labels": {
                    "environment": environment,
                    "cluster": cluster,
                    "replica": replica,
                },
            }
        )
        identities.append(f"{environment}\0{cluster}\0{replica}\0{instance}")
    try:
        normalize_inventory(
            proof_groups,
            expected_replicas=expected_replicas,
        )
    except TargetInventoryError as exc:
        raise PrometheusVerificationError(
            "active target inventory differs from the closed contract"
        ) from exc
    digest = hashlib.sha256("\n".join(sorted(identities)).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _verify_recorded_series(
    fetch: FetchJson,
    *,
    environment: str,
    cluster: str,
) -> list[str]:
    present: list[str] = []
    for record in sorted(EXPECTED_RECORDS):
        query = f'count({record}{{environment="{environment}",cluster="{cluster}"}})'
        data = _api_data(
            fetch("/api/v1/query", {"query": query}),
            endpoint="recorded series query",
        )
        if not isinstance(data, dict) or data.get("resultType") != "vector":
            raise PrometheusVerificationError("recorded series query has invalid type")
        result = data.get("result")
        if not isinstance(result, list) or len(result) != 1:
            raise PrometheusVerificationError("a canonical recording series is absent")
        sample = result[0]
        value = sample.get("value") if isinstance(sample, dict) else None
        if not isinstance(value, list) or len(value) != 2:
            raise PrometheusVerificationError("a canonical recording sample is invalid")
        try:
            count = float(value[1])
        except (TypeError, ValueError) as exc:
            raise PrometheusVerificationError("a canonical recording sample is invalid") from exc
        if not math.isfinite(count) or count < 1:
            raise PrometheusVerificationError("a canonical recording series is empty")
        present.append(record)
    return present


def verify_activation(
    fetch: FetchJson,
    *,
    environment: str,
    cluster: str,
    expected_replicas: int,
    now: datetime | None = None,
    max_scrape_age_seconds: int = 120,
) -> dict[str, Any]:
    """Exécute les preuves distantes et retourne un reçu redacted."""

    environment = _closed_label(environment, name="environment")
    cluster = _closed_label(cluster, name="cluster")
    expected_replicas = _positive_count(expected_replicas)
    if (
        not isinstance(max_scrape_age_seconds, int)
        or isinstance(max_scrape_age_seconds, bool)
        or not 30 <= max_scrape_age_seconds <= 600
    ):
        raise PrometheusVerificationError("maximum scrape age is invalid")
    reference = now or datetime.now(timezone.utc)
    if reference.utcoffset() is None:
        raise PrometheusVerificationError("verification time has no timezone")
    reference = reference.astimezone(timezone.utc)

    version = _verify_build(fetch)
    rules = _verify_rules(fetch)
    identity_fingerprint = _verify_scrapes(
        fetch,
        environment=environment,
        cluster=cluster,
        expected_replicas=expected_replicas,
        now=reference,
        max_scrape_age_seconds=max_scrape_age_seconds,
    )
    series = _verify_recorded_series(
        fetch,
        environment=environment,
        cluster=cluster,
    )
    return {
        "schema_version": 1,
        "status": "verified",
        "verified_at": reference.isoformat().replace("+00:00", "Z"),
        "source": "prometheus-http-api",
        "prometheus_version": version,
        "environment": environment,
        "cluster": cluster,
        "expected_replicas": expected_replicas,
        "healthy_replicas": expected_replicas,
        "max_scrape_age_seconds": max_scrape_age_seconds,
        "target_identity_fingerprint": identity_fingerprint,
        "recording_rule_group": RULE_GROUP,
        "recording_rules": rules,
        "recording_series_present": series,
    }


class PrometheusApiClient:
    def __init__(
        self,
        base_url: str,
        token: str,
        *,
        timeout_seconds: float = 10.0,
        transport: httpx.BaseTransport | None = None,
    ):
        parsed = urlsplit(base_url)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
        ):
            raise PrometheusVerificationError("Prometheus base URL must be HTTPS")
        if (
            not isinstance(token, str)
            or token != token.strip()
            or not 32 <= len(token) <= 256
            or not token.isascii()
            or any(character.isspace() or not character.isprintable() for character in token)
        ):
            raise PrometheusVerificationError("Prometheus verification token is invalid")
        self._base_url = base_url.rstrip("/")
        self._client = httpx.Client(
            timeout=timeout_seconds,
            follow_redirects=False,
            trust_env=False,
            transport=transport,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "User-Agent": "filon-prometheus-verifier/1",
            },
        )

    def __enter__(self) -> "PrometheusApiClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    def get_json(
        self,
        endpoint: str,
        params: Mapping[str, str] | None,
    ) -> dict[str, Any]:
        try:
            with self._client.stream(
                "GET",
                f"{self._base_url}{endpoint}",
                params=params,
            ) as response:
                if response.status_code != 200:
                    raise PrometheusVerificationError(
                        "Prometheus API request was rejected"
                    )
                chunks: list[bytes] = []
                size = 0
                for chunk in response.iter_bytes():
                    size += len(chunk)
                    if size > MAX_RESPONSE_BYTES:
                        raise PrometheusVerificationError(
                            "Prometheus API response is too large"
                        )
                    chunks.append(chunk)
        except httpx.HTTPError as exc:
            raise PrometheusVerificationError("Prometheus API request failed") from exc
        try:
            payload = json.loads(b"".join(chunks))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise PrometheusVerificationError("Prometheus API response is not JSON") from exc
        if not isinstance(payload, dict):
            raise PrometheusVerificationError("Prometheus API response is invalid")
        return payload


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify FILON Prometheus activation and write a redacted receipt."
    )
    parser.add_argument("--url", required=True)
    parser.add_argument("--environment", required=True)
    parser.add_argument("--cluster", required=True)
    parser.add_argument("--expected-replicas", required=True, type=int)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--token-env", default="PROMETHEUS_VERIFY_TOKEN")
    parser.add_argument("--max-scrape-age-seconds", type=int, default=120)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    token = os.environ.get(args.token_env)
    try:
        with PrometheusApiClient(args.url, token or "") as client:
            report = verify_activation(
                client.get_json,
                environment=args.environment,
                cluster=args.cluster,
                expected_replicas=args.expected_replicas,
                max_scrape_age_seconds=args.max_scrape_age_seconds,
            )
        payload = canonical_payload(report)
        atomic_write(args.report, payload)
    except (PrometheusVerificationError, TargetInventoryError) as exc:
        print(f"Prometheus activation rejected: {exc}", file=sys.stderr)
        return 2
    print(
        "Prometheus activation verified: "
        f"replicas={report['healthy_replicas']} "
        f"rules={len(report['recording_rules'])} "
        f"receipt={inventory_fingerprint(payload)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
