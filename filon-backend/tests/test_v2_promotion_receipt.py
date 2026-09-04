"""Persistance append-only des reçus de promotion V2."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, replace
from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import models as core_models  # noqa: F401
from app.db.base import Base
from app.v2_chain.models import V2PromotionReceipt
from app.v2_chain.promotion_receipt import (
    V2PromotionReceiptError,
    record_promotion_receipt,
)
from app.v2_chain.qualification import (
    V2PublicQualificationMetrics,
    V2PublicQualificationReport,
    V2QualificationMetrics,
    V2ShadowQualificationReport,
)
from quality_lab.v2_canary import V2CanaryEvidence, evaluate_shadow_to_canary
from quality_lab.v2_public import V2PublicEvidence, evaluate_canary_to_public


EVALUATED_AT = "2026-09-04T12:00:00Z"
ROUTES_ROOT = Path(__file__).resolve().parents[1] / "app" / "api" / "routes"


def _digest(value: object) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _proof_refs(names: tuple[str, ...]) -> dict[str, str]:
    return {
        name: "sha256:" + f"{index + 1:064x}"
        for index, name in enumerate(names)
    }


def _shadow_report() -> V2ShadowQualificationReport:
    metrics = V2QualificationMetrics(
        execution_rows=30,
        valid_terminal_windows=30,
        active_executions=0,
        failed_or_interrupted_executions=0,
        cursor_monotone=True,
        non_overlapping_executions=True,
        p95_window_ms=100,
        dark_observations=30,
        dark_eligible=30,
        dark_unsupported=0,
        dark_complete=30,
        dark_invalid=0,
        dark_raw_query_retained=0,
        observed_response_types=("ABSTAIN",),
    )
    gate = evaluate_shadow_to_canary(
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
    refs = _proof_refs(
        (
            "single_alembic_head_ref",
            "postgresql_migration_ref",
            "expand_only_rollback_ref",
            "replay_idempotence_ref",
            "inherited_benchmarks_ref",
            "safety_invariants_ref",
            "collision_exercise_ref",
            "stale_interruption_ref",
            "recovery_replay_ref",
            "dark_reader_rollback_ref",
            "performance_policy_ref",
        )
    )
    identity = {
        "evaluated_at": EVALUATED_AT,
        "campaign_id": "sha256:" + "c" * 64,
        "metrics": asdict(metrics),
        "gate": gate.to_dict(),
        "proof_refs": refs,
        "maximum_p95_window_ms": 500,
    }
    return V2ShadowQualificationReport(
        schema_version="v2-shadow-qualification/v1",
        evaluated_at=EVALUATED_AT,
        campaign_id="sha256:" + "c" * 64,
        metrics=metrics,
        gate=gate,
        proof_refs=refs,
        maximum_p95_window_ms=500,
        evaluation_id=_digest(identity),
    )


def _public_report(shadow) -> V2PublicQualificationReport:
    metrics = V2PublicQualificationMetrics(
        canary_observations=30,
        paired_observations=30,
        v2_served=30,
        v2_fallbacks=0,
        v2_reader_errors=0,
        invalid_or_incomplete=0,
        provenance_complete=30,
        raw_query_retained=0,
        p95_latency_delta_us=-500,
        served_response_types=("ABSTAIN",),
        served_response_type_counts={"ABSTAIN": 30},
    )
    gate = evaluate_canary_to_public(
        V2PublicEvidence(
            shadow_gate_authorized=True,
            readiness_and_5xx_green=True,
            minimum_paired_observations=30,
            minimum_observations_per_response_type=30,
            paired_observations=30,
            p95_latency_delta_us=-500,
            v2_fallbacks=0,
            v2_reader_errors=0,
            invalid_or_incomplete=0,
            raw_query_retained=0,
            v2_served=30,
            provenance_complete=30,
            requested_response_types=("ABSTAIN",),
            served_response_types=("ABSTAIN",),
            served_response_type_counts={"ABSTAIN": 30},
            failure_injection_green=True,
            rollback_to_shadow_green=True,
            backup_restore_green=True,
            capacity_and_alerting_green=True,
            inherited_regressions_green=True,
            no_integrity_recovery_security_blocker=True,
        )
    )
    refs = _proof_refs(
        (
            "shadow_gate_ref",
            "readiness_and_5xx_ref",
            "failure_injection_ref",
            "rollback_to_shadow_ref",
            "backup_restore_ref",
            "capacity_and_alerting_ref",
            "inherited_regressions_ref",
            "open_blockers_audit_ref",
            "public_policy_ref",
        )
    )
    refs["shadow_gate_ref"] = shadow.gate.evaluation_id
    identity = {
        "evaluated_at": EVALUATED_AT,
        "shadow_gate_evaluation_id": shadow.gate.evaluation_id,
        "metrics": asdict(metrics),
        "gate": gate.to_dict(),
        "proof_refs": refs,
        "minimum_paired_observations": 30,
        "minimum_observations_per_response_type": 30,
        "requested_response_types": ("ABSTAIN",),
    }
    return V2PublicQualificationReport(
        schema_version="v2-public-qualification/v1",
        evaluated_at=EVALUATED_AT,
        shadow_gate_evaluation_id=shadow.gate.evaluation_id,
        metrics=metrics,
        gate=gate,
        proof_refs=refs,
        minimum_paired_observations=30,
        minimum_observations_per_response_type=30,
        requested_response_types=("ABSTAIN",),
        evaluation_id=_digest(identity),
    )


async def _database():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    return engine, async_sessionmaker(engine, expire_on_commit=False)


@pytest.mark.asyncio
async def test_promotion_receipts_dry_apply_and_replay_are_append_only() -> None:
    engine, sessions = await _database()
    try:
        async with sessions() as session:
            shadow = _shadow_report()
            public = _public_report(shadow)

            dry = await record_promotion_receipt(session, report=shadow)
            assert dry.status == "dry_run"
            assert await session.scalar(
                select(func.count()).select_from(V2PromotionReceipt)
            ) == 0

            created = await record_promotion_receipt(
                session, report=shadow, apply=True
            )
            replay = await record_promotion_receipt(
                session, report=shadow, apply=True
            )
            published = await record_promotion_receipt(
                session, report=public, apply=True
            )
            await session.commit()

            receipts = list(
                (
                    await session.scalars(
                        select(V2PromotionReceipt).order_by(V2PromotionReceipt.id)
                    )
                ).all()
            )
            assert created.status == "created"
            assert replay.status == "existing"
            assert replay.receipt_id == created.receipt_id
            assert published.status == "created"
            assert len(receipts) == 2
            assert receipts[0].promotion_stage == "shadow_to_canary"
            assert receipts[0].source_gate_evaluation_id is None
            assert receipts[0].authorized_response_types_json == ["ABSTAIN"]
            assert receipts[1].promotion_stage == "canary_to_public"
            assert receipts[1].source_gate_evaluation_id == shadow.gate.evaluation_id
            assert receipts[1].raw_payload_retained is False
            assert not hasattr(receipts[1], "raw_query")
            assert not hasattr(receipts[1], "payload_json")
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_promotion_receipt_refuses_identity_drift() -> None:
    engine, sessions = await _database()
    try:
        async with sessions() as session:
            shadow = _shadow_report()
            with pytest.raises(V2PromotionReceiptError, match="identity drifted"):
                await record_promotion_receipt(
                    session,
                    report=replace(shadow, maximum_p95_window_ms=501),
                    apply=True,
                )
    finally:
        await engine.dispose()


def test_promotion_receipt_is_not_wired_to_public_routes() -> None:
    public_routes = "\n".join(
        path.read_text(encoding="utf-8") for path in ROUTES_ROOT.glob("*.py")
    )

    assert "v2_chain.promotion_receipt" not in public_routes
    assert "record_promotion_receipt" not in public_routes
