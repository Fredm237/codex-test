from __future__ import annotations

import json
from contextlib import asynccontextmanager
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import ANY, AsyncMock

import pytest
from jsonschema import Draft202012Validator
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import models as core_models
from app.db.base import Base
from app.observations.models import RawSourceRecord
from app.v2_chain import scheduler
from app.v2_chain.execution import V2ChainAlreadyRunning
from app.v2_chain.models import V2ChainExecution


CONTRACT_ROOT = Path(__file__).resolve().parents[2] / "contracts" / "v2-chain" / "v1"
SCHEDULE_SCHEMA = json.loads(
    (CONTRACT_ROOT / "shadow-schedule-receipt.schema.json").read_text()
)
SCHEDULE_VALIDATOR = Draft202012Validator(SCHEDULE_SCHEMA)
CAMPAIGN_ID = "sha256:" + "c" * 64


def _settings(*, mode: str = "shadow", canary: bool = False, public: bool = False):
    return SimpleNamespace(
        database_schema_mode="alembic",
        v2_chain_mode=mode,
        v2_chain_stale_after_seconds=14_400,
        v2_chain_campaign_id=CAMPAIGN_ID,
        v2_canary_reader_enabled=canary,
        v2_public_reader_enabled=public,
        debug=False,
    )


def _session_scope(session):
    @asynccontextmanager
    async def scope():
        yield session

    return scope


def _configure(monkeypatch, *, session=object()) -> None:
    monkeypatch.setattr(scheduler, "get_settings", lambda: _settings())
    monkeypatch.setattr(scheduler.db, "is_enabled", lambda: True)
    monkeypatch.setattr(scheduler.db, "prepare_schema", AsyncMock())
    monkeypatch.setattr(scheduler.db, "session_scope", _session_scope(session))
    monkeypatch.setattr(scheduler, "_active_v2_lease", AsyncMock(return_value={}))
    monkeypatch.setattr(
        scheduler,
        "_latest_terminal_recovery",
        AsyncMock(return_value=None),
    )


@pytest.mark.asyncio
async def test_preflight_is_read_only_and_reports_due_work(monkeypatch) -> None:
    _configure(monkeypatch)
    monkeypatch.setattr(scheduler, "next_after_raw_id", AsyncMock(return_value=20))
    monkeypatch.setattr(scheduler, "_latest_awin_raw_id", AsyncMock(return_value=45))
    monkeypatch.setattr(scheduler, "_catalog_sync_active", AsyncMock(return_value=False))
    monkeypatch.setattr(scheduler, "_v2_chain_active", AsyncMock(return_value=False))
    run = AsyncMock()
    monkeypatch.setattr(scheduler, "run_journaled_v2_shadow_chain", run)

    receipt = await scheduler.preflight(vertical="smartphones", limit=25)

    assert receipt.status == "due"
    assert receipt.due is True
    assert receipt.after_raw_id == 20
    assert receipt.latest_raw_id == 45
    SCHEDULE_VALIDATOR.validate(asdict(receipt))
    run.assert_not_awaited()
    scheduler.next_after_raw_id.assert_awaited_once_with(
        ANY,
        vertical="smartphones",
        campaign_id=CAMPAIGN_ID,
    )


