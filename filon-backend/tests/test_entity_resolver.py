"""Resolver Entity Resolution shadow, hiérarchique et abstentionniste."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from app.product_graph.entity_resolution import (
    EntityResolverError,
    confidence_is_finite,
    resolve_entity_candidates,
)
from app.product_graph.entity_signals import project_entity_signals


OBSERVED_AT = datetime(2026, 9, 1, 0, 0, tzinfo=timezone.utc)
ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "contracts" / "entity-resolution" / "v1" / "entity-resolution-decision.schema.json"


def _profile(raw_id: int, row: dict, *, candidate_id=None, identifiers=None):
    projection = project_entity_signals(
        row,
        raw_source_record_id=raw_id,
        source_type="awin_feed",
        source_ref=f"awin-feed:{raw_id}",
        observed_at=OBSERVED_AT,
    ).as_contract()
    payload = {
        "raw_source_record_id": projection["raw_source_record_id"],
        "source_type": projection["source_type"],
        "source_ref": projection["source_ref"],
        "observed_at": projection["observed_at"],
        "signals": projection["signals"],
        "identifiers": identifiers or {},
    }
    if candidate_id is not None:
        payload["candidate_id"] = candidate_id
    return payload


def _resolve(subject, candidates, subject_type="variant"):
    return resolve_entity_candidates(subject, candidates, subject_type=subject_type)


def _assert_contract(decision):
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    errors = list(Draft202012Validator(schema).iter_errors(decision.as_contract()))
    assert errors == []
    assert confidence_is_finite(decision)


def test_exact_gtin_remains_authoritative():
    subject = _profile(1, {"product_name": "Phone"}, identifiers={"ean": "4006381333931"})
    candidate = _profile(2, {"product_name": "Completely different"}, candidate_id=10, identifiers={"gtin": "4006381333931"})
    decision = _resolve(subject, [candidate])
    assert decision.resolution == "EXACT_VERIFIED"
    assert decision.canonical_id == 10
    assert decision.confidence_score == 1.0
    assert decision.reason_codes == ("exact_global_identifier",)
    _assert_contract(decision)


def test_exact_gtin_never_falls_back_to_structured_similarity():
    row = {"brand_name": "Example", "mpn": "ABC-1", "model": "Phone Pro", "color": "black"}
    subject = _profile(1, row, identifiers={"ean": "4006381333931"})
    candidate = _profile(2, row, candidate_id=10, identifiers={"ean": "9780201379624"})
    decision = _resolve(subject, [candidate])
    assert decision.resolution == "UNRESOLVED"
    assert decision.canonical_id is None
    assert decision.candidate_ids == ()
    _assert_contract(decision)


def test_invalid_identifier_blocks_structured_fallback():
    row = {"brand_name": "Example", "mpn": "ABC-1", "model": "Phone Pro", "color": "black"}
    subject = _profile(1, row, identifiers={"ean": "invalid"})
    candidate = _profile(2, row, candidate_id=10)
    decision = _resolve(subject, [candidate])
    assert decision.resolution == "UNRESOLVED"
    assert decision.reason_codes == ("identifier_conflict",)
    assert decision.canonical_id is None
    _assert_contract(decision)


def test_candidate_with_invalid_identifier_is_vetoed():
    row = {"brand_name": "Example", "mpn": "ABC-1", "model": "Phone Pro", "color": "black"}
    subject = _profile(1, row)
    candidate = _profile(2, row, candidate_id=10, identifiers={"ean": "invalid"})
    decision = _resolve(subject, [candidate])
    assert decision.resolution == "AMBIGUOUS"
    assert "identifier_conflict" in decision.reason_codes
    assert any(conflict.field == "identifier" for conflict in decision.conflicts)
    _assert_contract(decision)


def test_two_distinct_strong_signals_can_produce_high_confidence():
    row = {
        "brand_name": "Sony",
        "mpn": "WH1000XM5B",
        "model": "WH-1000XM5",
        "color": "black",
        "product_role": "primary_product",
    }
    subject = _profile(1, row)
    candidate = _profile(2, row, candidate_id=20)
    decision = _resolve(subject, [candidate])
    assert decision.resolution == "HIGH_CONFIDENCE"
    assert decision.canonical_id == 20
    assert {"brand_scoped_mpn", "structured_model_agreement", "structured_variant_agreement"} <= set(decision.reason_codes)
    assert decision.confidence_score >= 0.94
    assert len({item.signal for item in decision.evidence if item.strength == "strong"}) >= 2
    _assert_contract(decision)


def test_one_strong_signal_is_only_probable_and_never_canonical():
    subject = _profile(1, {"model": "Phone Pro"})
    candidate = _profile(2, {"model": "Phone Pro"}, candidate_id=20)
    decision = _resolve(subject, [candidate])
    assert decision.resolution == "PROBABLE"
    assert decision.canonical_id is None
    assert decision.candidate_ids == (20,)
    _assert_contract(decision)


def test_title_and_image_only_are_candidate_generation_not_identity():
    row = {"product_name": "Wireless headphones black", "merchant_image_url": "https://example.test/a.jpg"}
    subject = _profile(1, row)
    candidate = _profile(2, row, candidate_id=20)
    decision = _resolve(subject, [candidate])
    assert decision.resolution == "PROBABLE"
    assert decision.canonical_id is None
    assert all(item.strength == "weak" for item in decision.evidence)
    assert "candidate_generation_only" in decision.reason_codes
    _assert_contract(decision)


def test_variant_conflict_vetoes_an_otherwise_strong_candidate():
    base = {"brand_name": "Apple", "mpn": "PHONE-16", "model": "Phone 16"}
    subject = _profile(1, {**base, "storage": "128GB"})
    candidate = _profile(2, {**base, "storage": "256GB"}, candidate_id=20)
    decision = _resolve(subject, [candidate])
    assert decision.resolution == "AMBIGUOUS"
    assert decision.canonical_id is None
    assert decision.candidate_ids == (20,)
    assert any(conflict.field == "storage" for conflict in decision.conflicts)
    assert "variant_attribute_conflict" in decision.reason_codes
    _assert_contract(decision)


def test_same_mpn_under_different_brands_is_a_scope_conflict():
    subject = _profile(1, {"brand_name": "Brand A", "mpn": "SHARED-1", "model": "Model"})
    candidate = _profile(2, {"brand_name": "Brand B", "mpn": "SHARED-1", "model": "Model"}, candidate_id=20)
    decision = _resolve(subject, [candidate])
    assert decision.resolution == "AMBIGUOUS"
    assert "scope_mismatch" in decision.reason_codes
    assert any(conflict.reason_code == "scope_mismatch" for conflict in decision.conflicts)
    _assert_contract(decision)


def test_multiple_equally_supported_candidates_force_ambiguity():
    row = {"brand_name": "Example", "mpn": "ABC-1", "model": "Model Pro", "color": "black"}
    subject = _profile(1, row)
    candidates = [
        _profile(2, row, candidate_id=20),
        _profile(3, row, candidate_id=30),
    ]
    decision = _resolve(subject, candidates)
    assert decision.resolution == "AMBIGUOUS"
    assert decision.canonical_id is None
    assert decision.candidate_ids == (20, 30)
    assert decision.conflicts[0].reason_code == "multiple_candidates"
    _assert_contract(decision)


def test_missing_signals_remain_unresolved_with_empty_evidence():
    subject = _profile(1, {})
    decision = _resolve(subject, [])
    assert decision.resolution == "UNRESOLVED"
    assert decision.candidate_ids == ()
    assert decision.evidence == ()
    _assert_contract(decision)


def test_conflicting_aliases_cannot_be_used_as_evidence():
    subject = _profile(1, {"model": "Phone", "model_number": "Phone Pro", "brand_name": "Example"})
    candidate = _profile(2, {"model": "Phone", "brand_name": "Example"}, candidate_id=20)
    decision = _resolve(subject, [candidate])
    assert decision.resolution == "AMBIGUOUS"
    assert any(conflict.field == "model" for conflict in decision.conflicts)
    _assert_contract(decision)


def test_invalid_only_candidate_can_be_ambiguous_without_normalized_evidence():
    subject = _profile(1, {"mpn": {"invalid": "value"}})
    candidate = _profile(2, {}, candidate_id=20)
    decision = _resolve(subject, [candidate])
    assert decision.resolution == "AMBIGUOUS"
    assert decision.evidence == ()
    assert decision.conflicts
    _assert_contract(decision)


@pytest.mark.parametrize(
    "candidates, message",
    [
        ([{"candidate_id": 1}], "raw_source_record_id"),
        ([], ""),
    ],
)
def test_resolver_input_contract_is_bounded(candidates, message):
    subject = _profile(1, {})
    if candidates:
        with pytest.raises(EntityResolverError, match=message):
            _resolve(subject, candidates)
    else:
        oversized = [_profile(index + 2, {}, candidate_id=index + 1) for index in range(101)]
        with pytest.raises(EntityResolverError, match="too large"):
            _resolve(subject, oversized)


def test_duplicate_candidate_ids_are_rejected():
    subject = _profile(1, {"model": "Phone"})
    candidates = [
        _profile(2, {"model": "Phone"}, candidate_id=20),
        _profile(3, {"model": "Phone"}, candidate_id=20),
    ]
    with pytest.raises(EntityResolverError, match="unique"):
        _resolve(subject, candidates)
