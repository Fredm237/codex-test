"""Endpoints isolés de la FILON Intelligence Layer.

Aucun endpoint de ce fichier ne remplace le catalogue ou l’assistant. Les modules
sont fermés par défaut et fondés exclusivement sur les données réelles du Core.
"""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.core.config import get_settings
from app.db import session as db
from app.intelligence import models
from app.intelligence.catalog_adapter import retrieve_fashion_offers
from app.intelligence.fashion import compose_outfit, parse_fashion_intent, retrieval_query_for_intent

router = APIRouter(tags=["intelligence"])


class OutfitAnalyseRequest(BaseModel):
    request: str = Field(min_length=2, max_length=1000)
    mode: str | None = Field(default=None, max_length=32)
    locale: str = Field(default="fr", pattern="^(fr|nl|en)$")


class OutfitFeedbackRequest(BaseModel):
    trace_id: str | None = Field(default=None, max_length=64)
    recommendation_key: str | None = Field(default=None, max_length=64)
    action: str = Field(min_length=2, max_length=48)
    reason: str | None = Field(default=None, max_length=255)
    comment: str | None = Field(default=None, max_length=1200)


def intelligence_capabilities() -> dict[str, bool]:
    """État évalué à la requête pour respecter les flags d’environnement."""
    settings = get_settings()
    intelligence = bool(settings.filon_intelligence_enabled)
    fashion = intelligence and bool(settings.fashion_expert_enabled)
    outfit = fashion and bool(settings.outfit_studio_enabled)
    return {
        "intelligence": intelligence,
        "fashion_expert": fashion,
        "outfit_studio": outfit,
    }


def _require_outfit() -> None:
    if not intelligence_capabilities()["outfit_studio"]:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "feature_disabled",
                "message": "Outfit Studio is not enabled.",
            },
        )


def _trace_payload(intent) -> dict[str, object]:
    """Trace utile sans conserver la phrase libre saisie par la personne."""
    return {
        "mode": intent.mode,
        "budget_eur": intent.budget_eur,
        "occasion": intent.occasion,
        "style_hints": list(intent.style_hints),
        "color_hints": list(intent.color_hints),
        "missing_inputs": list(intent.missing_inputs),
    }


@router.get("/intelligence/status")
async def intelligence_status() -> dict:
    """Expose uniquement l’état des modules, jamais les données privées ou Core."""
    modules = intelligence_capabilities()
    return {
        "enabled": modules["intelligence"],
        "modules": modules,
        "version": "v1",
    }


@router.post("/intelligence/outfit/analyse")
async def outfit_analyse(
    payload: OutfitAnalyseRequest,
    session=Depends(db.get_session),
) -> dict:
    """Compose un premier look vérifiable ou s’abstient de recommander.

    Le total présenté ne porte que sur les articles. Aucun coût de livraison,
    délai, taille ou attribut absent du Core n’est inventé.
    """
    _require_outfit()
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "catalog_unavailable", "message": "Catalog data is unavailable."},
        )

    intent = parse_fashion_intent(payload.request, payload.mode)
    offers = await retrieve_fashion_offers(
        session,
        query=retrieval_query_for_intent(payload.request),
        occasion=intent.occasion,
    )
    solution = compose_outfit(intent, offers)
    trace_key = uuid4().hex

    trace = models.IntelligenceTrace(
        trace_key=trace_key,
        domain="fashion",
        status=str(solution["decision"]),
        request_json={"locale": payload.locale, "mode": intent.mode},
        intent_json=_trace_payload(intent),
        candidates_json=[
            {
                "offer_id": offer.offer_id,
                "category": offer.filon_category,
                "price": offer.price,
                "currency": offer.currency,
                "availability": offer.availability,
            }
            for offer in offers
        ],
        filters_json=[
            "fashion_department",
            "physical_product",
            "canonical",
            "not_adult",
            "known_price",
            "image_present",
            "not_explicitly_out_of_stock",
            "piece_lexical_proof",
            "occasion_term_when_explicitly_supported",
        ],
        result_json=solution,
        rules_version="fashion-m2",
    )
    session.add(trace)
    await session.commit()

    return {
        "trace_id": trace_key,
        "domain": "fashion",
        "intent": _trace_payload(intent),
        "candidates_considered": len(offers),
        "solution": solution,
    }


@router.post("/intelligence/outfit/feedback", status_code=status.HTTP_202_ACCEPTED)
async def outfit_feedback(
    payload: OutfitFeedbackRequest,
    session=Depends(db.get_session),
) -> dict:
    """Enregistre un feedback explicite sans créer de préférence silencieuse."""
    _require_outfit()
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "catalog_unavailable", "message": "Catalog data is unavailable."},
        )

    trace_id = None
    if payload.trace_id:
        trace = await session.scalar(
            select(models.IntelligenceTrace).where(
                models.IntelligenceTrace.trace_key == payload.trace_id
            )
        )
        trace_id = trace.id if trace else None
    session.add(
        models.IntelligenceFeedback(
            trace_id=trace_id,
            recommendation_key=payload.recommendation_key,
            action=payload.action,
            reason=payload.reason,
            comment=payload.comment,
        )
    )
    await session.commit()
    return {"accepted": True, "trace_found": trace_id is not None}
