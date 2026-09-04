from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator


CONTRACT_ROOT = Path(__file__).resolve().parents[2] / "contracts" / "v2-chain" / "v1"


def test_promotion_proof_contract_and_manifest_example_are_valid() -> None:
    schema = json.loads((CONTRACT_ROOT / "promotion-proof.schema.json").read_text())
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    manifest = json.loads((CONTRACT_ROOT / "manifest.json").read_text())

    assert manifest["promotion_proof_schema"] == "promotion-proof.schema.json"
    for relative_path in manifest["promotion_proof_examples"]:
        validator.validate(json.loads((CONTRACT_ROOT / relative_path).read_text()))
