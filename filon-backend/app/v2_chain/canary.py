"""Routage canary atomique et réversible, non raccordé aux routes publiques."""

from __future__ import annotations

import time
import hashlib
import json
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import Any

from quality_lab.v2_canary import V2CanaryGateReport


class V2CanaryError(ValueError):
    """Le contrat du lecteur canary est invalide."""


@dataclass(frozen=True)
class CanaryAssignment:
    cohort: str
    reason_code: str


@dataclass(frozen=True)
class V2CanaryEligibilityPolicy:
    """Périmètre fonctionnel fermé autorisé pour un canary."""

    policy_id: str
    supported_verticals: tuple[str, ...]
    supported_locales: tuple[str, ...]
    supported_decision_types: tuple[str, ...]
    maximum_data_age_seconds: int


@dataclass(frozen=True)
class V2CanaryEligibilityEvidence:
    """Preuves calculées pour une requête, sans contexte personnel brut."""

    vertical: str
    locale: str
    decision_type: str
    data_age_seconds: int | None
    dependencies_admissible: bool
    critical_unknown: bool
    hard_constraint_violation: bool
    confidence_required: bool
    confidence_admissible: bool
    rollback_available: bool


@dataclass(frozen=True)
class V2CanaryEligibilityDecision:
    schema_version: str
    eligible: bool
    reason_code: str
    vertical: str
    locale: str
    decision_type: str
    evaluation_id: str


@dataclass(frozen=True)
class V2CanaryPayload:
    response: Mapping[str, Any]
    chain_complete: bool
    safety_state: str
    provenance_complete: bool
    response_type: str


@dataclass(frozen=True)
class CanaryReadReceipt:
    schema_version: str
    source: str
    response_type: str
    fallback_reason: str | None
    gate_evaluation_id: str
    cohort: str
    assignment_reason: str
    eligibility_evaluation_id: str
    eligibility_status: str
    vertical: str
    locale: str
    decision_type: str
    core_latency_us: int
    v2_latency_us: int | None
    total_latency_us: int
    chain_complete: bool | None
    safety_state: str | None
    provenance_complete: bool | None
    raw_query_retained: bool = False


@dataclass(frozen=True)
class CanaryReadResult:
    response: Mapping[str, Any]
    receipt: CanaryReadReceipt


def _valid_digest(value: str) -> bool:
    if not isinstance(value, str) or not value.startswith("sha256:"):
        return False
    digest = value.removeprefix("sha256:")
    return len(digest) == 64 and all(character in "0123456789abcdef" for character in digest)


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _valid_token(value: object, *, maximum: int = 32) -> bool:
    return (
        isinstance(value, str)
        and 1 <= len(value) <= maximum
        and all(character.isalnum() or character in {"_", "-"} for character in value)
    )


def _validate_policy(policy: V2CanaryEligibilityPolicy) -> None:
    if not _valid_digest(policy.policy_id):
        raise V2CanaryError("canary eligibility policy id is invalid")
    dimensions = (
        ("verticals", policy.supported_verticals, 32),
        ("locales", policy.supported_locales, 8),
        ("decision types", policy.supported_decision_types, 32),
    )
    for label, values, maximum in dimensions:
        if not values or len(set(values)) != len(values):
            raise V2CanaryError(f"canary supported {label} are invalid")
        if any(not _valid_token(value, maximum=maximum) for value in values):
            raise V2CanaryError(f"canary supported {label} are invalid")
    if (
        isinstance(policy.maximum_data_age_seconds, bool)
        or not isinstance(policy.maximum_data_age_seconds, int)
        or policy.maximum_data_age_seconds < 1
    ):
        raise V2CanaryError("canary maximum data age is invalid")


