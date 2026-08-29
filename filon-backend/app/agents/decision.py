"""Agent 8 — Décision (agent principal).

Combine toutes les informations : calcule le prix réel (offre - cashback -
promo), l'économie face au marché, classe les produits et désigne le meilleur
choix avec une recommandation argumentée.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from numbers import Real

from app.agents.state import AdviseState


def _finite_number(value: object, *, positive: bool) -> float | None:
    if isinstance(value, bool) or not isinstance(value, Real):
        return None
    numeric = float(value)
    if not math.isfinite(numeric):
        return None
    violates_bound = numeric <= 0 if positive else numeric < 0
    if violates_bound:
        return None
    return numeric


def _price_components(
    e: dict,
) -> tuple[float, bool, Mapping | None, Mapping | None] | None:
    """Valide le total et les remises avant toute affirmation monétaire."""

    offer = e.get("best_offer")
    if not isinstance(offer, Mapping):
        return None
    item_price = _finite_number(offer.get("price"), positive=True)
    if item_price is None:
        return None
    delivery_raw = offer.get("delivery_cost")
    shipping_known = delivery_raw is not None
    delivery = 0.0
    if shipping_known:
        validated_delivery = _finite_number(delivery_raw, positive=False)
        if validated_delivery is None:
            return None
        delivery = validated_delivery
    base = item_price + delivery
    if not math.isfinite(base):
        return None

    def validated_discount(key: str) -> tuple[Mapping | None, float]:
        candidate = e.get(key)
        if not isinstance(candidate, Mapping):
            return None, 0.0
        amount = _finite_number(candidate.get("amount"), positive=True)
        if amount is None or amount > base:
            return None, 0.0
        if key == "cashback":
            rate = _finite_number(candidate.get("rate_percent"), positive=True)
            if (
                rate is None
                or rate > 100
                or not math.isclose(
                    amount,
                    round(item_price * rate / 100, 2),
                    abs_tol=0.01,
                )
            ):
                return None, 0.0
        return candidate, amount

    cashback, cashback_amount = validated_discount("cashback")
    promo, promo_amount = validated_discount("promo")
    if cashback is not None and promo is not None:
        combined = cashback_amount + promo_amount
        explicitly_stackable = promo.get("stackable") is True
        if not explicitly_stackable or not math.isfinite(combined) or combined > base:
            # Sans preuve explicite de cumul, n'appliquer qu'un avantage. Cela
            # évite de présenter un prix accessible uniquement par une
            # combinaison peut-être impossible.
            if cashback_amount >= promo_amount:
                promo, promo_amount = None, 0.0
            else:
                cashback, cashback_amount = None, 0.0
    discount_total = cashback_amount + promo_amount
    return round(base - discount_total, 2), shipping_known, cashback, promo


def _real_price(e: dict) -> float:
    components = _price_components(e)
    if components is None:
        raise ValueError("invalid or non-finite offer price components")
    return components[0]


def _build_analysis(product: dict, e: dict) -> dict | None:
    components = _price_components(e)
    if components is None:
        return None
    real, shipping_known, cashback, promo = components
    comparison_complete = bool(e.get("price_comparison_complete"))
    market_avg = (
        _finite_number(e.get("market_avg"), positive=True)
        if comparison_complete
        else None
    )
    comparison_complete = comparison_complete and market_avg is not None
    return {
        "product_id": product["product_id"],
        "name": product["name"],
        "relevance": product.get("relevance", 0.0),
        "specs": product.get("specs", {}),
        "best_offer": e["best_offer"],
        "cashback": cashback,
        "promo": promo,
        "history": e.get("history"),
        "reviews": e.get("reviews"),
        "real_price": real,
        "shipping_cost_known": shipping_known,
        "price_comparison_complete": comparison_complete,
        "savings_vs_market": (
            round(market_avg - real, 2) if market_avg is not None else None
        ),
    }


def _rank_key(a: dict) -> tuple:
    # `rating` peut être absent OU explicitement None : les flux Awin ne
    # fournissent aucune note (voir catalog_source._shape). `.get(k, 0.0)` ne
    # protège que de la clé manquante, pas d'une valeur None présente, d'où le
    # `or 0.0` qui couvre les deux cas avant l'inversion de signe.
    rating = (a.get("reviews") or {}).get("rating") or 0.0
    # La pertinence prime sur le prix.
    #
    # Le tri portait d'abord sur le prix réel croissant. Comme les candidats
    # pouvaient ne correspondre que par un mot, c'était toujours l'article le
    # moins cher du lot qui gagnait : une carte cadeau à 0,01 € plutôt qu'un
    # casque. Un résultat hors sujet ne devient pas bon parce qu'il est bon
    # marché — la correspondance passe donc devant, et le prix départage à
    # pertinence comparable.
    pertinence = float(a.get("relevance") or 0.0)
    # Arrondi au dixième : deux offres également pertinentes se départagent au
    # prix, sans qu'un écart de score négligeable ne l'emporte.
    return (
        -round(pertinence, 1),
        not bool(a.get("shipping_cost_known")),
        a["real_price"],
        -float(rating),
    )


async def run(state: AdviseState) -> AdviseState:
    enriched = state.get("enriched", {})
    criteria = state.get("criteria")
    raw_budget = (
        criteria.get("budget_max")
        if isinstance(criteria, Mapping)
        else getattr(criteria, "budget_max", None)
    )
    budget = (
        _finite_number(raw_budget, positive=True)
        if raw_budget is not None
        else None
    )
    analyses = []
    for product in state.get("candidates", []):
        entry = enriched.get(product["product_id"], {})
        if "best_offer" not in entry:
            continue
        analysis = _build_analysis(product, entry)
        if analysis is None:
            continue
        # Le budget est une contrainte dure sur tout montant actuellement
        # calculable. Une livraison inconnue reste affichée comme telle, mais
        # un sous-total déjà hors budget ne peut jamais être recommandé.
        if raw_budget is not None and (
            budget is None or analysis["real_price"] > budget
        ):
            continue
        analyses.append(analysis)
    analyses.sort(key=_rank_key)
    state["analyses"] = analyses

    if not analyses:
        state["recommendation"] = None
        state.setdefault("trace", []).append("decision: aucun produit éligible")
        return state

    best = analyses[0]
    reasons: list[str] = []

    if (
        len(analyses) > 1
        and best.get("shipping_cost_known")
        and analyses[1].get("shipping_cost_known")
    ):
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

    # Sans historique, FILON ne transforme pas l'absence de signal en conseil
    # d'achat positif. Le contrat v1 ne porte pas encore `abstain`, donc
    # `attendre` est le repli conservateur compatible.
    verdict = (best.get("history") or {}).get("buy_signal", "attendre")
    if best.get("shipping_cost_known"):
        price_label = f"{best['real_price']} € livraison incluse"
    else:
        price_label = (
            f"{best['real_price']} € hors frais de livraison non renseignés"
        )
    headline = f"{best['name']} à {price_label}" + (
        " : c'est le moment d'acheter."
        if verdict == "acheter"
        else " : à surveiller, mieux vaut attendre."
    )

    state["recommendation"] = {
        "product": best,
        "verdict": verdict,
        "headline": headline,
        "reasons": reasons,
    }
    state.setdefault("trace", []).append(f"decision: gagnant={best['product_id']} verdict={verdict}")
    return state
