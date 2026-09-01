"""Replay borné et idempotent Hybrid Retrieval Phase 5H."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import models as core_models
from app.db.base import Base
from app.hybrid_retrieval.replay import (
    HybridRetrievalReplayError,
    _document,
    _validate_window,
    replay_hybrid_retrieval_batch,
)
from app.observations.models import RawSourceRecord
from app.product_graph.models import GraphVariant
from app.product_ontology.models import ProductOntologySnapshot


def _snapshot(**overrides):
    values = {
        "id": 1,
        "variant_id": 101,
        "classification_json": {"product_type": {"state": "known", "value": {"concept_key": "smartphone"}}},
        "product_role_json": {"state": "known", "value": "PRIMARY_PRODUCT"},
        "attributes_json": [{"attribute_key": "storage", "state": "known", "value": {"value": 128, "unit": "GB"}}],
    }
    values.update(overrides)
    return type("Snapshot", (), values)()


def _offer(**overrides):
    values = {"id": 1001, "name": "Example Phone 15 128GB", "brand": "Example Mobile"}
    values.update(overrides)
    return type("Offer", (), values)()


def test_projection_uses_real_surface_in_memory_but_returns_structured_document():
    item = _document(_snapshot(), _offer())
    assert item.entity_ref == "variant:101"
    assert item.attributes == {"storage": "128GB"}
    assert item.query == "Example Mobile Example Phone 15 128GB"


def test_unresolved_snapshot_and_invalid_window_fail_closed():
    with pytest.raises(HybridRetrievalReplayError, match="unresolved"):
        _document(_snapshot(variant_id=None), _offer())
    with pytest.raises(ValueError, match="after_snapshot_id"):
        _validate_window(-1, 10)
    with pytest.raises(ValueError, match="limit"):
        _validate_window(0, 1001)


@pytest.mark.asyncio
async def test_real_shape_batch_is_dry_then_created_then_idempotent():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with sessions() as session:
        merchant = core_models.Merchant(id=1, awin_mid=1, name="Synthetic Merchant", slug="synthetic-merchant", joined=True)
        offer = core_models.Offer(id=1001, merchant_id=1, awin_product_id="p-1", name="Example Phone 15 128GB", brand="Example Mobile", is_canonical=True, is_adult=False)
        raw = RawSourceRecord(id=1, source_type="awin_feed", source_ref="synthetic", source_record_key="p-1", schema_version="test/v1", context_json={}, payload_json={}, payload_checksum="1" * 64, replay_key="2" * 64, observed_at=datetime(2026, 9, 1, tzinfo=timezone.utc).replace(tzinfo=None))
        variant = GraphVariant(id=101, variant_key="variant-101", model_id=None, attributes_json={}, status="shadow", resolver_version="test/v1")
        snapshot = ProductOntologySnapshot(
            id=1,
            snapshot_key="3" * 64,
            raw_source_record_id=1,
            offer_id=1001,
            variant_id=101,
            ontology_status="VERIFIED",
            classification_json={"product_type": {"state": "known", "value": {"concept_key": "smartphone"}}},
            product_role_json={"state": "known", "value": "PRIMARY_PRODUCT"},
            attributes_json=[{"attribute_key": "storage", "state": "known", "value": {"value": 128, "unit": "GB"}}],
            relationships_json=[],
            facets_json={},
            legacy_taxonomy_json={},
            reason_codes_json=["ontology_verified"],
            projection_version="test/v1",
            policy_version="test/v1",
            observed_at=datetime(2026, 9, 1),
            evaluated_at=datetime(2026, 9, 1, 1),
        )
        session.add_all([merchant, offer, raw, variant, snapshot])
        await session.commit()
        evaluated = datetime(2026, 9, 1, 18, tzinfo=timezone.utc)
        dry = await replay_hybrid_retrieval_batch(session, evaluated_at=evaluated, limit=1, apply=False)
        first = await replay_hybrid_retrieval_batch(session, evaluated_at=evaluated, limit=1, apply=True)
        replay = await replay_hybrid_retrieval_batch(session, evaluated_at=evaluated, limit=1, apply=True)
        assert dry.scanned == first.scanned == replay.scanned == 1
        assert dry.runs_created == 0
        assert first.candidate_runs == 1
        assert first.top1_target_hits == 1
        assert first.runs_created == 1
        assert replay.runs_existing == 1
        assert first.evaluation_id == replay.evaluation_id
    await engine.dispose()
