"""Primitives fail-closed pour les agrégats de prix du catalogue.

Les colonnes SQL historiques sont en UTC naïf, tandis que les sorties API
doivent rester horodatées explicitement. La devise d'un relevé ne peut en outre
jamais être déduite de l'offre courante : comparaison et agrégation exigent
deux codes supportés, identiques après normalisation, et un stock confirmé des
deux côtés.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import and_, func

from app.services.currency import SUPPORTED_CURRENCY_CODES


# Toute modification du contrat prix/devise/stock doit invalider les anciens
# agrégats mis en cache au lieu de les resservir avec une sémantique nouvelle.
PRICE_TRUTH_CACHE_VERSION = "catalog-price-truth-v1"


def utc_naive_now() -> datetime:
    """Retourne l'UTC courant compatible avec les colonnes SQL `DateTime`.

    Les modèles existants stockent des dates UTC sans `tzinfo`. Passer un objet
    aware à asyncpg pour ces colonnes peut lever une erreur de comparaison ;
    `datetime.utcnow()` est pour sa part déprécié. Cette conversion conserve le
    contrat de stockage sans perdre l'intention UTC.
    """

    return datetime.now(UTC).replace(tzinfo=None)


def normalized_currency_sql(column):
    """Normalisation SQL identique au roster Python, sans valeur par défaut."""

    return func.upper(func.trim(column))


def same_supported_currency_sql(left, right):
    """Vrai seulement pour deux devises explicites, supportées et identiques."""

    supported = tuple(sorted(SUPPORTED_CURRENCY_CODES))
    left_code = normalized_currency_sql(left)
    right_code = normalized_currency_sql(right)
    return and_(
        left.isnot(None),
        right.isnot(None),
        left_code.in_(supported),
        right_code.in_(supported),
        left_code == right_code,
    )


def comparable_price_evidence_sql(
    *,
    snapshot_currency,
    offer_currency,
    snapshot_in_stock,
    offer_in_stock,
):
    """Clause commune aux claims comparant historique et offre courante."""

    return and_(
        same_supported_currency_sql(snapshot_currency, offer_currency),
        snapshot_in_stock.is_(True),
        offer_in_stock.is_(True),
    )
