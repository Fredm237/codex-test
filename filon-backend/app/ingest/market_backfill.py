"""Rattrapage borné des preuves de marché de publication Awin."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import re
from collections.abc import Sequence
from dataclasses import asdict, dataclass

from sqlalchemy import select

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.db import session as db
from app.observations.awin import persist_projection, project_awin_row
from app.observations.models import Observation, RawSourceRecord
from app.services.awin_catalog import list_feeds


log = get_logger("listing_market_backfill")
MAX_ROWS = 5_000


@dataclass(frozen=True)
class MarketBackfillReceipt:
    schema_version: str
    status: str
    country_code: str
    after_raw_id: int
    through_raw_id: int
    limit: int
    selected: int
    eligible: int
    existing: int
    created: int
    final_state_digest: str
    raw_payload_retained: bool = False


def _scope(
    *, country_code: str, after_raw_id: int, through_raw_id: int, limit: int
) -> tuple[str, int, int, int]:
    country = country_code.strip().upper()
    if not re.fullmatch(r"[A-Z]{2}", country):
        raise ValueError("country must be an ISO alpha-2 code")
    if after_raw_id < 0 or through_raw_id <= after_raw_id:
        raise ValueError("raw id bounds are invalid")
    if isinstance(limit, bool) or not 1 <= limit <= MAX_ROWS:
        raise ValueError(f"limit must be between 1 and {MAX_ROWS}")
    return country, after_raw_id, through_raw_id, limit


def _digest(values: Sequence[tuple[int, int, str]]) -> str:
    canonical = json.dumps(tuple(values), separators=(",", ":"))
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


async def run(
    *,
    country_code: str,
    after_raw_id: int,
    through_raw_id: int,
    limit: int,
    apply: bool,
) -> MarketBackfillReceipt:
    country, lower, upper, limit = _scope(
        country_code=country_code,
        after_raw_id=after_raw_id,
        through_raw_id=through_raw_id,
        limit=limit,
    )
    await db.prepare_schema()
    feed_ids = {
        feed.feed_id
        for feed in await list_feeds()
        if feed.region == country
    }
    source_refs = tuple(sorted(f"awin-feed:{feed_id}" for feed_id in feed_ids))
    async with db.session_scope() as session:
        if session is None:
            raise RuntimeError("listing market backfill requires DATABASE_URL")
        raws = (
            (
                await session.scalars(
                    select(RawSourceRecord)
                    .where(
                        RawSourceRecord.id > lower,
                        RawSourceRecord.id <= upper,
                        RawSourceRecord.source_type == "awin_feed",
                        RawSourceRecord.source_ref.in_(source_refs),
                    )
                    .order_by(RawSourceRecord.id)
                    .limit(limit)
                )
            ).all()
            if source_refs
            else []
        )
        eligible_raws = list(raws)
        raw_ids = tuple(raw.id for raw in eligible_raws)
        offer_rows = (
            (
                await session.execute(
                    select(Observation.raw_source_record_id, Observation.offer_id)
                    .where(
                        Observation.raw_source_record_id.in_(raw_ids),
                        Observation.offer_id.is_not(None),
                    )
                    .order_by(Observation.raw_source_record_id, Observation.id)
                )
            ).all()
            if raw_ids
            else []
        )
        offer_by_raw: dict[int, int] = {}
        for raw_id, offer_id in offer_rows:
            offer_by_raw.setdefault(raw_id, offer_id)
        existing_rows = (
            (
                await session.execute(
                    select(
                        Observation.raw_source_record_id,
                        Observation.offer_id,
                        Observation.value_json,
                    ).where(
                        Observation.raw_source_record_id.in_(raw_ids),
                        Observation.field == "listing_market",
                        Observation.status == "verified",
                    )
                )
            ).all()
            if raw_ids
            else []
        )
        existing_ids = {
            raw_id
            for raw_id, _offer_id, value in existing_rows
            if value == country
        }
        created = 0
        if apply:
            for raw in eligible_raws:
                offer_id = offer_by_raw.get(raw.id)
                if offer_id is None or raw.id in existing_ids:
                    continue
                projection = project_awin_row(
                    raw.payload_json,
                    feed_id=str(
                        raw.context_json.get("feed_id")
                        or raw.source_ref.rsplit(":", 1)[-1]
                    ),
                    merchant_id=int(raw.context_json["merchant_id"]),
                    merchant_name=raw.context_json.get("merchant_name"),
                    listing_market_country=country,
                    observed_at=raw.observed_at,
                )
                result = await persist_projection(
                    session,
                    projection,
                    offer_id=offer_id,
                    sync_run_id=raw.sync_run_id,
                )
                if result.observations_created:
                    created += 1
            await session.commit()
        final_values = sorted(
            (raw.id, offer_by_raw[raw.id], country)
            for raw in eligible_raws
            if raw.id in offer_by_raw
        )
    return MarketBackfillReceipt(
        schema_version="listing-market-backfill-receipt/v1",
        status="applied" if apply else "dry_run",
        country_code=country,
        after_raw_id=lower,
        through_raw_id=upper,
        limit=limit,
        selected=len(raws),
        eligible=len(eligible_raws),
        existing=len(existing_ids),
        created=created,
        final_state_digest=_digest(final_values),
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bounded listing-market backfill")
    parser.add_argument("--country", required=True, dest="country_code")
    parser.add_argument("--after-raw-id", required=True, type=int)
    parser.add_argument("--through-raw-id", required=True, type=int)
    parser.add_argument("--limit", required=True, type=int)
    parser.add_argument("--apply", action="store_true")
    return parser


def main(argv: Sequence[str] = ()) -> int:
    try:
        arguments = _parser().parse_args(tuple(argv))
        configure_logging(get_settings().debug)
        receipt = asyncio.run(run(**vars(arguments)))
        print(json.dumps(asdict(receipt), separators=(",", ":"), sort_keys=True))
        return 0
    except Exception as exc:  # pragma: no cover - dépendances réelles
        log.error("Listing-market backfill failed (error_type=%s)", type(exc).__name__)
        return 1


if __name__ == "__main__":
    import sys

    raise SystemExit(main(tuple(sys.argv[1:])))
