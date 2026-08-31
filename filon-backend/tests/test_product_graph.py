"""Preuves du Product/Variant Graph exact-GTIN en shadow."""

from __future__ import annotations

from datetime import datetime

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import models as core_models
from app.db.base import Base
from app.core.config import Settings
from app.observations import models as observation_models
from app.product_graph import models
from app.product_graph.backfill import backfill_batch
from app.product_graph.resolution import (
    ProductGraphResolutionError,
    attach_offer_to_candidates,
    persist_awin_graph_projection,
    project_awin_variant,
    resolve_entity_pair,
    resolve_variant_observation,
)
from app.services import awin_catalog


OBSERVED_AT = datetime(2026, 8, 30, 18, 0, 0)


async def _session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    return engine, maker


async def _raw_and_offer(
    session,
    suffix: str,
    *,
    ean: str = "4006381333931",
):
    merchant = core_models.Merchant(
        awin_mid=100 + sum(ord(character) for character in suffix),
        name=f"Merchant {suffix}",
        slug=f"merchant-{suffix}",
    )
    session.add(merchant)
    await session.flush()
    offer = core_models.Offer(
        merchant_id=merchant.id,
        awin_product_id=f"offer-{suffix}",
        name=f"Offer {suffix}",
    )
    session.add(offer)
    await session.flush()
    raw = observation_models.RawSourceRecord(
        source_type="awin_feed",
        source_ref=f"awin-feed:{suffix}",
        source_record_key=f"record-{suffix}",
        schema_version="awin-create-a-feed-v1",
        context_json={"feed_id": suffix, "merchant_id": merchant.id},
        payload_json={"ean": ean},
        payload_checksum=(suffix[0] * 64),
        replay_key=(suffix[-1] * 64),
        sync_run_id=None,
        observed_at=OBSERVED_AT,
    )
    session.add(raw)
    await session.flush()
    return raw, offer


async def _link_raw_offer(session, raw, offer) -> None:
    session.add(
        observation_models.Observation(
            raw_source_record_id=raw.id,
            subject_type="merchant_offer",
            subject_ref=f"offer:{offer.id}",
            offer_id=offer.id,
            field="gtin",
            value_json=raw.payload_json.get("ean"),
            status="verified",
            source_type="awin_feed",
            source_ref=raw.source_ref,
            observed_at=raw.observed_at,
            transformation="awin_offer_observation",
            transformation_version="v1",
            confidence=1.0,
        )
    )
    await session.flush()


def test_variant_resolution_uses_only_one_exact_global_identifier():
    resolved = resolve_variant_observation(
        {
            "name": "ignored product title",
            "brand": "ignored brand",
            "identifiers": {"ean": "4006381333931"},
            "attributes": {"capacity": " 128 GB ", "unknown": None},
        }
    )
    assert resolved.prediction() == {
        "expected_variant": {
            "variant_key": "gtin:4006381333931",
            "attributes": {"capacity": "128 GB"},
            "resolution": "resolved",
        }
    }
    assert resolved.reason_code == "exact_gtin"

    assert resolve_variant_observation(
        {"identifiers": {"ean": "not-a-gtin"}}
    ).reason_code == "invalid_gtin"
    conflicting = resolve_variant_observation(
        {
            "identifiers": {
                "ean": "4006381333931",
                "gtin": "9780201379624",
            }
        }
    )
    assert conflicting.resolution == "ambiguous"
    assert conflicting.variant_key is None

    same = resolve_entity_pair(
        {"identifiers": {"ean": "4006381333931"}},
        {"identifiers": {"gtin": "4006381333931"}},
    )
    assert same.prediction() == {
        "product_relation": "same",
        "variant_relation": "same",
    }
    different_gtins = resolve_entity_pair(
        {"identifiers": {"ean": "4006381333931"}},
        {"identifiers": {"gtin": "9780201379624"}},
    )
    assert different_gtins.prediction() == {
        "product_relation": "ambiguous",
        "variant_relation": "ambiguous",
    }


