from __future__ import annotations

import json
from pathlib import Path

import jsonschema


ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = tuple(
    ROOT / "contracts" / "offer-optimization" / version for version in ("v1", "v2")
)


def test_offer_optimization_schema_and_examples_are_valid() -> None:
    for contract in CONTRACTS:
        schema = json.loads((contract / "offer-optimization-run.schema.json").read_text())
        jsonschema.Draft202012Validator.check_schema(schema)
        validator = jsonschema.Draft202012Validator(
            schema, format_checker=jsonschema.FormatChecker()
        )
        for path in sorted((contract / "examples").glob("*.json")):
            validator.validate(json.loads(path.read_text()))


def test_manifest_locks_user_value_and_fail_closed_policies() -> None:
    manifest = json.loads((CONTRACTS[-1] / "manifest.json").read_text())
    assert manifest["ranking_precondition"] == "only_rank_1_product_can_receive_an_offer"
    assert manifest["truth_policy"] == "only_verified_offer_truth_can_be_optimized"
    assert manifest["unknown_policy"] == "unknown_or_unsourced_operational_fact_never_receives_a_fallback"
    assert manifest["commercial_policy"] == "commission_affiliation_and_platform_revenue_are_not_inputs"
    assert manifest["landed_cost_policy"] == "price_plus_shipping_minus_explicit_sourced_cashback"
    assert manifest["returns_policy"] == "returns_must_be_explicitly_accepted_with_a_sourced_period"
    assert manifest["activation_policy"] == "shadow_only_no_public_reader"
