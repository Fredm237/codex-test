from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import models
from app.db.base import Base
from app.intelligence.general_catalog import _base_statement, retrieve_general_offers
from app.intelligence.intent_resolution import GeneralIntent, IntentScope, resolve_intent
from app.services import taxonomy


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as value:
        yield value
    await engine.dispose()


def catalog_offer(merchant_id: int, index: int, name: str, category: str, subcategory: str | None = None) -> models.Offer:
    return models.Offer(
        merchant_id=merchant_id,
        awin_product_id=f"general-{index}",
        name=name,
        filon_category=category,
        filon_subcategory=subcategory,
        offer_kind=taxonomy.PHYSICAL_PRODUCT,
        is_canonical=True,
        is_adult=False,
        price=25.0 + index / 100,
        currency="EUR",
        in_stock=True,
        image_url=f"https://example.test/{index}.jpg",
    )


async def test_lit_integralement_le_scope_resolu_meme_apres_l_ancienne_premiere_page(session):
    merchant = models.Merchant(awin_mid=9911, name="Test général", slug="test-general")
    session.add(merchant)
    await session.flush()
    session.add_all([
        catalog_offer(merchant.id, index, f"Tennis Shirt {index}", taxonomy.SPORT)
        for index in range(1, 502)
    ])
    session.add(catalog_offer(merchant.id, 9999, "Ballon de football", taxonomy.SPORT))
    await session.commit()

    intent = resolve_intent("Tenniskleding onder 200 €", "nl")
    offers = await retrieve_general_offers(session, intent)

    assert len(offers) == 501
    assert offers[-1].name == "Tennis Shirt 501"
    assert all("tennis" in offer.name.lower() for offer in offers)


async def test_exige_la_reference_de_modele_resolue_avant_la_selection(session):
    merchant = models.Merchant(awin_mid=9913, name="Test modèle", slug="test-modele")
    session.add(merchant)
    await session.flush()
    expected = catalog_offer(merchant.id, 15, "Apple iPhone 15 128GB", taxonomy.TELEPHONIE, "Smartphones")
    wrong = catalog_offer(merchant.id, 16, "Apple iPhone 16e écran 15,5 cm", taxonomy.TELEPHONIE, "Smartphones")
    session.add_all([expected, wrong])
    await session.commit()

    intent = resolve_intent("iPhone 15 sous 600 €", "fr")
    offers = await retrieve_general_offers(session, intent)

    assert [offer.offer_id for offer in offers] == [expected.id]


def test_borne_le_scope_sql_par_la_reference_modele_avant_pagination():
    intent = resolve_intent("iPhone 15 sous 600 €", "fr")
    statement = _base_statement(intent.scopes[0], intent.required_title_phrases)
    parameters = set(statement.compile().params.values())

    assert "%iphone 15%" in parameters
    assert "%iphone-15%" in parameters


async def test_lit_tous_les_scopes_d_une_demande_multi_produits(session):
    merchant = models.Merchant(awin_mid=9912, name="Test multi", slug="test-multi")
    session.add(merchant)
    await session.flush()
    laptop = catalog_offer(merchant.id, 1, "Ordinateur portable étudiant", taxonomy.INFORMATIQUE, "Ordinateurs portables")
    bag = catalog_offer(merchant.id, 2, "Sac à dos ordinateur", taxonomy.BAGAGERIE, "Sacs à dos")
    session.add_all([laptop, bag])
    await session.commit()

    intent = resolve_intent("ordinateur portable et sac à dos sous 1000 €", "fr")
    offers = await retrieve_general_offers(session, intent)

    assert {offer.offer_id for offer in offers} == {laptop.id, bag.id}


async def test_scope_taxonomique_valide_survit_aux_termes_libres_absents(session):
    merchant = models.Merchant(awin_mid=9914, name="Test scope", slug="test-scope")
    session.add(merchant)
    await session.flush()
    tent = catalog_offer(merchant.id, 1, "Tente familiale 4 personnes", taxonomy.SPORT, "Camping & Randonnée")
    sleeping_bag = catalog_offer(merchant.id, 2, "Sac de couchage léger", taxonomy.SPORT, "Camping & Randonnée")
    session.add_all([tent, sleeping_bag])
    await session.commit()

    intent = GeneralIntent(
        raw_request="kampeeruitrusting onder 300 €",
        locale="nl",
        scopes=(IntentScope(taxonomy.SPORT, "Camping & Randonnée", "kampeeruitrusting", ("kampeer", "uitrusting")),),
        terms=("kampeer", "uitrusting"),
        required_title_phrases=(),
        budget_eur=300.0,
    )
    offers = await retrieve_general_offers(session, intent)

    assert {offer.offer_id for offer in offers} == {tent.id, sleeping_bag.id}
