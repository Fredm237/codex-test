from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.confidence.engine import ConfidenceRequest, CoverageInput, calibrate_confidence
from app.confidence.models import ConfidenceCalibrationRun, ConfidenceDimensionRecord
from app.confidence.persistence import persist_confidence
from app.db.base import Base
from app.offer_optimization.models import OfferOptimizationRun
from tests.test_offer_optimization_persistence import DIGEST, _ranking_run


async def _offer_optimization_run(session) -> OfferOptimizationRun:
    ranking = await _ranking_run(session, outcome="ABSTAINED")
    run = OfferOptimizationRun(
        id=1,
        run_key="d" * 64,
        product_ranking_run_id=ranking.id,
        context_digest=DIGEST,
        raw_context_retained=False,
        policy_version="offer-optimization-policy/v2",
        outcome="ABSTAINED",
        selected_product_ref=None,
        selected_offer_ref=None,
        candidate_count=0,
        selected_count=0,
        eligible_count=0,
        unoptimizable_count=0,
        ineligible_count=0,
        result_digest=DIGEST,
        evaluated_at=datetime(2026, 9, 1),
    )
    session.add(run)
    await session.commit()
    return run


@pytest.mark.asyncio
async def test_dry_apply_and_replay_are_append_only_without_raw_context() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with sessions() as session:
        source = await _offer_optimization_run(session)
        confidence = calibrate_confidence(
            ConfidenceRequest("p9:1", (), CoverageInput(0, 0)), ()
        )
        kwargs = {
            "offer_optimization_run": source,
            "evaluated_at": datetime(2026, 9, 2, tzinfo=timezone.utc),
            "confidence": confidence,
        }
        dry = await persist_confidence(session, **kwargs)
        first = await persist_confidence(session, **kwargs, apply=True)
        replay = await persist_confidence(session, **kwargs, apply=True)
        assert dry.runs_created == 0
        assert first.runs_created == 1 and first.dimensions_created == 5
        assert replay.runs_existing == 1 and replay.dimensions_existing == 5
        assert first.evaluation_id == replay.evaluation_id
        assert await session.scalar(select(func.count()).select_from(ConfidenceCalibrationRun)) == 1
        assert await session.scalar(select(func.count()).select_from(ConfidenceDimensionRecord)) == 5
        stored = await session.scalar(select(ConfidenceCalibrationRun))
        assert stored is not None and stored.raw_context_retained is False
        assert stored.outcome == "ABSTAINED" and stored.evidence_coverage_ratio is None
    await engine.dispose()
