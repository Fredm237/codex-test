"""Le repli assistant doit rester une absence vérifiée, jamais une synthèse commerciale."""

import pytest

from app.core.observability import product_intelligence_metrics
from app.services import catalog_search, recommend


def test_fallback_labels_are_localized_and_do_not_claim_unverified_product_traits():
    assert recommend._verified_rank_label(0, "fr") == "Offre indexée"
    assert recommend._verified_rank_label(2, "en") == "Another indexed offer"
    assert recommend._verified_rank_label(3, "nl") == "Te controleren optie"
    assert "autonomie" not in recommend._verified_rank_label(2, "fr").lower()
    assert "performance" not in recommend._verified_rank_label(3, "fr").lower()
    assert "recondition" not in recommend._verified_rank_label(4, "fr").lower()


def test_legacy_synthetic_commercial_engine_is_removed():
    assert not hasattr(recommend, "_coerce_card")
    assert not hasattr(recommend, "_SYSTEM")
    assert "cashback" not in " ".join(recommend.STEPS).lower()
    assert "avis" not in " ".join(recommend.STEPS).lower()


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
    product_intelligence_metrics.reset()

    result = await recommend.generate_result("iPhone 15", 1500, country="ch", locale="fr")

    assert result["real"] is False
    assert result["offers"] == 0
    assert result["cards"] == []
    assert result["country"] == "ch"
    assert result["currency"] is None
    assert cache.value["cards"] == []
    assert cache.value["currency"] is None
    metrics = product_intelligence_metrics.snapshot()["recommendation_responses"]
    assert metrics["outcomes"] == {"abstained": 1}
    assert metrics["delivery"] == {"generated": 1}



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


@pytest.mark.anyio
async def test_reranker_abstains_before_model_without_current_card_evidence(monkeypatch):
    def forbidden_settings():
        raise AssertionError("Une carte non prouvée ne doit pas atteindre le reranker")

    monkeypatch.setattr(recommend, "get_settings", forbidden_settings)

    result = await recommend._rank_real_products(
        "casque documenté",
        100,
        [
            {
                "offer_id": 9,
                "name": "Casque sans snapshot canonique",
                "price": 90,
                "currency": "EUR",
                "merchant": "Marchand test",
            }
        ],
        "fr",
    )

    assert result == recommend._synth("casque documenté", 100)


def test_cache_revalidation_rejects_an_expired_real_card():
    cached = {
        "real": True,
        "offers": 1,
        "cards": [
            {
                "offer_id": 1,
                "name": "Produit suivi",
                "merchant": "Marchand test",
                "price": 99,
                "currency": "EUR",
                "buy": True,
                "decision": {
                    "version": 3,
                    "recommendation_scope": "meilleur_prix_observe",
                    "facts": {
                        "item_price": 99,
                        "currency": "EUR",
                        "last_observed_at": "2000-01-01T00:00:00+00:00",
                    },
                    "signals": [
                        {"key": "availability", "status": "positive", "in_stock": True},
                        {"key": "freshness", "status": "positive", "age_hours": 1},
                    ],
                    "price_verdict": {
                        "level": "bon",
                        "basis": "price_history",
                    },
                },
            }
        ],
    }

    assert recommend._revalidate_cached_cards(cached) is False


@pytest.mark.parametrize(
    "cards",
    [
        [{"offer_id": 1, "name": "X", "merchant": "M", "price": 10, "currency": None}],
        [
            {"offer_id": 1, "name": "X", "merchant": "M", "price": 10, "currency": "EUR"},
            {"offer_id": 2, "name": "Y", "merchant": "M", "price": 9, "currency": "GBP"},
        ],
        [{"offer_id": 1, "name": "X", "merchant": "M", "price": float("nan"), "currency": "EUR"}],
    ],
)
def test_cache_revalidation_rejects_unknown_mixed_or_invalid_money(cards):
    cached = {"real": True, "offers": len(cards), "cards": cards}

    assert recommend._revalidate_cached_cards(cached) is False
