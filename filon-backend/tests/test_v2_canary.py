from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.v2_chain.canary import (
    CanaryAssignment,
    V2CanaryError,
    V2CanaryEligibilityEvidence,
    V2CanaryEligibilityPolicy,
    V2CanaryPayload,
    assign_closed_cohort,
    evaluate_canary_eligibility,
    run_canary_read,
)
from quality_lab.v2_canary import (
    V2CanaryEvidence,
    evaluate_shadow_to_canary,
)


SUBJECT = "sha256:" + "a" * 64
OTHER_SUBJECT = "sha256:" + "b" * 64
POLICY_ID = "sha256:" + "c" * 64


def _evidence(**overrides) -> V2CanaryEvidence:
    values = {
        "single_alembic_head": True,
        "postgresql_migration_green": True,
        "expand_only_rollback_green": True,
        "replay_idempotent": True,
        "cursor_monotone": True,
        "single_execution_proven": True,
        "inherited_benchmarks_green": True,
        "safety_invariants_green": True,
        "real_terminal_windows": 30,
        "performance_distribution_ready": True,
        "collision_exercise_green": True,
        "stale_interruption_green": True,
        "recovery_replay_green": True,
        "dark_reader_qualified": True,
        "dark_reader_rollback_green": True,
        "observed_response_types": ("ABSTAIN", "BUY_NOW", "WAIT"),
    }
    values.update(overrides)
    return V2CanaryEvidence(**values)


def _eligibility(**overrides):
    values = {
        "vertical": "smartphones",
        "locale": "fr-BE",
        "decision_type": "purchase_advice",
        "data_age_seconds": 30,
        "dependencies_admissible": True,
        "critical_unknown": False,
        "hard_constraint_violation": False,
        "confidence_required": False,
        "confidence_admissible": False,
        "rollback_available": True,
    }
    values.update(overrides)
    return evaluate_canary_eligibility(
        policy=V2CanaryEligibilityPolicy(
            policy_id=POLICY_ID,
            supported_verticals=("smartphones",),
            supported_locales=("fr-BE",),
            supported_decision_types=("purchase_advice",),
            maximum_data_age_seconds=300,
        ),
        evidence=V2CanaryEligibilityEvidence(**values),
    )


def test_shadow_to_canary_gate_requires_every_objective_proof() -> None:
    report = evaluate_shadow_to_canary(_evidence())

    assert report.status == "CANARY_AUTHORIZED"
    assert all(report.gates.values())
    assert report.blocked_response_types == ()
    assert report.blocker_codes == ()
    assert report.evaluation_id.startswith("sha256:")


def test_unobserved_output_stays_off_without_blocking_observed_outputs() -> None:
    report = evaluate_shadow_to_canary(
        _evidence(observed_response_types=("ABSTAIN",))
    )

    assert report.status == "CANARY_AUTHORIZED"
    assert report.blocked_response_types == ("BUY_NOW", "WAIT")
    assert report.blocker_codes == (
        "RESPONSE_TYPE_OFF:BUY_NOW",
        "RESPONSE_TYPE_OFF:WAIT",
    )


def test_missing_recovery_or_real_windows_keeps_canary_closed() -> None:
    report = evaluate_shadow_to_canary(
        _evidence(real_terminal_windows=29, recovery_replay_green=False)
    )

    assert report.status == "CANARY_HOLD"
    assert report.gates["thirty_terminal_windows"] is False
    assert report.gates["recovery_exercises"] is False
    assert "THIRTY_TERMINAL_WINDOWS" in report.blocker_codes
    assert "RECOVERY_EXERCISES" in report.blocker_codes


def test_closed_cohort_is_exact_and_fail_closed() -> None:
    assert assign_closed_cohort(
        subject_digest=SUBJECT,
        allowed_subject_digests=(SUBJECT,),
    ).cohort == "canary"
    assert assign_closed_cohort(
        subject_digest=OTHER_SUBJECT,
        allowed_subject_digests=(SUBJECT,),
    ) == CanaryAssignment("core", "outside_closed_cohort")
    assert assign_closed_cohort(
        subject_digest="invalid",
        allowed_subject_digests=(SUBJECT,),
    ) == CanaryAssignment("core", "subject_invalid")
    assert assign_closed_cohort(
        subject_digest=None,
        allowed_subject_digests=(SUBJECT,),
    ) == CanaryAssignment("core", "subject_absent")
    with pytest.raises(V2CanaryError, match="duplicates"):
        assign_closed_cohort(
            subject_digest=SUBJECT,
            allowed_subject_digests=(SUBJECT, SUBJECT),
        )


def test_canary_eligibility_requires_every_request_proof() -> None:
    assert _eligibility().eligible is True
    assert _eligibility().reason_code == "eligible"

    cases = (
        ({"vertical": "audio"}, "vertical_unsupported"),
        ({"locale": "nl-BE"}, "locale_unsupported"),
        ({"decision_type": "comparison"}, "decision_type_unsupported"),
        ({"dependencies_admissible": False}, "dependencies_not_admissible"),
        ({"data_age_seconds": None}, "data_not_fresh"),
        ({"data_age_seconds": 301}, "data_not_fresh"),
        ({"critical_unknown": True}, "critical_unknown"),
        ({"hard_constraint_violation": True}, "hard_constraint_violation"),
        (
            {"confidence_required": True, "confidence_admissible": False},
            "confidence_not_admissible",
        ),
        ({"rollback_available": False}, "rollback_unavailable"),
    )
    for overrides, reason in cases:
        decision = _eligibility(**overrides)
        assert decision.eligible is False
        assert decision.reason_code == reason
        assert decision.evaluation_id.startswith("sha256:")


