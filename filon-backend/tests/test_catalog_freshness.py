from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.routes import catalog
from app.db import models
from app.db import session as db
from app.db.base import Base
from app.services.freshness import format_utc_timestamp


async def _offers(session):
    return await catalog.offers(
        q=None,
        merchant=None,
        department=None,
        category=None,
        subcategory=None,
        brand=None,
        price_min=None,
        price_max=None,
        sort="relevance",
        duplicates=False,
        limit=10,
        offset=0,
        session=session,
    )


def test_public_catalogue_timestamp_is_always_explicit_utc():
    naive = datetime(2026, 8, 30, 12, 0)
    assert format_utc_timestamp(naive) == "2026-08-30T12:00:00+00:00"
    assert (
        format_utc_timestamp("2026-08-30T14:00:00+02:00")
        == "2026-08-30T12:00:00+00:00"
    )
    assert format_utc_timestamp(None) is None


@pytest.fixture
async def freshness_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    previous = (db._engine, db._sessionmaker)
    db._engine = engine
    db._sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

    async with db._sessionmaker() as session:
        merchant = models.Merchant(awin_mid=9041, name="Marchand fraîcheur", slug="marchand-fraicheur")
        session.add(merchant)
        await session.flush()
        observed = models.Offer(
            merchant_id=merchant.id,
            awin_product_id="observed",
            name="Casque relevé",
            price=90.0,
            currency="EUR",
            image_url="https://example.test/observed.jpg",
            deep_link="https://example.test/observed",
            is_canonical=True,
            in_stock=True,
        )
        unobserved = models.Offer(
            merchant_id=merchant.id,
            awin_product_id="unobserved",
            name="Casque sans relevé",
            price=75.0,
            currency="EUR",
            image_url="https://example.test/unobserved.jpg",
            deep_link="https://example.test/unobserved",
            is_canonical=True,
            in_stock=True,
        )
        session.add_all([observed, unobserved])
        await session.flush()
        now = datetime.now(UTC).replace(tzinfo=None, microsecond=0)
        session.add_all([
            models.PriceSnapshot(
                offer_id=observed.id,
                price=110.0,
                currency="EUR",
                in_stock=True,
                captured_at=now - timedelta(days=5),
            ),
            models.PriceSnapshot(
                offer_id=observed.id,
                price=90.0,
                currency="EUR",
                in_stock=True,
                captured_at=now - timedelta(hours=2),
            ),
        ])
        await session.commit()
        yield session, now, observed.id, unobserved.id

    db._engine, db._sessionmaker = previous
    await engine.dispose()


@pytest.mark.anyio
async def test_offers_expose_latest_real_snapshot_or_null(freshness_session):
    session, now, observed_id, unobserved_id = freshness_session

    payload = await _offers(session)
    by_id = {item["id"]: item for item in payload["items"]}

    assert by_id[observed_id]["observed_at"] == (
        now.replace(tzinfo=UTC) - timedelta(hours=2)
    ).isoformat()
    assert by_id[observed_id]["evidence_current"] is True
    assert by_id[unobserved_id]["observed_at"] is None
    assert by_id[unobserved_id]["evidence_current"] is False
    assert by_id[unobserved_id]["price"] is None
    assert by_id[unobserved_id]["currency"] is None
    assert by_id[unobserved_id]["in_stock"] is None


@pytest.mark.anyio
async def test_freshness_comes_from_snapshot_not_offer_timestamp(freshness_session):
    session, _now, observed_id, _unobserved_id = freshness_session

    payload = await _offers(session)
    item = next(item for item in payload["items"] if item["id"] == observed_id)

    assert item["observed_at"] is not None
    assert item["observed_at"] != item.get("updated_at")


@pytest.mark.anyio
async def test_offers_mask_stale_or_non_matching_price_evidence(freshness_session):
    session, now, _observed_id, _unobserved_id = freshness_session
    merchant = (await session.execute(models.Merchant.__table__.select())).first()
    merchant_id = merchant.id
    stale = models.Offer(
        merchant_id=merchant_id,
        awin_product_id="stale",
        name="Casque relevé trop ancien",
        price=60.0,
        currency="EUR",
        in_stock=True,
        image_url="https://example.test/stale.jpg",
        is_canonical=True,
    )
    mismatch = models.Offer(
        merchant_id=merchant_id,
        awin_product_id="mismatch",
        name="Casque prix muté",
        price=55.0,
        currency="EUR",
        in_stock=True,
        image_url="https://example.test/mismatch.jpg",
        is_canonical=True,
    )
    session.add_all([stale, mismatch])
    await session.flush()
    session.add_all(
        [
            models.PriceSnapshot(
                offer_id=stale.id,
                price=60.0,
                currency="EUR",
                in_stock=True,
                captured_at=now - timedelta(days=4),
            ),
            models.PriceSnapshot(
                offer_id=mismatch.id,
                price=50.0,
                currency="EUR",
                in_stock=True,
                captured_at=now - timedelta(hours=1),
            ),
        ]
    )
    await session.commit()

    payload = await _offers(session)
    by_id = {item["id"]: item for item in payload["items"]}
    for offer_id in (stale.id, mismatch.id):
        assert by_id[offer_id]["evidence_current"] is False
        assert by_id[offer_id]["price"] is None
        assert by_id[offer_id]["currency"] is None
        assert by_id[offer_id]["in_stock"] is None
