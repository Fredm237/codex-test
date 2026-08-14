"""Recherche catalogue.

La première version cherchait la requête entière en sous-chaîne : elle exigeait
que les mots se suivent dans cet ordre exact et ne renvoyait rien dès deux mots
— c'est-à-dire presque toujours.
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.routes.catalog import offers as offers_endpoint
from tests.endpoint_call import call
from app.db import models
from app.db.base import Base
from app.services.search import (
    MAX_TERMS, department_browse_exclusions, primary_product_filter, relevance_order, search_clause, stem, terms_of,
)
from app.services.catalog_search import _PRIMARY_MIN_PRICE, _catalogue_intent, _primary_image_url, _required_name_terms


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

        # Le libellé du marchand dit « bleu », l'utilisateur tapera « bleue ».
        s.add(offer("1", "Chemise Regular Fit bleu rayé", "GANT", 89.0))
        s.add(offer("2", "Chemise Slim Fit verte", "GANT", 79.0))
        s.add(offer("3", "Pantalon chino beige", "GANT", 99.0))
        s.add(offer("4", "Casque audio sans fil Bluetooth", "Sony", 299.0))
        s.add(offer("5", "Apple iPhone 15 128 Go", "Apple", 899.0))
        s.add(offer("6", "Coque souple Apple iPhone 15", "Apple", 19.0))
        s.add(offer("7", "Support de bureau pour iPhone 15", "Marque", 12.0))
        s.add(offer("8", "Lenovo IdeaPad ordinateur portable 15 pouces", "Lenovo", 649.0))
        s.add(offer("9", "Support pour ordinateur portable 15 pouces", "Marque", 25.0))
        s.add(offer("10", "Siphon de cuisine inox", "Marque", 99.0))
        s.add(offer("11", "Plaque PCB iPhone 15", "Marque", 90.0))
        s.add(offer("12", "Valise avec compartiment ordinateur portable", "Marque", 220.0))
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
    # Les défauts viennent de la signature : ajouter un paramètre à l'endpoint
    # ne doit pas casser des tests qui ne s'y intéressent pas.
    return await call(offers_endpoint, q=q, session=session, **kw)


class TestMultiWordSearch:
    async def test_words_no_longer_need_to_be_adjacent(self, session):
        """« chemise bleue gant » : les trois mots ne se suivent nulle part."""
        res = await _search(session, "chemise bleue gant")
        assert res["total"] == 1
        assert res["items"][0]["name"].startswith("Chemise Regular Fit bleu")

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

    async def test_accord_is_absorbed(self, session):
        """Le marchand écrit « bleu », l'utilisateur tape « bleue »."""
        assert (await _search(session, "chemise bleue"))["total"] == 1
        assert (await _search(session, "chemises bleues"))["total"] == 1
        assert (await _search(session, "chemise bleu"))["total"] == 1


class TestCatalogueIntent:
    def test_high_tech_browse_excludes_gift_cards_and_phone_covers(self):
        excluded = department_browse_exclusions("high-tech")
        assert excluded is not None
        assert {"gift card", "backcover", "phone cover", "telefoonhoes", "service pack"}.issubset(excluded)

    def test_other_department_browse_does_not_hide_unrelated_products(self):
        assert department_browse_exclusions("maison") is None

    def test_laptop_request_keeps_product_anchor_and_excludes_accessories(self):
        intent = _catalogue_intent("un ordinateur portable étudiant sous 800 €")
        assert intent is not None
        anchor, excluded = intent
        assert anchor == "laptop"
        assert {"housse", "sleeve", "support"}.issubset(excluded)

    def test_video_editing_request_routes_to_catalogue_laptop_intent(self):
        intent = _catalogue_intent("une machine pour le montage vidéo")
        assert intent is not None
        assert intent[0] == "laptop"

    def test_smartphone_request_keeps_product_anchor_and_excludes_cases(self):
        intent = _catalogue_intent("un smartphone à 500 €")
        assert intent is not None
        anchor, excluded = intent
        assert anchor == "smartphone"
        assert {"coque", "case", "protection"}.issubset(excluded)

    def test_unrecognised_request_is_not_forced_into_a_category(self):
        assert _catalogue_intent("lampe de bureau minimaliste") is None

    def test_primary_product_thresholds_only_reject_implausible_feed_prices(self):
        assert _PRIMARY_MIN_PRICE["laptop"] == 200.0
        assert _PRIMARY_MIN_PRICE["smartphone"] == 80.0
        assert _PRIMARY_MIN_PRICE["casque"] == 25.0

    def test_public_search_primary_product_filter_keeps_explicit_accessories(self):
        assert primary_product_filter("coque iphone 15") is None

    def test_public_search_primary_product_filter_protects_generic_phone_queries(self):
        result = primary_product_filter("iphone 15")
        assert result is not None
        excluded, minimum_price = result
        assert "coque" in excluded
        assert minimum_price == 80.0

    def test_noise_cancelling_request_requires_a_verified_feature_in_title(self):
        required = _required_name_terms("casque à réduction de bruit", "casque")
        assert {"noise", "anc", "cancel"}.issubset(required)

    def test_generic_headphone_request_does_not_add_unrequested_feature_constraint(self):
        assert _required_name_terms("casque bluetooth", "casque") == ()

    def test_multiple_feed_images_use_the_first_valid_url(self):
        assert _primary_image_url("https://img.example/one.jpg, https://img.example/two.jpg") == "https://img.example/one.jpg"
        assert _primary_image_url("invalid, https://img.example/valid.jpg") == "https://img.example/valid.jpg"
        assert _primary_image_url(None) is None


