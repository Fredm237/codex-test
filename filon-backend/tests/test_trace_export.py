from __future__ import annotations

import json

import pytest
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)

from app.core.config import Settings
from app.core.observability import (
    bind_request_id_context,
    outbound_trace_headers,
    request_id_context,
    traced_dependency,
    traced_pipeline_stage,
)
from app.core.tracing import configure_trace_export, shutdown_trace_export


def _settings() -> Settings:
    return Settings(
        _env_file=None,
        env="test",
        trace_export_backend="otlp_http",
        otlp_traces_endpoint="http://localhost:4318/v1/traces",
        otlp_trace_export_token="t" * 32,
        trace_export_sample_ratio=1.0,
    )


@pytest.fixture
def memory_exporter():
    exporter = InMemorySpanExporter(max_spans=20)
    assert configure_trace_export(
        _settings(),
        exporter=exporter,
        synchronous=True,
    )
    try:
        yield exporter
    finally:
        shutdown_trace_export()


@pytest.mark.asyncio
async def test_dependency_span_preserves_traceparent_without_sensitive_data(
    memory_exporter,
) -> None:
    token = bind_request_id_context("1" * 32)
    try:
        async with traced_dependency("postgres", "read"):
            traceparent = outbound_trace_headers()["traceparent"]
    finally:
        request_id_context.reset(token)

    spans = memory_exporter.get_finished_spans()
    assert len(spans) == 1
    span = spans[0]
    assert span.name == "filon.dependency.postgres.read"
    assert f"{span.context.trace_id:032x}" == "1" * 32
    assert f"{span.context.span_id:016x}" in traceparent
    assert dict(span.attributes or {}) == {
        "filon.dependency": "postgres",
        "filon.operation": "read",
        "filon.outcome": "ok",
        "filon.span.kind": "dependency",
    }
    assert span.events == ()


@pytest.mark.asyncio
async def test_pipeline_error_exports_no_exception_message_or_payload(
    memory_exporter,
) -> None:
    class SecretFailure(RuntimeError):
        pass

    @traced_pipeline_stage("decision")
    async def fail(secret_argument: str):
        raise SecretFailure(f"do-not-export-{secret_argument}")

    with pytest.raises(SecretFailure):
        await fail("customer-query")

    spans = memory_exporter.get_finished_spans()
    assert len(spans) == 1
    span = spans[0]
    serialized = json.dumps(
        {
            "name": span.name,
            "attributes": dict(span.attributes or {}),
            "events": [event.name for event in span.events],
            "status": span.status.status_code.name,
        },
        sort_keys=True,
    )
    assert "do-not-export" not in serialized
    assert "customer-query" not in serialized
    assert "SecretFailure" not in serialized
    assert span.status.status_code.name == "ERROR"
    assert dict(span.attributes or {})["filon.outcome"] == "error"


def test_trace_exporter_refuses_double_configuration(memory_exporter) -> None:
    with pytest.raises(RuntimeError, match="already configured"):
        configure_trace_export(
            _settings(),
            exporter=InMemorySpanExporter(),
            synchronous=True,
        )


@pytest.mark.asyncio
async def test_unsampled_trace_propagates_w3c_flag_without_export() -> None:
    settings = _settings()
    settings.trace_export_sample_ratio = 0.0000001
    exporter = InMemorySpanExporter()
    assert configure_trace_export(settings, exporter=exporter, synchronous=True)
    token = bind_request_id_context("f" * 32)
    try:
        async with traced_dependency("redis", "read"):
            traceparent = outbound_trace_headers()["traceparent"]
    finally:
        request_id_context.reset(token)
        shutdown_trace_export()

    assert traceparent.endswith("-00")
    assert exporter.get_finished_spans() == ()
