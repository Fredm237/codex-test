from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest
import httpx
from jsonschema import Draft202012Validator

from observability.tools.verify_prometheus import (
    EXPECTED_RECORDS,
    MAX_RESPONSE_BYTES,
    PROMETHEUS_VERSION,
    PrometheusApiClient,
    PrometheusVerificationError,
    verify_activation,
)


NOW = datetime(2026, 8, 29, 12, 0, tzinfo=timezone.utc)
ROOT = Path(__file__).resolve().parents[1]
RECEIPT_SCHEMA = (
    ROOT
    / "observability"
    / "schemas"
    / "prometheus-activation-receipt.schema.json"
)


def _success(data: object) -> dict[str, object]:
    return {"status": "success", "data": data}


def _rules() -> dict[str, object]:
    return _success(
        {
            "groups": [
                {
                    "name": "filon-rollups-v1",
                    "rules": [
                        {
                            "type": "recording",
                            "name": name,
                            "health": "ok",
                            "lastError": "",
                        }
                        for name in sorted(EXPECTED_RECORDS)
                    ],
                }
            ]
        }
    )


def _target(replica: str) -> dict[str, object]:
    return {
        "labels": {
            "job": "filon-backend",
            "environment": "production",
            "cluster": "filon-eu",
            "replica": replica,
            "instance": f"{replica}.internal.example:443",
        },
        "health": "up",
        "lastError": "",
        "lastScrape": (NOW - timedelta(seconds=30)).isoformat(),
        "scrapeUrl": (
            f"https://{replica}.internal.example:443/health/metrics/openmetrics"
        ),
    }


class FakePrometheus:
    def __init__(self) -> None:
        self.build: dict[str, object] = _success({"version": PROMETHEUS_VERSION})
        self.rules: dict[str, object] = _rules()
        self.targets: dict[str, object] = _success(
            {"activeTargets": [_target("replica-a"), _target("replica-b")]}
        )
        self.missing_record: str | None = None
        self.calls: list[tuple[str, Mapping[str, str] | None]] = []

    def fetch(
        self,
        endpoint: str,
        params: Mapping[str, str] | None,
    ) -> dict[str, Any]:
        self.calls.append((endpoint, params))
        if endpoint == "/api/v1/status/buildinfo":
            return self.build  # type: ignore[return-value]
        if endpoint == "/api/v1/rules":
            return self.rules  # type: ignore[return-value]
        if endpoint == "/api/v1/targets":
            return self.targets  # type: ignore[return-value]
        assert endpoint == "/api/v1/query"
        query = str((params or {}).get("query"))
        if self.missing_record and self.missing_record in query:
            return _success({"resultType": "vector", "result": []})  # type: ignore[return-value]
        return _success(
            {
                "resultType": "vector",
                "result": [{"metric": {}, "value": [NOW.timestamp(), "1"]}],
            }
        )  # type: ignore[return-value]


def test_activation_receipt_schema_is_closed_and_matches_rule_roster():
    schema = json.loads(RECEIPT_SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)

    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["additionalProperties"] is False
    assert schema["properties"]["schema_version"]["const"] == 1
    assert schema["properties"]["status"]["const"] == "verified"
    roster = schema["$defs"]["ruleRoster"]
    assert roster["minItems"] == len(EXPECTED_RECORDS)
    assert roster["maxItems"] == len(EXPECTED_RECORDS)
    assert roster["uniqueItems"] is True
    assert set(roster["items"]["enum"]) == EXPECTED_RECORDS


