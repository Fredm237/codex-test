"""Cas adversariaux du contrat de preuve du Decision Service."""

from __future__ import annotations

import math
from datetime import datetime, timedelta

import pytest

from app.services.decision import compute_decision
from app.services.verdict import _money, compute_verdict


NOW = datetime(2026, 8, 29, 12, 0)


def _trend(*, current: float = 80.0) -> list[tuple[float, datetime]]:
    prices = [100.0, 98.0, 95.0, 92.0, 90.0, 88.0, 85.0, current]
    return [
        (price, NOW - timedelta(days=len(prices) - 1 - index))
        for index, price in enumerate(prices)
    ]


def _decision(**overrides):
    arguments = {
        "price": 80.0,
        "currency": "EUR",
        "history": _trend(),
        "history_currency": "EUR",
        "cheapest_elsewhere": 80.0,
        "comparison_currency": "EUR",
        "merchants_count": 3,
        "offers_count": 3,
        "in_stock": True,
        "now": NOW,
    }
    arguments.update(overrides)
    return compute_decision(**arguments)


def _assert_no_favourable_claim(result: dict) -> None:
    assert result["recommendation_scope"] != "meilleur_prix_observe"
    assert result["price_verdict"]["level"] not in {"bon", "excellent"}
    assert result["confidence"] == "not_calibrated"
    assert result["price_verdict"]["confidence"] == "not_calibrated"
    assert not any(
        signal.get("status") == "positive"
        and signal.get("key") in {"comparison", "price_moment", "comparison_strength"}
        for signal in result["signals"]
    )


@pytest.mark.parametrize(
    "price",
    [None, 0.0, -1.0, math.nan, math.inf, -math.inf, True],
)
def test_invalid_price_is_never_recommended(price):
    result = _decision(price=price)
    assert result["recommendation_scope"] == "non_recommandee"
    assert result["facts"]["item_price"] is None
    _assert_no_favourable_claim(result)


@pytest.mark.parametrize("currency", [None, "", "unknown", "XXX", "XTS", 123])
def test_absent_or_invalid_currency_forces_verification(currency):
    result = _decision(currency=currency)
    assert result["recommendation_scope"] == "a_verifier"
    assert result["facts"]["currency"] is None
    assert "currency" in result["missing"]
    _assert_no_favourable_claim(result)


@pytest.mark.parametrize("in_stock", [None, 1, 0, "true", object()])
def test_only_literal_true_is_a_confirmed_stock(in_stock):
    result = _decision(in_stock=in_stock)
    assert result["recommendation_scope"] == "a_verifier"
    assert "availability" in result["missing"]
    _assert_no_favourable_claim(result)


def test_literal_false_is_explicitly_non_recommended():
    result = _decision(in_stock=False)
    assert result["recommendation_scope"] == "non_recommandee"
    _assert_no_favourable_claim(result)


@pytest.mark.parametrize(
    ("history", "expected_reason"),
    [
        ([], "missing"),
        ([(80.0, NOW + timedelta(microseconds=1))], "future"),
        (_trend() + [(999.0, NOW + timedelta(microseconds=1))], "future"),
        ([(80.0, NOW - timedelta(hours=72, microseconds=1))], "stale"),
        ([(79.0, NOW)], "missing"),
    ],
)
def test_missing_future_stale_or_non_matching_observation_forces_verification(
    history, expected_reason
):
    result = _decision(history=history)
    freshness = next(signal for signal in result["signals"] if signal["key"] == "freshness")
    assert freshness["reason"] == expected_reason
    assert result["recommendation_scope"] == "a_verifier"
    assert "data_freshness" in result["missing"]
    _assert_no_favourable_claim(result)


def test_exact_ttl_boundary_remains_admissible():
    result = _decision(history=[(80.0, NOW - timedelta(hours=72))])
    freshness = next(signal for signal in result["signals"] if signal["key"] == "freshness")
    assert freshness == {
        "key": "freshness",
        "status": "positive",
        "age_hours": 72,
        "reason": "fresh",
    }
    assert result["recommendation_scope"] == "meilleur_prix_observe"


@pytest.mark.parametrize("history_currency", [None, "", "GBP", "XXX"])
def test_history_without_same_currency_proof_cannot_create_a_price_moment(
    history_currency
):
    result = _decision(
        history_currency=history_currency,
        cheapest_elsewhere=70.0,
    )
    assert result["price_verdict"]["level"] == "insuffisant"
    assert result["price_verdict"]["basis"] == "insufficient"
    assert result["recommendation_scope"] == "a_verifier"
    assert not any(
        signal.get("key") == "price_moment"
        and signal.get("level") in {"bon", "excellent"}
        for signal in result["signals"]
    )
    assert "history_currency" in result["missing"]


@pytest.mark.parametrize(
    ("cheapest_elsewhere", "comparison_currency"),
    [
        (80.0, "GBP"),
        (80.0, None),
        (80.0, "XXX"),
        (0.0, "EUR"),
        (-1.0, "EUR"),
        (math.nan, "EUR"),
        (math.inf, "EUR"),
    ],
)
def test_unproven_comparison_never_creates_a_best_price_scope(
    cheapest_elsewhere, comparison_currency
):
    result = _decision(
        cheapest_elsewhere=cheapest_elsewhere,
        comparison_currency=comparison_currency,
    )
    assert result["recommendation_scope"] != "meilleur_prix_observe"
    comparison = next(signal for signal in result["signals"] if signal["key"] == "comparison")
    assert comparison["status"] == "unknown"
    assert "comparison_scope" in result["missing"]


def test_verdict_itself_abstains_without_history_currency_proof():
    result = compute_verdict(
        price=80.0,
        currency="EUR",
        history=_trend(),
        history_currency=None,
        in_stock=True,
        now=NOW,
    )
    assert result["level"] == "insuffisant"
    assert result["confidence"] == "not_calibrated"


@pytest.mark.parametrize("currency", [None, "", "unknown", "XXX"])
def test_money_never_defaults_an_unknown_currency_to_euro(currency):
    rendered = _money(42.0, currency)
    assert "€" not in rendered
    assert "devise inconnue" in rendered


def test_money_uses_the_iso_code_when_no_symbol_is_defined():
    assert _money(42.0, "JPY").endswith(" JPY")
