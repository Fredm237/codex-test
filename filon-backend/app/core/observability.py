"""Observabilité HTTP bornée, sans payload ni identifiant utilisateur."""

from __future__ import annotations

import logging
import math
import threading
import time
import uuid
from collections import Counter, deque
from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Awaitable, Callable, TypeVar

from app.core.tracing import exported_span


_MAX_ROUTES = 100
_MAX_GLOBAL_SAMPLES = 5_000
_MAX_ROUTE_SAMPLES = 512
_MAX_ALERT_EVENTS = 512
_HTTP_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}

_DECISION_SCOPES = {
    "meilleur_prix_observe",
    "offre_documentee",
    "a_verifier",
    "non_recommandee",
    "tarif_a_verifier",
    "conditions_a_verifier",
}
_CONFIDENCE_LEVELS = {"not_calibrated"}
_OFFER_KINDS = {
    "physical_product",
    "tech_accessory",
    "accommodation",
    "service",
    "digital_content",
    "unknown",
}
_MISSING_DIMENSIONS = {
    "shipping_cost",
    "delivery_destination",
    "return_policy",
    "item_price",
    "currency",
    "history_currency",
    "comparison_scope",
    "price_history",
    "availability",
    "data_freshness",
    "stay_dates",
    "travellers",
    "booking_total",
    "mandatory_fees",
    "availability_for_dates",
    "cancellation_policy",
    "service_scope",
    "service_conditions",
    "appointment_availability",
    "digital_compatibility",
    "digital_region",
    "digital_terms",
    "offer_nature",
    "purchase_conditions",
}
_EVIDENCE_STATES = {"observed", "missing", "not_applicable"}
_RECOMMENDATION_DELIVERIES = {"generated", "cache", "timeout"}
_PIPELINE_STAGES = {"catalogue", "retrieval", "decision", "ingestion", "observation"}
_PIPELINE_OUTCOMES = {"ok", "degraded", "error", "cancelled"}
_DECISION_TRACE_STAGES = {
    "intent",
    "retrieval",
    "candidate_count",
    "filtering",
    "product_ranking",
    "offer_selection",
    "evidence",
    "decision",
}
_DECISION_TRACE_OUTCOMES = {
    "resolved",
    "unresolved",
    "recommend",
    "abstain",
    "fallback",
}
_DECISION_TRACE_REASONS = {
    "none",
    "intent_not_resolved",
    "no_eligible_offer",
    "no_verified_scope",
    "currency_not_comparable",
    "non_finite_total",
    "budget_unreachable",
    "no_catalog_offer",
    "no_comparable_offer",
    "no_current_evidence",
    "ranking_unavailable",
}
_DECISION_TRACE_COUNTS = {
    "scopes_count",
    "input_count",
    "candidate_count",
    "eligible_count",
    "rejected_count",
    "ranked_count",
    "selected_count",
    "evidenced_count",
    "unknown_count",
}
_DECISION_TRACE_FLAGS = {"semantic_used", "model_used", "cache_used"}
_DEPENDENCIES = {"postgres", "redis", "awin", "llm", "serpapi"}
_DEPENDENCY_OPERATIONS = {
    "read",
    "write",
    "invalidate",
    "complete",
    "complete_json",
    "programmes",
    "feed_list",
    "feed_download",
    "search",
}
_MAX_TRACE_COUNT = 2_147_483_647

_T = TypeVar("_T")


@dataclass(frozen=True)
class _RequestTrace:
    request_id: str


request_id_context: ContextVar[_RequestTrace | None] = ContextVar(
    "filon_request_id",
    default=None,
)
_dependency_span_context: ContextVar[str | None] = ContextVar(
    "filon_dependency_span_id",
    default=None,
)
_dependency_trace_flags_context: ContextVar[str | None] = ContextVar(
    "filon_dependency_trace_flags",
    default=None,
)


def normalize_request_id(value: str | None) -> str:
    """Génère un identifiant opaque sans faire confiance à l'entrée cliente.

    Le paramètre reste accepté pour préserver l'interface du middleware, mais sa
    valeur n'est ni réutilisée ni journalisée : un client ne peut donc injecter
    un identifiant personnel ou provoquer une collision dans les traces.
    """
    del value
    return uuid.uuid4().hex


