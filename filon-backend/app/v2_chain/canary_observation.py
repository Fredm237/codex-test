"""Persistance bornée des lectures canary, sans requête ni identité."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select

from app.v2_chain.canary import CanaryReadReceipt
from app.v2_chain.models import V2CanaryReadObservation


CANARY_OBSERVATION_VERSION = "v2-canary-observation/v1"


class V2CanaryObservationError(ValueError):
    """Le reçu canary n'est pas suffisamment sûr pour être persisté."""


@dataclass(frozen=True)
class V2CanaryObservationReport:
    schema_version: str
    status: str
    observation_key: str
    observation_id: int | None
    source: str
    response_type: str
    raw_query_retained: bool = False


def _digest(value: str) -> bool:
    if not isinstance(value, str) or not value.startswith("sha256:"):
        return False
    suffix = value.removeprefix("sha256:")
    return len(suffix) == 64 and all(character in "0123456789abcdef" for character in suffix)


def _observation_key(value: str) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _aware(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise V2CanaryObservationError("evaluated_at must include a timezone")
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def _validate(receipt: CanaryReadReceipt) -> None:
    if receipt.schema_version != "v2-canary-read-receipt/v1":
        raise V2CanaryObservationError("receipt schema is unsupported")
    if not _digest(receipt.gate_evaluation_id):
        raise V2CanaryObservationError("gate evaluation id is invalid")
    if not _digest(receipt.eligibility_evaluation_id):
        raise V2CanaryObservationError("eligibility evaluation id is invalid")
    if receipt.eligibility_status not in {"eligible", "ineligible"}:
        raise V2CanaryObservationError("eligibility status is invalid")
    if any(
        not isinstance(value, str) or not value or len(value) > maximum
        for value, maximum in (
            (receipt.vertical, 32),
            (receipt.locale, 8),
            (receipt.decision_type, 32),
        )
    ):
        raise V2CanaryObservationError("eligibility dimensions are invalid")
    if receipt.cohort not in {"core", "canary"}:
        raise V2CanaryObservationError("cohort is invalid")
    if not receipt.assignment_reason or len(receipt.assignment_reason) > 64:
        raise V2CanaryObservationError("assignment reason is invalid")
    if receipt.source not in {"core_v1", "v2"}:
        raise V2CanaryObservationError("source is invalid")
    if receipt.response_type not in {"CORE", "ABSTAIN", "BUY_NOW", "WAIT"}:
        raise V2CanaryObservationError("response type is invalid")
    latencies = (receipt.core_latency_us, receipt.total_latency_us)
    if any(
        isinstance(value, bool) or not isinstance(value, int) or value < 0
        for value in latencies
    ):
        raise V2CanaryObservationError("latency is invalid")
    if receipt.v2_latency_us is not None and (
        isinstance(receipt.v2_latency_us, bool)
        or not isinstance(receipt.v2_latency_us, int)
        or receipt.v2_latency_us < 0
    ):
        raise V2CanaryObservationError("V2 latency is invalid")
    minimum_total = receipt.core_latency_us + (receipt.v2_latency_us or 0)
    if receipt.total_latency_us < minimum_total:
        raise V2CanaryObservationError("total latency is inconsistent")
    if receipt.raw_query_retained is not False:
        raise V2CanaryObservationError("raw query retention is forbidden")
    if receipt.source == "v2":
        if (
            receipt.cohort != "canary"
            or receipt.eligibility_status != "eligible"
            or receipt.response_type == "CORE"
            or receipt.fallback_reason is not None
            or receipt.v2_latency_us is None
            or receipt.chain_complete is not True
            or receipt.safety_state not in {"SAFE", "ABSTAIN"}
            or receipt.provenance_complete is not True
        ):
            raise V2CanaryObservationError("V2 receipt is not atomically servable")
    elif receipt.response_type != "CORE" or not receipt.fallback_reason:
        raise V2CanaryObservationError("Core fallback receipt is incomplete")
    optional_states = (
        receipt.chain_complete,
        receipt.safety_state,
        receipt.provenance_complete,
    )
    if receipt.v2_latency_us is None and any(value is not None for value in optional_states):
        raise V2CanaryObservationError("V2 state exists without a V2 attempt")
    if receipt.safety_state not in {None, "SAFE", "ABSTAIN", "INVALID"}:
        raise V2CanaryObservationError("safety state is invalid")


def _values(receipt: CanaryReadReceipt, evaluated_at: datetime) -> dict[str, object]:
    return {
        "gate_evaluation_id": receipt.gate_evaluation_id,
        "cohort": receipt.cohort,
        "assignment_reason": receipt.assignment_reason,
        "eligibility_evaluation_id": receipt.eligibility_evaluation_id,
        "eligibility_status": receipt.eligibility_status,
        "vertical": receipt.vertical,
        "locale": receipt.locale,
        "decision_type": receipt.decision_type,
        "source": receipt.source,
        "response_type": receipt.response_type,
        "fallback_reason": receipt.fallback_reason,
        "core_latency_us": receipt.core_latency_us,
        "v2_latency_us": receipt.v2_latency_us,
        "total_latency_us": receipt.total_latency_us,
        "chain_complete": receipt.chain_complete,
        "safety_state": receipt.safety_state,
        "provenance_complete": receipt.provenance_complete,
        "raw_query_retained": False,
        "evaluated_at": _aware(evaluated_at),
    }


async def record_canary_read(
    session,
    *,
    observation_key: str,
    receipt: CanaryReadReceipt,
    evaluated_at: datetime,
    apply: bool = False,
) -> V2CanaryObservationReport:
    """Valide puis persiste un reçu idempotent, sans donnée de requête."""

    if not _observation_key(observation_key):
        raise V2CanaryObservationError("observation key is invalid")
    _validate(receipt)
    values = _values(receipt, evaluated_at)
    existing = await session.scalar(
        select(V2CanaryReadObservation).where(
            V2CanaryReadObservation.observation_key == observation_key
        )
    )
    if existing is not None:
        if any(getattr(existing, name) != value for name, value in values.items()):
            raise V2CanaryObservationError("observation replay drifted")
        return V2CanaryObservationReport(
            CANARY_OBSERVATION_VERSION,
            "existing",
            observation_key,
            existing.id,
            receipt.source,
            receipt.response_type,
        )
    if not apply:
        return V2CanaryObservationReport(
            CANARY_OBSERVATION_VERSION,
            "dry_run",
            observation_key,
            None,
            receipt.source,
            receipt.response_type,
        )
    observation = V2CanaryReadObservation(
        observation_key=observation_key,
        **values,
    )
    session.add(observation)
    await session.flush()
    return V2CanaryObservationReport(
        CANARY_OBSERVATION_VERSION,
        "created",
        observation_key,
        observation.id,
        receipt.source,
        receipt.response_type,
    )
