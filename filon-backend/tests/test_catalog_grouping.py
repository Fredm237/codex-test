"""Tests du regroupement des offres en produits, par EAN."""

from __future__ import annotations

from datetime import UTC, datetime

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

    seeded_offers = []

    def offer(m, pid, name, price, ean):
        row = models.Offer(
            merchant_id=m.id, awin_product_id=pid, name=name, brand="ACME",
            price=price, currency="EUR", in_stock=True, ean=ean,
            image_url="https://example.test/i.jpg", deep_link="https://example.test/go",
        )
        seeded_offers.append(row)
        return row

    # Même produit, trois marchands-lignes, trois écritures d'EAN différentes.
    s.add(offer(a, "a1", "Casque ACME X1", 129.0, EAN_A))
    s.add(offer(b, "b1", "Casque ACME X1 - Livraison gratuite !", 119.0, EAN_A))
    s.add(offer(b, "b2", "Casque ACME X1", 135.0, EAN_A))
    # Un autre produit, un seul marchand.
    s.add(offer(a, "a2", "Clavier ACME K2", 59.0, EAN_B))
    # Sans EAN exploitable : doit rester autonome.
    s.add(offer(a, "a3", "Produit sans code", 20.0, "N/A"))
    s.add(offer(a, "a4", "Produit code faux", 25.0, "4006381333932"))
    await s.flush()
    captured_at = datetime.now(UTC).replace(tzinfo=None)
    s.add_all(
        [
            models.PriceSnapshot(
                offer_id=offer_row.id,
                price=offer_row.price,
                currency="EUR",
                in_stock=True,
                captured_at=captured_at,
            )
            for offer_row in seeded_offers
        ]
    )
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
    assert all(offer["evidence_current"] is True for offer in detail["offers"])
    assert all(offer["observed_at"] is not None for offer in detail["offers"])
    assert all(
        datetime.fromisoformat(offer["observed_at"]).utcoffset() == UTC.utcoffset(None)
        for offer in detail["offers"]
    )
    assert detail["merchants_count"] == 2


async def test_product_detail_abstains_across_current_currencies(session):
    await _seed(session)
    await rebuild_products(session)
    gbp_offer = await session.scalar(
        select(models.Offer).where(models.Offer.awin_product_id == "b2")
    )
    gbp_offer.currency = "GBP"
    session.add(
        models.PriceSnapshot(
            offer_id=gbp_offer.id,
            price=gbp_offer.price,
            currency="GBP",
            in_stock=True,
            captured_at=datetime.now(UTC).replace(tzinfo=None),
        )
    )
    await session.commit()

    detail = await product_detail(ean=EAN_A, session=session)
    assert detail["currency"] is None
    assert detail["price_min"] is None
    assert detail["price_max"] is None
    assert {offer["currency"] for offer in detail["offers"]} == {"EUR", "GBP"}
    assert detail["decision"]["facts"]["currency"] is None

    listing = await products(
        q=None,
        brand=None,
        multi_merchant=False,
        limit=48,
        offset=0,
        session=session,
    )
    product = next(item for item in listing["items"] if item["ean"] == EAN_A)
    assert product["currency"] is None
    assert product["price_min"] is None
    assert product["price_max"] is None
    assert product["compared_offers_count"] == 0


async def test_offer_detail_masks_a_price_without_matching_snapshot(session):
    from app.api.routes.catalog import offer_detail

    await _seed(session)
    offer = await session.scalar(
        select(models.Offer).where(models.Offer.awin_product_id == "a3")
    )
    offer.price = 21.0
    await session.commit()

    detail = await offer_detail(offer_id=offer.id, session=session)
    assert detail["price"] is None
    assert detail["currency"] is None
    assert detail["in_stock"] is None
    assert detail["observed_at"] is None
    assert detail["evidence_current"] is False
    assert detail["history"]
    assert all(point["currency"] == "EUR" for point in detail["history"])
    assert all(point["in_stock"] is True for point in detail["history"])
    assert detail["decision"]["recommendation_scope"] == "non_recommandee"


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


async def test_offer_detail_links_to_grouped_product_only_when_useful(session):
    """Annoncer « disponible chez 1 marchand » n'aide personne."""
    from app.api.routes.catalog import offer_detail
    from sqlalchemy import select as _select

    await _seed(session)
    await rebuild_products(session)

    # EAN_A est vendu par deux marchands → le renvoi doit apparaître.
    shared = (
        await session.execute(
            _select(models.Offer.id)
            .join(models.CatalogProduct, models.Offer.product_id == models.CatalogProduct.id)
            .where(models.CatalogProduct.ean == EAN_A)
        )
    ).scalars().first()
    detail = await offer_detail(offer_id=shared, session=session)
    assert detail["product"] is not None
    assert detail["product"]["ean"] == EAN_A
    assert detail["product"]["merchants_count"] == 2

    # EAN_B n'a qu'un marchand → pas de renvoi.
    alone = (
        await session.execute(
            _select(models.Offer.id)
            .join(models.CatalogProduct, models.Offer.product_id == models.CatalogProduct.id)
            .where(models.CatalogProduct.ean == EAN_B)
        )
    ).scalars().first()
    assert (await offer_detail(offer_id=alone, session=session))["product"] is None

    # Offre sans EAN exploitable → pas de renvoi non plus.
    orphan = (
        await session.execute(
            _select(models.Offer.id).where(models.Offer.product_id.is_(None))
        )
    ).scalars().first()
    assert (await offer_detail(offer_id=orphan, session=session))["product"] is None


async def test_sitemap_only_lists_products_worth_indexing(session):
    """Une fiche à un seul marchand redirait ce que dit déjà la fiche de l'offre."""
    from app.api.routes.catalog import sitemap_products

    await _seed(session)
    await rebuild_products(session)

    listed = await sitemap_products(limit=5000, offset=0, min_merchants=2, session=session)
    eans = [i["ean"] for i in listed["items"]]
    assert listed["total"] == 1
    assert eans == [EAN_A]          # deux marchands
    assert EAN_B not in eans        # un seul marchand : exclu

    # Le seuil reste réglable, et la pagination est cohérente avec le total.
    everything = await sitemap_products(limit=5000, offset=0, min_merchants=1, session=session)
    assert everything["total"] == 2
    assert all(
        datetime.fromisoformat(item["updated"]).utcoffset() == UTC.utcoffset(None)
        for item in everything["items"]
    )
    page_two = await sitemap_products(limit=1, offset=1, min_merchants=1, session=session)
    assert len(page_two["items"]) == 1
    assert page_two["items"][0]["ean"] != everything["items"][0]["ean"]


async def test_contextual_offers_are_never_grouped_by_ean(session):
    await _seed(session)
    merchant = (await session.execute(select(models.Merchant).where(models.Merchant.slug == "a"))).scalar_one()
    stay = models.Offer(
        merchant_id=merchant.id,
        awin_product_id="stay-a",
        name="Appartement de vacances à Bruges",
        category="Appartement de vacances",
        offer_kind="accommodation",
        price=154.0,
        currency="EUR",
        ean=EAN_A,
        image_url="https://example.test/stay.jpg",
        deep_link="https://example.test/stay",
    )
    session.add(stay)
    await session.commit()

    summary = await rebuild_products(session)
    await session.refresh(stay)

    assert stay.product_id is None
    assert summary["offers_total"] == 6  # seuls les produits physiques sont éligibles
    detail = await product_detail(ean=EAN_A, session=session)
    assert detail["offers_count"] == 3
