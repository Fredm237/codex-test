"""Le repli assistant doit rester une absence vérifiée, jamais une synthèse commerciale."""

import pytest

from app.services import catalog_search, recommend


def test_fallback_labels_are_localized_and_do_not_claim_unverified_product_traits():
    assert recommend._verified_rank_label(0, "fr") == "Offre vérifiée"
    assert recommend._verified_rank_label(2, "en") == "Another verified offer"
    assert recommend._verified_rank_label(3, "nl") == "Te controleren optie"
    assert "autonomie" not in recommend._verified_rank_label(2, "fr").lower()
    assert "performance" not in recommend._verified_rank_label(3, "fr").lower()
    assert "recondition" not in recommend._verified_rank_label(4, "fr").lower()


class _EmptyCache:
    async def get_json(self, key):
        return None

    async def set_json(self, key, value, ttl):
        self.value = value


@pytest.mark.anyio
async def test_missing_catalogue_offer_does_not_generate_synthetic_cards_or_call_a_model(monkeypatch):
    async def no_products(*args, **kwargs):
        return []

    cache = _EmptyCache()
    monkeypatch.setattr(catalog_search, "search_internal_products", no_products)
    monkeypatch.setattr(recommend, "get_cache", lambda: cache)

    def forbidden_router():
        raise AssertionError("Aucun modèle ne doit être appelé sans offre catalogue vérifiée")

    monkeypatch.setattr(recommend, "get_router", forbidden_router)

    result = await recommend.generate_result("iPhone 15", 1500, country="be", locale="fr")

    assert result["real"] is False
    assert result["offers"] == 0
    assert result["cards"] == []
    assert cache.value["cards"] == []



def test_cle_cache_assistant_inclut_la_version_du_moteur_de_decision():
    current = recommend._recommend_cache_key("smartphone sous 400 euros", 400, "be", "fr")
    previous = recommend.cache_key("recommend", "1", "smartphone sous 400 euros", "400", "be", "fr")

    assert current != previous



def test_cle_cache_assistant_depend_de_la_politique_de_pertinence():
    from app.services import relevance

    key = recommend._recommend_cache_key("ordinateur portable sous 700 euros", 700, "be", "fr")

    assert relevance.CATALOG_RELEVANCE_POLICY_VERSION in recommend.RECOMMENDATION_ENGINE_VERSION
    assert recommend.RECOMMENDATION_ENGINE_VERSION in key or key != recommend.cache_key(
        "recommend", "assistant-catalog-policy-obsolete", "ordinateur portable sous 700 euros", "700", "be", "fr"
    )
