from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import models as core_models  # noqa: F401
from app.db.base import Base
from app.v2_chain.coverage_funnel import (
    FUNNEL_STAGES,
    evaluate_coverage_funnel,
    render_coverage_funnel_markdown,
)
from app.v2_chain.models import V2ChainExecution


CAMPAIGN = "sha256:" + "d" * 64
EVALUATED_AT = datetime(2026, 9, 4, 12, tzinfo=timezone.utc)


async def _database():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    return engine, async_sessionmaker(engine, expire_on_commit=False)


def _execution(index: int, *, after: int, counts: tuple[int, ...]):
    started = (EVALUATED_AT + timedelta(minutes=index)).replace(tzinfo=None)
    evaluation_id = "sha256:" + f"{index + 1:064x}"
    return V2ChainExecution(
        execution_key=f"{index + 1:064x}",
        mode="apply",
        status="succeeded",
        evaluated_at=started,
        vertical="smartphones",
        after_raw_id=after,
        row_limit=10,
        last_raw_source_id=after + 10,
        checkpoints_json={},
        completed_stages_json=[
            "product_identity",
            "entity_resolution",
            "offer_graph",
            "merchant_intelligence",
            "evidence_engine",
            "offer_truth",
            "product_ontology",
            "hybrid_retrieval",
            "constraint_engine",
            "product_ranking",
            "offer_optimization",
            "confidence",
            "buy_wait",
        ],
        report_evaluation_id=evaluation_id,
        campaign_id=CAMPAIGN,
        execution_kind="progression",
        window_metrics_json={
            "schema_version": "v2-window-metrics/v1",
            "errors": 0,
            "evaluation_identity": evaluation_id,
            "coverage_funnel": dict(zip(FUNNEL_STAGES, counts)),
        },
        heartbeat_at=started,
        finished_at=started + timedelta(seconds=1),
    )


@pytest.mark.asyncio
async def test_thirty_contiguous_windows_produce_ready_funnel() -> None:
    engine, sessions = await _database()
    try:
        async with sessions() as session:
            counts = (10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0)
            session.add_all(
                _execution(index, after=index * 10, counts=counts)
                for index in range(30)
            )
            await session.commit()

            report = await evaluate_coverage_funnel(
                session,
                campaign_id=CAMPAIGN,
                evaluated_at=EVALUATED_AT + timedelta(hours=1),
            )

            assert report.status == "READY"
            assert report.valid_terminal_windows == 30
            assert report.contiguous is True
            assert report.monotone_counts is True
            assert report.stages[0].records == 300
            assert report.stages[1].coverage_of_raw_ppm == 900_000
            assert "| identified | 270 | 90.00% | 90.00% |" in render_coverage_funnel_markdown(report)
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_gap_or_non_monotone_measurement_stays_pending() -> None:
    engine, sessions = await _database()
    try:
        async with sessions() as session:
            session.add(_execution(0, after=0, counts=(10,) * len(FUNNEL_STAGES)))
            session.add(
                _execution(
                    1,
                    after=20,
                    counts=(10, 11, *([1] * (len(FUNNEL_STAGES) - 2))),
                )
            )
            await session.commit()

            report = await evaluate_coverage_funnel(
                session,
                campaign_id=CAMPAIGN,
                evaluated_at=EVALUATED_AT,
            )

            assert report.status == "PENDING"
            assert report.contiguous is False
            assert report.monotone_counts is False
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_replay_is_never_counted_as_an_additional_coverage_window() -> None:
    engine, sessions = await _database()
    try:
        async with sessions() as session:
            source = _execution(0, after=0, counts=(10,) * len(FUNNEL_STAGES))
            session.add(source)
            await session.flush()
            replay = _execution(1, after=10, counts=(10,) * len(FUNNEL_STAGES))
            replay.execution_kind = "replay"
            replay.source_execution_id = source.id
            session.add(replay)
            await session.commit()

            report = await evaluate_coverage_funnel(
                session,
                campaign_id=CAMPAIGN,
                evaluated_at=EVALUATED_AT + timedelta(hours=1),
            )

            assert report.execution_rows == 2
            assert report.valid_terminal_windows == 1
            assert report.stages[0].records == 10
    finally:
        await engine.dispose()