def evaluate_canary_eligibility(
    *,
    policy: V2CanaryEligibilityPolicy,
    evidence: V2CanaryEligibilityEvidence,
) -> V2CanaryEligibilityDecision:
    """Autorise uniquement une requête entièrement prouvée dans le périmètre."""

    _validate_policy(policy)
    if not _valid_token(evidence.vertical):
        raise V2CanaryError("canary evidence vertical is invalid")
    if not _valid_token(evidence.locale, maximum=8):
        raise V2CanaryError("canary evidence locale is invalid")
    if not _valid_token(evidence.decision_type):
        raise V2CanaryError("canary evidence decision type is invalid")
    if evidence.data_age_seconds is not None and (
        isinstance(evidence.data_age_seconds, bool)
        or not isinstance(evidence.data_age_seconds, int)
        or evidence.data_age_seconds < 0
    ):
        raise V2CanaryError("canary evidence data age is invalid")

    checks = (
        (evidence.vertical in policy.supported_verticals, "vertical_unsupported"),
        (evidence.locale in policy.supported_locales, "locale_unsupported"),
        (
            evidence.decision_type in policy.supported_decision_types,
            "decision_type_unsupported",
        ),
        (evidence.dependencies_admissible, "dependencies_not_admissible"),
        (
            evidence.data_age_seconds is not None
            and evidence.data_age_seconds <= policy.maximum_data_age_seconds,
            "data_not_fresh",
        ),
        (not evidence.critical_unknown, "critical_unknown"),
        (not evidence.hard_constraint_violation, "hard_constraint_violation"),
        (
            not evidence.confidence_required or evidence.confidence_admissible,
            "confidence_not_admissible",
        ),
        (evidence.rollback_available, "rollback_unavailable"),
    )
    reason = next((code for passed, code in checks if not passed), "eligible")
    identity = {
        "policy": asdict(policy),
        "evidence": asdict(evidence),
        "eligible": reason == "eligible",
        "reason_code": reason,
    }
    return V2CanaryEligibilityDecision(
        schema_version="v2-canary-eligibility-decision/v1",
        eligible=reason == "eligible",
        reason_code=reason,
        vertical=evidence.vertical,
        locale=evidence.locale,
        decision_type=evidence.decision_type,
        evaluation_id=_digest(identity),
    )


