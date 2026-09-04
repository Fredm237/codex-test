from __future__ import annotations

from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
from app.v2_chain import live_dark_reader
from app.v2_chain.canary import V2CanaryPayload
from app.v2_chain.models import V2LiveDarkReadObservation


def test_vertical_inference_is_explicit_and_ambiguous_queries_are_unsupported() -> None:
    assert live_dark_reader.infer_supported_vertical("Un laptop étudiant") == "laptops"
    assert live_dark_reader.infer_supported_vertical("Des pneus hiver") == "tyres"
    assert live_dark_reader.infer_supported_vertical("Un laptop et un casque") is None
    assert live_dark_reader.infer_supported_vertical("Un cadeau utile") is None


def test_core_summary_never_retains_cards() -> None:
    summary = live_dark_reader.summarize_core_response(
        {"real": True, "cards": [{"offer_id": 1}, {"offer_id": 2}]}
    )

    assert summary.outcome == "CANDIDATES"
    assert summary.candidate_count == 2
    assert "cards" not in summary.__dict__


@pytest.mark.asyncio
async def test_off_mode_does_not_open_a_database_session(monkeypatch) -> None:
    monkeypatch.setattr(
        live_dark_reader,
        "get_settings",
        lambda: SimpleNamespace(v2_chain_mode="off"),
    )
    scope = AsyncMock()
    monkeypatch.setattr(live_dark_reader.db, "session_scope", scope)

    report = await live_dark_reader.observe_live_dark_read(
        query="ordinateur portable",
        budget=800,
        country="be",
        locale="fr",
        core_response={"cards": []},
        core_latency_us=10,
        surface="advise_stream",
    )

    assert report.status == "off"
    scope.assert_not_called()


@pytest.mark.asyncio
async def test_real_dark_read_persists_only_aggregate_comparison(monkeypatch) -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)

    @asynccontextmanager
    async def scope():
        async with sessions() as session:
            yield session

    monkeypatch.setattr(
        live_dark_reader,
        "get_settings",
        lambda: SimpleNamespace(
            v2_chain_mode="dark",
            v2_chain_campaign_id="sha256:" + "c" * 64,
        ),
    )
    monkeypatch.setattr(live_dark_reader.db, "session_scope", scope)
    read = AsyncMock(
        return_value=V2CanaryPayload(
            response={
                "outcome": "ABSTAIN",
                "items": [],
                "query_digest": "sha256:" + "f" * 64,
            },
            chain_complete=True,
            safety_state="ABSTAIN",
            provenance_complete=True,
            response_type="ABSTAIN",
        )
    )
    monkeypatch.setattr(live_dark_reader, "read_v2_online", read)
    raw_query = "ordinateur portable pour étudiant 800 euros"

    try:
        report = await live_dark_reader.observe_live_dark_read(
            query=raw_query,
            budget=800,
            country="be",
            locale="fr-BE",
            core_response={"real": True, "cards": [{"offer_id": 42}]},
            core_latency_us=1234,
            surface="advise_stream",
        )

        assert report.status == "recorded"
        assert report.classification == "AMBIGUOUS"
        read.assert_awaited_once()
        request = read.await_args.args[1]
        assert request.query == raw_query
        assert request.vertical == "laptops"
        assert request.country_code == "BE"
        assert request.budget_currency == "EUR"

        async with sessions() as session:
            stored = await session.scalar(select(V2LiveDarkReadObservation))
            assert stored is not None
            assert stored.core_outcome == "CANDIDATES"
            assert stored.v2_outcome == "ABSTAIN"
            assert stored.classification == "AMBIGUOUS"
            assert stored.core_candidate_count == 1
            assert stored.raw_query_retained is False
            assert raw_query not in repr(stored.__dict__)
            assert "query_digest" not in stored.__dict__
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_unsupported_real_query_is_recorded_without_running_v2(monkeypatch) -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)

    @asynccontextmanager
    async def scope():
        async with sessions() as session:
            yield session

    monkeypatch.setattr(
        live_dark_reader,
        "get_settings",
        lambda: SimpleNamespace(
            v2_chain_mode="dark",
            v2_chain_campaign_id="sha256:" + "c" * 64,
        ),
    )
    monkeypatch.setattr(live_dark_reader.db, "session_scope", scope)
    read = AsyncMock()
    monkeypatch.setattr(live_dark_reader, "read_v2_online", read)

    try:
        report = await live_dark_reader.observe_live_dark_read(
            query="un cadeau utile",
            budget=None,
            country=None,
            locale="fr",
            core_response={"cards": []},
            core_latency_us=50,
            surface="advise_stream",
        )

        assert report.classification == "V2_UNSUPPORTED"
        read.assert_not_awaited()
        async with sessions() as session:
            stored = await session.scalar(select(V2LiveDarkReadObservation))
            assert stored is not None
            assert stored.vertical is None
            assert stored.safety_state == "UNSUPPORTED"
    finally:
        await engine.dispose()
