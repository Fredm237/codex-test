from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
from app.product_ranking.replay import (
    _factual_dimensions,
    _validate_window,
    replay_product_ranking_batch,
)
from tests.test_product_ranking_persistence import _constraint_chain


def test_invalid_window_is_rejected() -> None:
    with pytest.raises(ValueError, match="after_constraint_run_id"):
        _validate_window(-1, 1)
    with pytest.raises(ValueError, match="limit"):
        _validate_window(0, 101)


def test_malformed_or_absent_retrieval_evidence_fails_closed() -> None:
    assert all(fact.state == "unknown" for fact in _factual_dimensions(None).values())
    candidate = type(
        "Candidate",
        (),
        {"candidate_rank": 1, "source_evidence_json": None, "id": 42},
    )()
    dimensions = _factual_dimensions(candidate)
    assert dimensions["need_fit"].state == "known"
    assert dimensions["evidence"].state == "unknown"
    assert dimensions["product_quality"].state == "unknown"
    assert dimensions["value"].state == "unknown"


@pytest.mark.asyncio
async def test_real_shape_replay_ranks_factual_signals_then_is_idempotent() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with sessions() as session:
        await _constraint_chain(session)
        evaluated = datetime(2026, 9, 1, 22, tzinfo=timezone.utc)
        dry = await replay_product_ranking_batch(
            session, evaluated_at=evaluated, vertical="smartphones", limit=1
        )
        first = await replay_product_ranking_batch(
            session, evaluated_at=evaluated, vertical="smartphones", limit=1, apply=True
        )
        replay = await replay_product_ranking_batch(
            session, evaluated_at=evaluated, vertical="smartphones", limit=1, apply=True
        )
        assert dry.scanned_runs == first.scanned_runs == replay.scanned_runs == 1
        assert dry.scanned_candidates == 1
        assert dry.rankable_runs == 1
        assert dry.ranked_candidates == 1
        assert dry.unrankable_candidates == 0
        assert dry.runs_created == 0
        assert first.runs_created == first.candidates_created == 1
        assert replay.runs_existing == replay.candidates_existing == 1
        assert first.evaluation_id == replay.evaluation_id
    await engine.dispose()