def _is_opaque_request_id(value: str) -> bool:
    return (
        len(value) == 32
        and value != "0" * 32
        and all(character in "0123456789abcdef" for character in value)
    )


def bind_request_id_context(request_id: str):
    """Installe uniquement une corrélation opaque créée par FILON."""
    safe_request_id = request_id if _is_opaque_request_id(request_id) else uuid.uuid4().hex
    return request_id_context.set(_RequestTrace(safe_request_id))


def current_request_id() -> str | None:
    """Retourne uniquement la corrélation opaque créée et validée par FILON."""
    trace = request_id_context.get()
    if isinstance(trace, _RequestTrace) and _is_opaque_request_id(trace.request_id):
        return trace.request_id
    return None


def _new_span_id() -> str:
    span_id = uuid.uuid4().hex[:16]
    return span_id if span_id != "0" * 16 else "1".zfill(16)


def outbound_trace_headers() -> dict[str, str]:
    """Construit des en-têtes de corrélation sans réutiliser d'entrée cliente.

    ``request_id`` respecte la taille d'un trace-id W3C. Le span courant est
    celui du bloc de dépendance lorsqu'il existe ; sinon un span opaque neuf est
    créé. Aucune URL, clé de cache ou donnée métier n'entre dans ces valeurs.
    """
    request_id = current_request_id()
    if request_id is None:
        return {}
    span_id = _dependency_span_context.get()
    if (
        not isinstance(span_id, str)
        or len(span_id) != 16
        or span_id == "0" * 16
        or any(character not in "0123456789abcdef" for character in span_id)
    ):
        span_id = _new_span_id()
    trace_flags = _dependency_trace_flags_context.get()
    if trace_flags not in {"00", "01"}:
        trace_flags = "01"
    return {
        "traceparent": f"00-{request_id}-{span_id}-{trace_flags}",
        "x-request-id": request_id,
    }