@pytest.mark.asyncio
async def test_preflight_reports_active_lease_heartbeat_without_mutation(
    monkeypatch,
) -> None:
    _configure(monkeypatch)
    monkeypatch.setattr(scheduler, "next_after_raw_id", AsyncMock(return_value=20))
    monkeypatch.setattr(scheduler, "_latest_awin_raw_id", AsyncMock(return_value=45))
    monkeypatch.setattr(scheduler, "_catalog_sync_active", AsyncMock(return_value=False))
    monkeypatch.setattr(scheduler, "_v2_chain_active", AsyncMock(return_value=True))
    lease = {
        "active_execution_id": 9,
        "active_heartbeat_at": "2026-09-04T00:00:00Z",
        "heartbeat_age_seconds": 14_401,
        "stale_recovery_eligible": True,
    }
    inspect = AsyncMock(return_value=lease)
    monkeypatch.setattr(scheduler, "_active_v2_lease", inspect)
    run = AsyncMock()
    interrupt = AsyncMock()
    monkeypatch.setattr(scheduler, "run_journaled_v2_shadow_chain", run)
    monkeypatch.setattr(scheduler, "interrupt_stale_execution", interrupt)

    receipt = await scheduler.preflight(vertical="smartphones", limit=25)

    assert receipt.status == "v2_running"
    assert receipt.active_execution_id == 9
    assert receipt.active_heartbeat_at == "2026-09-04T00:00:00Z"
    assert receipt.heartbeat_age_seconds == 14_401
    assert receipt.stale_recovery_eligible is True
    SCHEDULE_VALIDATOR.validate(asdict(receipt))
    inspect.assert_awaited_once_with(ANY, stale_after_seconds=14_400)
    run.assert_not_awaited()
    interrupt.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("catalog_active", "v2_active", "latest", "expected"),
    (
        (True, False, 45, "catalog_syncing"),
        (False, True, 45, "v2_running"),
        (False, False, 20, "fresh"),
    ),
)
async def test_run_skips_when_upstream_or_lease_is_not_ready(
    monkeypatch,
    catalog_active: bool,
    v2_active: bool,
    latest: int,
    expected: str,
) -> None:
    _configure(monkeypatch)
    monkeypatch.setattr(scheduler, "next_after_raw_id", AsyncMock(return_value=20))
    monkeypatch.setattr(scheduler, "_latest_awin_raw_id", AsyncMock(return_value=latest))
    monkeypatch.setattr(
        scheduler,
        "_catalog_sync_active",
        AsyncMock(return_value=catalog_active),
    )
    monkeypatch.setattr(
        scheduler,
        "_v2_chain_active",
        AsyncMock(return_value=v2_active),
    )
    run = AsyncMock()
    monkeypatch.setattr(scheduler, "run_journaled_v2_shadow_chain", run)

    receipt = await scheduler.run_once(vertical="smartphones", limit=25)

    assert receipt.status == expected
    run.assert_not_awaited()


@pytest.mark.asyncio
async def test_run_executes_one_bounded_apply(monkeypatch) -> None:
    session = object()
    _configure(monkeypatch, session=session)
    monkeypatch.setattr(scheduler, "next_after_raw_id", AsyncMock(return_value=20))
    monkeypatch.setattr(scheduler, "_latest_awin_raw_id", AsyncMock(return_value=45))
    monkeypatch.setattr(scheduler, "_catalog_sync_active", AsyncMock(return_value=False))
    monkeypatch.setattr(scheduler, "_v2_chain_active", AsyncMock(return_value=False))
    report = SimpleNamespace(execution_id=7, evaluation_id="sha256:" + "a" * 64)
    run = AsyncMock(return_value=report)
    monkeypatch.setattr(scheduler, "run_journaled_v2_shadow_chain", run)

    receipt = await scheduler.run_once(vertical="smartphones", limit=25)

    assert receipt.status == "succeeded"
    assert receipt.execution_id == 7
    assert receipt.evaluation_id == report.evaluation_id
    SCHEDULE_VALIDATOR.validate(asdict(receipt))
    kwargs = run.await_args.kwargs
    assert kwargs["vertical"] == "smartphones"
    assert kwargs["after_raw_id"] == 20
    assert kwargs["limit"] == 25
    assert kwargs["apply"] is True
    assert kwargs["evaluated_at"].tzinfo is not None


@pytest.mark.asyncio
async def test_run_resumes_interrupted_window_with_original_identity(
    monkeypatch,
) -> None:
    session = object()
    _configure(monkeypatch, session=session)
    checkpoints = {
        "ontology_snapshot_id": 11,
        "hybrid_run_id": 12,
        "constraint_run_id": 13,
        "ranking_run_id": 14,
        "optimization_run_id": 15,
        "confidence_run_id": 16,
    }
    interrupted_at = datetime(2026, 9, 4, 1, tzinfo=timezone.utc)
    recovery = SimpleNamespace(
        id=8,
        status="interrupted",
        row_limit=17,
        evaluated_at=interrupted_at.replace(tzinfo=None),
        checkpoints_json=checkpoints,
    )
    monkeypatch.setattr(
        scheduler,
        "_state",
        AsyncMock(return_value=("v2_resume_due", 20, 45)),
    )
    monkeypatch.setattr(
        scheduler,
        "_latest_terminal_recovery",
        AsyncMock(return_value=recovery),
    )
    report = SimpleNamespace(execution_id=9, evaluation_id="sha256:" + "a" * 64)
    run = AsyncMock(return_value=report)
    monkeypatch.setattr(scheduler, "run_journaled_v2_shadow_chain", run)

    receipt = await scheduler.run_once(vertical="smartphones", limit=25)

    assert receipt.status == "succeeded"
    assert receipt.row_limit == 17
    assert receipt.recovery_source_execution_id == 8
    kwargs = run.await_args.kwargs
    assert kwargs["evaluated_at"] == interrupted_at
    assert kwargs["limit"] == 17
    assert kwargs["checkpoints"] == scheduler.V2ChainCheckpoints(**checkpoints)
    SCHEDULE_VALIDATOR.validate(asdict(receipt))


