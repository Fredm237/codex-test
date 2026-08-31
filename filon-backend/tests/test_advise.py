"""Test de bout en bout du scénario cible, sans dépendance externe (mock)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.agents import product_search
from app.agents.orchestrator import advise
from app.schemas.advise import AdviseRequest


@pytest.fixture(autouse=True)
def observed_partner_catalog(monkeypatch):
    """Le test E2E injecte des observations explicites, jamais le catalogue démo."""

    async def search_products(*_args, **_kwargs):
        def product(pid: str, name: str, price: float, relevance: float) -> dict:
            return {
                "product_id": pid,
                "name": name,
                "category": "ordinateur_portable",
                "tags": ["étudiant", "bureautique", "ssd"],
                "specs": {"ram": "16 Go"},
                "rating": 4.2,
                "reviews_count": 10,
                "relevance": relevance,
                "offers": [
                    {
                        "merchant": "Marchand partenaire",
                        "price": price,
                        "currency": "EUR",
                        "observed_at": datetime.now(UTC),
                        "delivery_days": None,
                        "delivery_cost": None,
                        "warranty_months": None,
                        "in_stock": True,
                        "affiliate_network": "Awin",
                    }
                ],
                "price_history": {
                    "average_90d": price + 50,
                    "min_90d": price,
                    "max_90d": price + 100,
                },
                "cashback": [{"platform": "Partenaire cashback", "rate_percent": 2.0}],
                "promos": [],
                "pros": ["Observation de test"],
                "cons": [],
            }

        return [
            product("observed-laptop-a", "Portable étudiant A", 649.0, 0.95),
            product("observed-laptop-b", "Portable étudiant B", 749.0, 0.90),
        ]

    monkeypatch.setattr(product_search, "search_products", search_products)


@pytest.mark.asyncio
async def test_student_laptop_under_900():
    req = AdviseRequest(
        query="Je cherche un ordinateur portable pour étudiant à moins de 900€"
    )
    res = await advise(req)

    # Le besoin a été compris.
    assert res.criteria.category == "ordinateur_portable"
    assert res.criteria.budget_max == 900.0

    # Une recommandation argumentée est produite.
    assert res.recommendation is not None
    reco = res.recommendation
    assert reco.product.real_price <= 900.0
    assert reco.verdict in {"acheter", "attendre"}
    assert reco.reasons, "la recommandation doit être argumentée"

    # Le prix réel intègre cashback/promo → inférieur à l'offre brute.
    assert reco.product.real_price <= reco.product.best_offer.price
    assert reco.product.shipping_cost_known is False
    assert "hors frais de livraison non renseignés" in reco.headline

    # Le gaming (hors budget/usage) ne doit pas gagner.
    assert "tuf" not in reco.product.product_id

    # Des alternatives sont proposées.
    assert len(res.alternatives) >= 1


@pytest.mark.asyncio
async def test_trace_lists_all_agents():
    res = await advise(AdviseRequest(query="portable étudiant 900€"))
    joined = " ".join(res.trace)
    for agent in ["comprehension", "product_search", "price_compare",
                  "cashback", "promo", "price_history", "reviews", "decision"]:
        assert agent in joined
