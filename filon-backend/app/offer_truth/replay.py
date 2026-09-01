"""Replay borné et append-only des snapshots Offer Truth Phase 3."""

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
from app.core.logging import configure_logging, get_logger
from app.db import models as core_models
from app.db import session as db
from app.observations.models import Observation, RawSourceRecord
from app.offer_truth.extraction import (
    EXTRACTOR_VERSION,
    OFFER_TRUTH_POLICY_VERSION,
    extract_awin_offer_truth,
)
from app.offer_truth.models import OfferTruthSnapshot
from app.product_graph.entity_resolution import POLICY_VERSION, RESOLVER_VERSION
from app.product_graph.models import GraphEntityResolutionDecision


log = get_logger("offer_truth.replay")
MAX_REPLAY_ROWS = 10_000
REPORT_SCHEMA_VERSION = "offer-truth-replay-report/v1"


class OfferTruthReplayError(RuntimeError):
    """Replay impossible à prouver sans masquer une divergence."""


@dataclass(frozen=True)
class OfferTruthReplayReport:
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
    stale: int
    invalid: int
    quarantined: int
    snapshots_created: int
    snapshots_existing: int
    last_raw_source_id: int | None
    evaluation_id: str


@dataclass(frozen=True)
class _OfferContext:
    offer_id: int
    merchant_id: int
    merchant_status: str


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
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def _naive_utc(value: datetime) -> datetime:
    return _aware(value).replace(tzinfo=None)


def _validate_window(after_raw_id: int, limit: int) -> tuple[int, int]:
    if isinstance(after_raw_id, bool) or not isinstance(after_raw_id, int) or after_raw_id < 0:
        raise ValueError("after_raw_id must be a non-negative integer")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_REPLAY_ROWS:
        raise ValueError(f"limit must be between 1 and {MAX_REPLAY_ROWS}")
    return after_raw_id, limit


async def _offer_contexts(session, raw_ids: list[int]) -> dict[int, _OfferContext]:
    if not raw_ids:
        return {}
    rows = (
        await session.execute(
            select(
                Observation.raw_source_record_id,
                core_models.Offer.id,
                core_models.Merchant.id,
                core_models.Merchant.joined,
            )
            .join(core_models.Offer, Observation.offer_id == core_models.Offer.id)
            .join(
                core_models.Merchant,
                core_models.Offer.merchant_id == core_models.Merchant.id,
            )
            .where(Observation.raw_source_record_id.in_(raw_ids))
            .distinct()
        )
    ).all()
    grouped: dict[int, set[tuple[int, int, bool]]] = defaultdict(set)
    for raw_id, offer_id, merchant_id, joined in rows:
        grouped[int(raw_id)].add((int(offer_id), int(merchant_id), bool(joined)))
    if any(len(values) > 1 for values in grouped.values()):
        raise OfferTruthReplayError("raw source points to multiple offer contexts")
    return {
        raw_id: _OfferContext(
            offer_id=next(iter(values))[0],
            merchant_id=next(iter(values))[1],
            merchant_status="AFFILIATED" if next(iter(values))[2] else "INDEXED",
        )
        for raw_id, values in grouped.items()
    }


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
                GraphEntityResolutionDecision.policy_version == POLICY_VERSION,
                GraphEntityResolutionDecision.canonical_variant_id.is_not(None),
            )
        )
    ).all()
    grouped: dict[int, set[int]] = defaultdict(set)
    for raw_id, variant_id in rows:
        grouped[int(raw_id)].add(int(variant_id))
    if any(len(values) > 1 for values in grouped.values()):
        raise OfferTruthReplayError("raw source resolves to multiple variants")
    return {raw_id: next(iter(values)) for raw_id, values in grouped.items()}


