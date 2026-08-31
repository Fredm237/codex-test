"""Contrats Phase 1 Product Identity, fail-closed et sans lecteur public."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_ROOT = ROOT / "contracts" / "product-identity" / "v1"


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "schema_name",
    ["identity-assertion.schema.json", "identity-resolution.schema.json"],
)
def test_product_identity_schemas_are_valid_draft_2020_12(schema_name: str):
    Draft202012Validator.check_schema(_json(CONTRACT_ROOT / schema_name))


@pytest.mark.parametrize(
    ("example_name", "schema_name"),
    [
        ("exact-variant.json", "identity-resolution.schema.json"),
        ("unresolved-model.json", "identity-resolution.schema.json"),
    ],
)
def test_product_identity_examples_validate(example_name: str, schema_name: str):
    validator = Draft202012Validator(_json(CONTRACT_ROOT / schema_name))
    assert list(
        validator.iter_errors(_json(CONTRACT_ROOT / "examples" / example_name))
    ) == []


def _assertion(identifier: dict[str, str]) -> dict:
    return {
        "contract_version": "1.0.0",
        "raw_source_record_id": 17,
        "source_type": "awin_feed",
        "source_ref": "awin-feed:42",
        "observed_at": "2026-08-31T12:00:00Z",
        "subject_type": "variant",
        "field": "identifier",
        "value": identifier["normalized_value"],
        "identifier": identifier,
        "status": "validated",
        "transformation": "awin_product_identity",
        "transformation_version": "v1",
    }


@pytest.mark.parametrize(
    "identifier",
    [
        {"namespace": "gtin", "scope": "global", "normalized_value": "4006381333931"},
        {"namespace": "mpn", "scope": "brand:12", "normalized_value": "WH1000XM6"},
        {"namespace": "merchant_sku", "scope": "merchant:7", "normalized_value": "SKU-1"},
        {
            "namespace": "source_product_id",
            "scope": "source:awin:merchant-7",
            "normalized_value": "AW-42",
        },
    ],
)
def test_identifier_scopes_accept_only_their_explicit_namespace(identifier):
    validator = Draft202012Validator(
        _json(CONTRACT_ROOT / "identity-assertion.schema.json")
    )
    assert list(validator.iter_errors(_assertion(identifier))) == []


@pytest.mark.parametrize(
    "identifier",
    [
        {"namespace": "gtin", "scope": "merchant:7", "normalized_value": "4006381333931"},
        {"namespace": "mpn", "scope": "global", "normalized_value": "WH1000XM6"},
        {"namespace": "merchant_sku", "scope": "global", "normalized_value": "SKU-1"},
        {"namespace": "source_product_id", "scope": "global", "normalized_value": "AW-42"},
    ],
)
def test_identifier_scopes_fail_closed(identifier):
    validator = Draft202012Validator(
        _json(CONTRACT_ROOT / "identity-assertion.schema.json")
    )
    assert list(validator.iter_errors(_assertion(identifier))) != []


def test_non_resolved_identity_can_never_carry_a_canonical_id():
    payload = _json(CONTRACT_ROOT / "examples" / "unresolved-model.json")
    payload["canonical_id"] = 42
    validator = Draft202012Validator(
        _json(CONTRACT_ROOT / "identity-resolution.schema.json")
    )
    assert list(validator.iter_errors(payload)) != []


def test_resolved_identity_requires_at_least_one_raw_evidence():
    payload = _json(CONTRACT_ROOT / "examples" / "exact-variant.json")
    payload["evidence_raw_source_ids"] = []
    validator = Draft202012Validator(
        _json(CONTRACT_ROOT / "identity-resolution.schema.json")
    )
    assert list(validator.iter_errors(payload)) != []
