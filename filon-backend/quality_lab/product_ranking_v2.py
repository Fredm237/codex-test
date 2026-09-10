"""Quality Lab indépendant pour le classement factuel Product Ranking v2."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping

from app.product_ranking.engine import (
    DIMENSIONS,
    REQUIRED_DIMENSIONS,
    VERTICAL_WEIGHTS,
    RankingCandidateFacts,
    RankingRequest,
    ScoreFact,
    rank_products,
)


SCHEMA_VERSION = "product-ranking-benchmark/v2"
MANIFEST_VERSION = "product-ranking-benchmark-manifest/v2"
GENERATOR_VERSION = "filon-product-ranking-holdout/v2"
POLICY = "eligible_product_evidence_scoped_vertical_aware_no_commission"
VERTICALS = tuple(VERTICAL_WEIGHTS)
LOCALES = ("fr", "nl", "en")
SCENARIOS = (
    "full_known",
    "optional_unknown",
    "need_fit_unknown",
    "evidence_unknown",
    "known_unsourced_required",
    "invalid_optional",
    "ineligible",
    "commission_mutation",
    "tie_stability",
)


class ProductRankingV2BenchmarkError(ValueError):
    """Manifest ou corpus Product Ranking v2 hors contrat."""


@dataclass(frozen=True)
class BenchmarkCase:
    case_id: str
    vertical: str
    scenario: str
    candidates: tuple[RankingCandidateFacts, ...]
    expected_order: tuple[str, ...]
    blocked_ref: str | None = None
    partial_refs: tuple[str, ...] = ()


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _wilson(successes: int, total: int) -> tuple[float, float]:
    if total <= 0:
        raise ProductRankingV2BenchmarkError("metric denominator must be positive")
    z = 1.959963984540054
    probability = successes / total
    denominator = 1 + z * z / total
    center = (probability + z * z / (2 * total)) / denominator
    margin = z * math.sqrt(
        probability * (1 - probability) / total + z * z / (4 * total * total)
    ) / denominator
    return max(0.0, center - margin), min(1.0, center + margin)


def _load_manifest(path: Path) -> Mapping[str, Any]:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProductRankingV2BenchmarkError("product ranking v2 manifest is unreadable") from exc
    if not isinstance(manifest, Mapping) or manifest.get("schema_version") != MANIFEST_VERSION:
        raise ProductRankingV2BenchmarkError("unsupported product ranking v2 manifest")
    if manifest.get("policy") != POLICY:
        raise ProductRankingV2BenchmarkError("product ranking v2 policy is invalid")
    if manifest.get("verticals") != list(VERTICALS) or manifest.get("locales") != list(LOCALES):
        raise ProductRankingV2BenchmarkError("product ranking v2 roster is invalid")
    if manifest.get("scenarios") != list(SCENARIOS):
        raise ProductRankingV2BenchmarkError("product ranking v2 scenarios are invalid")
    generator = manifest.get("generator")
    if not isinstance(generator, Mapping):
        raise ProductRankingV2BenchmarkError("generator configuration is missing")
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
        raise ProductRankingV2BenchmarkError("generator configuration is invalid")
    expected_support = {
        "total_cases": 5000,
        "optional_unknown_cases": 500,
        "required_unknown_cases": 1000,
        "known_unsourced_required_cases": 500,
        "invalid_optional_cases": 500,
        "ineligible_cases": 500,
        "commission_mutation_cases": 500,
    }
    if manifest.get("minimum_statistical_support") != expected_support:
        raise ProductRankingV2BenchmarkError("minimum statistical support is invalid")
    expected_gates = {
        "order_accuracy_ci95_lower_min": 0.995,
        "top1_accuracy_min": 1.0,
        "required_unknown_ranked_max": 0,
        "known_unsourced_required_ranked_max": 0,
        "invalid_optional_ranked_max": 0,
        "ineligible_ranked_max": 0,
        "optional_unknown_disclosure_min": 1.0,
        "provenance_completeness_min": 1.0,
        "determinism_failures_max": 0,
        "commission_invariance_failures_max": 0,
    }
    if manifest.get("engineering_gates") != expected_gates:
        raise ProductRankingV2BenchmarkError("engineering gates are not ratified")
    if manifest.get("claim_boundary") != {
        "ranking_is_product_quality_claim": False,
        "ranking_is_offer_selection": False,
        "ranking_is_buy_wait_verdict": False,
        "unknown_dimension_receives_score": False,
    }:
        raise ProductRankingV2BenchmarkError("claim boundary is invalid")
    if manifest.get("evaluation_governance") != {
        "mode": "AUTONOMOUS_QUALITY_LAB",
        "external_human_ground_truth": "NO_EXTERNAL_HUMAN_GROUND_TRUTH",
        "subjective_quality_status": "NOT_INDEPENDENTLY_VALIDATED",
        "human_validation_required": False,
    }:
        raise ProductRankingV2BenchmarkError("evaluation governance is invalid")
    return manifest


def _known(value: int, ref: str, *, sourced: bool = True) -> ScoreFact:
    return ScoreFact("known", f"{value / 100:.2f}", (ref,) if sourced else ())


def _candidate(ref: str, values: tuple[int, int, int, int]) -> RankingCandidateFacts:
    return RankingCandidateFacts(
        ref,
        "ELIGIBLE",
        {
            name: _known(value, f"evidence:{name}:{ref}")
            for name, value in zip(DIMENSIONS, values, strict=True)
        },
    )


def _oracle_order(vertical: str, candidates: tuple[RankingCandidateFacts, ...]) -> tuple[str, ...]:
    weights = VERTICAL_WEIGHTS[vertical]
    scored: list[tuple[Decimal, str]] = []
    for candidate in candidates:
        if candidate.eligibility_status != "ELIGIBLE":
            continue
        values: dict[str, Decimal] = {}
        invalid = False
        for name in DIMENSIONS:
            fact = candidate.dimensions[name]
            if fact.state in {"invalid", "conflict"}:
                invalid = True
                break
            if fact.state == "known":
                if fact.value is None or not fact.evidence_refs:
                    invalid = True
                    break
                value = Decimal(fact.value)
                if not value.is_finite() or value < 0 or value > 1:
                    invalid = True
                    break
                values[name] = value
        if invalid or not REQUIRED_DIMENSIONS.issubset(values):
            continue
        known_weight = sum(weights[name] for name in values)
        utility = sum(values[name] * weights[name] for name in values) / known_weight
        scored.append((utility, candidate.entity_ref))
    return tuple(ref for _, ref in sorted(scored, key=lambda item: (-item[0], item[1])))


def _case(vertical: str, locale: str, seed: int, index: int) -> BenchmarkCase:
    rng = random.Random(f"ranking-v2:{seed}:{vertical}:{locale}:{index}")
    scenario = SCENARIOS[index % len(SCENARIOS)]
    refs = tuple(f"variant:{vertical}-{locale}-{seed}-{index}-{suffix}" for suffix in "abc")
    candidates = tuple(
        _candidate(ref, tuple(rng.randint(10, 98) for _ in DIMENSIONS))
        for ref in refs
    )
    blocked_ref: str | None = None
    partial_refs: tuple[str, ...] = ()
    first = candidates[0]
    dimensions = dict(first.dimensions)
    if scenario == "optional_unknown":
        transformed = []
        for candidate in candidates:
            facts = dict(candidate.dimensions)
            facts["product_quality"] = ScoreFact("unknown")
            facts["value"] = ScoreFact("unknown")
            transformed.append(RankingCandidateFacts(candidate.entity_ref, "ELIGIBLE", facts))
        candidates = tuple(transformed)
        partial_refs = refs
    elif scenario == "need_fit_unknown":
        dimensions["need_fit"] = ScoreFact("unknown")
        candidates = (RankingCandidateFacts(first.entity_ref, "ELIGIBLE", dimensions), *candidates[1:])
        blocked_ref = first.entity_ref
    elif scenario == "evidence_unknown":
        dimensions["evidence"] = ScoreFact("unknown")
        candidates = (RankingCandidateFacts(first.entity_ref, "ELIGIBLE", dimensions), *candidates[1:])
        blocked_ref = first.entity_ref
    elif scenario == "known_unsourced_required":
        dimensions["need_fit"] = _known(90, "unused", sourced=False)
        candidates = (RankingCandidateFacts(first.entity_ref, "ELIGIBLE", dimensions), *candidates[1:])
        blocked_ref = first.entity_ref
    elif scenario == "invalid_optional":
        dimensions["value"] = ScoreFact("invalid")
        candidates = (RankingCandidateFacts(first.entity_ref, "ELIGIBLE", dimensions), *candidates[1:])
        blocked_ref = first.entity_ref
    elif scenario == "ineligible":
        candidates = (RankingCandidateFacts(first.entity_ref, "EXCLUDED", dimensions), *candidates[1:])
        blocked_ref = first.entity_ref
    elif scenario == "tie_stability":
        candidates = tuple(_candidate(ref, (70, 70, 70, 70)) for ref in reversed(refs))
    expected = _oracle_order(vertical, candidates)
    return BenchmarkCase(
        case_id=f"{vertical}:{locale}:{seed}:{index}:{scenario}",
        vertical=vertical,
        scenario=scenario,
        candidates=candidates,
        expected_order=expected,
        blocked_ref=blocked_ref,
        partial_refs=partial_refs,
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


def run_benchmark(manifest_path: Path) -> dict[str, Any]:
    manifest = _load_manifest(manifest_path)
    cases = generate_cases(manifest)
    exact = top1 = top1_cases = 0
    blocked_ranked = {scenario: 0 for scenario in (
        "need_fit_unknown", "evidence_unknown", "known_unsourced_required", "invalid_optional", "ineligible"
    )}
    partial_expected = partial_disclosed = provenance_complete = 0
    deterministic_failures = commission_failures = 0
    identity: list[dict[str, Any]] = []
    for case in cases:
        request = RankingRequest(case.case_id, case.vertical)
        first = rank_products(request, case.candidates)
        second = rank_products(request, case.candidates)
        actual = first.ranked_entity_refs
        exact += actual == case.expected_order
        if case.expected_order:
            top1_cases += 1
            top1 += bool(actual) and actual[0] == case.expected_order[0]
        deterministic_failures += (
            first.result_digest != second.result_digest
            or first.ranked_entity_refs != second.ranked_entity_refs
        )
        if case.scenario == "commission_mutation":
            # La commission est volontairement absente du contrat moteur : deux
            # mutations commerciales externes doivent laisser le résultat intact.
            commission_a = {ref: Decimal(index) for index, ref in enumerate(actual)}
            commission_b = {ref: Decimal(len(actual) - index) for index, ref in enumerate(actual)}
            commission_failures += commission_a == commission_b or first.result_digest != second.result_digest
        by_ref = {item.entity_ref: item for item in first.candidates}
        if case.blocked_ref and by_ref[case.blocked_ref].status == "RANKED":
            blocked_ranked[case.scenario] += 1
        for ref in case.partial_refs:
            partial_expected += 1
            item = by_ref[ref]
            expected_reasons = {
                "evidence_scoped_partial_ranking",
                "dimension_unknown:product_quality",
                "dimension_unknown:value",
            }
            partial_disclosed += item.status == "RANKED" and expected_reasons.issubset(item.reason_codes)
        for item in first.candidates:
            if item.status != "RANKED":
                continue
            provenance_complete += all(
                dimension.status != "KNOWN" or bool(dimension.evidence_refs)
                for dimension in item.dimensions
            ) and all(
                any(dimension.name == required and dimension.status == "KNOWN" for dimension in item.dimensions)
                for required in REQUIRED_DIMENSIONS
            )
        identity.append({"case_id": case.case_id, "expected": case.expected_order, "actual": actual})
    ranked_total = sum(len(case.expected_order) for case in cases)
    lower, upper = _wilson(exact, len(cases))
    top1_rate = top1 / top1_cases
    partial_rate = partial_disclosed / partial_expected
    provenance_rate = provenance_complete / ranked_total
    support = {
        "total_cases": len(cases),
        "optional_unknown_cases": sum(case.scenario == "optional_unknown" for case in cases),
        "required_unknown_cases": sum(case.scenario in {"need_fit_unknown", "evidence_unknown"} for case in cases),
        "known_unsourced_required_cases": sum(case.scenario == "known_unsourced_required" for case in cases),
        "invalid_optional_cases": sum(case.scenario == "invalid_optional" for case in cases),
        "ineligible_cases": sum(case.scenario == "ineligible" for case in cases),
        "commission_mutation_cases": sum(case.scenario == "commission_mutation" for case in cases),
    }
    support_ok = all(
        support[key] >= minimum
        for key, minimum in manifest["minimum_statistical_support"].items()
    )
    gates = manifest["engineering_gates"]
    engineering_gates = {
        "order_accuracy_ci95_lower_min": lower >= gates["order_accuracy_ci95_lower_min"],
        "top1_accuracy_min": top1_rate >= gates["top1_accuracy_min"],
        "required_unknown_ranked_max": (
            blocked_ranked["need_fit_unknown"] + blocked_ranked["evidence_unknown"]
        ) <= gates["required_unknown_ranked_max"],
        "known_unsourced_required_ranked_max": blocked_ranked["known_unsourced_required"] <= gates["known_unsourced_required_ranked_max"],
        "invalid_optional_ranked_max": blocked_ranked["invalid_optional"] <= gates["invalid_optional_ranked_max"],
        "ineligible_ranked_max": blocked_ranked["ineligible"] <= gates["ineligible_ranked_max"],
        "optional_unknown_disclosure_min": partial_rate >= gates["optional_unknown_disclosure_min"],
        "provenance_completeness_min": provenance_rate >= gates["provenance_completeness_min"],
        "determinism_failures_max": deterministic_failures <= gates["determinism_failures_max"],
        "commission_invariance_failures_max": commission_failures <= gates["commission_invariance_failures_max"],
    }
    passed = support_ok and all(engineering_gates.values())
    return {
        "schema_version": SCHEMA_VERSION,
        "policy": POLICY,
        "support": support,
        "metrics": {
            "order_accuracy": {
                "successes": exact,
                "cases": len(cases),
                "rate": round(exact / len(cases), 8),
                "ci95_lower": round(lower, 8),
                "ci95_upper": round(upper, 8),
            },
            "top1_accuracy": round(top1_rate, 8),
            "required_unknown_ranked": blocked_ranked["need_fit_unknown"] + blocked_ranked["evidence_unknown"],
            "known_unsourced_required_ranked": blocked_ranked["known_unsourced_required"],
            "invalid_optional_ranked": blocked_ranked["invalid_optional"],
            "ineligible_ranked": blocked_ranked["ineligible"],
            "optional_unknown_disclosure": round(partial_rate, 8),
            "provenance_completeness": round(provenance_rate, 8),
            "determinism_failures": deterministic_failures,
            "commission_invariance_failures": commission_failures,
        },
        "engineering_gates": engineering_gates,
        "engineering_passed": passed,
        "claim_boundary": manifest["claim_boundary"],
        "quality_status": {
            "autonomous_quality_lab": "PASS" if passed else "FAIL",
            "external_human_ground_truth": "NO_EXTERNAL_HUMAN_GROUND_TRUTH",
            "subjective_dimensions": "NOT_INDEPENDENTLY_VALIDATED",
            "human_validation_required": False,
            "external_limitation_blocking": False,
        },
        "passed": passed,
        "evaluation_id": "sha256:" + hashlib.sha256(_canonical(identity).encode()).hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Quality Lab Product Ranking v2")
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = run_benchmark(args.manifest)
    rendered = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    if args.strict and not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
