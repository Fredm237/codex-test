from __future__ import annotations

import json
from pathlib import Path

import jsonschema


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_ROOT = ROOT / "contracts" / "product-ranking"


def test_product_ranking_schema_and_examples_are_valid() -> None:
    for contract in (CONTRACT_ROOT / "v1", CONTRACT_ROOT / "v2"):
        schema = json.loads((contract / "product-ranking-run.schema.json").read_text())
        jsonschema.Draft202012Validator.check_schema(schema)
        validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
        for path in sorted((contract / "examples").glob("*.json")):
            validator.validate(json.loads(path.read_text()))


def test_manifest_locks_product_first_fail_closed_policies() -> None:
    manifest = json.loads((CONTRACT_ROOT / "v1" / "manifest.json").read_text())
    assert manifest["eligibility_policy"] == "only_constraint_status_eligible_can_be_ranked"
    assert manifest["unknown_policy"] == "unknown_dimension_never_receives_a_score"
    assert manifest["commercial_policy"] == "commission_and_affiliation_are_not_inputs"
    assert manifest["offer_policy"] == "offer_optimization_is_phase_8"
    assert manifest["privacy_policy"] == "raw_context_and_user_profile_never_persisted"


def test_v2_manifest_allows_only_disclosed_partial_ranking() -> None:
    manifest = json.loads((CONTRACT_ROOT / "v2" / "manifest.json").read_text())
    assert manifest["required_dimensions"] == ["need_fit", "evidence"]
    assert manifest["optional_unknown_dimensions"] == ["product_quality", "value"]
    assert manifest["unknown_policy"] == "unknown_dimension_never_receives_a_score"
    assert manifest["normalization_policy"] == "renormalize_only_known_sourced_weights"
    assert manifest["claim_policy"] == "ranking_is_not_a_product_quality_or_buy_wait_claim"
