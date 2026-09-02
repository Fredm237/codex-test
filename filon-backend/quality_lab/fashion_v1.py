"""Engineering benchmark for Fashion v1 without subjective ground truth."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from app.intelligence.contracts import CoreOfferSnapshot
from app.intelligence.fashion import compose_outfit, parse_fashion_intent


class FashionBenchmarkError(ValueError):
    """The Fashion benchmark manifest is outside its ratified contract."""


def _snapshot(raw: dict[str, Any], now: datetime) -> CoreOfferSnapshot:
    return CoreOfferSnapshot(
        offer_id=int(raw["id"]),
        catalog_product_id=None,
        name=str(raw["name"]),
        brand=None,
        filon_category=str(raw["category"]),
        filon_subcategory=str(raw["subcategory"]),
        offer_kind="physical_product",
        price=float(raw["price"]),
        currency=str(raw["currency"]),
        availability=str(raw["availability"]),  # type: ignore[arg-type]
        image_url="https://images.example/item.jpg",
        deep_link="https://merchant.example/item",
        merchant_id=1,
        merchant_name="Synthetic merchant",
        merchant_region="BE",
        observed_at=now - timedelta(hours=float(raw["age_hours"])),
    )


def evaluate_manifest(path: Path) -> dict[str, Any]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != "fashion-v1-benchmark-manifest/v1":
        raise FashionBenchmarkError("unsupported Fashion benchmark manifest")
    if manifest.get("limitation") != "NO_EXTERNAL_HUMAN_GROUND_TRUTH":
        raise FashionBenchmarkError("external human ground-truth limitation is missing")
    if manifest.get("development_engine_input") is not False:
        raise FashionBenchmarkError("benchmark cases must be independent from engine development")
    cases = manifest.get("cases")
    if not isinstance(cases, list) or len(cases) < 10:
        raise FashionBenchmarkError("at least ten Fashion cases are required")

    now = datetime.now(UTC)
    decision_passes = 0
    identity_passes = 0
    false_recommendations = 0
    uncalibrated_passes = 0
    outcomes: list[dict[str, Any]] = []
    for case in cases:
        expected_decision = case["expected_decision"]
        result = compose_outfit(
            parse_fashion_intent(case["request"]),
            [_snapshot(raw, now) for raw in case["offers"]],
        )
        selected = [item["offer_id"] for item in result["items"]]
        decision_ok = result["decision"] == expected_decision
        identity_ok = selected == case["expected_offer_ids"]
        uncalibrated_ok = (
            result["style_score"] is None
            and result["confidence_score"] is None
            and result["confidence_band"] == "not_calibrated"
            and "confidence_not_calibrated" in result["unknowns"]
        )
        decision_passes += int(decision_ok)
        identity_passes += int(identity_ok)
        uncalibrated_passes += int(uncalibrated_ok)
        false_recommendations += int(result["decision"] == "recommend" and expected_decision == "abstain")
        outcomes.append({
            "case_id": case["id"],
            "decision": result["decision"],
            "selected_offer_ids": selected,
            "passed": decision_ok and identity_ok and uncalibrated_ok,
        })

    total = len(cases)
    metrics = {
        "total_cases": total,
        "decision_accuracy": decision_passes / total,
        "selected_identity_accuracy": identity_passes / total,
        "false_recommendations": false_recommendations,
        "uncalibrated_output_completeness": uncalibrated_passes / total,
    }
    gates = manifest["engineering_gates"]
    passed = (
        metrics["decision_accuracy"] >= gates["decision_accuracy_min"]
        and metrics["selected_identity_accuracy"] >= gates["selected_identity_accuracy_min"]
        and metrics["false_recommendations"] <= gates["false_recommendations_max"]
        and metrics["uncalibrated_output_completeness"] >= gates["uncalibrated_output_completeness_min"]
    )
    return {
        "benchmark": "fashion-v1",
        "status": "PASS" if passed else "FAIL",
        "limitation": manifest["limitation"],
        "metrics": metrics,
        "outcomes": outcomes,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--strict-engineering", action="store_true")
    args = parser.parse_args()
    report = evaluate_manifest(args.manifest)
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(f"{rendered}\n", encoding="utf-8")
    else:
        print(rendered)
    return 1 if args.strict_engineering and report["status"] != "PASS" else 0


if __name__ == "__main__":
    raise SystemExit(main())
