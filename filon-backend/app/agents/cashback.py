"""Agent 4 — Cashback.

Choisit la plateforme de cashback la plus rémunératrice pour la meilleure
offre du produit et calcule le montant récupéré.
"""

from __future__ import annotations

from app.agents.state import AdviseState


async def run(state: AdviseState) -> AdviseState:
    enriched = state.setdefault("enriched", {})
    for product in state.get("candidates", []):
        pid = product["product_id"]
        platforms = product.get("cashback", [])
        best = None
        if platforms:
            price = enriched[pid]["best_offer"]["price"]
            best_platform = max(platforms, key=lambda c: c["rate_percent"])
            best = {
                "platform": best_platform["platform"],
                "rate_percent": best_platform["rate_percent"],
                "amount": round(price * best_platform["rate_percent"] / 100, 2),
            }
        enriched[pid]["cashback"] = best
    state.setdefault("trace", []).append("cashback: meilleures plateformes calculées")
    return state
