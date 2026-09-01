"""Contrat Phase 3 Offer Truth, shadow-only et fail-closed."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_ROOT = ROOT / "contracts" / "offer-truth" / "v1"
SCHEMA = CONTRACT_ROOT / "offer-truth-snapshot.schema.json"


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _errors(payload: dict) -> list:
    return list(Draft202012Validator(_json(SCHEMA)).iter_errors(payload))


def _example(name: str) -> dict:
    return _json(CONTRACT_ROOT / "examples" / name)


def test_offer_truth_schema_is_valid_draft_2020_12():
    Draft202012Validator.check_schema(_json(SCHEMA))


@pytest.mark.parametrize(
    "example_name",
    ["verified-offer.json", "partial-offer.json", "stale-offer.json"],
)
def test_offer_truth_examples_validate(example_name: str):
    assert _errors(_example(example_name)) == []


@pytest.mark.parametrize("claim", ["price", "stock", "merchant"])
def test_verified_offer_rejects_unknown_core_truth(claim: str):
    payload = _example("verified-offer.json")
    payload["claims"][claim] = {"state": "unknown", "value": None, "evidence": []}
    assert _errors(payload) != []


def test_verified_offer_requires_fresh_observation():
    payload = _example("verified-offer.json")
    payload["claims"]["freshness"]["state"] = "stale"
    assert _errors(payload) != []


@pytest.mark.parametrize("claim", ["shipping", "returns", "warranty"])
def test_verified_offer_may_report_ancillary_truth_as_unknown(claim: str):
    payload = _example("verified-offer.json")
    assert payload["claims"][claim] == {
        "state": "unknown",
        "value": None,
        "evidence": [],
    }
    assert _errors(payload) == []


@pytest.mark.parametrize("claim", ["price", "shipping"])
def test_unknown_money_cannot_become_zero_or_free(claim: str):
    payload = _example("partial-offer.json")
    payload["claims"][claim]["value"] = {
        "amount_decimal": "0",
        "currency": "EUR",
    }
    assert _errors(payload) != []


def test_unknown_stock_cannot_default_to_available():
    payload = _example("partial-offer.json")
    payload["claims"]["stock"]["value"] = "in_stock"
    assert _errors(payload) != []


@pytest.mark.parametrize("amount", ["-1", "1e3", "01.00", "1.1234567", 12.5])
def test_money_requires_bounded_nonnegative_decimal_string(amount):
    payload = _example("verified-offer.json")
    payload["claims"]["price"]["value"]["amount_decimal"] = amount
    assert _errors(payload) != []


@pytest.mark.parametrize("currency", ["eur", "EU", "EURO", "12A"])
def test_money_requires_explicit_iso_shaped_currency(currency: str):
    payload = _example("verified-offer.json")
    payload["claims"]["price"]["value"]["currency"] = currency
    assert _errors(payload) != []


@pytest.mark.parametrize("claim", ["price", "stock", "merchant", "freshness"])
def test_known_core_truth_requires_provenance(claim: str):
    payload = _example("verified-offer.json")
    payload["claims"][claim]["evidence"] = []
    assert _errors(payload) != []


def test_evidence_requires_versioned_transformation_and_raw_source():
    payload = _example("verified-offer.json")
    evidence = payload["claims"]["price"]["evidence"][0]
    del evidence["raw_source_record_id"]
    del evidence["transformation_version"]
    assert _errors(payload) != []


def test_numeric_confidence_is_not_part_of_offer_truth_contract():
    payload = _example("verified-offer.json")
    payload["claims"]["price"]["evidence"][0]["confidence"] = 0.99
    assert _errors(payload) != []


def test_stale_offer_keeps_auditable_value_but_cannot_be_verified():
    payload = _example("stale-offer.json")
    assert _errors(payload) == []
    payload["offer_status"] = "VERIFIED"
    assert _errors(payload) != []


def test_quarantine_requires_unresolved_identity_and_reason():
    payload = _example("partial-offer.json")
    payload.update(
        offer_status="QUARANTINED",
        variant_id=None,
        reason_codes=["identity_unresolved"],
    )
    assert _errors(payload) == []

    promoted = deepcopy(payload)
    promoted["variant_id"] = 302
    assert _errors(promoted) != []


def test_examples_keep_top_level_and_claim_merchant_identity_equal():
    for name in ["verified-offer.json", "partial-offer.json", "stale-offer.json"]:
        payload = _example(name)
        assert payload["merchant_id"] == payload["claims"]["merchant"]["value"]["merchant_id"]


def test_manifest_freezes_fail_closed_policies_and_artifacts():
    manifest = _json(CONTRACT_ROOT / "manifest.json")
    assert manifest == {
        "contract_version": "1.0.0",
        "status": "draft_for_shadow",
        "opened_at": "2026-09-01",
        "public_reader_compatible": True,
        "unknown_policy": "missing_never_becomes_zero_free_available_or_favorable",
        "money_policy": "decimal_string_and_explicit_iso_currency_are_atomic",
        "confidence_policy": "no_numeric_confidence_without_external_calibration",
        "freshness_policy": "stale_and_future_observations_are_never_current_truth",
        "artifact": "offer-truth-snapshot.schema.json",
        "examples": {
            "verified": "examples/verified-offer.json",
            "partial": "examples/partial-offer.json",
            "stale": "examples/stale-offer.json",
        },
    }
    assert (CONTRACT_ROOT / manifest["artifact"]).is_file()
    for relative in manifest["examples"].values():
        assert (CONTRACT_ROOT / relative).is_file()
