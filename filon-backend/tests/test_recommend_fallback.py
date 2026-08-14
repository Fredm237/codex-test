"""Le repli assistant doit rester une absence vérifiée, jamais une synthèse commerciale."""

import pytest

from app.services import catalog_search, recommend


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
