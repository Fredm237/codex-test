"""Agent 3 — Comparaison des offres dont les coûts sont comparables.

Un total livré n'existe que si son prix et ses frais de livraison sont tous
deux observés. Sinon l'offre peut rester visible avec son prix article, mais ne
peut ni gagner contre un total connu ni produire une économie comparative.
"""

from __future__ import annotations

import math
from numbers import Real

from app.agents.state import AdviseState
from app.services.freshness import offer_observation_is_fresh


def _item_price(offer: dict) -> float | None:
    price = offer.get("price")
    if isinstance(price, bool) or not isinstance(price, Real):
        return None
    numeric = float(price)
    return numeric if math.isfinite(numeric) and numeric > 0 else None


def _delivered_total(offer: dict) -> float | None:
    """Retourne un total uniquement lorsque prix et livraison sont observés."""

    price = _item_price(offer)
    delivery_cost = offer.get("delivery_cost")
    if price is None or isinstance(delivery_cost, bool) or not isinstance(
        delivery_cost, Real
    ):
        return None
    numeric_delivery = float(delivery_cost)
    if not math.isfinite(numeric_delivery) or numeric_delivery < 0:
        return None
    total = price + numeric_delivery
    return total if math.isfinite(total) else None


async def run(state: AdviseState) -> AdviseState:
    enriched = state.setdefault("enriched", {})
    compared = 0
    incomplete = 0
    for product in state.get("candidates", []):
        pid = product["product_id"]
        entry = enriched.setdefault(pid, {})
        # Fail closed : stock, prix et devise doivent être explicitement
        # observés. Le contrat public exprime les budgets en euros et ne dispose
        # encore d'aucun moteur de conversion de devises.
        stocked = [o for o in product["offers"] if o.get("in_stock") is True]
        fresh_stocked = [
            offer
            for offer in stocked
            if offer_observation_is_fresh(offer.get("observed_at"))
        ]
        priced_offers = [
            offer
            for offer in fresh_stocked
            if _item_price(offer) is not None
            and offer.get("currency") == "EUR"
        ]
        offers = [
            offer
            for offer in priced_offers
            if (
                offer.get("delivery_cost") is None
                or _delivered_total(offer) is not None
            )
        ]
        if not offers:
            entry["eligibility"] = (
                "availability_unknown_or_unavailable"
                if not stocked
                else (
                    "stale_or_unobserved"
                    if not fresh_stocked
                    else (
                        "price_or_currency_unknown"
                        if not priced_offers
                        else "delivery_cost_invalid"
                    )
                )
            )
            continue

        comparable = [
            (total, offer)
            for offer in offers
            if (total := _delivered_total(offer)) is not None
        ]
        comparison_complete = len(comparable) == len(offers)
        if comparable:
            _, best = min(comparable, key=lambda item: item[0])
            comparison_basis = (
                "delivered_total"
                if comparison_complete
                else "known_delivered_total_only"
            )
        else:
            best = min(offers, key=lambda offer: _item_price(offer) or math.inf)
            comparison_basis = "item_price_only"

        market_avg = None
        if comparison_complete:
            # Diviser avant de sommer évite qu'une somme intermédiaire déborde
            # alors que la moyenne de totaux finis reste elle-même finie.
            market_avg = sum(
                total / len(comparable) for total, _offer in comparable
            )
        entry["best_offer"] = best
        entry["market_avg"] = market_avg
        entry["all_offers"] = offers
        entry["price_comparison_complete"] = comparison_complete
        entry["price_comparison_basis"] = comparison_basis
        entry["eligibility"] = "eligible"
        compared += 1
        incomplete += int(not comparison_complete)
    state.setdefault("trace", []).append(
        "price_compare: "
        f"{compared} produits éligibles, "
        f"{incomplete} comparaisons de total incomplètes"
    )
    return state
