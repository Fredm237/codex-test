"""Décision FILON — preuve, périmètre et incertitude.

Le module ne cherche pas à prédire la livraison ou à noter arbitrairement un
marchand. Il structure uniquement les signaux réellement observés dans les
feeds FILON et l'historique de prix, puis rend les inconnues visibles.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta
from typing import Any

from app.core.observability import product_intelligence_metrics
from app.services.currency import normalize_currency_code
from app.services.freshness import OFFER_RECOMMENDATION_MAX_AGE_HOURS
from app.services.freshness import parse_observed_at
from app.services.verdict import compute_verdict

# Les informations actuellement absentes de tous les flux doivent rester visibles
# comme telles. Les masquer derrière une note unique transformerait une lacune de
# donnée en promesse d'achat.
_ALWAYS_UNKNOWN = ("shipping_cost", "delivery_destination", "return_policy")

# Ces offres portent un prix observé, mais leur montant final dépend d’un
# contexte que les feeds ne fournissent pas. Elles ne passent jamais par le
# verdict « meilleur prix » des produits physiques.
_NON_COMPARABLE_KINDS = {"accommodation", "service", "digital_content", "unknown"}


def _valid_amount(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
        and float(value) > 0
    )


def _reference_time(value: datetime | None) -> datetime:
    parsed = parse_observed_at(value or datetime.now(UTC))
    return parsed or datetime.now(UTC)


def _latest_price_observation(
    *,
    price: float | None,
    history: list[tuple[float | None, datetime | None]],
) -> datetime | None:
    """Dernier relevé daté qui prouve le prix courant exact."""

    if not _valid_amount(price):
        return None
    observations: list[datetime] = []
    for row in history:
        if not isinstance(row, (tuple, list)) or len(row) < 2:
            continue
        amount, captured_at = row[0], row[1]
        if not _valid_amount(amount) or not math.isclose(
            float(amount), float(price), abs_tol=0.005
        ):
            continue
        observed = parse_observed_at(captured_at)
        if observed is not None:
            observations.append(observed)
    return max(observations, default=None)


def _history_has_future_observation(
    history: list[tuple[float | None, datetime | None]], *, now: datetime
) -> bool:
    reference = parse_observed_at(now)
    if reference is None:
        return True
    for row in history:
        if not isinstance(row, (tuple, list)) or len(row) < 2 or not _valid_amount(row[0]):
            continue
        observed = parse_observed_at(row[1])
        if observed is not None and observed > reference:
            return True
    return False


def _freshness(observed_at: datetime | None, *, now: datetime) -> dict[str, Any]:
    """Expose l'âge et l'admissibilité temporelle sans présomption.

    Les données qui ne portent aucune date ne deviennent jamais fraîches. Un
    horodatage futur est une preuve invalide, pas un âge de zéro heure.
    """
    if observed_at is None:
        return {"age_hours": None, "status": "unknown", "state": "missing"}
    observed = parse_observed_at(observed_at)
    reference = parse_observed_at(now)
    if observed is None or reference is None:
        return {"age_hours": None, "status": "warning", "state": "invalid"}
    delta = reference - observed
    if delta.total_seconds() < 0:
        return {"age_hours": None, "status": "warning", "state": "future"}
    age_hours = int(delta.total_seconds() // 3600)
    if delta <= timedelta(hours=OFFER_RECOMMENDATION_MAX_AGE_HOURS):
        return {"age_hours": age_hours, "status": "positive", "state": "fresh"}
    return {"age_hours": age_hours, "status": "warning", "state": "stale"}


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
    if currency is None:
        missing.append("currency")
    if price is None:
        missing.append("item_price")
        signals.append({"key": "price", "status": "unknown"})
    elif currency is None:
        signals.append({"key": "price", "status": "unknown", "reason": "invalid_currency"})
    else:
        signals.append({"key": "contextual_price", "status": "neutral", "price_semantics": price_semantics})

    freshness = _freshness(observed_at, now=now)
    freshness_hours = freshness["age_hours"]
    if freshness["state"] != "fresh":
        missing.append("data_freshness")
    signals.append(
        {
            "key": "freshness",
            "status": freshness["status"],
            "age_hours": freshness_hours,
            "reason": freshness["state"],
        }
    )
    evidence = [
        _evidence(
            "price",
            "observed" if price is not None and currency is not None and freshness["state"] in {"fresh", "stale"} else "missing",
            "merchant_feed",
            "tarif observé, hors total contextuel" if price is not None and currency is not None and freshness["state"] in {"fresh", "stale"} else "tarif insuffisamment documenté",
            observed_at=observed_at if price is not None and currency is not None and freshness["state"] in {"fresh", "stale"} else None,
            value={"amount": price, "currency": currency, "semantics": price_semantics} if price is not None and currency is not None else None,
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
            "observed" if freshness["state"] in {"fresh", "stale"} else "missing",
            "merchant_feed",
            "âge du dernier relevé de prix disponible" if freshness_hours is not None else "date de relevé absente",
            observed_at=observed_at if freshness_hours is not None else None,
            value={"age_hours": freshness_hours, "status": freshness["state"]} if freshness_hours is not None else None,
        ),
    ]
    for key in dict.fromkeys(missing):
        if key not in {"item_price", "data_freshness", "availability"}:
            evidence.append(_evidence(key, "missing", "not_collected", "information non documentée par FILON"))
    return {
        "version": 3,
        "offer_kind": offer_kind,
        "recommendation_scope": scope,
        "confidence": "not_calibrated",
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
        "price_verdict": {
            "level": "insuffisant",
            "samples": 0,
            "tracked_days": 0,
            "confidence": "not_calibrated",
            "basis": "insufficient",
        },
    }


def compute_decision(
    *,
    price: float | None,
    currency: str | None,
    history: list[tuple[float | None, datetime | None]],
    cheapest_elsewhere: float | None = None,
    comparison_currency: str | None = None,
    history_currency: str | None = None,
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
    reference = _reference_time(now)
    normalized_currency = normalize_currency_code(currency)
    normalized_comparison_currency = normalize_currency_code(comparison_currency)
    normalized_history_currency = normalize_currency_code(history_currency)
    current_price = float(price) if _valid_amount(price) else None
    history_currency_is_valid = (
        normalized_history_currency is not None
        and normalized_history_currency == normalized_currency
    )
    observed_at = (
        _latest_price_observation(price=price, history=history)
        if history_currency_is_valid
        else None
    )
    if offer_kind in _NON_COMPARABLE_KINDS:
        result = _contextual_decision(
            offer_kind=offer_kind,
            price=current_price,
            currency=normalized_currency,
            observed_at=observed_at,
            now=reference,
        )
        product_intelligence_metrics.record_decision(result)
        return result
    valid_merchants_count = (
        merchants_count
        if isinstance(merchants_count, int)
        and not isinstance(merchants_count, bool)
        and merchants_count > 0
        else 1
    )
    valid_offers_count = (
        offers_count
        if isinstance(offers_count, int)
        and not isinstance(offers_count, bool)
        and offers_count > 0
        else 1
    )
    price_is_valid = current_price is not None
    currency_is_valid = normalized_currency is not None
    freshness = _freshness(observed_at, now=reference)
    if _history_has_future_observation(history, now=reference):
        freshness = {
            "age_hours": None,
            "status": "warning",
            "state": "future",
        }
    freshness_is_valid = freshness["state"] == "fresh"
    observation_is_real = freshness["state"] in {"fresh", "stale"}
    stock_is_confirmed = in_stock is True
    stock_is_unavailable = in_stock is False
    current_offer_is_eligible = (
        price_is_valid
        and currency_is_valid
        and stock_is_confirmed
        and freshness_is_valid
    )
    comparison_scope_is_documented = (
        price_is_valid
        and currency_is_valid
        and valid_merchants_count >= 2
        and _valid_amount(cheapest_elsewhere)
        and normalized_comparison_currency is not None
        and normalized_comparison_currency == normalized_currency
    )
    comparison_is_comparable = (
        current_offer_is_eligible and comparison_scope_is_documented
    )

    verdict = compute_verdict(
        price=current_price,
        currency=normalized_currency,
        history=history,
        cheapest_elsewhere=cheapest_elsewhere,
        comparison_currency=normalized_comparison_currency,
        history_currency=normalized_history_currency,
        merchants_count=valid_merchants_count,
        in_stock=in_stock,
        now=reference,
    )

    missing = list(_ALWAYS_UNKNOWN)
    signals: list[dict[str, Any]] = []
    # Prix et périmètre de comparaison.
    is_best_observed = False
    if not currency_is_valid:
        missing.append("currency")
    if not price_is_valid:
        missing.append("item_price")
        signals.append({"key": "price", "status": "unknown"})
    elif not currency_is_valid:
        signals.append({"key": "price", "status": "unknown", "reason": "invalid_currency"})
    elif comparison_is_comparable:
        if current_price <= float(cheapest_elsewhere) + 0.005:
            is_best_observed = True
            signals.append(
                {
                    "key": "comparison",
                    "status": "positive",
                    "merchants_count": valid_merchants_count,
                    "offers_count": valid_offers_count,
                    "is_best_observed": True,
                }
            )
        else:
            signals.append(
                {
                    "key": "comparison",
                    "status": "warning",
                    "merchants_count": valid_merchants_count,
                    "offers_count": valid_offers_count,
                    "cheapest_elsewhere": cheapest_elsewhere,
                    "is_best_observed": False,
                }
            )
    else:
        missing.append("comparison_scope")
        signals.append(
            {
                "key": "comparison",
                "status": "unknown",
                "merchants_count": valid_merchants_count,
            }
        )

    if history and not history_currency_is_valid:
        missing.append("history_currency")

    # Moment prix : le verdict existant reste la source de vérité car il refuse
    # déjà de conclure quand l'historique est trop court.
    historical_levels = {"excellent", "bon", "neutre", "attendre"}
    historical_verdict = verdict.get("basis") == "price_history"
    if historical_verdict and verdict["level"] in historical_levels:
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
    if not stock_is_confirmed and not stock_is_unavailable:
        missing.append("availability")
        signals.append({"key": "availability", "status": "unknown"})
    else:
        if stock_is_confirmed:
            signals.append({"key": "availability", "status": "positive", "in_stock": True})
        else:
            signals.append({"key": "availability", "status": "warning", "in_stock": False})

    # Fraîcheur de collecte.
    freshness_hours = freshness["age_hours"]
    if not freshness_is_valid:
        missing.append("data_freshness")
    signals.append(
        {
            "key": "freshness",
            "status": freshness["status"],
            "age_hours": freshness_hours,
            "reason": freshness["state"],
        }
    )

    # Richesse de la comparaison : une preuve de périmètre, non une note marchand.
    if comparison_is_comparable:
        signals.append({"key": "comparison_strength", "status": "positive", "merchants_count": valid_merchants_count})

    evidence = [
        _evidence(
            "price",
            "observed" if price_is_valid and currency_is_valid and observation_is_real else "missing",
            "merchant_feed",
            "prix et devise reliés à un relevé" if price_is_valid and currency_is_valid and observation_is_real else "prix courant insuffisamment documenté",
            observed_at=observed_at if price_is_valid and currency_is_valid and observation_is_real else None,
            value={"amount": current_price, "currency": normalized_currency} if price_is_valid and currency_is_valid else None,
        ),
        _evidence(
            "comparison",
            "observed" if comparison_is_comparable else "missing",
            "catalog_grouping",
            "même produit et même devise regroupés par EAN" if comparison_is_comparable else "aucun autre marchand comparable avec devise et fraîcheur prouvées",
            value={"merchants_count": valid_merchants_count, "offers_count": valid_offers_count, "is_best_observed": is_best_observed} if comparison_is_comparable else None,
        ),
        _evidence(
            "price_history",
            "observed" if historical_verdict and verdict["level"] in historical_levels else "missing",
            "price_history",
            "historique de prix suffisant pour un verdict" if historical_verdict and verdict["level"] in historical_levels else "historique insuffisant pour conclure",
            value={"level": verdict["level"], "samples": verdict["samples"], "tracked_days": verdict["tracked_days"]},
        ),
        _evidence(
            "availability",
            "observed" if stock_is_confirmed or stock_is_unavailable else "missing",
            "merchant_feed",
            "stock du dernier flux marchand" if stock_is_confirmed or stock_is_unavailable else "stock absent ou invalide dans le dernier flux",
            observed_at=None,
            value={"in_stock": in_stock} if stock_is_confirmed or stock_is_unavailable else None,
        ),
        _evidence(
            "freshness",
            "observed" if freshness_is_valid else "missing",
            "merchant_feed",
            "relevé de prix sous le TTL" if freshness_is_valid else "relevé absent, futur ou périmé",
            observed_at=observed_at if freshness_is_valid else None,
            value={"age_hours": freshness_hours, "status": freshness["state"]} if freshness_hours is not None else None,
        ),
    ]
    for key in _ALWAYS_UNKNOWN:
        evidence.append(_evidence(key, "missing", "not_collected", "information non documentée par FILON"))

    if not price_is_valid or stock_is_unavailable:
        scope = "non_recommandee"
    elif not current_offer_is_eligible:
        scope = "a_verifier"
    elif is_best_observed:
        scope = "meilleur_prix_observe"
    elif current_offer_is_eligible:
        scope = "offre_documentee"
    else:
        scope = "a_verifier"

    result = {
        "version": 3,
        "offer_kind": offer_kind or "physical_product",
        "recommendation_scope": scope,
        "confidence": "not_calibrated",
        "signals": signals,
        "evidence": evidence,
        "evidence_summary": _evidence_summary(evidence),
        "missing": list(dict.fromkeys(missing)),
        "facts": {
            "item_price": current_price,
            "currency": normalized_currency,
            "offer_kind": offer_kind or "physical_product",
            "price_semantics": "comparable_product_price",
            "merchants_compared": valid_merchants_count if comparison_is_comparable else 0,
            "offers_compared": valid_offers_count if comparison_is_comparable else 0,
            "last_observed_at": observed_at.isoformat() if observed_at else None,
            "history_samples": verdict["samples"],
            "history_tracked_days": verdict["tracked_days"],
        },
        # Le verdict reste exposé car il porte une explication de l'historique
        # déjà éprouvée. Il ne constitue pas, à lui seul, la décision complète.
        "price_verdict": verdict,
    }
    product_intelligence_metrics.record_decision(result)
    return result
