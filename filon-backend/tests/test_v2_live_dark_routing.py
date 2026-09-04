from __future__ import annotations

import json
from unittest.mock import AsyncMock

import pytest
from fastapi import BackgroundTasks

from app.api.routes import advise, stream
from app.schemas.advise import AdviseRequest, AdviseResponse, Criteria


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
