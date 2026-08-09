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
    # `rating` peut être absent OU explicitement None : les flux Awin ne
    # fournissent aucune note (voir catalog_source._shape). `.get(k, 0.0)` ne
    # protège que de la clé manquante, pas d'une valeur None présente, d'où le
    # `or 0.0` qui couvre les deux cas avant l'inversion de signe.
    rating = (a.get("reviews") or {}).get("rating") or 0.0
    # Prix réel croissant d'abord, puis meilleure note.
    return (a["real_price"], -float(rating))


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
    # `pros` peut manquer ou être nul selon la source de données : on lit sans
    # supposer la présence de la clé, sinon un KeyError fait tomber la requête.
    pros = (best.get("reviews") or {}).get("pros") or []
    if pros:
        reasons.append(str(pros[0]).rstrip(".") + ".")

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
