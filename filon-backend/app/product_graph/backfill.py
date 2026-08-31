"""Backfill borné et rejouable du Product/Variant Graph shadow.

La commande est en lecture seule par défaut. ``--apply`` exige les deux flags
shadow et ne sert jamais le Graph aux lecteurs v1.
"""

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
from app.product_graph.resolution import (
    persist_awin_graph_projection,
    project_awin_variant,
)


log = get_logger("product_graph.backfill")
MAX_BACKFILL_ROWS = 10_000


@dataclass(frozen=True)
class GraphBackfillReport:
    mode: str
    scanned: int
    resolved: int
    quarantined: int
    links_created: int
    links_existing: int
    variants_created: int
    missing_offer_links: int
    last_raw_source_id: int | None


def _validated_window(after_raw_id: int, limit: int) -> tuple[int, int]:
    if isinstance(after_raw_id, bool) or after_raw_id < 0:
        raise ValueError("after_raw_id must be a non-negative integer")
    if isinstance(limit, bool) or not 1 <= limit <= MAX_BACKFILL_ROWS:
        raise ValueError(f"limit must be between 1 and {MAX_BACKFILL_ROWS}")
    return after_raw_id, limit


async def _offer_id_for_raw(session, raw_source_record_id: int) -> int | None:
    values = (
        (
            await session.execute(
                select(Observation.offer_id)
                .where(
                    Observation.raw_source_record_id == raw_source_record_id,
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


async def backfill_batch(
    session,
    *,
    after_raw_id: int = 0,
    limit: int = 1_000,
    apply: bool = False,
) -> GraphBackfillReport:
    """Projette au plus ``limit`` raws Awin, en ordre primaire stable."""

    after_raw_id, limit = _validated_window(after_raw_id, limit)
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
    resolved = quarantined = 0
    links_created = links_existing = variants_created = 0
    missing_offer_links = 0
    for raw in raws:
        offer_id = await _offer_id_for_raw(session, raw.id)
        if offer_id is None:
            missing_offer_links += 1
            continue
        projection = project_awin_variant(raw.payload_json)
        if projection.resolution == "resolved":
            resolved += 1
        else:
            quarantined += 1
        if not apply:
            continue
        captured = await persist_awin_graph_projection(
            session,
            projection=projection,
            raw_source_record_id=raw.id,
            offer_id=offer_id,
            source_ref=raw.source_ref,
            observed_at=raw.observed_at,
        )
        links_created += int(captured.link_created)
        links_existing += int(not captured.link_created)
        variants_created += int(captured.variant_created)

    if apply:
        await session.commit()
    return GraphBackfillReport(
        mode="apply" if apply else "dry_run",
        scanned=len(raws),
        resolved=resolved,
        quarantined=quarantined,
        links_created=links_created,
        links_existing=links_existing,
        variants_created=variants_created,
        missing_offer_links=missing_offer_links,
        last_raw_source_id=raws[-1].id if raws else None,
    )


async def _run(args: argparse.Namespace) -> GraphBackfillReport:
    settings = get_settings()
    configure_logging(settings.debug)
    if args.apply and not (
        settings.observation_shadow_enabled
        and settings.product_graph_shadow_enabled
    ):
        raise RuntimeError("both shadow flags are required for --apply")
    if not db.is_enabled():
        raise RuntimeError("DATABASE_URL is required")
    await db.prepare_schema()
    async with db.session_scope() as session:
        if session is None:
            raise RuntimeError("database session unavailable")
        return await backfill_batch(
            session,
            after_raw_id=args.after_raw_id,
            limit=args.limit,
            apply=args.apply,
        )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Backfill borné du Product/Variant Graph shadow",
    )
    parser.add_argument("--after-raw-id", type=int, default=0)
    parser.add_argument("--limit", type=int, default=1_000)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="persiste le lot ; sans ce drapeau, la commande reste en lecture seule",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        report = asyncio.run(_run(_parser().parse_args(argv)))
    except Exception as exc:
        log.error("Backfill Graph refusé (error_type=%s)", type(exc).__name__)
        return 1
    print(json.dumps(asdict(report), sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":  # pragma: no cover - frontière CLI
    raise SystemExit(main())
