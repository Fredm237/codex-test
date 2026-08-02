"""Endpoint de streaming (SSE) de l'assistant d'achat — Refonte 2026.

Améliorations :
- Validation de la longueur de la requête (max 500 caractères)
- Validation du pays (liste blanche)
- Headers de sécurité (Connection: keep-alive)
- Gestion propre de la déconnexion client
"""

from __future__ import annotations

import json
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.core.logging import get_logger
from app.services.recommend import stream_events

log = get_logger("stream")

router = APIRouter(tags=["advise"])

_VALID_COUNTRIES = {"be", "be-nl", "fr", "ch", "lu", "nl", "de", "uk"}


async def _sse(query: str, budget: float | None, country: str | None) -> AsyncGenerator[str, None]:
    try:
        async for event in stream_events(query, budget, country):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
    except GeneratorExit:
        log.info("Client déconnecté pendant le streaming pour '%s'", query[:30])
    except Exception as exc:
        log.error("Erreur streaming pour '%s': %s", query[:30], exc)
        yield f'data: {{"type": "error", "message": "Erreur interne"}}\n\n'


@router.get("/advise/stream")
async def advise_stream(
    q: str = Query(..., min_length=1, max_length=500, description="Besoin en langage naturel."),
    budget: float | None = Query(default=None, ge=0, le=100000, description="Budget max en euros."),
    country: str | None = Query(default=None, description="Pays : be, be-nl, fr, ch, lu, nl."),
) -> StreamingResponse:
    # Validation du pays
    if country and country.lower() not in _VALID_COUNTRIES:
        raise HTTPException(status_code=400, detail=f"Pays non supporté : {country}")

    log.info("Stream demandé : q='%s' budget=%s country=%s", q[:40], budget, country)

    return StreamingResponse(
        _sse(q, budget, country),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
            "X-Content-Type-Options": "nosniff",
        },
    )
