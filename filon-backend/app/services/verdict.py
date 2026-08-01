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

from dataclasses import asdict, dataclass
from datetime import datetime

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
    confidence: str     # faible | moyenne | bonne

    def as_dict(self) -> dict:
        return asdict(self)


def _money(value: float, currency: str | None) -> str:
    symbol = {"GBP": "£", "USD": "$"}.get(currency or "EUR", "€")
    return f"{value:,.2f} {symbol}".replace(",", " ").replace(".", ",")


def _confidence(samples: int, tracked_days: int) -> str:
    if samples >= 30 and tracked_days >= 30:
        return "bonne"
    if samples >= MIN_SAMPLES and tracked_days >= MIN_TRACKED_DAYS:
        return "moyenne"
    return "faible"


def compute_verdict(
    *,
    price: float | None,
    currency: str | None,
    history: list[tuple[float | None, datetime | None]],
    cheapest_elsewhere: float | None = None,
    merchants_count: int = 1,
) -> dict:
    """Rend un verdict à partir des mesures disponibles.

    `history` est la suite des relevés (prix, horodatage). `cheapest_elsewhere`
    est le meilleur prix constaté chez un autre marchand pour le même produit.
    """
    prices = [p for (p, _) in history if p is not None and p > 0]
    times = [t for (_, t) in history if t is not None]
    samples = len(prices)
    tracked_days = 0
    if len(times) >= 2:
        tracked_days = max(0, (max(times) - min(times)).days)

    reasons: list[str] = []

    # ── Écart entre marchands : mesurable immédiatement, sans historique ──────
    saving = None
    if (
        price is not None
        and cheapest_elsewhere is not None
        and cheapest_elsewhere < price
    ):
        saving = price - cheapest_elsewhere
        reasons.append(
            f"Le même produit est à {_money(cheapest_elsewhere, currency)} "
            f"chez un autre marchand, soit {_money(saving, currency)} de moins."
        )
    elif merchants_count > 1 and price is not None:
        reasons.append(
            f"C'est le meilleur prix parmi les {merchants_count} marchands qui "
            f"vendent ce produit."
        )

    confidence = _confidence(samples, tracked_days)

    # ── Historique trop court : on le dit, on ne l'invente pas ────────────────
    if price is None or samples < MIN_SAMPLES or tracked_days < MIN_TRACKED_DAYS:
        if saving is not None:
            return Verdict(
                level="attendre",
                headline="Moins cher ailleurs",
                reasons=reasons,
                tracked_days=tracked_days,
                samples=samples,
                confidence=confidence,
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
        ).as_dict()

    low = min(prices)
    high = max(prices)
    average = sum(prices) / len(prices)
    window = f"depuis {tracked_days} jours de suivi"

    if price <= low:
        level = "excellent"
        headline = "Excellent moment pour acheter"
        reasons.insert(0, f"Jamais relevé moins cher {window}.")
    elif price <= average * CHEAP_RATIO:
        level = "bon"
        headline = "Bon moment pour acheter"
        gap = round((1 - price / average) * 100)
        reasons.insert(0, f"{gap} % sous la moyenne observée {window}.")
    elif price >= average * EXPENSIVE_RATIO:
        level = "attendre"
        headline = "Mieux vaut attendre"
        gap = round((price / average - 1) * 100)
        reasons.insert(0, f"{gap} % au-dessus de la moyenne observée {window}.")
        reasons.append(f"Le prix est déjà descendu à {_money(low, currency)} {window}.")
    else:
        level = "neutre"
        headline = "Prix dans sa moyenne habituelle"
        reasons.insert(0, f"Au niveau habituel {window}.")

    if high > low and level in {"excellent", "bon"}:
        reasons.append(
            f"Amplitude constatée : de {_money(low, currency)} à {_money(high, currency)}."
        )

    return Verdict(
        level=level,
        headline=headline,
        reasons=reasons,
        tracked_days=tracked_days,
        samples=samples,
        confidence=confidence,
    ).as_dict()
