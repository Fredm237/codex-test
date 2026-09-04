"""Registre append-only des preuves externes utilisées par les gates V2."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from sqlalchemy import select

from app.v2_chain.models import V2PromotionProof


SHADOW_PROOF_KEYS = frozenset(
    {
        "single_alembic_head_ref",
        "postgresql_migration_ref",
        "expand_only_rollback_ref",
        "replay_idempotence_ref",
        "inherited_benchmarks_ref",
        "safety_invariants_ref",
        "collision_exercise_ref",
        "stale_interruption_ref",
        "recovery_replay_ref",
        "dark_reader_rollback_ref",
        "performance_policy_ref",
    }
)
PUBLIC_PROOF_KEYS = frozenset(
    {
        "shadow_gate_ref",
        "readiness_and_5xx_ref",
        "failure_injection_ref",
        "rollback_to_shadow_ref",
        "backup_restore_ref",
        "capacity_and_alerting_ref",
        "inherited_regressions_ref",
        "open_blockers_audit_ref",
        "public_policy_ref",
    }
)
REGISTERED_PROOF_KEYS = SHADOW_PROOF_KEYS | (PUBLIC_PROOF_KEYS - {"shadow_gate_ref"})
_ARTIFACT_PREFIXES = (
    "ci:",
    "doc:",
    "github:",
    "migration:",
    "policy:",
    "railway:",
    "receipt:",
    "test:",
)
_VERIFIER_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")


class V2PromotionProofError(ValueError):
    """Une preuve externe n'est pas sûre, vérifiable ou cohérente."""


@dataclass(frozen=True)
class V2PromotionProofPersistenceReport:
    schema_version: str
    status: str
    proof_ref: str
    proof_kind: str
    scope_ref: str
    proof_id: int | None
    raw_payload_retained: bool = False


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _valid_digest(value: object) -> bool:
    if not isinstance(value, str) or not value.startswith("sha256:"):
        return False
    suffix = value.removeprefix("sha256:")
    return len(suffix) == 64 and all(character in "0123456789abcdef" for character in suffix)


def _verified_at(value: datetime) -> tuple[datetime, str]:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise V2PromotionProofError("verified_at must include a timezone")
    aware = value.astimezone(timezone.utc)
    return aware.replace(tzinfo=None), aware.isoformat().replace("+00:00", "Z")


def _validated_values(
    *,
    scope_ref: str,
    proof_kind: str,
    artifact_ref: str,
    artifact_digest: str,
    verifier_version: str,
    verification_status: str,
    verified_at: datetime,
) -> dict[str, object]:
    if not _valid_digest(scope_ref):
        raise V2PromotionProofError("scope_ref must be a sha256 digest")
    if proof_kind not in REGISTERED_PROOF_KEYS:
        raise V2PromotionProofError("proof_kind is unsupported")
    if (
        not isinstance(artifact_ref, str)
        or not artifact_ref.startswith(_ARTIFACT_PREFIXES)
        or not 3 <= len(artifact_ref) <= 512
        or any(ord(character) < 32 for character in artifact_ref)
    ):
        raise V2PromotionProofError("artifact_ref is not an approved safe locator")
    if not _valid_digest(artifact_digest):
        raise V2PromotionProofError("artifact_digest must be a sha256 digest")
    if not isinstance(verifier_version, str) or not _VERIFIER_RE.fullmatch(verifier_version):
        raise V2PromotionProofError("verifier_version is invalid")
    normalized_status = verification_status.upper()
    if normalized_status not in {"VERIFIED", "REJECTED"}:
        raise V2PromotionProofError("verification_status is invalid")
    stored_at, canonical_at = _verified_at(verified_at)
    identity = {
        "scope_ref": scope_ref,
        "proof_kind": proof_kind,
        "artifact_ref": artifact_ref,
        "artifact_digest": artifact_digest,
        "verifier_version": verifier_version,
        "verification_status": normalized_status,
        "verified_at": canonical_at,
        "raw_payload_retained": False,
    }
    return {
        "proof_ref": _digest(identity),
        "scope_ref": scope_ref,
        "proof_kind": proof_kind,
        "artifact_ref": artifact_ref,
        "artifact_digest": artifact_digest,
        "verifier_version": verifier_version,
        "verification_status": normalized_status,
        "raw_payload_retained": False,
        "verified_at": stored_at,
    }


async def record_promotion_proof(
    session,
    *,
    scope_ref: str,
    proof_kind: str,
    artifact_ref: str,
    artifact_digest: str,
    verifier_version: str,
    verification_status: str,
    verified_at: datetime,
    apply: bool = False,
) -> V2PromotionProofPersistenceReport:
    """Valide et persiste une référence de preuve, sans contenu brut."""

    values = _validated_values(
        scope_ref=scope_ref,
        proof_kind=proof_kind,
        artifact_ref=artifact_ref,
        artifact_digest=artifact_digest,
        verifier_version=verifier_version,
        verification_status=verification_status,
        verified_at=verified_at,
    )
    existing = await session.scalar(
        select(V2PromotionProof).where(V2PromotionProof.proof_ref == values["proof_ref"])
    )
    if existing is not None:
        if any(getattr(existing, name) != value for name, value in values.items()):
            raise V2PromotionProofError("promotion proof replay drifted")
        status = "existing"
        proof_id = existing.id
    elif not apply:
        status = "dry_run"
        proof_id = None
    else:
        proof = V2PromotionProof(**values)
        session.add(proof)
        await session.flush()
        status = "created"
        proof_id = proof.id
    return V2PromotionProofPersistenceReport(
        schema_version="v2-promotion-proof-persistence/v1",
        status=status,
        proof_ref=values["proof_ref"],
        proof_kind=proof_kind,
        scope_ref=scope_ref,
        proof_id=proof_id,
    )


async def verify_registered_proofs(
    session,
    *,
    scope_ref: str,
    proof_refs: dict[str, str],
    expected_keys: frozenset[str],
) -> dict[str, bool]:
    """Résout chaque digest vers une preuve persistée et liée au bon scope."""

    if not _valid_digest(scope_ref):
        raise V2PromotionProofError("scope_ref must be a sha256 digest")
    if set(proof_refs) != expected_keys:
        raise V2PromotionProofError("proof refs do not match the required set")
    if any(not _valid_digest(value) for value in proof_refs.values()):
        raise V2PromotionProofError("proof refs contain an invalid digest")
    rows = list(
        (
            await session.scalars(
                select(V2PromotionProof).where(
                    V2PromotionProof.proof_ref.in_(tuple(proof_refs.values()))
                )
            )
        ).all()
    )
    by_ref = {row.proof_ref: row for row in rows}
    return {
        kind: bool(
            (row := by_ref.get(reference)) is not None
            and row.scope_ref == scope_ref
            and row.proof_kind == kind
            and row.verification_status == "VERIFIED"
            and row.raw_payload_retained is False
            and _valid_digest(row.artifact_digest)
        )
        for kind, reference in proof_refs.items()
    }
