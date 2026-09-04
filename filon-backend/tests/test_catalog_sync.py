"""Journal durable des cycles catalogue : pas de double exécution silencieuse."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import models

from app.db.base import Base
from app.services import catalog_sync


async def _session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    return engine, maker


async def test_a_single_running_sync_is_allowed_and_a_completed_one_becomes_fresh():
    engine, maker = await _session()
    try:
        async with maker() as session:
            run = await catalog_sync.start_run(session, trigger="scheduler")
            assert run is not None
            assert (await catalog_sync.start_run(session, trigger="manual")) is None

            await catalog_sync.finish_run(
                session,
                run,
                status="succeeded",
                merchants=3,
                feeds=4,
                offers=120,
            )
            state = await catalog_sync.health(session, interval_hours=6)

            assert state["status"] == "fresh"
            assert state["last_success"]["offers"] == 120
            assert state["last_success"]["trigger"] == "scheduler"
            assert datetime.fromisoformat(
                state["last_success"]["started_at"]
            ).utcoffset() == UTC.utcoffset(None)
            assert datetime.fromisoformat(
                state["last_success"]["finished_at"]
            ).utcoffset() == UTC.utcoffset(None)
            assert datetime.fromisoformat(
                state["last_success"]["heartbeat_at"]
            ).utcoffset() == UTC.utcoffset(None)
    finally:
        await engine.dispose()


async def test_an_abandoned_running_sync_becomes_recoverable():
    engine, maker = await _session()
    try:
        async with maker() as session:
            stale_run = await catalog_sync.start_run(session, trigger="scheduler")
            assert stale_run is not None
            stale_run.started_at = datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=5)
            stale_run.heartbeat_at = (
                datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=20)
            )
            await session.commit()

            state = await catalog_sync.health(session, interval_hours=6)
            assert state["status"] == "interrupted"
            assert state["recovery_required"] is True
            assert state["age_hours"] >= 5

            resumed_run = await catalog_sync.start_run(session, trigger="scheduler")
            assert resumed_run is not None
            assert resumed_run.id != stale_run.id
            assert resumed_run.resumed_from_run_id == stale_run.id
            assert resumed_run.status == "running"
            assert resumed_run.failure_reason is None
            assert resumed_run.heartbeat_at > stale_run.started_at

            await session.refresh(stale_run)
            assert stale_run.status == "interrupted"
            assert stale_run.failure_reason == "interrupted"
            assert stale_run.finished_at is not None
    finally:
        await engine.dispose()


async def test_a_stale_sync_can_be_interrupted_without_starting_a_successor():
    engine, maker = await _session()
    try:
        async with maker() as session:
            stale_run = await catalog_sync.start_run(session, trigger="scheduler")
            assert stale_run is not None
            stale_run.heartbeat_at = (
                datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=20)
            )
            await session.commit()

            receipt = await catalog_sync.interrupt_stale_run(session)

            assert receipt is not None
            assert receipt["id"] == stale_run.id
            assert receipt["status"] == "interrupted"
            assert receipt["failure_reason"] == "interrupted"
            assert receipt["finished_at"] is not None
            assert await catalog_sync._latest(session, status="running") is None
    finally:
        await engine.dispose()


async def test_a_fresh_sync_cannot_be_interrupted_by_maintenance():
    engine, maker = await _session()
    try:
        async with maker() as session:
            run = await catalog_sync.start_run(session, trigger="scheduler")
            assert run is not None

            assert await catalog_sync.interrupt_stale_run(session) is None
            await session.refresh(run)
            assert run.status == "running"
    finally:
        await engine.dispose()


async def test_a_long_running_sync_with_a_recent_heartbeat_is_not_recovered():
    engine, maker = await _session()
    try:
        async with maker() as session:
            run = await catalog_sync.start_run(session, trigger="scheduler")
            assert run is not None
            run.started_at = datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=8)
            run.heartbeat_at = datetime.now(UTC).replace(tzinfo=None)
            await session.commit()

            state = await catalog_sync.health(session, interval_hours=6)
            assert state["status"] == "syncing"
            assert state["age_hours"] >= 8
            assert state["heartbeat_age_seconds"] < 15
            assert state.get("recovery_required") is None
            assert await catalog_sync.start_run(session, trigger="scheduler") is None
    finally:
        await engine.dispose()


async def test_heartbeat_update_fails_closed_after_ownership_is_lost():
    engine, maker = await _session()
    try:
        async with maker() as session:
            run = await catalog_sync.start_run(session, trigger="scheduler")
            assert run is not None
            await catalog_sync.finish_run(session, run, status="succeeded")

            with pytest.raises(RuntimeError, match="lost ownership"):
                await catalog_sync.touch_run(session, run.id)
            with pytest.raises(RuntimeError, match="lost ownership"):
                await catalog_sync.finish_run(session, run, status="failed")

            await session.refresh(run)
            assert run.status == "succeeded"
    finally:
        await engine.dispose()


async def test_a_failed_first_sync_is_exposed_as_degraded_not_as_fresh():
    engine, maker = await _session()
    try:
        async with maker() as session:
            run = await catalog_sync.start_run(session, trigger="manual")
            assert run is not None
            await catalog_sync.finish_run(
                session,
                run,
                status="failed",
                failure_reason="sync_failed",
            )

            state = await catalog_sync.health(session, interval_hours=6)
            assert state["status"] == "degraded"
            assert state["last_success"] is None
    finally:
        await engine.dispose()


async def test_an_incomplete_first_sync_is_exposed_as_degraded():
    engine, maker = await _session()
    try:
        async with maker() as session:
            run = await catalog_sync.start_run(session, trigger="scheduler")
            assert run is not None
            await catalog_sync.finish_run(
                session,
                run,
                status="degraded",
                feeds=2,
                skipped_feeds=2,
                failure_reason="all_feeds_skipped",
            )

            state = await catalog_sync.health(session, interval_hours=6)
            assert state["status"] == "degraded"
            assert state["last_success"] is None
    finally:
        await engine.dispose()


async def test_run_marks_an_all_skipped_ingestion_degraded(monkeypatch):
    engine, maker = await _session()
    monkeypatch.setattr(
        catalog_sync.awin_catalog,
        "sync_merchants",
        AsyncMock(return_value=3),
    )
    monkeypatch.setattr(
        catalog_sync.awin_catalog,
        "ingest_feeds",
        AsyncMock(return_value={"feeds": 2, "offers": 0, "skipped": 2}),
    )
    monkeypatch.setattr(
        catalog_sync.catalog_grouping,
        "rebuild_products",
        AsyncMock(return_value={"products": 0}),
    )
    try:
        async with maker() as session:
            result = await catalog_sync.run_catalog_sync(
                session,
                trigger="scheduler",
            )

            assert result["started"] is True
            assert result["run"]["status"] == "degraded"
            assert result["run"]["failure_reason"] == "all_feeds_skipped"
            assert (await catalog_sync.health(session, interval_hours=6))["status"] == (
                "degraded"
            )
    finally:
        await engine.dispose()


async def test_run_marks_a_cooperative_feed_stop_interrupted(monkeypatch):
    engine, maker = await _session()
    monkeypatch.setattr(
        catalog_sync.awin_catalog,
        "sync_merchants",
        AsyncMock(return_value=3),
    )
    monkeypatch.setattr(
        catalog_sync.awin_catalog,
        "ingest_feeds",
        AsyncMock(
            return_value={
                "feeds": 1,
                "offers": 20_000,
                "skipped": 0,
                "stopped_after_feed": True,
            }
        ),
    )
    rebuild = AsyncMock(return_value={"products": 0})
    monkeypatch.setattr(catalog_sync.catalog_grouping, "rebuild_products", rebuild)
    try:
        async with maker() as session:
            result = await catalog_sync.run_catalog_sync(
                session,
                trigger="scheduler",
                stop_after_current_feed=True,
            )

            catalog_sync.awin_catalog.ingest_feeds.assert_awaited_once()
            assert (
                catalog_sync.awin_catalog.ingest_feeds.await_args.kwargs[
                    "stop_after_current_feed"
                ]
                is True
            )

            assert result["started"] is True
            assert result["run"]["status"] == "interrupted"
            assert result["run"]["failure_reason"] == "stop_after_current_feed"
            assert result["run"]["feeds"] == 1
            assert result["run"]["offers"] == 20_000
            rebuild.assert_not_awaited()
    finally:
        await engine.dispose()
