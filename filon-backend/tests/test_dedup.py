"""Un article, une carte.

Reproduit ce qui était affiché en production : cinq déclinaisons de la même
chemise, puis des pages entières du même marchand.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.routes.catalog import offers as offers_endpoint
from tests.endpoint_call import call
from app.db import models
from app.db.base import Base
from app.services.dedup import dedup_key, rebuild_canonical


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as s:
        yield s
    await engine.dispose()


class TestDedupKey:
    def test_size_suffixes_collapse_to_one_key(self):
        keys = {
            dedup_key(product_id=None, brand="GANT", name=f"GANT Regular Fit shirt green - Size {s}")
            for s in ("S", "M", "L", "XL")
        }
        assert len(keys) == 1

    def test_numeric_size_suffixes_collapse_too(self):
        a = dedup_key(product_id=None, brand="Nike", name="Nike Air Max - 42")
        b = dedup_key(product_id=None, brand="Nike", name="Nike Air Max - 44")
        assert a == b

    def test_different_products_keep_different_keys(self):
        a = dedup_key(product_id=None, brand="GANT", name="Chemise bleue")
        b = dedup_key(product_id=None, brand="GANT", name="Chemise verte")
        assert a != b

    def test_the_ean_product_wins_over_the_label(self):
        """Un suffixe de taille ne peut pas tromper un identifiant produit."""
        a = dedup_key(product_id=42, brand="GANT", name="Chemise - Size M")
        b = dedup_key(product_id=42, brand="AUTRE", name="Libellé totalement différent")
        assert a == b == "p:42"

    def test_empty_name_has_no_key(self):
        assert dedup_key(product_id=None, brand="X", name="") is None


async def _seed(s):
    m = models.Merchant(awin_mid=1, name="Overhemden - NL", slug="overhemden")
    s.add(m)
    await s.flush()
    seeded_offers = []
    for i, size in enumerate(("S", "M", "L", "XL")):
        offer = models.Offer(
            merchant_id=m.id, awin_product_id=f"g{i}",
            name=f"GANT Regular Fit shirt green, Chequered - Size {size}",
            brand="GANT", price=100.0 + i, currency="EUR", in_stock=True,
            image_url="https://example.test/i.jpg",
        )
        seeded_offers.append(offer)
        s.add(offer)
    blue = models.Offer(
        merchant_id=m.id, awin_product_id="blue", name="GANT Regular Fit shirt blue",
        brand="GANT", price=95.0, currency="EUR", in_stock=True,
        image_url="https://example.test/i.jpg",
    )
    seeded_offers.append(blue)
    s.add(blue)
    await s.flush()
    captured_at = datetime.now(UTC).replace(tzinfo=None)
    s.add_all(
        [
            models.PriceSnapshot(
                offer_id=offer.id,
                price=offer.price,
                currency="EUR",
                in_stock=True,
                captured_at=captured_at,
            )
            for offer in seeded_offers
        ]
    )
    await s.commit()


async def test_the_five_shirts_become_two_cards(session):
    await _seed(session)
    summary = await rebuild_canonical(session)
    assert summary["offers_processed"] == 5
    assert summary["distinct_products"] == 2

    # Défauts lus dans la signature : un nouveau paramètre d'endpoint ne doit
    # pas casser un test qui ne s'y intéresse pas.
    shown = await call(offers_endpoint, duplicates=False, session=session)
    assert shown["total"] == 2

    # Le représentant retenu est le moins cher de son groupe.
    green = next(i for i in shown["items"] if "green" in i["name"])
    assert green["price"] == 100.0

    # Les doublons restent consultables pour qui les demande explicitement.
    everything = await call(offers_endpoint, duplicates=True, session=session)
    assert everything["total"] == 5


async def test_offers_without_a_key_stay_visible(session):
    """Mieux vaut un doublon qu'un produit qui disparaît du catalogue."""
    m = models.Merchant(awin_mid=2, name="M", slug="m")
    session.add(m)
    await session.flush()
    session.add(models.Offer(
        merchant_id=m.id, awin_product_id="x", name="",
        brand=None, price=10.0, currency="EUR", image_url="https://example.test/i.jpg",
    ))
    await session.commit()
    await rebuild_canonical(session)

    kept = (
        await session.execute(select(models.Offer.is_canonical))
    ).scalars().all()
    assert all(kept)


class TestNeverMergesDistinctProducts:
    """Fusionner deux produits distincts est bien pire qu'afficher un doublon.

    Une première version rognait les chiffres finaux : « Article numéro 12345 »
    devenait « Article numéro 123 » et fusionnait avec un autre produit. Le
    défaut n'est apparu qu'à l'échelle — 40 000 produits réduits à 401.
    """

    @pytest.mark.parametrize(
        "a,b",
        [
            ("Article de catalogue numero 12345", "Article de catalogue numero 123"),
            ("iPhone 15", "iPhone 16"),
            ("Casque Sony WH-1000XM5", "Casque Sony WH-1000XM4"),
            ("Pneu Michelin 205", "Pneu Michelin 20"),
        ],
    )
    def test_trailing_digits_are_not_stripped_without_a_separator(self, a, b):
        ka = dedup_key(product_id=None, brand="X", name=a)
        kb = dedup_key(product_id=None, brand="X", name=b)
        assert ka != kb

    def test_a_separator_is_required_for_a_bare_size(self):
        same = dedup_key(product_id=None, brand="Nike", name="Nike Air Max - 42")
        other = dedup_key(product_id=None, brand="Nike", name="Nike Air Max - 44")
        assert same == other
