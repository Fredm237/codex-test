"""Régressions du pilote de compréhension rôle/relations, ancrées dans le golden dataset."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.services import product_role as roles


_DATA_PATH = Path(__file__).parent / "data" / "golden_catalog_v1.json"
_CASES = json.loads(_DATA_PATH.read_text(encoding="utf-8"))["cases"]


def _understanding(case: dict) -> dict:
    return roles.understand_offer(
        name=case.get("name"),
        merchant_category=case.get("merchant_category"),
        brand=case.get("brand"),
        offer_kind=case.get("expected_current", {}).get("offer_kind"),
    )


class TestProductRoleGoldenPilot:
    @pytest.mark.parametrize(
        "case",
        _CASES,
        ids=[case["id"] for case in _CASES],
    )
    def test_role_contract_for_the_pilot_scope(self, case):
        target = case["semantic_target"]
        actual = _understanding(case)
        if "product_role" in target:
            assert actual["product_role"] == target["product_role"]

    @pytest.mark.parametrize(
        "case_id",
        ["phone-case-fr-compatible", "screen-protector-en", "printer-ink-compatible-en", "dyson-battery-replacement-en"],
    )
    def test_compatibility_target_remains_a_textual_relation_not_a_false_product_link(self, case_id):
        case = next(c for c in _CASES if c["id"] == case_id)
        actual = _understanding(case)
        assert actual["relationships"]
        relation = actual["relationships"][0]
        assert relation["type"] == case["semantic_target"]["relation"]
        assert relation["target_text"] == case["semantic_target"]["mentioned_product"]
        assert "canonical_product_id" not in relation
        assert relation["state"] == "observed"

    def test_bundle_keeps_the_included_controller_quantity(self):
        case = next(c for c in _CASES if c["id"] == "gaming-bundle-en")
        actual = _understanding(case)
        assert actual["product_role"] == roles.BUNDLE
        assert actual["components"] == [{"type": "controller", "quantity": 2, "state": "observed"}]

    def test_storage_and_condition_are_independent_observed_attributes(self):
        case = next(c for c in _CASES if c["id"] == "phone-main-product-storage")
        actual = _understanding(case)
        assert actual["attributes"] == {"storage": "256GB", "condition": "refurbished"}

    def test_contextual_accommodation_is_a_service_not_a_comparable_product(self):
        case = next(c for c in _CASES if c["id"] == "accommodation-fr")
        actual = _understanding(case)
        assert actual["product_role"] == roles.SERVICE
        assert actual["confidence"] == "high"

    def test_empty_name_is_unknown_with_an_explicit_missing_evidence(self):
        actual = roles.understand_offer(name=None, merchant_category=None)
        assert actual["product_role"] == roles.UNKNOWN
        assert actual["missing"] == ["product_name"]
