from __future__ import annotations

import hashlib
from datetime import datetime, timezone

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.constraint_engine.engine import CandidateFacts, ConstraintRequest, Fact, HardConstraint, evaluate_constraints
from app.constraint_engine.models import ConstraintCandidateEvaluation, ConstraintEvaluationRun
from app.constraint_engine.persistence import ConstraintPersistenceError, persist_constraint_evaluation
from app.db.base import Base
from app.hybrid_retrieval.models import HybridRetrievalCandidate, HybridRetrievalRun


async def _retrieval(session):
    digest = "sha256:" + hashlib.sha256(b"synthetic query").hexdigest()
    run = HybridRetrievalRun(
        run_key="a" * 64,
        query_ref="synthetic-query",
        query_digest=digest,
        raw_query_retained=False,
        locale="fr",
        country_code="BE",
        intent_json={"status": "RESOLVED"},
        sources_json=[],
        outcome="CANDIDATES",
        reason_codes_json=[],
        retrieval_version="test/v1",
        fusion_version="test/v1",
        index_versions_json={},
        snapshot_ref="synthetic:1",
        result_digest=digest,
        evaluated_at=datetime(2026, 9, 1),
    )
    session.add(run)
    await session.flush()
    candidate = HybridRetrievalCandidate(
        run_id=run.id,
        candidate_rank=1,
        candidate_status="ELIGIBLE_SHADOW",
        entity_type="VARIANT",
        entity_ref="variant:101",
        group_key="variant:101",
        rrf_score="0.01",
        offer_ids_json=[1001],
        source_evidence_json=[],
    )
    session.add(candidate)
    await session.commit()
    return run, candidate


def _evaluation():
    request = ConstraintRequest(
        "synthetic-context",
        (HardConstraint("stock", "AVAILABILITY_REQUIRED", {"value": "in_stock"}),),
    )
    facts = CandidateFacts(
        "variant:101",
        Fact("unknown"),
        Fact("unknown"),
        Fact("known", "in_stock", ("offer:1001:stock",)),
        Fact("known", False, ("offer:1001:adult",)),
        {},
        {},
    )
    return evaluate_constraints(request, (facts,))


@pytest.mark.asyncio
async def test_dry_run_apply_and_replay_are_idempotent_without_raw_context():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with sessions() as session:
        run, candidate = await _retrieval(session)
        evaluated_at = datetime(2026, 9, 1, 20, tzinfo=timezone.utc)
        dry = await persist_constraint_evaluation(
            session,
            retrieval_run=run,
            candidate_ids={candidate.entity_ref: candidate.id},
            evaluated_at=evaluated_at,
            evaluation=_evaluation(),
            apply=False,
        )
        first = await persist_constraint_evaluation(
            session,
            retrieval_run=run,
            candidate_ids={candidate.entity_ref: candidate.id},
            evaluated_at=evaluated_at,
            evaluation=_evaluation(),
            apply=True,
        )
        replay = await persist_constraint_evaluation(
            session,
            retrieval_run=run,
            candidate_ids={candidate.entity_ref: candidate.id},
            evaluated_at=evaluated_at,
            evaluation=_evaluation(),
            apply=True,
        )
        assert dry.runs_created == 0
        assert first.runs_created == first.candidates_created == 1
        assert replay.runs_existing == replay.candidates_existing == 1
        assert first.run_key == replay.run_key
        assert await session.scalar(select(func.count()).select_from(ConstraintEvaluationRun)) == 1
        assert await session.scalar(select(func.count()).select_from(ConstraintCandidateEvaluation)) == 1
        stored = await session.scalar(select(ConstraintEvaluationRun))
        assert stored is not None and stored.raw_context_retained is False
        assert not hasattr(stored, "raw_context")
    await engine.dispose()


@pytest.mark.asyncio
async def test_incomplete_retrieval_mapping_fails_closed():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with sessions() as session:
        run, _candidate = await _retrieval(session)
        with pytest.raises(ConstraintPersistenceError, match="incomplete"):
            await persist_constraint_evaluation(
                session,
                retrieval_run=run,
                candidate_ids={},
                evaluated_at=datetime(2026, 9, 1, tzinfo=timezone.utc),
                evaluation=_evaluation(),
                apply=False,
            )
    await engine.dispose()
