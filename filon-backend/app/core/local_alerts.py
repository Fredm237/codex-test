"""Évaluation locale et provisoire de signaux bornés, sans notification réseau."""

from __future__ import annotations

import math
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Mapping

from app.core.observability import product_intelligence_metrics, request_metrics


POLICY_VERSION = "local-alert-policy-v1"
POLICY_STATUS = "provisional_local_not_slo"
MAX_SILENCE_DURATION = timedelta(hours=1)
SILENCE_REASON_CODES = frozenset(
    {
        "maintenance",
        "controlled_test",
        "dependency_incident",
    }
)


@dataclass(frozen=True)
class _RuleSpec:
    rule_id: str
    source_path: tuple[str, ...]
    metric: str
    counter_group: str | None
    counter_value: str | None
    allowed_counter_values: frozenset[str] | None
    minimum_samples: int
    trigger_gte: float
    resolve_lte: float
    unit: str


_RULES = (
    _RuleSpec(
        "http_5xx_ratio",
        ("http",),
        "ratio",
        "status_groups",
        "5xx",
        frozenset({"1xx", "2xx", "3xx", "4xx", "5xx"}),
        100,
        0.05,
        0.02,
        "ratio",
    ),
    _RuleSpec(
        "catalogue_error_ratio",
        ("product_intelligence", "pipeline_stages", "catalogue"),
        "ratio",
        "outcomes",
        "error",
        frozenset({"ok", "degraded", "error"}),
        50,
        0.10,
        0.02,
        "ratio",
    ),
    _RuleSpec(
        "retrieval_error_ratio",
        ("product_intelligence", "pipeline_stages", "retrieval"),
        "ratio",
        "outcomes",
        "error",
        frozenset({"ok", "degraded", "error"}),
        50,
        0.10,
        0.02,
        "ratio",
    ),
    _RuleSpec(
        "assistant_timeout_ratio",
        ("product_intelligence", "recommendations"),
        "ratio",
        "delivery",
        "timeout",
        frozenset({"generated", "cache", "timeout"}),
        100,
        0.05,
        0.01,
        "ratio",
    ),
    _RuleSpec(
        "retrieval_p95_ms",
        ("product_intelligence", "pipeline_stages", "retrieval"),
        "p95",
        None,
        None,
        None,
        200,
        750.0,
        600.0,
        "ms",
    ),
)

RULE_IDS = tuple(rule.rule_id for rule in _RULES)


@dataclass(frozen=True)
class AlertSilence:
    """Silence local borné ; il ne modifie jamais l'état du signal."""

    rule_id: str
    reason_code: str
    created_at: datetime
    expires_at: datetime


@dataclass(frozen=True)
class _Measurement:
    value: float | None
    sample_size: int
    reason_code: str | None
    window_truncated: bool
    generation: int | None
    sequence: int | None


@dataclass(frozen=True)
class _NormalizedSilence:
    rule_id: str
    reason_code: str
    created_at: datetime
    expires_at: datetime
    until: str


def collect_local_alert_inputs() -> dict[str, Any]:
    """Collecte directement les registres en mémoire, sans autopoll HTTP."""
    return {
        "http": request_metrics.alert_snapshot(),
        "product_intelligence": product_intelligence_metrics.alert_snapshot(),
    }


def _node_at(inputs: Mapping[str, Any], path: tuple[str, ...]) -> Mapping[str, Any] | None:
    current: Any = inputs
    for key in path:
        if not isinstance(current, Mapping):
            return None
        current = current.get(key)
    return current if isinstance(current, Mapping) else None


def _valid_count(value: Any) -> bool:
    return type(value) is int and value >= 0


def _is_aware_datetime(value: Any) -> bool:
    if not isinstance(value, datetime) or value.tzinfo is None:
        return False
    try:
        return value.utcoffset() is not None
    except Exception:
        return False


def _normalized_utc(value: datetime) -> datetime:
    converted = value.astimezone(timezone.utc)
    return datetime(
        converted.year,
        converted.month,
        converted.day,
        converted.hour,
        converted.minute,
        converted.second,
        converted.microsecond,
        tzinfo=timezone.utc,
        fold=converted.fold,
    )


