"""Preuves Merchant Intelligence sans score synthétique."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import models as core_models
from app.db.base import Base
from app.merchant_intelligence import models
from app.merchant_intelligence.backfill import measure_batch, parse_evaluated_at
from app.merchant_intelligence.measurement import (
    MerchantMeasurementError,
    measure_merchant_window,
    persist_measurement,
)
from app.observations import models as observation_models
from app.offer_graph.projection import (
    persist_awin_offer_projection,
    project_awin_offer,
)
from app.product_graph.resolution import (
    persist_awin_graph_projection,
    project_awin_variant,
)


BASE_TIME = datetime(2026, 8, 30, 20, 0, 0)


async def _session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    return engine, async_sessionmaker(engine, expire_on_commit=False)


async def _merchant(session, suffix: str, *, joined: bool = True):
    merchant = core_models.Merchant(
        awin_mid=7000 + ord(suffix),
        name=f"Merchant {suffix}",
        slug=f"merchant-intelligence-{suffix}",
        region="BE",
        joined=joined,
    )
    session.add(merchant)
    await session.flush()
    return merchant


async def _raw_offer(
    session,
    merchant,
    suffix: str,
    *,
    payload: dict,
    observed_at: datetime,
):
    offer = core_models.Offer(
        merchant_id=merchant.id,
        awin_product_id=f"merchant-offer-{suffix}",
        name=f"Merchant Offer {suffix}",
    )
    session.add(offer)
    await session.flush()
    raw = observation_models.RawSourceRecord(
        source_type="awin_feed",
        source_ref=f"awin-feed:{suffix}",
        source_record_key=f"merchant-record-{suffix}",
        schema_version="awin-create-a-feed-v1",
        context_json={"feed_id": suffix, "merchant_id": merchant.id},
        payload_json=payload,
        payload_checksum=(suffix.lower() * 64),
        replay_key=(suffix.upper() * 64),
        sync_run_id=None,
        observed_at=observed_at,
    )
    session.add(raw)
    await session.flush()
    session.add(
        observation_models.Observation(
            raw_source_record_id=raw.id,
            subject_type="merchant_offer",
            subject_ref=f"offer:{offer.id}",
            offer_id=offer.id,
            field="external_id",
            value_json=offer.awin_product_id,
            status="verified",
            source_type="awin_feed",
            source_ref=raw.source_ref,
            observed_at=observed_at,
            transformation="awin_offer_observation",
            transformation_version="v1",
            confidence=1.0,
        )
    )
    await session.flush()
    return raw, offer


async def _project(session, raw, offer, *, resolve_identity: bool):
    if resolve_identity:
        await persist_awin_graph_projection(
            session,
            projection=project_awin_variant(raw.payload_json),
            raw_source_record_id=raw.id,
            offer_id=offer.id,
            source_ref=raw.source_ref,
            observed_at=raw.observed_at,
        )
    await persist_awin_offer_projection(
        session,
        projection=project_awin_offer(raw.payload_json),
        raw_source_record_id=raw.id,
        offer_id=offer.id,
        observed_at=raw.observed_at,
    )


@pytest.mark.asyncio
async def test_measurement_exposes_counts_and_unknown_dimensions_without_score():
    engine, maker = await _session()
    try:
        async with maker() as session:
            merchant = await _merchant(session, "a", joined=True)
            first, first_offer = await _raw_offer(
                session,
                merchant,
                "a",
                payload={
                    "ean": "4006381333931",
                    "search_price": "49.90",
                    "currency": "EUR",
                    "in_stock": "yes",
                    "aw_deep_link": "https://merchant.example.org/item-a",
                },
                observed_at=BASE_TIME,
            )
            second, second_offer = await _raw_offer(
                session,
                merchant,
                "b",
                payload={
                    "ean": "invalid",
                    "search_price": "20.00",
                    "currency": "EUR",
                    "in_stock": "maybe",
                    "aw_deep_link": "http://merchant.example.org/item-b",
                },
                observed_at=BASE_TIME + timedelta(minutes=30),
            )
            await _project(session, first, first_offer, resolve_identity=True)
            await _project(session, second, second_offer, resolve_identity=False)

            measured = await measure_merchant_window(
                session,
                raws=[second, first],
                evaluated_at=BASE_TIME + timedelta(hours=1),
            )
            assert measured.merchant_status == "AFFILIATED"
            assert measured.source_record_count == 2
            assert measured.offer_observation_count == 2
            assert measured.gtin_known_count == 1
            assert measured.price_known_count == 2
            assert measured.price_fresh_count == 2
            assert measured.stock_known_count == 1
            assert measured.merchant_link_known_count == 1
            assert measured.invalid_link_count == 1
            assert measured.identity_resolved_count == 1
            assert measured.eligible_offer_count == 1
            assert measured.feed_age_seconds == 30 * 60
            assert measured.ratios()["decision_eligibility_rate"] == 0.5
            assert measured.measurement_states["delivery_reliability"] == (
                "not_measurable"
            )
            assert measured.measurement_states["shipping_coverage"] == (
                "not_measurable"
            )
            assert "score" not in measured.measurement_states
            assert "confidence" not in measured.measurement_states

            assert await persist_measurement(session, measured) is True
            assert await persist_measurement(session, measured) is False
            with pytest.raises(MerchantMeasurementError, match="roster"):
                await persist_measurement(
                    session,
                    replace(
                        measured,
                        measurement_states={
                            **measured.measurement_states,
                            "confidence": "invented",
                        },
                    ),
                )
            await session.commit()
            assert await session.scalar(
                select(func.count()).select_from(models.MerchantQualitySnapshot)
            ) == 1
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_future_feed_timestamp_is_invalid_not_fresh():
    engine, maker = await _session()
    try:
        async with maker() as session:
            merchant = await _merchant(session, "c", joined=False)
            raw, _offer = await _raw_offer(
                session,
                merchant,
                "c",
                payload={"ean": "4006381333931"},
                observed_at=BASE_TIME + timedelta(hours=2),
            )
            measured = await measure_merchant_window(
                session,
                raws=[raw],
                evaluated_at=BASE_TIME,
            )
            assert measured.merchant_status == "INDEXED"
            assert measured.feed_age_seconds is None
            assert measured.measurement_states["feed_freshness"] == "invalid_future"
            assert measured.price_fresh_count == 0
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_mixed_merchant_window_is_rejected():
    engine, maker = await _session()
    try:
        async with maker() as session:
            first_merchant = await _merchant(session, "d")
            second_merchant = await _merchant(session, "e")
            first, _ = await _raw_offer(
                session,
                first_merchant,
                "d",
                payload={"ean": "4006381333931"},
                observed_at=BASE_TIME,
            )
            second, _ = await _raw_offer(
                session,
                second_merchant,
                "e",
                payload={"ean": "4006381333931"},
                observed_at=BASE_TIME,
            )
            with pytest.raises(MerchantMeasurementError, match="mixes merchants"):
                await measure_merchant_window(
                    session,
                    raws=[first, second],
                    evaluated_at=BASE_TIME,
                )
    finally:
        await engine.dispose()


def test_evaluated_at_requires_an_explicit_offset():
    assert parse_evaluated_at("2026-08-30T22:00:00+02:00") == datetime(
        2026, 8, 30, 20, 0, 0
    )
    with pytest.raises(ValueError, match="explicit UTC offset"):
        parse_evaluated_at("2026-08-30T22:00:00")


@pytest.mark.asyncio
async def test_batch_is_dry_by_default_and_apply_is_idempotent():
    engine, maker = await _session()
    try:
        async with maker() as session:
            merchant = await _merchant(session, "f")
            raw, offer = await _raw_offer(
                session,
                merchant,
                "f",
                payload={
                    "ean": "4006381333931",
                    "search_price": "10",
                    "currency": "EUR",
                    "in_stock": "yes",
                    "aw_deep_link": "https://merchant.example.org/item-f",
                },
                observed_at=BASE_TIME,
            )
            await _project(session, raw, offer, resolve_identity=True)
            await session.commit()

            dry = await measure_batch(
                session,
                evaluated_at=BASE_TIME + timedelta(hours=1),
                limit=1,
            )
            assert dry.merchants_measured == 1
            assert dry.snapshots_created == 0
            applied = await measure_batch(
                session,
                evaluated_at=BASE_TIME + timedelta(hours=1),
                limit=1,
                apply=True,
            )
            assert applied.snapshots_created == 1
            replay = await measure_batch(
                session,
                evaluated_at=BASE_TIME + timedelta(hours=1),
                limit=1,
                apply=True,
            )
            assert replay.snapshots_existing == 1
    finally:
        await engine.dispose()
