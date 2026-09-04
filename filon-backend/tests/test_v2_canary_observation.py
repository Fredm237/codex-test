"""Télémétrie canary mesurable, idempotente et sans contexte brut."""

from __future__ import annotations

import json
from dataclasses import asdict, replace
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from jsonschema import Draft202012Validator
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
from app.v2_chain.canary import (
    CanaryAssignment,
    V2CanaryEligibilityEvidence,
    V2CanaryEligibilityPolicy,
    V2CanaryPayload,
    evaluate_canary_eligibility,
    run_canary_read,
)
from app.v2_chain.canary_observation import (
    V2CanaryObservationError,
    record_canary_read,
)
from app.v2_chain.models import V2CanaryReadObservation
from quality_lab.v2_canary import V2CanaryEvidence, evaluate_shadow_to_canary


EVALUATED_AT = datetime(2026, 9, 3, 21, tzinfo=timezone.utc)
OBSERVATION_KEY = "a" * 64
ROUTES_ROOT = Path(__file__).resolve().parents[1] / "app" / "api" / "routes"
CONTRACT_ROOT = Path(__file__).resolve().parents[2] / "contracts" / "v2-chain" / "v1"
RECEIPT_SCHEMA = json.loads(
    (CONTRACT_ROOT / "canary-read-receipt.schema.json").read_text()
)
RECEIPT_VALIDATOR = Draft202012Validator(RECEIPT_SCHEMA)
ELIGIBILITY_SCHEMA = json.loads(
    (CONTRACT_ROOT / "canary-eligibility.schema.json").read_text()
)
ELIGIBILITY_VALIDATOR = Draft202012Validator(ELIGIBILITY_SCHEMA)


def _gate():
    return evaluate_shadow_to_canary(
        V2CanaryEvidence(
            single_alembic_head=True,
            postgresql_migration_green=True,
            expand_only_rollback_green=True,
            replay_idempotent=True,
            cursor_monotone=True,
            single_execution_proven=True,
            inherited_benchmarks_green=True,
            safety_invariants_green=True,
            real_terminal_windows=30,
            performance_distribution_ready=True,
            collision_exercise_green=True,
            stale_interruption_green=True,
            recovery_replay_green=True,
            dark_reader_qualified=True,
            dark_reader_rollback_green=True,
            observed_response_types=("ABSTAIN",),
        )
    )


async def _database():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    return engine, async_sessionmaker(engine, expire_on_commit=False)


async def _result(*, source: str = "v2"):
    clock = iter((0, 2_000_000, 2_100_000, 3_500_000))
    assignment = (
        CanaryAssignment("canary", "closed_cohort_match")
        if source == "v2"
        else CanaryAssignment("core", "outside_closed_cohort")
    )
    return await run_canary_read(
        assignment=assignment,
        eligibility=evaluate_canary_eligibility(
            policy=V2CanaryEligibilityPolicy(
                policy_id="sha256:" + "c" * 64,
                supported_verticals=("smartphones",),
                supported_locales=("fr-BE",),
                supported_decision_types=("purchase_advice",),
                maximum_data_age_seconds=300,
            ),
            evidence=V2CanaryEligibilityEvidence(
                vertical="smartphones",
                locale="fr-BE",
                decision_type="purchase_advice",
                data_age_seconds=30,
                dependencies_admissible=True,
                critical_unknown=False,
                hard_constraint_violation=False,
                confidence_required=False,
                confidence_admissible=False,
                rollback_available=True,
            ),
        ),
        gate=_gate(),
        core_reader=AsyncMock(return_value={"source": "core"}),
        v2_reader=AsyncMock(
            return_value=V2CanaryPayload(
                response={"source": "v2", "items": []},
                chain_complete=True,
                safety_state="ABSTAIN",
                provenance_complete=True,
                response_type="ABSTAIN",
            )
        ),
        clock_ns=lambda: next(clock),
    )


