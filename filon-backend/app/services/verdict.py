"""Verdict FILON — la conclusion, pas la liste.

Un comparateur répond à « où acheter ». La question utile est « est-ce le bon
moment ». Ce module tranche, à partir des seules données réellement mesurées :
l'historique de prix relevé par FILON et l'écart entre marchands.

Règle cardinale : ne jamais prétendre savoir. L'historique se constitue jour
après jour et ne se rattrape pas ; tant qu'il est trop court, le verdict le dit
au lieu d'inventer une tendance. Un « prix au plus bas depuis 6 mois » affiché
au bout de deux jours de suivi serait un mensonge, et le mensonge le plus
coûteux qui soit pour un comparateur.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from datetime import UTC, datetime

from app.services.currency import normalize_currency_code
from app.services.freshness import offer_observation_is_fresh, parse_observed_at

# Seuils d'énonciation. En deçà, on ne parle pas de tendance.
MIN_SAMPLES = 5
MIN_TRACKED_DAYS = 7
# Marges autour de la moyenne : en dessous, la variation n'est pas signifiante.
CHEAP_RATIO = 0.95
EXPENSIVE_RATIO = 1.05


@dataclass
class Verdict:
    level: str          # excellent | bon | neutre | attendre | insuffisant
    headline: str
    reasons: list[str]
    tracked_days: int
    samples: int
    # Aucun niveau qualitatif ne peut être annoncé avant calibration sur un
    # jeu indépendant. La couverture historique reste exposée séparément via
    # `samples` et `tracked_days`.
    confidence: str     # not_calibrated
    basis: str          # price_history | merchant_comparison | insufficient

    def as_dict(self) -> dict:
        return asdict(self)


def _money(value: float, currency: str | None) -> str:
    amount = f"{value:,.2f}".replace(",", " ").replace(".", ",")
    code = normalize_currency_code(currency)
    if code is None:
        return f"{amount} (devise inconnue)"
    symbol = {"EUR": "€", "GBP": "£", "USD": "$"}.get(code)
    return f"{amount} {symbol or code}"


def _valid_amount(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
        and float(value) > 0
    )


def _utc_now(value: datetime | None) -> datetime:
    parsed = parse_observed_at(value or datetime.now(UTC))
    # L'annotation publique n'accepte qu'un datetime. Ce repli défensif garde
    # néanmoins le service fail-closed face à un objet malformé à l'exécution.
    return parsed or datetime.now(UTC)


def _history_measurements(
    history: list[tuple[float | None, datetime | None]],
) -> tuple[list[float], list[datetime]]:
    """Extrait uniquement les couples prix/date exploitables."""

    prices: list[float] = []
    times: list[datetime] = []
    for row in history:
        if not isinstance(row, (tuple, list)) or len(row) < 2:
            continue
        value, captured_at = row[0], row[1]
        if not _valid_amount(value):
            continue
        observed = parse_observed_at(captured_at)
        if observed is None:
            continue
        prices.append(float(value))
        times.append(observed)
    return prices, times


def _latest_price_observation(
    *,
    price: float,
    history: list[tuple[float | None, datetime | None]],
) -> datetime | None:
    observations: list[datetime] = []
    for row in history:
        if not isinstance(row, (tuple, list)) or len(row) < 2:
            continue
        value, captured_at = row[0], row[1]
        if not _valid_amount(value) or not math.isclose(float(value), price, abs_tol=0.005):
            continue
        observed = parse_observed_at(captured_at)
        if observed is not None:
            observations.append(observed)
    return max(observations, default=None)


def compute_verdict(
    *,
    price: float | None,
    currency: str | None,
    history: list[tuple[float | None, datetime | None]],
    cheapest_elsewhere: float | None = None,
    comparison_currency: str | None = None,
    history_currency: str | None = None,
    merchants_count: int = 1,
    in_stock: bool | None = None,
    now: datetime | None = None,
) -> dict:
    """Rend un verdict à partir des mesures disponibles.

    `history` est la suite des relevés (prix, horodatage). `cheapest_elsewhere`
    est le meilleur prix constaté chez un autre marchand pour le même produit.
    """
    reference = _utc_now(now)
    prices, times = _history_measurements(history)
    has_future = any(observed > reference for observed in times)
    samples = len(prices)
    tracked_days = 0
    if len(times) >= 2:
        tracked_days = max(0, (max(times) - min(times)).days)

    reasons: list[str] = []
    normalized_currency = normalize_currency_code(currency)
    normalized_history_currency = normalize_currency_code(history_currency)
    normalized_comparison_currency = normalize_currency_code(comparison_currency)
    valid_price = _valid_amount(price)
    history_currency_is_valid = (
        normalized_history_currency is not None
        and normalized_history_currency == normalized_currency
    )
    observed_at = (
        _latest_price_observation(price=float(price), history=history)
        if valid_price and history_currency_is_valid
        else None
    )
    current_offer_is_documented = (
        valid_price
        and normalized_currency is not None
        and history_currency_is_valid
        and in_stock is True
        and not has_future
        and offer_observation_is_fresh(observed_at, now=reference)
    )
    history_is_comparable = (
        current_offer_is_documented
        and history_currency_is_valid
    )
    comparison_is_comparable = (
        current_offer_is_documented
        and _valid_amount(cheapest_elsewhere)
        and normalized_comparison_currency is not None
        and normalized_comparison_currency == normalized_currency
        and isinstance(merchants_count, int)
        and not isinstance(merchants_count, bool)
        and merchants_count > 1
    )

    # ── Écart entre marchands : mesurable immédiatement, sans historique ──────
    saving = None
    if (
        comparison_is_comparable
        and float(cheapest_elsewhere) < float(price)
    ):
        saving = float(price) - float(cheapest_elsewhere)
        reasons.append(
            f"Le même produit est à {_money(float(cheapest_elsewhere), normalized_currency)} "
            f"chez un autre marchand, soit {_money(saving, normalized_currency)} de moins."
        )
    elif comparison_is_comparable:
        reasons.append(
            f"C'est le meilleur prix parmi les {merchants_count} marchands qui "
            f"vendent ce produit."
        )

    confidence = "not_calibrated"

    # ── Historique trop court : on le dit, on ne l'invente pas ────────────────
    if (
        not current_offer_is_documented
        or not history_is_comparable
        or samples < MIN_SAMPLES
        or tracked_days < MIN_TRACKED_DAYS
    ):
        if saving is not None:
            return Verdict(
                level="attendre",
                headline="Moins cher ailleurs",
                reasons=reasons,
                tracked_days=tracked_days,
                samples=samples,
                confidence=confidence,
                basis="merchant_comparison",
            ).as_dict()
        reasons.append(
            "FILON suit ce prix depuis peu : pas encore de quoi juger son évolution."
        )
        return Verdict(
            level="insuffisant",
            headline="Historique trop récent pour se prononcer",
            reasons=reasons,
            tracked_days=tracked_days,
            samples=samples,
            confidence=confidence,
            basis="insufficient",
        ).as_dict()

    low = min(prices)
    high = max(prices)
    average = sum(prices) / len(prices)
    window = f"sur {tracked_days} jours de suivi"

    current_price = float(price)
    if current_price <= low:
        level = "excellent"
        headline = "Excellent moment pour acheter"
        reasons.insert(
            0,
            f"Parmi les observations en stock, aucun prix inférieur n'a été relevé {window}.",
        )
    elif current_price <= average * CHEAP_RATIO:
        level = "bon"
        headline = "Bon moment pour acheter"
        gap = round((1 - current_price / average) * 100)
        reasons.insert(
            0,
            f"{gap} % sous la moyenne des observations en stock {window}.",
        )
    elif current_price >= average * EXPENSIVE_RATIO:
        level = "attendre"
        headline = "Mieux vaut attendre"
        gap = round((current_price / average - 1) * 100)
        reasons.insert(
            0,
            f"{gap} % au-dessus de la moyenne des observations en stock {window}.",
        )
        reasons.append(
            f"Parmi les observations en stock, le prix est déjà descendu à {_money(low, currency)} {window}."
        )
    else:
        level = "neutre"
        headline = "Prix dans sa moyenne habituelle"
        reasons.insert(0, f"Au niveau moyen des observations en stock {window}.")

    if high > low and level in {"excellent", "bon"}:
        reasons.append(
            f"Amplitude des observations en stock : de {_money(low, currency)} à {_money(high, currency)}."
        )

    return Verdict(
        level=level,
        headline=headline,
        reasons=reasons,
        tracked_days=tracked_days,
        samples=samples,
        confidence=confidence,
        basis="price_history",
    ).as_dict()
