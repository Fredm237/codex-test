"""Persistance append-only des décisions de promotion V2."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from sqlalchemy import select

from app.v2_chain.models import V2PromotionReceipt
from app.v2_chain.proof_registry import PUBLIC_PROOF_KEYS, SHADOW_PROOF_KEYS
from app.v2_chain.qualification import (
    RESPONSE_TYPES,
    V2PublicQualificationReport,
    V2ShadowQualificationReport,
)


class V2PromotionReceiptError(ValueError):
    """Le reçu de promotion n'est pas cohérent ou a dérivé."""


@dataclass(frozen=True)
class V2PromotionPersistenceReport:
    schema_version: str
    status: str
    promotion_stage: str
    evaluation_id: str
    receipt_id: int | None
    raw_payload_retained: bool = False


def _canonical(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _json_value(value: object) -> object:
    return json.loads(_canonical(value))


def _digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _valid_digest(value: object) -> bool:
    if not isinstance(value, str) or not value.startswith("sha256:"):
        return False
    suffix = value.removeprefix("sha256:")
    return len(suffix) == 64 and all(
        character in "0123456789abcdef" for character in suffix
    )


def _evaluated_at(value: str) -> datetime:
    if not isinstance(value, str):
        raise V2PromotionReceiptError("evaluated_at is invalid")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise V2PromotionReceiptError("evaluated_at is invalid") from exc
    if parsed.tzinfo is None:
        raise V2PromotionReceiptError("evaluated_at must include a timezone")
    return parsed.astimezone(timezone.utc).replace(tzinfo=None)


def _shadow_values(report: V2ShadowQualificationReport) -> dict[str, object]:
    authorized = (
        sorted(RESPONSE_TYPES - set(report.gate.blocked_response_types))
        if report.gate.status == "CANARY_AUTHORIZED"
        else []
    )
    identity = {
        "evaluated_at": report.evaluated_at,
        "campaign_id": report.campaign_id,
        "metrics": asdict(report.metrics),
        "gate": report.gate.to_dict(),
        "proof_refs": report.proof_refs,
        "maximum_p95_window_ms": report.maximum_p95_window_ms,
    }
    if report.schema_version != "v2-shadow-qualification/v1":
        raise V2PromotionReceiptError("shadow receipt schema is unsupported")
    if report.gate.status not in {"CANARY_HOLD", "CANARY_AUTHORIZED"}:
        raise V2PromotionReceiptError("shadow promotion status is invalid")
    if set(report.proof_refs) != SHADOW_PROOF_KEYS:
        raise V2PromotionReceiptError("shadow proof refs are incomplete")
    if _digest(identity) != report.evaluation_id:
        raise V2PromotionReceiptError("shadow receipt identity drifted")
    return {
        "evaluation_id": report.evaluation_id,
        "gate_evaluation_id": report.gate.evaluation_id,
        "source_gate_evaluation_id": None,
        "promotion_stage": "shadow_to_canary",
        "status": report.gate.status,
        "authorized_response_types_json": authorized,
        "blocked_response_types_json": sorted(RESPONSE_TYPES - set(authorized)),
        "gates_json": _json_value(report.gate.gates),
        "metrics_json": _json_value(asdict(report.metrics)),
        "proof_refs_json": _json_value(report.proof_refs),
        "policy_json": {
            "campaign_id": report.campaign_id,
            "maximum_p95_window_ms": report.maximum_p95_window_ms,
        },
        "raw_payload_retained": False,
        "evaluated_at": _evaluated_at(report.evaluated_at),
    }


def _public_values(report: V2PublicQualificationReport) -> dict[str, object]:
    identity = {
        "evaluated_at": report.evaluated_at,
        "shadow_gate_evaluation_id": report.shadow_gate_evaluation_id,
        "metrics": asdict(report.metrics),
        "gate": report.gate.to_dict(),
        "proof_refs": report.proof_refs,
        "minimum_paired_observations": report.minimum_paired_observations,
        "minimum_observations_per_response_type": (
            report.minimum_observations_per_response_type
        ),
        "requested_response_types": report.requested_response_types,
    }
    if report.schema_version != "v2-public-qualification/v1":
        raise V2PromotionReceiptError("public receipt schema is unsupported")
    if report.gate.status not in {"PUBLIC_HOLD", "PUBLIC_AUTHORIZED"}:
        raise V2PromotionReceiptError("public promotion status is invalid")
    if set(report.proof_refs) != PUBLIC_PROOF_KEYS:
        raise V2PromotionReceiptError("public proof refs are incomplete")
    if _digest(identity) != report.evaluation_id:
        raise V2PromotionReceiptError("public receipt identity drifted")
    return {
        "evaluation_id": report.evaluation_id,
        "gate_evaluation_id": report.gate.evaluation_id,
        "source_gate_evaluation_id": report.shadow_gate_evaluation_id,
        "promotion_stage": "canary_to_public",
        "status": report.gate.status,
        "authorized_response_types_json": list(
            report.gate.authorized_response_types
        ),
        "blocked_response_types_json": list(report.gate.blocked_response_types),
        "gates_json": _json_value(report.gate.gates),
        "metrics_json": _json_value(asdict(report.metrics)),
        "proof_refs_json": _json_value(report.proof_refs),
        "policy_json": {
            "minimum_paired_observations": report.minimum_paired_observations,
            "minimum_observations_per_response_type": (
                report.minimum_observations_per_response_type
            ),
            "requested_response_types": list(report.requested_response_types),
        },
        "raw_payload_retained": False,
        "evaluated_at": _evaluated_at(report.evaluated_at),
    }


def _values(
    report: V2ShadowQualificationReport | V2PublicQualificationReport,
) -> dict[str, object]:
    if isinstance(report, V2ShadowQualificationReport):
        values = _shadow_values(report)
    elif isinstance(report, V2PublicQualificationReport):
        values = _public_values(report)
    else:
        raise V2PromotionReceiptError("promotion receipt type is unsupported")
    digests = (
        values["evaluation_id"],
        values["gate_evaluation_id"],
        values["source_gate_evaluation_id"],
        *values["proof_refs_json"].values(),
    )
    if any(value is not None and not _valid_digest(value) for value in digests):
        raise V2PromotionReceiptError("promotion receipt contains an invalid digest")
    return values


async def record_promotion_receipt(
    session,
    *,
    report: V2ShadowQualificationReport | V2PublicQualificationReport,
    apply: bool = False,
) -> V2PromotionPersistenceReport:
    """Valide puis persiste un reçu sans payload, de façon idempotente."""

    values = _values(report)
    existing = await session.scalar(
        select(V2PromotionReceipt).where(
            V2PromotionReceipt.evaluation_id == values["evaluation_id"]
        )
    )
    if existing is not None:
        if any(getattr(existing, name) != value for name, value in values.items()):
            raise V2PromotionReceiptError("promotion receipt replay drifted")
        return V2PromotionPersistenceReport(
            "v2-promotion-persistence/v1",
            "existing",
            values["promotion_stage"],
            values["evaluation_id"],
            existing.id,
        )
    if not apply:
        return V2PromotionPersistenceReport(
            "v2-promotion-persistence/v1",
            "dry_run",
            values["promotion_stage"],
            values["evaluation_id"],
            None,
        )
    receipt = V2PromotionReceipt(**values)
    session.add(receipt)
    await session.flush()
    return V2PromotionPersistenceReport(
        "v2-promotion-persistence/v1",
        "created",
        values["promotion_stage"],
        values["evaluation_id"],
        receipt.id,
    )
