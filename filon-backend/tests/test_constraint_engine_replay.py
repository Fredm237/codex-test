from __future__ import annotations

import hashlib
from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.constraint_engine.replay import _facts, _validate_window, replay_constraint_batch
from app.db import models as core_models
from app.db.base import Base
from app.hybrid_retrieval.models import HybridRetrievalCandidate, HybridRetrievalRun


def _candidate():
    return type("Candidate", (), {"entity_ref": "variant:101"})()


def _offer(**overrides):
    values = {"id": 1001, "price": 99.99, "currency": "EUR", "in_stock": True, "is_adult": False}
    values.update(overrides)
    return type("Offer", (), values)()


def test_projection_is_fail_closed_for_missing_or_partial_offer_facts():
    missing = _facts(_candidate(), [])
    partial = _facts(_candidate(), [_offer(price=None, currency=None, in_stock=None)])
    assert missing.availability.state == "unknown"
    assert partial.price.state == "unknown"
    assert partial.availability.state == "unknown"


def test_invalid_window_is_rejected():
    with pytest.raises(ValueError, match="after_run_id"):
        _validate_window(-1, 1)
    with pytest.raises(ValueError, match="limit"):
        _validate_window(0, 101)


@pytest.mark.asyncio
async def test_real_shape_replay_is_dry_then_created_then_idempotent():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with sessions() as session:
        merchant = core_models.Merchant(id=1, awin_mid=1, name="Synthetic Merchant", slug="synthetic-merchant", joined=True)
        offer = core_models.Offer(
            id=1001,
            merchant_id=1,
            awin_product_id="p-1",
            name="Example Phone",
            is_canonical=True,
            is_adult=False,
            price=99.99,
            currency="EUR",
            in_stock=True,
        )
        digest = "sha256:" + hashlib.sha256(b"query").hexdigest()
        run = HybridRetrievalRun(
            id=1,
            run_key="a" * 64,
            query_ref="synthetic",
            query_digest=digest,
            raw_query_retained=False,
            locale="fr",
            country_code=None,
            intent_json={},
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
        candidate = HybridRetrievalCandidate(
            id=1,
            run_id=1,
            candidate_rank=1,
            candidate_status="ELIGIBLE_SHADOW",
            entity_type="VARIANT",
            entity_ref="variant:101",
            group_key="variant:101",
            rrf_score="0.01",
            offer_ids_json=[1001],
            source_evidence_json=[],
        )
        session.add_all([merchant, offer, run, candidate])
        await session.commit()
        evaluated = datetime(2026, 9, 1, 20, tzinfo=timezone.utc)
        dry = await replay_constraint_batch(session, evaluated_at=evaluated, limit=1, apply=False)
        first = await replay_constraint_batch(session, evaluated_at=evaluated, limit=1, apply=True)
        replay = await replay_constraint_batch(session, evaluated_at=evaluated, limit=1, apply=True)
        assert dry.scanned_runs == first.scanned_runs == replay.scanned_runs == 1
        assert dry.scanned_candidates == 1
        assert dry.eligible_candidates == 1
        assert dry.runs_created == 0
        assert first.runs_created == first.candidates_created == 1
        assert replay.runs_existing == replay.candidates_existing == 1
        assert first.evaluation_id == replay.evaluation_id
    await engine.dispose()
