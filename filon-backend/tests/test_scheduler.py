from __future__ import annotations

import json
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.ingest import scheduler


def _settings(
    *,
    hours: int,
    key: str | None = "feed-key",
    token: str | None = "api-token",
) -> SimpleNamespace:
    return SimpleNamespace(
        awin_auto_sync_hours=hours,
        awin_feed_api_key=key,
        awin_api_token=token,
        awin_max_decompressed_bytes=512 * 1024 * 1024,
        awin_max_download_bytes=256 * 1024 * 1024,
        awin_max_rows_per_feed=100_000,
        database_schema_mode="alembic",
        debug=False,
    )


@pytest.mark.asyncio
async def test_scheduler_command_refuses_a_disabled_configuration(monkeypatch) -> None:
    prepare = AsyncMock()
    monkeypatch.setattr(scheduler, "get_settings", lambda: _settings(hours=0))
    monkeypatch.setattr(scheduler.db, "prepare_schema", prepare)
    monkeypatch.setattr(scheduler.db, "is_enabled", lambda: True)

    with pytest.raises(RuntimeError, match="AWIN_AUTO_SYNC_HOURS"):
        await scheduler.run_once()
    prepare.assert_not_awaited()


@pytest.mark.asyncio
async def test_scheduler_refuses_missing_merchant_credentials(monkeypatch) -> None:
    monkeypatch.setattr(
        scheduler,
        "get_settings",
        lambda: _settings(hours=6, token=None),
    )

    with pytest.raises(RuntimeError, match="AWIN_API_TOKEN"):
        await scheduler.run_once()


@pytest.mark.asyncio
async def test_scheduler_refuses_missing_feed_credentials(monkeypatch) -> None:
    monkeypatch.setattr(
        scheduler,
        "get_settings",
        lambda: _settings(hours=6, key=None),
    )

    with pytest.raises(RuntimeError, match="AWIN_FEED_API_KEY"):
        await scheduler.run_once()


@pytest.mark.asyncio
async def test_scheduler_refuses_a_missing_database(monkeypatch) -> None:
    monkeypatch.setattr(scheduler, "get_settings", lambda: _settings(hours=6))
    monkeypatch.setattr(scheduler.db, "is_enabled", lambda: False)

    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        await scheduler.run_once()


@pytest.mark.asyncio
async def test_scheduler_refuses_unsafe_ingestion_bounds(monkeypatch) -> None:
    settings = _settings(hours=6)
    settings.awin_max_rows_per_feed = 100_001
    monkeypatch.setattr(scheduler, "get_settings", lambda: settings)
    monkeypatch.setattr(scheduler.db, "is_enabled", lambda: True)

    with pytest.raises(RuntimeError, match="rows-per-feed bound is unsafe"):
        await scheduler.run_once()


@pytest.mark.asyncio
async def test_scheduler_refuses_legacy_schema_mode(monkeypatch) -> None:
    settings = _settings(hours=6)
    settings.database_schema_mode = "legacy"
    monkeypatch.setattr(scheduler, "get_settings", lambda: settings)
    monkeypatch.setattr(scheduler.db, "is_enabled", lambda: True)

    with pytest.raises(RuntimeError, match="DATABASE_SCHEMA_MODE=alembic"):
        await scheduler.run_once()


def _session_scope(session):
    @asynccontextmanager
    async def scope():
        yield session

    return scope


@pytest.mark.asyncio
async def test_scheduler_validates_schema_and_skips_a_fresh_catalog(
    monkeypatch,
) -> None:
    session = object()
    prepare = AsyncMock()
    health = AsyncMock(return_value={"status": "fresh", "age_hours": 1})
    run = AsyncMock()
    monkeypatch.setattr(scheduler, "get_settings", lambda: _settings(hours=6))
    monkeypatch.setattr(scheduler.db, "is_enabled", lambda: True)
    monkeypatch.setattr(scheduler.db, "prepare_schema", prepare)
    monkeypatch.setattr(scheduler.db, "session_scope", _session_scope(session))
    monkeypatch.setattr(scheduler.catalog_sync, "health", health)
    monkeypatch.setattr(scheduler.catalog_sync, "run_catalog_sync", run)

    assert await scheduler.run_once() == "fresh"
    prepare.assert_awaited_once_with()
    health.assert_awaited_once_with(session, interval_hours=6)
    run.assert_not_awaited()


