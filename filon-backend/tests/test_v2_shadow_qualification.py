"""Reçu SHADOW → CANARY dérivé de preuves persistées et bornées."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import models as core_models  # noqa: F401
from app.db.base import Base
from app.v2_chain.models import V2ChainExecution, V2LiveDarkReadObservation
from app.v2_chain.proof_registry import SHADOW_PROOF_KEYS, record_promotion_proof
from app.v2_chain.qualification import (
    REQUIRED_STAGES,
    V2ExternalProofs,
    V2QualificationError,
    evaluate_persisted_shadow_to_canary,
)


EVALUATED_AT = datetime(2026, 9, 4, 8, tzinfo=timezone.utc)
CAMPAIGN_ID = "sha256:" + "c" * 64
CONTRACT_ROOT = (
    Path(__file__).resolve().parents[2] / "contracts" / "v2-chain" / "v1"
)
SCHEMA = json.loads((CONTRACT_ROOT / "shadow-qualification.schema.json").read_text())
VALIDATOR = Draft202012Validator(SCHEMA)


def _digest(character: str) -> str:
    return "sha256:" + character * 64


def _proofs(**overrides) -> V2ExternalProofs:
    values = {
        "campaign_id": CAMPAIGN_ID,
        "single_alembic_head_ref": _digest("1"),
        "postgresql_migration_ref": _digest("2"),
        "expand_only_rollback_ref": _digest("3"),
        "replay_idempotence_ref": _digest("4"),
        "inherited_benchmarks_ref": _digest("5"),
        "safety_invariants_ref": _digest("6"),
        "collision_exercise_ref": _digest("7"),
        "stale_interruption_ref": _digest("8"),
        "recovery_replay_ref": _digest("9"),
        "dark_reader_rollback_ref": _digest("a"),
        "performance_policy_ref": _digest("b"),
        "maximum_p95_window_ms": 500,
    }
    values.update(overrides)
    return V2ExternalProofs(**values)


async def _registered_proof_refs(session) -> dict[str, str]:
    refs: dict[str, str] = {}
    for index, proof_kind in enumerate(sorted(SHADOW_PROOF_KEYS)):
        persisted = await record_promotion_proof(
            session,
            scope_ref=CAMPAIGN_ID,
            proof_kind=proof_kind,
            artifact_ref=f"test:shadow/{proof_kind}",
            artifact_digest="sha256:" + f"{index + 1:064x}",
            verifier_version="pytest-v1",
            verification_status="VERIFIED",
            verified_at=EVALUATED_AT,
            apply=True,
        )
        refs[proof_kind] = persisted.proof_ref
    return refs


async def _database():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    return engine, async_sessionmaker(engine, expire_on_commit=False)


async def _seed_proven_window(
    session, index: int, *, outcome: str = "ABSTAIN"
) -> tuple[V2ChainExecution, V2LiveDarkReadObservation]:
    started = EVALUATED_AT + timedelta(seconds=index)
    report_digest = "sha256:" + f"{index + 100:064x}"
    execution = V2ChainExecution(
        execution_key=f"{index + 1:064x}",
        mode="apply",
        status="succeeded",
        evaluated_at=started.replace(tzinfo=None),
        vertical="smartphones",
        after_raw_id=index,
        row_limit=1,
        last_raw_source_id=index + 1,
        checkpoints_json={},
        completed_stages_json=sorted(REQUIRED_STAGES),
        campaign_id=CAMPAIGN_ID,
        execution_kind="progression",
        window_metrics_json={
            "schema_version": "v2-window-metrics/v1",
            "evaluation_identity": report_digest,
            "errors": 0,
        },
        report_evaluation_id=report_digest,
        started_at=started.replace(tzinfo=None),
        heartbeat_at=(started + timedelta(milliseconds=100)).replace(tzinfo=None),
        finished_at=(started + timedelta(milliseconds=100)).replace(tzinfo=None),
    )
    session.add(execution)
    await session.flush()
    observation = V2LiveDarkReadObservation(
        observation_key=f"{index + 3_000:064x}",
        campaign_id=CAMPAIGN_ID,
        comparison_version="qualification-v1",
        surface="advise_stream",
        vertical="smartphones",
        locale="fr",
        country_code="FR",
        core_outcome="CANDIDATES",
        v2_outcome=outcome,
        classification=(
            "V2_ABSTAINS_CORRECTLY" if outcome == "ABSTAIN" else "BOTH_VALID"
        ),
        core_candidate_count=1,
        v2_candidate_count=0 if outcome == "ABSTAIN" else 1,
        core_latency_us=100,
        v2_latency_us=100,
        chain_complete=True,
        safety_state="ABSTAIN" if outcome == "ABSTAIN" else "SAFE",
        provenance_complete=True,
        raw_query_retained=False,
        evaluated_at=started.replace(tzinfo=None),
    )
    session.add(observation)
    return execution, observation


@pytest.mark.asyncio
async def test_empty_evidence_keeps_canary_closed() -> None:
    engine, sessions = await _database()
    try:
        async with sessions() as session:
            report = await evaluate_persisted_shadow_to_canary(
                session,
                proofs=_proofs(),
                evaluated_at=EVALUATED_AT,
            )

            assert report.gate.status == "CANARY_HOLD"
            assert report.metrics.valid_terminal_windows == 0
            assert report.metrics.dark_observations == 0
            assert "THIRTY_TERMINAL_WINDOWS" in report.gate.blocker_codes
            assert "DARK_READER" in report.gate.blocker_codes
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_thirty_real_windows_authorize_only_observed_abstain() -> None:
    engine, sessions = await _database()
    try:
        async with sessions() as session:
            for index in range(30):
                await _seed_proven_window(session, index)
            proof_refs = await _registered_proof_refs(session)
            await session.commit()

            report = await evaluate_persisted_shadow_to_canary(
                session,
                proofs=_proofs(**proof_refs),
                evaluated_at=EVALUATED_AT + timedelta(hours=1),
            )

            assert report.gate.status == "CANARY_AUTHORIZED"
            assert report.metrics.valid_terminal_windows == 30
            assert report.metrics.cursor_monotone is True
            assert report.metrics.non_overlapping_executions is True
            assert report.metrics.p95_window_ms == 100
            assert report.metrics.dark_complete == 30
            assert report.metrics.observed_response_types == ("ABSTAIN",)
            assert report.gate.blocked_response_types == ("BUY_NOW", "WAIT")
            assert "RESPONSE_TYPE_OFF:BUY_NOW" in report.gate.blocker_codes
            assert report.evaluation_id.startswith("sha256:")
            VALIDATOR.validate(report.to_dict())
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_digest_shaped_but_unregistered_proofs_never_open_canary() -> None:
    engine, sessions = await _database()
    try:
        async with sessions() as session:
            for index in range(30):
                await _seed_proven_window(session, index)
            await session.commit()

            report = await evaluate_persisted_shadow_to_canary(
                session,
                proofs=_proofs(),
                evaluated_at=EVALUATED_AT + timedelta(hours=1),
            )

            assert report.gate.status == "CANARY_HOLD"
            assert "MIGRATION_AND_ROLLBACK" in report.gate.blocker_codes
            assert "IDEMPOTENT_CHAIN_REPLAY" in report.gate.blocker_codes
            assert "DARK_READER_ROLLBACK" in report.gate.blocker_codes
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_identical_replay_is_not_counted_as_a_new_real_window() -> None:
    engine, sessions = await _database()
    try:
        async with sessions() as session:
            source, _observation = await _seed_proven_window(session, 0)
            await session.commit()
            session.add(
                V2ChainExecution(
                    execution_key="f" * 64,
                    mode="apply",
                    status="succeeded",
                    evaluated_at=(EVALUATED_AT + timedelta(seconds=2)).replace(
                        tzinfo=None
                    ),
                    vertical="smartphones",
                    after_raw_id=0,
                    row_limit=1,
                    last_raw_source_id=1,
                    checkpoints_json={},
                    completed_stages_json=sorted(REQUIRED_STAGES),
                    campaign_id=CAMPAIGN_ID,
                    execution_kind="replay",
                    source_execution_id=source.id,
                    window_metrics_json={
                        "schema_version": "v2-window-metrics/v1",
                        "evaluation_identity": "sha256:" + f"{100:064x}",
                        "errors": 0,
                    },
                    report_evaluation_id="sha256:" + f"{100:064x}",
                    started_at=(EVALUATED_AT + timedelta(seconds=2)).replace(tzinfo=None),
                    heartbeat_at=(
                        EVALUATED_AT + timedelta(seconds=2, milliseconds=100)
                    ).replace(tzinfo=None),
                    finished_at=(
                        EVALUATED_AT + timedelta(seconds=2, milliseconds=100)
                    ).replace(tzinfo=None),
                )
            )
            await session.commit()

            report = await evaluate_persisted_shadow_to_canary(
                session,
                proofs=_proofs(),
                evaluated_at=EVALUATED_AT + timedelta(hours=1),
            )

            assert report.metrics.valid_terminal_windows == 1
            assert report.metrics.cursor_monotone is True
            assert report.gate.status == "CANARY_HOLD"
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_gap_overlap_or_invalid_dark_observation_keeps_gate_closed() -> None:
    engine, sessions = await _database()
    try:
        async with sessions() as session:
            seeded = [
                await _seed_proven_window(session, index) for index in range(30)
            ]
            executions = [item[0] for item in seeded]
            observations = [item[1] for item in seeded]
            executions[10].after_raw_id = 12
            executions[10].started_at = executions[9].started_at
            observations[0].safety_state = "INVALID"
            observations[0].chain_complete = False
            await session.commit()

            report = await evaluate_persisted_shadow_to_canary(
                session,
                proofs=_proofs(),
                evaluated_at=EVALUATED_AT + timedelta(hours=1),
            )

            assert report.metrics.cursor_monotone is False
            assert report.metrics.non_overlapping_executions is False
            assert report.metrics.dark_invalid == 1
            assert report.gate.status == "CANARY_HOLD"
            assert "MONOTONE_SINGLE_EXECUTION" in report.gate.blocker_codes
            assert "SAFETY_INVARIANTS" in report.gate.blocker_codes
    finally:
        await engine.dispose()


def test_external_proofs_are_digest_bound_and_policy_is_positive() -> None:
    with pytest.raises(V2QualificationError, match="sha256 proof ref"):
        _proofs(postgresql_migration_ref="green")
    with pytest.raises(V2QualificationError, match="positive"):
        _proofs(maximum_p95_window_ms=0)


def test_shadow_qualification_contract_and_example_are_valid() -> None:
    Draft202012Validator.check_schema(SCHEMA)
    example = json.loads(
        (CONTRACT_ROOT / "examples" / "shadow-qualification-abstain.json").read_text()
    )

    VALIDATOR.validate(example)
    assert example["gate"]["status"] == "CANARY_AUTHORIZED"
    assert example["gate"]["blocked_response_types"] == ["BUY_NOW", "WAIT"]
