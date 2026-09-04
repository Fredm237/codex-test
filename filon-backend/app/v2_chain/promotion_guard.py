"""Autorisation runtime des modes V2 promus à partir des reçus persistés.

La configuration ne constitue jamais une preuve de promotion. Ce garde exige
le reçu append-only exact désigné par le déploiement, revérifie sa structure et,
pour PUBLIC, sa filiation avec un reçu SHADOW → CANARY autorisé.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select

from app.core.config import Settings
from app.v2_chain.models import V2PromotionReceipt
from app.v2_chain.proof_registry import verify_registered_proofs
from app.v2_chain.promotion_receipt import PUBLIC_PROOF_KEYS, SHADOW_PROOF_KEYS
from app.v2_chain.qualification import RESPONSE_TYPES
from quality_lab.v2_canary import V2CanaryGateReport


CANARY_GATES = frozenset(
    {
        "migration_and_rollback",
        "idempotent_chain_replay",
        "monotone_single_execution",
        "inherited_benchmarks",
        "safety_invariants",
        "thirty_terminal_windows",
        "performance_distribution",
        "recovery_exercises",
        "dark_reader",
        "dark_reader_rollback",
    }
)
PUBLIC_GATES = frozenset(
    {
        "shadow_gate",
        "runtime_health",
        "safety_invariants",
        "paired_sample",
        "latency_non_inferiority",
        "error_non_inferiority",
        "provenance",
        "response_type_coverage",
        "failure_injection",
        "rollback_to_shadow",
        "operations",
        "regressions_and_blockers",
    }
)


class V2PromotionGuardError(RuntimeError):
    """Le déploiement ne possède pas une preuve suffisante pour lire V2."""


@dataclass(frozen=True)
class V2RuntimeAuthorization:
    schema_version: str
    mode: str
    promotion_stage: str
    receipt_evaluation_id: str
    gate_evaluation_id: str
    authorized_response_types: tuple[str, ...]
    canary_subjects: int
    raw_payload_retained: bool = False


def _valid_digest(value: object) -> bool:
    if not isinstance(value, str) or not value.startswith("sha256:"):
        return False
    digest = value.removeprefix("sha256:")
    return len(digest) == 64 and all(
        character in "0123456789abcdef" for character in digest
    )


def _validate_partition(receipt: V2PromotionReceipt) -> tuple[str, ...]:
    authorized = receipt.authorized_response_types_json
    blocked = receipt.blocked_response_types_json
    if not isinstance(authorized, list) or not isinstance(blocked, list):
        raise V2PromotionGuardError("promotion response-type partition is invalid")
    if any(not isinstance(value, str) for value in (*authorized, *blocked)):
        raise V2PromotionGuardError("promotion response-type partition is invalid")
    if len(set(authorized)) != len(authorized) or len(set(blocked)) != len(blocked):
        raise V2PromotionGuardError("promotion response-type partition has duplicates")
    authorized_set = set(authorized)
    blocked_set = set(blocked)
    if (
        not authorized_set
        or authorized_set & blocked_set
        or authorized_set | blocked_set != RESPONSE_TYPES
    ):
        raise V2PromotionGuardError("promotion response-type partition is incomplete")
    return tuple(sorted(authorized_set))


def _validate_receipt(
    receipt: V2PromotionReceipt,
    *,
    stage: str,
    status: str,
    gate_names: frozenset[str],
    proof_names: frozenset[str],
) -> tuple[str, ...]:
    if receipt.promotion_stage != stage or receipt.status != status:
        raise V2PromotionGuardError("promotion receipt is not authorized for this mode")
    if receipt.raw_payload_retained is not False:
        raise V2PromotionGuardError("promotion receipt retained a raw payload")
    if not _valid_digest(receipt.evaluation_id) or not _valid_digest(
        receipt.gate_evaluation_id
    ):
        raise V2PromotionGuardError("promotion receipt digest is invalid")
    if (
        not isinstance(receipt.gates_json, dict)
        or set(receipt.gates_json) != gate_names
        or any(value is not True for value in receipt.gates_json.values())
    ):
        raise V2PromotionGuardError("promotion gates are incomplete")
    if (
        not isinstance(receipt.proof_refs_json, dict)
        or set(receipt.proof_refs_json) != proof_names
        or any(not _valid_digest(value) for value in receipt.proof_refs_json.values())
    ):
        raise V2PromotionGuardError("promotion proof references are incomplete")
    return _validate_partition(receipt)


async def _require_registered_proofs(
    session,
    *,
    receipt: V2PromotionReceipt,
    scope_ref: str,
    proof_names: frozenset[str],
) -> None:
    registered_names = proof_names - {"shadow_gate_ref"}
    refs = {
        name: receipt.proof_refs_json[name]
        for name in registered_names
    }
    try:
        verified = await verify_registered_proofs(
            session,
            scope_ref=scope_ref,
            proof_refs=refs,
            expected_keys=registered_names,
        )
    except ValueError as exc:
        raise V2PromotionGuardError("promotion proof registry is invalid") from exc
    if not all(verified.values()):
        raise V2PromotionGuardError("promotion proof is absent or unverified")


async def authorize_v2_runtime(
    session,
    *,
    settings: Settings,
) -> V2RuntimeAuthorization:
    """Retourne l'autorisation exacte ou échoue fermé avant toute lecture V2."""

    mode = settings.v2_chain_mode
    if mode not in {"canary", "public"}:
        raise V2PromotionGuardError("V2 runtime authorization requires a promoted mode")
    evaluation_id = settings.v2_promotion_receipt_evaluation_id
    if not _valid_digest(evaluation_id):
        raise V2PromotionGuardError("configured promotion receipt digest is invalid")
    receipt = await session.scalar(
        select(V2PromotionReceipt).where(
            V2PromotionReceipt.evaluation_id == evaluation_id
        )
    )
    if receipt is None:
        raise V2PromotionGuardError("configured promotion receipt is absent")

    if mode == "canary":
        authorized = _validate_receipt(
            receipt,
            stage="shadow_to_canary",
            status="CANARY_AUTHORIZED",
            gate_names=CANARY_GATES,
            proof_names=SHADOW_PROOF_KEYS,
        )
        if receipt.policy_json.get("campaign_id") != settings.v2_chain_campaign_id:
            raise V2PromotionGuardError("canary receipt campaign drifted")
        await _require_registered_proofs(
            session,
            receipt=receipt,
            scope_ref=settings.v2_chain_campaign_id,
            proof_names=SHADOW_PROOF_KEYS,
        )
        canary_subjects = len(settings.v2_canary_subject_digests_list)
        if canary_subjects < 1:
            raise V2PromotionGuardError("canary cohort is empty")
    else:
        authorized = _validate_receipt(
            receipt,
            stage="canary_to_public",
            status="PUBLIC_AUTHORIZED",
            gate_names=PUBLIC_GATES,
            proof_names=PUBLIC_PROOF_KEYS,
        )
        source_gate = receipt.source_gate_evaluation_id
        if not _valid_digest(source_gate):
            raise V2PromotionGuardError("public receipt has no valid canary lineage")
        if receipt.proof_refs_json.get("shadow_gate_ref") != source_gate:
            raise V2PromotionGuardError("public receipt canary lineage drifted")
        source = await session.scalar(
            select(V2PromotionReceipt).where(
                V2PromotionReceipt.promotion_stage == "shadow_to_canary",
                V2PromotionReceipt.status == "CANARY_AUTHORIZED",
                V2PromotionReceipt.gate_evaluation_id == source_gate,
            )
            .order_by(
                V2PromotionReceipt.evaluated_at.desc(),
                V2PromotionReceipt.id.desc(),
            )
            .limit(1)
        )
        if source is None:
            raise V2PromotionGuardError("authorized canary lineage is absent")
        source_authorized = _validate_receipt(
            source,
            stage="shadow_to_canary",
            status="CANARY_AUTHORIZED",
            gate_names=CANARY_GATES,
            proof_names=SHADOW_PROOF_KEYS,
        )
        if source.policy_json.get("campaign_id") != settings.v2_chain_campaign_id:
            raise V2PromotionGuardError("public canary lineage campaign drifted")
        await _require_registered_proofs(
            session,
            receipt=receipt,
            scope_ref=source_gate,
            proof_names=PUBLIC_PROOF_KEYS,
        )
        await _require_registered_proofs(
            session,
            receipt=source,
            scope_ref=settings.v2_chain_campaign_id,
            proof_names=SHADOW_PROOF_KEYS,
        )
        if not set(authorized) <= set(source_authorized):
            raise V2PromotionGuardError(
                "public response types exceed the authorized canary lineage"
            )
        canary_subjects = 0

    return V2RuntimeAuthorization(
        schema_version="v2-runtime-authorization/v1",
        mode=mode,
        promotion_stage=receipt.promotion_stage,
        receipt_evaluation_id=receipt.evaluation_id,
        gate_evaluation_id=receipt.gate_evaluation_id,
        authorized_response_types=authorized,
        canary_subjects=canary_subjects,
    )