@pytest.mark.asyncio
async def test_scheduler_runs_one_due_cycle_then_exits(monkeypatch) -> None:
    session = object()
    prepare = AsyncMock()
    health = AsyncMock(return_value={"status": "stale", "age_hours": 13})
    run = AsyncMock(return_value={"started": True, "run": {"status": "succeeded"}})
    monkeypatch.setattr(scheduler, "get_settings", lambda: _settings(hours=6))
    monkeypatch.setattr(scheduler.db, "is_enabled", lambda: True)
    monkeypatch.setattr(scheduler.db, "prepare_schema", prepare)
    monkeypatch.setattr(scheduler.db, "session_scope", _session_scope(session))
    monkeypatch.setattr(scheduler.catalog_sync, "health", health)
    monkeypatch.setattr(scheduler.catalog_sync, "run_catalog_sync", run)

    assert await scheduler.run_once() == "succeeded"
    prepare.assert_awaited_once_with()
    run.assert_awaited_once_with(session, trigger="scheduler")


@pytest.mark.asyncio
async def test_scheduler_runs_when_the_interval_is_due_even_if_health_is_tolerant(
    monkeypatch,
) -> None:
    session = object()
    monkeypatch.setattr(scheduler, "get_settings", lambda: _settings(hours=6))
    monkeypatch.setattr(scheduler.db, "is_enabled", lambda: True)
    monkeypatch.setattr(scheduler.db, "prepare_schema", AsyncMock())
    monkeypatch.setattr(scheduler.db, "session_scope", _session_scope(session))
    monkeypatch.setattr(
        scheduler.catalog_sync,
        "health",
        AsyncMock(return_value={"status": "fresh", "age_hours": 6}),
    )
    run = AsyncMock(return_value={"started": True, "run": {"status": "succeeded"}})
    monkeypatch.setattr(scheduler.catalog_sync, "run_catalog_sync", run)

    assert await scheduler.run_once() == "succeeded"
    run.assert_awaited_once_with(session, trigger="scheduler")


@pytest.mark.asyncio
async def test_scheduler_fails_closed_on_an_invalid_sync_outcome(monkeypatch) -> None:
    session = object()
    monkeypatch.setattr(scheduler, "get_settings", lambda: _settings(hours=6))
    monkeypatch.setattr(scheduler.db, "is_enabled", lambda: True)
    monkeypatch.setattr(scheduler.db, "prepare_schema", AsyncMock())
    monkeypatch.setattr(scheduler.db, "session_scope", _session_scope(session))
    monkeypatch.setattr(
        scheduler.catalog_sync,
        "health",
        AsyncMock(return_value={"status": "stale", "age_hours": 12}),
    )
    monkeypatch.setattr(
        scheduler.catalog_sync,
        "run_catalog_sync",
        AsyncMock(return_value={"started": True, "run": {"status": "failed"}}),
    )

    with pytest.raises(RuntimeError, match="invalid sync outcome"):
        await scheduler.run_once()


@pytest.mark.asyncio
async def test_scheduler_preflight_is_read_only_and_returns_a_safe_receipt(
    monkeypatch,
) -> None:
    session = object()
    prepare = AsyncMock()
    health = AsyncMock(return_value={"status": "stale", "age_hours": 12})
    run = AsyncMock()
    monkeypatch.setattr(scheduler, "get_settings", lambda: _settings(hours=6))
    monkeypatch.setattr(scheduler.db, "is_enabled", lambda: True)
    monkeypatch.setattr(scheduler.db, "prepare_schema", prepare)
    monkeypatch.setattr(scheduler.db, "session_scope", _session_scope(session))
    monkeypatch.setattr(scheduler.catalog_sync, "health", health)
    monkeypatch.setattr(scheduler.catalog_sync, "run_catalog_sync", run)

    assert await scheduler.preflight() == {
        "catalog_state": "stale",
        "due": True,
        "interval_hours": 6,
        "schema_revision": scheduler.db.CURRENT_SCHEMA_REVISION,
        "status": "ready",
    }
    prepare.assert_awaited_once_with()
    health.assert_awaited_once_with(session, interval_hours=6)
    run.assert_not_awaited()


def test_scheduler_main_check_prints_machine_readable_receipt(
    monkeypatch,
    capsys,
) -> None:
    receipt = {
        "catalog_state": "fresh",
        "due": False,
        "interval_hours": 6,
        "schema_revision": scheduler.db.CURRENT_SCHEMA_REVISION,
        "status": "ready",
    }
    monkeypatch.setattr(scheduler, "get_settings", lambda: _settings(hours=6))
    monkeypatch.setattr(scheduler, "preflight", AsyncMock(return_value=receipt))

    assert scheduler.main(("--check",)) == 0
    assert json.loads(capsys.readouterr().out) == receipt


def test_scheduler_main_rejects_unknown_arguments() -> None:
    assert scheduler.main(("--write",)) == 2


def test_scheduler_main_sanitizes_configuration_failures(monkeypatch) -> None:
    def invalid_settings():
        raise RuntimeError("invalid settings")

    monkeypatch.setattr(scheduler, "get_settings", invalid_settings)

    assert scheduler.main() == 1
