"""L'assistant doit répondre depuis le catalogue réel, pas depuis la démo."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import models
from app.db import session as db
from app.db.base import Base
from app.services.catalog_grouping import rebuild_products
from app.services.catalog_source import keywords, search_products

EAN = "4006381333931"


@pytest.fixture
async def catalogue():
    """Base en mémoire branchée sur le module de session applicatif."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    previous = (db._engine, db._sessionmaker)
    db._engine = engine
    db._sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

    async with db._sessionmaker() as s:
        coolblue = models.Merchant(awin_mid=1, name="Coolblue BE", slug="coolblue")
        media = models.Merchant(awin_mid=2, name="MediaMarkt BE", slug="mediamarkt")
        blocked = models.Merchant(awin_mid=3, name="MontAmour", slug="montamour")
        s.add_all([coolblue, media, blocked])
        await s.flush()

        def offer(m, pid, name, price, ean=None, image="https://example.test/i.jpg"):
            return models.Offer(
                merchant_id=m.id, awin_product_id=pid, name=name, brand="Sony",
                price=price, currency="EUR", ean=ean, image_url=image,
                deep_link="https://example.test/go",
            )

        s.add(offer(coolblue, "1", "Sony WH-1000XM5 Casque sans fil", 329.0, EAN))
        s.add(offer(media, "2", "Sony WH-1000XM5 Casque sans fil", 299.0, EAN))
        s.add(offer(coolblue, "3", "Casque Bluetooth JBL Tune", 59.0))
        s.add(offer(blocked, "4", "Casque pour adulte", 49.0))
        s.add(offer(coolblue, "5", "Casque sans image", 39.0, image=None))
        await s.commit()
        await rebuild_products(s)

    yield
    db._engine, db._sessionmaker = previous
    await engine.dispose()


def test_keywords_drop_filler_words():
    # « je », « cherche », « un », « bon » et « sans » sont des mots vides :
    # les chercher dans les libellés produit ne filtrerait rien d'utile.
    assert keywords("je cherche un bon casque sans fil") == ["casque", "fil"]
    assert keywords("!!") == []


async def test_returns_real_products_with_real_merchants(catalogue):
    results = await search_products("un bon casque sans fil", budget_max=400)
    names = [p["name"] for p in results]
    assert "Sony WH-1000XM5 Casque sans fil" in names
    merchants = {o["merchant"] for p in results for o in p["offers"]}
    assert merchants & {"Coolblue BE", "MediaMarkt BE"}


async def test_groups_offers_of_the_same_product(catalogue):
    results = await search_products("casque sans fil", budget_max=400)
    sony = next(p for p in results if "WH-1000XM5" in p["name"])
    assert len(sony["offers"]) == 2
    # Offres du moins cher au plus cher : le comparateur s'appuie dessus.
    assert [o["price"] for o in sony["offers"]] == [299.0, 329.0]


async def test_excludes_blocked_merchants_and_imageless_offers(catalogue):
    results = await search_products("casque", budget_max=400)
    slugs = {o["merchant_slug"] for p in results for o in p["offers"]}
    assert "montamour" not in slugs
    assert all(p["image"] for p in results)


async def test_budget_is_respected(catalogue):
    results = await search_products("casque", budget_max=100)
    assert results
    assert all(min(o["price"] for o in p["offers"]) <= 105 for p in results)


async def test_no_database_returns_nothing_rather_than_invented_data():
    previous = (db._engine, db._sessionmaker)
    db._engine, db._sessionmaker = None, None
    try:
        assert await search_products("casque") == []
    finally:
        db._engine, db._sessionmaker = previous
