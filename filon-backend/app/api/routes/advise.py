"""Endpoint principal : transforme un besoin d'achat en recommandation.

C'est le point d'entrée que le frontend existant appellera.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.agents.orchestrator import advise as run_advise
from app.schemas.advise import AdviseRequest, AdviseResponse

router = APIRouter(tags=["advise"])


@router.post("/advise", response_model=AdviseResponse)
async def advise(request: AdviseRequest) -> AdviseResponse:
    return await run_advise(request)