class TestRelevance:
    async def test_the_exact_phrase_comes_first(self, session):
        res = await _search(session, "chemise slim")
        assert res["items"][0]["name"] == "Chemise Slim Fit verte"

    async def test_names_starting_with_the_first_term_rank_above_the_rest(self, session):
        res = await _search(session, "chemise")
        # Les deux commencent par « Chemise » : le moins cher départage.
        assert [i["price"] for i in res["items"]] == [79.0, 89.0]

    async def test_generic_iphone_query_does_not_present_parts_as_phones(self, session):
        res = await _search(session, "iphone")
        assert res["total"] == 1
        assert res["items"][0]["name"] == "Apple iPhone 15 128 Go"

    async def test_iphone_query_does_not_match_a_siphon_after_stemming(self, session):
        res = await _search(session, "iphone")
        assert all("siphon" not in item["name"].lower() for item in res["items"])
        assert all("plaque pcb" not in item["name"].lower() for item in res["items"])

    async def test_explicit_iphone_accessory_query_remains_searchable(self, session):
        res = await _search(session, "coque iphone")
        assert res["total"] == 1
        assert "Coque" in res["items"][0]["name"]

    async def test_generic_laptop_query_does_not_present_a_stand_as_a_computer(self, session):
        res = await _search(session, "ordinateur portable")
        assert res["total"] == 1
        assert res["items"][0]["name"].startswith("Lenovo IdeaPad")

    async def test_generic_laptop_query_does_not_present_a_suitcase_as_a_computer(self, session):
        res = await _search(session, "ordinateur portable")
        assert all("valise" not in item["name"].lower() for item in res["items"])


class TestStem:
    """Les libellés marchands n'accordent pas comme l'utilisateur écrit."""

    @pytest.mark.parametrize(
        "singular,plural",
        [
            ("bleu", "bleue"), ("bleu", "bleus"),
            ("chemise", "chemises"),
            ("manteau", "manteaux"),
            ("chaussure", "chaussures"),
        ],
    )
    def test_singular_and_plural_converge(self, singular, plural):
        assert stem(singular) == stem(plural)

    @pytest.mark.parametrize("term", ["robe", "sony", "prix", "ordinateur", "pantalon"])
    def test_short_or_invariant_terms_are_left_alone(self, term):
        assert stem(term) == term

    def test_stems_never_get_too_short(self):
        """Un radical trop court ramenerait n'importe quoi."""
        for term in ("manteaux", "chemises", "bleues", "sacs"):
            assert len(stem(term)) >= 3

    def test_brand_words_keep_their_significant_final_e(self):
        assert stem("iphone") == "iphone"

    @pytest.mark.parametrize(
        "terme,intrus",
        [
            ("robe", ["robot aspirateur", "robinet de cuisine"]),
            ("chargeur", ["chargement automatique", "chargeuse compacte"]),
            ("moniteur", ["monitorage cardiaque"]),
            ("alimentation", ["aliments pour chien"]),
        ],
    )
    def test_le_radical_ne_deporte_pas_la_recherche(self, terme, intrus):
        """Le radical sert de sous-chaîne : trop court, il change de rayon.

        Une passe de « stemming amélioré » avait ajouté les suffixes
        dérivationnels — tion, ment, eur, ique. « robe » devenait « rob » et
        ramenait robots et robinets ; « chargeur » devenait « charg » et
        ramenait chargement et chargeuse. C'est le même mélange de rayons que
        celui constaté au catalogue, par un autre chemin.
        """
        radical = stem(terme)
        for libelle in intrus:
            assert radical not in libelle, f"« {terme} » → « {radical} » ramène « {libelle} »"

    def test_le_pluriel_neerlandais_reste_absorbe(self):
        """La normalisation NL de la même passe était bonne, elle reste."""
        assert stem("tafels") == stem("tafel")

    def test_les_accents_sont_normalises(self):
        assert stem("écouteurs") == stem("ecouteurs")
