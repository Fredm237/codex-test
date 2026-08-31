from __future__ import annotations

import json
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from typing import Iterator

import pytest
from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import (
    ExportTraceServiceRequest,
)
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


@contextmanager
def _capturing_otlp_receiver() -> Iterator[dict[str, object]]:
    requests: list[dict[str, object]] = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802 - contrat HTTP stdlib
            length = int(self.headers.get("content-length", "0"))
            requests.append(
                {
                    "path": self.path,
                    "authorization": self.headers.get("authorization"),
                    "content_type": self.headers.get("content-type"),
                    "body": self.rfile.read(length),
                }
            )
            self.send_response(200)
            self.send_header("content-type", "application/x-protobuf")
            self.end_headers()

        def log_message(self, format: str, *args: object) -> None:
            del format, args

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield {
            "endpoint": f"http://127.0.0.1:{server.server_port}/v1/traces",
            "requests": requests,
        }
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


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


@pytest.mark.asyncio
async def test_real_otlp_http_transport_is_authenticated_and_payload_safe() -> None:
    export_token = "collector-token-transport-proof-0001"
    secret_payload = "customer-secret-do-not-export"

    with _capturing_otlp_receiver() as receiver:
        settings = _settings()
        settings.otlp_traces_endpoint = str(receiver["endpoint"])
        settings.otlp_trace_export_token = export_token
        assert configure_trace_export(settings, synchronous=True)

        class SecretFailure(RuntimeError):
            pass

        @traced_pipeline_stage("decision")
        async def fail(value: str) -> None:
            raise SecretFailure(value)

        token = bind_request_id_context("a" * 32)
        try:
            async with traced_dependency("serpapi", "search"):
                traceparent = outbound_trace_headers()["traceparent"]
            with pytest.raises(SecretFailure):
                await fail(secret_payload)
        finally:
            request_id_context.reset(token)
            shutdown_trace_export()

        captured = list(receiver["requests"])

    assert len(captured) == 2
    assert all(request["path"] == "/v1/traces" for request in captured)
    assert all(
        request["authorization"] == f"Bearer {export_token}"
        for request in captured
    )
    assert all(
        request["content_type"] == "application/x-protobuf"
        for request in captured
    )

    serialized_bodies = b"".join(request["body"] for request in captured)
    assert secret_payload.encode() not in serialized_bodies
    assert b"SecretFailure" not in serialized_bodies
    assert export_token.encode() not in serialized_bodies

    spans = []
    for captured_request in captured:
        export_request = ExportTraceServiceRequest()
        export_request.ParseFromString(captured_request["body"])
        assert len(export_request.resource_spans) == 1
        resource_span = export_request.resource_spans[0]
        resource_attributes = {
            attribute.key: attribute.value.string_value
            for attribute in resource_span.resource.attributes
        }
        assert resource_attributes == {
            "deployment.environment.name": "test",
            "service.name": "filon-backend",
            "service.version": "0.1.0",
        }
        spans.extend(resource_span.scope_spans[0].spans)

    assert [span.name for span in spans] == [
        "filon.dependency.serpapi.search",
        "filon.pipeline.decision",
    ]
    assert all(span.trace_id.hex() == "a" * 32 for span in spans)
    assert spans[0].span_id.hex() in traceparent
    assert spans[1].status.code == 2
