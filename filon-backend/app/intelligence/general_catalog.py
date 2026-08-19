"""Récupération catalogue générale fondée sur une intention taxonomique résolue."""
from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import models
from app.intelligence.contracts import CoreOfferSnapshot
from app.intelligence.intent_resolution import GeneralIntent, IntentScope
from app.services import relevance, taxonomy
from app.services.catalog_paging import fetch_all_offer_rows


def _availability(in_stock: bool | None) -> str:
    if in_stock is True:
        return "in_stock"
    if in_stock is False:
        return "out_of_stock"
    return "unknown"


def _base_statement(scope: IntentScope):
    clauses = [
        models.Offer.filon_category == scope.category,
        models.Offer.offer_kind == taxonomy.PHYSICAL_PRODUCT,
        models.Offer.is_canonical.is_(True),
        or_(models.Offer.is_adult.is_(False), models.Offer.is_adult.is_(None)),
        models.Offer.price.isnot(None),
        models.Offer.currency.isnot(None),
        models.Offer.image_url.isnot(None),
        models.Offer.image_url != "",
        or_(models.Offer.in_stock.is_(True), models.Offer.in_stock.is_(None)),
    ]
    if scope.subcategory is not None:
        clauses.append(models.Offer.filon_subcategory == scope.subcategory)
    return (
        select(models.Offer, models.Merchant)
        .join(models.Merchant, models.Offer.merchant_id == models.Merchant.id)
        .where(*clauses)
    )


def _snapshot(offer: models.Offer, merchant: models.Merchant) -> CoreOfferSnapshot:
    return CoreOfferSnapshot(
        offer_id=offer.id,
        catalog_product_id=offer.product_id,
        name=offer.name,
        brand=offer.brand,
        filon_category=offer.filon_category,
        filon_subcategory=offer.filon_subcategory,
        offer_kind=offer.offer_kind,
        price=offer.price,
        currency=offer.currency,
        availability=_availability(offer.in_stock),
        image_url=offer.image_url,
        deep_link=offer.deep_link,
        merchant_id=merchant.id,
        merchant_name=merchant.name,
        merchant_region=merchant.region,
        observed_at=offer.updated_at,
    )


async def retrieve_general_offers(session: AsyncSession, intent: GeneralIntent) -> list[CoreOfferSnapshot]:
    """Lit toutes les offres prouvant chaque scope, puis élimine les faux positifs.

    Les pages de base sont entièrement parcourues. Le seuil de correspondance est
    appliqué seulement après la lecture des offres du scope : il ne constitue pas
    une limite de volume et ne favorise pas les offres les moins chères.
    """
    seen: set[int] = set()
    snapshots: list[CoreOfferSnapshot] = []
    for scope in intent.scopes:
        rows = await fetch_all_offer_rows(session.execute, _base_statement(scope))
        for offer, merchant in rows:
            if offer.id in seen:
                continue
            normalized_name = (offer.name or "").lower().replace("-", " ")
            if intent.required_title_phrases and not any(
                phrase in normalized_name for phrase in intent.required_title_phrases
            ):
                continue
            terms = list(scope.query_terms)
            if relevance.is_unrequested_satellite(terms, offer.name or ""):
                continue
            if relevance.score(terms, offer.name or "", offer_kind=offer.offer_kind) < relevance.SEUIL:
                continue
            seen.add(offer.id)
            snapshots.append(_snapshot(offer, merchant))
    return snapshots
