from __future__ import annotations

import json
from pathlib import Path

import jsonschema


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "contracts" / "constraint-engine" / "v1"


def test_constraint_schema_and_examples_are_valid():
    schema = json.loads((CONTRACT / "constraint-evaluation-run.schema.json").read_text())
    jsonschema.Draft202012Validator.check_schema(schema)
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    for path in sorted((CONTRACT / "examples").glob("*.json")):
        validator.validate(json.loads(path.read_text()))


def test_manifest_locks_fail_closed_and_no_ranking_policies():
    manifest = json.loads((CONTRACT / "manifest.json").read_text())
    assert manifest["unknown_policy"] == "unknown_never_satisfies_a_required_constraint"
    assert manifest["ranking_policy"] == "preferences_are_observations_not_scores"
    assert manifest["privacy_policy"] == "raw_context_and_user_profile_never_persisted"
