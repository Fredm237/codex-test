"""Replay borné Product Ranking Phase 7.

Le replay production s'abstient tant que les quatre dimensions ne disposent
pas de preuves réelles. Il qualifie le câblage sans inventer un score.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from sqlalchemy import select

from app.constraint_engine.models import ConstraintCandidateEvaluation, ConstraintEvaluationRun
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db import session as db

from .engine import RankingCandidateFacts, RankingRequest, ScoreFact, VERTICAL_WEIGHTS, rank_products
from .persistence import persist_product_ranking


REPLAY_VERSION = "product-ranking-production-replay/v1"
MAX_REPLAY_RUNS = 100


@dataclass(frozen=True)
class ProductRankingReplayReport:
    schema_version: str
    replay_version: str
    mode: str
    evaluated_at: str
    vertical: str
    after_constraint_run_id: int
    limit: int
    scanned_runs: int
    scanned_candidates: int
    ranked_candidates: int
    unrankable_candidates: int
    ineligible_candidates: int
    runs_created: int
    runs_existing: int
    candidates_created: int
    candidates_existing: int
    last_constraint_run_id: int | None
    evaluation_id: str


def _validate_window(after_constraint_run_id: int, limit: int) -> tuple[int, int]:
    if isinstance(after_constraint_run_id, bool) or not isinstance(after_constraint_run_id, int) or after_constraint_run_id < 0:
        raise ValueError("after_constraint_run_id must be a non-negative integer")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_REPLAY_RUNS:
        raise ValueError(f"limit must be between 1 and {MAX_REPLAY_RUNS}")
    return after_constraint_run_id, limit


async def replay_product_ranking_batch(
    session,
    *,
    evaluated_at: datetime,
    vertical: str,
    after_constraint_run_id: int = 0,
    limit: int = 10,
    apply: bool = False,
) -> ProductRankingReplayReport:
    after_constraint_run_id, limit = _validate_window(after_constraint_run_id, limit)
    if vertical not in VERTICAL_WEIGHTS:
        raise ValueError("vertical is unsupported")
    if evaluated_at.tzinfo is None:
        raise ValueError("evaluated_at must include a timezone")
    evaluated = evaluated_at.astimezone(timezone.utc)
    runs = (
        (
            await session.execute(
                select(ConstraintEvaluationRun)
                .where(ConstraintEvaluationRun.id > after_constraint_run_id)
                .order_by(ConstraintEvaluationRun.id)
                .limit(limit)
            )
        )
        .scalars()
        .all()
    )
    counters = {key: 0 for key in ("candidates", "RANKED", "UNRANKABLE", "INELIGIBLE", "runs_created", "runs_existing", "candidates_created", "candidates_existing")}
    identities: list[dict[str, object]] = []
    for run in runs:
        rows = (
            (
                await session.execute(
                    select(ConstraintCandidateEvaluation)
                    .where(ConstraintCandidateEvaluation.run_id == run.id)
                    .order_by(ConstraintCandidateEvaluation.id)
                )
            )
            .scalars()
            .all()
        )
        # Aucune dimension n'est inférée d'un prix, d'un statut ou d'une
        # commission. Tant que les preuves Phase 7 manquent, le résultat est une
        # abstention honnête.
        candidates = [
            RankingCandidateFacts(
                row.entity_ref,
                row.status,
                {
                    "need_fit": ScoreFact("unknown"),
                    "product_quality": ScoreFact("unknown"),
                    "value": ScoreFact("unknown"),
                    "evidence": ScoreFact("unknown"),
                },
            )
            for row in rows
        ]
        ranking = rank_products(RankingRequest(f"p7g:{run.id}", vertical), candidates)
        report = await persist_product_ranking(
            session,
            constraint_run=run,
            candidate_ids={row.entity_ref: row.id for row in rows},
            evaluated_at=evaluated,
            ranking=ranking,
            apply=apply,
        )
        counters["candidates"] += len(ranking.candidates)
        for candidate in ranking.candidates:
            counters[candidate.status] += 1
        for key in ("runs_created", "runs_existing", "candidates_created", "candidates_existing"):
            counters[key] += getattr(report, key)
        identities.append({"constraint_run_id": run.id, "result_digest": ranking.result_digest, "run_key": report.run_key})
    payload = json.dumps(identities, sort_keys=True, separators=(",", ":")).encode()
    return ProductRankingReplayReport(
        "product-ranking-replay-report/v1",
        REPLAY_VERSION,
        "apply" if apply else "dry_run",
        evaluated.isoformat().replace("+00:00", "Z"),
        vertical,
        after_constraint_run_id,
        limit,
        len(runs),
        counters["candidates"],
        counters["RANKED"],
        counters["UNRANKABLE"],
        counters["INELIGIBLE"],
        counters["runs_created"],
        counters["runs_existing"],
        counters["candidates_created"],
        counters["candidates_existing"],
        runs[-1].id if runs else None,
        "sha256:" + hashlib.sha256(payload).hexdigest(),
    )


def _parse_evaluated_at(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise argparse.ArgumentTypeError("evaluated-at must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise argparse.ArgumentTypeError("evaluated-at must include a timezone")
    return parsed


async def _run(args: argparse.Namespace) -> ProductRankingReplayReport:
    settings = get_settings()
    configure_logging(settings.debug)
    if args.apply and not settings.product_ranking_shadow_enabled:
        raise RuntimeError("PRODUCT_RANKING_SHADOW_ENABLED is required for --apply")
    if not db.is_enabled():
        raise RuntimeError("DATABASE_URL is required")
    await db.prepare_schema()
    async with db.session_scope() as session:
        if session is None:
            raise RuntimeError("database session unavailable")
        return await replay_product_ranking_batch(
            session,
            evaluated_at=args.evaluated_at,
            vertical=args.vertical,
            after_constraint_run_id=args.after_constraint_run_id,
            limit=args.limit,
            apply=args.apply,
        )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Replay borné Product Ranking shadow Phase 7")
    parser.add_argument("--evaluated-at", required=True, type=_parse_evaluated_at)
    parser.add_argument("--vertical", required=True, choices=tuple(VERTICAL_WEIGHTS))
    parser.add_argument("--after-constraint-run-id", type=int, default=0)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--apply", action="store_true")
    return parser


def main() -> None:
    print(json.dumps(asdict(asyncio.run(_run(_parser().parse_args()))), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
