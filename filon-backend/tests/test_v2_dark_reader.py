"""Qualification du lecteur sombre V2/Core sans effet public."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import models as core_models
from app.db.base import Base
from app.hybrid_retrieval.models import HybridRetrievalRun
from app.observations.models import Observation, RawSourceRecord
from app.v2_chain import dark_reader
from app.v2_chain.dark_reader import V2DarkReaderError, compare_dark_window
from app.v2_chain.execution import run_journaled_v2_shadow_chain
from app.v2_chain.models import V2DarkReadObservation


EVALUATED_AT = datetime(2026, 9, 3, 18, tzinfo=timezone.utc)
ROUTES_ROOT = Path(__file__).resolve().parents[1] / "app" / "api" / "routes"


async def _seed(session) -> None:
    merchant = core_models.Merchant(
        awin_mid=1901,
        name="Dark Reader Merchant",
        slug="dark-reader-merchant",
        joined=True,
    )
    session.add(merchant)
    await session.flush()
    offer = core_models.Offer(
        merchant_id=merchant.id,
        awin_product_id="dark-reader-1",
        name="Acme Smartphone Prime 128GB",
        brand="Acme",
        price=599,
        currency="EUR",
        in_stock=True,
        is_canonical=True,
        is_adult=False,
    )
    session.add(offer)
    await session.flush()
    session.add(
        core_models.PriceSnapshot(
            offer_id=offer.id,
            price=599,
            currency="EUR",
            in_stock=True,
            captured_at=(EVALUATED_AT - timedelta(hours=1)).replace(tzinfo=None),
        )
    )
    raw = RawSourceRecord(
        source_type="awin_feed",
        source_ref="awin-feed:1901",
        source_record_key="1901:dark-reader-1",
        schema_version="awin-create-a-feed-v1",
        context_json={"merchant_id": merchant.id},
        payload_json={
            "ean": "4006381333931",
            "brand_name": "Acme",
            "product_name": offer.name,
            "name": offer.name,
            "offer_kind": "physical_product",
            "search_price": "599.00",
            "currency": "EUR",
            "in_stock": "yes",
        },
        payload_checksum="a" * 64,
        replay_key="b" * 64,
        observed_at=(EVALUATED_AT - timedelta(hours=1)).replace(tzinfo=None),
    )
    session.add(raw)
    await session.flush()
    session.add(
        Observation(
            raw_source_record_id=raw.id,
            subject_type="offer",
            subject_ref=f"offer:{offer.id}",
            offer_id=offer.id,
            field="name",
            value_json=offer.name,
            status="verified",
            source_type="awin_feed",
            source_ref=raw.source_ref,
            observed_at=raw.observed_at,
            transformation="test",
            transformation_version="v1",
            confidence=1.0,
        )
    )
    await session.commit()


async def _database():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    return engine, async_sessionmaker(engine, expire_on_commit=False)


@pytest.mark.asyncio
async def test_dark_reader_dry_apply_and_replay_are_private_and_idempotent() -> None:
    engine, sessions = await _database()
    try:
        async with sessions() as session:
            await _seed(session)
            await run_journaled_v2_shadow_chain(
                session,
                evaluated_at=EVALUATED_AT,
                vertical="smartphones",
                limit=1,
                apply=True,
            )

            dry = await compare_dark_window(
                session,
                evaluated_at=EVALUATED_AT,
                limit=1,
            )
            assert dry.scanned == 1
            assert dry.core_candidates == 1
            assert dry.v2_candidates == 1
            assert dry.intersections == 1
            assert dry.top1_matches == 1
            assert dry.complete == 1
            assert dry.observations_created == 0
            assert await session.scalar(
                select(func.count()).select_from(V2DarkReadObservation)
            ) == 0

            applied = await compare_dark_window(
                session,
                evaluated_at=EVALUATED_AT,
                limit=1,
                apply=True,
            )
            replay = await compare_dark_window(
                session,
                evaluated_at=EVALUATED_AT,
                limit=1,
                apply=True,
            )
            stored = await session.scalar(select(V2DarkReadObservation))

            assert applied.observations_created == 1
            assert replay.observations_created == 0
            assert replay.observations_existing == 1
            assert replay.evaluation_id == applied.evaluation_id
            assert stored is not None
            assert stored.raw_query_retained is False
            assert stored.query_digest.startswith("sha256:")
            assert stored.core_candidate_count == 1
            assert stored.v2_candidate_count == 1
            assert stored.intersection_count == 1
            assert stored.overlap_ppm == 1_000_000
            assert stored.top1_state == "MATCH"
            assert not hasattr(stored, "raw_query")
            assert not hasattr(stored, "candidate_ids_json")
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_dark_reader_fails_closed_on_query_digest_drift() -> None:
    engine, sessions = await _database()
    try:
        async with sessions() as session:
            await _seed(session)
            await run_journaled_v2_shadow_chain(
                session,
                evaluated_at=EVALUATED_AT,
                vertical="smartphones",
                limit=1,
                apply=True,
            )
            retrieval = await session.scalar(select(HybridRetrievalRun))
            assert retrieval is not None
            retrieval.query_digest = "sha256:" + "f" * 64
            await session.commit()

            report = await compare_dark_window(
                session,
                evaluated_at=EVALUATED_AT,
                limit=1,
            )

            assert report.invalid == 1
            assert report.core_candidates == 0
            assert report.top1_matches == 0
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_dark_reader_refuses_unstable_catalogue() -> None:
    engine, sessions = await _database()
    try:
        async with sessions() as session:
            session.add(
                core_models.CatalogSyncRun(
                    trigger="scheduler",
                    status="running",
                    heartbeat_at=EVALUATED_AT.replace(tzinfo=None),
                )
            )
            await session.commit()

            with pytest.raises(V2DarkReaderError, match="catalog sync"):
                await compare_dark_window(
                    session,
                    evaluated_at=EVALUATED_AT,
                    limit=1,
                )
    finally:
        await engine.dispose()


@pytest.mark.parametrize(
    ("settings", "apply", "message"),
    (
        (
            SimpleNamespace(
                database_schema_mode="legacy",
                v2_chain_mode="shadow",
                v2_canary_reader_enabled=False,
                v2_public_reader_enabled=False,
            ),
            False,
            "DATABASE_SCHEMA_MODE=alembic",
        ),
        (
            SimpleNamespace(
                database_schema_mode="alembic",
                v2_chain_mode="off",
                v2_canary_reader_enabled=False,
                v2_public_reader_enabled=False,
            ),
            False,
            "V2_CHAIN_MODE=dark",
        ),
        (
            SimpleNamespace(
                database_schema_mode="alembic",
                v2_chain_mode="dark",
                v2_canary_reader_enabled=True,
                v2_public_reader_enabled=False,
            ),
            False,
            "forbids canary/public readers",
        ),
    ),
)
def test_dark_reader_configuration_fails_closed(
    settings,
    apply: bool,
    message: str,
    monkeypatch,
) -> None:
    monkeypatch.setattr(dark_reader, "get_settings", lambda: settings)

    with pytest.raises(RuntimeError, match=message):
        dark_reader._validate_configuration(apply=apply)


def test_dark_reader_is_not_wired_to_public_routes() -> None:
    public_routes = "\n".join(
        path.read_text(encoding="utf-8") for path in ROUTES_ROOT.glob("*.py")
    )

    assert "v2_chain.dark_reader" not in public_routes
    assert "V2DarkReadObservation" not in public_routes
