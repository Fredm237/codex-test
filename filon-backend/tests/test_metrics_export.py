from __future__ import annotations

import math

import httpx
import pytest
from fastapi import FastAPI

from app.api.routes import health as health_module
from app.core.config import Settings
from app.core.metrics_export import (
    OPENMETRICS_CONTENT_TYPE,
    MetricsExportError,
    render_openmetrics,
)
from app.core.observability import product_intelligence_metrics, request_metrics


_TOKEN = "metrics-export-token-32-characters-minimum"


@pytest.fixture(autouse=True)
def reset_registries():
    request_metrics.reset()
    product_intelligence_metrics.reset()
    yield
    request_metrics.reset()
    product_intelligence_metrics.reset()


def _record_bounded_metrics() -> None:
    request_metrics.record(
        method="GET",
        route="/products/{product_id}",
        status_code=200,
        elapsed_ms=125,
    )
    product_intelligence_metrics.record_recommendation(
        {"real": False, "cards": []},
        delivery="generated",
    )
    product_intelligence_metrics.record_stage(
        stage="retrieval",
        outcome="degraded",
        elapsed_ms=250,
    )


def test_render_openmetrics_is_deterministic_bounded_and_parseable() -> None:
    _record_bounded_metrics()

    first = render_openmetrics(
        request_metrics.snapshot(),
        product_intelligence_metrics.snapshot(),
    )
    second = render_openmetrics(
        request_metrics.snapshot(),
        product_intelligence_metrics.snapshot(),
    )

    assert first == second
    assert first.endswith("# EOF\n")
    assert 'route="/products/{product_id}"' in first
    assert 'status_group="2xx"' in first
    assert 'stage="retrieval"' in first
    assert "filon_http_latency_seconds{statistic=\"p95\"} 0.125" in first
    assert "filon_pipeline_latency_seconds{stage=\"retrieval\",statistic=\"p95\"} 0.25" in first
    assert "product_id=" not in first
    assert "query=" not in first

    metadata = [
        line
        for line in first.splitlines()
        if line.startswith("# HELP ") or line.startswith("# TYPE ")
    ]
    assert len(metadata) == len(set(metadata))


def test_render_openmetrics_rejects_invalid_numbers_and_schema() -> None:
    _record_bounded_metrics()
    requests = request_metrics.snapshot()
    products = product_intelligence_metrics.snapshot()

    requests["uptime_seconds"] = math.nan
    with pytest.raises(MetricsExportError, match="invalid_number"):
        render_openmetrics(requests, products)

    requests = request_metrics.snapshot()
    products["schema_version"] = 2
    with pytest.raises(MetricsExportError, match="unsupported_product_metrics_schema"):
        render_openmetrics(requests, products)


@pytest.mark.asyncio
async def test_openmetrics_export_is_disabled_without_explicit_token(monkeypatch) -> None:
    monkeypatch.setattr(
        health_module,
        "get_settings",
        lambda: Settings(_env_file=None, env="test"),
    )

    response = await health_module.openmetrics()

    assert response.status_code == 503
    assert response.body == b'{"error":"metrics_export_disabled"}'
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.asyncio
async def test_openmetrics_export_requires_bearer_and_never_echoes_token(monkeypatch) -> None:
    monkeypatch.setattr(
        health_module,
        "get_settings",
        lambda: Settings(
            _env_file=None,
            env="test",
            metrics_export_token=_TOKEN,
        ),
    )

    missing = await health_module.openmetrics()
    wrong = await health_module.openmetrics("Bearer wrong-token")

    assert missing.status_code == wrong.status_code == 401
    assert missing.headers["www-authenticate"] == "Bearer"
    assert _TOKEN.encode() not in missing.body + wrong.body


@pytest.mark.asyncio
async def test_openmetrics_export_returns_the_standard_content_type(monkeypatch) -> None:
    _record_bounded_metrics()
    monkeypatch.setattr(
        health_module,
        "get_settings",
        lambda: Settings(
            _env_file=None,
            env="test",
            metrics_export_token=_TOKEN,
        ),
    )

    response = await health_module.openmetrics(f"Bearer {_TOKEN}")

    assert response.status_code == 200
    assert response.headers["content-type"] == OPENMETRICS_CONTENT_TYPE
    assert response.headers["cache-control"] == "no-store"
    assert response.body.endswith(b"# EOF\n")
    assert _TOKEN.encode() not in response.body


@pytest.mark.asyncio
async def test_openmetrics_fastapi_binding_reads_only_the_authorization_header(
    monkeypatch,
) -> None:
    _record_bounded_metrics()
    monkeypatch.setattr(
        health_module,
        "get_settings",
        lambda: Settings(
            _env_file=None,
            env="test",
            metrics_export_token=_TOKEN,
        ),
    )
    app = FastAPI()
    app.include_router(health_module.router)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        query_token = await client.get(
            f"/health/metrics/openmetrics?token={_TOKEN}"
        )
        authorized = await client.get(
            "/health/metrics/openmetrics",
            headers={"Authorization": f"Bearer {_TOKEN}"},
        )

    assert query_token.status_code == 401
    assert _TOKEN.encode() not in query_token.content
    assert authorized.status_code == 200
    assert authorized.headers["content-type"] == OPENMETRICS_CONTENT_TYPE
    assert "/health/metrics/openmetrics" not in app.openapi()["paths"]


@pytest.mark.asyncio
async def test_openmetrics_export_fails_closed_without_leaking_renderer_error(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        health_module,
        "get_settings",
        lambda: Settings(
            _env_file=None,
            env="test",
            metrics_export_token=_TOKEN,
        ),
    )

    def invalid_export(*_args):
        raise MetricsExportError("private-renderer-detail")

    monkeypatch.setattr(health_module, "render_openmetrics", invalid_export)

    response = await health_module.openmetrics(f"Bearer {_TOKEN}")

    assert response.status_code == 503
    assert response.body == b'{"error":"metrics_export_invalid"}'
    assert b"private-renderer-detail" not in response.body
