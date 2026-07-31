"""Tests du regroupement des offres en produits, par EAN."""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.routes.catalog import product_detail, products
from app.db import models
from app.db.base import Base
from app.services.catalog_grouping import normalize_ean, rebuild_products

# Codes-barres réels et valides (chiffre de contrôle correct).
EAN_A = "4006381333931"
EAN_B = "5901234123457"


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as s:
        yield s
    await engine.dispose()


class TestNormalizeEan:
    def test_accepts_valid_codes(self):
        assert normalize_ean(EAN_A) == EAN_A
        assert normalize_ean(f"  {EAN_A} ") == EAN_A

    def test_rejects_bad_check_digit(self):
        assert normalize_ean("4006381333932") is None

    def test_rejects_filler_and_junk(self):
        for junk in ("0000000000000", "1111111111111", "N/A", "", None, "123"):
            assert normalize_ean(junk) is None

    def test_upc_and_gtin14_converge_to_same_ean13(self):
        """Deux marchands au format différent doivent se rejoindre."""
        forms = {normalize_ean(x) for x in ("012345678905", "0012345678905", "00012345678905")}
        assert len(forms) == 1


async def _seed(s):
    a = models.Merchant(awin_mid=1, name="Boutique A", slug="a")
    b = models.Merchant(awin_mid=2, name="Boutique B", slug="b")
    s.add_all([a, b])
    await s.flush()

    def offer(m, pid, name, price, ean):
        return models.Offer(
            merchant_id=m.id, awin_product_id=pid, name=name, brand="ACME",
            price=price, currency="EUR", ean=ean,
            image_url="https://example.test/i.jpg", deep_link="https://example.test/go",
        )

    # Même produit, trois marchands-lignes, trois écritures d'EAN différentes.
    s.add(offer(a, "a1", "Casque ACME X1", 129.0, EAN_A))
    s.add(offer(b, "b1", "Casque ACME X1 - Livraison gratuite !", 119.0, EAN_A))
    s.add(offer(b, "b2", "Casque ACME X1", 135.0, EAN_A))
    # Un autre produit, un seul marchand.
    s.add(offer(a, "a2", "Clavier ACME K2", 59.0, EAN_B))
    # Sans EAN exploitable : doit rester autonome.
    s.add(offer(a, "a3", "Produit sans code", 20.0, "N/A"))
    s.add(offer(a, "a4", "Produit code faux", 25.0, "4006381333932"))
    await s.commit()


async def test_groups_offers_across_merchants(session):
    await _seed(session)
    summary = await rebuild_products(session)

    assert summary["products_total"] == 2
    assert summary["products_multi_merchant"] == 1
    assert summary["offers_total"] == 6
    assert summary["offers_with_valid_ean"] == 4  # 3 + 1, les 2 douteux exclus


async def test_offers_without_valid_ean_stay_unlinked(session):
    await _seed(session)
    await rebuild_products(session)

    orphans = (
        await session.execute(
            select(models.Offer.name).where(models.Offer.product_id.is_(None))
        )
    ).scalars().all()
    assert set(orphans) == {"Produit sans code", "Produit code faux"}


async def test_canonical_name_is_the_consensus_not_the_embellished_one(session):
    await _seed(session)
    await rebuild_products(session)

    p = (
        await session.execute(
            select(models.CatalogProduct).where(models.CatalogProduct.ean == EAN_A)
        )
    ).scalar_one()
    assert p.name == "Casque ACME X1"
    assert p.merchants_count == 2
    assert p.offers_count == 3
    assert p.price_min == 119.0
    assert p.price_max == 135.0


async def test_rebuild_is_idempotent(session):
    await _seed(session)
    first = await rebuild_products(session)
    second = await rebuild_products(session)

    assert first["products_created"] == 2
    assert second["products_created"] == 0
    assert second["products_updated"] == 2
    assert second["products_total"] == first["products_total"]


async def test_product_detail_lists_offers_cheapest_first(session):
    await _seed(session)
    await rebuild_products(session)

    detail = await product_detail(ean=EAN_A, session=session)
    prices = [o["price"] for o in detail["offers"]]
    assert prices == sorted(prices)
    assert prices[0] == 119.0
    assert detail["merchants_count"] == 2


async def test_products_endpoint_can_filter_multi_merchant(session):
    await _seed(session)
    await rebuild_products(session)

    # Tous les paramètres sont passés explicitement : appelée hors HTTP, la
    # fonction ne reçoit pas les valeurs par défaut que FastAPI résout à la
    # requête — et un `Query(default=None)` non résolu est truthy, donc les
    # filtres optionnels s'appliqueraient sur un objet Query.
    common = dict(q=None, brand=None, limit=48, offset=0, session=session)
    everything = await products(multi_merchant=False, **common)
    assert everything["total"] == 2

    shared = await products(multi_merchant=True, **common)
    assert shared["total"] == 1
    assert shared["items"][0]["ean"] == EAN_A
