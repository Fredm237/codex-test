"""Invariants de prix : un inconnu ne devient jamais zéro pour gagner."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.agents import decision, price_compare
from app.schemas.advise import Criteria


def _offer(
    merchant: str,
    price: float,
    *,
    delivery_cost: float | None,
    currency: str | None = "EUR",
) -> dict:
    return {
        "merchant": merchant,
        "price": price,
        "currency": currency,
        "observed_at": datetime.now(UTC),
        "delivery_cost": delivery_cost,
        "in_stock": True,
    }


@pytest.mark.asyncio
async def test_livraison_inconnue_ne_bat_pas_un_total_connu():
    state = {
        "candidates": [
            {
                "product_id": "p1",
                "offers": [
                    _offer("inconnu", 100.0, delivery_cost=None),
                    _offer("connu", 101.0, delivery_cost=1.0),
                ],
            }
        ]
    }

    result = await price_compare.run(state)
    entry = result["enriched"]["p1"]

    assert entry["best_offer"]["merchant"] == "connu"
    assert entry["price_comparison_basis"] == "known_delivered_total_only"
    assert entry["price_comparison_complete"] is False
    assert entry["market_avg"] is None


@pytest.mark.asyncio
async def test_offres_toutes_inconnues_restent_item_price_only_sans_economie():
    state = {
        "candidates": [
            {
                "product_id": "p1",
                "name": "Produit",
                "relevance": 1.0,
                "offers": [
                    _offer("a", 100.0, delivery_cost=None),
                    _offer("b", 101.0, delivery_cost=None),
                ],
            }
        ],
        "trace": [],
    }

    compared = await price_compare.run(state)
    decided = await decision.run(compared)
    analysis = decided["analyses"][0]

    assert analysis["best_offer"]["merchant"] == "a"
    assert analysis["shipping_cost_known"] is False
    assert analysis["price_comparison_complete"] is False
    assert analysis["savings_vs_market"] is None
    assert "hors frais de livraison non renseignés" in decided[
        "recommendation"
    ]["headline"]


@pytest.mark.asyncio
async def test_totaux_tous_connus_autorisent_une_comparaison_complete():
    state = {
        "candidates": [
            {
                "product_id": "p1",
                "name": "Produit",
                "relevance": 1.0,
                "offers": [
                    _offer("a", 100.0, delivery_cost=5.0),
                    _offer("b", 102.0, delivery_cost=1.0),
                ],
            }
        ],
        "trace": [],
    }

    compared = await price_compare.run(state)
    decided = await decision.run(compared)
    analysis = decided["analyses"][0]

    assert analysis["best_offer"]["merchant"] == "b"
    assert analysis["real_price"] == 103.0
    assert analysis["price_comparison_complete"] is True
    assert analysis["savings_vs_market"] == 1.0


@pytest.mark.asyncio
async def test_devise_inconnue_n_est_pas_eligible_a_un_total_en_euros():
    state = {
        "candidates": [
            {
                "product_id": "p1",
                "offers": [
                    _offer("sans-devise", 100.0, delivery_cost=0.0, currency=None)
                ],
            }
        ]
    }

    result = await price_compare.run(state)
    entry = result["enriched"]["p1"]

    assert "best_offer" not in entry
    assert entry["eligibility"] == "price_or_currency_unknown"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "observed_at",
    [None, datetime.now(UTC) - timedelta(hours=73)],
)
async def test_offre_non_datee_ou_expiree_ne_peut_pas_etre_recommandee(
    observed_at,
):
    stale = _offer("stale", 100.0, delivery_cost=None)
    stale["observed_at"] = observed_at
    state = {
        "candidates": [
            {
                "product_id": "p1",
                "offers": [stale],
            }
        ],
        "trace": [],
    }

    compared = await price_compare.run(state)
    decided = await decision.run(compared)

    assert compared["enriched"]["p1"]["eligibility"] == "stale_or_unobserved"
    assert decided["recommendation"] is None


@pytest.mark.asyncio
async def test_total_livre_non_fini_est_exclu_fail_closed():
    state = {
        "candidates": [
            {
                "product_id": "p1",
                "offers": [
                    _offer("overflow", 1e308, delivery_cost=1e308),
                ],
            }
        ]
    }

    result = await price_compare.run(state)
    entry = result["enriched"]["p1"]

    assert "best_offer" not in entry
    assert entry["eligibility"] == "delivery_cost_invalid"


@pytest.mark.asyncio
@pytest.mark.parametrize("delivery_cost", [-1.0, float("nan"), True, "5"])
async def test_livraison_invalide_ne_devient_jamais_un_total_connu(delivery_cost):
    state = {
        "candidates": [
            {
                "product_id": "p1",
                "offers": [
                    _offer("invalid", 100.0, delivery_cost=delivery_cost),
                ],
            }
        ],
        "trace": [],
    }

    compared = await price_compare.run(state)
    decided = await decision.run(compared)

    assert "best_offer" not in compared["enriched"]["p1"]
    assert decided["recommendation"] is None


@pytest.mark.asyncio
async def test_remises_superieures_au_total_ne_produisent_pas_un_prix_negatif():
    state = {
        "candidates": [
            {"product_id": "p1", "name": "Produit", "relevance": 1.0},
        ],
        "enriched": {
            "p1": {
                "best_offer": _offer("a", 100.0, delivery_cost=0.0),
                "cashback": {
                    "platform": "test",
                    "rate_percent": 80.0,
                    "amount": 80.0,
                },
                "promo": {
                    "code": "OVER",
                    "description": "test",
                    "amount": 80.0,
                    "stackable": True,
                },
                "price_comparison_complete": True,
                "market_avg": 100.0,
            }
        },
        "trace": [],
    }

    result = await decision.run(state)
    product = result["recommendation"]["product"]

    assert product["real_price"] == 20.0
    assert product["cashback"]["amount"] == 80.0
    assert product["promo"] is None
    assert any("Cashback" in reason for reason in result["recommendation"]["reasons"])
    assert not any("Code" in reason for reason in result["recommendation"]["reasons"])


@pytest.mark.asyncio
async def test_cashback_et_promo_non_stackable_ne_sont_pas_cumules():
    state = {
        "candidates": [
            {"product_id": "p1", "name": "Produit", "relevance": 1.0},
        ],
        "enriched": {
            "p1": {
                "best_offer": _offer("a", 100.0, delivery_cost=0.0),
                "cashback": {
                    "platform": "test",
                    "rate_percent": 10.0,
                    "amount": 10.0,
                },
                "promo": {
                    "code": "TEN",
                    "description": "test",
                    "amount": 15.0,
                    "stackable": False,
                },
                "price_comparison_complete": True,
                "market_avg": 100.0,
            }
        },
        "trace": [],
    }

    result = await decision.run(state)
    product = result["recommendation"]["product"]

    assert product["real_price"] == 85.0
    assert product["cashback"] is None
    assert product["promo"]["code"] == "TEN"
    assert not any("Cashback" in reason for reason in result["recommendation"]["reasons"])
    assert any("Code TEN" in reason for reason in result["recommendation"]["reasons"])


def test_ranking_prefere_un_total_connu_a_pertinence_egale():
    unknown = {
        "real_price": 10.0,
        "relevance": 0.9,
        "shipping_cost_known": False,
    }
    known = {
        "real_price": 11.0,
        "relevance": 0.9,
        "shipping_cost_known": True,
    }

    assert sorted([unknown, known], key=decision._rank_key)[0] is known


@pytest.mark.asyncio
async def test_ecart_en_euros_absent_si_une_alternative_a_livraison_inconnue():
    state = {
        "candidates": [
            {"product_id": "known", "name": "Connu", "relevance": 1.0},
            {"product_id": "unknown", "name": "Inconnu", "relevance": 0.9},
        ],
        "enriched": {
            "known": {
                "best_offer": _offer("a", 100.0, delivery_cost=0.0),
                "price_comparison_complete": True,
                "market_avg": 100.0,
            },
            "unknown": {
                "best_offer": _offer("b", 90.0, delivery_cost=None),
                "price_comparison_complete": False,
                "market_avg": None,
            },
        },
        "trace": [],
    }

    result = await decision.run(state)

    assert result["recommendation"]["product"]["product_id"] == "known"
    assert not any("€ de moins" in reason for reason in result["recommendation"]["reasons"])


@pytest.mark.asyncio
async def test_total_livre_hors_budget_ne_gagne_pas_sur_un_sous_total_eligible():
    state = {
        "criteria": Criteria(budget_max=100.0),
        "candidates": [
            {"product_id": "known", "name": "Connu", "relevance": 1.0},
            {"product_id": "unknown", "name": "Inconnu", "relevance": 1.0},
        ],
        "enriched": {
            "known": {
                "best_offer": _offer("a", 90.0, delivery_cost=100.0),
                "price_comparison_complete": True,
                "market_avg": 190.0,
            },
            "unknown": {
                "best_offer": _offer("b", 95.0, delivery_cost=None),
                "price_comparison_complete": False,
                "market_avg": None,
            },
        },
        "trace": [],
    }

    result = await decision.run(state)

    assert result["recommendation"]["product"]["product_id"] == "unknown"
    assert "hors frais de livraison non renseignés" in result[
        "recommendation"
    ]["headline"]