@pytest.mark.asyncio
async def test_canary_returns_entire_v2_response_only_when_fully_proven() -> None:
    core = {"source": "core", "items": [1]}
    v2 = {"source": "v2", "items": [2]}
    core_reader = AsyncMock(return_value=core)
    v2_reader = AsyncMock(
        return_value=V2CanaryPayload(
            response=v2,
            chain_complete=True,
            safety_state="SAFE",
            provenance_complete=True,
            response_type="BUY_NOW",
        )
    )

    result = await run_canary_read(
        assignment=CanaryAssignment("canary", "closed_cohort_match"),
        eligibility=_eligibility(),
        gate=evaluate_shadow_to_canary(_evidence()),
        core_reader=core_reader,
        v2_reader=v2_reader,
    )

    assert result.response is v2
    assert result.receipt.source == "v2"
    assert result.receipt.fallback_reason is None
    assert result.receipt.raw_query_retained is False
    core_reader.assert_awaited_once()
    v2_reader.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("payload", "reason"),
    (
        (
            V2CanaryPayload({}, False, "SAFE", True, "BUY_NOW"),
            "chain_incomplete",
        ),
        (
            V2CanaryPayload({}, True, "INVALID", True, "BUY_NOW"),
            "safety_state_not_servable",
        ),
        (
            V2CanaryPayload({}, True, "SAFE", False, "BUY_NOW"),
            "provenance_incomplete",
        ),
    ),
)
async def test_canary_falls_back_to_whole_core_response(
    payload: V2CanaryPayload,
    reason: str,
) -> None:
    core = {"source": "core", "items": [1]}

    result = await run_canary_read(
        assignment=CanaryAssignment("canary", "closed_cohort_match"),
        eligibility=_eligibility(),
        gate=evaluate_shadow_to_canary(_evidence()),
        core_reader=AsyncMock(return_value=core),
        v2_reader=AsyncMock(return_value=payload),
    )

    assert result.response is core
    assert result.receipt.source == "core_v1"
    assert result.receipt.fallback_reason == reason


@pytest.mark.asyncio
async def test_canary_error_or_closed_gate_returns_core_without_partial_mix() -> None:
    core = {"source": "core", "nested": {"items": [1]}}
    v2_error = AsyncMock(side_effect=RuntimeError("sensitive-payload"))

    errored = await run_canary_read(
        assignment=CanaryAssignment("canary", "closed_cohort_match"),
        eligibility=_eligibility(),
        gate=evaluate_shadow_to_canary(_evidence()),
        core_reader=AsyncMock(return_value=core),
        v2_reader=v2_error,
    )
    hold_reader = AsyncMock()
    held = await run_canary_read(
        assignment=CanaryAssignment("canary", "closed_cohort_match"),
        eligibility=_eligibility(),
        gate=evaluate_shadow_to_canary(
            _evidence(real_terminal_windows=0)
        ),
        core_reader=AsyncMock(return_value=core),
        v2_reader=hold_reader,
    )

    assert errored.response is core
    assert errored.receipt.fallback_reason == "v2_reader_error"
    assert "sensitive" not in str(errored.receipt)
    assert held.response is core
    assert held.receipt.fallback_reason == "gate_not_authorized"
    hold_reader.assert_not_awaited()


@pytest.mark.asyncio
async def test_unobserved_response_type_remains_core() -> None:
    core = {"source": "core"}
    gate = evaluate_shadow_to_canary(
        _evidence(observed_response_types=("ABSTAIN",))
    )

    result = await run_canary_read(
        assignment=CanaryAssignment("canary", "closed_cohort_match"),
        eligibility=_eligibility(),
        gate=gate,
        core_reader=AsyncMock(return_value=core),
        v2_reader=AsyncMock(
            return_value=V2CanaryPayload(
                response={"source": "v2"},
                chain_complete=True,
                safety_state="SAFE",
                provenance_complete=True,
                response_type="BUY_NOW",
            )
        ),
    )

    assert result.response is core
    assert result.receipt.fallback_reason == "response_type_not_qualified"


@pytest.mark.asyncio
async def test_ineligible_request_never_calls_v2() -> None:
    core = {"source": "core"}
    v2_reader = AsyncMock()

    result = await run_canary_read(
        assignment=CanaryAssignment("canary", "closed_cohort_match"),
        eligibility=_eligibility(data_age_seconds=301),
        gate=evaluate_shadow_to_canary(_evidence()),
        core_reader=AsyncMock(return_value=core),
        v2_reader=v2_reader,
    )

    assert result.response is core
    assert result.receipt.fallback_reason == "data_not_fresh"
    assert result.receipt.eligibility_status == "ineligible"
    v2_reader.assert_not_awaited()


def test_canary_is_not_wired_to_public_routes() -> None:
    from pathlib import Path

    routes = Path(__file__).resolve().parents[1] / "app" / "api" / "routes"
    public_sources = "\n".join(
        path.read_text(encoding="utf-8") for path in routes.glob("*.py")
    )

    assert "v2_chain.canary" not in public_sources
    assert "run_canary_read" not in public_sources
