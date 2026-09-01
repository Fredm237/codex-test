from __future__ import annotations

import json
from pathlib import Path

import jsonschema


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "contracts" / "product-ranking" / "v1"


def test_product_ranking_schema_and_examples_are_valid() -> None:
    schema = json.loads((CONTRACT / "product-ranking-run.schema.json").read_text())
    jsonschema.Draft202012Validator.check_schema(schema)
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    for path in sorted((CONTRACT / "examples").glob("*.json")):
        validator.validate(json.loads(path.read_text()))


def test_manifest_locks_product_first_fail_closed_policies() -> None:
    manifest = json.loads((CONTRACT / "manifest.json").read_text())
    assert manifest["eligibility_policy"] == "only_constraint_status_eligible_can_be_ranked"
    assert manifest["unknown_policy"] == "unknown_dimension_never_receives_a_score"
    assert manifest["commercial_policy"] == "commission_and_affiliation_are_not_inputs"
    assert manifest["offer_policy"] == "offer_optimization_is_phase_8"
    assert manifest["privacy_policy"] == "raw_context_and_user_profile_never_persisted"
