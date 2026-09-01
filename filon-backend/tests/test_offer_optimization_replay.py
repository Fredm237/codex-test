from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
from app.offer_optimization.replay import (
    _money,
    _returns,
    _validate_window,
    replay_offer_optimization_batch,
)
from tests.test_offer_optimization_persistence import _ranking_run


def test_invalid_window_is_rejected() -> None:
    with pytest.raises(ValueError, match="after_product_ranking_run_id"):
        _validate_window(-1, 1)
    with pytest.raises(ValueError, match="limit"):
        _validate_window(0, 101)


def test_cashback_and_returns_claims_require_explicit_sourced_values() -> None:
    evidence = [
        {
            "raw_source_record_id": 9,
            "field": "cashback",
            "transformation_version": "v1",
        }
    ]
    cashback = _money(
        {
            "state": "known",
            "value": {"amount_decimal": "5.00", "currency": "EUR"},
            "evidence": evidence,
        }
    )
    returns = _returns(
        {
            "state": "known",
            "value": {"accepted": True, "period_days": 30},
            "evidence": evidence,
        }
    )
    assert cashback.amount_decimal == "5.00"
    assert cashback.evidence_refs == ("raw:9:cashback:v1",)
    assert returns.accepted is True and returns.period_days == 30
    assert _money(None).state == "unknown"
    assert _returns({"state": "known", "value": {"accepted": True, "period_days": None}}).state == "invalid"


@pytest.mark.asyncio
async def test_real_shape_replay_propagates_ranking_abstention_and_is_idempotent() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with sessions() as session:
        await _ranking_run(session, outcome="ABSTAINED")
        evaluated = datetime(2026, 9, 1, 23, tzinfo=timezone.utc)
        dry = await replay_offer_optimization_batch(session, evaluated_at=evaluated, limit=1)
        first = await replay_offer_optimization_batch(
            session, evaluated_at=evaluated, limit=1, apply=True
        )
        replay = await replay_offer_optimization_batch(
            session, evaluated_at=evaluated, limit=1, apply=True
        )
        assert dry.scanned_runs == first.scanned_runs == replay.scanned_runs == 1
        assert dry.scanned_offers == 0
        assert dry.abstained_runs == 1
        assert dry.runs_created == 0
        assert first.runs_created == 1 and first.candidates_created == 0
        assert replay.runs_existing == 1 and replay.candidates_existing == 0
        assert first.evaluation_id == replay.evaluation_id
    await engine.dispose()
