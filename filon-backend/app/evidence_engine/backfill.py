"""Backfill borné du registre de claims, sans écriture par défaut."""

from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime

from sqlalchemy import select

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.db import session as db
from app.evidence_engine.policy import (
    ATOMIC_CLAIMS,
    STRONG_CLAIMS,
    evaluate_offer_claims,
    persist_offer_evaluation,
)
from app.observations.models import RawSourceRecord
from app.offer_graph.models import GraphOfferObservation


log = get_logger("evidence_engine.backfill")
MAX_BACKFILL_ROWS = 10_000


@dataclass(frozen=True)
class EvidenceBackfillReport:
    mode: str
    raw_records: int
    offer_observations: int
    claims_evaluated: int
    atomic_claims_eligible: int
    strong_claims_ineligible: int
    rankable_decisions: int
    decision_eligible: int
    claims_created: int
    claims_existing: int
    decisions_created: int
    decisions_existing: int
    last_raw_source_id: int | None


def parse_evaluated_at(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("evaluated_at must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("evaluated_at must include an explicit UTC offset")
    return parsed.astimezone(UTC).replace(tzinfo=None)


def _window(after_raw_id: int, limit: int) -> tuple[int, int]:
    if isinstance(after_raw_id, bool) or after_raw_id < 0:
        raise ValueError("after_raw_id must be a non-negative integer")
    if isinstance(limit, bool) or not 1 <= limit <= MAX_BACKFILL_ROWS:
        raise ValueError(f"limit must be between 1 and {MAX_BACKFILL_ROWS}")
    return after_raw_id, limit


async def backfill_evidence_batch(
    session,
    *,
    evaluated_at: datetime,
    after_raw_id: int = 0,
    limit: int = 1_000,
    apply: bool = False,
) -> EvidenceBackfillReport:
    after_raw_id, limit = _window(after_raw_id, limit)
    raws = (
        (
            await session.execute(
                select(RawSourceRecord)
                .where(
                    RawSourceRecord.source_type == "awin_feed",
                    RawSourceRecord.id > after_raw_id,
                )
                .order_by(RawSourceRecord.id)
                .limit(limit)
            )
        )
        .scalars()
        .all()
    )
    raw_ids = [raw.id for raw in raws]
    observations = []
    if raw_ids:
        observations = (
            (
                await session.execute(
                    select(GraphOfferObservation)
                    .where(GraphOfferObservation.raw_source_record_id.in_(raw_ids))
                    .order_by(
                        GraphOfferObservation.raw_source_record_id,
                        GraphOfferObservation.id,
                    )
                )
            )
            .scalars()
            .all()
        )

    atomic_eligible = strong_ineligible = rankable = decision_eligible = 0
    claims_created = decisions_created = 0
    for observation in observations:
        claims, decision = await evaluate_offer_claims(
            session,
            observation=observation,
            evaluated_at=evaluated_at,
        )
        atomic_eligible += sum(
            claim.claim_code in ATOMIC_CLAIMS and claim.eligibility == "eligible"
            for claim in claims
        )
        strong_ineligible += sum(
            claim.claim_code in STRONG_CLAIMS and claim.eligibility == "ineligible"
            for claim in claims
        )
        rankable += int(decision.highest_stage == "RANKABLE")
        decision_eligible += int(decision.decision_eligible)
        if apply:
            created, decision_was_created = await persist_offer_evaluation(
                session,
                observation=observation,
                claims=claims,
                decision=decision,
            )
            claims_created += created
            decisions_created += int(decision_was_created)
    if apply:
        await session.commit()
    claims_total = len(observations) * (len(ATOMIC_CLAIMS) + len(STRONG_CLAIMS))
    return EvidenceBackfillReport(
        mode="apply" if apply else "dry_run",
        raw_records=len(raws),
        offer_observations=len(observations),
        claims_evaluated=claims_total,
        atomic_claims_eligible=atomic_eligible,
        strong_claims_ineligible=strong_ineligible,
        rankable_decisions=rankable,
        decision_eligible=decision_eligible,
        claims_created=claims_created,
        claims_existing=claims_total - claims_created if apply else 0,
        decisions_created=decisions_created,
        decisions_existing=len(observations) - decisions_created if apply else 0,
        last_raw_source_id=raws[-1].id if raws else None,
    )


async def _run(args: argparse.Namespace) -> EvidenceBackfillReport:
    settings = get_settings()
    configure_logging(settings.debug)
    if args.apply and not (
        settings.observation_shadow_enabled
        and settings.product_graph_shadow_enabled
        and settings.offer_graph_shadow_enabled
        and settings.merchant_intelligence_shadow_enabled
        and settings.evidence_engine_shadow_enabled
    ):
        raise RuntimeError("all five intelligence shadow flags are required")
    if not db.is_enabled():
        raise RuntimeError("DATABASE_URL is required")
    await db.prepare_schema()
    async with db.session_scope() as session:
        if session is None:
            raise RuntimeError("database session unavailable")
        return await backfill_evidence_batch(
            session,
            evaluated_at=parse_evaluated_at(args.evaluated_at),
            after_raw_id=args.after_raw_id,
            limit=args.limit,
            apply=args.apply,
        )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evidence Engine shadow")
    parser.add_argument("--evaluated-at", required=True)
    parser.add_argument("--after-raw-id", type=int, default=0)
    parser.add_argument("--limit", type=int, default=1_000)
    parser.add_argument("--apply", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        report = asyncio.run(_run(_parser().parse_args(argv)))
    except Exception as exc:
        log.error("Backfill Evidence Engine refusé (error_type=%s)", type(exc).__name__)
        return 1
    print(json.dumps(asdict(report), sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
