"""Tests du Verdict FILON.

Le point le plus important n'est pas qu'il tranche bien, c'est qu'il refuse de
trancher quand les données ne le permettent pas.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from app.services.verdict import MIN_SAMPLES, compute_verdict

BASE = datetime(2026, 1, 1)


def _history(prices: list[float], *, days_apart: int = 1):
    return [(p, BASE + timedelta(days=i * days_apart)) for i, p in enumerate(prices)]


class TestRefusesToGuess:
    def test_says_so_when_history_is_too_short(self):
        v = compute_verdict(price=100.0, currency="EUR", history=_history([100.0, 99.0]))
        assert v["level"] == "insuffisant"
        assert "trop récent" in v["headline"]
        assert v["confidence"] == "faible"

    def test_no_history_at_all(self):
        v = compute_verdict(price=100.0, currency="EUR", history=[])
        assert v["level"] == "insuffisant"
        assert v["samples"] == 0

    def test_many_samples_but_over_a_single_day_is_not_a_trend(self):
        """Vingt relevés en une journée ne disent rien d'une tendance."""
        history = [(100.0, BASE + timedelta(hours=h)) for h in range(20)]
        v = compute_verdict(price=100.0, currency="EUR", history=history)
        assert v["level"] == "insuffisant"

    def test_never_claims_more_than_the_observed_window(self):
        v = compute_verdict(price=80.0, currency="EUR", history=_history([100.0] * 10 + [80.0]))
        assert v["tracked_days"] == 10   # 11 relevés espacés d'un jour
        assert "10 jours de suivi" in " ".join(v["reasons"])


class TestVerdictLevels:
    def test_lowest_ever_is_excellent(self):
        # Huit relevés sur huit jours : au-delà des deux seuils d'énonciation.
        v = compute_verdict(
            price=80.0, currency="EUR",
            history=_history([100.0, 98.0, 95.0, 92.0, 90.0, 88.0, 85.0, 80.0]),
        )
        assert v["level"] == "excellent"
        assert v["headline"] == "Excellent moment pour acheter"
        assert "Jamais relevé moins cher" in v["reasons"][0]

    def test_clearly_below_average_is_good(self):
        v = compute_verdict(
            price=85.0, currency="EUR",
            history=_history([100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 80.0, 85.0]),
        )
        assert v["level"] == "bon"
        assert "%" in v["reasons"][0]

    def test_clearly_above_average_says_wait(self):
        v = compute_verdict(
            price=120.0, currency="EUR",
            history=_history([100.0, 95.0, 100.0, 98.0, 102.0, 99.0, 101.0, 120.0]),
        )
        assert v["level"] == "attendre"
        assert v["headline"] == "Mieux vaut attendre"

    def test_near_average_stays_neutral(self):
        v = compute_verdict(
            price=100.0, currency="EUR",
            history=_history([100.0, 101.0, 99.0, 100.0, 100.0, 100.0, 99.0, 101.0]),
        )
        assert v["level"] == "neutre"


class TestMerchantSpread:
    def test_cheaper_elsewhere_wins_even_without_history(self):
        """L'écart entre marchands est mesurable dès le premier jour."""
        v = compute_verdict(
            price=150.0, currency="EUR", history=[],
            cheapest_elsewhere=120.0, merchants_count=3,
        )
        assert v["level"] == "attendre"
        assert v["headline"] == "Moins cher ailleurs"
        assert "120,00 €" in v["reasons"][0]
        assert "30,00 €" in v["reasons"][0]

    def test_best_price_among_merchants_is_stated(self):
        v = compute_verdict(
            price=120.0, currency="EUR", history=[],
            cheapest_elsewhere=None, merchants_count=3,
        )
        assert "meilleur prix parmi les 3 marchands" in " ".join(v["reasons"])

    def test_single_merchant_says_nothing_about_competition(self):
        v = compute_verdict(price=120.0, currency="EUR", history=[], merchants_count=1)
        assert all("marchand" not in r for r in v["reasons"])


class TestConfidence:
    def test_confidence_grows_with_evidence(self):
        short = compute_verdict(price=100.0, currency="EUR", history=_history([100.0] * 3))
        medium = compute_verdict(price=100.0, currency="EUR", history=_history([100.0] * 10))
        long = compute_verdict(price=100.0, currency="EUR", history=_history([100.0] * 40))
        assert short["confidence"] == "faible"
        assert medium["confidence"] == "moyenne"
        assert long["confidence"] == "bonne"

    def test_threshold_is_respected_exactly(self):
        just_under = compute_verdict(
            price=100.0, currency="EUR", history=_history([100.0] * (MIN_SAMPLES - 1))
        )
        assert just_under["level"] == "insuffisant"