@pytest.mark.asyncio
async def test_failed_window_requires_operator_and_is_not_restarted(
    monkeypatch,
) -> None:
    _configure(monkeypatch)
    monkeypatch.setattr(scheduler, "next_after_raw_id", AsyncMock(return_value=20))
    monkeypatch.setattr(scheduler, "_latest_awin_raw_id", AsyncMock(return_value=45))
    monkeypatch.setattr(scheduler, "_catalog_sync_active", AsyncMock(return_value=False))
    monkeypatch.setattr(scheduler, "_v2_chain_active", AsyncMock(return_value=False))
    failure = SimpleNamespace(id=7, status="failed")
    monkeypatch.setattr(
        scheduler,
        "_latest_terminal_recovery",
        AsyncMock(return_value=failure),
    )
    run = AsyncMock()
    monkeypatch.setattr(scheduler, "run_journaled_v2_shadow_chain", run)

    receipt = await scheduler.run_once(vertical="smartphones", limit=25)

    assert receipt.status == "v2_failed"
    assert receipt.recovery_source_execution_id == 7
    SCHEDULE_VALIDATOR.validate(asdict(receipt))
    run.assert_not_awaited()


@pytest.mark.asyncio
async def test_racing_scheduler_returns_running_without_second_execution(
    monkeypatch,
) -> None:
    _configure(monkeypatch)
    monkeypatch.setattr(scheduler, "next_after_raw_id", AsyncMock(return_value=20))
    monkeypatch.setattr(scheduler, "_latest_awin_raw_id", AsyncMock(return_value=45))
    monkeypatch.setattr(scheduler, "_catalog_sync_active", AsyncMock(return_value=False))
    monkeypatch.setattr(scheduler, "_v2_chain_active", AsyncMock(return_value=False))
    monkeypatch.setattr(
        scheduler,
        "run_journaled_v2_shadow_chain",
        AsyncMock(side_effect=V2ChainAlreadyRunning("occupied")),
    )

    receipt = await scheduler.run_once(vertical="smartphones", limit=25)

    assert receipt.status == "v2_running"
    assert receipt.execution_id is None


@pytest.mark.asyncio
async def test_explicit_recovery_interrupts_stale_lease_without_successor(
    monkeypatch,
) -> None:
    _configure(monkeypatch)
    monkeypatch.setattr(scheduler, "next_after_raw_id", AsyncMock(return_value=20))
    monkeypatch.setattr(scheduler, "_latest_awin_raw_id", AsyncMock(return_value=45))
    monkeypatch.setattr(scheduler, "_catalog_sync_active", AsyncMock(return_value=False))
    monkeypatch.setattr(scheduler, "_v2_chain_active", AsyncMock(return_value=True))
    interrupt = AsyncMock(return_value=1)
    monkeypatch.setattr(scheduler, "interrupt_stale_execution", interrupt)
    run = AsyncMock()
    monkeypatch.setattr(scheduler, "run_journaled_v2_shadow_chain", run)

    receipt = await scheduler.interrupt_stale_once(
        vertical="smartphones",
        limit=25,
    )

    assert receipt.status == "v2_interrupted"
    assert receipt.due is True
    SCHEDULE_VALIDATOR.validate(asdict(receipt))
    stale_before = interrupt.await_args.kwargs["stale_before"]
    assert stale_before.tzinfo is not None
    run.assert_not_awaited()


