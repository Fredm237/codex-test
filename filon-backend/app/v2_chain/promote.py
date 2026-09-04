"""Commande privée de qualification et de persistance des promotions V2."""

from __future__ import annotations

import argparse
import asyncio
import json
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import datetime

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db import session as db
from app.v2_chain.promotion_guard import load_authorized_canary_gate
from app.v2_chain.proof_registry import (
    REGISTERED_PROOF_KEYS,
    V2PromotionProofPersistenceReport,
    record_promotion_proof,
)
from app.v2_chain.promotion_receipt import (
    PUBLIC_PROOF_KEYS,
    SHADOW_PROOF_KEYS,
    record_promotion_receipt,
)
from app.v2_chain.qualification import (
    RESPONSE_TYPES,
    V2ExternalProofs,
    V2PublicExternalProofs,
    evaluate_persisted_canary_to_public,
    evaluate_persisted_shadow_to_canary,
)


@dataclass(frozen=True)
class V2PromotionCommandReceipt:
    schema_version: str
    promotion_stage: str
    qualification_status: str
    evaluation_id: str
    gate_evaluation_id: str
    authorized_response_types: tuple[str, ...]
    blocked_response_types: tuple[str, ...]
    persistence_status: str
    receipt_id: int | None
    raw_payload_retained: bool = False


