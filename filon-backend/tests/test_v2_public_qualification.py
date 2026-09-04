"""Qualification mesurable CANARY → PUBLIC de la chaîne V2."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import models as core_models  # noqa: F401
from app.db.base import Base
from app.v2_chain.models import V2CanaryReadObservation
from app.v2_chain.proof_registry import (
    PUBLIC_PROOF_KEYS,
    record_promotion_proof,
)
from app.v2_chain.qualification import (
    V2PublicExternalProofs,
    V2QualificationError,
    evaluate_persisted_canary_to_public,
)
from quality_lab.v2_canary import V2CanaryEvidence, evaluate_shadow_to_canary
from quality_lab.v2_public import V2PublicEvidence, evaluate_canary_to_public


EVALUATED_AT = datetime(2026, 9, 4, 10, tzinfo=timezone.utc)
SHADOW_GATE = evaluate_shadow_to_canary(
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
GATE_ID = SHADOW_GATE.evaluation_id
CONTRACT_ROOT = (
    Path(__file__).resolve().parents[2] / "contracts" / "v2-chain" / "v1"
)
SCHEMA = json.loads((CONTRACT_ROOT / "public-qualification.schema.json").read_text())
VALIDATOR = Draft202012Validator(SCHEMA)


def _digest(character: str) -> str:
    return "sha256:" + character * 64


def _proofs(**overrides) -> V2PublicExternalProofs:
    values = {
        "shadow_gate_ref": GATE_ID,
        "readiness_and_5xx_ref": _digest("1"),
        "failure_injection_ref": _digest("2"),
        "rollback_to_shadow_ref": _digest("3"),
        "backup_restore_ref": _digest("4"),
        "capacity_and_alerting_ref": _digest("5"),
        "inherited_regressions_ref": _digest("6"),
        "open_blockers_audit_ref": _digest("7"),
        "public_policy_ref": _digest("8"),
        "minimum_paired_observations": 30,
        "minimum_observations_per_response_type": 30,
        "requested_response_types": ("ABSTAIN",),
    }
    values.update(overrides)
    return V2PublicExternalProofs(**values)


async def _registered_proof_refs(session) -> dict[str, str]:
    refs: dict[str, str] = {}
    for index, proof_kind in enumerate(sorted(PUBLIC_PROOF_KEYS - {"shadow_gate_ref"})):
        persisted = await record_promotion_proof(
            session,
            scope_ref=GATE_ID,
            proof_kind=proof_kind,
            artifact_ref=f"test:public/{proof_kind}",
            artifact_digest="sha256:" + f"{index + 20:064x}",
            verifier_version="pytest-v1",
            verification_status="VERIFIED",
            verified_at=EVALUATED_AT,
            apply=True,
        )
        refs[proof_kind] = persisted.proof_ref
    return refs


def _pure_evidence(**overrides) -> V2PublicEvidence:
    values = {
        "shadow_gate_authorized": True,
        "readiness_and_5xx_green": True,
        "minimum_paired_observations": 30,
        "minimum_observations_per_response_type": 30,
        "paired_observations": 30,
        "p95_latency_delta_us": -500,
        "v2_fallbacks": 0,
        "v2_reader_errors": 0,
        "invalid_or_incomplete": 0,
        "raw_query_retained": 0,
        "v2_served": 30,
        "provenance_complete": 30,
        "requested_response_types": ("ABSTAIN",),
        "served_response_types": ("ABSTAIN",),
        "served_response_type_counts": {"ABSTAIN": 30},
        "failure_injection_green": True,
        "rollback_to_shadow_green": True,
        "backup_restore_green": True,
        "capacity_and_alerting_green": True,
        "inherited_regressions_green": True,
        "no_integrity_recovery_security_blocker": True,
    }
    values.update(overrides)
    return V2PublicEvidence(**values)


async def _database():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    return engine, async_sessionmaker(engine, expire_on_commit=False)


def _observation(
    index: int,
    *,
    source: str = "v2",
    v2_latency_us: int = 1_500,
    fallback_reason: str | None = None,
) -> V2CanaryReadObservation:
    served_v2 = source == "v2"
    return V2CanaryReadObservation(
        observation_key=f"{index + 1:064x}",
        gate_evaluation_id=GATE_ID,
        cohort="canary",
        assignment_reason="closed_cohort_match",
        eligibility_evaluation_id=_digest("9"),
        eligibility_status="eligible",
        vertical="smartphones",
        locale="fr-BE",
        decision_type="purchase_advice",
        source=source,
        response_type="ABSTAIN" if served_v2 else "CORE",
        fallback_reason=fallback_reason,
        core_latency_us=2_000,
        v2_latency_us=v2_latency_us,
        total_latency_us=2_000 + v2_latency_us,
        chain_complete=True if served_v2 else None,
        safety_state="ABSTAIN" if served_v2 else None,
        provenance_complete=True if served_v2 else None,
        raw_query_retained=False,
        evaluated_at=(EVALUATED_AT + timedelta(seconds=index)).replace(tzinfo=None),
    )


def test_pure_public_gate_is_fail_closed_and_type_scoped() -> None:
    authorized = evaluate_canary_to_public(_pure_evidence())
    held = evaluate_canary_to_public(
        _pure_evidence(v2_fallbacks=1, v2_reader_errors=1)
    )
    undercovered = evaluate_canary_to_public(
        _pure_evidence(
            requested_response_types=("ABSTAIN", "BUY_NOW"),
            served_response_types=("ABSTAIN", "BUY_NOW"),
            served_response_type_counts={"ABSTAIN": 30, "BUY_NOW": 1},
        )
    )

    assert authorized.status == "PUBLIC_AUTHORIZED"
    assert authorized.authorized_response_types == ("ABSTAIN",)
    assert authorized.blocked_response_types == ("BUY_NOW", "WAIT")
    assert held.status == "PUBLIC_HOLD"
    assert "RUNTIME_HEALTH" in held.blocker_codes
    assert "ERROR_NON_INFERIORITY" in held.blocker_codes
    assert undercovered.status == "PUBLIC_HOLD"
    assert "RESPONSE_TYPE_COVERAGE" in undercovered.blocker_codes


@pytest.mark.asyncio
async def test_thirty_paired_reads_authorize_only_abstain() -> None:
    engine, sessions = await _database()
    try:
        async with sessions() as session:
            session.add_all(_observation(index) for index in range(30))
            proof_refs = await _registered_proof_refs(session)
            await session.commit()

            report = await evaluate_persisted_canary_to_public(
                session,
                shadow_gate=SHADOW_GATE,
                proofs=_proofs(**proof_refs),
                evaluated_at=EVALUATED_AT + timedelta(hours=1),
            )

            assert report.gate.status == "PUBLIC_AUTHORIZED"
            assert report.metrics.canary_observations == 30
            assert report.metrics.paired_observations == 30
            assert report.metrics.p95_latency_delta_us == -500
            assert report.gate.authorized_response_types == ("ABSTAIN",)
            assert report.gate.blocked_response_types == ("BUY_NOW", "WAIT")
            VALIDATOR.validate(report.to_dict())
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_digest_shaped_but_unregistered_proofs_never_open_public() -> None:
    engine, sessions = await _database()
    try:
        async with sessions() as session:
            session.add_all(_observation(index) for index in range(30))
            await session.commit()

            report = await evaluate_persisted_canary_to_public(
                session,
                shadow_gate=SHADOW_GATE,
                proofs=_proofs(),
                evaluated_at=EVALUATED_AT + timedelta(hours=1),
            )

            assert report.gate.status == "PUBLIC_HOLD"
            assert "RUNTIME_HEALTH" in report.gate.blocker_codes
            assert "FAILURE_INJECTION" in report.gate.blocker_codes
            assert "OPERATIONS" in report.gate.blocker_codes
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_insufficient_or_slower_sample_keeps_public_closed() -> None:
    engine, sessions = await _database()
    try:
        async with sessions() as session:
            session.add_all(_observation(index) for index in range(28))
            session.add(_observation(28, v2_latency_us=2_600))
            session.add(_observation(29, v2_latency_us=2_600))
            proof_refs = await _registered_proof_refs(session)
            await session.commit()

            slower = await evaluate_persisted_canary_to_public(
                session,
                shadow_gate=SHADOW_GATE,
                proofs=_proofs(**proof_refs),
                evaluated_at=EVALUATED_AT + timedelta(hours=1),
            )
            insufficient = await evaluate_persisted_canary_to_public(
                session,
                shadow_gate=SHADOW_GATE,
                proofs=_proofs(
                    **proof_refs,
                    minimum_paired_observations=31,
                ),
                evaluated_at=EVALUATED_AT + timedelta(hours=1),
            )

            assert slower.metrics.p95_latency_delta_us == 600
            assert slower.gate.status == "PUBLIC_HOLD"
            assert "LATENCY_NON_INFERIORITY" in slower.gate.blocker_codes
            assert "PAIRED_SAMPLE" in insufficient.gate.blocker_codes
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_any_canary_fallback_keeps_public_closed() -> None:
    engine, sessions = await _database()
    try:
        async with sessions() as session:
            session.add_all(_observation(index) for index in range(29))
            session.add(
                _observation(
                    29,
                    source="core_v1",
                    fallback_reason="v2_reader_error",
                )
            )
            proof_refs = await _registered_proof_refs(session)
            await session.commit()

            report = await evaluate_persisted_canary_to_public(
                session,
                shadow_gate=SHADOW_GATE,
                proofs=_proofs(**proof_refs),
                evaluated_at=EVALUATED_AT + timedelta(hours=1),
            )

            assert report.metrics.v2_fallbacks == 1
            assert report.metrics.v2_reader_errors == 1
            assert report.gate.status == "PUBLIC_HOLD"
            assert "RUNTIME_HEALTH" in report.gate.blocker_codes
            assert "ERROR_NON_INFERIORITY" in report.gate.blocker_codes
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_public_proofs_must_match_candidate_gate() -> None:
    engine, sessions = await _database()
    try:
        async with sessions() as session:
            with pytest.raises(V2QualificationError, match="does not match"):
                await evaluate_persisted_canary_to_public(
                    session,
                    shadow_gate=SHADOW_GATE,
                    proofs=_proofs(shadow_gate_ref=_digest("d")),
                    evaluated_at=EVALUATED_AT,
                )
    finally:
        await engine.dispose()


def test_public_proofs_are_bounded_and_digest_bound() -> None:
    with pytest.raises(V2QualificationError, match="sha256 proof ref"):
        _proofs(backup_restore_ref="green")
    with pytest.raises(V2QualificationError, match="minimum paired"):
        _proofs(minimum_paired_observations=0)
    with pytest.raises(V2QualificationError, match="minimum response"):
        _proofs(minimum_observations_per_response_type=0)
    with pytest.raises(V2QualificationError, match="response types"):
        _proofs(requested_response_types=("BUY",))


def test_public_qualification_contract_and_example_are_valid() -> None:
    Draft202012Validator.check_schema(SCHEMA)
    example = json.loads(
        (CONTRACT_ROOT / "examples" / "public-qualification-abstain.json").read_text()
    )

    VALIDATOR.validate(example)
    assert example["gate"]["authorized_response_types"] == ["ABSTAIN"]
    assert example["gate"]["blocked_response_types"] == ["BUY_NOW", "WAIT"]
