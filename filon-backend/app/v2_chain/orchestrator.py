"""Replay borné de P0 shadows et P1–P10 sur une fenêtre commune.

Le module n'expose aucun lecteur. Il coordonne uniquement les writers append-only
déjà qualifiés et transporte des checkpoints explicites pour qu'un replay
strictement identique relise la même chaîne, même après les premiers commits.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from collections.abc import Awaitable, Callable
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select

from app.buy_wait.replay import replay_buy_wait_batch
from app.confidence.models import ConfidenceCalibrationRun
from app.confidence.replay import replay_confidence_batch
from app.constraint_engine.models import ConstraintEvaluationRun
from app.constraint_engine.replay import replay_constraint_batch
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db import session as db
from app.evidence_engine.backfill import backfill_evidence_batch
from app.hybrid_retrieval.models import HybridRetrievalRun
from app.hybrid_retrieval.replay import replay_hybrid_retrieval_batch
from app.merchant_intelligence.backfill import measure_batch
from app.offer_graph.backfill import backfill_offer_batch
from app.offer_optimization.models import OfferOptimizationRun
from app.offer_optimization.replay import replay_offer_optimization_batch
from app.offer_truth.replay import replay_offer_truth_batch
from app.product_graph.backfill import backfill_batch
from app.product_graph.entity_replay import replay_entity_resolution_batch
from app.product_ontology.models import ProductOntologySnapshot
from app.product_ontology.replay import replay_product_ontology_batch
from app.product_ranking.engine import VERTICAL_WEIGHTS
from app.product_ranking.models import ProductRankingRun
from app.product_ranking.replay import replay_product_ranking_batch


MAX_CHAIN_ROWS = 100


@dataclass(frozen=True)
class V2ChainCheckpoints:
    ontology_snapshot_id: int
    hybrid_run_id: int
    constraint_run_id: int
    ranking_run_id: int
    optimization_run_id: int
    confidence_run_id: int


@dataclass(frozen=True)
class V2ChainReport:
    schema_version: str
    mode: str
    evaluated_at: str
    vertical: str
    after_raw_id: int
    limit: int
    checkpoints: V2ChainCheckpoints
    stages: dict[str, dict[str, Any]]
    evaluation_id: str
    execution_id: int | None = None


async def _max_id(session, model) -> int:
    value = await session.scalar(select(func.max(model.id)))
    return int(value or 0)


async def capture_checkpoints(session) -> V2ChainCheckpoints:
    """Capture les bornes amont avant un premier apply ou un replay identique."""

    return V2ChainCheckpoints(
        ontology_snapshot_id=await _max_id(session, ProductOntologySnapshot),
        hybrid_run_id=await _max_id(session, HybridRetrievalRun),
        constraint_run_id=await _max_id(session, ConstraintEvaluationRun),
        ranking_run_id=await _max_id(session, ProductRankingRun),
        optimization_run_id=await _max_id(session, OfferOptimizationRun),
        confidence_run_id=await _max_id(session, ConfidenceCalibrationRun),
    )


def validate_v2_chain_request(
    *,
    evaluated_at: datetime,
    vertical: str,
    after_raw_id: int,
    limit: int,
    checkpoints: V2ChainCheckpoints,
) -> datetime:
    if evaluated_at.tzinfo is None:
        raise ValueError("evaluated_at must include a timezone")
    if vertical not in VERTICAL_WEIGHTS:
        raise ValueError("vertical is unsupported")
    if (
        isinstance(after_raw_id, bool)
        or not isinstance(after_raw_id, int)
        or after_raw_id < 0
    ):
        raise ValueError("after_raw_id must be a non-negative integer")
    if (
        isinstance(limit, bool)
        or not isinstance(limit, int)
        or not 1 <= limit <= MAX_CHAIN_ROWS
    ):
        raise ValueError(f"limit must be between 1 and {MAX_CHAIN_ROWS}")
    if any(
        isinstance(value, bool) or not isinstance(value, int) or value < 0
        for value in asdict(checkpoints).values()
    ):
        raise ValueError("V2 chain checkpoints must be non-negative integers")
    return evaluated_at.astimezone(timezone.utc)


def _stage(report: object) -> dict[str, Any]:
    return asdict(report)


async def _complete_stage(
    stages: dict[str, dict[str, Any]],
    name: str,
    report: object,
    on_stage_complete: Callable[[str], Awaitable[None]] | None,
) -> None:
    stages[name] = _stage(report)
    if on_stage_complete is not None:
        await on_stage_complete(name)


def _identity_payload(
    *,
    evaluated_at: datetime,
    vertical: str,
    after_raw_id: int,
    limit: int,
    checkpoints: V2ChainCheckpoints,
    stages: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    stable_stage_ids = {
        name: report.get("evaluation_id")
        for name, report in stages.items()
        if report.get("evaluation_id") is not None
    }
    return {
        "evaluated_at": evaluated_at.isoformat().replace("+00:00", "Z"),
        "vertical": vertical,
        "after_raw_id": after_raw_id,
        "limit": limit,
        "checkpoints": asdict(checkpoints),
        "stage_evaluation_ids": stable_stage_ids,
    }


async def run_v2_shadow_chain(
    session,
    *,
    evaluated_at: datetime,
    vertical: str,
    after_raw_id: int = 0,
    limit: int = 10,
    apply: bool = False,
    checkpoints: V2ChainCheckpoints | None = None,
    on_stage_complete: Callable[[str], Awaitable[None]] | None = None,
) -> V2ChainReport:
    """Exécute la chaîne avec une fenêtre et des checkpoints réutilisables."""

    captured = checkpoints or await capture_checkpoints(session)
    evaluated = validate_v2_chain_request(
        evaluated_at=evaluated_at,
        vertical=vertical,
        after_raw_id=after_raw_id,
        limit=limit,
        checkpoints=captured,
    )
    measured_at = evaluated.replace(tzinfo=None)

    stages: dict[str, dict[str, Any]] = {}
    await _complete_stage(
        stages,
        "product_identity",
        await backfill_batch(
            session,
            after_raw_id=after_raw_id,
            limit=limit,
            apply=apply,
        ),
        on_stage_complete,
    )
    await _complete_stage(
        stages,
        "entity_resolution",
        await replay_entity_resolution_batch(
            session,
            after_raw_id=after_raw_id,
            limit=limit,
            apply=apply,
        ),
        on_stage_complete,
    )
    await _complete_stage(
        stages,
        "offer_graph",
        await backfill_offer_batch(
            session,
            after_raw_id=after_raw_id,
            limit=limit,
            apply=apply,
        ),
        on_stage_complete,
    )
    await _complete_stage(
        stages,
        "merchant_intelligence",
        await measure_batch(
            session,
            evaluated_at=measured_at,
            after_raw_id=after_raw_id,
            limit=limit,
            apply=apply,
        ),
        on_stage_complete,
    )
    await _complete_stage(
        stages,
        "evidence_engine",
        await backfill_evidence_batch(
            session,
            evaluated_at=measured_at,
            after_raw_id=after_raw_id,
            limit=limit,
            apply=apply,
        ),
        on_stage_complete,
    )
    await _complete_stage(
        stages,
        "offer_truth",
        await replay_offer_truth_batch(
            session,
            evaluated_at=evaluated,
            after_raw_id=after_raw_id,
            limit=limit,
            apply=apply,
        ),
        on_stage_complete,
    )
    await _complete_stage(
        stages,
        "product_ontology",
        await replay_product_ontology_batch(
            session,
            evaluated_at=evaluated,
            after_raw_id=after_raw_id,
            limit=limit,
            apply=apply,
        ),
        on_stage_complete,
    )
    await _complete_stage(
        stages,
        "hybrid_retrieval",
        await replay_hybrid_retrieval_batch(
            session,
            evaluated_at=evaluated,
            after_snapshot_id=captured.ontology_snapshot_id,
            limit=limit,
            apply=apply,
        ),
        on_stage_complete,
    )
    await _complete_stage(
        stages,
        "constraint_engine",
        await replay_constraint_batch(
            session,
            evaluated_at=evaluated,
            after_run_id=captured.hybrid_run_id,
            limit=limit,
            apply=apply,
        ),
        on_stage_complete,
    )
    await _complete_stage(
        stages,
        "product_ranking",
        await replay_product_ranking_batch(
            session,
            evaluated_at=evaluated,
            vertical=vertical,
            after_constraint_run_id=captured.constraint_run_id,
            limit=limit,
            apply=apply,
        ),
        on_stage_complete,
    )
    await _complete_stage(
        stages,
        "offer_optimization",
        await replay_offer_optimization_batch(
            session,
            evaluated_at=evaluated,
            after_product_ranking_run_id=captured.ranking_run_id,
            limit=limit,
            apply=apply,
        ),
        on_stage_complete,
    )
    await _complete_stage(
        stages,
        "confidence",
        await replay_confidence_batch(
            session,
            evaluated_at=evaluated,
            after_offer_optimization_run_id=captured.optimization_run_id,
            limit=limit,
            apply=apply,
        ),
        on_stage_complete,
    )
    await _complete_stage(
        stages,
        "buy_wait",
        await replay_buy_wait_batch(
            session,
            evaluated_at=evaluated,
            after_confidence_run_id=captured.confidence_run_id,
            limit=limit,
            apply=apply,
        ),
        on_stage_complete,
    )

    identity = _identity_payload(
        evaluated_at=evaluated,
        vertical=vertical,
        after_raw_id=after_raw_id,
        limit=limit,
        checkpoints=captured,
        stages=stages,
    )
    encoded = json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
    return V2ChainReport(
        schema_version="v2-shadow-chain-report/v1",
        mode="apply" if apply else "dry_run",
        evaluated_at=evaluated.isoformat().replace("+00:00", "Z"),
        vertical=vertical,
        after_raw_id=after_raw_id,
        limit=limit,
        checkpoints=captured,
        stages=stages,
        evaluation_id="sha256:" + hashlib.sha256(encoded).hexdigest(),
    )


def _parse_evaluated_at(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise argparse.ArgumentTypeError("evaluated-at must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise argparse.ArgumentTypeError("evaluated-at must include a timezone")
    return parsed


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Replay borné de la chaîne V2 shadow P0/P1–P10"
    )
    evaluated_group = parser.add_mutually_exclusive_group(required=True)
    evaluated_group.add_argument("--evaluated-at", type=_parse_evaluated_at)
    evaluated_group.add_argument("--evaluated-at-now", action="store_true")
    parser.add_argument("--vertical", required=True, choices=tuple(VERTICAL_WEIGHTS))
    cursor_group = parser.add_mutually_exclusive_group()
    cursor_group.add_argument("--after-raw-id", type=int, default=0)
    cursor_group.add_argument("--continue-after-last-success", action="store_true")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--campaign-id")
    parser.add_argument(
        "--execution-kind",
        choices=("progression", "replay", "recovery"),
    )
    parser.add_argument("--source-execution-id", type=int)
    for field in V2ChainCheckpoints.__dataclass_fields__:
        parser.add_argument("--checkpoint-" + field.replace("_", "-"), type=int)
    return parser


async def _run(args: argparse.Namespace) -> V2ChainReport:
    settings = get_settings()
    configure_logging(settings.debug)
    if args.apply and settings.v2_chain_mode not in {
        "shadow",
        "dark",
        "canary",
        "public",
    }:
        raise RuntimeError("an active V2_CHAIN_MODE is required for --apply")
    if not db.is_enabled():
        raise RuntimeError("DATABASE_URL is required")
    campaign_values = (
        args.campaign_id,
        args.execution_kind,
        args.source_execution_id,
    )
    if any(value is not None for value in campaign_values) and not (
        args.campaign_id is not None and args.execution_kind is not None
    ):
        raise RuntimeError("campaign id and execution kind must be supplied together")
    if args.continue_after_last_success and args.campaign_id is None:
        raise RuntimeError("continuous cursor requires an exact campaign id")
    if args.apply and args.campaign_id is not None and (
        settings.v2_chain_campaign_id != args.campaign_id
    ):
        raise RuntimeError("execution campaign does not match active configuration")
    supplied = {
        field: getattr(args, "checkpoint_" + field)
        for field in V2ChainCheckpoints.__dataclass_fields__
    }
    if any(value is not None for value in supplied.values()) and not all(
        value is not None for value in supplied.values()
    ):
        raise RuntimeError("all V2 chain checkpoints must be supplied together")
    checkpoints = (
        V2ChainCheckpoints(**supplied)
        if all(value is not None for value in supplied.values())
        else None
    )
    await db.prepare_schema()
    async with db.session_scope() as session:
        if session is None:
            raise RuntimeError("database session unavailable")
        from app.v2_chain.execution import (
            next_after_raw_id,
            run_journaled_v2_shadow_chain,
        )

        after_raw_id = (
            await next_after_raw_id(
                session,
                vertical=args.vertical,
                campaign_id=args.campaign_id,
            )
            if args.continue_after_last_success
            else args.after_raw_id
        )
        evaluated_at = (
            datetime.now(timezone.utc) if args.evaluated_at_now else args.evaluated_at
        )

        return await run_journaled_v2_shadow_chain(
            session,
            evaluated_at=evaluated_at,
            vertical=args.vertical,
            after_raw_id=after_raw_id,
            limit=args.limit,
            apply=args.apply,
            checkpoints=checkpoints,
            campaign_id=args.campaign_id,
            execution_kind=args.execution_kind,
            source_execution_id=args.source_execution_id,
        )


def main(argv: list[str] | None = None) -> int:
    try:
        report = asyncio.run(_run(_parser().parse_args(argv)))
    except Exception as exc:
        print(
            json.dumps(
                {"status": "refused", "error_type": type(exc).__name__},
                sort_keys=True,
            )
        )
        return 1
    print(json.dumps(asdict(report), sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
