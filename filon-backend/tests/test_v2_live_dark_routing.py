from __future__ import annotations

import json
from unittest.mock import AsyncMock

import pytest
from fastapi import BackgroundTasks

from app.api.routes import advise, stream
from app.schemas.advise import AdviseRequest, AdviseResponse, Criteria
from app.v2_chain.live_router import V2LiveRouteResult


@pytest.mark.asyncio
async def test_sse_serves_the_unchanged_v1_result_before_scheduling_dark_read(
    monkeypatch,
) -> None:
    result = {"real": True, "cards": [{"offer_id": 7}]}

    async def events(*_args, **_kwargs):
        yield {"type": "results", "data": result}

    observe = AsyncMock()
    monkeypatch.setattr(stream, "stream_events", events)
    monkeypatch.setattr(stream, "observe_live_dark_read", observe)
    background = BackgroundTasks()

    chunks = [
        value
        async for value in stream._sse(
            "un smartphone",
            500,
            "be",
            "fr",
            background,
        )
    ]

    assert json.loads(chunks[0].removeprefix("data: ")) == {
        "type": "results",
        "data": result,
    }
    observe.assert_not_awaited()
    await background()
    observe.assert_awaited_once()
    assert observe.await_args.kwargs["core_response"] is result
    assert observe.await_args.kwargs["surface"] == "advise_stream"


@pytest.mark.asyncio
async def test_json_advise_response_is_unchanged_and_dark_read_is_backgrounded(
    monkeypatch,
) -> None:
    response = AdviseResponse(
        query="un casque",
        criteria=Criteria(),
        recommendation=None,
        alternatives=[],
        trace=[],
    )
    run = AsyncMock(return_value=response)
    observe = AsyncMock()
    monkeypatch.setattr(advise, "run_advise", run)
    monkeypatch.setattr(advise, "observe_live_dark_read", observe)
    background = BackgroundTasks()
    request = AdviseRequest(query="un casque", budget=200, locale="fr-BE")

    actual = await advise.advise(request, background)

    assert actual is response
    observe.assert_not_awaited()
    await background()
    observe.assert_awaited_once()
    assert observe.await_args.kwargs["surface"] == "advise"
    assert observe.await_args.kwargs["core_response"]["query"] == "un casque"


@pytest.mark.asyncio
async def test_sse_v2_only_never_calls_the_v1_stream(monkeypatch) -> None:
    core = AsyncMock()
    v2 = AsyncMock(
        return_value=V2LiveRouteResult(
            {
                "usage": "une cafetière",
                "offers": 0,
                "cards": [],
                "real": False,
                "currency": None,
                "country": "be",
            },
            "v2",
            "public_v2_only",
            "v2_abstained",
        )
    )
    monkeypatch.setattr(
        stream,
        "get_settings",
        lambda: type("Settings", (), {"v2_only_public_enabled": True})(),
    )
    monkeypatch.setattr(stream, "stream_events", core)
    monkeypatch.setattr(stream, "route_v2_only_response", v2)

    chunks = [
        value
        async for value in stream._sse(
            "une cafetière", None, "be", "fr", BackgroundTasks()
        )
    ]

    assert json.loads(chunks[0].removeprefix("data: "))["data"]["real"] is False
    core.assert_not_called()
    v2.assert_awaited_once()


@pytest.mark.asyncio
async def test_json_advise_v2_only_never_calls_the_v1_orchestrator(
    monkeypatch,
) -> None:
    core = AsyncMock()
    v2 = AsyncMock(
        return_value=V2LiveRouteResult(
            {
                "query": "une cafetière",
                "criteria": {
                    "category": "general",
                    "budget_max": None,
                    "usage": [],
                    "must_have": [],
                    "priorities": [],
                    "keywords": [],
                },
                "recommendation": None,
                "alternatives": [],
                "trace": [],
            },
            "v2",
            "public_v2_only",
            "v2_abstained",
        )
    )
    monkeypatch.setattr(
        advise,
        "get_settings",
        lambda: type("Settings", (), {"v2_only_public_enabled": True})(),
    )
    monkeypatch.setattr(advise, "run_advise", core)
    monkeypatch.setattr(advise, "route_v2_only_response", v2)

    response = await advise.advise(
        AdviseRequest(query="une cafetière", locale="fr-BE"),
        BackgroundTasks(),
    )

    assert response.recommendation is None
    assert response.criteria.category == "general"
    core.assert_not_awaited()
    v2.assert_awaited_once()
