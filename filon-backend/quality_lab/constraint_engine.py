"""Holdout synthétique indépendant Phase 6 Constraint Engine."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from app.constraint_engine.engine import (
    CandidateFacts,
    ConstraintRequest,
    Fact,
    HardConstraint,
    Preference,
    evaluate_constraints,
)


SCHEMA_VERSION = "constraint-engine-benchmark/v1"
MANIFEST_VERSION = "constraint-engine-benchmark-manifest/v1"
GENERATOR_VERSION = "filon-constraint-engine-holdout/v1"
LIMITATION = "NO_EXTERNAL_HUMAN_GROUND_TRUTH"
VERTICALS = ("smartphones", "laptops", "audio", "fashion", "appliances_hvac", "tyres")
LOCALES = ("fr", "nl", "en")
SCENARIOS = (
    "eligible",
    "budget_exceeded",
    "availability_unknown",
    "attribute_conflict",
    "adult_excluded",
    "preference_only",
)


class ConstraintBenchmarkError(ValueError):
    """Manifest ou corpus de benchmark hors contrat."""


@dataclass(frozen=True)
class BenchmarkCase:
    case_id: str
    vertical: str
    locale: str
    scenario: str
    expected_status: str
    truth_basis: str
    candidate: CandidateFacts
    request: ConstraintRequest


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    vertical: str
    locale: str
    scenario: str
    expected_status: str
    actual_status: str
    false_eligible: bool
    unknown_satisfied: bool
    preference_reintroduced: bool
    provenance_complete: bool
    passed: bool


def _wilson(successes: int, total: int, *, z: float = 1.959963984540054) -> tuple[float, float]:
    if total <= 0:
        raise ConstraintBenchmarkError("metric denominator must be positive")
    probability = successes / total
    denominator = 1 + z * z / total
    center = (probability + z * z / (2 * total)) / denominator
    margin = z * math.sqrt(probability * (1 - probability) / total + z * z / (4 * total * total)) / denominator
    return max(0.0, center - margin), min(1.0, center + margin)


def _load_manifest(path: Path) -> Mapping[str, Any]:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConstraintBenchmarkError("constraint benchmark manifest is unreadable") from exc
    if not isinstance(manifest, Mapping) or manifest.get("schema_version") != MANIFEST_VERSION:
        raise ConstraintBenchmarkError("unsupported constraint benchmark manifest")
    if manifest.get("limitation") != LIMITATION:
        raise ConstraintBenchmarkError("human-ground-truth limitation is missing")
    if manifest.get("policy") != "hard_constraints_before_preferences_fail_closed":
        raise ConstraintBenchmarkError("constraint policy is invalid")
    if manifest.get("verticals") != list(VERTICALS) or manifest.get("locales") != list(LOCALES):
        raise ConstraintBenchmarkError("benchmark roster is invalid")
    if manifest.get("scenarios") != list(SCENARIOS):
        raise ConstraintBenchmarkError("scenario roster is invalid")
    generator = manifest.get("generator")
    if not isinstance(generator, Mapping):
        raise ConstraintBenchmarkError("generator configuration is missing")
    seeds = generator.get("seeds")
    samples = generator.get("samples_per_vertical_locale_seed")
    if (
        generator.get("version") != GENERATOR_VERSION
        or generator.get("development_engine_input") is not False
        or not isinstance(seeds, list)
        or not seeds
        or any(isinstance(seed, bool) or not isinstance(seed, int) for seed in seeds)
        or isinstance(samples, bool)
        or not isinstance(samples, int)
        or not 16 <= samples <= 256
    ):
        raise ConstraintBenchmarkError("generator configuration is invalid")
    expected_support = {
        "total_cases": 4500,
        "eligible_cases": 700,
        "exclusion_cases": 2200,
        "unknown_cases": 700,
        "preference_cases": 700,
    }
    if manifest.get("minimum_statistical_support") != expected_support:
        raise ConstraintBenchmarkError("minimum statistical support is invalid")
    exact_gates = {
        "status_accuracy_ci95_lower_min": 0.995,
        "false_eligible_max": 0,
        "unknown_satisfied_max": 0,
        "preference_reintroductions_max": 0,
        "provenance_completeness_min": 1.0,
        "blocking_failures_max": 0,
    }
    if manifest.get("gates") != exact_gates:
        raise ConstraintBenchmarkError("benchmark gates are not ratified")
    if manifest.get("regression_ground_truth") != "constraint-engine-regressions.json":
        raise ConstraintBenchmarkError("regression path is invalid")
    return manifest


def _surface(vertical: str) -> tuple[str, str]:
    return {
        "smartphones": ("storage", "256GB"),
        "laptops": ("memory", "32GB"),
        "audio": ("color", "black"),
        "fashion": ("size", "M"),
        "appliances_hvac": ("capacity", "12000BTU"),
        "tyres": ("size", "205/55R16"),
    }[vertical]


def _case(vertical: str, locale: str, seed: int, index: int) -> BenchmarkCase:
    rng = random.Random(f"{seed}:{vertical}:{locale}:{index}")
    scenario = SCENARIOS[index % len(SCENARIOS)]
    attribute_key, expected_attribute = _surface(vertical)
    entity_ref = f"variant:{vertical}-{locale}-{seed}-{index}"
    amount = f"{rng.randint(20, 90)}.{rng.randint(0, 99):02d}"
    price = Fact("known", {"amount": amount, "currency": "EUR"}, (f"offer-truth:{entity_ref}:price",))
    availability = Fact("known", "in_stock", (f"offer-truth:{entity_ref}:stock",))
    attribute = Fact("known", expected_attribute, (f"ontology:{entity_ref}:{attribute_key}",))
    adult = Fact("known", False, (f"offer:{entity_ref}:adult",))
    expected_status = "ELIGIBLE"
    truth_basis = "ALL_HARD_CONSTRAINTS_SATISFIED"
    if scenario == "budget_exceeded":
        price = Fact("known", {"amount": "100.01", "currency": "EUR"}, price.evidence_refs)
        expected_status = "EXCLUDED"
        truth_basis = "BUDGET_EXCEEDED"
    elif scenario == "availability_unknown":
        availability = Fact("unknown")
        expected_status = "UNKNOWN"
        truth_basis = "UNKNOWN_REQUIRED_AVAILABILITY"
    elif scenario == "attribute_conflict":
        attribute = Fact("known", f"not-{expected_attribute}", attribute.evidence_refs)
        expected_status = "EXCLUDED"
        truth_basis = "ATTRIBUTE_INCOMPATIBLE"
    elif scenario == "adult_excluded":
        adult = Fact("known", True, adult.evidence_refs)
        expected_status = "EXCLUDED"
        truth_basis = "ADULT_SAFETY"
    elif scenario == "preference_only":
        truth_basis = "PREFERENCE_DOES_NOT_DEFINE_ELIGIBILITY"
    candidate = CandidateFacts(
        entity_ref=entity_ref,
        price=price,
        countries=Fact("known", ("BE",), (f"merchant:{entity_ref}:countries",)),
        availability=availability,
        adult_restricted=adult,
        attributes={attribute_key: attribute},
        preference_facts={"color": Fact("known", "black", (f"ontology:{entity_ref}:color",))},
    )
    request = ConstraintRequest(
        context_ref=f"holdout:{seed}:{vertical}:{locale}:{index}",
        hard_constraints=(
            HardConstraint("budget", "BUDGET_MAX", {"maximum": {"amount": "100.00", "currency": "EUR"}}),
            HardConstraint("country", "COUNTRY_ALLOWED", {"country_code": "BE"}),
            HardConstraint("stock", "AVAILABILITY_REQUIRED", {"value": "in_stock"}),
            HardConstraint("attribute", "ATTRIBUTE_EQUALS", {"attribute_key": attribute_key, "value": expected_attribute}),
            HardConstraint("adult", "ADULT_SAFETY", {"adult_allowed": False}),
        ),
        preferences=(Preference("prefer-color", "color", "black"),),
    )
    return BenchmarkCase(
        case_id=f"{vertical}:{locale}:{seed}:{index}:{scenario}",
        vertical=vertical,
        locale=locale,
        scenario=scenario,
        expected_status=expected_status,
        truth_basis=truth_basis,
        candidate=candidate,
        request=request,
    )


def generate_cases(manifest: Mapping[str, Any]) -> tuple[BenchmarkCase, ...]:
    generator = manifest["generator"]
    return tuple(
        _case(vertical, locale, seed, index)
        for vertical in VERTICALS
        for locale in LOCALES
        for seed in generator["seeds"]
        for index in range(generator["samples_per_vertical_locale_seed"])
    )


def _legacy_status(case: BenchmarkCase) -> str:
    if case.scenario in {"budget_exceeded", "attribute_conflict"}:
        return "EXCLUDED"
    return "ELIGIBLE"


def evaluate_case(case: BenchmarkCase, adapter: str) -> CaseResult:
    if adapter == "constraint_engine":
        evaluation = evaluate_constraints(case.request, (case.candidate,)).candidates[0]
        actual = evaluation.status
        hard = evaluation.hard_constraints
        preference_satisfied = any(item.status == "SATISFIED" for item in evaluation.preferences)
        provenance_complete = all(
            item.status == "UNKNOWN" or item.kind == "EXPLICIT_EXCLUSION" or bool(item.evidence_refs)
            for item in hard
        )
    elif adapter == "legacy_preference_first":
        actual = _legacy_status(case)
        hard = ()
        preference_satisfied = True
        provenance_complete = False
    else:
        raise ConstraintBenchmarkError("benchmark adapter is unknown")
    false_eligible = actual == "ELIGIBLE" and case.expected_status != "ELIGIBLE"
    unknown_satisfied = case.expected_status == "UNKNOWN" and actual == "ELIGIBLE"
    preference_reintroduced = (
        preference_satisfied and actual == "ELIGIBLE" and case.expected_status == "EXCLUDED"
    )
    passed = actual == case.expected_status and provenance_complete
    return CaseResult(
        case.case_id,
        case.vertical,
        case.locale,
        case.scenario,
        case.expected_status,
        actual,
        false_eligible,
        unknown_satisfied,
        preference_reintroduced,
        provenance_complete,
        passed,
    )


def run_benchmark(manifest_path: Path, *, adapter: str = "constraint_engine") -> dict[str, Any]:
    manifest = _load_manifest(manifest_path)
    cases = generate_cases(manifest)
    results = tuple(evaluate_case(case, adapter) for case in cases)
    successes = sum(item.actual_status == item.expected_status for item in results)
    lower, upper = _wilson(successes, len(results))
    false_eligible = sum(item.false_eligible for item in results)
    unknown_satisfied = sum(item.unknown_satisfied for item in results)
    preference_reintroductions = sum(item.preference_reintroduced for item in results)
    provenance = sum(item.provenance_complete for item in results) / len(results)
    failures = sum(not item.passed for item in results)
    support = {
        "total_cases": len(cases),
        "eligible_cases": sum(case.expected_status == "ELIGIBLE" for case in cases),
        "exclusion_cases": sum(case.expected_status == "EXCLUDED" for case in cases),
        "unknown_cases": sum(case.expected_status == "UNKNOWN" for case in cases),
        "preference_cases": sum(case.scenario == "preference_only" for case in cases),
    }
    gates = manifest["gates"]
    support_gates = {
        key: support[key] >= minimum for key, minimum in manifest["minimum_statistical_support"].items()
    }
    metric_gates = {
        "status_accuracy_ci95_lower_min": lower >= gates["status_accuracy_ci95_lower_min"],
        "false_eligible_max": false_eligible <= gates["false_eligible_max"],
        "unknown_satisfied_max": unknown_satisfied <= gates["unknown_satisfied_max"],
        "preference_reintroductions_max": preference_reintroductions <= gates["preference_reintroductions_max"],
        "provenance_completeness_min": provenance >= gates["provenance_completeness_min"],
        "blocking_failures_max": failures <= gates["blocking_failures_max"],
    }
    identity = [
        {
            "case_id": item.case_id,
            "expected_status": item.expected_status,
            "actual_status": item.actual_status,
            "passed": item.passed,
        }
        for item in results
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "adapter": adapter,
        "limitation": LIMITATION,
        "support": support,
        "metrics": {
            "status_accuracy": {
                "successes": successes,
                "cases": len(results),
                "rate": round(successes / len(results), 8),
                "ci95_lower": round(lower, 8),
                "ci95_upper": round(upper, 8),
            },
            "false_eligible": false_eligible,
            "unknown_satisfied": unknown_satisfied,
            "preference_reintroductions": preference_reintroductions,
            "provenance_completeness": round(provenance, 8),
            "blocking_failures": failures,
        },
        "gates": {**support_gates, **metric_gates},
        "passed": all(support_gates.values()) and all(metric_gates.values()),
        "evaluation_id": "sha256:" + hashlib.sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Benchmark autonome Constraint Engine Phase 6")
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--adapter", choices=("constraint_engine", "legacy_preference_first"), default="constraint_engine")
    parser.add_argument("--strict", action="store_true")
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
    if args.strict and not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
