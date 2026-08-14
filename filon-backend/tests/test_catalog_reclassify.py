"""Reclassement catalogue ciblé, reprenable et sans effet hors périmètre."""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.routes import catalog
from app.db import models
from app.db import session as db
from app.db.base import Base
from app.services import taxonomy


@pytest.fixture
async def scoped_catalogue():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    previous = (db._engine, db._sessionmaker)
    db._engine = engine
    db._sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

    async with db._sessionmaker() as session:
        merchant = models.Merchant(awin_mid=77, name="Marchand test", slug="marchand-test")
        session.add(merchant)
        await session.flush()
        session.add_all([
            models.Offer(
                merchant_id=merchant.id, awin_product_id="case", price=19.99,
                currency="EUR", name="Backcover pour iPhone 15", category="Mobile accessories",
                filon_category=taxonomy.TELEPHONIE, filon_subcategory="Smartphones",
            ),
            models.Offer(
                merchant_id=merchant.id, awin_product_id="phone", price=799.99,
                currency="EUR", name="iPhone 15 128 Go", category="Mobile phones",
                filon_category=taxonomy.TELEPHONIE, filon_subcategory=None,
            ),
            models.Offer(
                merchant_id=merchant.id, awin_product_id="outside", price=25.0,
                currency="EUR", name="Décoration test", category="Home", filon_category=taxonomy.MAISON,
                filon_subcategory="À conserver",
            ),
        ])
        await session.commit()

    yield
    db._engine, db._sessionmaker = previous
    await engine.dispose()


@pytest.mark.anyio
async def test_reclassify_can_target_one_existing_filon_category(monkeypatch, scoped_catalogue):
    monkeypatch.setattr(catalog, "_require_admin", lambda token: None)

    result = await catalog.reclassify_offers(
        batch=100,
        after_id=0,
        max_offers=0,
        max_seconds=30,
        filon_category=taxonomy.TELEPHONIE,
        x_admin_token="test",
    )

    assert result["done"] is True
    assert result["offers_processed"] == 2
    assert result["filon_category"] == taxonomy.TELEPHONIE

    async with db.session_scope() as session:
        offers = (await session.execute(select(models.Offer).order_by(models.Offer.awin_product_id))).scalars().all()

    by_id = {offer.awin_product_id: offer for offer in offers}
    assert by_id["case"].filon_category == taxonomy.TELEPHONIE
    assert by_id["case"].filon_subcategory == "Coques & Protections"
    assert by_id["phone"].filon_subcategory == "Smartphones"
    assert by_id["outside"].filon_subcategory == "À conserver"


@pytest.mark.anyio
async def test_reclassify_unclassified_assigns_stay_kind_and_aisle(monkeypatch, scoped_catalogue):
    monkeypatch.setattr(catalog, "_require_admin", lambda token: None)
    async with db.session_scope() as session:
        merchant_id = (await session.execute(select(models.Merchant.id))).scalar_one()
        session.add(models.Offer(
            merchant_id=merchant_id, awin_product_id="stay", price=154.0,
            currency="EUR", name="Appartement de vacances à Lac Balaton", category="Appartement de vacances",
        ))
        await session.commit()

    result = await catalog.reclassify_offers(
        batch=100,
        after_id=0,
        max_offers=0,
        max_seconds=30,
        filon_category=None,
        only_unclassified=True,
        x_admin_token="test",
    )

    assert result["done"] is True
    assert result["offers_processed"] == 1
    assert result["offer_kinds"] == {taxonomy.ACCOMMODATION: 1}
    async with db.session_scope() as session:
        stay = (await session.execute(select(models.Offer).where(models.Offer.awin_product_id == "stay"))).scalar_one()
    assert stay.filon_category == taxonomy.VOYAGES
    assert stay.filon_subcategory == "Locations de vacances"
    assert stay.offer_kind == taxonomy.ACCOMMODATION
