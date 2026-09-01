from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
from app.offer_optimization.engine import (
    AvailabilityFact,
    MoneyFact,
    OfferCandidateFacts,
    OptimizationRequest,
    ScoreFact,
    optimize_offers,
)
from app.offer_optimization.models import OfferOptimizationCandidate, OfferOptimizationRun
from app.offer_optimization.persistence import (
    OfferOptimizationPersistenceError,
    persist_offer_optimization,
)
from app.product_ranking.models import ProductRankingRun
from tests.test_product_ranking_persistence import _constraint_chain


DIGEST = "sha256:" + "a" * 64


async def _ranking_run(session, *, outcome: str = "RANKED_PRODUCTS") -> ProductRankingRun:
    constraint, _candidate = await _constraint_chain(session)
    run = ProductRankingRun(
        id=1,
        run_key="c" * 64,
        constraint_run_id=constraint.id,
        context_digest=DIGEST,
        raw_context_retained=False,
        policy_version="product-ranking-policy/v1",
        vertical="smartphones",
        outcome=outcome,
        candidate_count=1,
        ranked_count=1 if outcome == "RANKED_PRODUCTS" else 0,
        unrankable_count=0 if outcome == "RANKED_PRODUCTS" else 1,
        ineligible_count=0,
        result_digest=DIGEST,
        evaluated_at=datetime(2026, 9, 1),
    )
    session.add(run)
    await session.commit()
    return run


def _optimization():
    offer = OfferCandidateFacts(
        "offer:501",
        "variant:101",
        "VERIFIED",
        MoneyFact("known", "100", "EUR", ("price",)),
        MoneyFact("known", "5", "EUR", ("shipping",)),
        AvailabilityFact("known", "in_stock", ("stock",)),
        ScoreFact("known", "0.9", ("merchant-quality",)),
        ScoreFact("known", "0.8", ("freshness",)),
    )
    return optimize_offers(
        OptimizationRequest("ctx", "RANKED_PRODUCTS", "variant:101", 1),
        [offer],
    )


@pytest.mark.asyncio
async def test_dry_apply_and_replay_are_append_only_without_raw_context() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with sessions() as session:
        run = await _ranking_run(session)
        evaluated_at = datetime(2026, 9, 1, 23, tzinfo=timezone.utc)
        kwargs = {
            "product_ranking_run": run,
            "snapshot_ids": {"offer:501": 1},
            "evaluated_at": evaluated_at,
            "optimization": _optimization(),
        }
        dry = await persist_offer_optimization(session, **kwargs)
        first = await persist_offer_optimization(session, **kwargs, apply=True)
        replay = await persist_offer_optimization(session, **kwargs, apply=True)
        assert dry.runs_created == 0
        assert first.runs_created == first.candidates_created == 1
        assert replay.runs_existing == replay.candidates_existing == 1
        assert first.run_key == replay.run_key
        assert await session.scalar(select(func.count()).select_from(OfferOptimizationRun)) == 1
        assert await session.scalar(select(func.count()).select_from(OfferOptimizationCandidate)) == 1
        stored = await session.scalar(select(OfferOptimizationRun))
        assert stored is not None and stored.raw_context_retained is False
        assert stored.selected_offer_ref == "offer:501"
    await engine.dispose()


@pytest.mark.asyncio
async def test_incomplete_offer_truth_mapping_fails_closed() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with sessions() as session:
        run = await _ranking_run(session)
        with pytest.raises(OfferOptimizationPersistenceError, match="mapping"):
            await persist_offer_optimization(
                session,
                product_ranking_run=run,
                snapshot_ids={},
                evaluated_at=datetime(2026, 9, 1, tzinfo=timezone.utc),
                optimization=_optimization(),
            )
    await engine.dispose()
