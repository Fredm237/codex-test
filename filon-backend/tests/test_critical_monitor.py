"""Contrat de l'alerting critique minimal de production."""

from __future__ import annotations

import pytest

from observability.tools.critical_monitor import (
    CriticalMonitorError,
    _safe_base_url,
    evaluate_critical_state,
)


def _payloads() -> dict:
    return {
        "live": {"alive": True},
        "ready": {
            "ready": True,
            "database": {"status": "ok"},
            "schema": {"status": "ok", "revision": "head"},
        },
        "health": {
            "status": "ok",
            "dependencies": {
                "database": {"status": "ok"},
                "redis": {"status": "ok"},
            },
        },
        "pulse": {"live": True, "sync": {"status": "fresh"}},
        "metrics": {
            "overall": {"requests": 200, "status_groups": {"2xx": 199, "5xx": 1}}
        },
    }


def test_critical_monitor_accepts_a_safe_production_state() -> None:
    result = evaluate_critical_state(**_payloads())

    assert result.status == "ok"
    assert set(result.checks) == {
        "api_live",
        "postgres_ready",
        "schema_ready",
        "redis_ready",
        "catalog_fresh_or_syncing",
        "critical_5xx_rate_clear",
    }


@pytest.mark.parametrize(
    ("mutate", "reason"),
    [
        (lambda data: data["live"].update(alive=False), "api_down"),
        (
            lambda data: data["ready"].update(ready=False),
            "database_unhealthy",
        ),
        (
            lambda data: data["health"]["dependencies"]["redis"].update(
                status="error"
            ),
            "redis_unhealthy",
        ),
        (
            lambda data: data["pulse"]["sync"].update(status="stale"),
            "catalog_stale",
        ),
        (
            lambda data: data["metrics"].update(
                overall={"requests": 100, "status_groups": {"5xx": 5}}
            ),
            "critical_5xx_rate",
        ),
    ],
)
def test_critical_monitor_fails_closed_on_blockers(mutate, reason: str) -> None:
    payloads = _payloads()
    mutate(payloads)

    with pytest.raises(CriticalMonitorError, match=f"^{reason}$"):
        evaluate_critical_state(**payloads)


def test_critical_monitor_does_not_invent_an_error_rate_below_sample_floor() -> None:
    payloads = _payloads()
    payloads["metrics"] = {
        "overall": {"requests": 20, "status_groups": {"5xx": 20}}
    }

    assert evaluate_critical_state(**payloads).status == "ok"


@pytest.mark.parametrize(
    "url",
    [
        "http://filon.test",
        "https://user:password@filon.test",
        "https://filon.test/path",
        "https://filon.test?secret=value",
        "https://filon.test#fragment",
    ],
)
def test_critical_monitor_rejects_unsafe_base_urls(url: str) -> None:
    with pytest.raises(CriticalMonitorError, match="^invalid_base_url$"):
        _safe_base_url(url)


def test_critical_monitor_accepts_a_plain_https_origin() -> None:
    assert _safe_base_url("https://filon.test/") == "https://filon.test"
