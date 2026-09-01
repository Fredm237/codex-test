"""Extracteurs Phase 3 Offer Truth, purs et fail-closed."""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from app.offer_truth.extraction import (
    EXTRACTOR_VERSION,
    OfferTruthExtractionError,
    extract_awin_offer_truth,
)


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "contracts" / "offer-truth" / "v1" / "offer-truth-snapshot.schema.json"
NOW = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)


def _snapshot(row: dict | None = None, **overrides):
    arguments = {
        "raw_source_record_id": 101,
        "source_ref": "42:AWIN-101",
        "observed_at": NOW - timedelta(hours=1),
        "evaluated_at": NOW,
        "offer_id": 201,
        "variant_id": 301,
        "merchant_id": 42,
        "merchant_status": "AFFILIATED",
        "relationship_type": "AFFILIATED",
        "seller_type": "direct",
    }
    arguments.update(overrides)
    return extract_awin_offer_truth(
        row or {"search_price": "1 249,90 €", "currency": "eur", "in_stock": "yes"},
        **arguments,
    )


def _schema_errors(payload: dict) -> list:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    return list(Draft202012Validator(schema).iter_errors(payload))


def test_verified_snapshot_is_exact_sourced_and_contract_valid():
    snapshot = _snapshot()
    assert _schema_errors(snapshot) == []
    assert snapshot["offer_status"] == "VERIFIED"
    assert snapshot["claims"]["price"]["value"] == {
        "amount_decimal": "1249.9",
        "currency": "EUR",
    }
    assert snapshot["claims"]["stock"]["value"] == "in_stock"
    assert snapshot["claims"]["shipping"]["state"] == "unknown"
    assert snapshot["claims"]["returns"]["state"] == "unknown"
    assert snapshot["claims"]["warranty"]["state"] == "unknown"
    assert snapshot["projection_version"] == EXTRACTOR_VERSION
    assert snapshot["reason_codes"][0] == "verified_core_truth"


@pytest.mark.parametrize("field", ["search_price", "in_stock"])
def test_missing_core_claim_never_receives_a_favorable_fallback(field: str):
    row = {"search_price": "99.90", "currency": "EUR", "in_stock": "yes"}
    row.pop(field)
    snapshot = _snapshot(row)
    claim = "price" if field == "search_price" else "stock"
    assert snapshot["claims"][claim] == {"state": "unknown", "value": None, "evidence": []}
    assert snapshot["offer_status"] == "PARTIAL"


def test_missing_price_currency_is_unknown_and_invalid_currency_is_invalid():
    missing = _snapshot({"search_price": "99.90", "in_stock": "yes"})
    invalid = _snapshot({"search_price": "99.90", "currency": "EURO", "in_stock": "yes"})
    assert missing["claims"]["price"]["state"] == "unknown"
    assert invalid["claims"]["price"]["state"] == "invalid"
    assert missing["claims"]["price"]["value"] is None
    assert invalid["claims"]["price"]["value"] is None


def test_shipping_requires_its_own_explicit_currency_and_zero_is_only_explicit():
    without_currency = _snapshot({
        "search_price": "99.90",
        "currency": "EUR",
        "in_stock": "yes",
        "shipping_cost": "0",
    })
    explicit = _snapshot({
        "search_price": "99.90",
        "currency": "EUR",
        "in_stock": "yes",
        "shipping_cost": "0",
        "shipping_currency": "EUR",
    })
    assert without_currency["claims"]["shipping"]["state"] == "unknown"
    assert without_currency["claims"]["shipping"]["value"] is None
    assert explicit["claims"]["shipping"]["value"] == {
        "amount_decimal": "0",
        "currency": "EUR",
    }


def test_returns_and_warranty_only_use_explicit_structured_fields():
    snapshot = _snapshot({
        "search_price": "99.90",
        "currency": "EUR",
        "in_stock": "yes",
        "returns_accepted": "yes",
        "return_period": "30",
        "warranty_months": "24",
    })
    assert snapshot["claims"]["returns"]["value"] == {"accepted": True, "period_days": 30}
    assert snapshot["claims"]["warranty"]["value"] == {
        "duration_months": 24,
        "description": None,
    }


def test_merchant_relationship_cannot_be_embellished():
    snapshot = _snapshot(relationship_type="DIRECT_PARTNER")
    assert snapshot["claims"]["merchant"]["state"] == "invalid"
    assert snapshot["claims"]["merchant"]["value"] is None
    assert snapshot["offer_status"] == "INVALID"
    assert "merchant_unknown" in snapshot["reason_codes"]


def test_stale_snapshot_retains_values_for_audit_but_is_not_current():
    snapshot = _snapshot(observed_at=NOW - timedelta(hours=73))
    assert _schema_errors(snapshot) == []
    assert snapshot["offer_status"] == "STALE"
    assert snapshot["claims"]["freshness"]["state"] == "stale"
    assert snapshot["claims"]["price"]["state"] == "stale"
    assert snapshot["claims"]["price"]["value"] is not None
    assert "observation_stale" in snapshot["reason_codes"]


def test_future_snapshot_discards_values_and_is_invalid():
    snapshot = _snapshot(observed_at=NOW + timedelta(seconds=1))
    assert _schema_errors(snapshot) == []
    assert snapshot["offer_status"] == "INVALID"
    assert snapshot["claims"]["freshness"]["state"] == "invalid_future"
    assert snapshot["claims"]["price"]["state"] == "invalid"
    assert snapshot["claims"]["price"]["value"] is None
    assert "future_observation" in snapshot["reason_codes"]


def test_unresolved_identity_is_quarantined_without_losing_claims():
    snapshot = _snapshot(variant_id=None)
    assert _schema_errors(snapshot) == []
    assert snapshot["offer_status"] == "QUARANTINED"
    assert snapshot["claims"]["price"]["state"] == "known"
    assert "identity_unresolved" in snapshot["reason_codes"]


def test_projection_is_deterministic_and_does_not_mutate_source():
    row = {"search_price": "99.900", "currency": "EUR", "in_stock": "pre-order"}
    original = deepcopy(row)
    first = _snapshot(row)
    second = _snapshot(row)
    assert first == second
    assert row == original
    assert first["claims"]["stock"]["value"] == "preorder"


@pytest.mark.parametrize(
    "overrides",
    [
        {"raw_source_record_id": 0},
        {"offer_id": 0},
        {"variant_id": 0},
        {"source_ref": ""},
        {"evaluated_at": "2026-09-01"},
        {"ttl_seconds": 0},
    ],
)
def test_invalid_structural_metadata_fails_closed(overrides):
    with pytest.raises(OfferTruthExtractionError):
        _snapshot(**overrides)
