"""Qualification de l'amorçage régional Awin strictement borné."""

from __future__ import annotations

from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import models as core_models
from app.db.base import Base
from app.ingest import regional_seed
from app.services import awin_catalog


def test_regional_seed_scope_is_explicit_and_bounded() -> None:
    assert regional_seed._validate_scope(
        region="be",
        feed_ids=["111943"],
        row_limit=500,
    ) == ("BE", ("111943",), 500)

    with pytest.raises(ValueError, match="ISO"):
        regional_seed._validate_scope(region="Belgium", feed_ids=["1"], row_limit=1)
    with pytest.raises(ValueError, match="unique"):
        regional_seed._validate_scope(region="BE", feed_ids=["1", "1"], row_limit=1)
    with pytest.raises(ValueError, match="between"):
        regional_seed._validate_scope(region="BE", feed_ids=["1"], row_limit=20_001)


async def test_preflight_accepts_only_a_joined_feed_in_the_requested_region(
    monkeypatch,
) -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with maker() as session:
            session.add(
                core_models.Merchant(
                    awin_mid=77,
                    name="Marchand belge",
                    slug="marchand-belge",
                    region="BE",
                    joined=True,
                )
            )
            await session.commit()
            monkeypatch.setattr(
                awin_catalog,
                "list_feeds",
                AsyncMock(
                    return_value=[
                        awin_catalog.FeedInfo("41", 77, "Marchand belge", "BE", 500),
                        awin_catalog.FeedInfo("42", 77, "Marchand belge", "NL", 700),
                    ]
                ),
            )

            assert await regional_seed._scope_state(
                session,
                region="BE",
                feed_ids=("41",),
            ) == ("ready", 500)
            assert await regional_seed._scope_state(
                session,
                region="BE",
                feed_ids=("42",),
            ) == ("feed_scope_unavailable", 0)
    finally:
        await engine.dispose()


async def test_apply_uses_the_exact_preflighted_scope(monkeypatch) -> None:
    checked = regional_seed.RegionalSeedReceipt(
        schema_version="regional-catalog-seed-receipt/v1",
        status="ready",
        region="BE",
        feed_ids=("111943",),
        row_limit=500,
        declared_products=2_324,
    )
    monkeypatch.setattr(regional_seed, "preflight", AsyncMock(return_value=checked))

    fake_session = object()

    @asynccontextmanager
    async def session_scope():
        yield fake_session

    monkeypatch.setattr(regional_seed.db, "session_scope", session_scope)
    run = AsyncMock(
        return_value={
            "started": True,
            "run": {
                "id": 29,
                "status": "succeeded",
                "feeds": 1,
                "offers": 500,
                "skipped_feeds": 0,
            },
        }
    )
    monkeypatch.setattr(regional_seed.catalog_sync, "run_catalog_sync", run)

    receipt = await regional_seed.run_once(
        region="BE",
        feed_ids=["111943"],
        row_limit=500,
    )

    assert receipt.status == "succeeded"
    assert receipt.catalog_run_id == 29
    assert receipt.raw_payload_retained is False
    run.assert_awaited_once_with(
        fake_session,
        trigger="regional_seed",
        limit_override=1,
        region_override="BE",
        feed_ids_override=("111943",),
        max_rows_override=500,
    )


async def test_ingestion_downloads_only_the_exact_regional_feed(monkeypatch) -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with maker() as session:
            session.add(
                core_models.Merchant(
                    awin_mid=77,
                    name="Marchand belge",
                    slug="marchand-belge",
                    joined=True,
                )
            )
            await session.commit()
            settings = SimpleNamespace(
                awin_regions_list=["FR"],
                awin_max_rows_per_feed=1_000,
                awin_feed_limit=0,
                observation_shadow_enabled=False,
                product_graph_shadow_enabled=False,
                offer_graph_shadow_enabled=False,
            )
            monkeypatch.setattr(awin_catalog, "get_settings", lambda: settings)
            monkeypatch.setattr(
                awin_catalog,
                "list_feeds",
                AsyncMock(
                    return_value=[
                        awin_catalog.FeedInfo("41", 77, "Marchand belge", "BE", 500),
                        awin_catalog.FeedInfo("42", 77, "Marchand belge", "FR", 700),
                    ]
                ),
            )
            download = AsyncMock(return_value=[{"product_name": "Produit"}])
            monkeypatch.setattr(awin_catalog, "_download_feed_rows", download)
            monkeypatch.setattr(
                awin_catalog,
                "_upsert_offer",
                AsyncMock(return_value=None),
            )

            receipt = await awin_catalog.ingest_feeds(
                session,
                region_override="BE",
                feed_ids_override=("41",),
                max_rows_override=500,
            )

            assert receipt["feeds"] == 1
            assert receipt["offers"] == 1
            download.assert_awaited_once_with(["41"], max_rows=500)

            with pytest.raises(RuntimeError, match="scope is unavailable"):
                await awin_catalog.ingest_feeds(
                    session,
                    region_override="BE",
                    feed_ids_override=("42",),
                    max_rows_override=500,
                )
    finally:
        await engine.dispose()
