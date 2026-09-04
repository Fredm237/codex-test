"""Qualification de l'orchestrateur shadow atomique P0/P1–P10."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import models as core_models
from app.db.base import Base
from app.observations.models import Observation, RawSourceRecord
from app.v2_chain import execution as v2_execution
from app.v2_chain import scheduler as v2_scheduler
from app.v2_chain.execution import (
    V2ChainAlreadyRunning,
    interrupt_stale_execution,
    next_after_raw_id,
    run_journaled_v2_shadow_chain,
)
from app.v2_chain.models import V2ChainExecution
from app.v2_chain.orchestrator import _parser, run_v2_shadow_chain


EVALUATED_AT = datetime(2026, 9, 2, 8, tzinfo=timezone.utc)
ROUTES_ROOT = Path(__file__).resolve().parents[1] / "app" / "api" / "routes"


async def _seed(session) -> None:
    merchant = core_models.Merchant(
        awin_mid=1201,
        name="V2 Chain Merchant",
        slug="v2-chain-merchant",
        joined=True,
    )
    session.add(merchant)
    await session.flush()
    offer = core_models.Offer(
        merchant_id=merchant.id,
        awin_product_id="v2-chain-1",
        name="Acme Smartphone Prime 128GB",
        brand="Acme",
        price=599,
        currency="EUR",
        in_stock=True,
        is_canonical=True,
        is_adult=False,
    )
    session.add(offer)
    await session.flush()
    raw = RawSourceRecord(
        source_type="awin_feed",
        source_ref="awin-feed:1201",
        source_record_key="1201:v2-chain-1",
        schema_version="awin-create-a-feed-v1",
        context_json={"merchant_id": merchant.id},
        payload_json={
            "ean": "4006381333931",
            "brand_name": "Acme",
            "product_name": "Acme Smartphone Prime 128GB",
            "name": "Acme Smartphone Prime 128GB",
            "offer_kind": "physical_product",
            "search_price": "599.00",
            "currency": "EUR",
            "in_stock": "yes",
        },
        payload_checksum="a" * 64,
        replay_key="b" * 64,
        observed_at=datetime(2026, 9, 2, 7),
    )
    session.add(raw)
    await session.flush()
    session.add(
        Observation(
            raw_source_record_id=raw.id,
            subject_type="offer",
            subject_ref=f"offer:{offer.id}",
            offer_id=offer.id,
            field="name",
            value_json=offer.name,
            status="verified",
            source_type="awin_feed",
            source_ref=raw.source_ref,
            observed_at=raw.observed_at,
            transformation="test",
            transformation_version="v1",
            confidence=1.0,
        )
    )
    await session.commit()


@pytest.mark.asyncio
async def test_atomic_chain_apply_and_identical_replay_are_idempotent() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with sessions() as session:
            await _seed(session)
            first = await run_v2_shadow_chain(
                session,
                evaluated_at=EVALUATED_AT,
                vertical="smartphones",
                limit=1,
                apply=True,
            )
            replay = await run_v2_shadow_chain(
                session,
                evaluated_at=EVALUATED_AT,
                vertical="smartphones",
                limit=1,
                apply=True,
                checkpoints=first.checkpoints,
            )

            assert first.stages["product_identity"]["links_created"] == 1
            assert replay.stages["product_identity"]["links_created"] == 0
            assert replay.stages["product_identity"]["links_existing"] == 1
            assert first.stages["hybrid_retrieval"]["runs_created"] == 1
            assert replay.stages["hybrid_retrieval"]["runs_existing"] == 1
            assert first.stages["buy_wait"]["runs_created"] == 1
            assert replay.stages["buy_wait"]["runs_existing"] == 1
            assert first.stages["buy_wait"]["abstained_runs"] == 1
            assert first.evaluation_id == replay.evaluation_id
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_chain_window_and_timezone_fail_closed() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with sessions() as session:
            with pytest.raises(ValueError, match="timezone"):
                await run_v2_shadow_chain(
                    session,
                    evaluated_at=datetime(2026, 9, 2),
                    vertical="smartphones",
                )
            with pytest.raises(ValueError, match="limit"):
                await run_v2_shadow_chain(
                    session,
                    evaluated_at=EVALUATED_AT,
                    vertical="smartphones",
                    limit=101,
                )
    finally:
        await engine.dispose()


def test_only_non_influential_live_dark_reader_is_wired_to_public_routes() -> None:
    public_routes = "\n".join(
        path.read_text(encoding="utf-8") for path in ROUTES_ROOT.glob("*.py")
    )

    assert "app.v2_chain.live_dark_reader" in public_routes
    assert "app.v2_chain.canary" not in public_routes
    assert "app.v2_chain.online_reader" not in public_routes
    assert "V2CanaryPayload" not in public_routes
    assert "V2ChainExecution" not in public_routes


def test_scheduled_command_requires_atomic_cursor_and_runtime_timestamp() -> None:
    args = _parser().parse_args(
        [
            "--evaluated-at-now",
            "--vertical",
            "smartphones",
            "--continue-after-last-success",
            "--limit",
            "100",
            "--apply",
        ]
    )

    assert args.evaluated_at_now is True
    assert args.continue_after_last_success is True
    assert args.after_raw_id == 0
    assert args.limit == 100
    assert args.apply is True


@pytest.mark.asyncio
async def test_journaled_chain_records_terminal_success_and_all_stages() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with sessions() as session:
            await _seed(session)
            report = await run_journaled_v2_shadow_chain(
                session,
                evaluated_at=EVALUATED_AT,
                vertical="smartphones",
                limit=1,
                apply=True,
                campaign_id="sha256:" + "d" * 64,
                execution_kind="progression",
            )
            execution = await session.scalar(select(V2ChainExecution))

            assert execution is not None
            assert execution.status == "succeeded"
            assert execution.finished_at is not None
            assert execution.failure_reason is None
            assert execution.report_evaluation_id == report.evaluation_id
            assert execution.completed_stages_json == list(report.stages)
            assert report.execution_id == execution.id
            assert execution.last_raw_source_id == 1
            assert execution.campaign_id == "sha256:" + "d" * 64
            assert execution.execution_kind == "progression"
            assert execution.window_metrics_json["records_scanned"] == 1
            assert execution.window_metrics_json["evaluation_identity"] == report.evaluation_id
            assert execution.window_metrics_json["errors"] == 0
            assert await next_after_raw_id(session) == 1
            assert await next_after_raw_id(
                session,
                vertical="smartphones",
                campaign_id="sha256:" + "d" * 64,
            ) == 1
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_continuous_cursor_is_isolated_by_vertical() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with sessions() as session:
            for index, (vertical, cursor) in enumerate(
                (("smartphones", 40), ("audio", 17)),
                start=1,
            ):
                session.add(
                    V2ChainExecution(
                        execution_key=str(index) * 64,
                        mode="apply",
                        status="succeeded",
                        evaluated_at=EVALUATED_AT.replace(tzinfo=None),
                        vertical=vertical,
                        after_raw_id=0,
                        row_limit=1,
                        last_raw_source_id=cursor,
                        checkpoints_json={
                            "ontology_snapshot_id": 0,
                            "hybrid_run_id": 0,
                            "constraint_run_id": 0,
                            "ranking_run_id": 0,
                            "optimization_run_id": 0,
                            "confidence_run_id": 0,
                        },
                        completed_stages_json=[],
                        report_evaluation_id="sha256:" + str(index) * 64,
                        heartbeat_at=EVALUATED_AT.replace(tzinfo=None),
                        finished_at=EVALUATED_AT.replace(tzinfo=None),
                    )
                )
            await session.commit()

            assert await next_after_raw_id(session, vertical="smartphones") == 40
            assert await next_after_raw_id(session, vertical="audio") == 17
            assert await next_after_raw_id(session, vertical="tyres") == 0
            assert await next_after_raw_id(session) == 17
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_late_replay_cannot_regress_a_campaign_cursor() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    campaign = "sha256:" + "e" * 64
    try:
        async with sessions() as session:
            progression = V2ChainExecution(
                execution_key="a" * 64,
                mode="apply",
                status="succeeded",
                evaluated_at=EVALUATED_AT.replace(tzinfo=None),
                vertical="smartphones",
                after_raw_id=30,
                row_limit=10,
                last_raw_source_id=40,
                checkpoints_json={},
                completed_stages_json=[],
                report_evaluation_id="sha256:" + "1" * 64,
                campaign_id=campaign,
                execution_kind="progression",
                window_metrics_json={},
                heartbeat_at=EVALUATED_AT.replace(tzinfo=None),
                finished_at=EVALUATED_AT.replace(tzinfo=None),
            )
            session.add(progression)
            await session.flush()
            session.add(
                V2ChainExecution(
                    execution_key="b" * 64,
                    mode="apply",
                    status="succeeded",
                    evaluated_at=EVALUATED_AT.replace(tzinfo=None),
                    vertical="smartphones",
                    after_raw_id=0,
                    row_limit=10,
                    last_raw_source_id=10,
                    checkpoints_json={},
                    completed_stages_json=[],
                    report_evaluation_id="sha256:" + "2" * 64,
                    campaign_id=campaign,
                    execution_kind="replay",
                    source_execution_id=progression.id,
                    window_metrics_json={},
                    heartbeat_at=EVALUATED_AT.replace(tzinfo=None),
                    finished_at=EVALUATED_AT.replace(tzinfo=None),
                )
            )
            await session.commit()

            assert await next_after_raw_id(
                session,
                vertical="smartphones",
                campaign_id=campaign,
            ) == 40
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_invalid_request_creates_no_execution_journal() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with sessions() as session:
            with pytest.raises(ValueError, match="timezone"):
                await run_journaled_v2_shadow_chain(
                    session,
                    evaluated_at=EVALUATED_AT.replace(tzinfo=None),
                    vertical="smartphones",
                )
            assert await session.scalar(select(V2ChainExecution.id)) is None
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_failure_journal_retains_only_neutral_exception_type(
    monkeypatch,
) -> None:
    class SensitiveFailure(RuntimeError):
        pass

    async def fail_chain(*args, **kwargs):
        raise SensitiveFailure("credential-value-must-never-be-persisted")

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(v2_execution, "run_v2_shadow_chain", fail_chain)
    try:
        async with sessions() as session:
            with pytest.raises(SensitiveFailure):
                await run_journaled_v2_shadow_chain(
                    session,
                    evaluated_at=EVALUATED_AT,
                    vertical="smartphones",
                    limit=1,
                    apply=True,
                    campaign_id="sha256:" + "c" * 64,
                    execution_kind="progression",
                )
            execution = await session.scalar(select(V2ChainExecution))
            assert execution is not None
            assert execution.status == "failed"
            assert execution.failure_reason == "SensitiveFailure"
            assert "credential" not in execution.failure_reason
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_cancelled_execution_is_recorded_as_interrupted(monkeypatch) -> None:
    async def cancel_chain(*args, **kwargs):
        raise asyncio.CancelledError

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(v2_execution, "run_v2_shadow_chain", cancel_chain)
    try:
        async with sessions() as session:
            with pytest.raises(asyncio.CancelledError):
                await run_journaled_v2_shadow_chain(
                    session,
                    evaluated_at=EVALUATED_AT,
                    vertical="smartphones",
                    limit=1,
                    apply=True,
                )
            execution = await session.scalar(select(V2ChainExecution))
            assert execution is not None
            assert execution.status == "interrupted"
            assert execution.failure_reason == "CancelledError"
            assert execution.finished_at is not None
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_journaled_chain_refuses_a_second_running_execution() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with sessions() as session:
            await _seed(session)
            session.add(
                V2ChainExecution(
                    execution_key="c" * 64,
                    mode="apply",
                    status="running",
                    evaluated_at=EVALUATED_AT.replace(tzinfo=None),
                    vertical="smartphones",
                    after_raw_id=0,
                    row_limit=1,
                    last_raw_source_id=0,
                    checkpoints_json={
                        "ontology_snapshot_id": 0,
                        "hybrid_run_id": 0,
                        "constraint_run_id": 0,
                        "ranking_run_id": 0,
                        "optimization_run_id": 0,
                        "confidence_run_id": 0,
                    },
                    completed_stages_json=[],
                    heartbeat_at=EVALUATED_AT.replace(tzinfo=None),
                )
            )
            await session.commit()

            with pytest.raises(V2ChainAlreadyRunning):
                await run_journaled_v2_shadow_chain(
                    session,
                    evaluated_at=EVALUATED_AT,
                    vertical="smartphones",
                    limit=1,
                    apply=True,
                )

            executions = list(
                (await session.scalars(select(V2ChainExecution))).all()
            )
            assert len(executions) == 1
            assert executions[0].status == "running"
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_stale_execution_is_interrupted_without_starting_a_successor() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with sessions() as session:
            session.add(
                V2ChainExecution(
                    execution_key="d" * 64,
                    mode="apply",
                    status="running",
                    evaluated_at=EVALUATED_AT.replace(tzinfo=None),
                    vertical="smartphones",
                    after_raw_id=0,
                    row_limit=1,
                    last_raw_source_id=0,
                    checkpoints_json={
                        "ontology_snapshot_id": 0,
                        "hybrid_run_id": 0,
                        "constraint_run_id": 0,
                        "ranking_run_id": 0,
                        "optimization_run_id": 0,
                        "confidence_run_id": 0,
                    },
                    completed_stages_json=["product_identity"],
                    heartbeat_at=(EVALUATED_AT - timedelta(hours=2)).replace(
                        tzinfo=None
                    ),
                )
            )
            await session.commit()

            changed = await interrupt_stale_execution(
                session,
                stale_before=EVALUATED_AT - timedelta(hours=1),
            )
            executions = list(
                (await session.scalars(select(V2ChainExecution))).all()
            )

            assert changed == 1
            assert len(executions) == 1
            assert executions[0].status == "interrupted"
            assert executions[0].failure_reason == "stale_heartbeat"
            assert executions[0].finished_at is not None
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_scheduler_resumes_interrupted_chain_with_original_checkpoints(
    monkeypatch,
) -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    original_chain = v2_execution.run_v2_shadow_chain

    async def interrupt_after_ontology(*args, on_stage_complete=None, **kwargs):
        async def intercepted(stage_name: str) -> None:
            if on_stage_complete is not None:
                await on_stage_complete(stage_name)
            if stage_name == "product_ontology":
                raise asyncio.CancelledError

        return await original_chain(
            *args,
            on_stage_complete=intercepted,
            **kwargs,
        )

    try:
        async with sessions() as session:
            await _seed(session)
            monkeypatch.setattr(
                v2_execution,
                "run_v2_shadow_chain",
                interrupt_after_ontology,
            )
            with pytest.raises(asyncio.CancelledError):
                await run_journaled_v2_shadow_chain(
                    session,
                    evaluated_at=EVALUATED_AT,
                    vertical="smartphones",
                    limit=1,
                    apply=True,
                    campaign_id="sha256:" + "c" * 64,
                    execution_kind="progression",
                )
            interrupted = await session.scalar(
                select(V2ChainExecution).where(
                    V2ChainExecution.status == "interrupted"
                )
            )
            assert interrupted is not None
            assert interrupted.completed_stages_json[-1] == "product_ontology"
            original_checkpoints = dict(interrupted.checkpoints_json)

        monkeypatch.setattr(
            v2_execution,
            "run_v2_shadow_chain",
            original_chain,
        )

        @asynccontextmanager
        async def scope():
            async with sessions() as session:
                yield session

        monkeypatch.setattr(
            v2_scheduler,
            "get_settings",
            lambda: SimpleNamespace(
                database_schema_mode="alembic",
                v2_chain_mode="shadow",
                v2_chain_stale_after_seconds=14_400,
                v2_chain_campaign_id="sha256:" + "c" * 64,
            ),
        )
        monkeypatch.setattr(v2_scheduler.db, "is_enabled", lambda: True)
        monkeypatch.setattr(v2_scheduler.db, "prepare_schema", AsyncMock())
        monkeypatch.setattr(v2_scheduler.db, "session_scope", scope)

        receipt = await v2_scheduler.run_once(
            vertical="smartphones",
            limit=100,
        )

        assert receipt.status == "succeeded"
        assert receipt.row_limit == 1
        assert receipt.recovery_source_execution_id == interrupted.id
        async with sessions() as session:
            executions = list(
                (
                    await session.scalars(
                        select(V2ChainExecution).order_by(V2ChainExecution.id)
                    )
                ).all()
            )
            assert [item.status for item in executions] == [
                "interrupted",
                "succeeded",
            ]
            assert executions[1].evaluated_at == executions[0].evaluated_at
            assert executions[1].checkpoints_json == original_checkpoints
            assert len(executions[1].completed_stages_json) == 13
            assert executions[1].last_raw_source_id == 1
    finally:
        await engine.dispose()
