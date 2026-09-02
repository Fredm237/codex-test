"""Résolution exacte et comparaison Core pour une observation d'extension.

Le service ne lit aucune table shadow. Il exige un GTIN valide, utilise le
produit Core regroupé par ce même GTIN et ne publie un prix comparé que si au
moins deux marchands portent des preuves courantes dans une devise unique.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from urllib.parse import quote

from sqlalchemy import or_, select

from app.core.config import get_settings
from app.db import models
from app.extension_observation.projection import PageObservationProjection
from app.services.currency import normalize_currency_code
from app.services.freshness import offer_observation_is_fresh
from app.services.offer_evidence import load_offer_evidence


SITE = "https://filon.be"


@dataclass(frozen=True)
class ExactComparisonResult:
    observation_id: str
    resolution: str
    destination_url: str
    comparison: dict[str, Any] | None
    reason_codes: tuple[str, ...]

    def as_contract(self, *, status: str = "accepted") -> dict[str, Any]:
        return {
            "contract_version": "1.0.0",
            "status": status,
            "observation_id": self.observation_id,
            "resolution": self.resolution,
            "destination_url": self.destination_url,
            "comparison": self.comparison,
            "reason_codes": list(self.reason_codes),
        }


def _search_url(title: str) -> str:
    return f"{SITE}/recherche?q={quote(title[:140])}&utm_source=extension&utm_medium=core"


def _product_url(gtin: str) -> str:
    return f"{SITE}/produits/{quote(gtin)}?utm_source=extension&utm_medium=core"


def _unknown(*, offers: int = 0, merchants: int = 0) -> dict[str, Any]:
    return {
        "state": "unknown",
        "offers_compared": offers,
        "merchants_compared": merchants,
        "currency": None,
        "best_price": None,
    }


async def resolve_exact_comparison(
    session,
    projection: PageObservationProjection,
    *,
    evaluated_at: datetime | None = None,
) -> ExactComparisonResult:
    """Résout un GTIN Core puis compare seulement des preuves actuelles."""

    page = projection.payload["page"]
    title = str(page["title"])
    gtin = page.get("gtin")
    if not isinstance(gtin, str) or not gtin:
        return ExactComparisonResult(
            observation_id=projection.replay_key,
            resolution="ambiguous",
            destination_url=_search_url(title),
            comparison=None,
            reason_codes=("missing_exact_identifier",),
        )

    product = await session.scalar(
        select(models.CatalogProduct).where(models.CatalogProduct.ean == gtin)
    )
    if product is None:
        return ExactComparisonResult(
            observation_id=projection.replay_key,
            resolution="not_found",
            destination_url=_search_url(title),
            comparison=None,
            reason_codes=("catalog_product_not_found",),
        )

    statement = (
        select(models.Offer, models.Merchant)
        .join(models.Merchant, models.Offer.merchant_id == models.Merchant.id)
        .where(
            models.Offer.product_id == product.id,
            or_(models.Offer.is_adult.is_(False), models.Offer.is_adult.is_(None)),
        )
    )
    blocked = get_settings().blocked_merchant_slugs
    if blocked:
        statement = statement.where(models.Merchant.slug.notin_(blocked))
    rows = (await session.execute(statement)).all()
    offers = [offer for offer, _merchant in rows]
    evidence = await load_offer_evidence(session, offers, current_only=True)
    reference = evaluated_at or datetime.now(UTC)
    eligible: list[tuple[models.Offer, models.Merchant, str]] = []
    for offer, merchant in rows:
        proof = evidence.get(offer.id)
        currency = normalize_currency_code(offer.currency)
        if (
            not isinstance(offer.price, (int, float))
            or isinstance(offer.price, bool)
            or not math.isfinite(float(offer.price))
            or float(offer.price) <= 0
            or offer.in_stock is not True
            or currency is None
            or proof is None
            or proof.currency != currency
            or not offer_observation_is_fresh(proof.current_observed_at, now=reference)
        ):
            continue
        eligible.append((offer, merchant, currency))

    destination = _product_url(gtin)
    if not eligible:
        return ExactComparisonResult(
            observation_id=projection.replay_key,
            resolution="exact",
            destination_url=destination,
            comparison=_unknown(),
            reason_codes=("exact_gtin", "no_current_offer_evidence"),
        )
    currencies = {currency for _offer, _merchant, currency in eligible}
    merchants = {offer.merchant_id for offer, _merchant, _currency in eligible}
    if len(currencies) != 1:
        return ExactComparisonResult(
            observation_id=projection.replay_key,
            resolution="exact",
            destination_url=destination,
            comparison=_unknown(),
            reason_codes=("exact_gtin", "mixed_currency"),
        )
    if len(eligible) < 2 or len(merchants) < 2:
        return ExactComparisonResult(
            observation_id=projection.replay_key,
            resolution="exact",
            destination_url=destination,
            comparison=_unknown(offers=len(eligible), merchants=len(merchants)),
            reason_codes=("exact_gtin", "insufficient_comparable_offers"),
        )

    currency = next(iter(currencies))
    best = min(float(offer.price) for offer, _merchant, _currency in eligible)
    best_price = format(Decimal(str(best)).normalize(), "f")
    return ExactComparisonResult(
        observation_id=projection.replay_key,
        resolution="exact",
        destination_url=destination,
        comparison={
            "state": "verified",
            "offers_compared": len(eligible),
            "merchants_compared": len(merchants),
            "currency": currency,
            "best_price": best_price,
        },
        reason_codes=("exact_gtin", "current_offer_comparison"),
    )