def _parse_evaluated_at(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise argparse.ArgumentTypeError("evaluated-at must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise argparse.ArgumentTypeError("evaluated-at must include a timezone")
    return parsed


def _parse_proof(value: str) -> tuple[str, str]:
    name, separator, digest = value.partition("=")
    if not separator or not name or not digest:
        raise argparse.ArgumentTypeError("proof must use NAME=sha256:DIGEST")
    return name, digest


def _proof_mapping(
    values: Sequence[tuple[str, str]],
    *,
    expected: frozenset[str],
) -> dict[str, str]:
    names = [name for name, _ in values]
    if len(names) != len(set(names)):
        raise ValueError("promotion proofs contain duplicate names")
    mapping = dict(values)
    if set(mapping) != expected:
        raise ValueError("promotion proofs do not match the required set")
    return mapping


def _add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--evaluated-at", type=_parse_evaluated_at, required=True)
    parser.add_argument("--proof", action="append", type=_parse_proof, required=True)
    parser.add_argument("--apply", action="store_true")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Qualifier et persister une promotion atomique V2"
    )
    stages = parser.add_subparsers(dest="stage", required=True)

    proof = stages.add_parser("proof", help="Enregistrer une preuve externe")
    proof.add_argument("--scope-ref", required=True)
    proof.add_argument("--proof-kind", choices=tuple(sorted(REGISTERED_PROOF_KEYS)), required=True)
    proof.add_argument("--artifact-ref", required=True)
    proof.add_argument("--artifact-digest", required=True)
    proof.add_argument("--verifier-version", required=True)
    proof.add_argument(
        "--verification-status",
        choices=("VERIFIED", "REJECTED"),
        required=True,
    )
    proof.add_argument("--verified-at", type=_parse_evaluated_at, required=True)
    proof.add_argument("--apply", action="store_true")

    canary = stages.add_parser("canary", help="Qualifier SHADOW vers CANARY")
    _add_common_arguments(canary)
    canary.add_argument("--maximum-p95-window-ms", type=int, required=True)

    public = stages.add_parser("public", help="Qualifier CANARY vers PUBLIC")
    _add_common_arguments(public)
    public.add_argument("--shadow-receipt-evaluation-id", required=True)
    public.add_argument("--minimum-paired-observations", type=int, required=True)
    public.add_argument(
        "--minimum-observations-per-response-type",
        type=int,
        required=True,
    )
    public.add_argument(
        "--response-type",
        action="append",
        choices=tuple(sorted(RESPONSE_TYPES)),
        required=True,
    )
    return parser


def _validate_configuration(args: argparse.Namespace) -> None:
    settings = get_settings()
    if settings.database_schema_mode != "alembic":
        raise RuntimeError("V2 promotion requires DATABASE_SCHEMA_MODE=alembic")
    if not db.is_enabled():
        raise RuntimeError("V2 promotion requires DATABASE_URL")
    if args.stage == "proof":
        return
    if args.stage == "canary":
        if settings.v2_chain_mode != "dark":
            raise RuntimeError("canary qualification requires V2_CHAIN_MODE=dark")
        if settings.v2_canary_reader_enabled or settings.v2_public_reader_enabled:
            raise RuntimeError("canary qualification requires every reader OFF")
    elif args.stage == "public":
        if settings.v2_chain_mode != "canary":
            raise RuntimeError("public qualification requires V2_CHAIN_MODE=canary")
        if not settings.v2_canary_reader_enabled or settings.v2_public_reader_enabled:
            raise RuntimeError("public qualification requires only the canary reader")
        if (
            settings.v2_promotion_receipt_evaluation_id
            != args.shadow_receipt_evaluation_id
        ):
            raise RuntimeError(
                "public qualification requires the active canary receipt"
            )
    else:  # pragma: no cover - argparse protège ce chemin
        raise RuntimeError("promotion stage is unsupported")


def _evaluated_at(args: argparse.Namespace) -> datetime:
    return args.evaluated_at


async def _run(
    args: argparse.Namespace,
) -> V2PromotionCommandReceipt | V2PromotionProofPersistenceReport:
    _validate_configuration(args)
    settings = get_settings()
    configure_logging(settings.debug)
    await db.prepare_schema()
    async with db.session_scope() as session:
        if session is None:
            raise RuntimeError("V2 promotion database session unavailable")
        if args.stage == "proof":
            proof = await record_promotion_proof(
                session,
                scope_ref=args.scope_ref,
                proof_kind=args.proof_kind,
                artifact_ref=args.artifact_ref,
                artifact_digest=args.artifact_digest,
                verifier_version=args.verifier_version,
                verification_status=args.verification_status,
                verified_at=args.verified_at,
                apply=args.apply,
            )
            if args.apply:
                await session.commit()
            return proof
        if args.stage == "canary":
            proof_values = _proof_mapping(
                args.proof,
                expected=SHADOW_PROOF_KEYS,
            )
            report = await evaluate_persisted_shadow_to_canary(
                session,
                proofs=V2ExternalProofs(
                    **proof_values,
                    campaign_id=settings.v2_chain_campaign_id,
                    maximum_p95_window_ms=args.maximum_p95_window_ms,
                ),
                evaluated_at=_evaluated_at(args),
            )
        else:
            public_proof_names = PUBLIC_PROOF_KEYS - {"shadow_gate_ref"}
            proof_values = _proof_mapping(
                args.proof,
                expected=public_proof_names,
            )
            shadow_gate = await load_authorized_canary_gate(
                session,
                receipt_evaluation_id=args.shadow_receipt_evaluation_id,
            )
            report = await evaluate_persisted_canary_to_public(
                session,
                shadow_gate=shadow_gate,
                proofs=V2PublicExternalProofs(
                    shadow_gate_ref=shadow_gate.evaluation_id,
                    **proof_values,
                    minimum_paired_observations=args.minimum_paired_observations,
                    minimum_observations_per_response_type=(
                        args.minimum_observations_per_response_type
                    ),
                    requested_response_types=tuple(args.response_type),
                ),
                evaluated_at=_evaluated_at(args),
            )
        persisted = await record_promotion_receipt(
            session,
            report=report,
            apply=args.apply,
        )
        if args.apply:
            await session.commit()

    gate = report.gate
    authorized = (
        tuple(sorted(RESPONSE_TYPES - set(gate.blocked_response_types)))
        if gate.status == "CANARY_AUTHORIZED"
        else tuple(getattr(gate, "authorized_response_types", ()))
    )
    return V2PromotionCommandReceipt(
        schema_version="v2-promotion-command-receipt/v1",
        promotion_stage=persisted.promotion_stage,
        qualification_status=gate.status,
        evaluation_id=persisted.evaluation_id,
        gate_evaluation_id=gate.evaluation_id,
        authorized_response_types=authorized,
        blocked_response_types=tuple(gate.blocked_response_types),
        persistence_status=persisted.status,
        receipt_id=persisted.receipt_id,
    )


def main(argv: Sequence[str] | None = None) -> int:
    try:
        report = asyncio.run(_run(_parser().parse_args(argv)))
    except Exception as exc:  # pragma: no cover - dépendances réelles
        print(
            json.dumps(
                {"status": "refused", "error_type": type(exc).__name__},
                sort_keys=True,
            )
        )
        return 1
    print(json.dumps(asdict(report), separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
