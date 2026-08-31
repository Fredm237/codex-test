"""Contrat Phase 2 Entity Resolution, fail-closed et shadow-only."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_ROOT = ROOT / "contracts" / "entity-resolution" / "v1"
SCHEMA = CONTRACT_ROOT / "entity-resolution-decision.schema.json"


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _errors(payload: dict) -> list:
    return list(Draft202012Validator(_json(SCHEMA)).iter_errors(payload))


def test_entity_resolution_schema_is_valid_draft_2020_12():
    Draft202012Validator.check_schema(_json(SCHEMA))


@pytest.mark.parametrize(
    "example_name",
    [
        "exact-variant.json",
        "high-confidence-model.json",
        "probable-variant.json",
        "ambiguous-variant.json",
        "unresolved-model.json",
    ],
)
def test_every_entity_resolution_state_has_a_valid_example(example_name: str):
    assert _errors(_json(CONTRACT_ROOT / "examples" / example_name)) == []


@pytest.mark.parametrize(
    "example_name",
    ["probable-variant.json", "ambiguous-variant.json", "unresolved-model.json"],
)
def test_non_promotable_states_reject_a_canonical_id(example_name: str):
    payload = _json(CONTRACT_ROOT / "examples" / example_name)
    payload["canonical_id"] = 99
    assert _errors(payload) != []


def test_exact_verified_requires_exact_gtin_evidence():
    payload = _json(CONTRACT_ROOT / "examples" / "exact-variant.json")
    payload["evidence"][0].update(signal="model", strength="strong")
    assert _errors(payload) != []


def test_high_confidence_requires_two_strong_non_exact_proofs():
    payload = _json(CONTRACT_ROOT / "examples" / "high-confidence-model.json")
    payload["evidence"] = payload["evidence"][:1]
    assert _errors(payload) != []

    payload = _json(CONTRACT_ROOT / "examples" / "high-confidence-model.json")
    payload["evidence"][0].update(signal="gtin", strength="exact")
    assert _errors(payload) != []


def test_favorable_states_reject_any_conflict():
    conflict = {
        "field": "storage",
        "reason_code": "variant_attribute_conflict",
        "evidence_raw_source_ids": [20, 21],
    }
    for example_name in ["exact-variant.json", "high-confidence-model.json"]:
        payload = _json(CONTRACT_ROOT / "examples" / example_name)
        payload["conflicts"] = [conflict]
        assert _errors(payload) != []


@pytest.mark.parametrize("signal", ["title", "image", "semantic_similarity"])
def test_weak_similarity_signals_can_never_be_exact_or_primary(signal: str):
    payload = _json(CONTRACT_ROOT / "examples" / "probable-variant.json")
    payload["evidence"][0].update(
        signal=signal,
        strength="exact",
        role="primary",
    )
    assert _errors(payload) != []


def test_ambiguous_requires_multiple_candidates_and_a_conflict():
    original = _json(CONTRACT_ROOT / "examples" / "ambiguous-variant.json")
    without_conflict = deepcopy(original)
    without_conflict["conflicts"] = []
    assert _errors(without_conflict) != []

    one_candidate = deepcopy(original)
    one_candidate["candidate_ids"] = [401]
    assert _errors(one_candidate) != []


def test_unresolved_cannot_keep_a_favorable_candidate():
    payload = _json(CONTRACT_ROOT / "examples" / "unresolved-model.json")
    payload["candidate_ids"] = [77]
    payload["confidence_score"] = 0.99
    assert _errors(payload) != []


@pytest.mark.parametrize(
    "example_name",
    ["probable-variant.json", "unresolved-model.json"],
)
def test_non_exact_states_cannot_silently_downgrade_exact_evidence(example_name: str):
    payload = _json(CONTRACT_ROOT / "examples" / example_name)
    payload["evidence"][0].update(signal="gtin", strength="exact")
    assert _errors(payload) != []


def test_promoted_examples_keep_the_canonical_id_in_the_candidate_set():
    for example_name in ["exact-variant.json", "high-confidence-model.json"]:
        payload = _json(CONTRACT_ROOT / "examples" / example_name)
        assert payload["canonical_id"] in payload["candidate_ids"]


def test_manifest_references_every_checked_artifact():
    manifest = _json(CONTRACT_ROOT / "manifest.json")
    assert manifest["public_reader_compatible"] is True
    assert manifest["false_merge_policy"] == "false_merge_is_worse_than_false_split"
    assert (CONTRACT_ROOT / manifest["artifacts"]["decision"]).is_file()
    assert {
        (CONTRACT_ROOT / path).name for path in manifest["examples"].values()
    } == {
        "exact-variant.json",
        "high-confidence-model.json",
        "probable-variant.json",
        "ambiguous-variant.json",
        "unresolved-model.json",
    }


def test_decision_requires_versioned_provenance():
    payload = _json(CONTRACT_ROOT / "examples" / "exact-variant.json")
    del payload["evidence"][0]["raw_source_record_id"]
    assert _errors(payload) != []
