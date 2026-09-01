from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.buy_wait.replay import _validate_window, replay_buy_wait_batch
from app.db.base import Base
from tests.test_buy_wait_persistence import _confidence_run


def test_invalid_window_is_rejected() -> None:
    with pytest.raises(ValueError, match="after_confidence_run_id"):
        _validate_window(-1, 1)
    with pytest.raises(ValueError, match="limit"):
        _validate_window(0, 101)


@pytest.mark.asyncio
async def test_real_shape_replay_abstains_without_temporal_profile_and_is_idempotent() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with sessions() as session:
        await _confidence_run(session)
        evaluated = datetime(2026, 9, 2, tzinfo=timezone.utc)
        dry = await replay_buy_wait_batch(session, evaluated_at=evaluated, limit=1)
        first = await replay_buy_wait_batch(session, evaluated_at=evaluated, limit=1, apply=True)
        replay = await replay_buy_wait_batch(session, evaluated_at=evaluated, limit=1, apply=True)
        assert dry.scanned_runs == first.scanned_runs == replay.scanned_runs == 1
        assert dry.abstained_runs == 1 and dry.buy_now_runs == dry.wait_runs == 0
        assert first.runs_created == 1
        assert replay.runs_existing == 1
        assert first.evaluation_id == replay.evaluation_id
    await engine.dispose()
