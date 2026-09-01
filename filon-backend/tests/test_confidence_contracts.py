from __future__ import annotations

import json
from pathlib import Path

import jsonschema


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "contracts" / "confidence" / "v1"


def test_confidence_schema_and_synthetic_examples_are_valid() -> None:
    schema = json.loads((CONTRACT / "confidence-report.schema.json").read_text())
    jsonschema.Draft202012Validator.check_schema(schema)
    validator = jsonschema.Draft202012Validator(schema)
    for path in sorted((CONTRACT / "examples").glob("*.json")):
        validator.validate(json.loads(path.read_text()))


def test_manifest_separates_coverage_and_locks_all_dimensions() -> None:
    manifest = json.loads((CONTRACT / "manifest.json").read_text())
    assert manifest["evidence_coverage_is_probability"] is False
    assert manifest["raw_context_retained"] is False
    assert manifest["dimensions"] == [
        "RETRIEVAL_CONFIDENCE",
        "ENTITY_MATCH_CONFIDENCE",
        "ATTRIBUTE_CONFIDENCE",
        "OFFER_CONFIDENCE",
        "DECISION_CONFIDENCE",
    ]
