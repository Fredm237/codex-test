"""Agent 8 — Décision (agent principal).

Combine toutes les informations : calcule le prix réel (offre - cashback -
promo), l'économie face au marché, classe les produits et désigne le meilleur
choix avec une recommandation argumentée.
"""

from __future__ import annotations

from app.agents.state import AdviseState


def _real_price(e: dict) -> float:
    price = e["best_offer"]["price"] + e["best_offer"].get("delivery_cost", 0.0)
    if e.get("cashback"):
        price -= e["cashback"]["amount"]
    if e.get("promo"):
        price -= e["promo"]["amount"]
    return round(price, 2)


def _build_analysis(product: dict, e: dict) -> dict:
    real = _real_price(e)
    market_avg = e.get("market_avg", e["best_offer"]["price"])
    return {
        "product_id": product["product_id"],
        "name": product["name"],
        "specs": product.get("specs", {}),
        "best_offer": e["best_offer"],
        "cashback": e.get("cashback"),
        "promo": e.get("promo"),
        "history": e.get("history"),
        "reviews": e.get("reviews"),
        "real_price": real,
        "savings_vs_market": round(market_avg - real, 2),
    }


def _rank_key(a: dict) -> tuple:
    rating = (a.get("reviews") or {}).get("rating", 0.0)
    # Prix réel croissant d'abord, puis meilleure note.
    return (a["real_price"], -rating)


async def run(state: AdviseState) -> AdviseState:
    enriched = state.get("enriched", {})
    analyses = [
        _build_analysis(p, enriched[p["product_id"]])
        for p in state.get("candidates", [])
        if p["product_id"] in enriched
    ]
    analyses.sort(key=_rank_key)
    state["analyses"] = analyses

    if not analyses:
        state["recommendation"] = None
        state.setdefault("trace", []).append("decision: aucun produit éligible")
        return state

    best = analyses[0]
    reasons: list[str] = []

    if len(analyses) > 1:
        gap = round(analyses[1]["real_price"] - best["real_price"])
        if gap > 0:
            reasons.append(f"{gap} € de moins que l'alternative la plus proche.")
    if best.get("history"):
        reasons.append(best["history"]["reason"])
    if best.get("cashback"):
        cb = best["cashback"]
        reasons.append(f"Cashback {cb['rate_percent']}% via {cb['platform']} ({cb['amount']} €).")
    if best.get("promo"):
        reasons.append(f"Code {best['promo']['code']} : -{best['promo']['amount']} €.")
    if best.get("reviews") and best["reviews"]["pros"]:
        reasons.append(best["reviews"]["pros"][0] + ".")

    verdict = (best.get("history") or {}).get("buy_signal", "acheter")
    headline = (
        f"{best['name']} à {best['real_price']} € tout compris"
        + (" : c'est le moment d'acheter." if verdict == "acheter" else " : à surveiller, mieux vaut attendre.")
    )

    state["recommendation"] = {
        "product": best,
        "verdict": verdict,
        "headline": headline,
        "reasons": reasons,
    }
    state.setdefault("trace", []).append(f"decision: gagnant={best['product_id']} verdict={verdict}")
    return state
