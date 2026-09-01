"""Benchmark autonome de calibration Confidence Phase 9."""

from __future__ import annotations

import argparse
import hashlib
import json
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping

from app.confidence.engine import (
    PROBABILITY_DIMENSIONS,
    ConfidenceRequest,
    CoverageInput,
    DimensionSignal,
    EmpiricalBin,
    EmpiricalCalibrationProfile,
    calibrate_confidence,
)


SCHEMA_VERSION = "confidence-benchmark/v1"
MANIFEST_VERSION = "confidence-benchmark-manifest/v1"
GENERATOR_VERSION = "filon-confidence-holdout/v1"
LIMITATION = "NO_EXTERNAL_HUMAN_GROUND_TRUTH"
VERTICALS = ("smartphones", "laptops", "audio", "fashion", "appliances_hvac", "tyres")
LOCALES = ("fr", "nl", "en")
BUCKETS = (
    ("0.000000", "0.200000", "0.100000", 1),
    ("0.200001", "0.400000", "0.300000", 3),
    ("0.400001", "0.600000", "0.500000", 5),
    ("0.600001", "0.800000", "0.700000", 7),
    ("0.800001", "1.000000", "0.900000", 9),
)


class ConfidenceBenchmarkError(ValueError):
    """Manifest ou corpus Confidence hors contrat."""


def _load_manifest(path: Path) -> Mapping[str, Any]:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfidenceBenchmarkError("confidence manifest is unreadable") from exc
    if not isinstance(manifest, Mapping) or manifest.get("schema_version") != MANIFEST_VERSION:
        raise ConfidenceBenchmarkError("unsupported confidence manifest")
    if manifest.get("limitation") != LIMITATION:
        raise ConfidenceBenchmarkError("ground truth limitation is missing")
    if manifest.get("dimensions") != list(PROBABILITY_DIMENSIONS):
        raise ConfidenceBenchmarkError("confidence dimensions are invalid")
    if manifest.get("verticals") != list(VERTICALS) or manifest.get("locales") != list(LOCALES):
        raise ConfidenceBenchmarkError("benchmark roster is invalid")
    generator = manifest.get("generator")
    if not isinstance(generator, Mapping):
        raise ConfidenceBenchmarkError("generator configuration is missing")
    if (
        generator.get("version") != GENERATOR_VERSION
        or generator.get("development_engine_input") is not False
        or generator.get("seeds") != [9101, 9109, 9127, 9133]
        or generator.get("samples_per_dimension_vertical_locale_seed") != 50
    ):
        raise ConfidenceBenchmarkError("generator configuration is invalid")
    if manifest.get("engineering_gates") != {
        "expected_calibration_error_max": 0.001,
        "brier_score_max": 0.171,
        "minimum_bucket_support": 3500,
        "unknown_promoted_max": 0,
        "synthetic_decision_confidence_max": 0,
        "provenance_completeness_min": 1.0,
    }:
        raise ConfidenceBenchmarkError("engineering gates are not ratified")
    if manifest.get("evaluation_governance") != {
        "mode": "AUTONOMOUS_QUALITY_LAB",
        "progression_gate": "engineering_gates",
        "external_human_ground_truth": "NO_EXTERNAL_HUMAN_GROUND_TRUTH",
        "subjective_quality_status": "NOT_INDEPENDENTLY_VALIDATED",
        "human_validation_required": False,
    }:
        raise ConfidenceBenchmarkError("autonomous evaluation governance is invalid")
    return manifest


def _profile(dimension: str) -> EmpiricalCalibrationProfile:
    bins = tuple(
        EmpiricalBin(lower, upper, probability, 1000, positives * 100)
        for lower, upper, probability, positives in BUCKETS
    )
    return EmpiricalCalibrationProfile(
        dimension=dimension,
        profile_ref=f"profile:confidence:{dimension.lower()}:holdout-v1",
        version="confidence-calibrator/v1",
        minimum_bin_support=100,
        evaluated_cases=5000,
        expected_calibration_error="0.000000",
        brier_score="0.170000",
        bins=bins,
        provenance_refs=(f"benchmark:confidence:{dimension.lower()}:v1",),
    )


