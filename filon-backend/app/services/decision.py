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


def _freshness(observed_at: datetime | None, *, now: datetime) -> tuple[int | None, int, int, str]:
    """Renvoie âge, points, poids actif et statut de fraîcheur.

    Les données qui ne portent aucune date n'obtiennent aucun point et ne
    diminuent pas artificiellement la note : elles sont signalées comme
    inconnues dans `missing` par l'appelant.
    """
    if observed_at is None:
        return None, 0, 0, "unknown"
    age_hours = max(0, int((now - observed_at).total_seconds() // 3600))
    # La fraîcheur est une preuve temporelle, pas une présomption de disponibilité.
    # Au-delà de 72 h, le prix reste documenté mais il n’est plus suffisamment
    # récent pour renforcer une décision d’achat.
    if age_hours <= 72:
        return age_hours, 15, 15, "positive"
    if age_hours <= 7 * 24:
        return age_hours, 5, 15, "warning"
    if age_hours <= 30 * 24:
        return age_hours, 0, 15, "warning"
    return age_hours, 0, 15, "warning"


def _evidence(
    key: str,
    state: str,
    source: str,
    scope: str,
    *,
    observed_at: datetime | None = None,
    value: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Une preuve FILON : fait, origine, périmètre et date, jamais une inférence.

    `state` vaut `observed`, `missing` ou `not_applicable`. Une valeur présente
    n'est pas nécessairement fraîche : cet aspect reste visible dans la preuve
    `freshness` plutôt que d'être caché dans un score.
    """
    item: dict[str, Any] = {
        "key": key,
        "state": state,
        "source": source,
        "scope": scope,
        "observed_at": observed_at.isoformat() if observed_at else None,
    }
    if value is not None:
        item["value"] = value
    return item


def _evidence_summary(evidence: list[dict[str, Any]]) -> dict[str, int]:
    """Couverture documentaire, explicitement distincte d'une probabilité."""
    assessable = [item for item in evidence if item["state"] != "not_applicable"]
    documented = sum(item["state"] == "observed" for item in assessable)
    missing = sum(item["state"] == "missing" for item in assessable)
    return {
        "assessable_dimensions": len(assessable),
        "documented_dimensions": documented,
        "missing_dimensions": missing,
        "coverage_pct": round(documented / len(assessable) * 100) if assessable else 0,
    }


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
    observed_at: datetime | None,
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

    freshness_hours, freshness_points, freshness_weight, freshness_status = _freshness(observed_at, now=now)
    if freshness_hours is None:
        missing.append("data_freshness")
    signals.append({"key": "freshness", "status": freshness_status, "age_hours": freshness_hours})
    active = 1 if freshness_hours is not None else 0
    evidence = [
        _evidence(
            "price",
            "observed" if price is not None else "missing",
            "merchant_feed",
            "tarif observé, hors total contextuel" if price is not None else "tarif absent du dernier flux",
            observed_at=observed_at if price is not None else None,
            value={"amount": price, "currency": currency, "semantics": price_semantics} if price is not None else None,
        ),
        _evidence(
            "comparison",
            "not_applicable",
            "system_policy",
            "les tarifs contextuels ne sont pas comparés comme un même produit",
        ),
        _evidence(
            "availability",
            "missing",
            "merchant_feed",
            "la disponibilité contextuelle n’est pas présente dans le flux",
        ),
        _evidence(
            "freshness",
            "observed" if freshness_hours is not None else "missing",
            "merchant_feed",
            "âge du dernier relevé de prix disponible" if freshness_hours is not None else "date de relevé absente",
            observed_at=observed_at if freshness_hours is not None else None,
            value={"age_hours": freshness_hours, "status": freshness_status} if freshness_hours is not None else None,
        ),
    ]
    for key in dict.fromkeys(missing):
        if key not in {"item_price", "data_freshness", "availability"}:
            evidence.append(_evidence(key, "missing", "not_collected", "information non documentée par FILON"))
    return {
        "version": 3,
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
        "evidence": evidence,
        "evidence_summary": _evidence_summary(evidence),
        "missing": list(dict.fromkeys(missing)),
        "facts": {
            "item_price": price,
            "currency": currency,
            "offer_kind": offer_kind,
            "price_semantics": price_semantics,
            "merchants_compared": 0,
            "offers_compared": 0,
            "last_observed_at": observed_at.isoformat() if observed_at else None,
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
    # `offers.updated_at` peut changer après une correction interne : la fraîcheur
    # affichée doit uniquement provenir d’un snapshot de prix réellement observé.
    now = now or datetime.now(UTC).replace(tzinfo=None)
    observed_at = max((at for _, at in history if at is not None), default=None)
    if offer_kind in _NON_COMPARABLE_KINDS:
        return _contextual_decision(
            offer_kind=offer_kind,
            price=price,
            currency=currency,
            observed_at=observed_at,
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
    freshness_hours, freshness_points, freshness_weight, freshness_status = _freshness(observed_at, now=now)
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

    evidence = [
        _evidence(
            "price",
            "observed" if price is not None else "missing",
            "merchant_feed",
            "prix affiché dans le dernier flux" if price is not None else "prix absent du dernier flux",
            observed_at=observed_at if price is not None else None,
            value={"amount": price, "currency": currency} if price is not None else None,
        ),
        _evidence(
            "comparison",
            "observed" if merchants_count >= 2 else "missing",
            "catalog_grouping",
            "même produit regroupé par EAN" if merchants_count >= 2 else "aucun autre marchand comparable observé",
            value={"merchants_count": merchants_count, "offers_count": offers_count, "is_best_observed": is_best_observed} if merchants_count >= 2 else None,
        ),
        _evidence(
            "price_history",
            "observed" if verdict["level"] in moment_points else "missing",
            "price_history",
            "historique de prix suffisant pour un verdict" if verdict["level"] in moment_points else "historique insuffisant pour conclure",
            value={"level": verdict["level"], "samples": verdict["samples"], "tracked_days": verdict["tracked_days"]},
        ),
        _evidence(
            "availability",
            "observed" if in_stock is not None else "missing",
            "merchant_feed",
            "stock du dernier flux marchand" if in_stock is not None else "stock absent du dernier flux",
            observed_at=None,
            value={"in_stock": in_stock} if in_stock is not None else None,
        ),
        _evidence(
            "freshness",
            "observed" if freshness_hours is not None else "missing",
            "merchant_feed",
            "âge du dernier relevé de prix disponible" if freshness_hours is not None else "date de relevé absente",
            observed_at=observed_at if freshness_hours is not None else None,
            value={"age_hours": freshness_hours, "status": freshness_status} if freshness_hours is not None else None,
        ),
    ]
    for key in _ALWAYS_UNKNOWN:
        evidence.append(_evidence(key, "missing", "not_collected", "information non documentée par FILON"))

    if price is None or in_stock is False:
        scope = "non_recommandee"
    elif is_best_observed:
        scope = "meilleur_prix_observe"
    elif possible >= 30:
        scope = "offre_documentee"
    else:
        scope = "a_verifier"

    return {
        "version": 3,
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
        "evidence": evidence,
        "evidence_summary": _evidence_summary(evidence),
        "missing": list(dict.fromkeys(missing)),
        "facts": {
            "item_price": price,
            "currency": currency,
            "offer_kind": offer_kind or "physical_product",
            "price_semantics": "comparable_product_price",
            "merchants_compared": merchants_count,
            "offers_compared": offers_count,
            "last_observed_at": observed_at.isoformat() if observed_at else None,
            "history_samples": verdict["samples"],
            "history_tracked_days": verdict["tracked_days"],
        },
        # Le verdict reste exposé car il porte une explication de l'historique
        # déjà éprouvée. Il ne constitue pas, à lui seul, la décision complète.
        "price_verdict": verdict,
    }
