"""Endpoint de streaming (SSE) de l'assistant d'achat — Refonte 2026.

Améliorations :
- Validation de la longueur de la requête (max 500 caractères)
- Validation du pays (liste blanche)
- Headers de sécurité (Connection: keep-alive)
- Gestion propre de la déconnexion client
"""

from __future__ import annotations

import json
import time
from typing import AsyncGenerator

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.core.logging import get_logger
from app.services.recommend import stream_events
from app.v2_chain.live_dark_reader import observe_live_dark_read

log = get_logger("stream")

router = APIRouter(tags=["advise"])

_VALID_COUNTRIES = {"be", "be-nl", "fr", "ch", "lu", "nl", "de", "uk"}
_VALID_LOCALES = {"fr", "nl", "en"}


async def _sse(
    query: str,
    budget: float | None,
    country: str | None,
    locale: str,
    background_tasks: BackgroundTasks,
) -> AsyncGenerator[str, None]:
    started_ns = time.perf_counter_ns()
    try:
        async for event in stream_events(query, budget, country, locale):
            if event.get("type") == "results" and isinstance(event.get("data"), dict):
                background_tasks.add_task(
                    observe_live_dark_read,
                    query=query,
                    budget=budget,
                    country=country,
                    locale=locale,
                    core_response=event["data"],
                    core_latency_us=max(
                        0,
                        (time.perf_counter_ns() - started_ns) // 1_000,
                    ),
                    surface="advise_stream",
                )
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
    except GeneratorExit:
        log.info("Client déconnecté pendant le streaming")
    except Exception as exc:
        log.error("Erreur streaming (error_type=%s)", type(exc).__name__)
        yield f'data: {{"type": "error", "message": "Erreur interne"}}\n\n'


@router.get("/advise/stream")
async def advise_stream(
    background_tasks: BackgroundTasks,
    q: str = Query(..., min_length=1, max_length=500, description="Besoin en langage naturel."),
    budget: float | None = Query(default=None, ge=0, le=100000, description="Budget max en euros."),
    country: str | None = Query(default=None, description="Pays : be, be-nl, fr, ch, lu, nl."),
    locale: str = Query(default="fr", description="Langue d'interface : fr, nl ou en."),
) -> StreamingResponse:
    # Validation du pays
    if country and country.lower() not in _VALID_COUNTRIES:
        raise HTTPException(status_code=400, detail=f"Pays non supporté : {country}")
    locale = locale.lower().split("-")[0]
    if locale not in _VALID_LOCALES:
        raise HTTPException(status_code=400, detail=f"Langue non supportée : {locale}")

    log.info("Stream assistant demandé")

    return StreamingResponse(
        _sse(q, budget, country, locale, background_tasks),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
            "X-Content-Type-Options": "nosniff",
        },
    )
