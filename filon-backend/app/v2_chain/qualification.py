"""Reçu SHADOW → CANARY dérivé des journaux V2 persistés."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from sqlalchemy import select

from app.v2_chain.models import (
    V2CanaryReadObservation,
    V2ChainExecution,
    V2LiveDarkReadObservation,
)
from app.v2_chain.proof_registry import (
    PUBLIC_PROOF_KEYS,
    SHADOW_PROOF_KEYS,
    verify_registered_proofs,
)
from quality_lab.v2_canary import (
    V2CanaryEvidence,
    V2CanaryGateReport,
    evaluate_shadow_to_canary,
)
from quality_lab.v2_public import (
    V2PublicEvidence,
    V2PublicGateReport,
    evaluate_canary_to_public,
)


MAX_QUALIFICATION_ROWS = 10_000
REQUIRED_STAGES = frozenset(
    {
        "product_identity",
        "entity_resolution",
        "offer_graph",
        "merchant_intelligence",
        "evidence_engine",
        "offer_truth",
        "product_ontology",
        "hybrid_retrieval",
        "constraint_engine",
        "product_ranking",
        "offer_optimization",
        "confidence",
        "buy_wait",
    }
)
RESPONSE_TYPES = frozenset({"BUY_NOW", "WAIT", "ABSTAIN"})


class V2QualificationError(ValueError):
    """Les preuves de promotion ne sont pas bornées ou cohérentes."""


@dataclass(frozen=True)
class V2ExternalProofs:
    campaign_id: str
    single_alembic_head_ref: str
    postgresql_migration_ref: str
    expand_only_rollback_ref: str
    replay_idempotence_ref: str
    inherited_benchmarks_ref: str
    safety_invariants_ref: str
    collision_exercise_ref: str
    stale_interruption_ref: str
    recovery_replay_ref: str
    dark_reader_rollback_ref: str
    performance_policy_ref: str
    maximum_p95_window_ms: int

    def __post_init__(self) -> None:
        for name, value in asdict(self).items():
            if name == "maximum_p95_window_ms":
                continue
            if not _valid_digest(value):
                raise V2QualificationError(f"{name} must be a sha256 proof ref")
        if (
            isinstance(self.maximum_p95_window_ms, bool)
            or not isinstance(self.maximum_p95_window_ms, int)
            or self.maximum_p95_window_ms < 1
        ):
            raise V2QualificationError("maximum p95 window must be positive")


@dataclass(frozen=True)
class V2PublicExternalProofs:
    shadow_gate_ref: str
    readiness_and_5xx_ref: str
    failure_injection_ref: str
    rollback_to_shadow_ref: str
    backup_restore_ref: str
    capacity_and_alerting_ref: str
    inherited_regressions_ref: str
    open_blockers_audit_ref: str
    public_policy_ref: str
    minimum_paired_observations: int
    minimum_observations_per_response_type: int
    requested_response_types: tuple[str, ...]

    def __post_init__(self) -> None:
        for name, value in asdict(self).items():
            if name.endswith("_ref") and not _valid_digest(value):
                raise V2QualificationError(f"{name} must be a sha256 proof ref")
        if (
            isinstance(self.minimum_paired_observations, bool)
            or not isinstance(self.minimum_paired_observations, int)
            or not 1 <= self.minimum_paired_observations <= MAX_QUALIFICATION_ROWS
        ):
            raise V2QualificationError("minimum paired observations is invalid")
        if (
            isinstance(self.minimum_observations_per_response_type, bool)
            or not isinstance(self.minimum_observations_per_response_type, int)
            or not 1
            <= self.minimum_observations_per_response_type
            <= MAX_QUALIFICATION_ROWS
        ):
            raise V2QualificationError("minimum response observations is invalid")
        requested = set(self.requested_response_types)
        if (
            not requested
            or len(requested) != len(self.requested_response_types)
            or not requested <= RESPONSE_TYPES
        ):
            raise V2QualificationError("requested response types are invalid")


@dataclass(frozen=True)
class V2QualificationMetrics:
    execution_rows: int
    valid_terminal_windows: int
    active_executions: int
    failed_or_interrupted_executions: int
    cursor_monotone: bool
    non_overlapping_executions: bool
    p95_window_ms: int | None
    dark_observations: int
    dark_eligible: int
    dark_unsupported: int
    dark_complete: int
    dark_invalid: int
    dark_raw_query_retained: int
    observed_response_types: tuple[str, ...]


@dataclass(frozen=True)
class V2ShadowQualificationReport:
    schema_version: str
    evaluated_at: str
    campaign_id: str
    metrics: V2QualificationMetrics
    gate: V2CanaryGateReport
    proof_refs: dict[str, str]
    maximum_p95_window_ms: int
    evaluation_id: str

    def to_dict(self) -> dict[str, object]:
        return json.loads(_canonical(asdict(self)))


@dataclass(frozen=True)
class V2PublicQualificationMetrics:
    canary_observations: int
    paired_observations: int
    v2_served: int
    v2_fallbacks: int
    v2_reader_errors: int
    invalid_or_incomplete: int
    provenance_complete: int
    raw_query_retained: int
    p95_latency_delta_us: int | None
    served_response_types: tuple[str, ...]
    served_response_type_counts: dict[str, int]


@dataclass(frozen=True)
class V2PublicQualificationReport:
    schema_version: str
    evaluated_at: str
    shadow_gate_evaluation_id: str
    metrics: V2PublicQualificationMetrics
    gate: V2PublicGateReport
    proof_refs: dict[str, str]
    minimum_paired_observations: int
    minimum_observations_per_response_type: int
    requested_response_types: tuple[str, ...]
    evaluation_id: str

    def to_dict(self) -> dict[str, object]:
        return json.loads(_canonical(asdict(self)))


def _valid_digest(value: object) -> bool:
    if not isinstance(value, str) or not value.startswith("sha256:"):
        return False
    suffix = value.removeprefix("sha256:")
    return len(suffix) == 64 and all(
        character in "0123456789abcdef" for character in suffix
    )


def _canonical(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _aware(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise V2QualificationError("evaluated_at must include a timezone")
    return value.astimezone(timezone.utc)


def _utc(value: datetime) -> datetime:
    return (
        value.replace(tzinfo=timezone.utc)
        if value.tzinfo is None
        else value.astimezone(timezone.utc)
    )


def _valid_execution(execution: V2ChainExecution) -> bool:
    completed = execution.completed_stages_json or []
    metrics = execution.window_metrics_json or {}
    return (
        execution.mode == "apply"
        and execution.status == "succeeded"
        and execution.finished_at is not None
        and _valid_digest(execution.report_evaluation_id)
        and len(completed) == len(REQUIRED_STAGES)
        and set(completed) == REQUIRED_STAGES
        and execution.last_raw_source_id > execution.after_raw_id
        and metrics.get("schema_version") == "v2-window-metrics/v1"
        and metrics.get("evaluation_identity") == execution.report_evaluation_id
        and metrics.get("errors") == 0
    )


def _progress_windows(
    executions: list[V2ChainExecution],
) -> tuple[list[V2ChainExecution], bool]:
    """Isole les fenêtres réelles sans compter un replay identique deux fois."""

    windows: list[V2ChainExecution] = []
    last_by_vertical: dict[str, int] = {}
    seen: dict[tuple[str, int, int], str] = {}
    for execution in executions:
        if not _valid_execution(execution):
            continue
        bounds = (
            execution.vertical,
            execution.after_raw_id,
            execution.last_raw_source_id,
        )
        previous_report = seen.get(bounds)
        if previous_report is not None:
            if previous_report != execution.report_evaluation_id:
                return windows, False
            continue
        previous_cursor = last_by_vertical.get(execution.vertical)
        if previous_cursor is not None and execution.after_raw_id != previous_cursor:
            return windows, False
        seen[bounds] = execution.report_evaluation_id
        last_by_vertical[execution.vertical] = execution.last_raw_source_id
        windows.append(execution)
    return windows, bool(windows)


def _non_overlapping(executions: list[V2ChainExecution]) -> bool:
    intervals: list[tuple[datetime, datetime]] = []
    for execution in executions:
        if execution.status == "running" or execution.finished_at is None:
            return False
        started = _utc(execution.started_at)
        finished = _utc(execution.finished_at)
        if finished < started:
            return False
        intervals.append((started, finished))
    intervals.sort()
    return all(
        current[0] >= previous[1]
        for previous, current in zip(intervals, intervals[1:])
    )


def _p95_window_ms(executions: list[V2ChainExecution]) -> int | None:
    durations = sorted(
        max(
            0,
            math.ceil(
                (_utc(item.finished_at) - _utc(item.started_at)).total_seconds()
                * 1_000
            ),
        )
        for item in executions
        if _valid_execution(item) and item.finished_at is not None
    )
    if not durations:
        return None
    rank = max(1, math.ceil(len(durations) * 0.95))
    return durations[rank - 1]


def _p95_latency_delta_us(observations: list[object]) -> int | None:
    deltas = sorted(
        item.v2_latency_us - item.core_latency_us
        for item in observations
        if item.v2_latency_us is not None
    )
    if not deltas:
        return None
    rank = max(1, math.ceil(len(deltas) * 0.95))
    return deltas[rank - 1]


def _proof_refs(
    proofs: V2ExternalProofs | V2PublicExternalProofs,
) -> dict[str, str]:
    return {
        name: value
        for name, value in asdict(proofs).items()
        if name.endswith("_ref")
    }


async def evaluate_persisted_shadow_to_canary(
    session,
    *,
    proofs: V2ExternalProofs,
    evaluated_at: datetime,
) -> V2ShadowQualificationReport:
    """Calcule le gate à partir des journaux et de reçus externes digestés."""

    evaluated = _aware(evaluated_at)
    executions = list(
        (
            await session.execute(
                select(V2ChainExecution)
                .where(
                    V2ChainExecution.mode == "apply",
                    V2ChainExecution.campaign_id == proofs.campaign_id,
                    V2ChainExecution.execution_kind.in_(("progression", "recovery")),
                )
                .order_by(V2ChainExecution.id)
                .limit(MAX_QUALIFICATION_ROWS + 1)
            )
        )
        .scalars()
        .all()
    )
    observations = list(
        (
            await session.execute(
                select(V2LiveDarkReadObservation)
                .where(V2LiveDarkReadObservation.campaign_id == proofs.campaign_id)
                .order_by(V2LiveDarkReadObservation.id)
                .limit(MAX_QUALIFICATION_ROWS + 1)
            )
        )
        .scalars()
        .all()
    )
    if (
        len(executions) > MAX_QUALIFICATION_ROWS
        or len(observations) > MAX_QUALIFICATION_ROWS
    ):
        raise V2QualificationError("qualification window exceeds the bounded audit limit")

    progress_windows, cursor_monotone = _progress_windows(executions)
    p95 = _p95_window_ms(progress_windows)
    dark_invalid = sum(item.safety_state == "INVALID" for item in observations)
    dark_raw = sum(item.raw_query_retained is not False for item in observations)
    eligible_observations = [
        item for item in observations if item.v2_outcome != "UNSUPPORTED"
    ]
    dark_complete = sum(item.chain_complete is True for item in eligible_observations)
    observed = tuple(
        sorted(
            {
                item.v2_outcome
                for item in eligible_observations
                if item.chain_complete is True
                and item.safety_state in {"SAFE", "ABSTAIN"}
                and item.v2_outcome in RESPONSE_TYPES
            }
        )
    )
    metrics = V2QualificationMetrics(
        execution_rows=len(executions),
        valid_terminal_windows=len(progress_windows),
        active_executions=sum(item.status == "running" for item in executions),
        failed_or_interrupted_executions=sum(
            item.status in {"failed", "interrupted"} for item in executions
        ),
        cursor_monotone=cursor_monotone,
        non_overlapping_executions=_non_overlapping(executions),
        p95_window_ms=p95,
        dark_observations=len(observations),
        dark_eligible=len(eligible_observations),
        dark_unsupported=len(observations) - len(eligible_observations),
        dark_complete=dark_complete,
        dark_invalid=dark_invalid,
        dark_raw_query_retained=dark_raw,
        observed_response_types=observed,
    )
    refs = _proof_refs(proofs)
    verified = await verify_registered_proofs(
        session,
        scope_ref=proofs.campaign_id,
        proof_refs=refs,
        expected_keys=SHADOW_PROOF_KEYS,
    )
    gate = evaluate_shadow_to_canary(
        V2CanaryEvidence(
            single_alembic_head=verified["single_alembic_head_ref"],
            postgresql_migration_green=verified["postgresql_migration_ref"],
            expand_only_rollback_green=verified["expand_only_rollback_ref"],
            replay_idempotent=verified["replay_idempotence_ref"],
            cursor_monotone=metrics.cursor_monotone,
            single_execution_proven=metrics.non_overlapping_executions,
            inherited_benchmarks_green=verified["inherited_benchmarks_ref"],
            safety_invariants_green=(
                verified["safety_invariants_ref"]
                and dark_invalid == 0
                and dark_raw == 0
            ),
            real_terminal_windows=metrics.valid_terminal_windows,
            performance_distribution_ready=(
                verified["performance_policy_ref"]
                and metrics.valid_terminal_windows >= 30
                and p95 is not None
                and p95 <= proofs.maximum_p95_window_ms
            ),
            collision_exercise_green=verified["collision_exercise_ref"],
            stale_interruption_green=verified["stale_interruption_ref"],
            recovery_replay_green=verified["recovery_replay_ref"],
            dark_reader_qualified=(
                len(eligible_observations) >= 30
                and dark_complete == len(eligible_observations)
                and dark_invalid == 0
                and dark_raw == 0
            ),
            dark_reader_rollback_green=verified["dark_reader_rollback_ref"],
            observed_response_types=observed,
        )
    )
    identity = {
        "evaluated_at": evaluated.isoformat().replace("+00:00", "Z"),
        "campaign_id": proofs.campaign_id,
        "metrics": asdict(metrics),
        "gate": gate.to_dict(),
        "proof_refs": refs,
        "maximum_p95_window_ms": proofs.maximum_p95_window_ms,
    }
    return V2ShadowQualificationReport(
        schema_version="v2-shadow-qualification/v1",
        evaluated_at=identity["evaluated_at"],
        campaign_id=proofs.campaign_id,
        metrics=metrics,
        gate=gate,
        proof_refs=refs,
        maximum_p95_window_ms=proofs.maximum_p95_window_ms,
        evaluation_id=_digest(identity),
    )


async def evaluate_persisted_canary_to_public(
    session,
    *,
    shadow_gate: V2CanaryGateReport,
    proofs: V2PublicExternalProofs,
    evaluated_at: datetime,
) -> V2PublicQualificationReport:
    """Calcule le gate public pour une révision de gate canary précise."""

    evaluated = _aware(evaluated_at)
    if (
        shadow_gate.schema_version != "v2-shadow-to-canary-gate/v1"
        or not _valid_digest(shadow_gate.evaluation_id)
    ):
        raise V2QualificationError("shadow gate evaluation id is invalid")
    if proofs.shadow_gate_ref != shadow_gate.evaluation_id:
        raise V2QualificationError("shadow gate proof does not match candidate")
    refs = _proof_refs(proofs)
    registered_refs = {
        name: value for name, value in refs.items() if name != "shadow_gate_ref"
    }
    verified = await verify_registered_proofs(
        session,
        scope_ref=shadow_gate.evaluation_id,
        proof_refs=registered_refs,
        expected_keys=PUBLIC_PROOF_KEYS - {"shadow_gate_ref"},
    )
    observations = list(
        (
            await session.execute(
                select(V2CanaryReadObservation)
                .where(
                    V2CanaryReadObservation.cohort == "canary",
                    V2CanaryReadObservation.gate_evaluation_id
                    == shadow_gate.evaluation_id,
                )
                .order_by(V2CanaryReadObservation.id)
                .limit(MAX_QUALIFICATION_ROWS + 1)
            )
        )
        .scalars()
        .all()
    )
    if len(observations) > MAX_QUALIFICATION_ROWS:
        raise V2QualificationError("public qualification exceeds the audit limit")
    paired = [item for item in observations if item.v2_latency_us is not None]
    served = [item for item in observations if item.source == "v2"]
    fallbacks = [item for item in observations if item.source == "core_v1"]
    served_type_counts = {
        response_type: sum(item.response_type == response_type for item in served)
        for response_type in sorted({item.response_type for item in served})
    }
    invalid_or_incomplete = sum(
        item.chain_complete is not True
        or item.provenance_complete is not True
        or item.safety_state not in {"SAFE", "ABSTAIN"}
        or item.eligibility_status != "eligible"
        or not _valid_digest(item.eligibility_evaluation_id)
        or not item.vertical
        or not item.locale
        or not item.decision_type
        for item in paired
    )
    metrics = V2PublicQualificationMetrics(
        canary_observations=len(observations),
        paired_observations=len(paired),
        v2_served=len(served),
        v2_fallbacks=len(fallbacks),
        v2_reader_errors=sum(
            item.fallback_reason == "v2_reader_error" for item in observations
        ),
        invalid_or_incomplete=invalid_or_incomplete,
        provenance_complete=sum(
            item.provenance_complete is True for item in served
        ),
        raw_query_retained=sum(
            item.raw_query_retained is not False for item in observations
        ),
        p95_latency_delta_us=_p95_latency_delta_us(paired),
        served_response_types=tuple(
            served_type_counts
        ),
        served_response_type_counts=served_type_counts,
    )
    gate = evaluate_canary_to_public(
        V2PublicEvidence(
            shadow_gate_authorized=(shadow_gate.status == "CANARY_AUTHORIZED"),
            readiness_and_5xx_green=verified["readiness_and_5xx_ref"],
            minimum_paired_observations=proofs.minimum_paired_observations,
            minimum_observations_per_response_type=(
                proofs.minimum_observations_per_response_type
            ),
            paired_observations=metrics.paired_observations,
            p95_latency_delta_us=metrics.p95_latency_delta_us,
            v2_fallbacks=metrics.v2_fallbacks,
            v2_reader_errors=metrics.v2_reader_errors,
            invalid_or_incomplete=metrics.invalid_or_incomplete,
            raw_query_retained=metrics.raw_query_retained,
            v2_served=metrics.v2_served,
            provenance_complete=metrics.provenance_complete,
            requested_response_types=proofs.requested_response_types,
            served_response_types=metrics.served_response_types,
            served_response_type_counts=metrics.served_response_type_counts,
            failure_injection_green=verified["failure_injection_ref"],
            rollback_to_shadow_green=verified["rollback_to_shadow_ref"],
            backup_restore_green=verified["backup_restore_ref"],
            capacity_and_alerting_green=verified["capacity_and_alerting_ref"],
            inherited_regressions_green=verified["inherited_regressions_ref"],
            no_integrity_recovery_security_blocker=(
                verified["open_blockers_audit_ref"]
                and verified["public_policy_ref"]
            ),
        )
    )
    identity = {
        "evaluated_at": evaluated.isoformat().replace("+00:00", "Z"),
        "shadow_gate_evaluation_id": shadow_gate.evaluation_id,
        "metrics": asdict(metrics),
        "gate": gate.to_dict(),
        "proof_refs": refs,
        "minimum_paired_observations": proofs.minimum_paired_observations,
        "minimum_observations_per_response_type": (
            proofs.minimum_observations_per_response_type
        ),
        "requested_response_types": proofs.requested_response_types,
    }
    return V2PublicQualificationReport(
        schema_version="v2-public-qualification/v1",
        evaluated_at=identity["evaluated_at"],
        shadow_gate_evaluation_id=shadow_gate.evaluation_id,
        metrics=metrics,
        gate=gate,
        proof_refs=refs,
        minimum_paired_observations=proofs.minimum_paired_observations,
        minimum_observations_per_response_type=(
            proofs.minimum_observations_per_response_type
        ),
        requested_response_types=proofs.requested_response_types,
        evaluation_id=_digest(identity),
    )
