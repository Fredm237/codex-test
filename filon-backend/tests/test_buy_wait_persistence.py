from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.buy_wait.engine import BuyWaitRequest, DecisionConfidence, decide_buy_wait
from app.buy_wait.models import BuyWaitDecisionRun
from app.buy_wait.persistence import persist_buy_wait
from app.confidence.models import ConfidenceCalibrationRun
from app.db.base import Base
from tests.test_confidence_persistence import _offer_optimization_run


async def _confidence_run(session) -> ConfidenceCalibrationRun:
    source = await _offer_optimization_run(session)
    run = ConfidenceCalibrationRun(
        id=1,
        run_key="e" * 64,
        offer_optimization_run_id=source.id,
        context_digest="sha256:" + "1" * 64,
        raw_context_retained=False,
        policy_version="confidence-calibration-policy/v1",
        outcome="ABSTAINED",
        dimension_count=5,
        calibrated_dimension_count=0,
        evidence_coverage_state="UNKNOWN",
        evidence_coverage_ratio=None,
        evidence_observed_count=0,
        evidence_required_count=0,
        evidence_refs_json=[],
        result_digest="sha256:" + "2" * 64,
        evaluated_at=datetime(2026, 9, 1),
    )
    session.add(run)
    await session.commit()
    return run


@pytest.mark.asyncio
async def test_dry_apply_and_replay_are_append_only_without_future_or_raw_context() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with sessions() as session:
        source = await _confidence_run(session)
        evaluated = datetime(2026, 9, 2, tzinfo=timezone.utc)
        decision = decide_buy_wait(
            BuyWaitRequest(
                "p10:1", evaluated, None, None, None, (),
                DecisionConfidence("UNKNOWN", None, 0, None, ()), None,
            )
        )
        kwargs = {"confidence_run": source, "evaluated_at": evaluated, "decision": decision}
        dry = await persist_buy_wait(session, **kwargs)
        first = await persist_buy_wait(session, **kwargs, apply=True)
        replay = await persist_buy_wait(session, **kwargs, apply=True)
        assert dry.runs_created == 0
        assert first.runs_created == 1
        assert replay.runs_existing == 1
        assert first.evaluation_id == replay.evaluation_id
        assert await session.scalar(select(func.count()).select_from(BuyWaitDecisionRun)) == 1
        stored = await session.scalar(select(BuyWaitDecisionRun))
        assert stored is not None and stored.raw_context_retained is False
        assert stored.future_observations_used is False
        assert stored.outcome == "ABSTAIN" and stored.backtest_profile_ref is None
    await engine.dispose()
