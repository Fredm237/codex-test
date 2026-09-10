"""Endpoint principal : transforme un besoin d'achat en recommandation.

C'est le point d'entrée que le frontend existant appellera.
"""

from __future__ import annotations

import time

from fastapi import APIRouter, BackgroundTasks, Header

from app.agents.orchestrator import advise as run_advise
from app.core.config import get_settings
from app.schemas.advise import AdviseRequest, AdviseResponse
from app.v2_chain.live_dark_reader import observe_live_dark_read
from app.v2_chain.live_router import route_promoted_response, route_v2_only_response

router = APIRouter(tags=["advise"])


@router.post("/advise", response_model=AdviseResponse)
async def advise(
    request: AdviseRequest,
    background_tasks: BackgroundTasks,
    x_filon_v2_subject_digest: str | None = Header(default=None),
) -> AdviseResponse:
    if get_settings().v2_only_public_enabled:
        routed = await route_v2_only_response(
            query=request.query,
            budget=request.budget,
            country=None,
            locale=request.locale,
            surface="advise",
        )
        return AdviseResponse.model_validate(routed.response)

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
    routed = await route_promoted_response(
        core_response=response.model_dump(mode="json"),
        core_latency_us=max(0, (time.perf_counter_ns() - started_ns) // 1_000),
        query=request.query,
        budget=request.budget,
        country=None,
        locale=request.locale,
        surface="advise",
        subject_digest=x_filon_v2_subject_digest,
    )
    if routed.source == "core_v1":
        return response
    return AdviseResponse.model_validate(routed.response)
