"""Gates P0.e : raw immuable, projection déterministe et quarantaine."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import Settings
from app.core.error_taxonomy import ProductErrorCode
from app.core.observability import product_intelligence_metrics
from app.db import models as core_models  # noqa: F401
from app.db.base import Base
from app.observations import models
from app.observations.awin import (
    capture_awin_row,
    project_awin_row,
    replay_raw_source,
    shadow_counts,
)
from app.services import awin_catalog


VALID_ROW = {
    "aw_product_id": "sony-xm6-black",
    "product_name": "Sony WH-1000XM6 Black",
    "brand_name": "Sony",
    "merchant_category": "Headphones",
    "merchant_image_url": "https://merchant.test/xm6.jpg",
    "aw_deep_link": "https://merchant.test/xm6",
    "search_price": "449,00 EUR",
    "currency": "eur",
    "ean": "4006381333931",
    "in_stock": "yes",
}


@pytest.mark.asyncio
async def test_same_source_record_is_idempotent_inside_a_resumed_sync_run():
    engine, maker = await _session()
    try:
        async with maker() as session:
            now = datetime.now(UTC).replace(tzinfo=None)
            run = core_models.CatalogSyncRun(
                trigger="scheduler",
                status="running",
                heartbeat_at=now,
            )
            session.add(run)
            await session.flush()

            first = await capture_awin_row(
                session,
                VALID_ROW,
                feed_id="42",
                merchant_id=77,
                merchant_name="Marchand test",
                offer_id=None,
                sync_run_id=run.id,
                observed_at=now,
            )
            second = await capture_awin_row(
                session,
                VALID_ROW,
                feed_id="42",
                merchant_id=77,
                merchant_name="Marchand test",
                offer_id=None,
                sync_run_id=run.id,
                observed_at=now + timedelta(minutes=10),
            )
            await session.commit()

            assert first.raw_created is True
            assert second.raw_created is False
            assert second.raw_source_record_id == first.raw_source_record_id
            assert second.observations_created == 0
            assert await shadow_counts(session) == {
                "raw_sources": 1,
                "observations": 10,
                "quarantine_open": 0,
            }
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_successor_run_reuses_predecessor_raw_source_record():
    engine, maker = await _session()
    try:
        async with maker() as session:
            now = datetime.now(UTC).replace(tzinfo=None)
            predecessor = core_models.CatalogSyncRun(
                trigger="scheduler",
                status="interrupted",
                heartbeat_at=now,
                finished_at=now,
                failure_reason="interrupted",
            )
            session.add(predecessor)
            await session.flush()
            successor = core_models.CatalogSyncRun(
                resumed_from_run_id=predecessor.id,
                trigger="scheduler",
                status="running",
                heartbeat_at=now,
            )
            session.add(successor)
            await session.flush()

            first = await capture_awin_row(
                session,
                VALID_ROW,
                feed_id="42",
                merchant_id=77,
                merchant_name="Marchand test",
                offer_id=None,
                sync_run_id=predecessor.id,
                observed_at=now,
            )
            second = await capture_awin_row(
                session,
                VALID_ROW,
                feed_id="42",
                merchant_id=77,
                merchant_name="Marchand test",
                offer_id=None,
                sync_run_id=successor.id,
                resume_from_run_id=predecessor.id,
                observed_at=now + timedelta(minutes=10),
            )
            await session.commit()

            assert first.raw_created is True
            assert second.raw_created is False
            assert second.raw_source_record_id == first.raw_source_record_id
            assert second.observations_created == 0
            assert await shadow_counts(session) == {
                "raw_sources": 1,
                "observations": 10,
                "quarantine_open": 0,
            }
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_pre_checkpoint_run_infers_only_the_latest_feed_as_partial():
    engine, maker = await _session()
    try:
        async with maker() as session:
            now = datetime.now(UTC).replace(tzinfo=None)
            run = core_models.CatalogSyncRun(
                trigger="scheduler",
                status="running",
                heartbeat_at=now,
            )
            session.add(run)
            await session.flush()
            await capture_awin_row(
                session,
                VALID_ROW,
                feed_id="41",
                merchant_id=77,
                merchant_name="Marchand test",
                offer_id=None,
                sync_run_id=run.id,
                observed_at=now,
            )
            later_row = {**VALID_ROW, "aw_product_id": "sony-xm6-silver"}
            await capture_awin_row(
                session,
                later_row,
                feed_id="42",
                merchant_id=77,
                merchant_name="Marchand test",
                offer_id=None,
                sync_run_id=run.id,
                observed_at=now + timedelta(minutes=10),
            )
            await session.commit()

            checkpoints = await awin_catalog._load_or_infer_feed_checkpoints(
                session,
                sync_run_id=run.id,
            )

            assert checkpoints["41"].status == "succeeded"
            assert checkpoints["41"].rows_count == 1
            assert checkpoints["42"].status == "running"
            assert checkpoints["42"].rows_count == 1
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_successor_run_clones_predecessor_feed_checkpoints():
    engine, maker = await _session()
    try:
        async with maker() as session:
            now = datetime.now(UTC).replace(tzinfo=None)
            predecessor = core_models.CatalogSyncRun(
                trigger="scheduler",
                status="interrupted",
                heartbeat_at=now,
                finished_at=now,
                failure_reason="interrupted",
            )
            session.add(predecessor)
            await session.flush()
            session.add_all(
                [
                    core_models.CatalogSyncFeedCheckpoint(
                        sync_run_id=predecessor.id,
                        feed_id="41",
                        status="succeeded",
                        rows_count=3,
                        started_at=now,
                        heartbeat_at=now,
                        finished_at=now,
                    ),
                    core_models.CatalogSyncFeedCheckpoint(
                        sync_run_id=predecessor.id,
                        feed_id="42",
                        status="running",
                        rows_count=1,
                        started_at=now,
                        heartbeat_at=now,
                    ),
                ]
            )
            successor = core_models.CatalogSyncRun(
                resumed_from_run_id=predecessor.id,
                trigger="scheduler",
                status="running",
                heartbeat_at=now,
            )
            session.add(successor)
            await session.commit()

            checkpoints = await awin_catalog._load_or_infer_feed_checkpoints(
                session,
                sync_run_id=successor.id,
                resume_from_run_id=predecessor.id,
            )

            assert checkpoints["41"].sync_run_id == successor.id
            assert checkpoints["41"].status == "succeeded"
            assert checkpoints["41"].rows_count == 3
            assert checkpoints["42"].sync_run_id == successor.id
            assert checkpoints["42"].status == "running"
            assert checkpoints["42"].rows_count == 1
            assert checkpoints["42"].finished_at is None
    finally:
        await engine.dispose()
OBSERVED_AT = datetime(2026, 8, 28, 18, 30, 0)


def _by_field(projection):
    return {observation.field: observation for observation in projection.observations}


async def _session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    return engine, maker


def test_projection_is_deterministic_and_keeps_money_explicit():
    first = project_awin_row(
        VALID_ROW,
        feed_id="42",
        merchant_id=7,
        merchant_name="Marchand test",
        observed_at=OBSERVED_AT,
    )
    second = project_awin_row(
        dict(reversed(VALID_ROW.items())),
        feed_id="42",
        merchant_id=7,
        merchant_name="Marchand test",
        observed_at=OBSERVED_AT,
    )

    assert first == second
    assert len(first.payload_checksum) == 64
    assert len(first.replay_key) == 64
    fields = _by_field(first)
    assert fields["gtin"].value == "4006381333931"
    assert fields["price"].value == {"amount": "449.00", "currency": "EUR"}
    assert fields["availability"].value == "in_stock"
    assert fields["price"].status == "verified"
    assert first.issues == ()


def test_unknown_and_invalid_values_never_become_favourable_claims():
    projection = project_awin_row(
        {
            "aw_product_id": "",
            "product_name": "",
            "search_price": "-12,00",
            "currency": "",
            "ean": "4006381333932",
            "in_stock": "perhaps",
        },
        feed_id="bad-feed",
        merchant_id=9,
        observed_at=OBSERVED_AT,
    )
    fields = _by_field(projection)

    assert fields["price"].status == "unknown"
    assert fields["price"].value is None
    assert fields["availability"].status == "unknown"
    assert fields["availability"].value is None
    assert fields["gtin"].status == "unknown"
    assert fields["gtin"].value is None
    assert [
        (issue.error_code, issue.stage, issue.field, issue.rejected_value)
        for issue in projection.issues
    ] == [
        (
            ProductErrorCode.SCHEMA_INVALID,
            "schema_validation",
            "aw_product_id",
            None,
        ),
        (
            ProductErrorCode.SCHEMA_INVALID,
            "schema_validation",
            "product_name",
            None,
        ),
        (
            ProductErrorCode.INVALID_IDENTIFIER,
            "identifier_validation",
            "ean",
            "4006381333932",
        ),
        (
            ProductErrorCode.WRONG_PRICE,
            "price_validation",
            "search_price",
            "-12,00",
        ),
        (
            ProductErrorCode.WRONG_STOCK,
            "availability_validation",
            "in_stock",
            "perhaps",
        ),
    ]


def test_sensitive_source_keys_are_redacted_before_persistence():
    projection = project_awin_row(
        {**VALID_ROW, "api_token": "must-not-leak"},
        feed_id="42",
        merchant_id=7,
        observed_at=OBSERVED_AT,
    )

    assert projection.payload["api_token"] == "[REDACTED]"
    assert "must-not-leak" not in str(projection.payload)


@pytest.mark.asyncio
async def test_capture_and_replay_are_idempotent_and_versioned():
    engine, maker = await _session()
    product_intelligence_metrics.reset()
    try:
        async with maker() as session:
            first = await capture_awin_row(
                session,
                VALID_ROW,
                feed_id="42",
                merchant_id=7,
                merchant_name="Marchand test",
                offer_id=None,
                sync_run_id=None,
                observed_at=OBSERVED_AT,
            )
            second = await capture_awin_row(
                session,
                VALID_ROW,
                feed_id="42",
                merchant_id=7,
                merchant_name="Marchand test",
                offer_id=None,
                sync_run_id=None,
                observed_at=OBSERVED_AT,
            )
            await session.commit()

            assert first.raw_created is True
            assert first.observations_created == 10
            assert second.raw_created is False
            assert second.observations_created == 0
            assert await shadow_counts(session) == {
                "raw_sources": 1,
                "observations": 10,
                "quarantine_open": 0,
            }
            assert "observation" not in product_intelligence_metrics.snapshot()[
                "pipeline_stages"
            ]

            same_version = await replay_raw_source(session, first.raw_source_record_id)
            next_version = await replay_raw_source(
                session,
                first.raw_source_record_id,
                transformation_version="v2-test",
            )
            await session.commit()

            assert same_version.observations_created == 0
            assert next_version.raw_created is False
            assert next_version.observations_created == 10
            assert (await shadow_counts(session))["observations"] == 20
            observation_stage = product_intelligence_metrics.snapshot()[
                "pipeline_stages"
            ]["observation"]
            assert observation_stage["executions"] == 2
            assert observation_stage["outcomes"] == {"ok": 2}
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_quarantine_keeps_raw_and_replay_detects_tampering():
    engine, maker = await _session()
    try:
        async with maker() as session:
            captured = await capture_awin_row(
                session,
                {"search_price": "abc", "in_stock": "maybe"},
                feed_id="broken",
                merchant_id=11,
                merchant_name=None,
                offer_id=None,
                sync_run_id=None,
                observed_at=OBSERVED_AT,
            )
            await session.commit()

            raw = await session.get(models.RawSourceRecord, captured.raw_source_record_id)
            issues = (
                await session.execute(
                    select(models.QuarantineRecord).where(
                        models.QuarantineRecord.raw_source_record_id == raw.id
                    )
                )
            ).scalars().all()
            assert raw.payload_json["search_price"] == "abc"
            assert captured.quarantine_created == 4
            assert len(issues) == 4
            assert all(issue.status == "open" for issue in issues)
            assert sorted(
                (issue.error_code, issue.stage, issue.field) for issue in issues
            ) == sorted(
                [
                    (
                        ProductErrorCode.SCHEMA_INVALID.value,
                        "schema_validation",
                        "aw_product_id",
                    ),
                    (
                        ProductErrorCode.SCHEMA_INVALID.value,
                        "schema_validation",
                        "product_name",
                    ),
                    (
                        ProductErrorCode.WRONG_PRICE.value,
                        "price_validation",
                        "search_price",
                    ),
                    (
                        ProductErrorCode.WRONG_STOCK.value,
                        "availability_validation",
                        "in_stock",
                    ),
                ]
            )

            raw.payload_json = {**raw.payload_json, "search_price": "1.00"}
            await session.flush()
            with pytest.raises(RuntimeError, match="modifié"):
                await replay_raw_source(session, raw.id)
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_currency_quarantine_replay_is_scoped_and_versioned():
    engine, maker = await _session()
    try:
        async with maker() as session:
            captured = await capture_awin_row(
                session,
                {
                    "aw_product_id": "x",
                    "product_name": "X",
                    "search_price": "12.50",
                    "currency": "EURO",
                    "in_stock": "yes",
                },
                feed_id="42",
                merchant_id=7,
                merchant_name="Marchand test",
                offer_id=None,
                sync_run_id=None,
                observed_at=OBSERVED_AT,
            )
            await session.commit()

            same_version = await replay_raw_source(
                session,
                captured.raw_source_record_id,
            )
            next_version = await replay_raw_source(
                session,
                captured.raw_source_record_id,
                transformation_version="v2-taxonomy-test",
            )
            await session.commit()

            assert captured.quarantine_created == 2
            assert same_version.quarantine_created == 0
            assert next_version.quarantine_created == 2

            issues = (
                await session.execute(
                    select(models.QuarantineRecord).where(
                        models.QuarantineRecord.raw_source_record_id
                        == captured.raw_source_record_id
                    )
                )
            ).scalars().all()
            assert {
                (
                    issue.transformation_version,
                    issue.error_code,
                    issue.stage,
                    issue.field,
                    tuple(sorted((issue.details_json or {}).items())),
                )
                for issue in issues
            } == {
                (
                    version,
                    ProductErrorCode.CURRENCY_MISMATCH.value,
                    stage,
                    field,
                    details,
                )
                for version in ("v1", "v2-taxonomy-test")
                for stage, field, details in (
                    ("currency_validation", "currency", ()),
                    (
                        "price_validation",
                        "search_price",
                        (("parsed_amount", "12.50"),),
                    ),
                )
            }
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_shadow_capture_never_mutates_the_v1_offer():
    engine, maker = await _session()
    try:
        async with maker() as session:
            merchant = core_models.Merchant(
                awin_mid=7,
                name="Marchand test",
                slug="marchand-test",
            )
            session.add(merchant)
            await session.flush()
            offer = core_models.Offer(
                merchant_id=merchant.id,
                awin_product_id="sony-xm6-black",
                name="Sony WH-1000XM6 Black",
                brand="Sony",
                price=449.0,
                currency="EUR",
                in_stock=True,
            )
            session.add(offer)
            await session.commit()
            before = (
                offer.name,
                offer.brand,
                offer.price,
                offer.currency,
                offer.in_stock,
            )

            await capture_awin_row(
                session,
                VALID_ROW,
                feed_id="42",
                merchant_id=merchant.id,
                merchant_name=merchant.name,
                offer_id=offer.id,
                sync_run_id=None,
                observed_at=OBSERVED_AT,
            )
            await session.commit()
            await session.refresh(offer)

            assert (
                offer.name,
                offer.brand,
                offer.price,
                offer.currency,
                offer.in_stock,
            ) == before
            linked = await session.scalar(
                select(models.Observation.offer_id).where(
                    models.Observation.field == "price"
                )
            )
            assert linked == offer.id
    finally:
        await engine.dispose()


def test_shadow_writer_is_opt_in():
    assert Settings().observation_shadow_enabled is False


@pytest.mark.asyncio
@pytest.mark.parametrize("enabled", [False, True])
async def test_feed_ingestion_writes_shadow_only_when_enabled(monkeypatch, enabled):
    engine, maker = await _session()
    try:
        async with maker() as session:
            session.add(
                core_models.Merchant(
                    awin_mid=77,
                    name="Marchand test",
                    slug="marchand-test",
                )
            )
            await session.commit()

            settings = Settings(
                observation_shadow_enabled=enabled,
                awin_regions="BE",
                awin_max_rows_per_feed=0,
                awin_feed_limit=0,
            )

            async def feeds():
                return [
                    awin_catalog.FeedInfo(
                        feed_id="42",
                        advertiser_id=77,
                        advertiser_name="Marchand test",
                        region="BE",
                        products=1,
                    )
                ]

            async def rows(_feed_ids, *, max_rows=0):
                return [VALID_ROW]

            async def legacy_upsert(*_args, **_kwargs):
                return None

            monkeypatch.setattr(awin_catalog, "get_settings", lambda: settings)
            monkeypatch.setattr(awin_catalog, "list_feeds", feeds)
            monkeypatch.setattr(awin_catalog, "_download_feed_rows", rows)
            monkeypatch.setattr(awin_catalog, "_upsert_offer", legacy_upsert)

            heartbeats = 0

            async def progress():
                nonlocal heartbeats
                heartbeats += 1

            result = await awin_catalog.ingest_feeds(
                session,
                sync_run_id=None,
                progress=progress,
            )
            counts = await shadow_counts(session)

            assert result["offers"] == 1
            assert heartbeats == 4
            assert result["shadow"]["enabled"] is enabled
            assert counts["raw_sources"] == (1 if enabled else 0)
            assert counts["observations"] == (10 if enabled else 0)
            assert result["shadow"]["failures"] == 0
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_shadow_failure_rolls_back_its_savepoint_not_the_legacy_offer(monkeypatch):
    engine, maker = await _session()
    product_intelligence_metrics.reset()
    try:
        async with maker() as session:
            merchant = core_models.Merchant(
                awin_mid=77,
                name="Marchand test",
                slug="marchand-test",
            )
            session.add(merchant)
            await session.commit()

            settings = Settings(
                observation_shadow_enabled=True,
                awin_regions="BE",
            )

            async def feeds():
                return [
                    awin_catalog.FeedInfo(
                        feed_id="42",
                        advertiser_id=77,
                        advertiser_name="Marchand test",
                        region="BE",
                        products=1,
                    )
                ]

            async def rows(_feed_ids, *, max_rows=0):
                return [VALID_ROW]

            async def legacy_upsert(db_session, merchant_id, row, **_kwargs):
                offer = core_models.Offer(
                    merchant_id=merchant_id,
                    awin_product_id=row["aw_product_id"],
                    name=row["product_name"],
                    price=449.0,
                    currency="EUR",
                )
                db_session.add(offer)
                await db_session.flush()
                return offer.id

            async def broken_shadow(*_args, **_kwargs):
                raise RuntimeError("shadow failure")

            monkeypatch.setattr(awin_catalog, "get_settings", lambda: settings)
            monkeypatch.setattr(awin_catalog, "list_feeds", feeds)
            monkeypatch.setattr(awin_catalog, "_download_feed_rows", rows)
            monkeypatch.setattr(awin_catalog, "_upsert_offer", legacy_upsert)
            monkeypatch.setattr(
                "app.observations.awin.capture_awin_row",
                broken_shadow,
            )

            result = await awin_catalog.ingest_feeds(session)
            offers = (
                await session.execute(select(core_models.Offer))
            ).scalars().all()

            assert result["shadow"]["failures"] == 1
            assert product_intelligence_metrics.snapshot()["pipeline_stages"][
                "ingestion"
            ]["outcomes"] == {"degraded": 1}
            assert len(offers) == 1
            assert offers[0].awin_product_id == "sony-xm6-black"
            assert await shadow_counts(session) == {
                "raw_sources": 0,
                "observations": 0,
                "quarantine_open": 0,
            }
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_ingestion_resumes_after_a_succeeded_feed_checkpoint(monkeypatch):
    engine, maker = await _session()
    try:
        async with maker() as session:
            merchant = core_models.Merchant(
                awin_mid=77,
                name="Marchand test",
                slug="marchand-test",
            )
            run = core_models.CatalogSyncRun(
                trigger="scheduler",
                status="running",
                heartbeat_at=datetime.now(UTC).replace(tzinfo=None),
            )
            session.add_all([merchant, run])
            await session.flush()
            session.add(
                core_models.CatalogSyncFeedCheckpoint(
                    sync_run_id=run.id,
                    feed_id="41",
                    status="succeeded",
                    rows_count=3,
                )
            )
            await session.commit()

            settings = Settings(
                observation_shadow_enabled=False,
                awin_regions="BE",
                awin_max_rows_per_feed=0,
                awin_feed_limit=0,
            )

            async def feeds():
                return [
                    awin_catalog.FeedInfo("41", 77, "Marchand test", "BE", 3),
                    awin_catalog.FeedInfo("42", 77, "Marchand test", "BE", 1),
                ]

            downloaded: list[str] = []

            async def rows(feed_ids, *, max_rows=0):
                downloaded.extend(feed_ids)
                return [VALID_ROW]

            async def legacy_upsert(*_args, **_kwargs):
                return None

            monkeypatch.setattr(awin_catalog, "get_settings", lambda: settings)
            monkeypatch.setattr(awin_catalog, "list_feeds", feeds)
            monkeypatch.setattr(awin_catalog, "_download_feed_rows", rows)
            monkeypatch.setattr(awin_catalog, "_upsert_offer", legacy_upsert)

            result = await awin_catalog.ingest_feeds(
                session,
                sync_run_id=run.id,
            )

            assert downloaded == ["42"]
            assert result["feeds"] == 2
            assert result["offers"] == 4
            checkpoints = (
                (
                    await session.execute(
                        select(core_models.CatalogSyncFeedCheckpoint).order_by(
                            core_models.CatalogSyncFeedCheckpoint.feed_id
                        )
                    )
                )
                .scalars()
                .all()
            )
            assert [(item.feed_id, item.status, item.rows_count) for item in checkpoints] == [
                ("41", "succeeded", 3),
                ("42", "succeeded", 1),
            ]
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_ingestion_stops_cooperatively_after_a_committed_feed(monkeypatch):
    engine, maker = await _session()
    try:
        async with maker() as session:
            session.add(
                core_models.Merchant(
                    awin_mid=77,
                    name="Marchand test",
                    slug="marchand-test",
                )
            )
            await session.commit()

            settings = Settings(
                observation_shadow_enabled=False,
                awin_regions="BE",
                awin_max_rows_per_feed=0,
                awin_feed_limit=0,
            )

            async def feeds():
                return [
                    awin_catalog.FeedInfo("41", 77, "Marchand test", "BE", 1),
                    awin_catalog.FeedInfo("42", 77, "Marchand test", "BE", 1),
                ]

            downloaded: list[str] = []

            async def rows(feed_ids, *, max_rows=0):
                downloaded.extend(feed_ids)
                return [VALID_ROW]

            async def legacy_upsert(*_args, **_kwargs):
                return None

            monkeypatch.setattr(awin_catalog, "get_settings", lambda: settings)
            monkeypatch.setattr(awin_catalog, "list_feeds", feeds)
            monkeypatch.setattr(awin_catalog, "_download_feed_rows", rows)
            monkeypatch.setattr(awin_catalog, "_upsert_offer", legacy_upsert)

            result = await awin_catalog.ingest_feeds(
                session,
                stop_after_current_feed=True,
            )

            assert downloaded == ["41"]
            assert result["feeds"] == 1
            assert result["selected_feeds"] == 2
            assert result["offers"] == 1
            assert result["stopped_after_feed"] is True
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_bounded_resume_counts_only_selected_checkpoint_offers(monkeypatch):
    engine, maker = await _session()
    try:
        async with maker() as session:
            merchant = core_models.Merchant(
                awin_mid=77,
                name="Marchand test",
                slug="marchand-test",
            )
            run = core_models.CatalogSyncRun(
                trigger="scheduler",
                status="running",
                heartbeat_at=datetime.now(UTC).replace(tzinfo=None),
            )
            session.add_all([merchant, run])
            await session.flush()
            session.add_all(
                [
                    core_models.CatalogSyncFeedCheckpoint(
                        sync_run_id=run.id,
                        feed_id="41",
                        status="succeeded",
                        rows_count=3,
                    ),
                    core_models.CatalogSyncFeedCheckpoint(
                        sync_run_id=run.id,
                        feed_id="42",
                        status="succeeded",
                        rows_count=7,
                    ),
                ]
            )
            await session.commit()

            settings = Settings(
                observation_shadow_enabled=False,
                awin_regions="BE",
                awin_max_rows_per_feed=0,
                awin_feed_limit=1,
            )

            async def feeds():
                return [
                    awin_catalog.FeedInfo("41", 77, "Marchand test", "BE", 3),
                    awin_catalog.FeedInfo("42", 77, "Marchand test", "BE", 7),
                ]

            async def should_not_download(*_args, **_kwargs):
                raise AssertionError("a succeeded checkpoint must not be downloaded")

            monkeypatch.setattr(awin_catalog, "get_settings", lambda: settings)
            monkeypatch.setattr(awin_catalog, "list_feeds", feeds)
            monkeypatch.setattr(
                awin_catalog,
                "_download_feed_rows",
                should_not_download,
            )

            result = await awin_catalog.ingest_feeds(
                session,
                sync_run_id=run.id,
            )

            assert result["feeds"] == 1
            assert result["selected_feeds"] == 1
            assert result["offers"] == 3
            assert result["stopped_after_feed"] is False
    finally:
        await engine.dispose()
