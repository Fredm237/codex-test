"""Journal durable des cycles catalogue : pas de double exécution silencieuse."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

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
    finally:
        await engine.dispose()


async def test_an_abandoned_running_sync_becomes_recoverable():
    engine, maker = await _session()
    try:
        async with maker() as session:
            stale_run = await catalog_sync.start_run(session, trigger="scheduler")
            assert stale_run is not None
            stale_run.started_at = datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=5)
            await session.commit()

            state = await catalog_sync.health(session, interval_hours=6)
            assert state["status"] == "interrupted"
            assert state["recovery_required"] is True
            assert state["age_hours"] >= 5

            new_run = await catalog_sync.start_run(session, trigger="scheduler")
            assert new_run is not None
            previous = (
                await session.execute(
                    select(models.CatalogSyncRun).where(models.CatalogSyncRun.id == stale_run.id)
                )
            ).scalar_one()
            assert previous.status == "interrupted"
            assert previous.failure_reason == "interrupted"
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
