"""Replay borné Product Ranking v2 fondé sur les preuves Hybrid Retrieval.

Le replay classe uniquement lorsque le rang de récupération et sa provenance
sont persistés. La qualité produit et la valeur restent inconnues et ne
reçoivent jamais de valeur de remplacement.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import select

from app.constraint_engine.models import ConstraintCandidateEvaluation, ConstraintEvaluationRun
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db import session as db
from app.hybrid_retrieval.models import HybridRetrievalCandidate

from .engine import RankingCandidateFacts, RankingRequest, ScoreFact, VERTICAL_WEIGHTS, rank_products
from .persistence import persist_product_ranking


REPLAY_VERSION = "product-ranking-production-replay/v2"
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
    rankable_runs: int
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


def _bounded_score(value: Decimal) -> str:
    return format(
        min(Decimal("1"), max(Decimal("0"), value)).quantize(
            Decimal("0.000001"), rounding=ROUND_HALF_UP
        ),
        "f",
    )


def _factual_dimensions(
    candidate: HybridRetrievalCandidate | None,
) -> dict[str, ScoreFact]:
    """Construit uniquement les dimensions prouvables depuis P5.

    Le rang et la couverture des sources sont des faits persistés. La qualité
    produit et la valeur marchande restent explicitement inconnues : elles ne
    reçoivent ni valeur neutre, ni moyenne inventée.
    """

    if candidate is None or candidate.candidate_rank < 1:
        return {name: ScoreFact("unknown") for name in (
            "need_fit", "product_quality", "value", "evidence"
        )}
    raw_source_rows = (
        candidate.source_evidence_json
        if isinstance(candidate.source_evidence_json, list)
        else []
    )
    source_rows = [
        item
        for item in raw_source_rows
        if isinstance(item, dict)
        and item.get("source_type") in {"LEXICAL", "STRUCTURED", "SEMANTIC"}
        and isinstance(item.get("evidence_ref"), str)
        and item["evidence_ref"]
    ]
    source_types = {str(item["source_type"]) for item in source_rows}
    source_refs = tuple(
        sorted({str(item["evidence_ref"]) for item in source_rows})
    )
    if not source_refs:
        evidence = ScoreFact("unknown")
    else:
        evidence = ScoreFact(
            "known",
            _bounded_score(Decimal(len(source_types)) / Decimal("3")),
            source_refs,
        )
    return {
        "need_fit": ScoreFact(
            "known",
            _bounded_score(Decimal("1") / Decimal(candidate.candidate_rank)),
            (f"hybrid-retrieval-candidate:{candidate.id}:rank",),
        ),
        "product_quality": ScoreFact("unknown"),
        "value": ScoreFact("unknown"),
        "evidence": evidence,
    }


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
    counters = {key: 0 for key in ("candidates", "rankable_runs", "RANKED", "UNRANKABLE", "INELIGIBLE", "runs_created", "runs_existing", "candidates_created", "candidates_existing")}
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
        retrieval_ids = [row.retrieval_candidate_id for row in rows]
        retrieval_rows = (
            (
                await session.execute(
                    select(HybridRetrievalCandidate).where(
                        HybridRetrievalCandidate.id.in_(retrieval_ids)
                    )
                )
            )
            .scalars()
            .all()
            if retrieval_ids
            else []
        )
        retrieval_by_id = {item.id: item for item in retrieval_rows}
        candidates = [
            RankingCandidateFacts(
                row.entity_ref,
                row.status,
                _factual_dimensions(retrieval_by_id.get(row.retrieval_candidate_id)),
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
        counters["rankable_runs"] += bool(ranking.ranked_entity_refs)
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
        counters["rankable_runs"],
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
