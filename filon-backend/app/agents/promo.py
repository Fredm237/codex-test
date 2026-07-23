"""Agent 5 — Promotions.

Retient le meilleur code promo applicable (le plus avantageux) pour chaque
produit. En Phase 3, branché sur une base de codes vérifiés.
"""

from __future__ import annotations

from app.agents.state import AdviseState


async def run(state: AdviseState) -> AdviseState:
    enriched = state.setdefault("enriched", {})
    for product in state.get("candidates", []):
        pid = product["product_id"]
        promos = product.get("promos", [])
        best = max(promos, key=lambda p: p["amount"]) if promos else None
        enriched[pid]["promo"] = best
    state.setdefault("trace", []).append("promo: meilleurs codes retenus")
    return state