def _elapsed_us(started_ns: int, finished_ns: int) -> int:
    return max(0, (finished_ns - started_ns) // 1_000)


def _receipt(
    *,
    source: str,
    response_type: str,
    fallback_reason: str | None,
    assignment: CanaryAssignment,
    eligibility: V2CanaryEligibilityDecision,
    gate: V2CanaryGateReport,
    started_ns: int,
    core_finished_ns: int,
    finished_ns: int,
    v2_started_ns: int | None = None,
    payload: V2CanaryPayload | None = None,
) -> CanaryReadReceipt:
    return CanaryReadReceipt(
        schema_version="v2-canary-read-receipt/v1",
        source=source,
        response_type=response_type,
        fallback_reason=fallback_reason,
        gate_evaluation_id=gate.evaluation_id,
        cohort=assignment.cohort,
        assignment_reason=assignment.reason_code,
        eligibility_evaluation_id=eligibility.evaluation_id,
        eligibility_status="eligible" if eligibility.eligible else "ineligible",
        vertical=eligibility.vertical,
        locale=eligibility.locale,
        decision_type=eligibility.decision_type,
        core_latency_us=_elapsed_us(started_ns, core_finished_ns),
        v2_latency_us=(
            _elapsed_us(v2_started_ns, finished_ns)
            if v2_started_ns is not None
            else None
        ),
        total_latency_us=_elapsed_us(started_ns, finished_ns),
        chain_complete=payload.chain_complete if payload is not None else None,
        safety_state=payload.safety_state if payload is not None else None,
        provenance_complete=(
            payload.provenance_complete if payload is not None else None
        ),
    )


def assign_closed_cohort(
    *,
    subject_digest: str | None,
    allowed_subject_digests: Sequence[str],
) -> CanaryAssignment:
    """Assigne seulement une identité pseudonymisée explicitement autorisée."""

    if len(set(allowed_subject_digests)) != len(allowed_subject_digests):
        raise V2CanaryError("canary allowlist contains duplicates")
    if any(not _valid_digest(value) for value in allowed_subject_digests):
        raise V2CanaryError("canary allowlist digest is invalid")
    if subject_digest is None:
        return CanaryAssignment("core", "subject_absent")
    if not _valid_digest(subject_digest):
        return CanaryAssignment("core", "subject_invalid")
    return (
        CanaryAssignment("canary", "closed_cohort_match")
        if subject_digest in allowed_subject_digests
        else CanaryAssignment("core", "outside_closed_cohort")
    )


def _can_serve_v2(
    *,
    assignment: CanaryAssignment,
    eligibility: V2CanaryEligibilityDecision,
    gate: V2CanaryGateReport,
    payload: V2CanaryPayload,
) -> str | None:
    if assignment.cohort != "canary":
        return assignment.reason_code
    if not eligibility.eligible:
        return eligibility.reason_code
    if gate.status != "CANARY_AUTHORIZED":
        return "gate_not_authorized"
    if payload.response_type in gate.blocked_response_types:
        return "response_type_not_qualified"
    if not payload.chain_complete:
        return "chain_incomplete"
    if payload.safety_state not in {"SAFE", "ABSTAIN"}:
        return "safety_state_not_servable"
    if not payload.provenance_complete:
        return "provenance_incomplete"
    if not isinstance(payload.response, Mapping):
        return "response_invalid"
    return None


async def run_canary_read(
    *,
    assignment: CanaryAssignment,
    eligibility: V2CanaryEligibilityDecision,
    gate: V2CanaryGateReport,
    core_reader: Callable[[], Awaitable[Mapping[str, Any]]],
    v2_reader: Callable[[], Awaitable[V2CanaryPayload]],
    clock_ns: Callable[[], int] = time.perf_counter_ns,
) -> CanaryReadResult:
    """Calcule toujours Core et ne remplace sa réponse que par un bloc V2 entier."""

    started_ns = clock_ns()
    core_response = await core_reader()
    core_finished_ns = clock_ns()
    if not isinstance(core_response, Mapping):
        raise V2CanaryError("Core reader response is invalid")
    if not _valid_digest(eligibility.evaluation_id):
        raise V2CanaryError("canary eligibility decision is invalid")
    if (
        assignment.cohort != "canary"
        or not eligibility.eligible
        or gate.status != "CANARY_AUTHORIZED"
    ):
        fallback = (
            assignment.reason_code
            if assignment.cohort != "canary"
            else eligibility.reason_code
            if not eligibility.eligible
            else "gate_not_authorized"
        )
        return CanaryReadResult(
            response=core_response,
            receipt=_receipt(
                source="core_v1",
                response_type="CORE",
                fallback_reason=fallback,
                assignment=assignment,
                eligibility=eligibility,
                gate=gate,
                started_ns=started_ns,
                core_finished_ns=core_finished_ns,
                finished_ns=core_finished_ns,
            ),
        )

    v2_started_ns = clock_ns()
    try:
        payload = await v2_reader()
    except Exception:
        finished_ns = clock_ns()
        return CanaryReadResult(
            response=core_response,
            receipt=_receipt(
                source="core_v1",
                response_type="CORE",
                fallback_reason="v2_reader_error",
                assignment=assignment,
                eligibility=eligibility,
                gate=gate,
                started_ns=started_ns,
                core_finished_ns=core_finished_ns,
                v2_started_ns=v2_started_ns,
                finished_ns=finished_ns,
            ),
        )
    finished_ns = clock_ns()
    fallback = _can_serve_v2(
        assignment=assignment,
        eligibility=eligibility,
        gate=gate,
        payload=payload,
    )
    if fallback is not None:
        return CanaryReadResult(
            response=core_response,
            receipt=_receipt(
                source="core_v1",
                response_type="CORE",
                fallback_reason=fallback,
                assignment=assignment,
                eligibility=eligibility,
                gate=gate,
                started_ns=started_ns,
                core_finished_ns=core_finished_ns,
                v2_started_ns=v2_started_ns,
                finished_ns=finished_ns,
                payload=payload,
            ),
        )
    return CanaryReadResult(
        response=payload.response,
        receipt=_receipt(
            source="v2",
            response_type=payload.response_type,
            fallback_reason=None,
            assignment=assignment,
            eligibility=eligibility,
            gate=gate,
            started_ns=started_ns,
            core_finished_ns=core_finished_ns,
            v2_started_ns=v2_started_ns,
            finished_ns=finished_ns,
            payload=payload,
        ),
    )
