"""Endpoint principal : transforme un besoin d'achat en recommandation.

C'est le point d'entrée que le frontend existant appellera.
"""

from __future__ import annotations

import time

from fastapi import APIRouter, BackgroundTasks

from app.agents.orchestrator import advise as run_advise
from app.schemas.advise import AdviseRequest, AdviseResponse
from app.v2_chain.live_dark_reader import observe_live_dark_read

router = APIRouter(tags=["advise"])


@router.post("/advise", response_model=AdviseResponse)
async def advise(
    request: AdviseRequest,
    background_tasks: BackgroundTasks,
) -> AdviseResponse:
    started_ns = time.perf_counter_ns()
    response = await run_advise(request)
    background_tasks.add_task(
        observe_live_dark_read,
        query=request.query,
        budget=request.budget,
        country=None,
        locale=request.locale,
        core_response=response.model_dump(mode="json"),
        core_latency_us=max(0, (time.perf_counter_ns() - started_ns) // 1_000),
        surface="advise",
    )
    return response
