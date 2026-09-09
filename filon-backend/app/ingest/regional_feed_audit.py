"""Audit Awin régional, agrégé, borné et strictement sans écriture.

La commande repère les feeds qui publient réellement des smartphones avec un
GTIN valide avant tout amorçage catalogue. Les lignes sources ne sont jamais
persistées ni imprimées : seul un reçu de compteurs agrégés est produit.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass

from sqlalchemy import select

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.db import models as core_models
from app.db import session as db
from app.services import awin_catalog, taxonomy
from app.services.catalog_grouping import AWIN_GTIN_FIELDS, extract_awin_gtin

log = get_logger("regional_feed_audit")
_MAX_FEEDS = 64
_DEFAULT_MAX_SAMPLED_FEEDS = 12
_MAX_SAMPLE_ROWS = 2_000
_IDENTIFIER_COLUMNS = frozenset(value.casefold() for value in AWIN_GTIN_FIELDS)


@dataclass(frozen=True)
class FeedAuditAggregate:
    feed_id: str
    declared_products: int
    mapped_identifier_fields: tuple[str, ...]
    sample_status: str
    sampled_rows: int = 0
    identifier_supplied_rows: int = 0
    valid_gtin_rows: int = 0
    smartphone_rows: int = 0
    smartphone_valid_gtin_rows: int = 0


@dataclass(frozen=True)
class RegionalFeedAuditReceipt:
    schema_version: str
    status: str
    region: str
    sample_rows_per_feed: int
    eligible_feed_count: int
    sampled_feed_count: int
    qualified_feed_ids: tuple[str, ...]
    recommended_feed_id: str | None
    feeds: tuple[FeedAuditAggregate, ...]
    raw_payload_retained: bool = False
    product_names_retained: bool = False
    prices_retained: bool = False
    urls_retained: bool = False


def _validate_scope(
    *,
    region: str,
    feed_ids: Sequence[str],
    sample_rows: int,
    max_sampled_feeds: int,
) -> tuple[str, tuple[str, ...], int, int]:
    normalized_region = region.strip().upper()
    normalized_ids = tuple(value.strip() for value in feed_ids)
    if not re.fullmatch(r"[A-Z]{2}", normalized_region):
        raise ValueError("region must be an ISO alpha-2 code")
    if (
        len(normalized_ids) > _MAX_FEEDS
        or len(normalized_ids) != len(set(normalized_ids))
        or any(not value.isdigit() for value in normalized_ids)
    ):
        raise ValueError("feed ids must be unique numeric ids")
    if isinstance(sample_rows, bool) or not 0 <= sample_rows <= _MAX_SAMPLE_ROWS:
        raise ValueError(f"sample rows must be between 0 and {_MAX_SAMPLE_ROWS}")
    if (
        isinstance(max_sampled_feeds, bool)
        or not 1 <= max_sampled_feeds <= _MAX_FEEDS
    ):
        raise ValueError(f"max sampled feeds must be between 1 and {_MAX_FEEDS}")
    return normalized_region, normalized_ids, sample_rows, max_sampled_feeds


def _validate_configuration() -> None:
    settings = get_settings()
    if not settings.awin_feed_api_key:
        raise RuntimeError("regional feed audit requires AWIN_FEED_API_KEY")
    if not db.is_enabled():
        raise RuntimeError("regional feed audit requires DATABASE_URL")


def _mapped_identifier_fields(feed: awin_catalog.FeedInfo) -> tuple[str, ...]:
    return tuple(
        field
        for field in feed.mapped_columns
        if field.casefold() in _IDENTIFIER_COLUMNS
    )


def _is_smartphone(row: Mapping[str, object], merchant_name: str) -> bool:
    name = str(row.get("product_name") or "")
    merchant_category = str(row.get("merchant_category") or "")
    brand = str(row.get("brand_name") or "")
    category = taxonomy.classify(
        merchant_category,
        name,
        brand,
        merchant_name,
    )
    return (
        category == taxonomy.TELEPHONIE
        and taxonomy.classify_subcategory(
            category,
            name,
            merchant_category,
            merchant_name,
        )
        == "Smartphones"
    )


def _aggregate_rows(
    feed: awin_catalog.FeedInfo,
    rows: Sequence[Mapping[str, object]],
) -> FeedAuditAggregate:
    identifier_supplied = valid_gtin = smartphones = smartphone_gtin = 0
    for row in rows:
        normalized_gtin, source_field, _ = extract_awin_gtin(row)
        is_smartphone = _is_smartphone(row, feed.advertiser_name)
        identifier_supplied += int(source_field is not None)
        valid_gtin += int(normalized_gtin is not None)
        smartphones += int(is_smartphone)
        smartphone_gtin += int(is_smartphone and normalized_gtin is not None)
    return FeedAuditAggregate(
        feed_id=feed.feed_id,
        declared_products=feed.products,
        mapped_identifier_fields=_mapped_identifier_fields(feed),
        sample_status="sampled",
        sampled_rows=len(rows),
        identifier_supplied_rows=identifier_supplied,
        valid_gtin_rows=valid_gtin,
        smartphone_rows=smartphones,
        smartphone_valid_gtin_rows=smartphone_gtin,
    )


def _recommend(feeds: Sequence[FeedAuditAggregate]) -> tuple[str, ...]:
    candidates = [feed for feed in feeds if feed.smartphone_valid_gtin_rows > 0]
    candidates.sort(
        key=lambda feed: (
            -feed.smartphone_valid_gtin_rows,
            -feed.valid_gtin_rows,
            int(feed.feed_id),
        )
    )
    return tuple(feed.feed_id for feed in candidates)


async def audit(
    *,
    region: str,
    feed_ids: Sequence[str] = (),
    sample_rows: int = 0,
    max_sampled_feeds: int = _DEFAULT_MAX_SAMPLED_FEEDS,
) -> RegionalFeedAuditReceipt:
    """Retourne uniquement les agrégats nécessaires à une sélection sûre."""

    region, requested_ids, sample_rows, max_sampled_feeds = _validate_scope(
        region=region,
        feed_ids=feed_ids,
        sample_rows=sample_rows,
        max_sampled_feeds=max_sampled_feeds,
    )
    _validate_configuration()

    async with db.session_scope() as session:
        if session is None:
            raise RuntimeError("regional feed audit database session unavailable")
        joined_mids = set(
            (
                await session.scalars(
                    select(core_models.Merchant.awin_mid).where(
                        core_models.Merchant.joined.is_(True)
                    )
                )
            ).all()
        )

    available = [
        feed
        for feed in await awin_catalog.list_feeds()
        if feed.advertiser_id in joined_mids and feed.region == region
    ]
    available_by_id = {feed.feed_id: feed for feed in available}
    if requested_ids:
        if any(feed_id not in available_by_id for feed_id in requested_ids):
            return RegionalFeedAuditReceipt(
                schema_version="v2-regional-feed-audit/v1",
                status="scope_unavailable",
                region=region,
                sample_rows_per_feed=sample_rows,
                eligible_feed_count=len(available),
                sampled_feed_count=0,
                qualified_feed_ids=(),
                recommended_feed_id=None,
                feeds=(),
            )
        scoped = [available_by_id[feed_id] for feed_id in requested_ids]
    else:
        scoped = sorted(available, key=lambda feed: int(feed.feed_id))

    if sample_rows == 0:
        aggregates = tuple(
            FeedAuditAggregate(
                feed_id=feed.feed_id,
                declared_products=feed.products,
                mapped_identifier_fields=_mapped_identifier_fields(feed),
                sample_status="metadata_only",
            )
            for feed in scoped
        )
        return RegionalFeedAuditReceipt(
            schema_version="v2-regional-feed-audit/v1",
            status="metadata_only",
            region=region,
            sample_rows_per_feed=0,
            eligible_feed_count=len(available),
            sampled_feed_count=0,
            qualified_feed_ids=(),
            recommended_feed_id=None,
            feeds=aggregates,
        )

    # Sans sélection explicite, seuls les feeds annonçant une colonne globale
    # sont téléchargés. Une sélection explicite peut auditer un ancien feed
    # dont l'URL ne fournit pas les métadonnées de colonnes.
    candidates = (
        scoped
        if requested_ids
        else [feed for feed in scoped if _mapped_identifier_fields(feed)]
    )[:max_sampled_feeds]
    results: list[FeedAuditAggregate] = []
    failures = 0
    for feed in candidates:
        try:
            rows = await awin_catalog._download_feed_rows(
                [feed.feed_id],
                max_rows=sample_rows,
            )
        except Exception as exc:  # noqa: BLE001  # pragma: no cover - fournisseur réel
            failures += 1
            log.warning(
                "Regional feed sample unavailable (error_type=%s)",
                type(exc).__name__,
            )
            results.append(
                FeedAuditAggregate(
                    feed_id=feed.feed_id,
                    declared_products=feed.products,
                    mapped_identifier_fields=_mapped_identifier_fields(feed),
                    sample_status="download_failed",
                )
            )
            continue
        results.append(_aggregate_rows(feed, rows))

    qualified_ids = _recommend(results)
    status = (
        "qualified"
        if qualified_ids
        else "partial"
        if failures
        else "no_qualified_feed"
    )
    return RegionalFeedAuditReceipt(
        schema_version="v2-regional-feed-audit/v1",
        status=status,
        region=region,
        sample_rows_per_feed=sample_rows,
        eligible_feed_count=len(available),
        sampled_feed_count=sum(feed.sample_status == "sampled" for feed in results),
        qualified_feed_ids=qualified_ids,
        recommended_feed_id=qualified_ids[0] if qualified_ids else None,
        feeds=tuple(results),
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only regional Awin feed audit")
    parser.add_argument("--region", required=True)
    parser.add_argument("--feed-id", action="append", default=[], dest="feed_ids")
    parser.add_argument("--sample-rows", type=int, default=0)
    parser.add_argument(
        "--max-sampled-feeds",
        type=int,
        default=_DEFAULT_MAX_SAMPLED_FEEDS,
    )
    return parser


def main(argv: Sequence[str] = ()) -> int:
    try:
        arguments = _parser().parse_args(tuple(argv))
        configure_logging(get_settings().debug)
        receipt = asyncio.run(
            audit(
                region=arguments.region,
                feed_ids=arguments.feed_ids,
                sample_rows=arguments.sample_rows,
                max_sampled_feeds=arguments.max_sampled_feeds,
            )
        )
        print(json.dumps(asdict(receipt), separators=(",", ":"), sort_keys=True))
        return 0 if receipt.status in {"metadata_only", "qualified"} else 1
    except Exception as exc:  # noqa: BLE001  # pragma: no cover - dépendances réelles
        log.error("Regional feed audit failed (error_type=%s)", type(exc).__name__)
        return 1


if __name__ == "__main__":
    import sys

    raise SystemExit(main(tuple(sys.argv[1:])))
