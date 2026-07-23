"""Agent 3 — Comparaison prix.

Pour chaque candidat, retient la meilleure offre marchande en tenant compte
du prix, des frais et délais de livraison, et de la garantie.
"""

from __future__ import annotations

from app.agents.state import AdviseState


def _effective(offer: dict) -> float:
    return offer["price"] + offer.get("delivery_cost", 0.0)


async def run(state: AdviseState) -> AdviseState:
    enriched = state.setdefault("enriched", {})
    for product in state.get("candidates", []):
        offers = [o for o in product["offers"] if o.get("in_stock", True)]
        best = min(offers, key=_effective)
        market_avg = sum(o["price"] for o in offers) / len(offers)
        enriched.setdefault(product["product_id"], {})
        enriched[product["product_id"]]["best_offer"] = best
        enriched[product["product_id"]]["market_avg"] = market_avg
        enriched[product["product_id"]]["all_offers"] = offers
    state.setdefault("trace", []).append(
        f"price_compare: meilleures offres pour {len(state.get('candidates', []))} produits"
    )
    return state
