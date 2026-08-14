"""Tests du socle de décision FILON.

La propriété critique n'est pas le calcul d'une note : c'est l'affichage explicite
quand livraison, retours, stock ou historique ne sont pas connus.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from app.services.decision import compute_decision

BASE = datetime(2026, 8, 1, 12, 0)


def _history(prices: list[float]):
    return [(price, BASE + timedelta(days=index)) for index, price in enumerate(prices)]


def test_best_observed_price_keeps_delivery_unknown_visible():
    d = compute_decision(
        price=80.0,
        currency="EUR",
        history=_history([100, 98, 95, 92, 90, 88, 85, 80]),
        cheapest_elsewhere=80.0,
        comparison_currency="EUR",
        merchants_count=5,
        offers_count=8,
        in_stock=True,
        updated_at=BASE + timedelta(days=7),
        now=BASE + timedelta(days=7, hours=2),
    )
    assert d["recommendation_scope"] == "meilleur_prix_observe"
    # Huit jours suffisent pour un verdict exploitable, mais pas pour une
    # confiance élevée : celle-ci exige 30 relevés sur 30 jours.
    assert d["confidence"] == "moyenne"
    assert {"shipping_cost", "delivery_destination", "return_policy"}.issubset(d["missing"])
    assert any(s["key"] == "comparison" and s["is_best_observed"] for s in d["signals"])


def test_stock_absent_is_not_presented_as_in_stock():
    d = compute_decision(
        price=100.0,
        currency="EUR",
        history=[],
        in_stock=None,
        updated_at=BASE,
        now=BASE + timedelta(hours=1),
    )
    assert "availability" in d["missing"]
    availability = next(s for s in d["signals"] if s["key"] == "availability")
    assert availability["status"] == "unknown"
    assert d["confidence"] != "elevee"


def test_cross_currency_is_never_used_for_a_best_price_claim():
    d = compute_decision(
        price=100.0,
        currency="EUR",
        history=[],
        cheapest_elsewhere=90.0,
        comparison_currency="GBP",
        merchants_count=4,
        in_stock=True,
        updated_at=BASE,
        now=BASE + timedelta(hours=1),
    )
    assert d["recommendation_scope"] != "meilleur_prix_observe"
    assert "comparison_scope" in d["missing"]


def test_out_of_stock_offer_is_never_recommended():
    d = compute_decision(
        price=50.0,
        currency="EUR",
        history=_history([60, 58, 55, 52, 50, 50, 50, 50]),
        cheapest_elsewhere=50.0,
        comparison_currency="EUR",
        merchants_count=3,
        in_stock=False,
        updated_at=BASE + timedelta(days=7),
        now=BASE + timedelta(days=7, hours=2),
    )
    assert d["recommendation_scope"] == "non_recommandee"


def test_stale_price_has_a_visible_warning_not_a_hidden_penalty():
    d = compute_decision(
        price=100.0,
        currency="EUR",
        history=[],
        in_stock=True,
        updated_at=BASE,
        now=BASE + timedelta(days=45),
    )
    freshness = next(s for s in d["signals"] if s["key"] == "freshness")
    assert freshness["status"] == "warning"
    assert freshness["age_hours"] == 45 * 24


def test_accommodation_is_an_indicative_rate_not_a_best_price():
    d = compute_decision(
        price=154.0,
        currency="EUR",
        history=_history([180, 154]),
        cheapest_elsewhere=120.0,
        comparison_currency="EUR",
        merchants_count=4,
        in_stock=True,
        updated_at=BASE,
        offer_kind="accommodation",
        now=BASE + timedelta(hours=2),
    )
    assert d["offer_kind"] == "accommodation"
    assert d["recommendation_scope"] == "tarif_a_verifier"
    assert d["facts"]["price_semantics"] == "indicative_stay_rate"
    assert d["facts"]["merchants_compared"] == 0
    assert {"stay_dates", "travellers", "booking_total", "mandatory_fees", "availability_for_dates", "cancellation_policy"}.issubset(d["missing"])
    assert all(signal["key"] != "comparison" for signal in d["signals"])


def test_service_and_digital_content_require_conditions_instead_of_product_verdict():
    for kind, expected_missing in (("service", "service_scope"), ("digital_content", "digital_region")):
        d = compute_decision(
            price=29.99,
            currency="EUR",
            history=_history([32, 29.99]),
            merchants_count=3,
            in_stock=True,
            updated_at=BASE,
            offer_kind=kind,
            now=BASE + timedelta(hours=1),
        )
        assert d["recommendation_scope"] == "conditions_a_verifier"
        assert expected_missing in d["missing"]
        assert d["price_verdict"]["level"] == "insuffisant"
