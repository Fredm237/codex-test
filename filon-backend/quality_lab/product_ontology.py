"""Benchmark autonome Phase 4 pour taxonomie, rôles et relations.

Le corpus est synthétique et déterministe. Il ratifie les budgets fail-closed
avant l'extracteur Product Ontology ; il ne prétend pas constituer une vérité
humaine externe sur le catalogue réel.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from app.services import product_role as legacy_roles
from app.product_ontology.extraction import EXTRACTOR_VERSION, extract_product_ontology

from .integrity import atomic_write_text, canonical_json


SCHEMA_VERSION = "product-ontology-benchmark/v1"
MANIFEST_VERSION = "product-ontology-benchmark-manifest/v1"
GENERATOR_VERSION = "filon-product-ontology-holdout/v2"
LIMITATION = "NO_EXTERNAL_HUMAN_GROUND_TRUTH"
LEGACY_VERSION = legacy_roles.VERSION

ROLES = (
    "PRIMARY_PRODUCT",
    "ACCESSORY",
    "REPLACEMENT_PART",
    "CONSUMABLE",
    "SERVICE",
    "DIGITAL_CONTENT",
    "ACCOMMODATION",
    "BUNDLE",
    "UNKNOWN",
)

VERTICALS = (
    "smartphones",
    "fashion",
    "tyres",
    "appliances_hvac",
    "hospitality",
    "digital",
)


class ProductOntologyBenchmarkError(ValueError):
    """Entrée benchmark invalide : l'évaluation échoue fermée."""


@dataclass(frozen=True)
class BenchmarkCase:
    case_id: str
    vertical: str
    kind: str
    payload: Mapping[str, Any]
    expected_role: str
    expected_relationship_state: str
    truth_basis: str


@dataclass(frozen=True)
class Prediction:
    role: str
    relationship_state: str


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    vertical: str
    kind: str
    expected_role: str
    actual_role: str
    expected_relationship_state: str
    actual_relationship_state: str
    role_passed: bool
    relationship_passed: bool
    truth_basis: str


def _wilson(successes: int, total: int, *, z: float = 1.959963984540054) -> tuple[float, float]:
    if total <= 0:
        raise ProductOntologyBenchmarkError("metric denominator must be positive")
    probability = successes / total
    denominator = 1 + z * z / total
    center = (probability + z * z / (2 * total)) / denominator
    margin = z * math.sqrt(
        probability * (1 - probability) / total + z * z / (4 * total * total)
    ) / denominator
    return max(0.0, center - margin), min(1.0, center + margin)


def _metric(successes: int, total: int) -> dict[str, Any]:
    lower, upper = _wilson(successes, total)
    return {
        "cases": total,
        "successes": successes,
        "rate": round(successes / total, 8),
        "ci95_lower": round(lower, 8),
        "ci95_upper": round(upper, 8),
    }


def _event_metric(events: int, total: int, name: str) -> dict[str, Any]:
    lower, upper = _wilson(events, total)
    return {
        "cases": total,
        name: events,
        "rate": round(events / total, 8),
        "ci95_lower": round(lower, 8),
        "ci95_upper": round(upper, 8),
    }


def _load_json(path: Path, message: str) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProductOntologyBenchmarkError(message) from exc
    if not isinstance(value, Mapping):
        raise ProductOntologyBenchmarkError(message)
    return value