def test_verifies_version_rules_recent_unique_scrapes_and_all_series():
    prometheus = FakePrometheus()

    report = verify_activation(
        prometheus.fetch,
        environment="production",
        cluster="filon-eu",
        expected_replicas=2,
        now=NOW,
    )

    assert report == {
        "schema_version": 1,
        "status": "verified",
        "verified_at": "2026-08-29T12:00:00Z",
        "source": "prometheus-http-api",
        "prometheus_version": PROMETHEUS_VERSION,
        "environment": "production",
        "cluster": "filon-eu",
        "expected_replicas": 2,
        "healthy_replicas": 2,
        "max_scrape_age_seconds": 120,
        "target_identity_fingerprint": report["target_identity_fingerprint"],
        "recording_rule_group": "filon-rollups-v1",
        "recording_rules": sorted(EXPECTED_RECORDS),
        "recording_series_present": sorted(EXPECTED_RECORDS),
    }
    assert str(report["target_identity_fingerprint"]).startswith("sha256:")
    assert "replica-a" not in json.dumps(report)
    assert len(prometheus.calls) == 3 + len(EXPECTED_RECORDS)
    schema = json.loads(RECEIPT_SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(report)


def test_rejects_wrong_version_before_claiming_activation():
    prometheus = FakePrometheus()
    prometheus.build = _success({"version": "3.13.1"})

    with pytest.raises(PrometheusVerificationError, match="version"):
        verify_activation(
            prometheus.fetch,
            environment="production",
            cluster="filon-eu",
            expected_replicas=2,
            now=NOW,
        )


def test_rejects_unhealthy_or_changed_rule_roster():
    prometheus = FakePrometheus()
    groups = prometheus.rules["data"]["groups"]  # type: ignore[index]
    groups[0]["rules"][0]["health"] = "err"  # type: ignore[index]

    with pytest.raises(PrometheusVerificationError, match="unhealthy"):
        verify_activation(
            prometheus.fetch,
            environment="production",
            cluster="filon-eu",
            expected_replicas=2,
            now=NOW,
        )


@pytest.mark.parametrize(
    "mutation",
    ["count", "health", "stale", "url", "identity", "duplicate"],
)
def test_rejects_incomplete_unhealthy_or_ambiguous_replica_proof(mutation: str):
    prometheus = FakePrometheus()
    targets = prometheus.targets["data"]["activeTargets"]  # type: ignore[index]
    if mutation == "count":
        targets.pop()
    elif mutation == "health":
        targets[0]["health"] = "down"
    elif mutation == "stale":
        targets[0]["lastScrape"] = (NOW - timedelta(minutes=10)).isoformat()
    elif mutation == "url":
        targets[0]["scrapeUrl"] = (
            "https://replica-a.internal.example:443/health/metrics/openmetrics?token=bad"
        )
    elif mutation == "identity":
        targets[0]["labels"]["instance"] = "other.internal.example:443"
    else:
        targets[1]["labels"]["replica"] = "replica-a"

    with pytest.raises(PrometheusVerificationError):
        verify_activation(
            prometheus.fetch,
            environment="production",
            cluster="filon-eu",
            expected_replicas=2,
            now=NOW,
        )


def test_rejects_a_rule_without_active_recorded_series():
    prometheus = FakePrometheus()
    prometheus.missing_record = sorted(EXPECTED_RECORDS)[0]

    with pytest.raises(PrometheusVerificationError, match="absent"):
        verify_activation(
            prometheus.fetch,
            environment="production",
            cluster="filon-eu",
            expected_replicas=2,
            now=NOW,
        )


@pytest.mark.parametrize(
    "url",
    [
        "http://prometheus.internal.example",
        "https://user:password@prometheus.internal.example",
        "https://prometheus.internal.example?token=bad",
    ],
)
def test_api_client_requires_secret_free_https_url(url: str):
    with pytest.raises(PrometheusVerificationError):
        PrometheusApiClient(url, "a" * 32)


def test_api_client_requires_a_strong_environment_token():
    with pytest.raises(PrometheusVerificationError):
        PrometheusApiClient("https://prometheus.internal.example", "short")


def test_api_client_sends_bearer_without_leaking_it_into_the_url():
    token = "s" * 32

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == f"Bearer {token}"
        assert request.headers["Accept"] == "application/json"
        assert request.url.scheme == "https"
        assert request.url.path == "/api/v1/query"
        assert request.url.params["query"] == "up"
        assert token not in str(request.url)
        return httpx.Response(200, json=_success({"result": []}))

    with PrometheusApiClient(
        "https://prometheus.internal.example",
        token,
        transport=httpx.MockTransport(handler),
    ) as client:
        assert client.get_json("/api/v1/query", {"query": "up"}) == _success(
            {"result": []}
        )


def test_api_client_refuses_redirect_without_forwarding_authorization():
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            307,
            headers={"Location": "https://untrusted.example/api/v1/targets"},
        )

    with PrometheusApiClient(
        "https://prometheus.internal.example",
        "s" * 32,
        transport=httpx.MockTransport(handler),
    ) as client:
        with pytest.raises(PrometheusVerificationError, match="rejected"):
            client.get_json("/api/v1/targets", None)

    assert calls == 1


def test_api_client_stops_reading_an_oversized_response():
    def handler(request: httpx.Request) -> httpx.Response:
        del request
        return httpx.Response(200, content=b"x" * (MAX_RESPONSE_BYTES + 1))

    with PrometheusApiClient(
        "https://prometheus.internal.example",
        "s" * 32,
        transport=httpx.MockTransport(handler),
    ) as client:
        with pytest.raises(PrometheusVerificationError, match="too large"):
            client.get_json("/api/v1/targets", None)
