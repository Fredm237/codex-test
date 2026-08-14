"""Décision FILON — preuve, périmètre et incertitude.

Le module ne cherche pas à prédire la livraison ou à noter arbitrairement un
marchand. Il structure uniquement les signaux réellement observés dans les
feeds FILON et l'historique de prix, puis rend les inconnues visibles.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.services.verdict import compute_verdict

# Les informations actuellement absentes de tous les flux doivent rester visibles
# comme telles. Les masquer derrière une note unique transformerait une lacune de
# donnée en promesse d'achat.
_ALWAYS_UNKNOWN = ("shipping_cost", "delivery_destination", "return_policy")

# Ces offres portent un prix observé, mais leur montant final dépend d’un
# contexte que les feeds ne fournissent pas. Elles ne passent jamais par le
# verdict « meilleur prix » des produits physiques.
_NON_COMPARABLE_KINDS = {"accommodation", "service", "digital_content", "unknown"}


def _freshness(updated_at: datetime | None, *, now: datetime) -> tuple[int | None, int, int, str]:
    """Renvoie âge, points, poids actif et statut de fraîcheur.

    Les données qui ne portent aucune date n'obtiennent aucun point et ne
    diminuent pas artificiellement la note : elles sont signalées comme
    inconnues dans `missing` par l'appelant.
    """
    if updated_at is None:
        return None, 0, 0, "unknown"
    age_hours = max(0, int((now - updated_at).total_seconds() // 3600))
    if age_hours <= 24:
        return age_hours, 15, 15, "positive"
    if age_hours <= 7 * 24:
        return age_hours, 10, 15, "positive"
    if age_hours <= 30 * 24:
        return age_hours, 5, 15, "warning"
    return age_hours, 0, 15, "warning"


def _confidence(*, active_signals: int, history_confidence: str, merchants_count: int,
                in_stock: bool | None, freshness_hours: int | None) -> str:
    """Niveau de confiance, jamais confondu avec une probabilité de livraison."""
    if (
        history_confidence == "bonne"
        and merchants_count >= 2
        and in_stock is not None
        and freshness_hours is not None
        and freshness_hours <= 48
    ):
        return "elevee"
    if active_signals >= 2:
        return "moyenne"
    if active_signals:
        return "faible"
    return "insuffisante"


def _contextual_decision(
    *,
    offer_kind: str,
    price: float | None,
    currency: str | None,
    updated_at: datetime | None,
    now: datetime,
) -> dict[str, Any]:
    """Décision pour un tarif dépendant d’un contexte non observé par FILON."""
    kind_missing = {
        "accommodation": (
            "stay_dates", "travellers", "booking_total", "mandatory_fees",
            "availability_for_dates", "cancellation_policy",
        ),
        "service": ("service_scope", "service_conditions", "appointment_availability"),
        "digital_content": ("digital_compatibility", "digital_region", "digital_terms"),
        "unknown": ("offer_nature", "purchase_conditions"),
    }
    price_semantics = {
        "accommodation": "indicative_stay_rate",
        "service": "indicative_service_rate",
        "digital_content": "observed_digital_price",
        "unknown": "unclassified_price",
    }.get(offer_kind, "contextual_price")
    scope = "tarif_a_verifier" if offer_kind == "accommodation" else "conditions_a_verifier"
    missing = list(_ALWAYS_UNKNOWN) + list(kind_missing.get(offer_kind, kind_missing["unknown"]))
    signals: list[dict[str, Any]] = []
    if price is None:
        missing.append("item_price")
        signals.append({"key": "price", "status": "unknown"})
    else:
        signals.append({"key": "contextual_price", "status": "neutral", "price_semantics": price_semantics})

    freshness_hours, freshness_points, freshness_weight, freshness_status = _freshness(updated_at, now=now)
    if freshness_hours is None:
        missing.append("data_freshness")
    signals.append({"key": "freshness", "status": freshness_status, "age_hours": freshness_hours})
    active = 1 if freshness_hours is not None else 0
    return {
        "version": 2,
        "offer_kind": offer_kind,
        "recommendation_scope": scope,
        "score_observed": freshness_points if freshness_hours is not None else 0,
        "score_possible": freshness_weight if freshness_hours is not None else 0,
        "confidence": _confidence(
            active_signals=active,
            history_confidence="insuffisante",
            merchants_count=1,
            in_stock=None,
            freshness_hours=freshness_hours,
        ),
        "signals": signals,
        "missing": list(dict.fromkeys(missing)),
        "facts": {
            "item_price": price,
            "currency": currency,
            "offer_kind": offer_kind,
            "price_semantics": price_semantics,
            "merchants_compared": 0,
            "offers_compared": 0,
            "updated_at": updated_at.isoformat() if updated_at else None,
            "history_samples": 0,
            "history_tracked_days": 0,
        },
        "price_verdict": {"level": "insuffisant", "samples": 0, "tracked_days": 0, "confidence": "insuffisante"},
    }


def compute_decision(
    *,
    price: float | None,
    currency: str | None,
    history: list[tuple[float | None, datetime | None]],
    cheapest_elsewhere: float | None = None,
    comparison_currency: str | None = None,
    merchants_count: int = 1,
    offers_count: int = 1,
    in_stock: bool | None = None,
    updated_at: datetime | None = None,
    offer_kind: str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Construit une décision explicable à partir des seules données observées.

    `cheapest_elsewhere` doit désigner le plus bas prix du même EAN. Une
    comparaison de devises différente est volontairement neutralisée : un prix
    GBP n'est pas comparable à un prix EUR sans taux et frais vérifiables.
    """
    # Les timestamps existants de la base sont naïfs mais exprimés en UTC.
    # On conserve ce contrat tout en évitant datetime.utcnow(), désormais obsolète.
    now = now or datetime.now(UTC).replace(tzinfo=None)
    if offer_kind in _NON_COMPARABLE_KINDS:
        return _contextual_decision(
            offer_kind=offer_kind,
            price=price,
            currency=currency,
            updated_at=updated_at,
            now=now,
        )
    if comparison_currency and currency and comparison_currency != currency:
        cheapest_elsewhere = None
        merchants_count = 1

    verdict = compute_verdict(
        price=price,
        currency=currency,
        history=history,
        cheapest_elsewhere=cheapest_elsewhere,
        merchants_count=merchants_count,
    )

    missing = list(_ALWAYS_UNKNOWN)
    signals: list[dict[str, Any]] = []
    observed = 0
    possible = 0
    active_signals = 0

    # Prix et périmètre de comparaison.
    is_best_observed = False
    if price is None:
        missing.append("item_price")
        signals.append({"key": "price", "status": "unknown"})
    elif merchants_count >= 2:
        possible += 35
        active_signals += 1
        if cheapest_elsewhere is None or price <= cheapest_elsewhere + 0.005:
            observed += 35
            is_best_observed = True
            signals.append(
                {
                    "key": "comparison",
                    "status": "positive",
                    "merchants_count": merchants_count,
                    "offers_count": offers_count,
                    "is_best_observed": True,
                }
            )
        else:
            signals.append(
                {
                    "key": "comparison",
                    "status": "warning",
                    "merchants_count": merchants_count,
                    "offers_count": offers_count,
                    "cheapest_elsewhere": cheapest_elsewhere,
                    "is_best_observed": False,
                }
            )
    else:
        missing.append("comparison_scope")
        signals.append({"key": "comparison", "status": "unknown", "merchants_count": merchants_count})

    # Moment prix : le verdict existant reste la source de vérité car il refuse
    # déjà de conclure quand l'historique est trop court.
    moment_points = {"excellent": 25, "bon": 20, "neutre": 12, "attendre": 0}
    if verdict["level"] in moment_points:
        possible += 25
        active_signals += 1
        observed += moment_points[verdict["level"]]
        status = "positive" if verdict["level"] in {"excellent", "bon"} else "warning" if verdict["level"] == "attendre" else "neutral"
        signals.append(
            {
                "key": "price_moment",
                "status": status,
                "level": verdict["level"],
                "tracked_days": verdict["tracked_days"],
                "samples": verdict["samples"],
            }
        )
    else:
        missing.append("price_history")
        signals.append(
            {
                "key": "price_moment",
                "status": "unknown",
                "tracked_days": verdict["tracked_days"],
                "samples": verdict["samples"],
            }
        )

    # Stock : l'absence de valeur n'est jamais assimilée à « en stock ».
    if in_stock is None:
        missing.append("availability")
        signals.append({"key": "availability", "status": "unknown"})
    else:
        possible += 15
        active_signals += 1
        if in_stock:
            observed += 15
            signals.append({"key": "availability", "status": "positive", "in_stock": True})
        else:
            signals.append({"key": "availability", "status": "warning", "in_stock": False})

    # Fraîcheur de collecte.
    freshness_hours, freshness_points, freshness_weight, freshness_status = _freshness(updated_at, now=now)
    if freshness_hours is None:
        missing.append("data_freshness")
    else:
        observed += freshness_points
        possible += freshness_weight
        active_signals += 1
    signals.append(
        {
            "key": "freshness",
            "status": freshness_status,
            "age_hours": freshness_hours,
        }
    )

    # Richesse de la comparaison : une preuve de périmètre, non une note marchand.
    if merchants_count >= 2:
        possible += 10
        active_signals += 1
        strength = 10 if merchants_count >= 5 else 7 if merchants_count >= 3 else 5
        observed += strength
        signals.append({"key": "comparison_strength", "status": "positive", "merchants_count": merchants_count})

    if price is None or in_stock is False:
        scope = "non_recommandee"
    elif is_best_observed:
        scope = "meilleur_prix_observe"
    elif possible >= 30:
        scope = "offre_documentee"
    else:
        scope = "a_verifier"

    return {
        "version": 1,
        "offer_kind": offer_kind or "physical_product",
        "recommendation_scope": scope,
        "score_observed": observed,
        "score_possible": possible,
        "confidence": _confidence(
            active_signals=active_signals,
            history_confidence=verdict["confidence"],
            merchants_count=merchants_count,
            in_stock=in_stock,
            freshness_hours=freshness_hours,
        ),
        "signals": signals,
        "missing": list(dict.fromkeys(missing)),
        "facts": {
            "item_price": price,
            "currency": currency,
            "offer_kind": offer_kind or "physical_product",
            "price_semantics": "comparable_product_price",
            "merchants_compared": merchants_count,
            "offers_compared": offers_count,
            "updated_at": updated_at.isoformat() if updated_at else None,
            "history_samples": verdict["samples"],
            "history_tracked_days": verdict["tracked_days"],
        },
        # Le verdict reste exposé car il porte une explication de l'historique
        # déjà éprouvée. Il ne constitue pas, à lui seul, la décision complète.
        "price_verdict": verdict,
    }
