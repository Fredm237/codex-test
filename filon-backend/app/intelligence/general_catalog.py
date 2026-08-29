"""Récupération catalogue générale fondée sur une intention taxonomique résolue."""
from __future__ import annotations

from dataclasses import replace

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.observability import decision_trace_event, traced_dependency
from app.db import models
from app.intelligence.contracts import CoreOfferSnapshot
from app.intelligence.intent_resolution import GeneralIntent, IntentScope
from app.services import relevance, taxonomy
from app.services.catalog_paging import fetch_all_offer_rows
from app.services.offer_evidence import load_offer_evidence


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
        # `updated_at` est technique et peut changer lors d'un reclassement.
        # Le vrai relevé prix+devise+stock est rattaché en lot ci-dessous.
        observed_at=None,
    )


async def retrieve_general_offers(session: AsyncSession, intent: GeneralIntent) -> list[CoreOfferSnapshot]:
    """Lit toutes les offres prouvant chaque scope, puis élimine les faux positifs.

    Les pages de base sont entièrement parcourues. Le seuil de correspondance est
    appliqué seulement après la lecture des offres du scope : il ne constitue pas
    une limite de volume et ne favorise pas les offres les moins chères.
    """
    seen: set[int] = set()
    snapshots: list[CoreOfferSnapshot] = []
    input_count = 0
    for scope in intent.scopes:
        async with traced_dependency("postgres", "read"):
            rows = await fetch_all_offer_rows(
                session.execute,
                _base_statement(scope),
            )
        input_count += len(rows)
        strict: list[CoreOfferSnapshot] = []
        scoped: list[CoreOfferSnapshot] = []
        terms = list(scope.query_terms)
        for offer, merchant in rows:
            if offer.id in seen:
                continue
            normalized_name = (offer.name or "").lower().replace("-", " ")
            if intent.required_title_phrases and not any(
                phrase in normalized_name for phrase in intent.required_title_phrases
            ):
                continue
            # Le scope FILON résolu est la preuve de compatibilité principale.
            # L’heuristique locale « satellite » ne s’applique pas ici : elle
            # éliminerait des composants légitimes d’un kit (p. ex. sac de couchage).
            snapshot = _snapshot(offer, merchant)
            scoped.append(snapshot)
            if relevance.score(terms, offer.name or "", offer_kind=offer.offer_kind) >= relevance.SEUIL:
                strict.append(snapshot)
        # Une résolution de scope est une preuve plus forte qu’un mot de requête
        # absent des titres des marchands. Ainsi « kampeeruitrusting » peut lire
        # tout Camping & Randonnée sans devenir une abstention artificielle.
        selected = strict or scoped
        for snapshot in selected:
            if snapshot.offer_id not in seen:
                seen.add(snapshot.offer_id)
                snapshots.append(snapshot)
    decision_trace_event(
        "retrieval",
        counts={
            "scopes_count": len(intent.scopes),
            "input_count": input_count,
            "candidate_count": len(snapshots),
        },
    )
    decision_trace_event(
        "candidate_count",
        counts={"candidate_count": len(snapshots)},
    )
    decision_trace_event(
        "filtering",
        counts={
            "input_count": input_count,
            "eligible_count": len(snapshots),
            "rejected_count": max(0, input_count - len(snapshots)),
        },
    )
    async with traced_dependency("postgres", "read"):
        evidence_by_offer = await load_offer_evidence(
            session,
            list(snapshots),
            current_only=True,
        )
    evidenced = [
        replace(
            snapshot,
            currency=evidence_by_offer.get(snapshot.offer_id).currency,
            observed_at=evidence_by_offer.get(snapshot.offer_id).current_observed_at,
        )
        if snapshot.offer_id in evidence_by_offer
        else replace(snapshot, currency=None, observed_at=None)
        for snapshot in snapshots
    ]
    decision_trace_event(
        "evidence",
        counts={
            "evidenced_count": len(evidence_by_offer),
            "unknown_count": max(0, len(snapshots) - len(evidence_by_offer)),
        },
    )
    return evidenced