async def _persist_snapshot(
    session,
    *,
    snapshot: dict[str, Any],
    raw: RawSourceRecord,
) -> bool:
    snapshot_key = _digest(snapshot)
    evaluated_at = datetime.fromisoformat(snapshot["evaluated_at"].replace("Z", "+00:00"))
    existing = await session.scalar(
        select(OfferTruthSnapshot).where(
            OfferTruthSnapshot.raw_source_record_id == raw.id,
            OfferTruthSnapshot.projection_version == EXTRACTOR_VERSION,
            OfferTruthSnapshot.policy_version == OFFER_TRUTH_POLICY_VERSION,
            OfferTruthSnapshot.evaluated_at == _naive_utc(evaluated_at),
        )
    )
    if existing is not None:
        if (
            existing.snapshot_key != snapshot_key
            or existing.claims_json != snapshot["claims"]
            or existing.reason_codes_json != snapshot["reason_codes"]
            or existing.offer_status != snapshot["offer_status"]
            or existing.variant_id != snapshot["variant_id"]
            or existing.merchant_id != snapshot["merchant_id"]
        ):
            raise OfferTruthReplayError("offer truth replay divergence")
        return False
    session.add(
        OfferTruthSnapshot(
            snapshot_key=snapshot_key,
            raw_source_record_id=raw.id,
            offer_id=snapshot["offer_id"],
            variant_id=snapshot["variant_id"],
            merchant_id=snapshot["merchant_id"],
            offer_status=snapshot["offer_status"],
            claims_json=snapshot["claims"],
            reason_codes_json=snapshot["reason_codes"],
            projection_version=EXTRACTOR_VERSION,
            policy_version=OFFER_TRUTH_POLICY_VERSION,
            observed_at=_naive_utc(raw.observed_at),
            evaluated_at=_naive_utc(evaluated_at),
        )
    )
    await session.flush()
    return True


async def replay_offer_truth_batch(
    session,
    *,
    evaluated_at: datetime,
    after_raw_id: int = 0,
    limit: int = 1_000,
    apply: bool = False,
) -> OfferTruthReplayReport:
    """Projette au plus ``limit`` raws pour un instant d'évaluation explicite."""

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
    contexts = await _offer_contexts(session, raw_ids)
    variants = await _variant_map(session, raw_ids)
    projected: list[tuple[RawSourceRecord, dict[str, Any]]] = []
    states: dict[str, int] = defaultdict(int)
    for raw in raws:
        context = contexts.get(raw.id)
        if context is None:
            continue
        snapshot = extract_awin_offer_truth(
            raw.payload_json,
            raw_source_record_id=raw.id,
            source_ref=raw.source_ref,
            observed_at=_aware(raw.observed_at),
            evaluated_at=evaluated,
            offer_id=context.offer_id,
            variant_id=variants.get(raw.id),
            merchant_id=context.merchant_id,
            merchant_status=context.merchant_status,
            relationship_type=context.merchant_status,
            seller_type="direct",
        )
        states[snapshot["offer_status"]] += 1
        projected.append((raw, snapshot))

    created = existing = 0
    if apply:
        for raw, snapshot in projected:
            if await _persist_snapshot(session, snapshot=snapshot, raw=raw):
                created += 1
            else:
                existing += 1
        await session.commit()

    evaluation_id = _digest(
        [
            {
                "raw_source_record_id": raw.id,
                "snapshot": snapshot,
            }
            for raw, snapshot in projected
        ]
    )
    return OfferTruthReplayReport(
        schema_version=REPORT_SCHEMA_VERSION,
        projection_version=EXTRACTOR_VERSION,
        policy_version=OFFER_TRUTH_POLICY_VERSION,
        mode="apply" if apply else "dry_run",
        evaluated_at=evaluated.isoformat().replace("+00:00", "Z"),
        after_raw_id=after_raw_id,
        limit=limit,
        scanned=len(raws),
        projected=len(projected),
        missing_offer_links=len(raws) - len(projected),
        verified=states["VERIFIED"],
        partial=states["PARTIAL"],
        stale=states["STALE"],
        invalid=states["INVALID"],
        quarantined=states["QUARANTINED"],
        snapshots_created=created,
        snapshots_existing=existing,
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


async def _run(args: argparse.Namespace) -> OfferTruthReplayReport:
    settings = get_settings()
    configure_logging(settings.debug)
    if args.apply and not settings.offer_truth_shadow_enabled:
        raise RuntimeError("OFFER_TRUTH_SHADOW_ENABLED is required for --apply")
    if not db.is_enabled():
        raise RuntimeError("DATABASE_URL is required")
    await db.prepare_schema()
    async with db.session_scope() as session:
        if session is None:
            raise RuntimeError("database session unavailable")
        return await replay_offer_truth_batch(
            session,
            evaluated_at=args.evaluated_at,
            after_raw_id=args.after_raw_id,
            limit=args.limit,
            apply=args.apply,
        )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Replay borné Offer Truth shadow Phase 3")
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
