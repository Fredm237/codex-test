"""Projection et persistance des assertions Product Identity Phase 1."""

from __future__ import annotations

from datetime import datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import models as core_models
from app.db.base import Base
from app.observations import models as observation_models
from app.product_graph import models
from app.product_graph.identity import (
    persist_awin_identity_assertions,
    project_awin_identity_assertions,
)
from app.product_graph.resolution import ProductGraphResolutionError


OBSERVED_AT = datetime(2026, 8, 31, 18, 0, 0)


async def _session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    return engine, async_sessionmaker(engine, expire_on_commit=False)


async def _raw_offer(session):
    merchant = core_models.Merchant(
        awin_mid=700,
        name="Merchant",
        slug="merchant",
    )
    session.add(merchant)
    await session.flush()
    offer = core_models.Offer(
        merchant_id=merchant.id,
        awin_product_id="sku-42",
        name="Phone Pro",
    )
    session.add(offer)
    await session.flush()
    raw = observation_models.RawSourceRecord(
        source_type="awin_feed",
        source_ref="awin-feed:42",
        source_record_key="700:sku-42",
        schema_version="awin-create-a-feed-v1",
        context_json={"merchant_id": merchant.id},
        payload_json={"ean": "4006381333931"},
        payload_checksum="a" * 64,
        replay_key="b" * 64,
        sync_run_id=None,
        observed_at=OBSERVED_AT,
    )
    session.add(raw)
    await session.flush()
    return merchant, offer, raw


def test_awin_identity_projection_keeps_brand_observed_and_identifiers_scoped():
    projections = project_awin_identity_assertions(
        {
            "brand_name": "  Main  Sauvage ",
            "ean": "4006381333931",
            "aw_product_id": " SKU-42 ",
        },
        merchant_id=7,
    )
    assert [projection.status for projection in projections] == [
        "observed",
        "validated",
        "validated",
    ]
    assert projections[0].normalized_value == "main sauvage"
    assert projections[0].identifier_namespace is None
    assert projections[1].identifier_namespace == "gtin"
    assert projections[1].identifier_scope == "global"
    assert projections[2].identifier_namespace == "merchant_sku"
    assert projections[2].identifier_scope == "merchant:7"


def test_invalid_gtin_is_quarantined_and_unknowns_create_no_assertion():
    projections = project_awin_identity_assertions(
        {"ean": "invalid", "brand_name": " ", "aw_product_id": None},
        merchant_id=7,
    )
    assert len(projections) == 1
    assert projections[0].status == "quarantine"
    assert projections[0].normalized_value is None
    assert projections[0].value == "invalid"


@pytest.mark.parametrize("merchant_id", [0, -1, True, "7"])
def test_identity_projection_rejects_an_invalid_merchant_scope(merchant_id):
    with pytest.raises(ProductGraphResolutionError, match="merchant_id"):
        project_awin_identity_assertions({}, merchant_id=merchant_id)


@pytest.mark.asyncio
async def test_identity_assertions_are_append_only_and_replay_idempotent():
    engine, maker = await _session()
    try:
        async with maker() as session:
            merchant, offer, raw = await _raw_offer(session)
            projections = project_awin_identity_assertions(
                {
                    "brand_name": "Example Brand",
                    "ean": "4006381333931",
                    "aw_product_id": "sku-42",
                },
                merchant_id=merchant.id,
            )
            first = await persist_awin_identity_assertions(
                session,
                projections=projections,
                raw_source_record_id=raw.id,
                offer_id=offer.id,
                source_ref=raw.source_ref,
                observed_at=raw.observed_at,
            )
            replay = await persist_awin_identity_assertions(
                session,
                projections=projections,
                raw_source_record_id=raw.id,
                offer_id=offer.id,
                source_ref=raw.source_ref,
                observed_at=raw.observed_at,
            )
            await session.commit()

            assertions = (
                (await session.execute(select(models.GraphIdentityAssertion)))
                .scalars()
                .all()
            )
            assert first.created == 3
            assert (first.observed, first.validated, first.quarantined) == (1, 2, 0)
            assert replay.created == 0
            assert replay.existing == 3
            assert len(assertions) == 3
            assert all(assertion.raw_source_record_id == raw.id for assertion in assertions)
            assert all(assertion.offer_id == offer.id for assertion in assertions)
            assert all(len(assertion.assertion_key) == 64 for assertion in assertions)
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_identity_assertion_persistence_rejects_missing_provenance():
    engine, maker = await _session()
    try:
        async with maker() as session:
            with pytest.raises(ProductGraphResolutionError, match="source_ref"):
                await persist_awin_identity_assertions(
                    session,
                    projections=(),
                    raw_source_record_id=1,
                    offer_id=1,
                    source_ref="",
                    observed_at=OBSERVED_AT,
                )
    finally:
        await engine.dispose()
