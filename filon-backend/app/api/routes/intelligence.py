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
from app.intelligence.general_catalog import retrieve_general_offers
from app.intelligence.general_decision import compose_general_plan
from app.intelligence.intent_resolution import resolve_intent_with_fallback
from app.services import taxonomy

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

    fashion_intent = parse_fashion_intent(payload.request, payload.mode)
    general_intent = await resolve_intent_with_fallback(payload.request, payload.locale)
    # Les besoins hors Mode passent au moteur général : une même résolution
    # taxonomique multilingue sert tous les rayons, sans profils de produit.
    # Le moteur mode ne peut traiter qu’une pièce explicitement vestimentaire.
    # Une demande générale encore non résolue doit s’abstenir dans le moteur
    # général, jamais être transformée en tenue ou en accessoire de mode.
    fashion_piece_requested = bool(retrieval_query_for_intent(payload.request))
    use_general = (
        general_intent.resolved
        and not any(scope.category == taxonomy.MODE for scope in general_intent.scopes)
    ) or not fashion_piece_requested
    if use_general:
        intent = general_intent
        offers = await retrieve_general_offers(session, general_intent)
        solution = compose_general_plan(general_intent, offers)
        trace_domain = "general"
    else:
        intent = fashion_intent
        offers = await retrieve_fashion_offers(
            session,
            query=retrieval_query_for_intent(payload.request),
            occasion=fashion_intent.occasion,
        )
        solution = compose_outfit(fashion_intent, offers)
        trace_domain = "fashion"
    trace_key = uuid4().hex

    trace = models.IntelligenceTrace(
        trace_key=trace_key,
        domain=trace_domain,
        status=str(solution["decision"]),
        request_json={"locale": payload.locale, "mode": payload.mode},
        intent_json=(intent.as_dict() if trace_domain == "general" else _trace_payload(intent)),
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
            "taxonomy_resolved_scope" if trace_domain == "general" else "fashion_department",
            "physical_product",
            "canonical",
            "not_adult",
            "known_price",
            "image_present",
            "not_explicitly_out_of_stock",
            "general_lexical_proof" if trace_domain == "general" else "piece_lexical_proof",
            "occasion_term_when_explicitly_supported",
        ],
        result_json=solution,
        rules_version="general-intent-m1" if trace_domain == "general" else "fashion-m2",
    )
    session.add(trace)
    await session.commit()

    return {
        "trace_id": trace_key,
        "domain": trace_domain,
        "intent": (intent.as_dict() if trace_domain == "general" else _trace_payload(intent)),
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
