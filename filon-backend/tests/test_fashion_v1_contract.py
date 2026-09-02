import json
from datetime import UTC, datetime
from pathlib import Path

from jsonschema import validate

from app.intelligence.contracts import CoreOfferSnapshot
from app.intelligence.fashion import compose_outfit, parse_fashion_intent


def _schema():
    path = Path(__file__).parents[2] / "contracts" / "fashion" / "v1" / "response.schema.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_recommendation_and_abstention_follow_the_public_fashion_contract():
    offer = CoreOfferSnapshot(
        offer_id=1,
        catalog_product_id=1,
        name="Robe noire de soirée",
        brand=None,
        filon_category="Mode femme",
        filon_subcategory="Robes",
        offer_kind="physical_product",
        price=99.0,
        currency="EUR",
        availability="in_stock",
        image_url="https://images.example/robe.jpg",
        deep_link="https://merchant.example/robe",
        merchant_id=1,
        merchant_name="Synthetic merchant",
        merchant_region="BE",
        observed_at=datetime.now(UTC),
    )
    intent = parse_fashion_intent("Une robe noire de soirée sous 150 euros")

    recommendation = compose_outfit(intent, [offer])
    abstention = compose_outfit(intent, [])

    validate(recommendation, _schema())
    validate(abstention, _schema())
    assert recommendation["style_score"] is None
    assert recommendation["confidence_score"] is None
    assert abstention["confidence_band"] == "not_calibrated"