async def load_authorized_canary_gate(
    session,
    *,
    receipt_evaluation_id: str,
) -> V2CanaryGateReport:
    """Reconstruit le gate canary exact depuis son reçu externe autorisé."""

    if not _valid_digest(receipt_evaluation_id):
        raise V2PromotionGuardError("canary receipt evaluation digest is invalid")
    receipt = await session.scalar(
        select(V2PromotionReceipt).where(
            V2PromotionReceipt.evaluation_id == receipt_evaluation_id
        )
    )
    if receipt is None:
        raise V2PromotionGuardError("canary receipt is absent")
    authorized = _validate_receipt(
        receipt,
        stage="shadow_to_canary",
        status="CANARY_AUTHORIZED",
        gate_names=CANARY_GATES,
        proof_names=SHADOW_PROOF_KEYS,
    )
    campaign_id = receipt.policy_json.get("campaign_id")
    if not _valid_digest(campaign_id):
        raise V2PromotionGuardError("canary receipt campaign is invalid")
    await _require_registered_proofs(
        session,
        receipt=receipt,
        scope_ref=campaign_id,
        proof_names=SHADOW_PROOF_KEYS,
    )
    blocked = tuple(sorted(RESPONSE_TYPES - set(authorized)))
    return V2CanaryGateReport(
        schema_version="v2-shadow-to-canary-gate/v1",
        status="CANARY_AUTHORIZED",
        gates=dict(receipt.gates_json),
        blocked_response_types=blocked,
        blocker_codes=tuple(
            f"RESPONSE_TYPE_OFF:{response_type}" for response_type in blocked
        ),
        evaluation_id=receipt.gate_evaluation_id,
    )
