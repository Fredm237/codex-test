"""Export OTLP/HTTP opt-in de spans strictement bornés.

Ce module ne fait aucune auto-instrumentation : les seules données exportées
sont les noms et attributs fermés fournis par les wrappers FILON. Les arguments,
retours, messages d'erreur et ressources de processus ne sont jamais collectés.
"""

from __future__ import annotations

import threading
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Iterator, Mapping

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    SimpleSpanProcessor,
    SpanExporter,
)
from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased
from opentelemetry.trace import (
    NonRecordingSpan,
    Span,
    SpanContext,
    SpanKind,
    Status,
    StatusCode,
    TraceFlags,
    TraceState,
    set_span_in_context,
)

from app import __version__


_lock = threading.Lock()
_provider: TracerProvider | None = None
_tracer: trace.Tracer | None = None
_root_sampler: TraceIdRatioBased | None = None


def _valid_trace_id(value: str) -> bool:
    return (
        len(value) == 32
        and value != "0" * 32
        and all(character in "0123456789abcdef" for character in value)
    )


def _valid_span_id(value: str | None) -> bool:
    return bool(
        isinstance(value, str)
        and len(value) == 16
        and value != "0" * 16
        and all(character in "0123456789abcdef" for character in value)
    )


def _synthetic_parent_context(trace_id: str, span_id: str | None):
    safe_span_id = span_id if _valid_span_id(span_id) else "1".zfill(16)
    sampler = _root_sampler
    sampled = bool(
        sampler is not None
        and sampler.should_sample(
            parent_context=None,
            trace_id=int(trace_id, 16),
            name="filon.root",
        ).decision.is_sampled()
    )
    context = SpanContext(
        trace_id=int(trace_id, 16),
        span_id=int(safe_span_id, 16),
        is_remote=False,
        trace_flags=TraceFlags(TraceFlags.SAMPLED if sampled else 0),
        trace_state=TraceState(),
    )
    return set_span_in_context(NonRecordingSpan(context))


def configure_trace_export(
    settings: Any,
    *,
    exporter: SpanExporter | None = None,
    synchronous: bool = False,
) -> bool:
    """Configure une fois l'exporteur privé ; renvoie ``False`` si désactivé."""

    global _provider, _root_sampler, _tracer
    if settings.trace_export_backend == "disabled":
        return False

    with _lock:
        if _provider is not None:
            raise RuntimeError("trace exporter is already configured")
        selected_exporter = exporter or OTLPSpanExporter(
            endpoint=settings.otlp_traces_endpoint,
            headers={
                "authorization": f"Bearer {settings.otlp_trace_export_token}"
            },
            timeout=settings.trace_export_timeout_seconds,
        )
        root_sampler = TraceIdRatioBased(settings.trace_export_sample_ratio)
        provider = TracerProvider(
            resource=Resource(
                {
                    "service.name": "filon-backend",
                    "service.version": __version__,
                    "deployment.environment.name": settings.env,
                }
            ),
            sampler=ParentBased(root_sampler),
        )
        processor = (
            SimpleSpanProcessor(selected_exporter)
            if synchronous
            else BatchSpanProcessor(
                selected_exporter,
                max_queue_size=512,
                max_export_batch_size=128,
                schedule_delay_millis=5_000,
                export_timeout_millis=int(
                    settings.trace_export_timeout_seconds * 1_000
                ),
            )
        )
        provider.add_span_processor(processor)
        _provider = provider
        _root_sampler = root_sampler
        _tracer = provider.get_tracer("filon.observability", __version__)
    return True


def shutdown_trace_export() -> None:
    """Vide la file bornée et ferme l'exporteur, sans journaliser sa config."""

    global _provider, _root_sampler, _tracer
    with _lock:
        provider = _provider
        _provider = None
        _root_sampler = None
        _tracer = None
    if provider is not None:
        provider.shutdown()


@dataclass
class ExportedSpan:
    span: Span | None
    span_id: str | None
    sampled: bool | None

    def finish(self, *, outcome: str) -> None:
        if self.span is None:
            return
        self.span.set_attribute("filon.outcome", outcome)
        if outcome in {"error", "cancelled"}:
            self.span.set_status(Status(StatusCode.ERROR))


@contextmanager
def exported_span(
    name: str,
    *,
    request_id: str,
    parent_span_id: str | None = None,
    attributes: Mapping[str, str],
) -> Iterator[ExportedSpan]:
    """Crée un span sans exception, payload, URL ni attribut dynamique."""

    tracer = _tracer
    if tracer is None or not _valid_trace_id(request_id):
        yield ExportedSpan(span=None, span_id=None, sampled=None)
        return

    current = trace.get_current_span().get_span_context()
    context = None
    if not current.is_valid or current.trace_id != int(request_id, 16):
        context = _synthetic_parent_context(request_id, parent_span_id)
    with tracer.start_as_current_span(
        name,
        context=context,
        kind=SpanKind.INTERNAL,
        attributes=dict(attributes),
        record_exception=False,
        set_status_on_exception=False,
    ) as span:
        span_context = span.get_span_context()
        yield ExportedSpan(
            span=span,
            span_id=f"{span_context.span_id:016x}" if span_context.is_valid else None,
            sampled=(
                bool(span_context.trace_flags & TraceFlags.SAMPLED)
                if span_context.is_valid
                else None
            ),
        )
