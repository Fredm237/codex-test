"""Persistance et replay borné Offer Truth Phase 3E."""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import models as core_models
from app.db.base import Base
from app.observations import models as observation_models
from app.offer_truth import models
from app.offer_truth.replay import OfferTruthReplayError, replay_offer_truth_batch
from app.product_graph import models as graph_models
from app.product_graph.entity_resolution import POLICY_VERSION, RESOLVER_VERSION


OBSERVED_AT = datetime(2026, 9, 1, 9, 0, 0)
EVALUATED_AT = datetime(2026, 9, 1, 10, 0, 0, tzinfo=timezone.utc)


def test_offer_truth_model_loads_foreign_key_dependencies_in_isolation():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from sqlalchemy.orm import configure_mappers; "
                "from app.offer_truth.models import OfferTruthSnapshot; "
                "configure_mappers()"
            ),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr


async def _database():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    return engine, async_sessionmaker(engine, expire_on_commit=False)


async def _seed(session):
    merchant = core_models.Merchant(
        awin_mid=903,
        name="Offer Truth Replay",
        slug="offer-truth-replay",
        joined=True,
    )
    session.add(merchant)
    await session.flush()
    payloads = (
        {"search_price": "99.90", "currency": "EUR", "in_stock": "yes"},
        {"search_price": "49.90", "currency": "EUR", "in_stock": "no"},
        {"currency": "EUR", "in_stock": "yes"},
    )
    raws = []
    offers = []
    for index, payload in enumerate(payloads, start=1):
        offer = core_models.Offer(
            merchant_id=merchant.id,
            awin_product_id=f"truth-{index}",
            name=f"Truth product {index}",
        )
        session.add(offer)
        await session.flush()
        raw = observation_models.RawSourceRecord(
            source_type="awin_feed",
            source_ref="awin-feed:903",
            source_record_key=f"903:truth-{index}",
            schema_version="awin-create-a-feed-v1",
            context_json={"merchant_id": merchant.id},
            payload_json=payload,
            payload_checksum=str(index) * 64,
            replay_key=chr(96 + index) * 64,
            sync_run_id=None,
            observed_at=OBSERVED_AT,
        )
        session.add(raw)
        await session.flush()
        session.add(
            observation_models.Observation(
                raw_source_record_id=raw.id,
                subject_type="offer",
                subject_ref=f"offer:{offer.id}",
                offer_id=offer.id,
                field="name",
                value_json=offer.name,
                status="verified",
                source_type="awin_feed",
                source_ref=raw.source_ref,
                observed_at=OBSERVED_AT,
                transformation="test",
                transformation_version="v1",
                confidence=1.0,
            )
        )
        raws.append(raw)
        offers.append(offer)

    variant = graph_models.GraphVariant(
        variant_key="gtin:offer-truth-replay",
        model_id=None,
        attributes_json={},
        status="shadow",
        resolver_version=RESOLVER_VERSION,
    )
    session.add(variant)
    await session.flush()
    for index in (0, 2):
        raw = raws[index]
        session.add(
            graph_models.GraphEntityResolutionDecision(
                decision_key=str(index + 4) * 64,
                raw_source_record_id=raw.id,
                offer_id=offers[index].id,
                subject_type="variant",
                resolution="EXACT_VERIFIED",
                canonical_variant_id=variant.id,
                candidate_ids_json=[variant.id],
                confidence_score=1.0,
                reason_codes_json=["exact_global_identifier"],
                evidence_json=[],
                conflicts_json=[],
                extractor_version="test-extractor/v1",
                resolver_version=RESOLVER_VERSION,
                policy_version=POLICY_VERSION,
                observed_at=OBSERVED_AT,
            )
        )
    await session.commit()
    return raws


@pytest.mark.asyncio
async def test_replay_is_idempotent_for_the_same_explicit_evaluation():
    engine, maker = await _database()
    try:
        async with maker() as session:
            await _seed(session)
            first = await replay_offer_truth_batch(
                session,
                evaluated_at=EVALUATED_AT,
                limit=10,
                apply=True,
            )
            replay = await replay_offer_truth_batch(
                session,
                evaluated_at=EVALUATED_AT,
                limit=10,
                apply=True,
            )
            assert (first.scanned, first.projected, first.missing_offer_links) == (3, 3, 0)
            assert (first.verified, first.partial, first.quarantined) == (1, 1, 1)
            assert first.snapshots_created == 3
            assert replay.snapshots_created == 0
            assert replay.snapshots_existing == 3
            assert replay.evaluation_id == first.evaluation_id
            rows = (
                (
                    await session.execute(
                        select(models.OfferTruthSnapshot).order_by(
                            models.OfferTruthSnapshot.raw_source_record_id
                        )
                    )
                )
                .scalars()
                .all()
            )
            assert [row.offer_status for row in rows] == [
                "VERIFIED",
                "QUARANTINED",
                "PARTIAL",
            ]
            assert rows[0].claims_json["shipping"]["state"] == "unknown"
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_new_explicit_evaluation_is_a_new_append_only_snapshot():
    engine, maker = await _database()
    try:
        async with maker() as session:
            await _seed(session)
            await replay_offer_truth_batch(
                session,
                evaluated_at=EVALUATED_AT,
                apply=True,
            )
            later = await replay_offer_truth_batch(
                session,
                evaluated_at=EVALUATED_AT + timedelta(hours=1),
                apply=True,
            )
            assert later.snapshots_created == 3
            assert await session.scalar(
                select(func.count()).select_from(models.OfferTruthSnapshot)
            ) == 6
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_same_evaluation_refuses_changed_source_truth():
    engine, maker = await _database()
    try:
        async with maker() as session:
            raws = await _seed(session)
            await replay_offer_truth_batch(
                session,
                evaluated_at=EVALUATED_AT,
                apply=True,
            )
            raws[0].payload_json = {**raws[0].payload_json, "search_price": "100.00"}
            await session.flush()
            with pytest.raises(OfferTruthReplayError, match="replay divergence"):
                await replay_offer_truth_batch(
                    session,
                    evaluated_at=EVALUATED_AT,
                    apply=True,
                )
            await session.rollback()
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_dry_run_never_persists_a_snapshot():
    engine, maker = await _database()
    try:
        async with maker() as session:
            await _seed(session)
            report = await replay_offer_truth_batch(
                session,
                evaluated_at=EVALUATED_AT,
                limit=2,
            )
            assert report.mode == "dry_run"
            assert report.scanned == 2
            assert await session.scalar(
                select(func.count()).select_from(models.OfferTruthSnapshot)
            ) == 0
    finally:
        await engine.dispose()


@pytest.mark.parametrize(
    ("after_raw_id", "limit"),
    [(-1, 1), (True, 1), (0, 0), (0, 10_001), (0, True)],
)
@pytest.mark.asyncio
async def test_replay_window_is_strictly_bounded(after_raw_id, limit):
    engine, maker = await _database()
    try:
        async with maker() as session:
            with pytest.raises(ValueError):
                await replay_offer_truth_batch(
                    session,
                    evaluated_at=EVALUATED_AT,
                    after_raw_id=after_raw_id,
                    limit=limit,
                )
    finally:
        await engine.dispose()
