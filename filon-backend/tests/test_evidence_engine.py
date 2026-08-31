"""Preuves du moteur de claims et de son abstention fail-closed."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import models as core_models
from app.db.base import Base
from app.evidence_engine import models
from app.evidence_engine.backfill import (
    backfill_evidence_batch,
    parse_evaluated_at,
)
from app.evidence_engine.policy import (
    ATOMIC_CLAIMS,
    STRONG_CLAIMS,
    EvidencePolicyError,
    evaluate_offer_claims,
    persist_offer_evaluation,
)
from app.observations import models as observation_models
from app.offer_graph.models import GraphOfferObservation
from app.offer_graph.projection import (
    persist_awin_offer_projection,
    project_awin_offer,
)
from app.product_graph.resolution import (
    persist_awin_graph_projection,
    project_awin_variant,
)


BASE_TIME = datetime(2026, 8, 30, 20, 0, 0)


async def _session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    return engine, async_sessionmaker(engine, expire_on_commit=False)


async def _offer_observation(
    session,
    suffix: str,
    *,
    resolve_identity: bool = True,
    price: str | None = "49.90",
    stock: str | None = "yes",
    link: str | None = "https://merchant.example.org/item",
    observed_at: datetime = BASE_TIME,
):
    merchant = core_models.Merchant(
        awin_mid=8100 + ord(suffix),
        name=f"Evidence Merchant {suffix}",
        slug=f"evidence-merchant-{suffix}",
        region="BE",
        joined=True,
    )
    session.add(merchant)
    await session.flush()
    offer = core_models.Offer(
        merchant_id=merchant.id,
        awin_product_id=f"evidence-offer-{suffix}",
        name=f"Evidence Offer {suffix}",
    )
    session.add(offer)
    await session.flush()
    payload = {
        "ean": "4006381333931" if resolve_identity else None,
        "search_price": price,
        "currency": "EUR" if price is not None else None,
        "in_stock": stock,
        "aw_deep_link": link,
    }
    raw = observation_models.RawSourceRecord(
        source_type="awin_feed",
        source_ref=f"awin-feed:evidence-{suffix}",
        source_record_key=f"evidence-record-{suffix}",
        schema_version="awin-create-a-feed-v1",
        context_json={"feed_id": suffix, "merchant_id": merchant.id},
        payload_json=payload,
        payload_checksum=(suffix * 64),
        replay_key=(suffix.upper() * 64),
        sync_run_id=None,
        observed_at=observed_at,
    )
    session.add(raw)
    await session.flush()
    session.add(
        observation_models.Observation(
            raw_source_record_id=raw.id,
            subject_type="merchant_offer",
            subject_ref=f"offer:{offer.id}",
            offer_id=offer.id,
            field="external_id",
            value_json=offer.awin_product_id,
            status="verified",
            source_type="awin_feed",
            source_ref=raw.source_ref,
            observed_at=observed_at,
            transformation="awin_offer_observation",
            transformation_version="v1",
            confidence=1.0,
        )
    )
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
    return raw, observation


@pytest.mark.asyncio
async def test_fresh_exact_offer_is_rankable_but_never_decision_eligible():
    engine, maker = await _session()
    try:
        async with maker() as session:
            _raw, observation = await _offer_observation(session, "a")
            claims, decision = await evaluate_offer_claims(
                session,
                observation=observation,
                evaluated_at=BASE_TIME + timedelta(hours=1),
            )
            by_code = {claim.claim_code: claim for claim in claims}

            assert tuple(by_code) == ATOMIC_CLAIMS + STRONG_CLAIMS
            assert all(
                by_code[code].knowledge_status == "VERIFIED"
                and by_code[code].eligibility == "eligible"
                for code in ATOMIC_CLAIMS
            )
            assert by_code["PRICE_OBSERVED"].value == {
                "amount": "49.900000",
                "currency": "EUR",
            }
            assert all(
                by_code[code].knowledge_status == "UNKNOWN"
                and by_code[code].value is None
                and by_code[code].eligibility == "ineligible"
                for code in STRONG_CLAIMS
            )
            assert all(claim.confidence is None for claim in claims)
            assert decision.highest_stage == "RANKABLE"
            assert decision.decision_eligible is False
            assert decision.blocker_reason == "country_shipping_unknown"
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_stale_missing_identity_and_out_of_stock_fail_closed():
    engine, maker = await _session()
    try:
        async with maker() as session:
            _raw_a, stale = await _offer_observation(session, "b")
            stale_claims, stale_decision = await evaluate_offer_claims(
                session,
                observation=stale,
                evaluated_at=BASE_TIME + timedelta(hours=73),
            )
            stale_by_code = {claim.claim_code: claim for claim in stale_claims}
            assert stale_by_code["PRICE_OBSERVED"].eligibility == "unknown"
            assert stale_by_code["PRICE_OBSERVED"].value is None
            assert stale_by_code["VARIANT_IDENTITY_EXACT"].eligibility == "eligible"
            assert stale_decision.highest_stage == "DISCOVERABLE"

            _raw_b, unresolved = await _offer_observation(
                session,
                "c",
                resolve_identity=False,
            )
            unresolved_claims, unresolved_decision = await evaluate_offer_claims(
                session,
                observation=unresolved,
                evaluated_at=BASE_TIME + timedelta(hours=1),
            )
            unresolved_by_code = {
                claim.claim_code: claim for claim in unresolved_claims
            }
            assert unresolved_by_code["VARIANT_IDENTITY_EXACT"].knowledge_status == (
                "UNKNOWN"
            )
            assert unresolved_by_code["VARIANT_IDENTITY_EXACT"].value is None
            assert unresolved_decision.highest_stage == "DISCOVERABLE"

            _raw_c, unavailable = await _offer_observation(
                session,
                "d",
                stock="no",
            )
            unavailable_claims, unavailable_decision = await evaluate_offer_claims(
                session,
                observation=unavailable,
                evaluated_at=BASE_TIME + timedelta(hours=1),
            )
            availability = {
                claim.claim_code: claim for claim in unavailable_claims
            }["AVAILABILITY_OBSERVED"]
            assert availability.value == "out_of_stock"
            assert availability.eligibility == "eligible"
            assert unavailable_decision.highest_stage == "COMPARABLE"
            assert unavailable_decision.blocker_reason == "out_of_stock"
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_persistence_is_idempotent_and_rejects_an_incomplete_roster():
    engine, maker = await _session()
    try:
        async with maker() as session:
            _raw, observation = await _offer_observation(session, "e")
            claims, decision = await evaluate_offer_claims(
                session,
                observation=observation,
                evaluated_at=BASE_TIME + timedelta(hours=1),
            )
            with pytest.raises(EvidencePolicyError, match="roster"):
                await persist_offer_evaluation(
                    session,
                    observation=observation,
                    claims=claims[:-1],
                    decision=decision,
                )

            assert await persist_offer_evaluation(
                session,
                observation=observation,
                claims=claims,
                decision=decision,
            ) == (11, True)
            assert await persist_offer_evaluation(
                session,
                observation=observation,
                claims=claims,
                decision=decision,
            ) == (0, False)
            await session.commit()
            assert await session.scalar(
                select(func.count()).select_from(models.EvidenceClaimRecord)
            ) == 11
            assert await session.scalar(
                select(func.count()).select_from(models.DecisionEligibilityRecord)
            ) == 1
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_identity_link_from_another_offer_is_not_accepted_as_evidence():
    engine, maker = await _session()
    try:
        async with maker() as session:
            _first_raw, first = await _offer_observation(session, "g")
            _second_raw, second = await _offer_observation(session, "h")
            first.offer_variant_link_id = second.offer_variant_link_id

            claims, decision = await evaluate_offer_claims(
                session,
                observation=first,
                evaluated_at=BASE_TIME + timedelta(hours=1),
            )
            identity = {claim.claim_code: claim for claim in claims}[
                "VARIANT_IDENTITY_EXACT"
            ]
            assert identity.knowledge_status == "UNKNOWN"
            assert identity.value is None
            assert decision.highest_stage == "DISCOVERABLE"
            assert decision.blocker_reason == "identity_unresolved"
    finally:
        await engine.dispose()


def test_evaluated_at_requires_explicit_timezone():
    assert parse_evaluated_at("2026-08-30T22:00:00+02:00") == BASE_TIME
    with pytest.raises(ValueError, match="explicit UTC offset"):
        parse_evaluated_at("2026-08-30T22:00:00")


@pytest.mark.asyncio
async def test_backfill_is_dry_by_default_and_apply_is_idempotent():
    engine, maker = await _session()
    try:
        async with maker() as session:
            await _offer_observation(session, "f")
            await session.commit()

            dry = await backfill_evidence_batch(
                session,
                evaluated_at=BASE_TIME + timedelta(hours=1),
                limit=1,
            )
            assert dry.offer_observations == 1
            assert dry.claims_evaluated == 11
            assert dry.atomic_claims_eligible == 4
            assert dry.strong_claims_ineligible == 7
            assert dry.rankable_decisions == 1
            assert dry.decision_eligible == 0
            assert dry.claims_created == 0

            applied = await backfill_evidence_batch(
                session,
                evaluated_at=BASE_TIME + timedelta(hours=1),
                limit=1,
                apply=True,
            )
            assert applied.claims_created == 11
            assert applied.decisions_created == 1
            replay = await backfill_evidence_batch(
                session,
                evaluated_at=BASE_TIME + timedelta(hours=1),
                limit=1,
                apply=True,
            )
            assert replay.claims_existing == 11
            assert replay.decisions_existing == 1
    finally:
        await engine.dispose()
