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
        entry = enriched.setdefault(pid, {})
        # Les flux marchands (Awin) ne portent ni note ni nombre d'avis : les
        # champs valent None. Le schéma ReviewSummary attend des non-nuls et le
        # tri de l'agent décision inverse le signe de la note, donc on normalise
        # ici plutôt que de laisser un None se propager dans le graphe.
        entry["reviews"] = {
            "count": product.get("reviews_count") or 0,
            "rating": product.get("rating") or 0.0,
            "pros": product.get("pros") or [],
            "cons": product.get("cons") or [],
        }
    state.setdefault("trace", []).append("reviews: synthèses générées")
    return state
