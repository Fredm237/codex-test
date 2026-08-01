"""Recherche catalogue.

La première version cherchait la requête entière en sous-chaîne : elle exigeait
que les mots se suivent dans cet ordre exact et ne renvoyait rien dès deux mots
— c'est-à-dire presque toujours.
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.routes.catalog import offers as offers_endpoint
from app.db import models
from app.db.base import Base
from app.services.search import MAX_TERMS, relevance_order, search_clause, terms_of


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as s:
        m = models.Merchant(awin_mid=1, name="Boutique", slug="b")
        s.add(m)
        await s.flush()

        def offer(pid, name, brand, price):
            return models.Offer(
                merchant_id=m.id, awin_product_id=pid, name=name, brand=brand,
                price=price, currency="EUR", image_url="https://example.test/i.jpg",
                is_canonical=True,
            )

        s.add(offer("1", "Chemise Regular Fit bleue rayée", "GANT", 89.0))
        s.add(offer("2", "Chemise Slim Fit verte", "GANT", 79.0))
        s.add(offer("3", "Pantalon chino beige", "GANT", 99.0))
        s.add(offer("4", "Casque audio sans fil Bluetooth", "Sony", 299.0))
        await s.commit()
        yield s
    await engine.dispose()


class TestTerms:
    def test_splits_and_normalises(self):
        assert terms_of("Chemise BLEUE gant") == ["chemise", "bleue", "gant"]

    def test_drops_single_letters_and_duplicates(self):
        assert terms_of("a chemise chemise b") == ["chemise"]

    def test_is_bounded(self):
        assert len(terms_of(" ".join(f"mot{i}" for i in range(20)))) == MAX_TERMS

    def test_empty_query_yields_nothing(self):
        assert terms_of("") == []
        assert terms_of(None) == []
        assert search_clause("  ") is None
        assert relevance_order("!!") is None


async def _search(session, q, **kw):
    params = dict(
        q=q, merchant=None, category=None, subcategory=None, brand=None,
        price_min=None, price_max=None, sort="relevance", duplicates=False,
        limit=48, offset=0, session=session,
    )
    params.update(kw)
    return await offers_endpoint(**params)


class TestMultiWordSearch:
    async def test_words_no_longer_need_to_be_adjacent(self, session):
        """« chemise bleue gant » : les trois mots ne se suivent nulle part."""
        res = await _search(session, "chemise bleue gant")
        assert res["total"] == 1
        assert res["items"][0]["name"].startswith("Chemise Regular Fit bleue")

    async def test_the_brand_is_searched_too(self, session):
        res = await _search(session, "gant chino")
        assert res["total"] == 1
        assert "chino" in res["items"][0]["name"].lower()

    async def test_every_term_must_match(self, session):
        assert (await _search(session, "chemise inexistante"))["total"] == 0

    async def test_a_single_word_still_works(self, session):
        assert (await _search(session, "chemise"))["total"] == 2

    async def test_search_is_case_insensitive(self, session):
        assert (await _search(session, "CHEMISE Bleue"))["total"] == 1


class TestRelevance:
    async def test_the_exact_phrase_comes_first(self, session):
        res = await _search(session, "chemise slim")
        assert res["items"][0]["name"] == "Chemise Slim Fit verte"

    async def test_names_starting_with_the_first_term_rank_above_the_rest(self, session):
        res = await _search(session, "chemise")
        # Les deux commencent par « Chemise » : le moins cher départage.
        assert [i["price"] for i in res["items"]] == [79.0, 89.0]