def _window_metadata(
    node: Mapping[str, Any],
) -> tuple[int, int, int, int, bool] | None:
    capacity = node.get("window_capacity")
    truncated = node.get("window_truncated")
    generation = node.get("generation")
    events_seen = node.get("events_seen")
    retained_events = node.get("retained_events")
    sample_size = node.get("sample_size")
    if (
        node.get("window_kind") != "last_events"
        or capacity != 512
        or not isinstance(truncated, bool)
        or not _valid_count(generation)
        or generation == 0
        or not _valid_count(events_seen)
        or not _valid_count(retained_events)
        or not _valid_count(sample_size)
        or retained_events != min(events_seen, capacity)
        or truncated != (events_seen > capacity)
        or sample_size > retained_events
    ):
        return None
    cancelled_excluded = node.get("cancelled_excluded", 0)
    if (
        not _valid_count(cancelled_excluded)
        or sample_size + cancelled_excluded != retained_events
    ):
        return None
    return sample_size, retained_events, generation, events_seen, truncated


def _ratio_measurement(node: Mapping[str, Any], rule: _RuleSpec) -> _Measurement:
    metadata = _window_metadata(node)
    if metadata is None:
        return _Measurement(None, 0, "invalid_aggregate", False, None, None)
    sample_size, retained_events, generation, sequence, truncated = metadata
    counters = node.get(rule.counter_group or "")
    if not isinstance(counters, Mapping):
        return _Measurement(
            None, 0, "invalid_aggregate", truncated, generation, sequence
        )
    if not set(counters).issubset(rule.allowed_counter_values or frozenset()):
        return _Measurement(
            None, 0, "invalid_aggregate", truncated, generation, sequence
        )
    values = list(counters.values())
    if not all(_valid_count(value) for value in values):
        return _Measurement(
            None, 0, "invalid_aggregate", truncated, generation, sequence
        )
    if sum(values) != sample_size:
        return _Measurement(
            None, 0, "invalid_aggregate", truncated, generation, sequence
        )
    numerator = counters.get(rule.counter_value or "", 0)
    if not _valid_count(numerator):
        return _Measurement(
            None, 0, "invalid_aggregate", truncated, generation, sequence
        )
    value = (numerator / sample_size) if sample_size else None
    if (
        sample_size * 2 < retained_events
        and (value is None or value < rule.trigger_gte)
    ):
        return _Measurement(
            None,
            sample_size,
            "insufficient_observable_events",
            truncated,
            generation,
            sequence,
        )
    return _Measurement(
        value,
        sample_size,
        None,
        truncated,
        generation,
        sequence,
    )


def _p95_measurement(node: Mapping[str, Any], rule: _RuleSpec) -> _Measurement:
    metadata = _window_metadata(node)
    if metadata is None:
        return _Measurement(None, 0, "invalid_aggregate", False, None, None)
    event_sample_size, retained_events, generation, sequence, truncated = metadata
    latency = node.get("latency_ms")
    if not isinstance(latency, Mapping):
        return _Measurement(
            None, 0, "invalid_aggregate", truncated, generation, sequence
        )
    sample_size = latency.get("sample_size")
    value = latency.get("p95")
    if not _valid_count(sample_size) or sample_size != event_sample_size:
        return _Measurement(
            None, 0, "invalid_aggregate", truncated, generation, sequence
        )
    if value is None and sample_size == 0:
        return _Measurement(
            None,
            0,
            None,
            truncated,
            generation,
            sequence,
        )
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
        or value < 0
    ):
        return _Measurement(
            None, 0, "invalid_aggregate", truncated, generation, sequence
        )
    if event_sample_size * 2 < retained_events and float(value) < rule.trigger_gte:
        return _Measurement(
            None,
            event_sample_size,
            "insufficient_observable_events",
            truncated,
            generation,
            sequence,
        )
    return _Measurement(
        float(value),
        sample_size,
        None,
        truncated,
        generation,
        sequence,
    )


def _measurement(inputs: Mapping[str, Any], rule: _RuleSpec) -> _Measurement:
    node = _node_at(inputs, rule.source_path)
    if node is None:
        return _Measurement(None, 0, "source_missing", False, None, None)
    if rule.metric == "ratio":
        return _ratio_measurement(node, rule)
    return _p95_measurement(node, rule)


def _utc_iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


