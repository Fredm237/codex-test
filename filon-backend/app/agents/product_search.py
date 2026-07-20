"""Agent 2 — Recherche produit.

Sélectionne, dans les sources disponibles (ici le catalogue de démo), les
produits qui correspondent aux critères. Un score simple classe la pertinence.
"""

from __future__ import annotations

from app.agents.state import AdviseState
from app.data.catalog import all_products


def _score(product: dict, criteria) -> float:
    score = 0.0
    tags = set(product.get("tags", []))
    for u in criteria.usage:
        if u in tags:
            score += 1.0
    for m in criteria.must_have:
        if m in tags:
            score += 1.5
    if criteria.category and product.get("category") == criteria.category:
        score += 3.0
    for k in criteria.keywords:
        if k in tags:
            score += 0.3
    return score


async def run(state: AdviseState) -> AdviseState:
    criteria = state["criteria"]
    products = all_products()

    if criteria.category:
        products = [p for p in products if p.get("category") == criteria.category]

    # Filtre budget : on garde ceux dont la meilleure offre tient dans le budget.
    if criteria.budget_max:
        products = [
            p
            for p in products
            if min(o["price"] for o in p["offers"]) <= criteria.budget_max * 1.05
        ]

    ranked = sorted(products, key=lambda p: _score(p, criteria), reverse=True)
    state["candidates"] = ranked[:5]
    state.setdefault("trace", []).append(
        f"product_search: {len(ranked)} produits retenus"
    )
    return state
