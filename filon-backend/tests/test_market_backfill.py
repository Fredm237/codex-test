"""Qualification du rattrapage borné de marché de publication."""

from __future__ import annotations

from contextlib import asynccontextmanager
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import models as core_models
from app.db.base import Base
from app.ingest import market_backfill
from app.observations.awin import capture_awin_row
from app.observations.models import Observation
from app.services.awin_catalog import FeedInfo


@pytest.mark.asyncio
async def test_market_backfill_is_bounded_and_idempotent(monkeypatch) -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)

    @asynccontextmanager
    async def scope():
        async with sessions() as session:
            yield session

    async def feeds():
        return [FeedInfo("42", 77, "Merchant", "BE", 1)]

    async def prepare_schema():
        return None

    monkeypatch.setattr(market_backfill.db, "session_scope", scope)
    monkeypatch.setattr(market_backfill.db, "prepare_schema", prepare_schema)
    monkeypatch.setattr(market_backfill, "list_feeds", feeds)

    try:
        async with sessions() as session:
            merchant = core_models.Merchant(
                awin_mid=77,
                name="Merchant",
                slug="merchant",
            )
            session.add(merchant)
            await session.flush()
            offer = core_models.Offer(
                merchant_id=merchant.id,
                awin_product_id="product-1",
                name="Product",
                price=10,
                currency="EUR",
                in_stock=True,
            )
            session.add(offer)
            await session.flush()
            capture = await capture_awin_row(
                session,
                {
                    "aw_product_id": "product-1",
                    "product_name": "Product",
                    "search_price": "10",
                    "currency": "EUR",
                    "in_stock": "yes",
                },
                feed_id="42",
                merchant_id=merchant.id,
                merchant_name=merchant.name,
                offer_id=offer.id,
                sync_run_id=None,
            )
            await session.commit()
            raw_id = capture.raw_source_record_id

        arguments = {
            "country_code": "BE",
            "after_raw_id": raw_id - 1,
            "through_raw_id": raw_id,
            "limit": 1,
        }
        dry = await market_backfill.run(**arguments, apply=False)
        applied = await market_backfill.run(**arguments, apply=True)
        replay = await market_backfill.run(**arguments, apply=True)

        assert dry.status == "dry_run"
        assert dry.selected == dry.eligible == 1
        assert dry.created == 0
        assert applied.status == "applied"
        assert applied.created == 1
        assert replay.created == 0
        assert replay.existing == 1
        assert dry.final_state_digest == applied.final_state_digest
        assert applied.final_state_digest == replay.final_state_digest

        async with sessions() as session:
            markets = (
                await session.scalars(
                    select(Observation).where(
                        Observation.field == "listing_market"
                    )
                )
            ).all()
            assert len(markets) == 1
            assert markets[0].value_json == "BE"
    finally:
        await engine.dispose()


@pytest.mark.parametrize(
    "values",
    (
        {"country_code": "BEL", "after_raw_id": 0, "through_raw_id": 1, "limit": 1},
        {"country_code": "BE", "after_raw_id": 1, "through_raw_id": 1, "limit": 1},
        {"country_code": "BE", "after_raw_id": 0, "through_raw_id": 1, "limit": 0},
    ),
)
def test_market_backfill_rejects_unbounded_or_invalid_scope(values) -> None:
    with pytest.raises(ValueError):
        market_backfill._scope(**values)
