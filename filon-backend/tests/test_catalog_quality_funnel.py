"""Preuves du Catalog Quality Funnel interne et fail-closed."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.catalog_quality.funnel import (
    FUNNEL_STAGES,
    MAX_FUNNEL_ROWS,
    _run,
    build_catalog_quality_funnel,
    parse_evaluated_at,
)
from app.db import models as core_models
from app.db.base import Base
from app.observations.models import RawSourceRecord
from app.offer_graph.models import GraphOfferObservation
from app.offer_graph.projection import (
    PROJECTION_VERSION as OFFER_PROJECTION_VERSION,
    persist_awin_offer_projection,
    project_awin_offer,
)
from app.product_graph.models import (
    GraphOfferVariantLink,
    GraphProductModel,
    GraphVariant,
)
from app.product_graph.resolution import (
    persist_awin_graph_projection,
    project_awin_variant,
)


EVALUATED_AT = datetime(2026, 8, 30, 20, 0, 0)
EXACT_GTIN = "4006381333931"


async def _session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    return engine, async_sessionmaker(engine, expire_on_commit=False)


async def _capture(
    session,
    suffix: str,
    *,
    observed_at: datetime,
    ean: str | None = EXACT_GTIN,
    stock: str = "yes",
    classified: bool = True,
    offer: core_models.Offer | None = None,
):
    if offer is None:
        merchant = core_models.Merchant(
            awin_mid=20_000 + ord(suffix),
            name=f"Funnel Merchant {suffix}",
            slug=f"funnel-merchant-{suffix}",
            joined=True,
        )
        session.add(merchant)
        await session.flush()
        offer = core_models.Offer(
            merchant_id=merchant.id,
            awin_product_id=f"funnel-offer-{suffix}",
            name=f"Funnel Offer {suffix}",
            filon_category="informatique" if classified else None,
            filon_subcategory="ordinateurs" if classified else None,
            offer_kind="physical_product" if classified else None,
        )
        session.add(offer)
        await session.flush()
    payload = {
        "ean": ean,
        "search_price": "49.90",
        "currency": "EUR",
        "in_stock": stock,
        "aw_deep_link": f"https://merchant-{suffix}.filon.shop/item",
    }
    raw = RawSourceRecord(
        source_type="awin_feed",
        source_ref=f"awin-feed:funnel-{suffix}",
        source_record_key=f"funnel-record-{suffix}",
        schema_version="awin-create-a-feed-v1",
        context_json={"feed_id": suffix, "merchant_id": offer.merchant_id},
        payload_json=payload,
        payload_checksum=(suffix.lower() * 64),
        replay_key=(suffix.upper() * 64),
        sync_run_id=None,
        observed_at=observed_at,
    )
    session.add(raw)
    await session.flush()
    await persist_awin_graph_projection(
        session,
        projection=project_awin_variant(payload),
        raw_source_record_id=raw.id,
        offer_id=offer.id,
        source_ref=raw.source_ref,
        observed_at=observed_at,
    )
    await persist_awin_offer_projection(
        session,
        projection=project_awin_offer(payload),
        raw_source_record_id=raw.id,
        offer_id=offer.id,
        observed_at=observed_at,
    )
    observation = await session.scalar(
        select(GraphOfferObservation).where(
            GraphOfferObservation.raw_source_record_id == raw.id
        )
    )
    assert observation is not None
    return raw, offer, observation


def _by_code(rows):
    return {row.code: row for row in rows}


@pytest.mark.asyncio
async def test_funnel_measures_only_technical_truth_and_blocks_human_dependent_stages():
    engine, maker = await _session()
    try:
        async with maker() as session:
            first_raw, first_offer, _ = await _capture(
                session,
                "a",
                observed_at=EVALUATED_AT - timedelta(hours=1),
            )
            await _capture(
                session,
                "b",
                observed_at=EVALUATED_AT - timedelta(hours=2),
            )
            await _capture(
                session,
                "c",
                observed_at=EVALUATED_AT - timedelta(hours=3),
                ean=None,
                classified=False,
            )
            await _capture(
                session,
                "d",
                observed_at=EVALUATED_AT - timedelta(hours=73),
            )
            await _capture(
                session,
                "e",
                observed_at=EVALUATED_AT - timedelta(hours=1),
                stock="no",
            )
            model = GraphProductModel(
                model_key="funnel:model:shared",
                canonical_name="Human review pending",
            )
            session.add(model)
            await session.flush()
            variant = await session.scalar(
                select(GraphVariant).where(
                    GraphVariant.variant_key == f"gtin:{EXACT_GTIN}"
                )
            )
            assert variant is not None
            variant.model_id = model.id
            session.add(
                core_models.PriceSnapshot(
                    offer_id=first_offer.id,
                    price=59.90,
                    currency="EUR",
                    in_stock=True,
                    captured_at=EVALUATED_AT - timedelta(days=31),
                )
            )
            await session.commit()

            report = await build_catalog_quality_funnel(
                session,
                evaluated_at=EVALUATED_AT,
            )
            stages = _by_code(report.stages)
            signals = _by_code(report.technical_signals)

            assert tuple(stages) == FUNNEL_STAGES
            assert (
                stages["RAW_OFFERS"].qualified_count,
                stages["RAW_OFFERS"].denominator_count,
            ) == (5, 5)
            assert (
                stages["ACTIVE_OFFERS"].qualified_count,
                stages["ACTIVE_OFFERS"].denominator_count,
            ) == (3, 5)
            assert (
                stages["VALID_PRICE"].qualified_count,
                stages["VALID_PRICE"].denominator_count,
            ) == (3, 3)
            assert (
                stages["VALID_MERCHANT"].qualified_count,
                stages["VALID_MERCHANT"].denominator_count,
            ) == (3, 3)
            assert stages["CORRECTLY_CLASSIFIED"].status == "not_measurable"
            assert stages["CORRECTLY_CLASSIFIED"].qualified_count is None
            assert stages["CORRECTLY_CLASSIFIED"].denominator_count == 3
            assert all(
                stage.status == "blocked"
                and stage.qualified_count is None
                and stage.denominator_count is None
                for stage in report.stages[5:]
            )

            assert signals["OFFER_GRAPH_OBSERVED"].observed_count == 5
            assert signals["CURRENT_OFFER_OBSERVATIONS"].observed_count == 5
            assert signals["CLASSIFICATION_FIELDS_PRESENT"].observed_count == 2
            assert signals["RESOLVED_PRODUCT"].observed_count == 2
            assert signals["RESOLVED_VARIANT"].observed_count == 2
            assert signals["MULTI_MERCHANT_COMPARABLE"].observed_count == 2
            assert signals["30D_HISTORY"].observed_count == 1
            assert signals["COMPLETE_LANDED_COST"].status == "not_supported"
            assert signals["COMPLETE_LANDED_COST"].observed_count is None
            assert signals["DECISION_ELIGIBLE"].observed_count == 0
            assert report.last_raw_source_id == first_raw.id + 4
            assert report.launch_gate_eligible is False
            assert report.report_fingerprint.startswith("sha256:")

            replay = await build_catalog_quality_funnel(
                session,
                evaluated_at=EVALUATED_AT,
            )
            assert replay == report
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_funnel_uses_latest_observation_per_offer_without_hiding_raw_volume():
    engine, maker = await _session()
    try:
        async with maker() as session:
            _old_raw, offer, _ = await _capture(
                session,
                "f",
                observed_at=EVALUATED_AT - timedelta(hours=2),
            )
            await _capture(
                session,
                "g",
                observed_at=EVALUATED_AT - timedelta(hours=1),
                stock="no",
                offer=offer,
            )
            await session.commit()

            report = await build_catalog_quality_funnel(
                session,
                evaluated_at=EVALUATED_AT,
            )
            stages = _by_code(report.stages)
            signals = _by_code(report.technical_signals)

            assert report.raw_source_records == 2
            assert report.offer_observations == 2
            assert report.current_offer_observations == 1
            assert stages["ACTIVE_OFFERS"].qualified_count == 0
            assert signals["CURRENT_OFFER_OBSERVATIONS"].observed_count == 1
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_funnel_ignores_obsolete_projection_and_resolver_versions():
    engine, maker = await _session()
    try:
        async with maker() as session:
            _raw, _offer, observation = await _capture(
                session,
                "h",
                observed_at=EVALUATED_AT - timedelta(hours=1),
            )
            observation.projection_version = "obsolete-offer-projection"
            await session.commit()

            obsolete_offer_report = await build_catalog_quality_funnel(
                session,
                evaluated_at=EVALUATED_AT,
            )
            assert obsolete_offer_report.raw_source_records == 1
            assert obsolete_offer_report.offer_observations == 0
            assert _by_code(obsolete_offer_report.stages)[
                "ACTIVE_OFFERS"
            ].qualified_count == 0

            observation.projection_version = OFFER_PROJECTION_VERSION
            link = await session.get(
                GraphOfferVariantLink,
                observation.offer_variant_link_id,
            )
            assert link is not None
            link.resolver_version = "obsolete-resolver"
            await session.commit()

            obsolete_resolver_report = await build_catalog_quality_funnel(
                session,
                evaluated_at=EVALUATED_AT,
            )
            assert _by_code(obsolete_resolver_report.stages)[
                "VALID_MERCHANT"
            ].qualified_count == 1
            assert _by_code(obsolete_resolver_report.technical_signals)[
                "RESOLVED_VARIANT"
            ].observed_count == 0
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_empty_window_remains_fail_closed():
    engine, maker = await _session()
    try:
        async with maker() as session:
            report = await build_catalog_quality_funnel(
                session,
                evaluated_at=EVALUATED_AT,
                after_raw_id=99,
                limit=1,
            )
            stages = _by_code(report.stages)

            assert stages["RAW_OFFERS"].qualified_count == 0
            assert stages["ACTIVE_OFFERS"].qualified_count == 0
            assert stages["CORRECTLY_CLASSIFIED"].status == "not_measurable"
            assert report.launch_gate_eligible is False
    finally:
        await engine.dispose()


def test_funnel_input_contract_is_strict():
    assert parse_evaluated_at("2026-08-30T20:00:00Z") == EVALUATED_AT
    with pytest.raises(ValueError, match="explicit UTC offset"):
        parse_evaluated_at("2026-08-30T20:00:00")
    with pytest.raises(ValueError, match="ISO-8601"):
        parse_evaluated_at("not-a-date")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("after_raw_id", "limit"),
    [(-1, 1), (True, 1), (0, 0), (0, MAX_FUNNEL_ROWS + 1), (0, True)],
)
async def test_funnel_rejects_unbounded_or_ambiguous_windows(after_raw_id, limit):
    engine, maker = await _session()
    try:
        async with maker() as session:
            with pytest.raises(ValueError):
                await build_catalog_quality_funnel(
                    session,
                    evaluated_at=EVALUATED_AT,
                    after_raw_id=after_raw_id,
                    limit=limit,
                )
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_funnel_rejects_timezone_aware_internal_timestamp():
    engine, maker = await _session()
    try:
        async with maker() as session:
            with pytest.raises(ValueError, match="UTC-naive internally"):
                await build_catalog_quality_funnel(
                    session,
                    evaluated_at=EVALUATED_AT.replace(tzinfo=UTC),
                )
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_funnel_cli_refuses_legacy_schema_mode_before_database_access(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.catalog_quality.funnel.get_settings",
        lambda: SimpleNamespace(debug=False, database_schema_mode="legacy"),
    )
    with pytest.raises(RuntimeError, match="read-only Alembic mode"):
        await _run(
            SimpleNamespace(
                evaluated_at="2026-08-30T20:00:00Z",
                after_raw_id=0,
                limit=1,
            )
        )
