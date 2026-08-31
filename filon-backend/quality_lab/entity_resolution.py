"""Benchmark Phase 2 pour Entity Resolution.

Le benchmark ratifie un oracle déterministe, des hard negatives et les gates
statistiques avant l'implémentation du resolver multi-signal. Le baseline
évalué ici reproduit volontairement la politique exacte-GTIN de Phase 1 sans
importer le writer ou les modèles SQLAlchemy : il sert à montrer que la
sécurité est conservée et que la couverture non-GTIN reste incomplète.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from .integrity import atomic_write_text, canonical_json


SCHEMA_VERSION = "entity-resolution-benchmark/v1"
MANIFEST_VERSION = "entity-resolution-benchmark-manifest/v1"
GENERATOR_VERSION = "filon-entity-resolution-holdout/v1"
LIMITATION = "NO_EXTERNAL_HUMAN_GROUND_TRUTH"
BASELINE_VERSION = "exact-gtin-policy-adapter/v1"
VERTICALS = (
    "smartphones",
    "laptops",
    "tyres",
    "appliances_hvac",
    "audio",
)


class EntityResolutionBenchmarkError(ValueError):
    """Entrée benchmark hors contrat : l'évaluation échoue fermée."""


@dataclass(frozen=True)
class BenchmarkCase:
    case_id: str
    vertical: str
    kind: str
    left: Mapping[str, Any]
    right: Mapping[str, Any]
    expected: str
    truth_basis: str


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    vertical: str
    kind: str
    expected: str
    actual: str
    passed: bool
    truth_basis: str


def _wilson(successes: int, total: int, *, z: float = 1.959963984540054) -> tuple[float, float]:
    if total <= 0:
        raise EntityResolutionBenchmarkError("metric denominator must be positive")
    probability = successes / total
    denominator = 1 + z * z / total
    center = (probability + z * z / (2 * total)) / denominator
    margin = (
        z
        * math.sqrt(
            probability * (1 - probability) / total
            + z * z / (4 * total * total)
        )
        / denominator
    )
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


def _event_metric(events: int, total: int, event_name: str) -> dict[str, Any]:
    lower, upper = _wilson(events, total)
    return {
        "cases": total,
        event_name: events,
        "rate": round(events / total, 8),
        "ci95_lower": round(lower, 8),
        "ci95_upper": round(upper, 8),
    }


def _load_json(path: Path, error: str) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EntityResolutionBenchmarkError(error) from exc
    if not isinstance(value, Mapping):
        raise EntityResolutionBenchmarkError(error)
    return value


