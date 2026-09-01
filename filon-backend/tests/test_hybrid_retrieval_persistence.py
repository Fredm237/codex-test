"""Writer append-only Hybrid Retrieval Phase 5G."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
from app.hybrid_retrieval.fusion import FusionSourceHit, reciprocal_rank_fusion
from app.hybrid_retrieval.models import HybridRetrievalCandidate, HybridRetrievalRun
from app.hybrid_retrieval.persistence import persist_fusion_result


def _fusion():
    query_digest = "sha256:" + hashlib.sha256(b"synthetic query").hexdigest()
    return query_digest, reciprocal_rank_fusion(
        (FusionSourceHit("LEXICAL", 1, "variant:101", (1001, 1002), "lexical:1"),),
        query_digest=query_digest,
        snapshot_ref="synthetic:snapshot:1",
        index_versions={"LEXICAL": "synthetic/v1"},
    )


async def _persist(session, *, apply: bool):
    query_digest, fusion = _fusion()
    return await persist_fusion_result(
        session,
        query_ref="synthetic-query-1",
        query_digest=query_digest,
        locale="fr",
        country_code="BE",
        intent={"status": "RESOLVED"},
        sources=[{"source_type": "LEXICAL", "status": "SUCCEEDED"}],
        retrieval_version="hybrid-retrieval/v1",
        index_versions={"LEXICAL": "synthetic/v1"},
        snapshot_ref="synthetic:snapshot:1",
        evaluated_at=datetime(2026, 9, 1, 17, tzinfo=timezone.utc),
        fusion=fusion,
        apply=apply,
    )


@pytest.mark.asyncio
async def test_dry_run_writes_nothing_and_apply_replays_idempotently():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with sessions() as session:
        dry = await _persist(session, apply=False)
        assert dry.mode == "dry_run"
        assert await session.scalar(select(func.count()).select_from(HybridRetrievalRun)) == 0
        first = await _persist(session, apply=True)
        replay = await _persist(session, apply=True)
        assert first.run_key == replay.run_key
        assert first.runs_created == 1
        assert first.candidates_created == 1
        assert replay.runs_existing == 1
        assert replay.candidates_existing == 1
        assert await session.scalar(select(func.count()).select_from(HybridRetrievalRun)) == 1
        assert await session.scalar(select(func.count()).select_from(HybridRetrievalCandidate)) == 1
        stored = await session.scalar(select(HybridRetrievalRun))
        assert stored is not None
        assert stored.raw_query_retained is False
        assert not hasattr(stored, "raw_query")
    await engine.dispose()
