"""Contrat public : les cartes et filtres utilisent la taxonomie FILON.

Une offre peut ne pas avoir de catégorie brute de marchand. Cela ne doit jamais
faire disparaître sa catégorie FILON de l'API ni empêcher sa navigation.
"""
from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.routes.catalog import offers as offers_endpoint
from app.db import models
from app.db.base import Base
from app.services import taxonomy
from tests.endpoint_call import call


TELEPHONIE = "Téléphonie"
SPORT = "Sport & Plein air"
MODE_HOMME = "Mode homme"


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as s:
        merchant = models.Merchant(awin_mid=91, name="Source catalogue", slug="source")
        s.add(merchant)
        await s.flush()
        s.add_all([
            models.Offer(
                merchant_id=merchant.id,
                awin_product_id="phone-1",
                name="Samsung Galaxy S25",
                category=None,
                filon_category=TELEPHONIE,
                filon_subcategory="Smartphones",
                offer_kind="physical_product",
                price=799.0,
                currency="EUR",
                image_url="https://example.test/phone.jpg",
                is_canonical=True,
            ),
            models.Offer(
                merchant_id=merchant.id,
                awin_product_id="case-1",
                name="Coque pour Samsung Galaxy S25",
                category="Phone accessories",
                filon_category=TELEPHONIE,
                filon_subcategory="Coques & Protections",
                offer_kind="tech_accessory",
                price=19.0,
                currency="EUR",
                image_url="https://example.test/case.jpg",
                is_canonical=True,
            ),
            # Simule une ligne historique qui n'a pas encore été rattrapée :
            # elle doit être invisible sous Smartphones dès maintenant.
            models.Offer(
                merchant_id=merchant.id,
                awin_product_id="legacy-case-in-phone",
                name="Selencia Telefoonhoes voor Samsung Galaxy S24",
                category="Phone Cover",
                filon_category=TELEPHONIE,
                filon_subcategory="Smartphones",
                offer_kind="tech_accessory",
                price=24.0,
                currency="EUR",
                image_url="https://example.test/legacy-case.jpg",
                is_canonical=True,
            ),
            models.Offer(
                merchant_id=merchant.id,
                awin_product_id="wrong-gender",
                name="Robe femme longue",
                category="Women's clothing",
                filon_category=MODE_HOMME,
                filon_subcategory="Chemises",
                offer_kind="physical_product",
                price=69.0,
                currency="EUR",
                image_url="https://example.test/wrong-gender.jpg",
                is_canonical=True,
            ),
            models.Offer(
                merchant_id=merchant.id,
                awin_product_id="bike-1",
                name="Casque vélo urbain",
                category=None,
                filon_category=SPORT,
                filon_subcategory="Cyclisme",
                offer_kind="physical_product",
                price=59.0,
                currency="EUR",
                image_url="https://example.test/bike.jpg",
                is_canonical=True,
            ),
        ])
        await s.commit()
        yield s
    await engine.dispose()


async def test_la_carte_expose_la_categorie_filon_et_la_source_separement(session):
    result = await call(offers_endpoint, category=TELEPHONIE, session=session)
    assert result["total"] == 3
    phone = next(item for item in result["items"] if item["id"])
    assert all(item["category"] == TELEPHONIE for item in result["items"])
    assert {item["subcategory"] for item in result["items"]} == {"Smartphones", "Coques & Protections"}
    assert any(item["source_category"] is None for item in result["items"])
    assert all("offer_kind" in item for item in result["items"])
    assert phone["category"] != phone["source_category"]


async def test_le_filtre_par_slug_filon_trouve_les_offres_meme_sans_categorie_source(session):
    result = await call(
        offers_endpoint,
        category=taxonomy.slug_of(TELEPHONIE),
        subcategory="Smartphones",
        session=session,
    )
    assert result["total"] == 1
    assert result["items"][0]["name"] == "Samsung Galaxy S25"
    assert result["items"][0]["category"] == TELEPHONIE
    assert result["items"][0]["source_category"] is None


async def test_le_sous_rayon_smartphones_masque_les_coques_historiques_non_encore_rattrapees(session):
    result = await call(
        offers_endpoint,
        category=TELEPHONIE,
        subcategory="Smartphones",
        session=session,
    )
    assert result["total"] == 1
    assert [item["name"] for item in result["items"]] == ["Samsung Galaxy S25"]


@pytest.mark.parametrize(
    "name,source_category",
    [
        ("BasicPlus Schermbeschermer iPhone 11 Pro Max", "Telefoon- & tablet accessoires"),
        ("BeHello Schermprotector Glas iPhone 15 Plus", "Phone accessories"),
        ("Verre de protection trempé Quad Lock iPhone 12", "Cyclisme urbain"),
        ("Kit protection de smartphone Tigra MtCase", "Étui smartphone"),
        ("Bicycle mobile phone bracket for Samsung iPhone", "Cellphones & Telecommunications"),
        ("Support de table universel pour smartphones", "Accessoires Tablettes / Smartphones"),
        ("Support de Travail Reballing pour Apple iPhone", None),
        ("Amitec USB-oplader voor Smartphone en Tablet", "Opladers"),
    ],
)
async def test_le_sous_rayon_smartphones_masque_les_accessoires_residuels(session, name, source_category):
    merchant = await session.scalar(select(models.Merchant))
    session.add(models.Offer(
        merchant_id=merchant.id,
        awin_product_id=f"legacy-{name[:18]}",
        name=name,
        category=source_category,
        filon_category=TELEPHONIE,
        filon_subcategory="Smartphones",
        offer_kind="tech_accessory",
        price=9.0,
        currency="EUR",
        image_url="https://example.test/legacy-residual.jpg",
        is_canonical=True,
    ))
    await session.commit()
    result = await call(
        offers_endpoint,
        category=TELEPHONIE,
        subcategory="Smartphones",
        session=session,
    )
    assert result["total"] == 1
    assert [item["name"] for item in result["items"]] == ["Samsung Galaxy S25"]


async def test_mode_homme_masque_un_vetement_explicitement_feminin(session):
    result = await call(offers_endpoint, category=MODE_HOMME, session=session)
    assert result == {"total": 0, "items": []}


async def test_un_filtre_categorie_invalide_ne_retombe_pas_sur_les_categories_source(session):
    result = await call(offers_endpoint, category="Phone accessories", session=session)
    assert result == {"total": 0, "items": []}


async def test_le_rayon_et_sous_rayon_ensemble_ne_laissent_pas_passer_un_couple_incoherent(session):
    result = await call(
        offers_endpoint,
        category=SPORT,
        subcategory="Smartphones",
        session=session,
    )
    assert result == {"total": 0, "items": []}
