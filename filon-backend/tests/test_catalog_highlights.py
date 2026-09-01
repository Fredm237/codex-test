"""Tests des rails de la home catalogue, sur une base en mémoire.

Ces tests figent deux défauts constatés en production : un rail affichait cinq
fois la même chemise (déclinaisons de taille du même feed), et un seul marchand
pouvait occuper toute la rangée.
"""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.routes.catalog import _bound_highlights_parallelism, highlights
from app.db import models
from app.db.base import Base


class _Dialect:
    def __init__(self, name: str):
        self.name = name


class _Bind:
    def __init__(self, dialect: str):
        self.dialect = _Dialect(dialect)


class _RecordingSession:
    def __init__(self, dialect: str):
        self.bind = _Bind(dialect)
        self.statements = []

    def get_bind(self):
        return self.bind

    async def execute(self, statement):
        self.statements.append(str(statement))


async def test_highlights_bounds_postgresql_parallelism_per_transaction():
    session = _RecordingSession("postgresql")

    await _bound_highlights_parallelism(session)

    assert session.statements == [
        "SET LOCAL max_parallel_workers_per_gather = 0"
    ]


async def test_highlights_keeps_non_postgresql_sessions_unchanged():
    session = _RecordingSession("sqlite")

    await _bound_highlights_parallelism(session)

    assert session.statements == []


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

    seeded_offers = []

    def offer(m, pid, name, price, brand="GANT"):
        row = models.Offer(
            merchant_id=m.id, awin_product_id=pid, name=name, brand=brand,
            price=price, currency="EUR", in_stock=True,
            image_url="https://example.test/i.jpg",
        )
        seeded_offers.append(row)
        return row

    # Le cas réel : quatre tailles du même article, donc quatre lignes identiques.
    for i in range(4):
        s.add(offer(shirts, f"green-{i}", "GANT Regular Fit shirt green, Chequered", 100.0))
    s.add(offer(shirts, "blue", "GANT Regular Fit shirt blue, Chequered", 100.0))
    for i in range(8):
        s.add(offer(shirts, f"oxford-{i}", f"Chemise Oxford {i}", 50.0 + i))
    for i in range(6):
        s.add(offer(other, f"divers-{i}", f"Produit Divers {i}", 30.0 + i, brand="AUTRE"))
    await s.flush()
    captured_at = datetime.now(UTC).replace(tzinfo=None)
    s.add_all(
        [
            models.PriceSnapshot(
                offer_id=row.id,
                price=row.price,
                currency="EUR",
                in_stock=True,
                captured_at=captured_at,
            )
            for row in seeded_offers
        ]
    )
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


async def test_rail_dedups_size_variants_via_ean(session):
    """Le cas réel : mêmes produits, noms différents par suffixe de taille.

    L'affichage tronque le titre à deux lignes, donc ces cartes paraissent
    identiques sans l'être. Seul le regroupement par EAN les réunit.
    """
    from app.services.catalog_grouping import rebuild_products

    m = models.Merchant(awin_mid=9, name="Overhemden - NL", slug="overhemden")
    session.add(m)
    await session.flush()
    ean = "4006381333931"
    seeded_offers = []
    for size in ("S", "M", "L", "XL"):
        offer = models.Offer(
            merchant_id=m.id, awin_product_id=f"shirt-{size}",
            name=f"GANT Regular Fit shirt green, Chequered - Size {size}",
            brand="GANT", price=100.0, currency="EUR", in_stock=True, ean=ean,
            image_url="https://example.test/i.jpg",
        )
        seeded_offers.append(offer)
        session.add(offer)
    # Assez d'articles distincts pour que le rail atteigne le minimum d'affichage.
    for i, (pid, name, price) in enumerate([
        ("tie", "Cravate", 45.0), ("belt", "Ceinture", 55.0),
        ("sock", "Chaussettes", 15.0), ("scarf", "Écharpe", 65.0),
    ]):
        offer = models.Offer(
            merchant_id=m.id, awin_product_id=pid, name=name,
            brand="GANT", price=price, currency="EUR", in_stock=True,
            image_url="https://example.test/i.jpg",
        )
        seeded_offers.append(offer)
        session.add(offer)
    await session.flush()
    captured_at = datetime.now(UTC).replace(tzinfo=None)
    session.add_all(
        [
            models.PriceSnapshot(
                offer_id=row.id,
                price=row.price,
                currency="EUR",
                in_stock=True,
                captured_at=captured_at,
            )
            for row in seeded_offers
        ]
    )
    await session.commit()
    await rebuild_products(session)

    items = await _budget(session, limit=12)
    assert all(item["evidence_current"] is True for item in items)
    assert all(item["observed_at"] is not None for item in items)
    shirts = [i for i in items if "Chequered" in i["name"]]
    assert len(shirts) == 1, f"les 4 tailles devraient donner 1 carte, obtenu {len(shirts)}"


async def test_budget_rail_excludes_non_euro_and_out_of_range(session):
    await _seed(session)
    m = models.Merchant(awin_mid=3, name="UK Shop", slug="uk-shop")
    session.add(m)
    await session.flush()
    session.add(models.Offer(
        merchant_id=m.id, awin_product_id="gbp", name="Veste Anglaise", brand="UK",
        price=95.0, currency="GBP", in_stock=True, image_url="https://example.test/i.jpg",
    ))
    session.add(models.Offer(
        merchant_id=m.id, awin_product_id="cheap", name="Bricole", brand="UK",
        price=2.0, currency="EUR", in_stock=True, image_url="https://example.test/i.jpg",
    ))
    await session.commit()

    items = await _budget(session, limit=24)
    assert all(i["currency"] == "EUR" for i in items)
    assert all(10 <= i["price"] <= 100 for i in items)
    names = [i["name"] for i in items]
    assert "Veste Anglaise" not in names  # 95 GBP n'est pas « moins de 100 € »
    assert "Bricole" not in names


async def test_cartes_sans_devise_ou_stock_confirme_disparaissent(session):
    await _seed(session)
    merchant = models.Merchant(
        awin_mid=77,
        name="Boutique Inconnue",
        slug="boutique-inconnue",
    )
    session.add(merchant)
    await session.flush()
    session.add_all(
        [
            models.Offer(
                merchant_id=merchant.id,
                awin_product_id="missing-currency",
                name="Devise absente",
                price=50.0,
                currency=None,
                in_stock=True,
                image_url="https://example.test/i.jpg",
            ),
            models.Offer(
                merchant_id=merchant.id,
                awin_product_id="unknown-stock",
                name="Stock inconnu",
                price=50.0,
                currency="EUR",
                in_stock=None,
                image_url="https://example.test/i.jpg",
            ),
        ]
    )
    await session.commit()

    names = [item["name"] for item in await _budget(session, limit=24)]
    assert "Devise absente" not in names
    assert "Stock inconnu" not in names
