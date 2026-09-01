"""Contrat Phase 5 Hybrid Retrieval, product-first et shadow-only."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_ROOT = ROOT / "contracts" / "hybrid-retrieval" / "v1"
SCHEMA = CONTRACT_ROOT / "hybrid-retrieval-run.schema.json"


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _errors(payload: dict) -> list:
    return list(Draft202012Validator(_json(SCHEMA)).iter_errors(payload))


def _example(name: str) -> dict:
    return _json(CONTRACT_ROOT / "examples" / name)


def test_hybrid_retrieval_schema_is_valid_draft_2020_12():
    Draft202012Validator.check_schema(_json(SCHEMA))


def test_all_synthetic_examples_validate():
    manifest = _json(CONTRACT_ROOT / "manifest.json")
    for relative_path in manifest["examples"]:
        assert _errors(_json(CONTRACT_ROOT / relative_path)) == []


def test_raw_query_cannot_be_persisted_or_marked_retained():
    payload = _example("exact-product.json")
    payload["query"]["raw_query"] = "synthetic secret-like query"
    assert _errors(payload) != []
    payload["query"].pop("raw_query")
    payload["query"]["raw_query_retained"] = True
    assert _errors(payload) != []


def test_no_match_cannot_invent_a_candidate():
    payload = _example("no-match.json")
    payload["candidates"] = deepcopy(_example("exact-product.json")["candidates"])
    assert _errors(payload) != []


def test_candidate_outcome_requires_at_least_one_candidate():
    payload = _example("exact-product.json")
    payload["candidates"] = []
    assert _errors(payload) != []


def test_resolved_entity_requires_entity_resolution_evidence():
    payload = _example("exact-product.json")
    payload["candidates"][0]["entity"]["evidence"][0]["evidence_type"] = "SEMANTIC_HIT"
    assert _errors(payload) != []


def test_semantic_only_candidate_stays_quarantined_and_unresolved():
    payload = _example("ambiguous.json")
    assert _errors(payload) == []
    payload["candidates"][0]["candidate_status"] = "ELIGIBLE_SHADOW"
    assert _errors(payload) != []


def test_unresolved_entity_cannot_keep_a_canonical_identifier():
    payload = _example("ambiguous.json")
    payload["candidates"][0]["entity"]["entity_id"] = 99
    assert _errors(payload) != []


def test_offer_ids_are_unique_inside_a_product_candidate():
    payload = _example("exact-product.json")
    payload["candidates"][0]["offer_ids"] = [1001, 1001]
    assert _errors(payload) != []


def test_numeric_confidence_and_decision_scores_are_not_accepted():
    payload = _example("exact-product.json")
    payload["candidates"][0]["confidence"] = 0.99
    payload["candidates"][0]["product_score"] = 91
    assert _errors(payload) != []


def test_manifest_freezes_identity_ranking_and_commercial_safety():
    manifest = _json(CONTRACT_ROOT / "manifest.json")
    assert manifest["status"] == "draft_for_shadow"
    assert manifest["public_reader_compatible"] is True
    assert manifest["raw_query_policy"] == (
        "digest_and_opaque_ref_only_never_persist_raw_query"
    )
    assert manifest["identity_policy"] == (
        "semantic_signal_never_resolves_entity_without_entity_resolution"
    )
    assert manifest["commercial_policy"] == (
        "affiliate_relationship_and_commission_never_affect_product_retrieval"
    )
    assert (CONTRACT_ROOT / manifest["artifact"]).is_file()


def test_contract_is_deterministic_under_deep_copy():
    payload = _example("exact-product.json")
    assert deepcopy(payload) == payload
    assert _errors(payload) == _errors(deepcopy(payload))
