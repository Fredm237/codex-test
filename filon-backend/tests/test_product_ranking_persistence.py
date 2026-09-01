from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.constraint_engine.models import ConstraintCandidateEvaluation, ConstraintEvaluationRun
from app.db.base import Base
from app.hybrid_retrieval.models import HybridRetrievalCandidate, HybridRetrievalRun
from app.product_ranking.engine import RankingCandidateFacts, RankingRequest, ScoreFact, rank_products
from app.product_ranking.models import ProductRankingCandidate, ProductRankingRun
from app.product_ranking.persistence import ProductRankingPersistenceError, persist_product_ranking


DIGEST = "sha256:" + "a" * 64


async def _constraint_chain(session):
    retrieval = HybridRetrievalRun(
        id=1,
        run_key="a" * 64,
        query_ref="synthetic",
        query_digest=DIGEST,
        raw_query_retained=False,
        locale="fr",
        country_code="BE",
        intent_json={},
        sources_json=[],
        outcome="CANDIDATES",
        reason_codes_json=[],
        retrieval_version="test/v1",
        fusion_version="test/v1",
        index_versions_json={},
        snapshot_ref="synthetic:1",
        result_digest=DIGEST,
        evaluated_at=datetime(2026, 9, 1),
    )
    retrieval_candidate = HybridRetrievalCandidate(
        id=1,
        run_id=1,
        candidate_rank=1,
        candidate_status="ELIGIBLE_SHADOW",
        entity_type="VARIANT",
        entity_ref="variant:101",
        group_key="variant:101",
        rrf_score="0.01",
        offer_ids_json=[],
        source_evidence_json=[],
    )
    constraint = ConstraintEvaluationRun(
        id=1,
        run_key="b" * 64,
        retrieval_run_id=1,
        context_digest=DIGEST,
        raw_context_retained=False,
        policy_version="constraint/v1",
        outcome="ELIGIBLE_CANDIDATES",
        candidate_count=1,
        eligible_count=1,
        excluded_count=0,
        unknown_count=0,
        result_digest=DIGEST,
        evaluated_at=datetime(2026, 9, 1),
    )
    candidate = ConstraintCandidateEvaluation(
        id=1,
        run_id=1,
        retrieval_candidate_id=1,
        entity_type="VARIANT",
        entity_ref="variant:101",
        status="ELIGIBLE",
        hard_results_json=[],
        preference_results_json=[],
        reason_codes_json=[],
    )
    session.add_all([retrieval, retrieval_candidate, constraint, candidate])
    await session.commit()
    return constraint, candidate


def _fact(name: str) -> ScoreFact:
    return ScoreFact("known", "0.8", (f"evidence:{name}",))


def _ranking():
    candidate = RankingCandidateFacts(
        "variant:101",
        "ELIGIBLE",
        {name: _fact(name) for name in ("need_fit", "product_quality", "value", "evidence")},
    )
    return rank_products(RankingRequest("synthetic-context", "smartphones"), [candidate])


@pytest.mark.asyncio
async def test_dry_apply_and_replay_are_append_only_without_raw_context() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with sessions() as session:
        run, candidate = await _constraint_chain(session)
        evaluated_at = datetime(2026, 9, 1, 22, tzinfo=timezone.utc)
        dry = await persist_product_ranking(
            session,
            constraint_run=run,
            candidate_ids={candidate.entity_ref: candidate.id},
            evaluated_at=evaluated_at,
            ranking=_ranking(),
            apply=False,
        )
        first = await persist_product_ranking(
            session,
            constraint_run=run,
            candidate_ids={candidate.entity_ref: candidate.id},
            evaluated_at=evaluated_at,
            ranking=_ranking(),
            apply=True,
        )
        replay = await persist_product_ranking(
            session,
            constraint_run=run,
            candidate_ids={candidate.entity_ref: candidate.id},
            evaluated_at=evaluated_at,
            ranking=_ranking(),
            apply=True,
        )
        assert dry.runs_created == 0
        assert first.runs_created == first.candidates_created == 1
        assert replay.runs_existing == replay.candidates_existing == 1
        assert first.run_key == replay.run_key
        assert await session.scalar(select(func.count()).select_from(ProductRankingRun)) == 1
        assert await session.scalar(select(func.count()).select_from(ProductRankingCandidate)) == 1
        stored = await session.scalar(select(ProductRankingRun))
        assert stored is not None and stored.raw_context_retained is False
        assert not hasattr(stored, "raw_context")
    await engine.dispose()


@pytest.mark.asyncio
async def test_incomplete_constraint_mapping_fails_closed() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with sessions() as session:
        run, _candidate = await _constraint_chain(session)
        with pytest.raises(ProductRankingPersistenceError, match="mapping"):
            await persist_product_ranking(
                session,
                constraint_run=run,
                candidate_ids={},
                evaluated_at=datetime(2026, 9, 1, tzinfo=timezone.utc),
                ranking=_ranking(),
                apply=False,
            )
    await engine.dispose()
