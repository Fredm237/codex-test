"""Tests des rails de la home catalogue, sur une base en mémoire.

Ces tests figent deux défauts constatés en production : un rail affichait cinq
fois la même chemise (déclinaisons de taille du même feed), et un seul marchand
pouvait occuper toute la rangée.
"""

from __future__ import annotations

from collections import Counter

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.routes.catalog import highlights
from app.db import models
from app.db.base import Base


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as s:
        yield s
    await engine.dispose()


async def _seed(s) -> None:
    shirts = models.Merchant(awin_mid=1, name="Overhemden - NL", slug="overhemden")
    other = models.Merchant(awin_mid=2, name="Autre Boutique", slug="autre")
    s.add_all([shirts, other])
    await s.flush()

    def offer(m, pid, name, price, brand="GANT"):
        return models.Offer(
            merchant_id=m.id, awin_product_id=pid, name=name, brand=brand,
            price=price, currency="EUR", image_url="https://example.test/i.jpg",
        )

    # Le cas réel : quatre tailles du même article, donc quatre lignes identiques.
    for i in range(4):
        s.add(offer(shirts, f"green-{i}", "GANT Regular Fit shirt green, Chequered", 100.0))
    s.add(offer(shirts, "blue", "GANT Regular Fit shirt blue, Chequered", 100.0))
    for i in range(8):
        s.add(offer(shirts, f"oxford-{i}", f"Chemise Oxford {i}", 50.0 + i))
    for i in range(6):
        s.add(offer(other, f"divers-{i}", f"Produit Divers {i}", 30.0 + i, brand="AUTRE"))
    await s.commit()


async def _budget(s, limit=12):
    data = await highlights(limit=limit, session=s)
    section = next((x for x in data["sections"] if x["key"] == "budget"), None)
    return section["items"] if section else []


async def test_rail_has_no_duplicate_products(session):
    await _seed(session)
    names = [i["name"] for i in await _budget(session)]
    assert len(set(names)) == len(names)
    greens = [n for n in names if n.startswith("GANT Regular Fit shirt green")]
    assert len(greens) <= 1


async def test_rail_interleaves_merchants(session):
    await _seed(session)
    items = await _budget(session)
    # Deux marchands disponibles : ils doivent alterner en tête de rail.
    assert items[0]["merchant"]["slug"] != items[1]["merchant"]["slug"]
    counts = Counter(i["merchant"]["slug"] for i in items)
    assert max(counts.values()) - min(counts.values()) <= 1


async def test_rail_stays_full_when_few_merchants(session):
    """Un simple plafond par marchand laissait des rangées à moitié vides."""
    await _seed(session)
    assert len(await _budget(session, limit=12)) == 12


async def test_budget_rail_excludes_non_euro_and_out_of_range(session):
    await _seed(session)
    m = models.Merchant(awin_mid=3, name="UK Shop", slug="uk-shop")
    session.add(m)
    await session.flush()
    session.add(models.Offer(
        merchant_id=m.id, awin_product_id="gbp", name="Veste Anglaise", brand="UK",
        price=95.0, currency="GBP", image_url="https://example.test/i.jpg",
    ))
    session.add(models.Offer(
        merchant_id=m.id, awin_product_id="cheap", name="Bricole", brand="UK",
        price=2.0, currency="EUR", image_url="https://example.test/i.jpg",
    ))
    await session.commit()

    items = await _budget(session, limit=24)
    assert all(i["currency"] == "EUR" for i in items)
    assert all(10 <= i["price"] <= 100 for i in items)
    names = [i["name"] for i in items]
    assert "Veste Anglaise" not in names  # 95 GBP n'est pas « moins de 100 € »
    assert "Bricole" not in names