def _load_manifest(path: Path) -> Mapping[str, Any]:
    manifest = _load_json(path, "product ontology manifest is unreadable")
    if manifest.get("schema_version") != MANIFEST_VERSION:
        raise ProductOntologyBenchmarkError("unsupported product ontology manifest")
    if manifest.get("limitation") != LIMITATION:
        raise ProductOntologyBenchmarkError("human-ground-truth limitation is missing")
    if manifest.get("roles") != list(ROLES):
        raise ProductOntologyBenchmarkError("role roster is invalid")
    if manifest.get("verticals") != list(VERTICALS):
        raise ProductOntologyBenchmarkError("vertical roster is invalid")
    if manifest.get("unknown_policy") != "unknown_never_defaults_to_primary_product":
        raise ProductOntologyBenchmarkError("unknown policy is invalid")
    if manifest.get("relationship_policy") != "observed_text_never_becomes_canonical":
        raise ProductOntologyBenchmarkError("relationship policy is invalid")

    generator = manifest.get("generator")
    if not isinstance(generator, Mapping):
        raise ProductOntologyBenchmarkError("generator configuration is missing")
    seeds = generator.get("seeds")
    samples = generator.get("samples_per_vertical_seed")
    if (
        generator.get("version") != GENERATOR_VERSION
        or generator.get("development_engine_input") is not False
        or not isinstance(seeds, list)
        or len(seeds) < 3
        or any(isinstance(seed, bool) or not isinstance(seed, int) for seed in seeds)
        or isinstance(samples, bool)
        or not isinstance(samples, int)
        or not 64 <= samples <= 1_000
    ):
        raise ProductOntologyBenchmarkError("generator configuration is invalid")

    required_gates = {
        "known_role_accuracy_ci95_lower_min",
        "unknown_abstention_accuracy_ci95_lower_min",
        "false_primary_product_rate_ci95_upper_max",
        "canonical_relation_false_promotion_rate_ci95_upper_max",
        "blocking_failures_max",
    }
    gates = manifest.get("gates")
    if not isinstance(gates, Mapping) or set(gates) != required_gates:
        raise ProductOntologyBenchmarkError("benchmark gates are invalid")
    for key in required_gates - {"blocking_failures_max"}:
        value = gates[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= float(value) <= 1:
            raise ProductOntologyBenchmarkError("benchmark threshold is invalid")
    if gates["blocking_failures_max"] != 0:
        raise ProductOntologyBenchmarkError("blocking failure budget must remain zero")
    if float(gates["false_primary_product_rate_ci95_upper_max"]) > 0.005:
        raise ProductOntologyBenchmarkError("false primary product target cannot exceed 0.5 percent")
    if float(gates["canonical_relation_false_promotion_rate_ci95_upper_max"]) > 0.005:
        raise ProductOntologyBenchmarkError("false canonical relation target cannot exceed 0.5 percent")

    expected_support = {
        "known_role_cases": 3_000,
        "primary_negative_cases": 3_000,
        "unknown_cases": 3_000,
        "observed_relation_cases": 3_000,
    }
    if manifest.get("minimum_statistical_support") != expected_support:
        raise ProductOntologyBenchmarkError("minimum statistical support is invalid")
    regression = manifest.get("regression_ground_truth")
    if not isinstance(regression, str) or Path(regression).name != regression:
        raise ProductOntologyBenchmarkError("regression path is invalid")
    return manifest


def _surfaces(vertical: str, index: int) -> tuple[str, str]:
    values = {
        "smartphones": ("Example Phone", "mobile device"),
        "fashion": ("Example Jacket", "garment"),
        "tyres": ("Example Road tyre 205/55R16", "vehicle tyre"),
        "appliances_hvac": ("Example Climate air conditioner 9000 BTU", "air conditioner"),
        "hospitality": ("Example Coast travel guide", "holiday stay"),
        "digital": ("Example Studio laptop", "software title"),
    }
    model, category = values[vertical]
    return f"{model} {index}", category


def _known_role_payload(role: str, model: str, merchant_category: str) -> Mapping[str, Any]:
    if role == "PRIMARY_PRODUCT":
        return {"name": model, "merchant_category": merchant_category, "offer_kind": "physical_product"}
    if role == "ACCESSORY":
        return {"name": f"Protective case for {model}", "merchant_category": merchant_category, "offer_kind": "physical_product"}
    if role == "REPLACEMENT_PART":
        return {"name": f"Replacement screen for {model}", "merchant_category": merchant_category, "offer_kind": "physical_product"}
    if role == "CONSUMABLE":
        return {"name": f"Ink cartridge compatible with {model}", "merchant_category": merchant_category, "offer_kind": "physical_product"}
    if role == "SERVICE":
        return {"name": f"Installation service for {model}", "merchant_category": "services", "offer_kind": "service"}
    if role == "DIGITAL_CONTENT":
        return {"name": f"Software licence download {model}", "merchant_category": "software", "offer_kind": "digital_content"}
    if role == "ACCOMMODATION":
        return {"name": f"Holiday apartment {model}", "merchant_category": "holiday homes", "offer_kind": "accommodation"}
    if role == "BUNDLE":
        return {"name": f"Bundle {model} with 2 controllers", "merchant_category": merchant_category, "offer_kind": "physical_product"}
    raise ProductOntologyBenchmarkError("known role generator received UNKNOWN")


def _generated_cases(*, seed: int, samples: int) -> list[BenchmarkCase]:
    cases: list[BenchmarkCase] = []
    known_roles = ROLES[:-1]
    for vertical_index, vertical in enumerate(VERTICALS):
        for index in range(samples):
            model, merchant_category = _surfaces(vertical, seed % 10_000 + index)
            role = known_roles[(index + vertical_index + seed) % len(known_roles)]
            role_relationship = (
                "observed_text"
                if role in {"ACCESSORY", "REPLACEMENT_PART", "CONSUMABLE"}
                else "none"
            )
            prefix = f"holdout:{seed}:{vertical}:{index}"
            cases.extend(
                [
                    BenchmarkCase(
                        f"{prefix}:known-role",
                        vertical,
                        "known_role",
                        _known_role_payload(role, model, merchant_category),
                        role,
                        role_relationship,
                        "SYNTHETIC_EXPLICIT_PRODUCT_FORM",
                    ),
                    BenchmarkCase(
                        f"{prefix}:primary-negative",
                        vertical,
                        "primary_negative",
                        {
                            "name": f"Compatible with {model}",
                            "merchant_category": merchant_category,
                            "offer_kind": "physical_product",
                        },
                        "UNKNOWN",
                        "observed_text",
                        "NO_POSITIVE_SOLD_OBJECT_SIGNAL",
                    ),
                    BenchmarkCase(
                        f"{prefix}:unknown",
                        vertical,
                        "unknown",
                        {"name": None, "merchant_category": None, "offer_kind": None},
                        "UNKNOWN",
                        "none",
                        "MISSING_PRODUCT_SURFACE",
                    ),
                    BenchmarkCase(
                        f"{prefix}:observed-relation",
                        vertical,
                        "observed_relation",
                        {
                            "name": f"Protective case compatible with {model}",
                            "merchant_category": merchant_category,
                            "offer_kind": "physical_product",
                        },
                        "ACCESSORY",
                        "observed_text",
                        "TEXT_RELATION_WITHOUT_CANONICAL_TARGET",
                    ),
                ]
            )
    return cases


def _regression_cases(manifest_path: Path, manifest: Mapping[str, Any]) -> tuple[list[BenchmarkCase], Mapping[str, Any]]:
    path = manifest_path.parent / str(manifest["regression_ground_truth"])
    payload = _load_json(path, "product ontology regressions are unreadable")
    if (
        payload.get("schema_version") != "product-ontology-regressions/v1"
        or payload.get("truth_basis") != "REGRESSION_GROUND_TRUTH"
        or payload.get("limitation") != LIMITATION
        or not isinstance(payload.get("cases"), list)
    ):
        raise ProductOntologyBenchmarkError("product ontology regressions are invalid")
    cases: list[BenchmarkCase] = []
    identifiers: set[str] = set()
    allowed_kinds = {"known_role", "primary_negative", "unknown", "observed_relation"}
    for raw in payload["cases"]:
        if not isinstance(raw, Mapping):
            raise ProductOntologyBenchmarkError("regression case is invalid")
        case_id = raw.get("case_id")
        vertical = raw.get("vertical")
        kind = raw.get("kind")
        role = raw.get("expected_role")
        relationship = raw.get("expected_relationship_state")
        if (
            not isinstance(case_id, str)
            or not case_id
            or case_id in identifiers
            or vertical not in VERTICALS
            or kind not in allowed_kinds
            or role not in ROLES
            or relationship not in {"none", "observed_text"}
            or not isinstance(raw.get("payload"), Mapping)
            or not isinstance(raw.get("truth_basis"), str)
        ):
            raise ProductOntologyBenchmarkError("regression case is invalid")
        identifiers.add(case_id)
        cases.append(
            BenchmarkCase(
                case_id=f"regression:{case_id}",
                vertical=str(vertical),
                kind=str(kind),
                payload=raw["payload"],
                expected_role=str(role),
                expected_relationship_state=str(relationship),
                truth_basis=str(raw["truth_basis"]),
            )
        )
    if {case.vertical for case in cases} != set(VERTICALS):
        raise ProductOntologyBenchmarkError("regressions must cover every vertical")
    if {case.expected_role for case in cases} != set(ROLES):
        raise ProductOntologyBenchmarkError("regressions must cover every role")
    return cases, payload


_LEGACY_ROLE_MAP = {
    legacy_roles.MAIN_PRODUCT: "PRIMARY_PRODUCT",
    legacy_roles.ACCESSORY: "ACCESSORY",
    legacy_roles.PROTECTIVE_CASE: "ACCESSORY",
    legacy_roles.SCREEN_PROTECTOR: "ACCESSORY",
    legacy_roles.CHARGER: "ACCESSORY",
    legacy_roles.CABLE: "ACCESSORY",
    legacy_roles.BATTERY: "ACCESSORY",
    legacy_roles.ADAPTER: "ACCESSORY",
    legacy_roles.STAND: "ACCESSORY",
    legacy_roles.MOUNT: "ACCESSORY",
    legacy_roles.HOLDER: "ACCESSORY",
    legacy_roles.BAG: "ACCESSORY",
    legacy_roles.REPLACEMENT_PART: "REPLACEMENT_PART",
    legacy_roles.CONSUMABLE: "CONSUMABLE",
    legacy_roles.SERVICE: "SERVICE",
    legacy_roles.SUBSCRIPTION: "SERVICE",
    legacy_roles.SOFTWARE: "DIGITAL_CONTENT",
    legacy_roles.BUNDLE: "BUNDLE",
    legacy_roles.UNKNOWN: "UNKNOWN",
}


def _legacy_prediction(case: BenchmarkCase) -> Prediction:
    value = legacy_roles.understand_offer(
        name=case.payload.get("name"),
        merchant_category=case.payload.get("merchant_category"),
        brand=case.payload.get("brand"),
        offer_kind=case.payload.get("offer_kind"),
    )
    relationships = value["relationships"]
    relationship_state = "observed_text" if relationships else "none"
    return Prediction(_LEGACY_ROLE_MAP.get(value["product_role"], "UNKNOWN"), relationship_state)


def _extractor_prediction(case: BenchmarkCase) -> Prediction:
    from datetime import datetime, timezone

    snapshot = extract_product_ontology(
        case.payload,
        raw_source_record_id=1,
        source_type="quality_holdout",
        source_ref="quality-holdout:product-ontology:1",
        observed_at=datetime(2026, 9, 1, 10, tzinfo=timezone.utc),
        evaluated_at=datetime(2026, 9, 1, 11, tzinfo=timezone.utc),
        offer_id=1,
        variant_id=1,
    )
    relationships = snapshot["relationships"]
    if any(item["target_state"] == "canonical" for item in relationships):
        relationship_state = "canonical"
    elif any(item["target_state"] == "observed_text" for item in relationships):
        relationship_state = "observed_text"
    else:
        relationship_state = "none"
    return Prediction(snapshot["product_role"]["value"], relationship_state)


def _evaluate(case: BenchmarkCase, *, adapter: str) -> CaseResult:
    if adapter == "oracle":
        prediction = Prediction(case.expected_role, case.expected_relationship_state)
    elif adapter == "legacy":
        prediction = _legacy_prediction(case)
    elif adapter == "extractor":
        prediction = _extractor_prediction(case)
    else:
        raise ProductOntologyBenchmarkError("benchmark adapter is invalid")
    return CaseResult(
        case_id=case.case_id,
        vertical=case.vertical,
        kind=case.kind,
        expected_role=case.expected_role,
        actual_role=prediction.role,
        expected_relationship_state=case.expected_relationship_state,
        actual_relationship_state=prediction.relationship_state,
        role_passed=prediction.role == case.expected_role,
        relationship_passed=prediction.relationship_state == case.expected_relationship_state,
        truth_basis=case.truth_basis,
    )


def build_report(manifest_path: str | Path, *, adapter: str = "oracle") -> dict[str, Any]:
    path = Path(manifest_path).resolve()
    manifest = _load_manifest(path)
    cases, regressions = _regression_cases(path, manifest)
    generator = manifest["generator"]
    for seed in generator["seeds"]:
        cases.extend(_generated_cases(seed=seed, samples=generator["samples_per_vertical_seed"]))
    results = [_evaluate(case, adapter=adapter) for case in cases]

    known = [result for result in results if result.kind == "known_role"]
    primary_negatives = [result for result in results if result.kind == "primary_negative"]
    unknowns = [result for result in results if result.kind == "unknown"]
    relations = [result for result in results if result.kind == "observed_relation"]
    known_successes = sum(result.role_passed for result in known)
    unknown_successes = sum(result.actual_role == "UNKNOWN" for result in unknowns)
    false_primary = sum(result.actual_role == "PRIMARY_PRODUCT" for result in primary_negatives)
    canonical_promotions = sum(result.actual_relationship_state == "canonical" for result in relations)
    blocking_failures = false_primary + canonical_promotions

    metrics = {
        "known_role_accuracy": _metric(known_successes, len(known)),
        "unknown_abstention_accuracy": _metric(unknown_successes, len(unknowns)),
        "false_primary_product_rate": _event_metric(false_primary, len(primary_negatives), "false_primary_products"),
        "canonical_relation_false_promotion_rate": _event_metric(canonical_promotions, len(relations), "canonical_promotions"),
    }
    gates = manifest["gates"]
    gate_results = {
        "known_role_accuracy_ci95_lower_min": metrics["known_role_accuracy"]["ci95_lower"] >= gates["known_role_accuracy_ci95_lower_min"],
        "unknown_abstention_accuracy_ci95_lower_min": metrics["unknown_abstention_accuracy"]["ci95_lower"] >= gates["unknown_abstention_accuracy_ci95_lower_min"],
        "false_primary_product_rate_ci95_upper_max": metrics["false_primary_product_rate"]["ci95_upper"] <= gates["false_primary_product_rate_ci95_upper_max"],
        "canonical_relation_false_promotion_rate_ci95_upper_max": metrics["canonical_relation_false_promotion_rate"]["ci95_upper"] <= gates["canonical_relation_false_promotion_rate_ci95_upper_max"],
        "blocking_failures_max": blocking_failures <= gates["blocking_failures_max"],
    }
    support = manifest["minimum_statistical_support"]
    support_results = {
        "known_role_cases": len(known) >= support["known_role_cases"],
        "primary_negative_cases": len(primary_negatives) >= support["primary_negative_cases"],
        "unknown_cases": len(unknowns) >= support["unknown_cases"],
        "observed_relation_cases": len(relations) >= support["observed_relation_cases"],
    }
    report = {
        "schema_version": SCHEMA_VERSION,
        "benchmark_version": manifest["benchmark_version"],
        "limitation": LIMITATION,
        "quality_status": "DETERMINISTIC_ORACLE_WITHOUT_EXTERNAL_HUMAN_GROUND_TRUTH",
        "adapter_version": (
            "contract-oracle/v1"
            if adapter == "oracle"
            else (LEGACY_VERSION if adapter == "legacy" else EXTRACTOR_VERSION)
        ),
        "generator": generator,
        "roles": list(ROLES),
        "verticals": list(VERTICALS),
        "summary": {
            "benchmark_status": "RATIFIED" if all(support_results.values()) else "INVALID_SUPPORT",
            "adapter_status": "QUALIFIED" if all(gate_results.values()) else "UNSAFE",
            "promotion_eligible": adapter != "oracle" and all(gate_results.values()) and all(support_results.values()),
            "cases": len(results),
            "role_mismatches": sum(not result.role_passed for result in results),
            "relationship_mismatches": sum(not result.relationship_passed for result in results),
            "blocking_failures": blocking_failures,
            "gate_results": gate_results,
            "support_results": support_results,
        },
        "metrics": metrics,
        "by_role": {
            role: {
                "cases": sum(result.expected_role == role for result in results),
                "mismatches": sum(result.expected_role == role and not result.role_passed for result in results),
            }
            for role in ROLES
        },
        "by_vertical": {
            vertical: {
                "cases": sum(result.vertical == vertical for result in results),
                "role_mismatches": sum(result.vertical == vertical and not result.role_passed for result in results),
            }
            for vertical in VERTICALS
        },
        "regressions": {
            "cases": sum(result.case_id.startswith("regression:") for result in results),
            "mismatches": [result.case_id for result in results if result.case_id.startswith("regression:") and (not result.role_passed or not result.relationship_passed)],
        },
        "mismatch_samples": [asdict(result) for result in results if not result.role_passed or not result.relationship_passed][:25],
    }
    corpus = [asdict(case) for case in cases]
    report["corpus_sha256"] = "sha256:" + hashlib.sha256(canonical_json(corpus).encode("utf-8")).hexdigest()
    report["regressions_sha256"] = "sha256:" + hashlib.sha256(canonical_json(regressions).encode("utf-8")).hexdigest()
    report["evaluation_id"] = "sha256:" + hashlib.sha256(
        canonical_json({"manifest": manifest, "report": report}).encode("utf-8")
    ).hexdigest()
    return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Benchmark Product Ontology FILON")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output")
    parser.add_argument("--adapter", choices=("oracle", "legacy", "extractor"), default="oracle")
    parser.add_argument("--require-promotion", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        report = build_report(args.manifest, adapter=args.adapter)
    except ProductOntologyBenchmarkError as exc:
        print(json.dumps({"status": "INVALID", "error": str(exc)}))
        return 2
    payload = canonical_json(report) + "\n"
    if args.output:
        atomic_write_text(args.output, payload)
        print(canonical_json({"evaluation_id": report["evaluation_id"], "summary": report["summary"], "metrics": report["metrics"]}))
    else:
        print(payload, end="")
    return int(args.require_promotion and not report["summary"]["promotion_eligible"])


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
