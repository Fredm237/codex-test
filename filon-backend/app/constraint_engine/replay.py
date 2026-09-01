"""Replay borné Constraint Engine Phase 6."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from sqlalchemy import select

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db import models as core_models
from app.db import session as db
from app.hybrid_retrieval.models import HybridRetrievalCandidate, HybridRetrievalRun

from .engine import CandidateFacts, ConstraintRequest, Fact, HardConstraint, evaluate_constraints
from .persistence import persist_constraint_evaluation


REPLAY_VERSION = "constraint-engine-production-replay/v1"
MAX_REPLAY_RUNS = 100


class ConstraintReplayError(RuntimeError):
    """Replay impossible à qualifier sans inventer de preuve."""


@dataclass(frozen=True)
class ConstraintReplayReport:
    schema_version: str
    replay_version: str
    mode: str
    evaluated_at: str
    after_run_id: int
    limit: int
    scanned_runs: int
    scanned_candidates: int
    eligible_candidates: int
    excluded_candidates: int
    unknown_candidates: int
    runs_created: int
    runs_existing: int
    candidates_created: int
    candidates_existing: int
    last_run_id: int | None
    evaluation_id: str


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ConstraintReplayError("evaluated_at must include a timezone")
    return value.astimezone(timezone.utc)


def _validate_window(after_run_id: int, limit: int) -> tuple[int, int]:
    if isinstance(after_run_id, bool) or not isinstance(after_run_id, int) or after_run_id < 0:
        raise ValueError("after_run_id must be a non-negative integer")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_REPLAY_RUNS:
        raise ValueError(f"limit must be between 1 and {MAX_REPLAY_RUNS}")
    return after_run_id, limit


def _facts(candidate: HybridRetrievalCandidate, offers: list[core_models.Offer]) -> CandidateFacts:
    if not offers:
        price = availability = adult = Fact("unknown")
    else:
        known_prices = [offer for offer in offers if offer.price is not None and offer.currency]
        if known_prices:
            cheapest = min(known_prices, key=lambda offer: offer.price)
            price = Fact(
                "known",
                {"amount": format(cheapest.price, ".2f"), "currency": cheapest.currency},
                (f"offer:{cheapest.id}:price",),
            )
        else:
            price = Fact("unknown")
        if any(offer.in_stock is True for offer in offers):
            availability = Fact("known", "in_stock", tuple(f"offer:{offer.id}:stock" for offer in offers if offer.in_stock is True))
        elif all(offer.in_stock is False for offer in offers):
            availability = Fact("known", "out_of_stock", tuple(f"offer:{offer.id}:stock" for offer in offers))
        else:
            availability = Fact("unknown")
        adult = Fact(
            "known",
            any(offer.is_adult for offer in offers),
            tuple(f"offer:{offer.id}:adult" for offer in offers),
        )
    return CandidateFacts(
        entity_ref=candidate.entity_ref,
        price=price,
        countries=Fact("unknown"),
        availability=availability,
        adult_restricted=adult,
        attributes={},
        preference_facts={},
    )


async def replay_constraint_batch(
    session,
    *,
    evaluated_at: datetime,
    after_run_id: int = 0,
    limit: int = 10,
    apply: bool = False,
) -> ConstraintReplayReport:
    after_run_id, limit = _validate_window(after_run_id, limit)
    evaluated = _aware(evaluated_at)
    runs = (
        (
            await session.execute(
                select(HybridRetrievalRun)
                .where(HybridRetrievalRun.id > after_run_id)
                .order_by(HybridRetrievalRun.id)
                .limit(limit)
            )
        )
        .scalars()
        .all()
    )
    counters = {key: 0 for key in ("candidates", "ELIGIBLE", "EXCLUDED", "UNKNOWN", "runs_created", "runs_existing", "candidates_created", "candidates_existing")}
    identities: list[dict[str, object]] = []
    for run in runs:
        candidates = (
            (
                await session.execute(
                    select(HybridRetrievalCandidate)
                    .where(HybridRetrievalCandidate.run_id == run.id)
                    .order_by(HybridRetrievalCandidate.candidate_rank)
                )
            )
            .scalars()
            .all()
        )
        offer_ids = sorted({offer_id for candidate in candidates for offer_id in candidate.offer_ids_json})
        offers = (
            (
                await session.execute(select(core_models.Offer).where(core_models.Offer.id.in_(offer_ids)))
            )
            .scalars()
            .all()
            if offer_ids
            else []
        )
        by_id = {offer.id: offer for offer in offers}
        facts = [
            _facts(candidate, [by_id[item] for item in candidate.offer_ids_json if item in by_id])
            for candidate in candidates
        ]
        request = ConstraintRequest(
            context_ref=f"p6g:{run.id}",
            hard_constraints=(
                HardConstraint("availability", "AVAILABILITY_REQUIRED", {"value": "in_stock"}),
                HardConstraint("adult-safety", "ADULT_SAFETY", {"adult_allowed": False}),
            ),
        )
        evaluation = evaluate_constraints(request, facts)
        report = await persist_constraint_evaluation(
            session,
            retrieval_run=run,
            candidate_ids={candidate.entity_ref: candidate.id for candidate in candidates},
            evaluated_at=evaluated,
            evaluation=evaluation,
            apply=apply,
        )
        counters["candidates"] += len(evaluation.candidates)
        for item in evaluation.candidates:
            counters[item.status] += 1
        for key in ("runs_created", "runs_existing", "candidates_created", "candidates_existing"):
            counters[key] += getattr(report, key)
        identities.append({"retrieval_run_id": run.id, "result_digest": evaluation.result_digest, "run_key": report.run_key})
    payload = json.dumps(identities, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return ConstraintReplayReport(
        schema_version="constraint-replay-report/v1",
        replay_version=REPLAY_VERSION,
        mode="apply" if apply else "dry_run",
        evaluated_at=evaluated.isoformat().replace("+00:00", "Z"),
        after_run_id=after_run_id,
        limit=limit,
        scanned_runs=len(runs),
        scanned_candidates=counters["candidates"],
        eligible_candidates=counters["ELIGIBLE"],
        excluded_candidates=counters["EXCLUDED"],
        unknown_candidates=counters["UNKNOWN"],
        runs_created=counters["runs_created"],
        runs_existing=counters["runs_existing"],
        candidates_created=counters["candidates_created"],
        candidates_existing=counters["candidates_existing"],
        last_run_id=runs[-1].id if runs else None,
        evaluation_id="sha256:" + hashlib.sha256(payload).hexdigest(),
    )


def _parse_evaluated_at(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise argparse.ArgumentTypeError("evaluated-at must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise argparse.ArgumentTypeError("evaluated-at must include a timezone")
    return parsed


async def _run(args: argparse.Namespace) -> ConstraintReplayReport:
    settings = get_settings()
    configure_logging(settings.debug)
    if args.apply and not settings.constraint_engine_shadow_enabled:
        raise RuntimeError("CONSTRAINT_ENGINE_SHADOW_ENABLED is required for --apply")
    if not db.is_enabled():
        raise RuntimeError("DATABASE_URL is required")
    await db.prepare_schema()
    async with db.session_scope() as session:
        if session is None:
            raise RuntimeError("database session unavailable")
        return await replay_constraint_batch(
            session,
            evaluated_at=args.evaluated_at,
            after_run_id=args.after_run_id,
            limit=args.limit,
            apply=args.apply,
        )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Replay borné Constraint Engine shadow Phase 6")
    parser.add_argument("--evaluated-at", required=True, type=_parse_evaluated_at)
    parser.add_argument("--after-run-id", type=int, default=0)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--apply", action="store_true")
    return parser


def main() -> None:
    print(json.dumps(asdict(asyncio.run(_run(_parser().parse_args()))), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
