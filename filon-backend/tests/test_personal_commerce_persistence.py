from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.buy_wait.engine import BuyWaitRequest, DecisionConfidence, decide_buy_wait
from app.buy_wait.models import BuyWaitDecisionRun
from app.buy_wait.persistence import persist_buy_wait
from app.db.base import Base
from app.personal_commerce.engine import (
    ExplicitPreference,
    PersonalCommerceCandidate,
    PersonalCommerceRequest,
    decide_personal_commerce,
)
from app.personal_commerce.models import (
    PersonalCommerceDecisionRun,
    PersonalCommerceErasureReceipt,
)
from app.personal_commerce.persistence import (
    PersonalCommercePersistenceError,
    erase_personal_commerce,
    export_personal_commerce,
    persist_personal_commerce,
    purge_expired_personal_commerce,
)
from tests.test_buy_wait_persistence import _confidence_run


SUBJECT_SECRET = "p18-test-subject-hmac-secret-32-chars"


async def _buy_wait_run(session) -> BuyWaitDecisionRun:
    confidence = await _confidence_run(session)
    evaluated = datetime(2026, 9, 2, tzinfo=timezone.utc)
    decision = decide_buy_wait(BuyWaitRequest(
        "p18:source",
        evaluated,
        None,
        None,
        None,
        (),
        DecisionConfidence("UNKNOWN", None, 0, None, ()),
        None,
    ))
    await persist_buy_wait(
        session,
        confidence_run=confidence,
        evaluated_at=evaluated,
        decision=decision,
        apply=True,
    )
    run = await session.scalar(select(BuyWaitDecisionRun))
    assert run is not None
    return run


@pytest.mark.asyncio
async def test_dry_apply_and_replay_abstention_are_append_only_without_subject() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with sessions() as session:
        source = await _buy_wait_run(session)
        evaluated = datetime(2026, 9, 2, 12, tzinfo=timezone.utc)
        request = PersonalCommerceRequest(
            "objective:shadow",
            False,
            ("outfit",),
            None,
            None,
        )
        decision = decide_personal_commerce(request, ())
        kwargs = {
            "buy_wait_run": source,
            "request": request,
            "decision": decision,
            "evaluated_at": evaluated,
        }

        dry = await persist_personal_commerce(session, **kwargs)
        first = await persist_personal_commerce(session, **kwargs, apply=True)
        replay = await persist_personal_commerce(session, **kwargs, apply=True)

        assert dry.runs_created == 0
        assert first.runs_created == 1
        assert replay.runs_existing == 1
        assert first.evaluation_id == replay.evaluation_id
        assert await session.scalar(select(func.count()).select_from(PersonalCommerceDecisionRun)) == 1
        stored = await session.scalar(select(PersonalCommerceDecisionRun))
        assert stored is not None
        assert stored.subject_digest is None
        assert stored.personalization_consent is False
        assert stored.raw_context_retained is False
        assert stored.action == "ABSTAIN"
        assert stored.measurement_status == "not_calibrated"
    await engine.dispose()


@pytest.mark.asyncio
async def test_subject_material_requires_consent_and_a_strong_hmac_secret() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with sessions() as session:
        source = await _buy_wait_run(session)
        evaluated = datetime(2026, 9, 2, 12, 30, tzinfo=timezone.utc)
        request = PersonalCommerceRequest(
            "objective:no-consent", False, ("outfit",), None, None,
        )
        decision = decide_personal_commerce(request, ())
        with pytest.raises(PersonalCommercePersistenceError, match="subject material"):
            await persist_personal_commerce(
                session,
                buy_wait_run=source,
                request=request,
                decision=decision,
                evaluated_at=evaluated,
                subject_ref="subject:forbidden",
            )

        consented = PersonalCommerceRequest(
            "objective:consented", True, ("outfit",), None, None,
        )
        consented_decision = decide_personal_commerce(consented, ())
        with pytest.raises(PersonalCommercePersistenceError, match="does not match"):
            await persist_personal_commerce(
                session,
                buy_wait_run=source,
                request=consented,
                decision=replace(consented_decision, objective_digest="sha256:" + "0" * 64),
                evaluated_at=evaluated,
                subject_ref="subject:consented",
                subject_digest_secret=SUBJECT_SECRET,
            )
        with pytest.raises(PersonalCommercePersistenceError, match="subject digest secret"):
            await persist_personal_commerce(
                session,
                buy_wait_run=source,
                request=consented,
                decision=consented_decision,
                evaluated_at=evaluated,
                subject_ref="subject:consented",
                subject_digest_secret="weak",
            )
        with pytest.raises(PersonalCommercePersistenceError, match="retention expiry"):
            await persist_personal_commerce(
                session,
                buy_wait_run=source,
                request=consented,
                decision=consented_decision,
                evaluated_at=evaluated,
                subject_ref="subject:consented",
                subject_digest_secret=SUBJECT_SECRET,
            )
    await engine.dispose()