@pytest.mark.asyncio
async def test_canary_observation_dry_apply_and_replay_are_idempotent() -> None:
    engine, sessions = await _database()
    try:
        async with sessions() as session:
            result = await _result()
            assert result.receipt.core_latency_us == 2_000
            assert result.receipt.v2_latency_us == 1_400
            assert result.receipt.total_latency_us == 3_500
            RECEIPT_VALIDATOR.validate(asdict(result.receipt))

            dry = await record_canary_read(
                session,
                observation_key=OBSERVATION_KEY,
                receipt=result.receipt,
                evaluated_at=EVALUATED_AT,
            )
            assert dry.status == "dry_run"
            assert await session.scalar(
                select(func.count()).select_from(V2CanaryReadObservation)
            ) == 0

            created = await record_canary_read(
                session,
                observation_key=OBSERVATION_KEY,
                receipt=result.receipt,
                evaluated_at=EVALUATED_AT,
                apply=True,
            )
            replay = await record_canary_read(
                session,
                observation_key=OBSERVATION_KEY,
                receipt=result.receipt,
                evaluated_at=EVALUATED_AT,
                apply=True,
            )
            stored = await session.scalar(select(V2CanaryReadObservation))

            assert created.status == "created"
            assert replay.status == "existing"
            assert replay.observation_id == created.observation_id
            assert stored is not None
            assert stored.source == "v2"
            assert stored.response_type == "ABSTAIN"
            assert stored.eligibility_status == "eligible"
            assert stored.vertical == "smartphones"
            assert stored.locale == "fr-BE"
            assert stored.decision_type == "purchase_advice"
            assert stored.raw_query_retained is False
            assert stored.core_latency_us == 2_000
            assert stored.v2_latency_us == 1_400
            assert stored.total_latency_us == 3_500
            assert not hasattr(stored, "raw_query")
            assert not hasattr(stored, "subject_digest")
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_canary_observation_refuses_replay_drift() -> None:
    engine, sessions = await _database()
    try:
        async with sessions() as session:
            result = await _result()
            await record_canary_read(
                session,
                observation_key=OBSERVATION_KEY,
                receipt=result.receipt,
                evaluated_at=EVALUATED_AT,
                apply=True,
            )
            drifted = replace(
                result.receipt,
                core_latency_us=result.receipt.core_latency_us + 1,
                total_latency_us=result.receipt.total_latency_us + 1,
            )

            with pytest.raises(V2CanaryObservationError, match="drifted"):
                await record_canary_read(
                    session,
                    observation_key=OBSERVATION_KEY,
                    receipt=drifted,
                    evaluated_at=EVALUATED_AT,
                    apply=True,
                )
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_core_fallback_observation_contains_no_v2_or_identity_state() -> None:
    engine, sessions = await _database()
    try:
        async with sessions() as session:
            result = await _result(source="core")
            assert result.receipt.source == "core_v1"
            assert result.receipt.v2_latency_us is None
            assert result.receipt.chain_complete is None

            report = await record_canary_read(
                session,
                observation_key="b" * 64,
                receipt=result.receipt,
                evaluated_at=EVALUATED_AT,
                apply=True,
            )
            assert report.status == "created"
            stored = await session.scalar(select(V2CanaryReadObservation))
            assert stored is not None
            assert stored.cohort == "core"
            assert stored.fallback_reason == "outside_closed_cohort"
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_canary_observation_rejects_raw_retention_and_invalid_keys() -> None:
    engine, sessions = await _database()
    try:
        async with sessions() as session:
            result = await _result()
            with pytest.raises(V2CanaryObservationError, match="retention"):
                await record_canary_read(
                    session,
                    observation_key=OBSERVATION_KEY,
                    receipt=replace(result.receipt, raw_query_retained=True),
                    evaluated_at=EVALUATED_AT,
                    apply=True,
                )
            with pytest.raises(V2CanaryObservationError, match="key"):
                await record_canary_read(
                    session,
                    observation_key="not-a-digest",
                    receipt=result.receipt,
                    evaluated_at=EVALUATED_AT,
                    apply=True,
                )
    finally:
        await engine.dispose()


def test_canary_observation_is_not_wired_to_public_routes() -> None:
    public_routes = "\n".join(
        path.read_text(encoding="utf-8") for path in ROUTES_ROOT.glob("*.py")
    )

    assert "v2_chain.canary_observation" not in public_routes
    assert "record_canary_read" not in public_routes


def test_canary_receipt_contract_and_example_are_valid() -> None:
    Draft202012Validator.check_schema(RECEIPT_SCHEMA)
    example = json.loads(
        (CONTRACT_ROOT / "examples" / "canary-abstain-receipt.json").read_text()
    )

    RECEIPT_VALIDATOR.validate(example)
    assert example["raw_query_retained"] is False


def test_canary_eligibility_contract_and_example_are_valid() -> None:
    Draft202012Validator.check_schema(ELIGIBILITY_SCHEMA)
    example = json.loads(
        (CONTRACT_ROOT / "examples" / "canary-eligibility-smartphone.json").read_text()
    )

    ELIGIBILITY_VALIDATOR.validate(example)
    assert example["eligible"] is True
    assert example["reason_code"] == "eligible"
