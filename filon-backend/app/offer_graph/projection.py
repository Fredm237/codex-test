"""Projection fail-closed d'une ligne Awin vers l'Offer Graph shadow."""

from __future__ import annotations

import ipaddress
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any
from urllib.parse import urlsplit

from sqlalchemy import select

from app.offer_graph import models
from app.product_graph.models import GraphOfferVariantLink
from app.product_graph.resolution import RESOLVER_VERSION
from app.services.currency import normalize_currency_code
from app.services.source_normalization import parse_price, parse_tristate_bool


PROJECTION_VERSION = "awin-offer-graph-v1"
_RESERVED_HOST_SUFFIXES = (
    ".internal",
    ".invalid",
    ".local",
    ".localhost",
    ".test",
    ".example",
)


class OfferGraphProjectionError(ValueError):
    """Entrée hors contrat ; le writer doit rester isolé."""


@dataclass(frozen=True)
class OfferGraphProjection:
    price_amount: Decimal | None
    price_currency: str | None
    price_state: str
    price_reason: str
    availability: str
    merchant_url: str | None
    merchant_url_state: str


@dataclass(frozen=True)
class OfferGraphCapture:
    created: bool
    eligibility: str
    reason_code: str


@dataclass(frozen=True)
class OfferGraphEvaluation:
    offer_variant_link_id: int | None
    eligibility: str
    reason_code: str


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _public_https_url(value: Any) -> tuple[str | None, str]:
    text = _text(value)
    if text is None:
        return None, "unknown"
    try:
        parsed = urlsplit(text)
        hostname = parsed.hostname
        if (
            parsed.scheme.lower() != "https"
            or not hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.port not in {None, 443}
        ):
            return None, "invalid"
    except ValueError:
        return None, "invalid"
    host = hostname.rstrip(".").lower()
    if host == "localhost" or host.endswith(_RESERVED_HOST_SUFFIXES):
        return None, "invalid"
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        # Les clients FILON refusent aussi les littéraux IP publics : un lien
        # marchand doit porter un nom DNS auditable.
        return None, "invalid"
    return text, "known"


def project_awin_offer(row: Mapping[str, Any]) -> OfferGraphProjection:
    if not isinstance(row, Mapping):
        raise OfferGraphProjectionError("awin row must be an object")
    raw_price = _text(row.get("search_price"))
    parsed_price = parse_price(raw_price)
    raw_currency = _text(row.get("currency"))
    currency = normalize_currency_code(raw_currency)
    if raw_price is None:
        amount = None
        price_state = "unknown"
        price_reason = "missing_price"
    elif parsed_price is None or parsed_price <= 0:
        amount = None
        price_state = "invalid"
        price_reason = "invalid_price"
    elif raw_currency is None:
        amount = None
        price_state = "unknown"
        price_reason = "missing_currency"
    elif currency is None:
        amount = None
        price_state = "invalid"
        price_reason = "invalid_currency"
    else:
        amount = Decimal(str(parsed_price)).quantize(Decimal("0.01"))
        price_state = "known"
        price_reason = "known"

    stock = parse_tristate_bool(_text(row.get("in_stock")))
    availability = (
        "in_stock" if stock is True else "out_of_stock" if stock is False else "unknown"
    )
    merchant_url, merchant_url_state = _public_https_url(row.get("aw_deep_link"))
    return OfferGraphProjection(
        price_amount=amount,
        price_currency=currency if price_state == "known" else None,
        price_state=price_state,
        price_reason=price_reason,
        availability=availability,
        merchant_url=merchant_url,
        merchant_url_state=merchant_url_state,
    )


def _eligibility(
    projection: OfferGraphProjection,
    *,
    identity_resolved: bool,
) -> tuple[str, str]:
    if not identity_resolved:
        return "quarantine", "identity_unresolved"
    if projection.price_state == "unknown":
        return "unknown", projection.price_reason
    if projection.price_state == "invalid":
        return "ineligible", projection.price_reason
    if projection.availability == "unknown":
        return "unknown", "availability_unknown"
    if projection.availability == "out_of_stock":
        return "ineligible", "out_of_stock"
    if projection.merchant_url_state == "unknown":
        return "unknown", "missing_link"
    if projection.merchant_url_state == "invalid":
        return "ineligible", "invalid_link"
    return "eligible", "eligible_exact"


async def evaluate_offer_projection(
    session,
    *,
    projection: OfferGraphProjection,
    raw_source_record_id: int,
) -> OfferGraphEvaluation:
    """Évalue sans écrire, pour dry-run et writer partagés."""

    variant_link = await session.scalar(
        select(GraphOfferVariantLink).where(
            GraphOfferVariantLink.raw_source_record_id == raw_source_record_id,
            GraphOfferVariantLink.resolver_version == RESOLVER_VERSION,
        )
    )
    identity_resolved = bool(
        variant_link is not None and variant_link.resolution == "resolved"
    )
    eligibility, reason_code = _eligibility(
        projection,
        identity_resolved=identity_resolved,
    )
    return OfferGraphEvaluation(
        offer_variant_link_id=(variant_link.id if variant_link is not None else None),
        eligibility=eligibility,
        reason_code=reason_code,
    )


async def persist_awin_offer_projection(
    session,
    *,
    projection: OfferGraphProjection,
    raw_source_record_id: int,
    offer_id: int,
    observed_at: datetime,
) -> OfferGraphCapture:
    if raw_source_record_id <= 0 or offer_id <= 0:
        raise OfferGraphProjectionError("offer graph ids must be positive")
    existing = await session.scalar(
        select(models.GraphOfferObservation).where(
            models.GraphOfferObservation.raw_source_record_id
            == raw_source_record_id,
            models.GraphOfferObservation.projection_version == PROJECTION_VERSION,
        )
    )
    if existing is not None:
        return OfferGraphCapture(
            created=False,
            eligibility=existing.eligibility,
            reason_code=existing.reason_code,
        )
    evaluation = await evaluate_offer_projection(
        session,
        projection=projection,
        raw_source_record_id=raw_source_record_id,
    )
    session.add(
        models.GraphOfferObservation(
            raw_source_record_id=raw_source_record_id,
            offer_id=offer_id,
            offer_variant_link_id=evaluation.offer_variant_link_id,
            price_amount=projection.price_amount,
            price_currency=projection.price_currency,
            price_state=projection.price_state,
            availability=projection.availability,
            merchant_url=projection.merchant_url,
            merchant_url_state=projection.merchant_url_state,
            eligibility=evaluation.eligibility,
            reason_code=evaluation.reason_code,
            projection_version=PROJECTION_VERSION,
            observed_at=observed_at,
        )
    )
    await session.flush()
    return OfferGraphCapture(
        created=True,
        eligibility=evaluation.eligibility,
        reason_code=evaluation.reason_code,
    )
