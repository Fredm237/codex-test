"""Agent 6 — Historique prix.

Compare le prix actuel à l'historique 90 jours pour produire un signal
d'achat : acheter maintenant ou attendre.
"""

from __future__ import annotations

from app.agents.state import AdviseState


async def run(state: AdviseState) -> AdviseState:
    enriched = state.setdefault("enriched", {})
    for product in state.get("candidates", []):
        pid = product["product_id"]
        hist = product.get("price_history")
        if not hist:
            enriched[pid]["history"] = None
            continue
        current = enriched[pid]["best_offer"]["price"]
        avg = hist["average_90d"]
        low = hist["min_90d"]

        if current <= low * 1.02:
            trend, signal, reason = ("baisse", "acheter", "Prix au plus bas des 90 derniers jours.")
        elif current < avg:
            trend, signal, reason = ("baisse", "acheter", f"{round(avg - current)} € sous la moyenne 90 j.")
        elif current > avg * 1.05:
            trend, signal, reason = ("hausse", "attendre", "Au-dessus de la moyenne, une baisse est probable.")
        else:
            trend, signal, reason = ("stable", "acheter", "Prix stable, proche de la moyenne.")

        enriched[pid]["history"] = {
            "current": current,
            "average_90d": avg,
            "min_90d": low,
            "max_90d": hist["max_90d"],
            "trend": trend,
            "buy_signal": signal,
            "reason": reason,
        }
    state.setdefault("trace", []).append("price_history: signaux d'achat calculés")
    return state
