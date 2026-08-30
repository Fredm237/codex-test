"""Backfill borné de l'Offer Graph, en lecture seule par défaut."""

from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import asdict, dataclass

from sqlalchemy import select

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.db import session as db
from app.observations.models import Observation, RawSourceRecord
from app.offer_graph.projection import (
    evaluate_offer_projection,
    persist_awin_offer_projection,
    project_awin_offer,
)


log = get_logger("offer_graph.backfill")
MAX_BACKFILL_ROWS = 10_000


@dataclass(frozen=True)
class OfferGraphBackfillReport:
    mode: str
    scanned: int
    eligible: int
    unknown: int
    ineligible: int
    quarantine: int
    observations_created: int
    observations_existing: int
    missing_offer_links: int
    last_raw_source_id: int | None


def _window(after_raw_id: int, limit: int) -> tuple[int, int]:
    if isinstance(after_raw_id, bool) or after_raw_id < 0:
        raise ValueError("after_raw_id must be a non-negative integer")
    if isinstance(limit, bool) or not 1 <= limit <= MAX_BACKFILL_ROWS:
        raise ValueError(f"limit must be between 1 and {MAX_BACKFILL_ROWS}")
    return after_raw_id, limit


async def _offer_id(session, raw_id: int) -> int | None:
    values = (
        (
            await session.execute(
                select(Observation.offer_id)
                .where(
                    Observation.raw_source_record_id == raw_id,
                    Observation.offer_id.is_not(None),
                )
                .distinct()
                .limit(2)
            )
        )
        .scalars()
        .all()
    )
    if len(values) > 1:
        raise RuntimeError("raw source points to multiple Core offers")
    return int(values[0]) if values else None


async def backfill_offer_batch(
    session,
    *,
    after_raw_id: int = 0,
    limit: int = 1_000,
    apply: bool = False,
) -> OfferGraphBackfillReport:
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
    counts = {state: 0 for state in ("eligible", "unknown", "ineligible", "quarantine")}
    created = existing = missing_offer_links = 0
    for raw in raws:
        offer_id = await _offer_id(session, raw.id)
        if offer_id is None:
            missing_offer_links += 1
            continue
        projection = project_awin_offer(raw.payload_json)
        evaluation = await evaluate_offer_projection(
            session,
            projection=projection,
            raw_source_record_id=raw.id,
        )
        counts[evaluation.eligibility] += 1
        if not apply:
            continue
        capture = await persist_awin_offer_projection(
            session,
            projection=projection,
            raw_source_record_id=raw.id,
            offer_id=offer_id,
            observed_at=raw.observed_at,
        )
        created += int(capture.created)
        existing += int(not capture.created)
    if apply:
        await session.commit()
    return OfferGraphBackfillReport(
        mode="apply" if apply else "dry_run",
        scanned=len(raws),
        eligible=counts["eligible"],
        unknown=counts["unknown"],
        ineligible=counts["ineligible"],
        quarantine=counts["quarantine"],
        observations_created=created,
        observations_existing=existing,
        missing_offer_links=missing_offer_links,
        last_raw_source_id=raws[-1].id if raws else None,
    )


async def _run(args: argparse.Namespace) -> OfferGraphBackfillReport:
    settings = get_settings()
    configure_logging(settings.debug)
    if args.apply and not (
        settings.observation_shadow_enabled and settings.offer_graph_shadow_enabled
    ):
        raise RuntimeError("observation and offer graph flags are required for --apply")
    if not db.is_enabled():
        raise RuntimeError("DATABASE_URL is required")
    await db.prepare_schema()
    async with db.session_scope() as session:
        if session is None:
            raise RuntimeError("database session unavailable")
        return await backfill_offer_batch(
            session,
            after_raw_id=args.after_raw_id,
            limit=args.limit,
            apply=args.apply,
        )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Backfill Offer Graph shadow")
    parser.add_argument("--after-raw-id", type=int, default=0)
    parser.add_argument("--limit", type=int, default=1_000)
    parser.add_argument("--apply", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        report = asyncio.run(_run(_parser().parse_args(argv)))
    except Exception as exc:
        log.error("Backfill Offer Graph refusé (error_type=%s)", type(exc).__name__)
        return 1
    print(json.dumps(asdict(report), sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
