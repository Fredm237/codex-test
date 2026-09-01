"""Extracteurs shadow Entity Resolution, sans fallback favorable."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json

import pytest
from jsonschema import Draft202012Validator

from app.product_graph.entity_signals import (
    EXTRACTOR_VERSION,
    TARGET_SIGNALS,
    EntitySignalExtractionError,
    project_entity_signals,
)


OBSERVED_AT = datetime(2026, 9, 1, 0, 0, tzinfo=timezone.utc)
ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "contracts" / "entity-resolution" / "v1" / "entity-resolution-signal-extraction.schema.json"


def _project(row: dict):
    return project_entity_signals(
        row,
        raw_source_record_id=42,
        source_type="awin_feed",
        source_ref="awin-feed:7",
        observed_at=OBSERVED_AT,
    )


def _signals(projection):
    return {signal.signal: signal for signal in projection.signals}


def test_current_awin_feed_keeps_missing_structured_identity_unknown():
    projection = _project(
        {
            "aw_product_id": "SKU-42",
            "brand_name": "Sony",
            "product_name": "Wireless headphones black 32GB",
            "merchant_image_url": "https://example.test/item.jpg",
            "merchant_category": "Audio > Headphones",
        }
    )
    signals = _signals(projection)
    assert tuple(signals) == TARGET_SIGNALS
    assert signals["brand"].status == "observed"
    assert signals["brand"].strength == "weak"
    assert signals["mpn"].status == "unknown"
    assert signals["model"].status == "unknown"
    assert signals["storage"].status == "candidate_only"
    assert signals["storage"].normalized_values == ("32GB",)
    assert signals["color"].normalized_values == ("black",)
    assert signals["title"].status == "candidate_only"
    assert signals["image"].status == "candidate_only"
    assert signals["taxonomy"].status == "candidate_only"
    assert projection.as_contract()["extractor_version"] == EXTRACTOR_VERSION


def test_structured_fields_become_versioned_strong_facts():
    signals = _signals(
        _project(
            {
                "brand_name": "Sony",
                "mpn": " wh1000xm5b ",
                "model_number": "WH-1000XM5",
                "storage_capacity": "128 GB",
                "color": "Black",
                "generation": "5th gen",
                "product_role": "primary_product",
            }
        )
    )
    assert signals["mpn"].normalized_values == ("WH1000XM5B",)
    for signal in ("mpn", "model", "storage", "color", "generation", "product_role"):
        assert signals[signal].status == "observed"
        assert signals[signal].strength == "strong"
        assert signals[signal].role == "primary"
        assert signals[signal].transformation_version == EXTRACTOR_VERSION


def test_title_never_invents_mpn_or_model_and_attributes_remain_candidate_only():
    signals = _signals(
        _project(
            {
                "product_name": "ACME XZ-900 Pro 16GB RAM 512GB SSD 55 inch black Gen 4",
            }
        )
    )
    assert signals["mpn"].status == "unknown"
    assert signals["model"].status == "unknown"
    assert signals["memory"].normalized_values == ("16GB",)
    assert signals["storage"].normalized_values == ("512GB",)
    assert signals["size"].normalized_values == ('55INCH',)
    assert signals["generation"].normalized_values == ("GEN 4",)
    assert all(
        signals[signal].status == "candidate_only"
        and signals[signal].strength == "weak"
        and signals[signal].role == "candidate_only"
        for signal in ("memory", "storage", "size", "color", "generation")
    )


def test_conflicting_structured_aliases_are_never_a_strong_fact():
    signal = _signals(_project({"model": "Phone 16", "model_number": "Phone 16 Pro"}))["model"]
    assert signal.status == "conflict"
    assert signal.normalized_values == ("phone 16", "phone 16 pro")
    assert signal.strength == "none"
    assert signal.role == "none"


def test_invalid_structured_value_is_fail_closed():
    signal = _signals(_project({"mpn": {"unsafe": "value"}}))["mpn"]
    assert signal.status == "invalid"
    assert signal.normalized_values == ()
    assert signal.reason_code == "invalid_signal"


def test_projection_matches_the_signal_contract():
    payload = _project(
        {
            "brand_name": "Example",
            "product_name": "Climate Pro 12000 BTU white",
            "merchant_category": "HVAC",
        }
    ).as_contract()
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    assert list(Draft202012Validator(schema).iter_errors(payload)) == []


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"raw_source_record_id": 0}, "raw_source_record_id"),
        ({"source_type": ""}, "source_type"),
        ({"source_ref": ""}, "source_ref"),
        ({"observed_at": datetime(2026, 9, 1)}, "offset"),
    ],
)
def test_projection_rejects_missing_or_ambiguous_provenance(kwargs, message):
    values = {
        "raw_source_record_id": 42,
        "source_type": "awin_feed",
        "source_ref": "awin-feed:7",
        "observed_at": OBSERVED_AT,
    }
    values.update(kwargs)
    with pytest.raises(EntitySignalExtractionError, match=message):
        project_entity_signals({}, **values)
