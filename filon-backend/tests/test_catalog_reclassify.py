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


@pytest.mark.anyio
async def test_reclassify_can_target_a_raw_merchant_category(monkeypatch, scoped_catalogue):
    monkeypatch.setattr(catalog, "_require_admin", lambda token: None)
    async with db.session_scope() as session:
        merchant_id = (await session.execute(select(models.Merchant.id))).scalar_one()
        session.add_all([
            models.Offer(
                merchant_id=merchant_id, awin_product_id="stay-raw", price=154.0,
                currency="EUR", name="Appartement de vacances à Bruges", category="Appartement de vacances",
            ),
            models.Offer(
                merchant_id=merchant_id, awin_product_id="other-raw", price=20.0,
                currency="EUR", name="Article non ciblé", category="Divers",
            ),
        ])
        await session.commit()

    result = await catalog.reclassify_offers(
        batch=100, after_id=0, max_offers=0, max_seconds=30,
        filon_category=None, only_unclassified=True,
        merchant_category="Appartement de vacances", x_admin_token="test",
    )

    assert result["offers_processed"] == 1
    assert result["merchant_category"] == "Appartement de vacances"
    async with db.session_scope() as session:
        targeted = (await session.execute(select(models.Offer).where(models.Offer.awin_product_id == "stay-raw"))).scalar_one()
        untouched = (await session.execute(select(models.Offer).where(models.Offer.awin_product_id == "other-raw"))).scalar_one()
    assert targeted.filon_category == taxonomy.VOYAGES
    assert targeted.offer_kind == taxonomy.ACCOMMODATION
    assert untouched.filon_category is None
    assert untouched.offer_kind is None


@pytest.mark.anyio
async def test_reclassify_can_target_one_merchant_without_touching_another(monkeypatch, scoped_catalogue):
    monkeypatch.setattr(catalog, "_require_admin", lambda token: None)
    async with db.session_scope() as session:
        original_merchant = (await session.execute(select(models.Merchant))).scalar_one()
        specialist = models.Merchant(awin_mid=78, name="Atelier patrons", slug="atelier-patrons")
        session.add(specialist)
        await session.flush()
        session.add_all([
            models.Offer(
                merchant_id=specialist.id, awin_product_id="sewing-pattern", price=12.0,
                currency="EUR", name="Patron Butterick n°7019 – Robe vintage", category=None,
                filon_category=taxonomy.MODE_FEMME, filon_subcategory="Robes",
            ),
            models.Offer(
                merchant_id=original_merchant.id, awin_product_id="finished-dress", price=80.0,
                currency="EUR", name="Robe en coton bio femme", category=None,
                filon_category=taxonomy.MODE_FEMME, filon_subcategory="Robes",
            ),
        ])
        await session.commit()

    result = await catalog.reclassify_offers(
        batch=100, after_id=0, max_offers=0, max_seconds=30,
        filon_category=None, merchant_id=specialist.id, x_admin_token="test",
    )

    assert result["offers_processed"] == 1
    assert result["merchant_id"] == specialist.id
    async with db.session_scope() as session:
        pattern = (await session.execute(select(models.Offer).where(models.Offer.awin_product_id == "sewing-pattern"))).scalar_one()
        dress = (await session.execute(select(models.Offer).where(models.Offer.awin_product_id == "finished-dress"))).scalar_one()
    assert pattern.filon_category == taxonomy.LOISIRS
    assert pattern.filon_subcategory == "Patrons & Kits de couture"
    assert dress.filon_category == taxonomy.MODE_FEMME
    assert dress.filon_subcategory == "Robes"


@pytest.mark.anyio
async def test_taxonomy_quality_reports_known_contradictions_without_writing(monkeypatch, scoped_catalogue):
    monkeypatch.setattr(catalog, "_require_admin", lambda token: None)

    async with db.session_scope() as session:
        before = (await session.execute(select(models.Offer))).scalars().all()
        result = await catalog.taxonomy_quality(
            limit=10,
            scan=100,
            x_admin_token="test",
            session=session,
        )
        after = (await session.execute(select(models.Offer))).scalars().all()

    assert result["scanned"] == 3
    assert result["flagged"] == 1
    assert result["by_signal"] == [
        {"signal": taxonomy.QUALITY_PHONE_PART_AS_SMARTPHONE, "count": 1}
    ]
    assert result["items"][0]["name"] == "Backcover pour iPhone 15"
    assert result["items"][0]["signals"] == [taxonomy.QUALITY_PHONE_PART_AS_SMARTPHONE]
    assert [(offer.id, offer.filon_category, offer.filon_subcategory) for offer in after] == [
        (offer.id, offer.filon_category, offer.filon_subcategory) for offer in before
    ]


@pytest.mark.anyio
async def test_reclassify_can_target_explicit_offer_ids_without_touching_other_rows(monkeypatch, scoped_catalogue):
    monkeypatch.setattr(catalog, "_require_admin", lambda token: None)
    async with db.session_scope() as session:
        offers = (await session.execute(select(models.Offer).order_by(models.Offer.awin_product_id))).scalars().all()
        by_product = {offer.awin_product_id: offer for offer in offers}
        case_id = by_product["case"].id
        phone_id = by_product["phone"].id

    result = await catalog.reclassify_offers(
        batch=100,
        after_id=0,
        max_offers=0,
        max_seconds=30,
        filon_category=None,
        offer_ids=f"{case_id},{phone_id}",
        x_admin_token="test",
    )

    assert result["done"] is True
    assert result["offers_processed"] == 2
    assert result["offer_ids_count"] == 2
    async with db.session_scope() as session:
        offers = (await session.execute(select(models.Offer).order_by(models.Offer.awin_product_id))).scalars().all()
    by_product = {offer.awin_product_id: offer for offer in offers}
    assert by_product["case"].filon_subcategory == "Coques & Protections"
    assert by_product["phone"].filon_subcategory == "Smartphones"
    assert by_product["outside"].filon_subcategory == "À conserver"
