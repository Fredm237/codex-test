"""Preuves du shadow Offer Graph fail-closed."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import models as core_models
from app.db.base import Base
from app.observations import models as observation_models
from app.offer_graph import models
from app.offer_graph.backfill import backfill_offer_batch
from app.offer_graph.projection import (
    persist_awin_offer_projection,
    project_awin_offer,
)
from app.product_graph.resolution import (
    persist_awin_graph_projection,
    project_awin_variant,
)


OBSERVED_AT = datetime(2026, 8, 30, 22, 30, 0)


async def _session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    return engine, async_sessionmaker(engine, expire_on_commit=False)


async def _raw_offer(session, suffix: str, *, payload=None):
    merchant = core_models.Merchant(
        awin_mid=900 + ord(suffix),
        name=f"Merchant {suffix}",
        slug=f"merchant-offer-{suffix}",
    )
    session.add(merchant)
    await session.flush()
    offer = core_models.Offer(
        merchant_id=merchant.id,
        awin_product_id=f"offer-graph-{suffix}",
        name=f"Offer Graph {suffix}",
    )
    session.add(offer)
    await session.flush()
    raw = observation_models.RawSourceRecord(
        source_type="awin_feed",
        source_ref=f"awin-feed:{suffix}",
        source_record_key=f"offer-graph-{suffix}",
        schema_version="awin-create-a-feed-v1",
        context_json={"feed_id": suffix, "merchant_id": merchant.id},
        payload_json=payload or {"ean": "4006381333931"},
        payload_checksum=(suffix * 64),
        replay_key=(suffix.upper() * 64),
        sync_run_id=None,
        observed_at=OBSERVED_AT,
    )
    session.add(raw)
    await session.flush()
    return raw, offer


async def _link_raw_offer(session, raw, offer):
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
            observed_at=raw.observed_at,
            transformation="awin_offer_observation",
            transformation_version="v1",
            confidence=1.0,
        )
    )
    await session.flush()


async def _resolved_identity(session, raw, offer):
    return await persist_awin_graph_projection(
        session,
        projection=project_awin_variant({"ean": "4006381333931"}),
        raw_source_record_id=raw.id,
        offer_id=offer.id,
        source_ref=raw.source_ref,
        observed_at=OBSERVED_AT,
    )


def test_projection_requires_money_pair_and_public_https_merchant_link():
    projection = project_awin_offer(
        {
            "search_price": "1 299,90",
            "currency": "eur",
            "in_stock": "yes",
            "aw_deep_link": "https://merchant.example.com/product/1",
        }
    )
    assert projection.price_amount == Decimal("1299.90")
    assert projection.price_currency == "EUR"
    assert projection.price_state == "known"
    assert projection.availability == "in_stock"
    assert projection.merchant_url_state == "known"

    missing_currency = project_awin_offer(
        {"search_price": "12.50", "in_stock": "yes"}
    )
    assert missing_currency.price_amount is None
    assert missing_currency.price_reason == "missing_currency"

    for unsafe in (
        "http://merchant.example.com/item",
        "https://127.0.0.1/item",
        "https://localhost/item",
        "https://merchant.test/item",
        "https://user:secret@merchant.example.com/item",
    ):
        assert project_awin_offer({"aw_deep_link": unsafe}).merchant_url_state == (
            "invalid"
        )


@pytest.mark.asyncio
async def test_resolved_fresh_offer_is_eligible_and_replay_is_idempotent():
    engine, maker = await _session()
    try:
        async with maker() as session:
            raw, offer = await _raw_offer(session, "a")
            await _resolved_identity(session, raw, offer)
            projection = project_awin_offer(
                {
                    "search_price": "449.00",
                    "currency": "EUR",
                    "in_stock": "yes",
                    "aw_deep_link": "https://shop.filon-merchant.be/xm6",
                }
            )
            first = await persist_awin_offer_projection(
                session,
                projection=projection,
                raw_source_record_id=raw.id,
                offer_id=offer.id,
                observed_at=OBSERVED_AT,
            )
            replay = await persist_awin_offer_projection(
                session,
                projection=projection,
                raw_source_record_id=raw.id,
                offer_id=offer.id,
                observed_at=OBSERVED_AT,
            )
            await session.commit()

            observed = await session.scalar(select(models.GraphOfferObservation))
            assert first.created is True
            assert first.eligibility == "eligible"
            assert first.reason_code == "eligible_exact"
            assert replay.created is False
            assert observed is not None
            assert observed.price_amount == Decimal("449.000000")
            assert observed.offer_variant_link_id is not None
            assert await session.scalar(
                select(func.count()).select_from(models.GraphOfferObservation)
            ) == 1
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_unknown_identity_is_quarantined_before_other_claims():
    engine, maker = await _session()
    try:
        async with maker() as session:
            raw, offer = await _raw_offer(session, "b")
            capture = await persist_awin_offer_projection(
                session,
                projection=project_awin_offer(
                    {
                        "search_price": "10.00",
                        "currency": "EUR",
                        "in_stock": "yes",
                        "aw_deep_link": "https://merchant.example.org/item",
                    }
                ),
                raw_source_record_id=raw.id,
                offer_id=offer.id,
                observed_at=OBSERVED_AT,
            )
            assert capture.eligibility == "quarantine"
            assert capture.reason_code == "identity_unresolved"
    finally:
        await engine.dispose()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("row", "eligibility", "reason"),
    [
        (
            {
                "currency": "EUR",
                "in_stock": "yes",
                "aw_deep_link": "https://merchant.example.org/item",
            },
            "unknown",
            "missing_price",
        ),
        (
            {
                "search_price": "10.00",
                "currency": "EUR",
                "in_stock": "maybe",
                "aw_deep_link": "https://merchant.example.org/item",
            },
            "unknown",
            "availability_unknown",
        ),
        (
            {
                "search_price": "10.00",
                "currency": "EUR",
                "in_stock": "no",
                "aw_deep_link": "https://merchant.example.org/item",
            },
            "ineligible",
            "out_of_stock",
        ),
        (
            {
                "search_price": "10.00",
                "currency": "EUR",
                "in_stock": "yes",
                "aw_deep_link": "http://merchant.example.org/item",
            },
            "ineligible",
            "invalid_link",
        ),
    ],
)
async def test_resolved_identity_still_fails_closed_on_offer_truth(
    row,
    eligibility,
    reason,
):
    engine, maker = await _session()
    try:
        async with maker() as session:
            raw, offer = await _raw_offer(session, reason[0])
            await _resolved_identity(session, raw, offer)
            capture = await persist_awin_offer_projection(
                session,
                projection=project_awin_offer(row),
                raw_source_record_id=raw.id,
                offer_id=offer.id,
                observed_at=OBSERVED_AT,
            )
            assert capture.eligibility == eligibility
            assert capture.reason_code == reason
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_offer_backfill_is_dry_bounded_and_idempotent():
    engine, maker = await _session()
    try:
        async with maker() as session:
            valid_payload = {
                "ean": "4006381333931",
                "search_price": "49.90",
                "currency": "EUR",
                "in_stock": "yes",
                "aw_deep_link": "https://merchant.example.org/item",
            }
            raw, offer = await _raw_offer(session, "z", payload=valid_payload)
            await _link_raw_offer(session, raw, offer)
            await _resolved_identity(session, raw, offer)
            await session.commit()

            dry = await backfill_offer_batch(session, limit=1)
            assert dry.mode == "dry_run"
            assert dry.eligible == 1
            assert dry.observations_created == 0

            applied = await backfill_offer_batch(session, limit=1, apply=True)
            assert applied.observations_created == 1
            replay = await backfill_offer_batch(session, limit=1, apply=True)
            assert replay.observations_created == 0
            assert replay.observations_existing == 1
    finally:
        await engine.dispose()
