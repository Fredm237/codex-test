"""Contrat Phase 4 Product Ontology, shadow-only et fail-closed."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_ROOT = ROOT / "contracts" / "product-ontology" / "v1"
SCHEMA = CONTRACT_ROOT / "product-ontology-assertion.schema.json"


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _evidence(field: str = "product_type") -> dict:
    return {
        "raw_source_record_id": 1,
        "source_type": "synthetic_contract",
        "source_ref": "synthetic:product-ontology:1",
        "observed_at": "2000-01-01T00:00:00Z",
        "field": field,
        "transformation": "synthetic_contract_projection",
        "transformation_version": "product-ontology-contract-test/v1",
        "evidence_strength": "exact_structured",
    }


def _concept(key: str, label: str, field: str) -> dict:
    return {
        "state": "known",
        "value": {"concept_key": key, "label": label},
        "evidence": [_evidence(field)],
    }


def _unknown_concept() -> dict:
    return {"state": "unknown", "value": None, "evidence": []}


def _payload() -> dict:
    return {
        "contract_version": "1.0.0",
        "raw_source_record_id": 1,
        "offer_id": 1,
        "variant_id": 1,
        "ontology_status": "VERIFIED",
        "classification": {
            "category": _concept("electronics.telephony", "Téléphonie", "category"),
            "subcategory": _concept("electronics.telephony.smartphones", "Smartphones", "subcategory"),
            "product_type": _concept("smartphone", "Smartphone", "product_type"),
        },
        "product_role": {
            "state": "known",
            "value": "PRIMARY_PRODUCT",
            "evidence": [_evidence("product_role")],
        },
        "attributes": [
            {
                "attribute_key": "storage",
                "state": "known",
                "value": {"value_type": "integer", "value": 128, "unit": "GB"},
                "evidence": [_evidence("storage")],
            }
        ],
        "relationships": [],
        "facets": {
            "use_case": [],
            "audience": [],
            "compatibility": [],
            "style": [],
            "material": [],
            "season": [],
            "occasion": [],
            "function": [],
        },
        "legacy_taxonomy": {
            "category": "Téléphonie",
            "subcategory": "Smartphones",
            "migration_state": "mapped_exact",
            "evidence": [_evidence("legacy_category")],
        },
        "reason_codes": ["ontology_verified"],
        "extractor_version": "product-ontology-extractor/v1",
        "policy_version": "product-ontology-policy/v1",
        "evaluated_at": "2000-01-01T01:00:00Z",
    }


def _errors(payload: dict) -> list:
    return list(Draft202012Validator(_json(SCHEMA)).iter_errors(payload))


def test_product_ontology_schema_is_valid_draft_2020_12():
    Draft202012Validator.check_schema(_json(SCHEMA))


def test_verified_synthetic_assertion_validates():
    assert _errors(_payload()) == []


@pytest.mark.parametrize("field", ["category", "product_type"])
def test_verified_requires_known_category_and_product_type(field: str):
    payload = _payload()
    payload["classification"][field] = _unknown_concept()
    assert _errors(payload) != []


def test_verified_requires_known_non_unknown_product_role():
    payload = _payload()
    payload["product_role"] = {
        "state": "unknown",
        "value": "UNKNOWN",
        "evidence": [],
    }
    assert _errors(payload) != []


def test_unknown_role_cannot_default_to_primary_product():
    payload = _payload()
    payload["ontology_status"] = "PARTIAL"
    payload["reason_codes"] = ["product_role_unknown"]
    payload["product_role"] = {
        "state": "unknown",
        "value": "PRIMARY_PRODUCT",
        "evidence": [],
    }
    assert _errors(payload) != []


def test_observed_text_relationship_cannot_claim_canonical_variant():
    payload = _payload()
    payload["relationships"] = [
        {
            "relationship_type": "ACCESSORY_FOR",
            "target_state": "observed_text",
            "target_variant_id": 99,
            "target_text": "Synthetic Phone",
            "evidence": [_evidence("compatibility")],
        }
    ]
    assert _errors(payload) != []


def test_canonical_relationship_cannot_keep_text_as_identity_substitute():
    payload = _payload()
    payload["relationships"] = [
        {
            "relationship_type": "ACCESSORY_FOR",
            "target_state": "canonical",
            "target_variant_id": 99,
            "target_text": "Synthetic Phone",
            "evidence": [_evidence("compatibility")],
        }
    ]
    assert _errors(payload) != []


def test_canonical_relationship_requires_provenance():
    payload = _payload()
    payload["relationships"] = [
        {
            "relationship_type": "ACCESSORY_FOR",
            "target_state": "canonical",
            "target_variant_id": 99,
            "target_text": None,
            "evidence": [],
        }
    ]
    assert _errors(payload) != []


def test_observed_text_relationship_is_a_valid_noncanonical_fact():
    payload = _payload()
    payload["relationships"] = [
        {
            "relationship_type": "COMPATIBLE_WITH",
            "target_state": "observed_text",
            "target_variant_id": None,
            "target_text": "Synthetic Phone",
            "evidence": [_evidence("compatibility")],
        }
    ]
    assert _errors(payload) == []


def test_invalid_attribute_cannot_retain_a_favorable_value():
    payload = _payload()
    payload["attributes"][0]["state"] = "invalid"
    assert _errors(payload) != []
    payload["attributes"][0]["value"] = None
    assert _errors(payload) == []


@pytest.mark.parametrize("value", ["1e3", "01.0", "1.1234567", 1.5])
def test_decimal_attribute_uses_exact_bounded_string(value):
    payload = _payload()
    payload["attributes"][0]["value"] = {
        "value_type": "decimal",
        "value": value,
        "unit": "kg",
    }
    assert _errors(payload) != []


def test_quarantine_requires_null_variant_and_identity_reason():
    payload = _payload()
    payload.update(
        ontology_status="QUARANTINED",
        variant_id=None,
        reason_codes=["identity_unresolved"],
    )
    assert _errors(payload) == []
    payload["variant_id"] = 1
    assert _errors(payload) != []


def test_numeric_confidence_is_not_accepted_in_evidence():
    payload = _payload()
    payload["product_role"]["evidence"][0]["confidence"] = 0.99
    assert _errors(payload) != []


def test_manifest_freezes_legacy_and_relationship_safety():
    manifest = _json(CONTRACT_ROOT / "manifest.json")
    assert manifest["status"] == "draft_for_shadow"
    assert manifest["public_reader_compatible"] is True
    assert manifest["legacy_taxonomy_policy"] == "fallback_signal_never_central_truth"
    assert manifest["relationship_policy"] == (
        "observed_text_never_becomes_canonical_without_entity_resolution"
    )
    assert (CONTRACT_ROOT / manifest["artifact"]).is_file()


def test_contract_is_deterministic_under_deep_copy():
    payload = _payload()
    assert deepcopy(payload) == payload
    assert _errors(payload) == _errors(deepcopy(payload))