@pytest.mark.asyncio
async def test_consented_record_is_erasable_and_receipt_replay_is_idempotent() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with sessions() as session:
        source = await _buy_wait_run(session)
        evaluated = datetime(2026, 9, 2, 13, tzinfo=timezone.utc)
        preference = ExplicitPreference(
            "preference:blue", "color", "blue", "LIKE",
            "personal_commerce", "user:preference:blue",
        )
        request = PersonalCommerceRequest(
            "objective:owned-first",
            True,
            ("outfit",),
            None,
            None,
            (preference,),
        )
        candidate = PersonalCommerceCandidate(
            "solution:owned-blue",
            "outfit",
            "SOLUTION_COMPOSED",
            "ELIGIBLE",
            2,
            0,
            "0",
            None,
            None,
            None,
            {"color": "blue"},
            ("evidence:owned-blue",),
        )
        decision = decide_personal_commerce(request, (candidate,))
        with pytest.raises(PersonalCommercePersistenceError, match="diverges"):
            await persist_personal_commerce(
                session,
                buy_wait_run=source,
                request=request,
                decision=replace(decision, action="BUY"),
                evaluated_at=evaluated,
                subject_ref="subject:test-only",
                subject_digest_secret=SUBJECT_SECRET,
            )
        await persist_personal_commerce(
            session,
            buy_wait_run=source,
            request=request,
            decision=decision,
            evaluated_at=evaluated,
            subject_ref="subject:test-only",
            subject_digest_secret=SUBJECT_SECRET,
            retention_expires_at=evaluated + timedelta(days=30),
            apply=True,
        )
        stored = await session.scalar(select(PersonalCommerceDecisionRun))
        assert stored is not None
        assert stored.subject_digest is not None
        assert "subject:test-only" not in stored.subject_digest
        assert stored.matched_preference_count == 1

        portable = await export_personal_commerce(
            session,
            subject_ref="subject:test-only",
            subject_digest_secret=SUBJECT_SECRET,
            exported_at=evaluated,
        )
        assert portable.schema_version == "personal-commerce-portable-export/v1"
        assert portable.record_count == 1
        assert portable.records[0].action == "USE_WHAT_YOU_OWN"
        assert portable.records[0].retention_expires_at == "2026-10-02T13:00:00Z"
        assert portable.raw_context_retained is False
        assert "subject:test-only" not in str(portable)
        assert stored.subject_digest not in str(portable)

        dry = await erase_personal_commerce(
            session,
            subject_ref="subject:test-only",
            erasure_request_ref="request:one",
            erased_at=evaluated,
            subject_digest_secret=SUBJECT_SECRET,
        )
        first = await erase_personal_commerce(
            session,
            subject_ref="subject:test-only",
            erasure_request_ref="request:one",
            erased_at=evaluated,
            subject_digest_secret=SUBJECT_SECRET,
            apply=True,
        )
        replay = await erase_personal_commerce(
            session,
            subject_ref="subject:test-only",
            erasure_request_ref="request:one",
            erased_at=datetime(2026, 9, 3, 13, tzinfo=timezone.utc),
            subject_digest_secret=SUBJECT_SECRET,
            apply=True,
        )

        assert dry.matched_records == 1 and dry.erased_records == 0
        assert first.erased_records == 1 and first.verified_empty is True
        assert replay.receipts_existing == 1 and replay.verified_empty is True
        assert await session.scalar(select(func.count()).select_from(PersonalCommerceDecisionRun)) == 0
        receipt = await session.scalar(select(PersonalCommerceErasureReceipt))
        assert receipt is not None and receipt.raw_context_retained is False
        assert "subject:test-only" not in str(vars(receipt))
    await engine.dispose()


@pytest.mark.asyncio
async def test_expired_consent_records_are_purged_and_replay_is_idempotent() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with sessions() as session:
        source = await _buy_wait_run(session)
        evaluated = datetime(2026, 9, 2, 15, tzinfo=timezone.utc)
        request = PersonalCommerceRequest(
            "objective:retention", True, ("outfit",), None, None,
        )
        decision = decide_personal_commerce(request, ())
        await persist_personal_commerce(
            session,
            buy_wait_run=source,
            request=request,
            decision=decision,
            evaluated_at=evaluated,
            subject_ref="subject:retention",
            subject_digest_secret=SUBJECT_SECRET,
            retention_expires_at=evaluated + timedelta(days=1),
            apply=True,
        )

        before = await purge_expired_personal_commerce(session, as_of=evaluated)
        cutoff = evaluated + timedelta(days=2)
        due = await purge_expired_personal_commerce(session, as_of=cutoff)
        applied = await purge_expired_personal_commerce(
            session, as_of=cutoff, apply=True,
        )
        replay = await purge_expired_personal_commerce(
            session, as_of=cutoff, apply=True,
        )

        assert before.matched_records == 0 and before.verified_empty is True
        assert due.matched_records == 1 and due.verified_empty is False
        assert applied.erased_records == 1 and applied.receipts_created == 1
        assert replay.receipts_existing == 1 and replay.verified_empty is True
        assert await session.scalar(select(func.count()).select_from(PersonalCommerceDecisionRun)) == 0
    await engine.dispose()