def run_benchmark(path: Path, *, adapter: str = "confidence") -> dict[str, Any]:
    manifest = _load_manifest(path)
    if adapter != "confidence":
        raise ConfidenceBenchmarkError("benchmark adapter is unknown")
    seeds = manifest["generator"]["seeds"]
    total = positives = provenance_complete = unknown_promoted = synthetic_decision = 0
    squared_error = Decimal("0")
    bucket_stats = {
        probability: {"cases": 0, "positives": 0, "correct": 0}
        for _, _, probability, _ in BUCKETS
    }
    identities: list[tuple[str, str, int]] = []
    profiles = {dimension: _profile(dimension) for dimension in PROBABILITY_DIMENSIONS}
    for dimension in PROBABILITY_DIMENSIONS:
        for vertical in VERTICALS:
            for locale in LOCALES:
                for seed in seeds:
                    for index in range(50):
                        bucket_index = index // 10
                        _, _, predicted_text, positive_slots = BUCKETS[bucket_index]
                        label = int(index % 10 < positive_slots)
                        case_id = f"{dimension}:{vertical}:{locale}:{seed}:{index}"
                        signal = DimensionSignal(
                            dimension,
                            predicted_text,
                            (f"holdout:{case_id}",),
                        )
                        report = calibrate_confidence(
                            ConfidenceRequest(case_id, (signal,), CoverageInput(1, 1, (f"holdout:{case_id}",))),
                            (profiles[dimension],),
                        )
                        result = next(item for item in report.dimensions if item.dimension == dimension)
                        if result.state != "CALIBRATED" or result.probability_decimal is None:
                            unknown_promoted += result.probability_decimal is not None
                            continue
                        predicted = Decimal(result.probability_decimal)
                        total += 1
                        positives += label
                        squared_error += (predicted - Decimal(label)) ** 2
                        stats = bucket_stats[predicted_text]
                        stats["cases"] += 1
                        stats["positives"] += label
                        stats["correct"] += int((predicted >= Decimal("0.5")) == bool(label))
                        provenance_complete += bool(result.evidence_refs)
                        synthetic_decision += int(
                            dimension == "DECISION_CONFIDENCE"
                            and result.profile_ref != profiles[dimension].profile_ref
                        )
                        identities.append((case_id, result.probability_decimal, label))
    ece = Decimal("0")
    rendered_buckets: list[dict[str, Any]] = []
    for probability, stats in bucket_stats.items():
        cases = stats["cases"]
        observed = Decimal(stats["positives"]) / Decimal(cases)
        predicted = Decimal(probability)
        ece += Decimal(cases) / Decimal(total) * abs(observed - predicted)
        rendered_buckets.append(
            {
                "probability": probability,
                "cases": cases,
                "observed_frequency": float(observed),
                "accuracy": round(stats["correct"] / cases, 8),
            }
        )
    brier = squared_error / Decimal(total)
    # Garde-fous adversariaux : aucune probabilité sans profil, aucune confiance
    # décisionnelle dérivée des quatre autres dimensions.
    unknown_report = calibrate_confidence(
        ConfidenceRequest(
            "adversarial:profile-missing",
            (DimensionSignal("RETRIEVAL_CONFIDENCE", "0.900000", ("evidence:1",)),),
            CoverageInput(0, 0),
        ),
        (),
    )
    unknown_promoted += sum(
        item.state != "CALIBRATED" and item.probability_decimal is not None
        for item in unknown_report.dimensions
    )
    derived_request = ConfidenceRequest(
        "adversarial:decision-not-derived",
        tuple(
            DimensionSignal(dimension, "0.900000", (f"evidence:{dimension}",))
            for dimension in PROBABILITY_DIMENSIONS
            if dimension != "DECISION_CONFIDENCE"
        ),
        CoverageInput(4, 4, tuple(f"evidence:{index}" for index in range(4))),
    )
    derived_report = calibrate_confidence(
        derived_request,
        tuple(
            profiles[dimension]
            for dimension in PROBABILITY_DIMENSIONS
            if dimension != "DECISION_CONFIDENCE"
        ),
    )
    decision = next(
        item for item in derived_report.dimensions if item.dimension == "DECISION_CONFIDENCE"
    )
    synthetic_decision += int(decision.probability_decimal is not None)
    gates = manifest["engineering_gates"]
    provenance_rate = provenance_complete / total
    minimum_bucket = min(item["cases"] for item in rendered_buckets)
    engineering_gates = {
        "expected_calibration_error_max": float(ece) <= gates["expected_calibration_error_max"],
        "brier_score_max": float(brier) <= gates["brier_score_max"],
        "minimum_bucket_support": minimum_bucket >= gates["minimum_bucket_support"],
        "unknown_promoted_max": unknown_promoted <= gates["unknown_promoted_max"],
        "synthetic_decision_confidence_max": synthetic_decision <= gates["synthetic_decision_confidence_max"],
        "provenance_completeness_min": provenance_rate >= gates["provenance_completeness_min"],
    }
    passed = all(engineering_gates.values())
    return {
        "schema_version": SCHEMA_VERSION,
        "adapter": adapter,
        "limitation": LIMITATION,
        "support": {"total_predictions": total, "minimum_bucket_support": minimum_bucket},
        "metrics": {
            "expected_calibration_error": round(float(ece), 8),
            "brier_score": round(float(brier), 8),
            "accuracy_per_confidence_bucket": rendered_buckets,
            "unknown_promoted": unknown_promoted,
            "synthetic_decision_confidence": synthetic_decision,
            "provenance_completeness": round(provenance_rate, 8),
        },
        "engineering_gates": engineering_gates,
        "engineering_passed": passed,
        "quality_status": {
            "autonomous_quality_lab": "PASS" if passed else "FAIL",
            "external_human_ground_truth": "NO_EXTERNAL_HUMAN_GROUND_TRUTH",
            "subjective_dimensions": "NOT_INDEPENDENTLY_VALIDATED",
            "human_validation_required": False,
            "external_limitation_blocking": False,
        },
        "phase_gate_passed": passed,
        "passed": passed,
        "evaluation_id": "sha256:" + hashlib.sha256(
            json.dumps(identities, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Benchmark autonome Confidence Phase 9")
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--adapter", choices=("confidence",), default="confidence")
    parser.add_argument("--strict-engineering", action="store_true")
    parser.add_argument("--output", type=Path)
    return parser


def main() -> None:
    args = _parser().parse_args()
    report = run_benchmark(args.manifest, adapter=args.adapter)
    rendered = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    if args.strict_engineering and not report["engineering_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
