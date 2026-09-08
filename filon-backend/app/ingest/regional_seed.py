"""Amorçage régional Awin, explicite, borné et journalisé.

Cette commande de maintenance ne choisit jamais le premier feed disponible.
L'opérateur fournit la région et les identifiants préqualifiés ; le writer
catalogue habituel conserve alors les mêmes upserts, preuves brutes,
checkpoints, heartbeats et protections de concurrence qu'un cycle normal.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
from collections.abc import Sequence
from dataclasses import asdict, dataclass

from sqlalchemy import select

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.db import models as core_models
from app.db import session as db
from app.services import awin_catalog, catalog_sync
from app.v2_chain.models import V2ChainExecution


log = get_logger("regional_catalog_seed")
_MAX_FEEDS = 8
_MAX_ROWS = 20_000


@dataclass(frozen=True)
class RegionalSeedReceipt:
    schema_version: str
    status: str
    region: str
    feed_ids: tuple[str, ...]
    row_limit: int
    declared_products: int
    catalog_run_id: int | None = None
    feeds: int = 0
    offers: int = 0
    skipped_feeds: int = 0
    raw_payload_retained: bool = False


def _validate_scope(
    *,
    region: str,
    feed_ids: Sequence[str],
    row_limit: int,
) -> tuple[str, tuple[str, ...], int]:
    normalized_region = region.strip().upper()
    normalized_ids = tuple(value.strip() for value in feed_ids)
    if not re.fullmatch(r"[A-Z]{2}", normalized_region):
        raise ValueError("region must be an ISO alpha-2 code")
    if (
        not normalized_ids
        or len(normalized_ids) > _MAX_FEEDS
        or len(normalized_ids) != len(set(normalized_ids))
        or any(not value.isdigit() for value in normalized_ids)
    ):
        raise ValueError("feed ids must be one to eight unique numeric ids")
    if isinstance(row_limit, bool) or not 1 <= row_limit <= _MAX_ROWS:
        raise ValueError(f"row limit must be between 1 and {_MAX_ROWS}")
    return normalized_region, normalized_ids, row_limit


def _validate_configuration(*, row_limit: int) -> None:
    settings = get_settings()
    if settings.database_schema_mode != "alembic":
        raise RuntimeError("regional seed requires DATABASE_SCHEMA_MODE=alembic")
    if not settings.awin_api_token or not settings.awin_feed_api_key:
        raise RuntimeError("regional seed requires Awin credentials")
    if not db.is_enabled():
        raise RuntimeError("regional seed requires DATABASE_URL")
    if settings.awin_max_rows_per_feed and row_limit > settings.awin_max_rows_per_feed:
        raise RuntimeError("regional seed row limit exceeds configured bound")


async def _scope_state(
    session,
    *,
    region: str,
    feed_ids: tuple[str, ...],
) -> tuple[str, int]:
    if await session.scalar(
        select(core_models.CatalogSyncRun.id)
        .where(core_models.CatalogSyncRun.status == "running")
        .limit(1)
    ):
        return "catalog_syncing", 0
    if await session.scalar(
        select(V2ChainExecution.id)
        .where(V2ChainExecution.status == "running")
        .limit(1)
    ):
        return "v2_running", 0

    joined_mids = set(
        (
            await session.scalars(
                select(core_models.Merchant.awin_mid).where(
                    core_models.Merchant.joined.is_(True)
                )
            )
        ).all()
    )
    feeds = await awin_catalog.list_feeds()
    eligible = {
        feed.feed_id: feed
        for feed in feeds
        if feed.advertiser_id in joined_mids and feed.region == region
    }
    if any(feed_id not in eligible for feed_id in feed_ids):
        return "feed_scope_unavailable", 0
    return "ready", sum(eligible[feed_id].products for feed_id in feed_ids)


async def preflight(
    *,
    region: str,
    feed_ids: Sequence[str],
    row_limit: int,
) -> RegionalSeedReceipt:
    """Vérifie le scope réel sans lancer de writer ni retenir de payload."""

    region, feed_ids, row_limit = _validate_scope(
        region=region,
        feed_ids=feed_ids,
        row_limit=row_limit,
    )
    _validate_configuration(row_limit=row_limit)
    await db.prepare_schema()
    async with db.session_scope() as session:
        if session is None:
            raise RuntimeError("regional seed database session unavailable")
        status, declared_products = await _scope_state(
            session,
            region=region,
            feed_ids=feed_ids,
        )
    return RegionalSeedReceipt(
        schema_version="regional-catalog-seed-receipt/v1",
        status=status,
        region=region,
        feed_ids=feed_ids,
        row_limit=row_limit,
        declared_products=declared_products,
    )


async def run_once(
    *,
    region: str,
    feed_ids: Sequence[str],
    row_limit: int,
) -> RegionalSeedReceipt:
    """Exécute exactement le scope préqualifié sous le lease catalogue."""

    checked = await preflight(
        region=region,
        feed_ids=feed_ids,
        row_limit=row_limit,
    )
    if checked.status != "ready":
        return checked

    async with db.session_scope() as session:
        if session is None:
            raise RuntimeError("regional seed database session unavailable")
        result = await catalog_sync.run_catalog_sync(
            session,
            trigger="regional_seed",
            limit_override=len(checked.feed_ids),
            region_override=checked.region,
            feed_ids_override=checked.feed_ids,
            max_rows_override=checked.row_limit,
        )
    if result.get("started") is False:
        return RegionalSeedReceipt(
            **{
                **asdict(checked),
                "status": str(result.get("status") or "already_running"),
            }
        )
    run = result.get("run")
    if not isinstance(run, dict):
        raise RuntimeError("regional seed returned an invalid catalog receipt")
    return RegionalSeedReceipt(
        **{
            **asdict(checked),
            "status": str(run.get("status") or "invalid"),
            "catalog_run_id": int(run["id"]),
            "feeds": int(run.get("feeds") or 0),
            "offers": int(run.get("offers") or 0),
            "skipped_feeds": int(run.get("skipped_feeds") or 0),
        }
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bounded regional Awin seed")
    parser.add_argument("--region", required=True)
    parser.add_argument("--feed-id", action="append", required=True, dest="feed_ids")
    parser.add_argument("--max-rows", type=int, required=True, dest="row_limit")
    parser.add_argument("--check", action="store_true")
    return parser


def main(argv: Sequence[str] = ()) -> int:
    try:
        arguments = _parser().parse_args(tuple(argv))
        configure_logging(get_settings().debug)
        operation = preflight if arguments.check else run_once
        receipt = asyncio.run(
            operation(
                region=arguments.region,
                feed_ids=arguments.feed_ids,
                row_limit=arguments.row_limit,
            )
        )
        print(json.dumps(asdict(receipt), separators=(",", ":"), sort_keys=True))
        allowed = {"ready"} if arguments.check else {"succeeded"}
        return 0 if receipt.status in allowed else 1
    except Exception as exc:  # pragma: no cover - dépendances réelles
        log.error("Regional seed failed (error_type=%s)", type(exc).__name__)
        return 1


if __name__ == "__main__":
    import sys

    raise SystemExit(main(tuple(sys.argv[1:])))
