"""Jeu de référence FILON v1 : invariants de catalogue multilingue et adversarial.

Les attentes `semantic_target` du JSON décrivent le prochain contrat du rôle
produit et des relations. Ce test verrouille ce que le moteur actuel sait
prouver aujourd'hui : rayon FILON et nature transactionnelle. Ainsi, la future
implémentation enrichit la connaissance sans réécrire ni masquer les décisions
fiables déjà publiées.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.services import taxonomy


_DATA_PATH = Path(__file__).parent / "data" / "golden_catalog_v1.json"
_GOLDEN = json.loads(_DATA_PATH.read_text(encoding="utf-8"))
_CASES = _GOLDEN["cases"]


class TestGoldenCatalogContract:
    def test_dataset_declares_the_safety_policy(self):
        assert _GOLDEN["version"] == "1.0.0"
        assert _GOLDEN["policy"]["unknown_first"] is True
        assert _GOLDEN["policy"]["false_merge_is_worse_than_false_split"] is True
        assert set(_GOLDEN["policy"]["languages"]) == {"fr", "nl", "en"}

    def test_case_ids_are_unique_and_semantic_targets_are_explicit(self):
        ids = [case["id"] for case in _CASES]
        assert len(ids) == len(set(ids))
        assert all(case.get("semantic_target") for case in _CASES)

    @pytest.mark.parametrize("case", _CASES, ids=[case["id"] for case in _CASES])
    def test_current_taxonomy_matches_the_verified_baseline(self, case):
        expected = case["expected_current"]
        category = taxonomy.classify(
            case.get("merchant_category"),
            case.get("name"),
            case.get("brand"),
            case.get("merchant_name"),
        )
        kind = taxonomy.classify_offer_kind(
            case.get("merchant_category"),
            case.get("name"),
            case.get("brand"),
            case.get("merchant_name"),
        )
        if "category" in expected:
            assert category == expected["category"]
        if "offer_kind" in expected:
            assert kind == expected["offer_kind"]

    def test_mention_and_product_are_distinct_in_the_phone_case_reference(self):
        case = next(c for c in _CASES if c["id"] == "phone-case-fr-compatible")
        assert case["semantic_target"]["product_role"] == "protective_case"
        assert case["semantic_target"]["mentioned_product"] == "Apple iPhone 16 Pro Max"
        assert case["semantic_target"]["mentioned_product"] not in case["semantic_target"]["product_role"]

    def test_accommodation_reference_cannot_be_evaluated_as_a_physical_product(self):
        case = next(c for c in _CASES if c["id"] == "accommodation-fr")
        assert case["expected_current"]["offer_kind"] == taxonomy.ACCOMMODATION
        assert case["semantic_target"]["must_not_be_compared_as"] == "physical_product"
