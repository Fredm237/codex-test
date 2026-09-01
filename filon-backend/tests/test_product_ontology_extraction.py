"""Extracteur fail-closed Phase 4 Product Ontology."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from app.product_ontology.extraction import (
    ProductOntologyExtractionError,
    extract_product_ontology,
)


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "contracts" / "product-ontology" / "v1" / "product-ontology-assertion.schema.json"
VALIDATOR = Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8")))
OBSERVED = datetime(2026, 9, 1, 10, tzinfo=timezone.utc)
EVALUATED = datetime(2026, 9, 1, 11, tzinfo=timezone.utc)


def _extract(row: dict, *, variant_id: int | None = 7) -> dict:
    return extract_product_ontology(
        row,
        raw_source_record_id=1,
        source_type="synthetic_test",
        source_ref="synthetic:ontology:1",
        observed_at=OBSERVED,
        evaluated_at=EVALUATED,
        offer_id=2,
        variant_id=variant_id,
    )


def _assert_valid(payload: dict) -> None:
    assert list(VALIDATOR.iter_errors(payload)) == []


def test_explicit_smartphone_is_verified_primary_with_provenance():
    payload = _extract(
        {
            "name": "Example Smartphone 128GB",
            "merchant_category": "Smartphones",
            "offer_kind": "physical_product",
        }
    )
    _assert_valid(payload)
    assert payload["ontology_status"] == "VERIFIED"
    assert payload["product_role"]["value"] == "PRIMARY_PRODUCT"
    assert payload["classification"]["product_type"]["value"]["concept_key"] == "smartphone"
    assert payload["attributes"][0]["value"] == {"value_type": "integer", "value": 128, "unit": "GB"}


def test_ambiguous_compatibility_never_defaults_to_primary_or_canonical():
    payload = _extract(
        {
            "name": "Compatible with Example Smartphone",
            "merchant_category": "Mobile device",
            "offer_kind": "physical_product",
        }
    )
    _assert_valid(payload)
    assert payload["ontology_status"] == "PARTIAL"
    assert payload["product_role"] == {"state": "unknown", "value": "UNKNOWN", "evidence": []}
    assert payload["relationships"][0]["target_state"] == "observed_text"
    assert payload["relationships"][0]["target_variant_id"] is None


def test_synthetic_family_name_without_product_noun_never_becomes_primary():
    payload = _extract(
        {
            "name": "Example Climate 9000 BTU",
            "merchant_category": "Air conditioners",
            "offer_kind": "physical_product",
        }
    )
    _assert_valid(payload)
    assert payload["product_role"] == {
        "state": "unknown",
        "value": "UNKNOWN",
        "evidence": [],
    }


@pytest.mark.parametrize(
    "offer_kind, name, expected",
    [
        ("accommodation", "Holiday apartment Example Coast", "ACCOMMODATION"),
        ("digital_content", "Software licence download Example Studio", "DIGITAL_CONTENT"),
        ("service", "Installation service for Example Climate", "SERVICE"),
    ],
)
def test_structured_offer_kinds_remain_distinct(offer_kind: str, name: str, expected: str):
    payload = _extract({"name": name, "offer_kind": offer_kind})
    _assert_valid(payload)
    assert payload["product_role"]["value"] == expected


def test_explicit_facets_are_sourced_and_absence_stays_empty():
    payload = _extract(
        {
            "name": "Women's waterproof cotton winter running jacket casual",
            "merchant_category": "Jackets",
            "offer_kind": "physical_product",
        }
    )
    _assert_valid(payload)
    assert payload["facets"]["audience"][0]["value"]["concept_key"] == "audience.women"
    assert payload["facets"]["material"][0]["value"]["concept_key"] == "material.cotton"
    assert payload["facets"]["compatibility"] == []
    assert payload["facets"]["function"][0]["value"]["concept_key"] == "function.waterproof"


def test_missing_variant_is_quarantined_without_losing_observed_facts():
    payload = _extract(
        {"name": "Protective case for Example Smartphone", "offer_kind": "physical_product"},
        variant_id=None,
    )
    _assert_valid(payload)
    assert payload["ontology_status"] == "QUARANTINED"
    assert payload["reason_codes"][0] == "identity_unresolved"
    assert payload["product_role"]["value"] == "ACCESSORY"


def test_naive_or_future_timestamps_fail_closed():
    with pytest.raises(ProductOntologyExtractionError, match="timezone-aware"):
        extract_product_ontology(
            {},
            raw_source_record_id=1,
            source_type="synthetic_test",
            source_ref="synthetic:ontology:1",
            observed_at=datetime(2026, 9, 1),
            evaluated_at=EVALUATED,
            offer_id=2,
            variant_id=7,
        )
    with pytest.raises(ProductOntologyExtractionError, match="cannot be after"):
        extract_product_ontology(
            {},
            raw_source_record_id=1,
            source_type="synthetic_test",
            source_ref="synthetic:ontology:1",
            observed_at=EVALUATED,
            evaluated_at=OBSERVED,
            offer_id=2,
            variant_id=7,
        )