def _bounded_trace_count(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return min(value, _MAX_TRACE_COUNT)


def decision_trace_event(
    stage: str,
    *,
    outcome: str | None = None,
    reason: str | None = None,
    counts: Mapping[str, object] | None = None,
    flags: Mapping[str, object] | None = None,
) -> bool:
    """Journalise un jalon décisionnel fermé et sans donnée métier libre.

    Les champs inconnus sont ignorés. Les codes hors contrat deviennent
    ``OTHER`` et les comptes invalides sont retirés. Sans contexte FILON valide,
    aucun événement n'est émis afin de ne jamais adopter un identifiant externe.
    """
    request_id = current_request_id()
    if request_id is None or stage not in _DECISION_TRACE_STAGES:
        return False
    fields = [f"request_id={request_id}", "pipeline=decision", f"event={stage}"]
    if outcome is not None:
        fields.append(
            f"outcome={outcome if outcome in _DECISION_TRACE_OUTCOMES else 'OTHER'}"
        )
    if reason is not None:
        fields.append(
            f"reason={reason if reason in _DECISION_TRACE_REASONS else 'OTHER'}"
        )
    if counts is not None:
        for key in sorted(_DECISION_TRACE_COUNTS):
            if key not in counts:
                continue
            value = _bounded_trace_count(counts[key])
            if value is not None:
                fields.append(f"{key}={value}")
    if flags is not None:
        for key in sorted(_DECISION_TRACE_FLAGS):
            if type(flags.get(key)) is bool:
                fields.append(f"{key}={'true' if flags[key] else 'false'}")
    logging.getLogger("filon.decision_trace").info(" ".join(fields))
    return True


@asynccontextmanager
async def traced_dependency(
    dependency: str,
    operation: str,
) -> AsyncIterator[None]:
    """Corrèle une dépendance sans journaliser arguments, retours ou erreurs."""
    dependency_label = _bounded_label(dependency, _DEPENDENCIES)
    operation_label = _bounded_label(operation, _DEPENDENCY_OPERATIONS)
    owned_request_token = None
    request_id = current_request_id()
    if request_id is None:
        request_id = uuid.uuid4().hex
        owned_request_token = request_id_context.set(_RequestTrace(request_id))
    span_id = _new_span_id()
    dependency_log = logging.getLogger(
        f"filon.dependency.{dependency_label.lower()}"
    )
    started = time.monotonic()
    with exported_span(
        f"filon.dependency.{dependency_label.lower()}.{operation_label.lower()}",
        request_id=request_id,
        parent_span_id=_dependency_span_context.get(),
        attributes={
            "filon.span.kind": "dependency",
            "filon.dependency": dependency_label,
            "filon.operation": operation_label,
        },
    ) as exported:
        if exported.span_id is not None:
            span_id = exported.span_id
        span_token = _dependency_span_context.set(span_id)
        trace_flags_token = _dependency_trace_flags_context.set(
            "01" if exported.sampled is not False else "00"
        )
        dependency_log.info(
            "request_id=%s span_id=%s dependency=%s operation=%s "
            "event=start",
            request_id,
            span_id,
            dependency_label,
            operation_label,
        )
        try:
            yield
        except BaseException as exc:
            outcome = "error" if isinstance(exc, Exception) else "cancelled"
            exported.finish(outcome=outcome)
            dependency_log.warning(
                "request_id=%s span_id=%s dependency=%s operation=%s "
                "event=finish outcome=%s error_type=%s elapsed_ms=%.1f",
                request_id,
                span_id,
                dependency_label,
                operation_label,
                outcome,
                type(exc).__name__,
                (time.monotonic() - started) * 1000,
            )
            raise
        else:
            exported.finish(outcome="ok")
            dependency_log.info(
                "request_id=%s span_id=%s dependency=%s operation=%s "
                "event=finish outcome=ok elapsed_ms=%.1f",
                request_id,
                span_id,
                dependency_label,
                operation_label,
                (time.monotonic() - started) * 1000,
            )
        finally:
            _dependency_trace_flags_context.reset(trace_flags_token)
            _dependency_span_context.reset(span_token)
            if owned_request_token is not None:
                request_id_context.reset(owned_request_token)


def _percentile(samples: deque[float], percentile: float) -> float | None:
    if not samples:
        return None
    values = sorted(samples)
    index = max(0, math.ceil(percentile * len(values)) - 1)
    return round(values[index], 1)


def _bounded_http_method(value: str) -> str:
    """Empêche un verbe libre d'occuper toutes les séries de routes."""
    method = str(value or "").upper()
    return method if method in _HTTP_METHODS else "OTHER_METHOD"


def _bounded_status_group(value: object) -> str:
    """Conserve seulement les cinq familles de statut HTTP définies."""
    if type(value) is int and 100 <= value <= 599:
        return f"{value // 100}xx"
    return "OTHER_STATUS"


def _validated_elapsed_ms(value: object) -> float:
    """Refuse toute latence qui pourrait muter ou empoisonner les agrégats."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("elapsed_ms_must_be_finite_nonnegative")
    try:
        safe_value = float(value)
    except (OverflowError, TypeError, ValueError) as exc:
        raise ValueError("elapsed_ms_must_be_finite_nonnegative") from exc
    if not math.isfinite(safe_value) or safe_value < 0:
        raise ValueError("elapsed_ms_must_be_finite_nonnegative")
    return safe_value


@dataclass
class _LatencySeries:
    max_samples: int
    count: int = 0
    total_ms: float = 0.0
    maximum_ms: float = 0.0
    statuses: Counter[str] = field(default_factory=Counter)
    samples: deque[float] = field(init=False)

    def __post_init__(self) -> None:
        self.samples = deque(maxlen=self.max_samples)

    def record(self, status_group: str, elapsed_ms: float) -> None:
        self.count += 1
        self.total_ms += elapsed_ms
        self.maximum_ms = max(self.maximum_ms, elapsed_ms)
        self.statuses[status_group] += 1
        self.samples.append(elapsed_ms)

    def snapshot(self) -> dict[str, Any]:
        return {
            "requests": self.count,
            "status_groups": dict(sorted(self.statuses.items())),
            "latency_ms": {
                "average": round(self.total_ms / self.count, 1)
                if self.count
                else None,
                "p50": _percentile(self.samples, 0.50),
                "p95": _percentile(self.samples, 0.95),
                "p99": _percentile(self.samples, 0.99),
                "maximum": round(self.maximum_ms, 1) if self.count else None,
                "sample_size": len(self.samples),
            },
        }


@dataclass
class _StageSeries:
    max_samples: int
    count: int = 0
    total_ms: float = 0.0
    maximum_ms: float = 0.0
    outcomes: Counter[str] = field(default_factory=Counter)
    samples: deque[float] = field(init=False)

    def __post_init__(self) -> None:
        self.samples = deque(maxlen=self.max_samples)

    def record(self, outcome: str, elapsed_ms: float) -> None:
        self.count += 1
        self.total_ms += elapsed_ms
        self.maximum_ms = max(self.maximum_ms, elapsed_ms)
        self.outcomes[outcome] += 1
        self.samples.append(elapsed_ms)

    def snapshot(self) -> dict[str, Any]:
        return {
            "executions": self.count,
            "outcomes": dict(sorted(self.outcomes.items())),
            "latency_ms": {
                "average": round(self.total_ms / self.count, 1) if self.count else None,
                "p50": _percentile(self.samples, 0.50),
                "p95": _percentile(self.samples, 0.95),
                "p99": _percentile(self.samples, 0.99),
                "maximum": round(self.maximum_ms, 1) if self.count else None,
                "sample_size": len(self.samples),
            },
        }


class RequestMetricsRegistry:
    """Agrège des routes templatisées avec une cardinalité plafonnée."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._started = time.time()
        self._global = _LatencySeries(_MAX_GLOBAL_SAMPLES)
        self._routes: dict[str, _LatencySeries] = {}
        self._alert_events: deque[str] = deque(maxlen=_MAX_ALERT_EVENTS)
        self._alert_events_seen = 0
        self._alert_generation = 1

    def record(
        self,
        *,
        method: str,
        route: str,
        status_code: int,
        elapsed_ms: float,
    ) -> None:
        method_label = _bounded_http_method(method)
        key = f"{method_label} {route}"
        status_group = _bounded_status_group(status_code)
        safe_elapsed = _validated_elapsed_ms(elapsed_ms)
        with self._lock:
            # Une place est réservée au seau OTHER afin que le nombre total
            # de séries ne dépasse jamais la cardinalité annoncée.
            if (
                key not in self._routes
                and "OTHER" not in self._routes
                and len(self._routes) >= _MAX_ROUTES - 1
            ):
                key = "OTHER"
            elif key not in self._routes and len(self._routes) >= _MAX_ROUTES:
                key = "OTHER"
            series = self._routes.setdefault(
                key,
                _LatencySeries(_MAX_ROUTE_SAMPLES),
            )
            self._global.record(status_group, safe_elapsed)
            series.record(status_group, safe_elapsed)
            self._alert_events_seen += 1
            self._alert_events.append(status_group)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            overall = self._global.snapshot()
            routes = {
                key: series.snapshot()
                for key, series in sorted(
                    self._routes.items(),
                    key=lambda item: (-item[1].count, item[0]),
                )
            }
            return {
                "uptime_seconds": round(time.time() - self._started),
                "retention": {
                    "global_samples": _MAX_GLOBAL_SAMPLES,
                    "samples_per_route": _MAX_ROUTE_SAMPLES,
                    "route_cardinality": _MAX_ROUTES,
                },
                "overall": overall,
                "routes": routes,
            }

    def alert_snapshot(self) -> dict[str, Any]:
        """Retourne une fenêtre d'événements sans route ni donnée libre."""
        with self._lock:
            statuses = Counter(self._alert_events)
            return {
                "window_kind": "last_events",
                "window_capacity": _MAX_ALERT_EVENTS,
                "window_truncated": self._alert_events_seen > _MAX_ALERT_EVENTS,
                "generation": self._alert_generation,
                "events_seen": self._alert_events_seen,
                "retained_events": len(self._alert_events),
                "sample_size": len(self._alert_events),
                "status_groups": dict(sorted(statuses.items())),
            }

    def reset(self) -> None:
        """Réinitialise uniquement les tests ; aucun endpoint ne l'expose."""
        with self._lock:
            self._started = time.time()
            self._global = _LatencySeries(_MAX_GLOBAL_SAMPLES)
            self._routes = {}
            self._alert_events = deque(maxlen=_MAX_ALERT_EVENTS)
            self._alert_events_seen = 0
            self._alert_generation += 1


request_metrics = RequestMetricsRegistry()


def _bounded_label(value: object, allowed: set[str]) -> str:
    """Garde une dimension connue sans ouvrir une cardinalité libre."""
    label = str(value or "unknown")
    return label if label in allowed else "OTHER"


def _freshness_bucket(age_hours: object) -> str:
    if not isinstance(age_hours, (int, float)):
        return "unknown"
    if age_hours <= 72:
        return "0_72h"
    if age_hours <= 7 * 24:
        return "73_168h"
    if age_hours <= 30 * 24:
        return "8_30d"
    return "over_30d"


class ProductIntelligenceMetricsRegistry:
    """Compteurs métier bornés, sans requête ni identifiant d'offre.

    Les valeurs libres sont systématiquement ramenées à ``OTHER``. Le
    registre compte les évaluations produites et les réponses de l'assistant ;
    il ne conserve ni payload, ni titre produit, ni pays, ni utilisateur.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._alert_generation = 0
        self.reset()

    def record_decision(self, decision: dict[str, Any]) -> None:
        scope = _bounded_label(decision.get("recommendation_scope"), _DECISION_SCOPES)
        confidence = _bounded_label(decision.get("confidence"), _CONFIDENCE_LEVELS)
        offer_kind = _bounded_label(decision.get("offer_kind"), _OFFER_KINDS)
        missing = decision.get("missing") if isinstance(decision.get("missing"), list) else []
        evidence = decision.get("evidence") if isinstance(decision.get("evidence"), list) else []
        signals = decision.get("signals") if isinstance(decision.get("signals"), list) else []
        freshness = next(
            (
                signal
                for signal in signals
                if isinstance(signal, dict) and signal.get("key") == "freshness"
            ),
            {},
        )
        exclusions: list[str] = []
        if scope == "non_recommandee":
            facts = decision.get("facts") if isinstance(decision.get("facts"), dict) else {}
            if facts.get("item_price") is None:
                exclusions.append("missing_price")
            availability = next(
                (
                    signal
                    for signal in signals
                    if isinstance(signal, dict) and signal.get("key") == "availability"
                ),
                {},
            )
            if availability.get("in_stock") is False:
                exclusions.append("out_of_stock")
            if not exclusions:
                exclusions.append("policy")
        freshness_status = _bounded_label(
            freshness.get("status"),
            {"positive", "warning", "unknown"},
        )
        freshness_bucket = _freshness_bucket(freshness.get("age_hours"))
        missing_labels = [_bounded_label(key, _MISSING_DIMENSIONS) for key in missing]
        evidence_states = [
            _bounded_label(item.get("state"), _EVIDENCE_STATES)
            for item in evidence
            if isinstance(item, dict)
        ]

        with self._lock:
            self._decisions += 1
            self._scopes[scope] += 1
            self._confidences[confidence] += 1
            self._offer_kinds[offer_kind] += 1
            self._freshness_statuses[freshness_status] += 1
            self._freshness_buckets[freshness_bucket] += 1
            for label in missing_labels:
                self._missing_dimensions[label] += 1
            for state in evidence_states:
                self._evidence_states[state] += 1
            for reason in exclusions:
                self._decision_exclusions[reason] += 1

    def record_recommendation(self, result: dict[str, Any], *, delivery: str) -> None:
        cards = result.get("cards") if isinstance(result.get("cards"), list) else []
        real = result.get("real") is True
        card_count = len(cards)
        card_bucket = str(card_count) if card_count <= 5 else "6_plus"
        outcome = "documented" if real and card_count else "abstained"
        buy_cards = sum(card.get("buy") is True for card in cards if isinstance(card, dict))
        delivery_label = _bounded_label(delivery, _RECOMMENDATION_DELIVERIES)
        with self._lock:
            self._recommendations += 1
            self._recommendation_outcomes[outcome] += 1
            self._recommendation_deliveries[delivery_label] += 1
            self._card_counts[card_bucket] += 1
            self._buy_cards += buy_cards
            self._recommendation_alert_events.append(delivery_label)
            self._recommendation_alert_events_seen += 1

    def record_stage(self, *, stage: str, outcome: str, elapsed_ms: float) -> None:
        safe_elapsed = _validated_elapsed_ms(elapsed_ms)
        stage_label = _bounded_label(stage, _PIPELINE_STAGES)
        outcome_label = _bounded_label(outcome, _PIPELINE_OUTCOMES)
        with self._lock:
            series = self._pipeline_stages.setdefault(
                stage_label,
                _StageSeries(_MAX_ROUTE_SAMPLES),
            )
            series.record(outcome_label, safe_elapsed)
            alert_events = self._stage_alert_events.setdefault(
                stage_label,
                deque(maxlen=_MAX_ALERT_EVENTS),
            )
            alert_events.append((outcome_label, safe_elapsed))
            self._stage_alert_events_seen[stage_label] += 1

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "schema_version": 1,
                "privacy": "aggregate_only_no_query_or_offer_identifier",
                "decision_evaluations": {
                    "total": self._decisions,
                    "scopes": dict(sorted(self._scopes.items())),
                    "confidence": dict(sorted(self._confidences.items())),
                    "offer_kinds": dict(sorted(self._offer_kinds.items())),
                    "freshness_status": dict(sorted(self._freshness_statuses.items())),
                    "freshness_age_buckets": dict(sorted(self._freshness_buckets.items())),
                    "missing_dimensions": dict(sorted(self._missing_dimensions.items())),
                    "evidence_states": dict(sorted(self._evidence_states.items())),
                    "exclusions": dict(sorted(self._decision_exclusions.items())),
                },
                "recommendation_responses": {
                    "total": self._recommendations,
                    "outcomes": dict(sorted(self._recommendation_outcomes.items())),
                    "delivery": dict(sorted(self._recommendation_deliveries.items())),
                    "card_count_buckets": dict(sorted(self._card_counts.items())),
                    "buy_cards": self._buy_cards,
                },
                "pipeline_stages": {
                    key: series.snapshot()
                    for key, series in sorted(self._pipeline_stages.items())
                },
            }

    def alert_snapshot(self) -> dict[str, Any]:
        """Expose uniquement les fenêtres nécessaires à l'évaluateur local."""
        with self._lock:
            deliveries = Counter(self._recommendation_alert_events)
            stages: dict[str, dict[str, Any]] = {}
            for stage, events in sorted(self._stage_alert_events.items()):
                observable = [event for event in events if event[0] != "cancelled"]
                outcomes = Counter(outcome for outcome, _elapsed in observable)
                latencies = deque(elapsed for _outcome, elapsed in observable)
                stages[stage] = {
                    "window_kind": "last_events",
                    "window_capacity": _MAX_ALERT_EVENTS,
                    "window_truncated": (
                        self._stage_alert_events_seen[stage] > _MAX_ALERT_EVENTS
                    ),
                    "generation": self._alert_generation,
                    "events_seen": self._stage_alert_events_seen[stage],
                    "retained_events": len(events),
                    "sample_size": len(observable),
                    "cancelled_excluded": len(events) - len(observable),
                    "outcomes": dict(sorted(outcomes.items())),
                    "latency_ms": {
                        "p95": _percentile(latencies, 0.95),
                        "sample_size": len(latencies),
                    },
                }
            return {
                "recommendations": {
                    "window_kind": "last_events",
                    "window_capacity": _MAX_ALERT_EVENTS,
                    "window_truncated": (
                        self._recommendation_alert_events_seen > _MAX_ALERT_EVENTS
                    ),
                    "generation": self._alert_generation,
                    "events_seen": self._recommendation_alert_events_seen,
                    "retained_events": len(self._recommendation_alert_events),
                    "sample_size": len(self._recommendation_alert_events),
                    "delivery": dict(sorted(deliveries.items())),
                },
                "pipeline_stages": stages,
            }

    def reset(self) -> None:
        """Réinitialise uniquement les tests ; aucun endpoint ne l'expose."""
        with self._lock:
            self._alert_generation += 1
            self._decisions = 0
            self._recommendations = 0
            self._buy_cards = 0
            self._scopes: Counter[str] = Counter()
            self._confidences: Counter[str] = Counter()
            self._offer_kinds: Counter[str] = Counter()
            self._freshness_statuses: Counter[str] = Counter()
            self._freshness_buckets: Counter[str] = Counter()
            self._missing_dimensions: Counter[str] = Counter()
            self._evidence_states: Counter[str] = Counter()
            self._decision_exclusions: Counter[str] = Counter()
            self._recommendation_outcomes: Counter[str] = Counter()
            self._recommendation_deliveries: Counter[str] = Counter()
            self._card_counts: Counter[str] = Counter()
            self._pipeline_stages: dict[str, _StageSeries] = {}
            self._recommendation_alert_events: deque[str] = deque(
                maxlen=_MAX_ALERT_EVENTS
            )
            self._recommendation_alert_events_seen = 0
            self._stage_alert_events: dict[
                str,
                deque[tuple[str, float]],
            ] = {}
            self._stage_alert_events_seen: Counter[str] = Counter()


product_intelligence_metrics = ProductIntelligenceMetricsRegistry()


def traced_pipeline_stage(
    stage: str,
    *,
    result_outcome: Callable[[Any], str] | None = None,
) -> Callable[[Callable[..., Awaitable[_T]]], Callable[..., Awaitable[_T]]]:
    """Corrèle une étape async sans journaliser ses arguments ni son retour.

    Une exécution hors HTTP reçoit un identifiant opaque propre. Les étapes
    imbriquées réutilisent le contexte existant, ce qui relie par exemple
    catalogue → retrieval → decision. Les jobs d'ingestion et de replay
    d'observation reçoivent la même protection hors HTTP.
    """
    stage_label = _bounded_label(stage, _PIPELINE_STAGES)
    stage_log = logging.getLogger(f"filon.stage.{stage_label.lower()}")

    def decorator(function: Callable[..., Awaitable[_T]]) -> Callable[..., Awaitable[_T]]:
        @wraps(function)
        async def wrapped(*args: Any, **kwargs: Any) -> _T:
            owned_token = None
            trace = request_id_context.get()
            if isinstance(trace, _RequestTrace):
                request_id = trace.request_id
            else:
                request_id = uuid.uuid4().hex
                owned_token = request_id_context.set(_RequestTrace(request_id))
            started = time.monotonic()
            with exported_span(
                f"filon.pipeline.{stage_label.lower()}",
                request_id=request_id,
                attributes={
                    "filon.span.kind": "pipeline",
                    "filon.stage": stage_label,
                },
            ) as exported:
                stage_log.info("request_id=%s stage=%s event=start", request_id, stage_label)
                try:
                    result = await function(*args, **kwargs)
                except BaseException as exc:
                    elapsed_ms = (time.monotonic() - started) * 1000
                    outcome = "error" if isinstance(exc, Exception) else "cancelled"
                    exported.finish(outcome=outcome)
                    product_intelligence_metrics.record_stage(
                        stage=stage_label,
                        outcome=outcome,
                        elapsed_ms=elapsed_ms,
                    )
                    # Seul le type est journalisé : le message d'exception peut
                    # contenir une URL signée, une requête ou une valeur source.
                    stage_log.warning(
                        "request_id=%s stage=%s event=finish outcome=%s error_type=%s elapsed_ms=%.1f",
                        request_id,
                        stage_label,
                        outcome,
                        type(exc).__name__,
                        elapsed_ms,
                    )
                    raise
                else:
                    elapsed_ms = (time.monotonic() - started) * 1000
                    outcome = "ok"
                    if result_outcome is not None:
                        try:
                            outcome = _bounded_label(result_outcome(result), _PIPELINE_OUTCOMES)
                        except Exception as exc:
                            # Une erreur d'instrumentation ne doit jamais modifier
                            # le résultat métier. La mesure devient explicitement
                            # dégradée, sans exposer le message de l'exception.
                            outcome = "degraded"
                            stage_log.warning(
                                "request_id=%s stage=%s event=outcome_resolution "
                                "outcome=degraded error_type=%s",
                                request_id,
                                stage_label,
                                type(exc).__name__,
                            )
                    exported.finish(outcome=outcome)
                    product_intelligence_metrics.record_stage(
                        stage=stage_label,
                        outcome=outcome,
                        elapsed_ms=elapsed_ms,
                    )
                    stage_log.info(
                        "request_id=%s stage=%s event=finish outcome=%s elapsed_ms=%.1f",
                        request_id,
                        stage_label,
                        outcome,
                        elapsed_ms,
                    )
                    return result
                finally:
                    if owned_token is not None:
                        request_id_context.reset(owned_token)

        return wrapped

    return decorator
