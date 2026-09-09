from __future__ import annotations

import json
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_PATH = (
    REPOSITORY_ROOT
    / "docs"
    / "architecture"
    / "V2_FACTUAL_PUBLIC_QUALIFICATION_EVIDENCE.json"
)


def test_factual_public_evidence_is_bounded_and_fail_closed() -> None:
    evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))

    assert evidence["schema_version"] == (
        "filon-v2-factual-public-qualification-evidence/v1"
    )
    assert evidence["candidate_status"] == "PUBLIC_ACTIVE_PROVEN"
    assert evidence["scope"]["requested_public_response_types"] == [
        "FACTUAL_OPTIONS"
    ]
    assert evidence["scope"]["blocked_response_types"] == [
        "ABSTAIN",
        "BUY_NOW",
        "WAIT",
    ]

    canary = evidence["canary"]
    assert canary["observations"] >= 30
    assert canary["paired_observations"] == canary["observations"]
    assert canary["v2_served"] == canary["observations"]
    assert canary["served_response_type_counts"] == {
        "FACTUAL_OPTIONS": canary["observations"]
    }
    assert canary["eligible_fallbacks"] == 0
    assert canary["reader_errors"] == 0
    assert canary["invalid_or_incomplete"] == 0
    assert canary["provenance_complete"] == canary["observations"]
    assert canary["raw_query_retained"] == 0
    assert canary["p95_latency_delta_us"] <= 0

    rollback = evidence["rollback_to_shadow"]
    assert rollback["status"] == "VERIFIED"
    assert rollback["canary_reader_enabled"] is False
    assert rollback["public_reader_enabled"] is False
    assert rollback["core_v1_probe_http"] == 200
    assert rollback["canary_observations_before"] == (
        rollback["canary_observations_after"]
    )
    assert rollback["journal_preserved"] is True
    assert rollback["restored_mode"] == "canary"
    assert rollback["restored_canary_reader_enabled"] is True
    assert rollback["restored_public_reader_enabled"] is False

    policy = evidence["public_policy"]
    assert policy["status"] == "ACTIVE_PROVEN"
    assert policy["current_mode"] == "public"
    assert policy["current_public_reader"] is True
    assert policy["current_canary_reader"] is False
    assert policy["requested_response_types"] == ["FACTUAL_OPTIONS"]
    assert policy["core_v1_computed_first"] is True
    assert policy["core_v1_fallback"] is True
    assert policy["no_partial_v2_response"] is True
    assert policy["no_implicit_verdict"] is True
    assert policy["factual_options_are_not_a_recommendation"] is True

    activation = evidence["public_activation"]
    assert activation["qualification_status"] == "PUBLIC_AUTHORIZED"
    assert activation["dry_run_apply_replay"] == "VERIFIED"
    assert activation["runtime_mode"] == "public"
    assert activation["public_reader_enabled"] is True
    assert activation["canary_reader_enabled"] is False
    assert activation["health_http"] == {
        "live": 200,
        "ready": 200,
        "dependencies": 200,
        "catalog_pulse": 200,
    }
    assert activation["public_observations"] >= 2
    assert activation["public_v2_factual_options"] >= 1
    assert activation["public_core_v1_fallbacks"] >= 1
    assert activation["fallback_reason"] == "response_type_not_qualified"
    assert activation["safety_violations"] == 0

    assert evidence["raw_payload_retained"] is False
    assert evidence["user_data_retained"] is False
    assert evidence["secrets_retained"] is False
