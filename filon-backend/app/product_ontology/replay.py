"""Replay borné et append-only Product Ontology Phase 4."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db import models as core_models
from app.db import session as db
from app.observations.models import Observation, RawSourceRecord
from app.product_graph.entity_resolution import POLICY_VERSION as ENTITY_POLICY_VERSION
from app.product_graph.entity_resolution import RESOLVER_VERSION
from app.product_graph.models import GraphEntityResolutionDecision
from app.product_ontology.extraction import (
    EXTRACTOR_VERSION,
    POLICY_VERSION,
    extract_product_ontology,
)
from app.product_ontology.models import ProductOntologySnapshot


MAX_REPLAY_ROWS = 10_000
REPORT_SCHEMA_VERSION = "product-ontology-replay-report/v1"


class ProductOntologyReplayError(RuntimeError):
    """Replay impossible à prouver sans masquer une divergence."""


@dataclass(frozen=True)
class ProductOntologyReplayReport:
    schema_version: str
    projection_version: str
    policy_version: str
    mode: str
    evaluated_at: str
    after_raw_id: int
    limit: int
    scanned: int
    projected: int
    missing_offer_links: int
    verified: int
    partial: int
    quarantined: int
    invalid: int
    snapshots_created: int
    snapshots_existing: int
    last_raw_source_id: int | None
    evaluation_id: str


def _canonical(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _naive_utc(value: datetime) -> datetime:
    return _aware(value).replace(tzinfo=None)


def _validate_window(after_raw_id: int, limit: int) -> tuple[int, int]:
    if (
        isinstance(after_raw_id, bool)
        or not isinstance(after_raw_id, int)
        or after_raw_id < 0
    ):
        raise ValueError("after_raw_id must be a non-negative integer")
    if (
        isinstance(limit, bool)
        or not isinstance(limit, int)
        or not 1 <= limit <= MAX_REPLAY_ROWS
    ):
        raise ValueError(f"limit must be between 1 and {MAX_REPLAY_ROWS}")
    return after_raw_id, limit


async def _offer_map(session, raw_ids: list[int]) -> dict[int, int]:
    if not raw_ids:
        return {}
    rows = (
        await session.execute(
            select(Observation.raw_source_record_id, core_models.Offer.id)
            .join(core_models.Offer, Observation.offer_id == core_models.Offer.id)
            .where(Observation.raw_source_record_id.in_(raw_ids))
            .distinct()
        )
    ).all()
    grouped: dict[int, set[int]] = defaultdict(set)
    for raw_id, offer_id in rows:
        grouped[int(raw_id)].add(int(offer_id))
    if any(len(values) > 1 for values in grouped.values()):
        raise ProductOntologyReplayError("raw source points to multiple offers")
    return {raw_id: next(iter(values)) for raw_id, values in grouped.items()}


async def _variant_map(session, raw_ids: list[int]) -> dict[int, int]:
    if not raw_ids:
        return {}
    rows = (
        await session.execute(
            select(
                GraphEntityResolutionDecision.raw_source_record_id,
                GraphEntityResolutionDecision.canonical_variant_id,
            ).where(
                GraphEntityResolutionDecision.raw_source_record_id.in_(raw_ids),
                GraphEntityResolutionDecision.resolver_version == RESOLVER_VERSION,
                GraphEntityResolutionDecision.policy_version == ENTITY_POLICY_VERSION,
                GraphEntityResolutionDecision.canonical_variant_id.is_not(None),
            )
        )
    ).all()
    grouped: dict[int, set[int]] = defaultdict(set)
    for raw_id, variant_id in rows:
        grouped[int(raw_id)].add(int(variant_id))
    if any(len(values) > 1 for values in grouped.values()):
        raise ProductOntologyReplayError("raw source resolves to multiple variants")
    return {raw_id: next(iter(values)) for raw_id, values in grouped.items()}


async def _existing_map(
    session,
    *,
    raw_ids: list[int],
    evaluated_at: datetime,
) -> dict[int, ProductOntologySnapshot]:
    if not raw_ids:
        return {}
    rows = (
        (
            await session.execute(
                select(ProductOntologySnapshot).where(
                    ProductOntologySnapshot.raw_source_record_id.in_(raw_ids),
                    ProductOntologySnapshot.projection_version == EXTRACTOR_VERSION,
                    ProductOntologySnapshot.policy_version == POLICY_VERSION,
                    ProductOntologySnapshot.evaluated_at
                    == _naive_utc(evaluated_at),
                )
            )
        )
        .scalars()
        .all()
    )
    return {row.raw_source_record_id: row for row in rows}


def _assert_existing(
    existing: ProductOntologySnapshot,
    *,
    snapshot: dict[str, Any],
    snapshot_key: str,
) -> None:
    if (
        existing.snapshot_key != snapshot_key
        or existing.offer_id != snapshot["offer_id"]
        or existing.variant_id != snapshot["variant_id"]
        or existing.ontology_status != snapshot["ontology_status"]
        or existing.classification_json != snapshot["classification"]
        or existing.product_role_json != snapshot["product_role"]
        or existing.attributes_json != snapshot["attributes"]
        or existing.relationships_json != snapshot["relationships"]
        or existing.facets_json != snapshot["facets"]
        or existing.legacy_taxonomy_json != snapshot["legacy_taxonomy"]
        or existing.reason_codes_json != snapshot["reason_codes"]
    ):
        raise ProductOntologyReplayError("product ontology replay divergence")


async def replay_product_ontology_batch(
    session,
    *,
    evaluated_at: datetime,
    after_raw_id: int = 0,
    limit: int = 1_000,
    apply: bool = False,
) -> ProductOntologyReplayReport:
    """Projette au plus ``limit`` raws ; aucune écriture sans ``apply``."""

    after_raw_id, limit = _validate_window(after_raw_id, limit)
    evaluated = _aware(evaluated_at)
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
    offers = await _offer_map(session, raw_ids)
    variants = await _variant_map(session, raw_ids)
    projected: list[tuple[RawSourceRecord, dict[str, Any]]] = []
    states: dict[str, int] = defaultdict(int)
    for raw in raws:
        offer_id = offers.get(raw.id)
        if offer_id is None:
            continue
        snapshot = extract_product_ontology(
            raw.payload_json,
            raw_source_record_id=raw.id,
            source_type=raw.source_type,
            source_ref=raw.source_ref,
            observed_at=_aware(raw.observed_at),
            evaluated_at=evaluated,
            offer_id=offer_id,
            variant_id=variants.get(raw.id),
        )
        states[snapshot["ontology_status"]] += 1
        projected.append((raw, snapshot))

    created = existing_count = 0
    if apply:
        existing = await _existing_map(
            session,
            raw_ids=[raw.id for raw, _snapshot in projected],
            evaluated_at=evaluated,
        )
        pending: list[ProductOntologySnapshot] = []
        for raw, snapshot in projected:
            snapshot_key = _digest(snapshot)
            current = existing.get(raw.id)
            if current is not None:
                _assert_existing(current, snapshot=snapshot, snapshot_key=snapshot_key)
                existing_count += 1
                continue
            pending.append(
                ProductOntologySnapshot(
                    snapshot_key=snapshot_key,
                    raw_source_record_id=raw.id,
                    offer_id=snapshot["offer_id"],
                    variant_id=snapshot["variant_id"],
                    ontology_status=snapshot["ontology_status"],
                    classification_json=snapshot["classification"],
                    product_role_json=snapshot["product_role"],
                    attributes_json=snapshot["attributes"],
                    relationships_json=snapshot["relationships"],
                    facets_json=snapshot["facets"],
                    legacy_taxonomy_json=snapshot["legacy_taxonomy"],
                    reason_codes_json=snapshot["reason_codes"],
                    projection_version=EXTRACTOR_VERSION,
                    policy_version=POLICY_VERSION,
                    observed_at=_naive_utc(raw.observed_at),
                    evaluated_at=_naive_utc(evaluated),
                )
            )
        session.add_all(pending)
        await session.flush()
        created = len(pending)
        await session.commit()

    evaluation_id = _digest(
        [
            {"raw_source_record_id": raw.id, "snapshot": snapshot}
            for raw, snapshot in projected
        ]
    )
    return ProductOntologyReplayReport(
        schema_version=REPORT_SCHEMA_VERSION,
        projection_version=EXTRACTOR_VERSION,
        policy_version=POLICY_VERSION,
        mode="apply" if apply else "dry_run",
        evaluated_at=evaluated.isoformat().replace("+00:00", "Z"),
        after_raw_id=after_raw_id,
        limit=limit,
        scanned=len(raws),
        projected=len(projected),
        missing_offer_links=len(raws) - len(projected),
        verified=states["VERIFIED"],
        partial=states["PARTIAL"],
        quarantined=states["QUARANTINED"],
        invalid=states["INVALID"],
        snapshots_created=created,
        snapshots_existing=existing_count,
        last_raw_source_id=raws[-1].id if raws else None,
        evaluation_id=f"sha256:{evaluation_id}",
    )


def _parse_evaluated_at(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise argparse.ArgumentTypeError("evaluated-at must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise argparse.ArgumentTypeError("evaluated-at must include a timezone")
    return parsed


async def _run(args: argparse.Namespace) -> ProductOntologyReplayReport:
    settings = get_settings()
    configure_logging(settings.debug)
    if args.apply and not settings.product_ontology_shadow_enabled:
        raise RuntimeError("PRODUCT_ONTOLOGY_SHADOW_ENABLED is required for --apply")
    if not db.is_enabled():
        raise RuntimeError("DATABASE_URL is required")
    await db.prepare_schema()
    async with db.session_scope() as session:
        if session is None:
            raise RuntimeError("database session unavailable")
        return await replay_product_ontology_batch(
            session,
            evaluated_at=args.evaluated_at,
            after_raw_id=args.after_raw_id,
            limit=args.limit,
            apply=args.apply,
        )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Replay borné Product Ontology shadow Phase 4"
    )
    parser.add_argument("--evaluated-at", required=True, type=_parse_evaluated_at)
    parser.add_argument("--after-raw-id", type=int, default=0)
    parser.add_argument("--limit", type=int, default=1_000)
    parser.add_argument("--apply", action="store_true")
    return parser


def main() -> None:
    report = asyncio.run(_run(_parser().parse_args()))
    print(json.dumps(asdict(report), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
