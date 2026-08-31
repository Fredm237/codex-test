"""Mesure bornée des marchands, dry-run par défaut."""

from __future__ import annotations

import argparse
import asyncio
import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import UTC, datetime

from sqlalchemy import select

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.db import session as db
from app.merchant_intelligence.measurement import (
    measure_merchant_window,
    persist_measurement,
)
from app.observations.models import RawSourceRecord


log = get_logger("merchant_intelligence.backfill")
MAX_BACKFILL_ROWS = 10_000


@dataclass(frozen=True)
class MerchantBackfillReport:
    mode: str
    raw_records: int
    merchants_measured: int
    snapshots_created: int
    snapshots_existing: int
    invalid_raw_records: int
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


async def measure_batch(
    session,
    *,
    evaluated_at: datetime,
    after_raw_id: int = 0,
    limit: int = 1_000,
    apply: bool = False,
) -> MerchantBackfillReport:
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
    grouped: dict[int, list[RawSourceRecord]] = defaultdict(list)
    invalid = 0
    for raw in raws:
        merchant_id = raw.context_json.get("merchant_id")
        if isinstance(merchant_id, bool) or not isinstance(merchant_id, int) or merchant_id <= 0:
            invalid += 1
            continue
        grouped[merchant_id].append(raw)

    created = existing = 0
    for merchant_id in sorted(grouped):
        measurement = await measure_merchant_window(
            session,
            raws=grouped[merchant_id],
            evaluated_at=evaluated_at,
        )
        if not apply:
            continue
        was_created = await persist_measurement(session, measurement)
        created += int(was_created)
        existing += int(not was_created)
    if apply:
        await session.commit()
    return MerchantBackfillReport(
        mode="apply" if apply else "dry_run",
        raw_records=len(raws),
        merchants_measured=len(grouped),
        snapshots_created=created,
        snapshots_existing=existing,
        invalid_raw_records=invalid,
        last_raw_source_id=raws[-1].id if raws else None,
    )


async def _run(args: argparse.Namespace) -> MerchantBackfillReport:
    settings = get_settings()
    configure_logging(settings.debug)
    if args.apply and not (
        settings.observation_shadow_enabled
        and settings.product_graph_shadow_enabled
        and settings.offer_graph_shadow_enabled
        and settings.merchant_intelligence_shadow_enabled
    ):
        raise RuntimeError("all four intelligence shadow flags are required")
    if not db.is_enabled():
        raise RuntimeError("DATABASE_URL is required")
    await db.prepare_schema()
    async with db.session_scope() as session:
        if session is None:
            raise RuntimeError("database session unavailable")
        return await measure_batch(
            session,
            evaluated_at=parse_evaluated_at(args.evaluated_at),
            after_raw_id=args.after_raw_id,
            limit=args.limit,
            apply=args.apply,
        )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Merchant Intelligence shadow")
    parser.add_argument("--evaluated-at", required=True)
    parser.add_argument("--after-raw-id", type=int, default=0)
    parser.add_argument("--limit", type=int, default=1_000)
    parser.add_argument("--apply", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        report = asyncio.run(_run(_parser().parse_args(argv)))
    except Exception as exc:
        log.error("Mesure marchand refusée (error_type=%s)", type(exc).__name__)
        return 1
    print(json.dumps(asdict(report), sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
