from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
from app.personal_commerce.replay import _validate_window, replay_personal_commerce_batch
from tests.test_personal_commerce_persistence import _buy_wait_run


def test_invalid_window_is_rejected() -> None:
    with pytest.raises(ValueError, match="after_buy_wait_run_id"):
        _validate_window(-1, 1)
    with pytest.raises(ValueError, match="limit"):
        _validate_window(0, 101)


@pytest.mark.asyncio
async def test_real_shape_replay_abstains_without_consent_and_is_idempotent() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with sessions() as session:
        await _buy_wait_run(session)
        evaluated = datetime(2026, 9, 2, 14, tzinfo=timezone.utc)
        dry = await replay_personal_commerce_batch(session, evaluated_at=evaluated, limit=1)
        first = await replay_personal_commerce_batch(
            session, evaluated_at=evaluated, limit=1, apply=True,
        )
        replay = await replay_personal_commerce_batch(
            session, evaluated_at=evaluated, limit=1, apply=True,
        )

        assert dry.scanned_runs == first.scanned_runs == replay.scanned_runs == 1
        assert dry.abstained_runs == 1 and dry.selected_runs == 0
        assert first.runs_created == 1
        assert replay.runs_existing == 1
        assert first.evaluation_id == replay.evaluation_id
    await engine.dispose()