def _load_manifest(path: Path) -> Mapping[str, Any]:
    manifest = _load_json(path, "entity resolution manifest is unreadable")
    if manifest.get("schema_version") != MANIFEST_VERSION:
        raise EntityResolutionBenchmarkError("unsupported entity resolution manifest")
    if manifest.get("limitation") != LIMITATION:
        raise EntityResolutionBenchmarkError("human-ground-truth limitation is missing")
    if manifest.get("false_merge_policy") != "false_merge_is_worse_than_false_split":
        raise EntityResolutionBenchmarkError("false merge policy is invalid")

    generator = manifest.get("generator")
    if not isinstance(generator, Mapping):
        raise EntityResolutionBenchmarkError("generator configuration is missing")
    seeds = generator.get("seeds")
    samples = generator.get("samples_per_vertical_seed")
    if (
        generator.get("version") != GENERATOR_VERSION
        or generator.get("development_engine_input") is not False
        or not isinstance(seeds, list)
        or not seeds
        or any(isinstance(seed, bool) or not isinstance(seed, int) for seed in seeds)
        or isinstance(samples, bool)
        or not isinstance(samples, int)
        or not 32 <= samples <= 1000
    ):
        raise EntityResolutionBenchmarkError("generator configuration is invalid")
    if manifest.get("verticals") != list(VERTICALS):
        raise EntityResolutionBenchmarkError("vertical roster is invalid")

    gates = manifest.get("gates")
    required_gates = {
        "exact_preservation_accuracy_ci95_lower_min",
        "false_merge_rate_ci95_upper_max",
        "conflict_abstention_accuracy_ci95_lower_min",
        "weak_only_abstention_accuracy_ci95_lower_min",
        "known_structured_positive_resolution_ci95_lower_min",
        "known_structured_positive_abstention_rate_ci95_upper_max",
        "known_conflict_promotions_max",
    }
    if not isinstance(gates, Mapping) or set(gates) != required_gates:
        raise EntityResolutionBenchmarkError("benchmark gates are invalid")
    for key in required_gates - {"known_conflict_promotions_max"}:
        value = gates[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= float(value) <= 1:
            raise EntityResolutionBenchmarkError("benchmark threshold is invalid")
    if gates["known_conflict_promotions_max"] != 0:
        raise EntityResolutionBenchmarkError("known conflict promotion budget must remain zero")
    if float(gates["false_merge_rate_ci95_upper_max"]) > 0.005:
        raise EntityResolutionBenchmarkError("false merge target cannot exceed 0.5 percent")

    support = manifest.get("minimum_statistical_support")
    expected_support = {
        "hard_negative_cases": 2800,
        "exact_positive_cases": 900,
        "structured_positive_cases": 900,
        "weak_only_cases": 900,
    }
    if support != expected_support:
        raise EntityResolutionBenchmarkError("minimum statistical support is invalid")

    regression = manifest.get("regression_ground_truth")
    if not isinstance(regression, str) or Path(regression).name != regression:
        raise EntityResolutionBenchmarkError("regression path is invalid")
    return manifest


def _valid_gtin(value: Any) -> str | None:
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        return None
    text = str(value).strip()
    if not text.isdigit() or len(text) not in {8, 12, 13, 14}:
        return None
    digits = [int(character) for character in text]
    expected = (10 - sum(
        digit * (3 if index % 2 == 0 else 1)
        for index, digit in enumerate(reversed(digits[:-1]))
    ) % 10) % 10
    return text if digits[-1] == expected else None


def _exact_identifier(observation: Mapping[str, Any]) -> tuple[str | None, bool]:
    identifiers = observation.get("identifiers")
    if identifiers is None:
        return None, False
    if not isinstance(identifiers, Mapping):
        raise EntityResolutionBenchmarkError("identifiers must be an object")
    supplied = False
    valid: set[str] = set()
    for key in ("gtin", "ean", "ean13", "upc"):
        if key not in identifiers or identifiers[key] in (None, ""):
            continue
        supplied = True
        normalized = _valid_gtin(identifiers[key])
        if normalized is not None:
            valid.add(normalized)
    if len(valid) != 1:
        return None, supplied
    return next(iter(valid)), supplied


def exact_gtin_baseline(left: Mapping[str, Any], right: Mapping[str, Any]) -> str:
    """Adaptateur pur de la politique Phase 1 : exact ou abstention."""

    left_gtin, _ = _exact_identifier(left)
    right_gtin, _ = _exact_identifier(right)
    if left_gtin is not None and left_gtin == right_gtin:
        return "same"
    return "abstain"


def _valid_ean(rng: random.Random) -> str:
    prefix = "".join(str(rng.randrange(10)) for _ in range(12))
    total = sum(
        int(character) * (3 if index % 2 == 0 else 1)
        for index, character in enumerate(reversed(prefix))
    )
    return prefix + str((10 - total % 10) % 10)


def _different_ean(rng: random.Random, current: str) -> str:
    candidate = _valid_ean(rng)
    while candidate == current:
        candidate = _valid_ean(rng)
    return candidate


def _surfaces(vertical: str, index: int) -> dict[str, str]:
    values = {
        "smartphones": {
            "brand": "Example Mobile",
            "model": f"Phone Pro {index}",
            "mpn": f"MBL-{index:05d}",
            "attribute": "storage",
            "a": "128GB",
            "b": "256GB",
            "accessory": "protective case",
        },
        "laptops": {
            "brand": "Example Compute",
            "model": f"Notebook Air {index}",
            "mpn": f"LTP-{index:05d}",
            "attribute": "memory",
            "a": "16GB",
            "b": "32GB",
            "accessory": "power adapter",
        },
        "tyres": {
            "brand": "Example Tyres",
            "model": f"Road Grip {index}",
            "mpn": f"TYR-{index:05d}",
            "attribute": "size",
            "a": "205/55R16",
            "b": "225/45R17",
            "accessory": "wheel cover",
        },
        "appliances_hvac": {
            "brand": "Example Home",
            "model": f"Climate Pro {index}",
            "mpn": f"HVC-{index:05d}",
            "attribute": "capacity",
            "a": "9000BTU",
            "b": "12000BTU",
            "accessory": "replacement filter",
        },
        "audio": {
            "brand": "Example Audio",
            "model": f"Sound Max {index}",
            "mpn": f"AUD-{index:05d}",
            "attribute": "color",
            "a": "black",
            "b": "white",
            "accessory": "carrying case",
        },
    }
    return values[vertical]


def _generated_cases(*, seed: int, samples: int) -> list[BenchmarkCase]:
    rng = random.Random(seed)
    cases: list[BenchmarkCase] = []
    for vertical in VERTICALS:
        for index in range(samples):
            surface = _surfaces(vertical, index)
            first = _valid_ean(rng)
            second = _different_ean(rng, first)
            base = f"holdout:{seed}:{vertical}:{index}"
            structured = {
                "brand": surface["brand"],
                "mpn": surface["mpn"],
                "model": surface["model"],
                "attributes": {surface["attribute"]: surface["a"]},
                "product_role": "primary_product",
            }
            cases.extend(
                [
                    BenchmarkCase(
                        f"{base}:exact", vertical, "exact_positive",
                        {**structured, "identifiers": {"ean": first}},
                        {**structured, "identifiers": {"gtin": first}},
                        "same", "EXACT_GLOBAL_IDENTIFIER",
                    ),
                    BenchmarkCase(
                        f"{base}:structured", vertical, "structured_positive",
                        structured,
                        {**structured, "title": surface["model"].lower()},
                        "same", "SYNTHETIC_STRUCTURED_IDENTITY",
                    ),
                    BenchmarkCase(
                        f"{base}:distinct-gtin", vertical, "hard_negative",
                        {**structured, "identifiers": {"ean": first}},
                        {**structured, "identifiers": {"ean": second}},
                        "abstain", "DISTINCT_GLOBAL_IDENTIFIERS",
                    ),
                    BenchmarkCase(
                        f"{base}:attribute-conflict", vertical, "hard_negative",
                        structured,
                        {**structured, "attributes": {surface["attribute"]: surface["b"]}},
                        "abstain", "STRUCTURED_VARIANT_CONFLICT",
                    ),
                    BenchmarkCase(
                        f"{base}:role-conflict", vertical, "hard_negative",
                        structured,
                        {**structured, "product_role": "accessory", "title": surface["accessory"]},
                        "abstain", "PRODUCT_ROLE_CONFLICT",
                    ),
                    BenchmarkCase(
                        f"{base}:mpn-scope-conflict", vertical, "hard_negative",
                        structured,
                        {**structured, "brand": "Different Brand"},
                        "abstain", "BRAND_SCOPED_MPN_CONFLICT",
                    ),
                    BenchmarkCase(
                        f"{base}:weak-only", vertical, "weak_only",
                        {"title": surface["model"], "image": f"https://example.test/{index}.jpg"},
                        {"title": surface["model"].lower(), "image": f"https://example.test/{index}.jpg"},
                        "abstain", "WEAK_SIGNALS_ONLY",
                    ),
                ]
            )
    return cases


def _regression_cases(manifest_path: Path, manifest: Mapping[str, Any]) -> list[BenchmarkCase]:
    path = manifest_path.parent / str(manifest["regression_ground_truth"])
    payload = _load_json(path, "entity resolution regressions are unreadable")
    if (
        payload.get("schema_version") != "entity-resolution-regressions/v1"
        or payload.get("truth_basis") != "REGRESSION_GROUND_TRUTH"
        or payload.get("limitation") != LIMITATION
        or not isinstance(payload.get("cases"), list)
    ):
        raise EntityResolutionBenchmarkError("entity resolution regressions are invalid")
    cases: list[BenchmarkCase] = []
    identifiers: set[str] = set()
    allowed_kinds = {"exact_positive", "structured_positive", "hard_negative", "weak_only"}
    for raw in payload["cases"]:
        if not isinstance(raw, Mapping):
            raise EntityResolutionBenchmarkError("regression case is invalid")
        case_id = raw.get("case_id")
        vertical = raw.get("vertical")
        kind = raw.get("kind")
        expected = raw.get("expected")
        if (
            not isinstance(case_id, str)
            or not case_id
            or case_id in identifiers
            or vertical not in VERTICALS
            or kind not in allowed_kinds
            or expected not in {"same", "abstain"}
            or not isinstance(raw.get("left"), Mapping)
            or not isinstance(raw.get("right"), Mapping)
            or not isinstance(raw.get("truth_basis"), str)
        ):
            raise EntityResolutionBenchmarkError("regression case is invalid")
        identifiers.add(case_id)
        cases.append(
            BenchmarkCase(
                case_id=f"regression:{case_id}",
                vertical=str(vertical),
                kind=str(kind),
                left=raw["left"],
                right=raw["right"],
                expected=str(expected),
                truth_basis=str(raw["truth_basis"]),
            )
        )
    if {case.vertical for case in cases} != set(VERTICALS):
        raise EntityResolutionBenchmarkError("regressions must cover every vertical")
    return cases


def _evaluate(case: BenchmarkCase) -> CaseResult:
    actual = exact_gtin_baseline(case.left, case.right)
    return CaseResult(
        case_id=case.case_id,
        vertical=case.vertical,
        kind=case.kind,
        expected=case.expected,
        actual=actual,
        passed=actual == case.expected,
        truth_basis=case.truth_basis,
    )


def build_report(manifest_path: str | Path) -> dict[str, Any]:
    path = Path(manifest_path).resolve()
    manifest = _load_manifest(path)
    cases = _regression_cases(path, manifest)
    generator = manifest["generator"]
    for seed in generator["seeds"]:
        cases.extend(_generated_cases(seed=seed, samples=generator["samples_per_vertical_seed"]))
    results = [_evaluate(case) for case in cases]

    exact = [result for result in results if result.kind == "exact_positive"]
    structured = [result for result in results if result.kind == "structured_positive"]
    negatives = [result for result in results if result.kind == "hard_negative"]
    weak = [result for result in results if result.kind == "weak_only"]
    conflicts = [result for result in negatives if result.truth_basis != "DISTINCT_GLOBAL_IDENTIFIERS"]

    exact_promotions = sum(result.actual == "same" for result in exact)
    structured_promotions = sum(result.actual == "same" for result in structured)
    false_merges = sum(result.actual == "same" for result in negatives)
    conflict_abstentions = sum(result.actual == "abstain" for result in conflicts)
    weak_abstentions = sum(result.actual == "abstain" for result in weak)
    structured_abstentions = sum(result.actual == "abstain" for result in structured)

    metrics = {
        "exact_preservation_accuracy": _metric(exact_promotions, len(exact)),
        "false_merge_rate": _event_metric(false_merges, len(negatives), "false_merges"),
        "conflict_abstention_accuracy": _metric(conflict_abstentions, len(conflicts)),
        "weak_only_abstention_accuracy": _metric(weak_abstentions, len(weak)),
        "known_structured_positive_resolution": _metric(structured_promotions, len(structured)),
        "known_structured_positive_abstention_rate": _event_metric(
            structured_abstentions,
            len(structured),
            "abstentions",
        ),
    }
    gates = manifest["gates"]
    safety_gates = {
        "exact_preservation_accuracy_ci95_lower_min": metrics["exact_preservation_accuracy"]["ci95_lower"]
        >= gates["exact_preservation_accuracy_ci95_lower_min"],
        "false_merge_rate_ci95_upper_max": metrics["false_merge_rate"]["ci95_upper"]
        <= gates["false_merge_rate_ci95_upper_max"],
        "conflict_abstention_accuracy_ci95_lower_min": metrics["conflict_abstention_accuracy"]["ci95_lower"]
        >= gates["conflict_abstention_accuracy_ci95_lower_min"],
        "weak_only_abstention_accuracy_ci95_lower_min": metrics["weak_only_abstention_accuracy"]["ci95_lower"]
        >= gates["weak_only_abstention_accuracy_ci95_lower_min"],
        "known_conflict_promotions_max": false_merges <= gates["known_conflict_promotions_max"],
    }
    coverage_gates = {
        "known_structured_positive_resolution_ci95_lower_min": metrics["known_structured_positive_resolution"]["ci95_lower"]
        >= gates["known_structured_positive_resolution_ci95_lower_min"],
        "known_structured_positive_abstention_rate_ci95_upper_max": metrics["known_structured_positive_abstention_rate"]["ci95_upper"]
        <= gates["known_structured_positive_abstention_rate_ci95_upper_max"],
    }
    support = manifest["minimum_statistical_support"]
    support_gates = {
        "hard_negative_cases": len(negatives) >= support["hard_negative_cases"],
        "exact_positive_cases": len(exact) >= support["exact_positive_cases"],
        "structured_positive_cases": len(structured) >= support["structured_positive_cases"],
        "weak_only_cases": len(weak) >= support["weak_only_cases"],
    }
    promotion_eligible = all(safety_gates.values()) and all(coverage_gates.values())
    report = {
        "schema_version": SCHEMA_VERSION,
        "benchmark_version": manifest["benchmark_version"],
        "limitation": LIMITATION,
        "quality_status": "DETERMINISTIC_ORACLE_WITHOUT_EXTERNAL_HUMAN_GROUND_TRUTH",
        "baseline_version": BASELINE_VERSION,
        "generator": generator,
        "verticals": list(VERTICALS),
        "summary": {
            "benchmark_status": "RATIFIED" if all(support_gates.values()) else "INVALID_SUPPORT",
            "baseline_status": "SAFE_INCOMPLETE" if all(safety_gates.values()) and not promotion_eligible else ("QUALIFIED" if promotion_eligible else "UNSAFE"),
            "promotion_eligible": promotion_eligible,
            "cases": len(results),
            "oracle_mismatches": sum(not result.passed for result in results),
            "safety_gate_results": safety_gates,
            "coverage_gate_results": coverage_gates,
            "support_gate_results": support_gates,
        },
        "metrics": metrics,
        "by_vertical": {
            vertical: {
                "cases": sum(result.vertical == vertical for result in results),
                "oracle_mismatches": sum(result.vertical == vertical and not result.passed for result in results),
                "false_merges": sum(result.vertical == vertical and result.kind == "hard_negative" and result.actual == "same" for result in results),
            }
            for vertical in VERTICALS
        },
        "regressions": {
            "cases": sum(result.case_id.startswith("regression:") for result in results),
            "mismatches": [
                result.case_id
                for result in results
                if result.case_id.startswith("regression:") and not result.passed
            ],
        },
        "oracle_mismatch_samples": [asdict(result) for result in results if not result.passed][:25],
    }
    report["evaluation_id"] = "sha256:" + hashlib.sha256(
        canonical_json({"manifest": manifest, "report": report}).encode("utf-8")
    ).hexdigest()
    return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Benchmark Entity Resolution FILON")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output")
    parser.add_argument("--require-promotion", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        report = build_report(args.manifest)
    except EntityResolutionBenchmarkError as exc:
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