def test_offer_attachment_never_uses_title_or_brand_as_a_fallback():
    base_candidate = {
        "variant_id": "variant-xm6",
        "identifiers": {"gtin": "4006381333931"},
    }
    attached = attach_offer_to_candidates(
        {
            "name": "completely different title",
            "brand": "different brand",
            "identifiers": {"ean": "4006381333931"},
            "variant_candidates": [base_candidate],
        }
    )
    assert attached.prediction() == {
        "expected_variant_id": "variant-xm6",
        "eligibility": "eligible",
    }

    rejected = attach_offer_to_candidates(
        {
            "name": "same title does not matter",
            "identifiers": {"ean": "9780201379624"},
            "variant_candidates": [base_candidate],
        }
    )
    assert rejected.prediction() == {
        "expected_variant_id": None,
        "eligibility": "reject",
    }

    with pytest.raises(ProductGraphResolutionError, match="1-100"):
        attach_offer_to_candidates(
            {
                "identifiers": {"ean": "4006381333931"},
                "variant_candidates": [],
            }
        )


@pytest.mark.asyncio
async def test_graph_persistence_is_idempotent_and_keeps_evidence_append_only():
    engine, maker = await _session()
    try:
        async with maker() as session:
            first_raw, first_offer = await _raw_and_offer(session, "a")
            projection = project_awin_variant({"ean": "4006381333931"})
            first = await persist_awin_graph_projection(
                session,
                projection=projection,
                raw_source_record_id=first_raw.id,
                offer_id=first_offer.id,
                source_ref=first_raw.source_ref,
                observed_at=OBSERVED_AT,
            )
            replay = await persist_awin_graph_projection(
                session,
                projection=projection,
                raw_source_record_id=first_raw.id,
                offer_id=first_offer.id,
                source_ref=first_raw.source_ref,
                observed_at=OBSERVED_AT,
            )
            second_raw, second_offer = await _raw_and_offer(session, "b")
            second = await persist_awin_graph_projection(
                session,
                projection=projection,
                raw_source_record_id=second_raw.id,
                offer_id=second_offer.id,
                source_ref=second_raw.source_ref,
                observed_at=OBSERVED_AT,
            )
            await session.commit()

            assert first.variant_created is True
            assert first.identifier_created is True
            assert replay.link_created is False
            assert second.variant_created is False
            assert second.identifier_created is False
            assert int(
                await session.scalar(select(func.count()).select_from(models.GraphVariant))
            ) == 1
            assert int(
                await session.scalar(
                    select(func.count()).select_from(models.GraphIdentifier)
                )
            ) == 1
            assert int(
                await session.scalar(
                    select(func.count()).select_from(models.GraphIdentifierEvidence)
                )
            ) == 2
            assert int(
                await session.scalar(
                    select(func.count()).select_from(models.GraphOfferVariantLink)
                )
            ) == 2
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_unresolved_offer_is_quarantined_without_creating_a_variant():
    engine, maker = await _session()
    try:
        async with maker() as session:
            raw, offer = await _raw_and_offer(session, "c")
            captured = await persist_awin_graph_projection(
                session,
                projection=project_awin_variant({"ean": "invalid"}),
                raw_source_record_id=raw.id,
                offer_id=offer.id,
                source_ref=raw.source_ref,
                observed_at=OBSERVED_AT,
            )
            await session.commit()

            link = await session.scalar(select(models.GraphOfferVariantLink))
            assert captured.resolution == "quarantine"
            assert link is not None
            assert link.variant_id is None
            assert link.reason_code == "invalid_gtin"
            assert await session.scalar(
                select(func.count()).select_from(models.GraphVariant)
            ) == 0
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_awin_writer_projects_graph_only_under_both_shadow_flags(monkeypatch):
    engine, maker = await _session()
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
                _env_file=None,
                env="test",
                observation_shadow_enabled=True,
                product_graph_shadow_enabled=True,
                awin_regions="BE",
                awin_max_rows_per_feed=1,
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
                return [
                    {
                        "aw_product_id": "xm6-black",
                        "product_name": "Sony WH-1000XM6 Black",
                        "brand_name": "Sony",
                        "merchant_category": "Headphones",
                        "merchant_image_url": "https://merchant.test/xm6.jpg",
                        "aw_deep_link": "https://merchant.test/xm6",
                        "search_price": "449.00",
                        "currency": "EUR",
                        "ean": "4006381333931",
                        "in_stock": "yes",
                    }
                ]

            async def upsert(db_session, merchant_id, row, **_kwargs):
                offer = core_models.Offer(
                    merchant_id=merchant_id,
                    awin_product_id=row["aw_product_id"],
                    name=row["product_name"],
                    ean=row["ean"],
                )
                db_session.add(offer)
                await db_session.flush()
                return offer.id

            monkeypatch.setattr(awin_catalog, "get_settings", lambda: settings)
            monkeypatch.setattr(awin_catalog, "list_feeds", feeds)
            monkeypatch.setattr(awin_catalog, "_download_feed_rows", rows)
            monkeypatch.setattr(awin_catalog, "_upsert_offer", upsert)

            result = await awin_catalog.ingest_feeds(session)
            assert result["shadow"] == {
                "enabled": True,
                "raw_sources": 1,
                "observations": 10,
                "quarantine": 0,
                "failures": 0,
            }
            assert result["graph_shadow"] == {
                "enabled": True,
                "variants": 1,
                "identifiers": 1,
                "evidence": 1,
                "links": 1,
                "assertions": 3,
                "quarantine": 0,
                "failures": 0,
            }
            link = await session.scalar(select(models.GraphOfferVariantLink))
            assert link is not None
            assert link.resolution == "resolved"
            assert link.variant_id is not None
            assertions = (
                (
                    await session.execute(
                        select(models.GraphIdentityAssertion).order_by(
                            models.GraphIdentityAssertion.id
                        )
                    )
                )
                .scalars()
                .all()
            )
            assert len(assertions) == 3
            assert {
                (
                    assertion.subject_type,
                    assertion.identifier_namespace,
                    assertion.identifier_scope,
                    assertion.status,
                )
                for assertion in assertions
            } == {
                ("brand", None, None, "observed"),
                ("variant", "gtin", "global", "validated"),
                ("variant", "merchant_sku", f"merchant:{merchant.id}", "validated"),
            }
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_backfill_is_bounded_dry_by_default_and_replay_idempotent():
    engine, maker = await _session()
    try:
        async with maker() as session:
            valid_raw, valid_offer = await _raw_and_offer(session, "d")
            invalid_raw, invalid_offer = await _raw_and_offer(
                session,
                "e",
                ean="invalid",
            )
            unlinked_raw, _unlinked_offer = await _raw_and_offer(session, "f")
            await _link_raw_offer(session, valid_raw, valid_offer)
            await _link_raw_offer(session, invalid_raw, invalid_offer)
            await session.commit()

            dry = await backfill_batch(session, limit=2)
            assert dry.mode == "dry_run"
            assert (dry.scanned, dry.resolved, dry.quarantined) == (2, 1, 1)
            assert await session.scalar(
                select(func.count()).select_from(models.GraphOfferVariantLink)
            ) == 0

            applied = await backfill_batch(session, limit=3, apply=True)
            assert applied.mode == "apply"
            assert applied.links_created == 2
            assert applied.variants_created == 1
            assert applied.assertions_created == 2
            assert applied.assertions_quarantined == 1
            assert applied.missing_offer_links == 1
            replayed = await backfill_batch(session, limit=3, apply=True)
            assert replayed.links_created == 0
            assert replayed.links_existing == 2
            assert replayed.variants_created == 0
            assert replayed.assertions_created == 0
            assert replayed.assertions_existing == 2
            assert replayed.last_raw_source_id == unlinked_raw.id
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_backfill_dry_run_reports_brand_and_scoped_identifier_collisions():
    engine, maker = await _session()
    try:
        async with maker() as session:
            first_raw, first_offer = await _raw_and_offer(session, "g")
            second_raw, second_offer = await _raw_and_offer(session, "h")
            first_raw.payload_json = {
                "ean": "4006381333931",
                "brand_name": "Rc Design",
                "aw_product_id": "shared-sku",
            }
            second_raw.payload_json = {
                "ean": "9780201379624",
                "brand_name": "rc design",
                "aw_product_id": "shared-sku",
            }
            second_raw.context_json = first_raw.context_json
            await _link_raw_offer(session, first_raw, first_offer)
            await _link_raw_offer(session, second_raw, second_offer)
            await session.commit()

            report = await backfill_batch(session, limit=2)
            assert report.mode == "dry_run"
            assert report.assertions_projected == 6
            assert report.assertions_observed == 2
            assert report.assertions_validated == 4
            assert report.assertions_quarantined == 0
            assert report.brand_normalization_collisions == 1
            assert report.scoped_identifier_collisions == 1
            assert await session.scalar(
                select(func.count()).select_from(models.GraphIdentityAssertion)
            ) == 0
    finally:
        await engine.dispose()
