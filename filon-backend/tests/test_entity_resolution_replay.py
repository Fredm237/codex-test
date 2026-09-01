"""Persistance et replay borné Entity Resolution Phase 2F."""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import models as core_models
from app.db.base import Base
from app.observations import models as observation_models
from app.product_graph import models
from app.product_graph.entity_replay import (
    EntityReplayError,
    replay_entity_resolution_batch,
)
from app.product_graph.resolution import RESOLVER_VERSION as GRAPH_RESOLVER_VERSION


OBSERVED_AT = datetime(2026, 9, 1, 1, 0, 0)


def test_product_graph_models_load_their_foreign_key_dependencies_in_isolation():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from sqlalchemy.orm import configure_mappers; "
                "from app.product_graph.models import "
                "GraphEntityResolutionDecision; "
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
    merchant = core_models.Merchant(awin_mid=902, name="Replay", slug="replay")
    session.add(merchant)
    await session.flush()
    payloads = (
        {
            "ean": "4006381333931",
            "brand_name": "Acme",
            "mpn": "P-1",
            "model": "Prime",
            "product_name": "Acme Prime",
        },
        {
            "brand_name": "Acme",
            "mpn": "P-1",
            "model": "Prime",
            "product_name": "Acme Prime renewed",
        },
        {"product_name": "Unknown object"},
    )
    raws = []
    offers = []
    for index, payload in enumerate(payloads, start=1):
        offer = core_models.Offer(
            merchant_id=merchant.id,
            awin_product_id=f"sku-{index}",
            name=str(payload["product_name"]),
        )
        session.add(offer)
        await session.flush()
        raw = observation_models.RawSourceRecord(
            source_type="awin_feed",
            source_ref="awin-feed:902",
            source_record_key=f"902:sku-{index}",
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

    variant = models.GraphVariant(
        variant_key="gtin:4006381333931",
        model_id=None,
        attributes_json={},
        status="shadow",
        resolver_version=GRAPH_RESOLVER_VERSION,
    )
    session.add(variant)
    await session.flush()
    session.add(
        models.GraphOfferVariantLink(
            raw_source_record_id=raws[0].id,
            offer_id=offers[0].id,
            variant_id=variant.id,
            resolution="resolved",
            reason_code="exact_gtin",
            resolver_version=GRAPH_RESOLVER_VERSION,
            observed_at=OBSERVED_AT,
        )
    )
    await session.commit()
    return raws, variant


@pytest.mark.asyncio
async def test_realistic_replay_is_idempotent_and_keeps_five_state_truth():
    engine, maker = await _database()
    try:
        async with maker() as session:
            _raws, variant = await _seed(session)
            first = await replay_entity_resolution_batch(session, limit=10, apply=True)
            replay = await replay_entity_resolution_batch(session, limit=10, apply=True)

            assert (first.scanned, first.projected, first.missing_offer_links) == (3, 3, 0)
            assert first.exact_verified == 1
            assert first.high_confidence == 1
            assert first.probable == 0
            assert first.ambiguous == 0
            assert first.unresolved == 1
            assert first.signal_projections_created == 3
            assert first.decisions_created == 3
            assert replay.evaluation_id == first.evaluation_id
            assert replay.signal_projections_created == 0
            assert replay.signal_projections_existing == 3
            assert replay.decisions_created == 0
            assert replay.decisions_existing == 3

            decisions = (
                (
                    await session.execute(
                        select(models.GraphEntityResolutionDecision).order_by(
                            models.GraphEntityResolutionDecision.raw_source_record_id
                        )
                    )
                )
                .scalars()
                .all()
            )
            assert [decision.resolution for decision in decisions] == [
                "EXACT_VERIFIED",
                "HIGH_CONFIDENCE",
                "UNRESOLVED",
            ]
            assert decisions[0].canonical_variant_id == variant.id
            assert decisions[1].canonical_variant_id == variant.id
            assert decisions[2].canonical_variant_id is None
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_dry_run_never_persists_a_projection_or_decision():
    engine, maker = await _database()
    try:
        async with maker() as session:
            await _seed(session)
            report = await replay_entity_resolution_batch(session, limit=2)
            assert report.mode == "dry_run"
            assert report.scanned == 2
            assert await session.scalar(
                select(func.count()).select_from(models.GraphEntitySignalProjection)
            ) == 0
            assert await session.scalar(
                select(func.count()).select_from(models.GraphEntityResolutionDecision)
            ) == 0
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_same_version_replay_refuses_changed_source_truth():
    engine, maker = await _database()
    try:
        async with maker() as session:
            raws, _variant = await _seed(session)
            await replay_entity_resolution_batch(session, limit=3, apply=True)
            raws[1].payload_json = {
                **raws[1].payload_json,
                "model": "Different",
            }
            await session.flush()
            with pytest.raises(EntityReplayError, match="signal replay divergence"):
                await replay_entity_resolution_batch(session, limit=3, apply=True)
            await session.rollback()
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
                await replay_entity_resolution_batch(
                    session,
                    after_raw_id=after_raw_id,
                    limit=limit,
                )
    finally:
        await engine.dispose()
