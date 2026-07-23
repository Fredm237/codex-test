"""Endpoint de streaming (SSE) de l'assistant d'achat.

Le frontend (SearchAssistant) lit ce flux et allume son UI à l'identique : il
attend des événements JSON ``{type: step|step-done|results}``, exactement ceux
produits par ``recommend.stream_events``.
"""

from __future__ import annotations

import json
from typing import AsyncGenerator

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from app.services.recommend import stream_events

router = APIRouter(tags=["advise"])


async def _sse(query: str, budget: float | None) -> AsyncGenerator[str, None]:
    async for event in stream_events(query, budget):
        yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


@router.get("/advise/stream")
async def advise_stream(
    q: str = Query(..., min_length=1, description="Besoin en langage naturel."),
    budget: float | None = Query(default=None, description="Budget max en euros."),
) -> StreamingResponse:
    return StreamingResponse(
        _sse(q, budget),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # désactive le buffering (nginx/proxies)
        },
    )