class LocalAlertEvaluator:
    """Applique seuils et hystérésis sans déclarer de SLO ou d'état sain."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._firing: set[str] = set()
        self._silenced_firing: set[str] = set()
        self._last_positions: dict[str, tuple[int, int]] = {}
        self._pending_invalid_positions: dict[str, tuple[int, int]] = {}
        self._last_signatures: dict[
            str,
            tuple[float | None, int, str | None, bool],
        ] = {}
        self._last_evaluation_time: datetime | None = None

    @staticmethod
    def _normalize_silences(
        silences: Iterable[AlertSilence],
    ) -> tuple[_NormalizedSilence, ...]:
        normalized: list[_NormalizedSilence] = []
        for silence in silences:
            if type(silence) is not AlertSilence:
                raise ValueError("invalid_silence")
            if type(silence.rule_id) is not str:
                raise ValueError("invalid_silence")
            if type(silence.reason_code) is not str:
                raise ValueError("invalid_silence")
            if silence.rule_id not in RULE_IDS:
                raise ValueError("unknown_alert_rule")
            if silence.reason_code not in SILENCE_REASON_CODES:
                raise ValueError("unknown_silence_reason")
            if not _is_aware_datetime(silence.created_at) or not _is_aware_datetime(
                silence.expires_at
            ):
                raise ValueError("silence_requires_timezone")
            created_at = _normalized_utc(silence.created_at)
            expires_at = _normalized_utc(silence.expires_at)
            duration = expires_at - created_at
            if duration <= timedelta(0) or duration > MAX_SILENCE_DURATION:
                raise ValueError("invalid_silence_duration")
            normalized.append(
                _NormalizedSilence(
                    rule_id=silence.rule_id,
                    reason_code=silence.reason_code,
                    created_at=created_at,
                    expires_at=expires_at,
                    until=_utc_iso(expires_at),
                )
            )
        return tuple(normalized)

    def evaluate(
        self,
        inputs: Mapping[str, Any],
        *,
        silences: Iterable[AlertSilence] = (),
        now: datetime | None = None,
    ) -> dict[str, Any]:
        current_time = datetime.now(timezone.utc) if now is None else now
        if not _is_aware_datetime(current_time):
            raise ValueError("evaluation_requires_timezone")

        # Les itérateurs et Mapping fournis peuvent exécuter du code utilisateur.
        # Ils sont entièrement matérialisés/lus avant le verrou d'état afin
        # d'éviter interblocage et rappel externe dans la section critique.
        evaluation_time = _normalized_utc(current_time)
        normalized_silences = self._normalize_silences(tuple(silences))
        measurements = tuple((rule, _measurement(inputs, rule)) for rule in _RULES)

        with self._lock:
            effective_time = max(
                evaluation_time,
                self._last_evaluation_time or evaluation_time,
            )
            active_silences: dict[str, _NormalizedSilence] = {}
            for silence in normalized_silences:
                if silence.created_at <= effective_time < silence.expires_at:
                    if silence.rule_id in active_silences:
                        raise ValueError("duplicate_active_silence")
                    active_silences[silence.rule_id] = silence
            self._last_evaluation_time = effective_time
            evaluated: dict[str, dict[str, Any]] = {}

            for rule, measured in measurements:
                transition = "none"
                reason_code = measured.reason_code
                position = (
                    (measured.generation, measured.sequence)
                    if measured.generation is not None
                    and measured.sequence is not None
                    else None
                )
                previous_position = self._last_positions.get(rule.rule_id)
                stale_snapshot = False
                conflicting_snapshot = False
                has_new_observation = False
                signature = (
                    measured.value,
                    measured.sample_size,
                    measured.reason_code,
                    measured.window_truncated,
                )
                invalid_measurement = measured.reason_code == "invalid_aggregate"
                if position is not None:
                    if previous_position is None or (
                        position[0] > previous_position[0]
                        or (
                            position[0] == previous_position[0]
                            and position[1] > previous_position[1]
                        )
                    ):
                        self._last_positions[rule.rule_id] = position
                        if invalid_measurement:
                            self._pending_invalid_positions[rule.rule_id] = position
                            self._last_signatures.pop(rule.rule_id, None)
                        else:
                            has_new_observation = True
                            self._pending_invalid_positions.pop(rule.rule_id, None)
                            self._last_signatures[rule.rule_id] = signature
                    elif position < previous_position:
                        stale_snapshot = True
                    elif self._pending_invalid_positions.get(rule.rule_id) == position:
                        if not invalid_measurement:
                            has_new_observation = True
                            self._pending_invalid_positions.pop(rule.rule_id, None)
                            self._last_signatures[rule.rule_id] = signature
                    elif self._last_signatures.get(rule.rule_id) != signature:
                        conflicting_snapshot = True

                if stale_snapshot:
                    state = "insufficient_data"
                    reason_code = "stale_snapshot"
                elif conflicting_snapshot:
                    state = "insufficient_data"
                    reason_code = "conflicting_snapshot"
                elif measured.value is None or measured.sample_size < rule.minimum_samples:
                    state = "insufficient_data"
                    if reason_code is None:
                        reason_code = "minimum_samples_not_met"
                elif rule.rule_id in self._firing:
                    if has_new_observation and measured.value <= rule.resolve_lte:
                        self._firing.discard(rule.rule_id)
                        self._silenced_firing.discard(rule.rule_id)
                        state = "not_firing_provisional"
                        transition = "resolved"
                    else:
                        state = "firing"
                elif has_new_observation and measured.value >= rule.trigger_gte:
                    self._firing.add(rule.rule_id)
                    state = "firing"
                    transition = "triggered"
                else:
                    state = "not_firing_provisional"

                silence = active_silences.get(rule.rule_id)
                was_silenced = rule.rule_id in self._silenced_firing
                if state == "firing" and silence is not None:
                    notification_state = "silenced"
                    self._silenced_firing.add(rule.rule_id)
                elif state == "firing" and (
                    transition == "triggered" or (was_silenced and has_new_observation)
                ):
                    notification_state = "notify"
                    self._silenced_firing.discard(rule.rule_id)
                else:
                    notification_state = "inactive"

                evaluated[rule.rule_id] = {
                    "state": state,
                    "transition": transition,
                    "reason_code": reason_code,
                    "generation": measured.generation,
                    "events_seen": measured.sequence,
                    "sample_size": measured.sample_size,
                    "value": (
                        round(measured.value, 6)
                        if measured.value is not None and rule.unit == "ratio"
                        else measured.value
                    ),
                    "window_truncated": measured.window_truncated,
                    "threshold": {
                        "minimum_samples": rule.minimum_samples,
                        "trigger_gte": rule.trigger_gte,
                        "resolve_lte": rule.resolve_lte,
                        "unit": rule.unit,
                    },
                    "notification": {
                        "state": notification_state,
                        "reason_code": silence.reason_code if silence else None,
                        "until": silence.until if silence else None,
                    },
                }

            state_counts = {
                state: sum(rule["state"] == state for rule in evaluated.values())
                for state in (
                    "insufficient_data",
                    "not_firing_provisional",
                    "firing",
                )
            }
            notification_counts = {
                state: sum(
                    rule["notification"]["state"] == state
                    for rule in evaluated.values()
                )
                for state in ("inactive", "notify", "silenced")
            }
            return {
                "schema_version": 1,
                "policy_version": POLICY_VERSION,
                "policy_status": POLICY_STATUS,
                "scope": "single_process_last_512_events",
                "representative_traffic": False,
                "overall_state": (
                    "firing" if state_counts["firing"] else "insufficient_data"
                ),
                "summary": {
                    "rules": state_counts,
                    "notification_candidates": notification_counts,
                },
                "rules": evaluated,
            }

    def reset(self) -> None:
        with self._lock:
            self._firing.clear()
            self._silenced_firing.clear()
            self._last_positions.clear()
            self._pending_invalid_positions.clear()
            self._last_signatures.clear()
            self._last_evaluation_time = None


local_alert_evaluator = LocalAlertEvaluator()


def evaluate_local_alerts(
    *,
    silences: Iterable[AlertSilence] = (),
    now: datetime | None = None,
) -> dict[str, Any]:
    """Évalue les registres avec l'instance canonique longue durée du processus."""
    return local_alert_evaluator.evaluate(
        collect_local_alert_inputs(),
        silences=silences,
        now=now,
    )


__all__ = [
    "AlertSilence",
    "LocalAlertEvaluator",
    "MAX_SILENCE_DURATION",
    "POLICY_STATUS",
    "POLICY_VERSION",
    "RULE_IDS",
    "SILENCE_REASON_CODES",
    "collect_local_alert_inputs",
    "evaluate_local_alerts",
    "local_alert_evaluator",
]
