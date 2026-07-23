"""Test de bout en bout du scénario cible, sans dépendance externe (mock)."""

from __future__ import annotations

import pytest

from app.agents.orchestrator import advise
from app.schemas.advise import AdviseRequest


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