@pytest.mark.asyncio
async def test_explicit_recovery_preserves_fresh_lease(monkeypatch) -> None:
    _configure(monkeypatch)
    monkeypatch.setattr(scheduler, "next_after_raw_id", AsyncMock(return_value=20))
    monkeypatch.setattr(scheduler, "_latest_awin_raw_id", AsyncMock(return_value=45))
    monkeypatch.setattr(scheduler, "_catalog_sync_active", AsyncMock(return_value=False))
    monkeypatch.setattr(scheduler, "_v2_chain_active", AsyncMock(return_value=True))
    interrupt = AsyncMock(return_value=0)
    monkeypatch.setattr(scheduler, "interrupt_stale_execution", interrupt)

    receipt = await scheduler.interrupt_stale_once(
        vertical="smartphones",
        limit=25,
    )

    assert receipt.status == "v2_running"
    interrupt.assert_awaited_once()


@pytest.mark.asyncio
async def test_explicit_recovery_does_not_touch_lease_while_catalog_writes(
    monkeypatch,
) -> None:
    _configure(monkeypatch)
    monkeypatch.setattr(scheduler, "next_after_raw_id", AsyncMock(return_value=20))
    monkeypatch.setattr(scheduler, "_latest_awin_raw_id", AsyncMock(return_value=45))
    monkeypatch.setattr(scheduler, "_catalog_sync_active", AsyncMock(return_value=True))
    monkeypatch.setattr(scheduler, "_v2_chain_active", AsyncMock(return_value=True))
    interrupt = AsyncMock()
    monkeypatch.setattr(scheduler, "interrupt_stale_execution", interrupt)

    receipt = await scheduler.interrupt_stale_once(
        vertical="smartphones",
        limit=25,
    )

    assert receipt.status == "catalog_syncing"
    interrupt.assert_not_awaited()


@pytest.mark.parametrize(
    ("settings", "vertical", "limit", "message"),
    (
        (_settings(mode="off"), "smartphones", 25, "active V2_CHAIN_MODE"),
        (_settings(), "unknown", 25, "vertical is unsupported"),
        (_settings(), "smartphones", 101, "limit must be between"),
    ),
)
def test_configuration_fails_closed(settings, vertical, limit, message, monkeypatch) -> None:
    monkeypatch.setattr(scheduler, "get_settings", lambda: settings)
    monkeypatch.setattr(scheduler.db, "is_enabled", lambda: True)

    with pytest.raises(RuntimeError, match=message):
        scheduler._validate_configuration(vertical, limit)


@pytest.mark.parametrize("mode", ["shadow", "dark", "canary", "public"])
def test_scheduler_keeps_writers_active_through_promoted_modes(
    mode: str,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        scheduler,
        "get_settings",
        lambda: _settings(
            mode=mode,
            canary=mode == "canary",
            public=mode == "public",
        ),
    )
    monkeypatch.setattr(scheduler.db, "is_enabled", lambda: True)

    scheduler._validate_configuration("smartphones", 25)


def test_main_prints_a_machine_readable_safe_receipt(monkeypatch, capsys) -> None:
    receipt = scheduler.V2ScheduleReceipt(
        schema_version="v2-shadow-schedule-receipt/v1",
        status="fresh",
        vertical="smartphones",
        row_limit=25,
        after_raw_id=45,
        latest_raw_id=45,
        due=False,
    )
    monkeypatch.setattr(scheduler, "get_settings", lambda: _settings())
    preflight = AsyncMock(return_value=receipt)
    monkeypatch.setattr(scheduler, "preflight", preflight)

    assert scheduler.main(["--vertical", "smartphones", "--limit", "25", "--check"]) == 0
    assert json.loads(capsys.readouterr().out) == asdict(receipt)
    preflight.assert_awaited_once_with(vertical="smartphones", limit=25)


def test_main_routes_explicit_stale_recovery(monkeypatch, capsys) -> None:
    receipt = scheduler.V2ScheduleReceipt(
        schema_version="v2-shadow-schedule-receipt/v1",
        status="v2_interrupted",
        vertical="smartphones",
        row_limit=25,
        after_raw_id=20,
        latest_raw_id=45,
        due=True,
    )
    monkeypatch.setattr(scheduler, "get_settings", lambda: _settings())
    recover = AsyncMock(return_value=receipt)
    monkeypatch.setattr(scheduler, "interrupt_stale_once", recover)

    assert scheduler.main(
        ["--vertical", "smartphones", "--limit", "25", "--interrupt-stale"]
    ) == 0
    assert json.loads(capsys.readouterr().out) == asdict(receipt)
    recover.assert_awaited_once_with(vertical="smartphones", limit=25)


