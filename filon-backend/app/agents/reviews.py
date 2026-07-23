"""Agent 7 — Avis IA.

Synthétise les avis (note, points forts, points faibles). Ici à partir des
métadonnées du catalogue ; en production, résumé LLM de milliers d'avis.
"""

from __future__ import annotations

from app.agents.state import AdviseState


async def run(state: AdviseState) -> AdviseState:
    enriched = state.setdefault("enriched", {})
    for product in state.get("candidates", []):
        pid = product["product_id"]
        enriched[pid]["reviews"] = {
            "count": product.get("reviews_count", 0),
            "rating": product.get("rating", 0.0),
            "pros": product.get("pros", []),
            "cons": product.get("cons", []),
        }
    state.setdefault("trace", []).append("reviews: synthèses générées")
    return state