def test_main_refuses_check_and_recovery_together(monkeypatch, capsys) -> None:
    monkeypatch.setattr(scheduler, "get_settings", lambda: _settings())

    assert scheduler.main(
        ["--vertical", "smartphones", "--check", "--interrupt-stale"]
    ) == 1
    assert json.loads(capsys.readouterr().out) == {
        "error_type": "RuntimeError",
        "status": "refused",
    }


def test_shadow_schedule_contract_and_examples_are_valid() -> None:
    Draft202012Validator.check_schema(SCHEDULE_SCHEMA)
    manifest = json.loads((CONTRACT_ROOT / "manifest.json").read_text())

    assert manifest["shadow_schedule_receipt_schema"] == (
        "shadow-schedule-receipt.schema.json"
    )
    for relative_path in manifest["shadow_schedule_receipt_examples"]:
        SCHEDULE_VALIDATOR.validate(
            json.loads((CONTRACT_ROOT / relative_path).read_text())
        )


@pytest.mark.asyncio
async def test_real_state_queries_block_catalog_and_keep_vertical_cursors() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with sessions() as session:
            session.add(
                RawSourceRecord(
                    source_type="awin_feed",
                    source_ref="awin-feed:1201",
                    source_record_key="1201:continuous-v2",
                    schema_version="awin-create-a-feed-v1",
                    context_json={"merchant_id": 1201},
                    payload_json={"name": "Bounded source"},
                    payload_checksum="a" * 64,
                    replay_key="b" * 64,
                    observed_at=scheduler.datetime(2026, 9, 3),
                )
            )
            session.add(
                core_models.CatalogSyncRun(
                    trigger="scheduler",
                    status="running",
                    heartbeat_at=scheduler.datetime(2026, 9, 3),
                )
            )
            session.add(
                V2ChainExecution(
                    execution_key="c" * 64,
                    mode="apply",
                    status="succeeded",
                    evaluated_at=scheduler.datetime(2026, 9, 3),
                    vertical="audio",
                    after_raw_id=0,
                    row_limit=1,
                    last_raw_source_id=1,
                    checkpoints_json={},
                    completed_stages_json=[],
                    campaign_id=CAMPAIGN_ID,
                    execution_kind="progression",
                    heartbeat_at=scheduler.datetime(2026, 9, 3),
                    finished_at=scheduler.datetime(2026, 9, 3),
                )
            )
            await session.commit()

            assert await scheduler._state(
                session, vertical="smartphones", campaign_id=CAMPAIGN_ID
            ) == (
                "catalog_syncing",
                0,
                1,
            )

            catalog = await session.get(core_models.CatalogSyncRun, 1)
            assert catalog is not None
            catalog.status = "succeeded"
            await session.commit()

            assert await scheduler._state(
                session, vertical="smartphones", campaign_id=CAMPAIGN_ID
            ) == (
                "due",
                0,
                1,
            )
            assert await scheduler._state(
                session, vertical="audio", campaign_id=CAMPAIGN_ID
            ) == (
                "fresh",
                1,
                1,
            )
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_real_active_lease_observation_reports_staleness() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    try:
        heartbeat = datetime.now(timezone.utc) - timedelta(hours=2)
        async with sessions() as session:
            session.add(
                V2ChainExecution(
                    execution_key="d" * 64,
                    mode="apply",
                    status="running",
                    evaluated_at=heartbeat.replace(tzinfo=None),
                    vertical="smartphones",
                    after_raw_id=0,
                    row_limit=1,
                    last_raw_source_id=0,
                    checkpoints_json={},
                    completed_stages_json=[],
                    heartbeat_at=heartbeat.replace(tzinfo=None),
                )
            )
            await session.commit()

            lease = await scheduler._active_v2_lease(
                session,
                stale_after_seconds=3_600,
            )

            assert lease["active_execution_id"] == 1
            assert lease["active_heartbeat_at"].endswith("Z")
            assert lease["heartbeat_age_seconds"] >= 7_199
            assert lease["stale_recovery_eligible"] is True
    finally:
        await engine.dispose()
