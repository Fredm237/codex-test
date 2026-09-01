"""Holdout synthétique indépendant Product Ranking Phase 7."""

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
    RankingCandidateFacts,
    RankingRequest,
    ScoreFact,
    rank_products,
)


SCHEMA_VERSION = "product-ranking-benchmark/v1"
MANIFEST_VERSION = "product-ranking-benchmark-manifest/v1"
GENERATOR_VERSION = "filon-product-ranking-holdout/v1"
LIMITATION = "NO_EXTERNAL_HUMAN_PREFERENCE_GROUND_TRUTH"
VERTICALS = ("smartphones", "laptops", "audio", "fashion", "appliances_hvac", "tyres")
LOCALES = ("fr", "nl", "en")
SCENARIOS = (
    "exact_order",
    "vertical_flip",
    "unknown_dimension",
    "excluded_reentry",
    "commission_mutation",
    "tie_stability",
)
ORACLE_WEIGHTS = {
    "smartphones": (35, 30, 25, 10),
    "laptops": (35, 30, 25, 10),
    "audio": (30, 35, 25, 10),
    "fashion": (35, 25, 25, 15),
    "appliances_hvac": (30, 35, 25, 10),
    "tyres": (35, 35, 20, 10),
}


class ProductRankingBenchmarkError(ValueError):
    """Manifest ou corpus Product Ranking hors contrat."""


@dataclass(frozen=True)
class BenchmarkCase:
    case_id: str
    vertical: str
    locale: str
    scenario: str
    candidates: tuple[RankingCandidateFacts, ...]
    expected_order: tuple[str, ...]
    commissions_a: Mapping[str, Decimal]
    commissions_b: Mapping[str, Decimal]


def _wilson(successes: int, total: int, *, z: float = 1.959963984540054) -> tuple[float, float]:
    if total <= 0:
        raise ProductRankingBenchmarkError("metric denominator must be positive")
    probability = successes / total
    denominator = 1 + z * z / total
    center = (probability + z * z / (2 * total)) / denominator
    margin = z * math.sqrt(probability * (1 - probability) / total + z * z / (4 * total * total)) / denominator
    return max(0.0, center - margin), min(1.0, center + margin)


def _load_manifest(path: Path) -> Mapping[str, Any]:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProductRankingBenchmarkError("product ranking manifest is unreadable") from exc
    if not isinstance(manifest, Mapping) or manifest.get("schema_version") != MANIFEST_VERSION:
        raise ProductRankingBenchmarkError("unsupported product ranking manifest")
    if manifest.get("limitation") != LIMITATION:
        raise ProductRankingBenchmarkError("human preference limitation is missing")
    if manifest.get("policy") != "eligible_product_first_vertical_aware_no_commission":
        raise ProductRankingBenchmarkError("ranking policy is invalid")
    if manifest.get("verticals") != list(VERTICALS) or manifest.get("locales") != list(LOCALES):
        raise ProductRankingBenchmarkError("benchmark roster is invalid")
    if manifest.get("scenarios") != list(SCENARIOS):
        raise ProductRankingBenchmarkError("scenario roster is invalid")
    generator = manifest.get("generator")
    if not isinstance(generator, Mapping):
        raise ProductRankingBenchmarkError("generator configuration is missing")
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
        raise ProductRankingBenchmarkError("generator configuration is invalid")
    if manifest.get("minimum_statistical_support") != {
        "total_cases": 4500,
        "unknown_cases": 700,
        "ineligible_cases": 700,
        "affiliate_mutation_cases": 700,
    }:
        raise ProductRankingBenchmarkError("minimum statistical support is invalid")
    if manifest.get("engineering_gates") != {
        "order_accuracy_ci95_lower_min": 0.995,
        "top1_accuracy_min": 1.0,
        "ineligible_ranked_max": 0,
        "unknown_ranked_max": 0,
        "affiliate_invariance_failures_max": 0,
        "provenance_completeness_min": 1.0,
    }:
        raise ProductRankingBenchmarkError("engineering gates are not ratified")
    if manifest.get("evaluation_governance") != {
        "mode": "AUTONOMOUS_QUALITY_LAB",
        "progression_gate": "engineering_gates",
        "external_human_ground_truth": "NO_EXTERNAL_HUMAN_GROUND_TRUTH",
        "subjective_quality_status": "NOT_INDEPENDENTLY_VALIDATED",
        "human_validation_required": False,
    }:
        raise ProductRankingBenchmarkError("autonomous evaluation governance is invalid")
    return manifest


def _fact(value: int, ref: str) -> ScoreFact:
    return ScoreFact("known", f"{value / 100:.2f}", (ref,))


def _candidate(ref: str, scores: tuple[int, int, int, int], *, status: str = "ELIGIBLE") -> RankingCandidateFacts:
    return RankingCandidateFacts(
        ref,
        status,
        {
            "need_fit": _fact(scores[0], f"need:{ref}"),
            "product_quality": _fact(scores[1], f"quality:{ref}"),
            "value": _fact(scores[2], f"value:{ref}"),
            "evidence": _fact(scores[3], f"evidence:{ref}"),
        },
    )


def _oracle_order(vertical: str, candidates: tuple[RankingCandidateFacts, ...]) -> tuple[str, ...]:
    weights = ORACLE_WEIGHTS[vertical]
    scored = []
    for candidate in candidates:
        if candidate.eligibility_status != "ELIGIBLE":
            continue
        values: list[int] = []
        for key in ("need_fit", "product_quality", "value", "evidence"):
            fact = candidate.dimensions[key]
            if fact.state != "known" or fact.value is None or not fact.evidence_refs:
                break
            values.append(int(Decimal(fact.value) * 100))
        if len(values) != 4:
            continue
        scored.append((sum(value * weight for value, weight in zip(values, weights, strict=True)), candidate.entity_ref))
    return tuple(item[1] for item in sorted(scored, key=lambda item: (-item[0], item[1])))


def _case(vertical: str, locale: str, seed: int, index: int) -> BenchmarkCase:
    rng = random.Random(f"ranking:{seed}:{vertical}:{locale}:{index}")
    scenario = SCENARIOS[index % len(SCENARIOS)]
    refs = tuple(f"variant:{vertical}-{locale}-{seed}-{index}-{suffix}" for suffix in "abc")
    scores = [tuple(rng.randint(20, 95) for _ in range(4)) for _ in refs]
    candidates = tuple(_candidate(ref, score) for ref, score in zip(refs, scores, strict=True))
    if scenario == "vertical_flip":
        candidates = (
            _candidate(refs[0], (100, 0, 100, 100)),
            _candidate(refs[1], (0, 100, 100, 100)),
            _candidate(refs[2], (20, 20, 20, 20)),
        )
    elif scenario == "unknown_dimension":
        first = candidates[0]
        dimensions = dict(first.dimensions)
        dimensions["need_fit"] = ScoreFact("unknown")
        candidates = (RankingCandidateFacts(first.entity_ref, "ELIGIBLE", dimensions), *candidates[1:])
    elif scenario == "excluded_reentry":
        candidates = (_candidate(refs[0], (100, 100, 100, 100), status="EXCLUDED"), *candidates[1:])
    elif scenario == "tie_stability":
        candidates = tuple(_candidate(ref, (70, 70, 70, 70)) for ref in reversed(refs))
    expected = _oracle_order(vertical, candidates)
    # Mutation volontairement extrême : un moteur qui mélange commission et
    # pertinence doit changer d'ordre et être rejeté par le benchmark.
    commissions_a = {refs[0]: Decimal("0"), refs[1]: Decimal("0"), refs[2]: Decimal("1")}
    commissions_b = {refs[0]: Decimal("1"), refs[1]: Decimal("0"), refs[2]: Decimal("0")}
    return BenchmarkCase(
        f"{vertical}:{locale}:{seed}:{index}:{scenario}",
        vertical,
        locale,
        scenario,
        candidates,
        expected,
        commissions_a,
        commissions_b,
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


def _legacy_order(case: BenchmarkCase, commissions: Mapping[str, Decimal]) -> tuple[str, ...]:
    scored = []
    for candidate in case.candidates:
        values = []
        for fact in candidate.dimensions.values():
            values.append(Decimal(fact.value) if fact.state == "known" and fact.value else Decimal("0.50"))
        # Simule l'ancien mélange dangereux : moyenne universelle et commission.
        score = sum(values) / 4 + commissions[candidate.entity_ref]
        scored.append((score, candidate.entity_ref))
    return tuple(item[1] for item in sorted(scored, key=lambda item: (-item[0], item[1])))


def run_benchmark(manifest_path: Path, *, adapter: str = "product_ranking") -> dict[str, Any]:
    manifest = _load_manifest(manifest_path)
    cases = generate_cases(manifest)
    exact = top1 = ineligible_ranked = unknown_ranked = affiliate_failures = provenance_complete = 0
    identity = []
    for case in cases:
        if adapter == "product_ranking":
            first = rank_products(RankingRequest(case.case_id, case.vertical), case.candidates)
            second = rank_products(RankingRequest(case.case_id, case.vertical), case.candidates)
            actual = first.ranked_entity_refs
            invariant = first.result_digest == second.result_digest and actual == second.ranked_entity_refs
            statuses = {item.entity_ref: item.status for item in first.candidates}
            evidence_ok = all(
                item.status != "RANKED" or all(dimension.evidence_refs for dimension in item.dimensions)
                for item in first.candidates
            )
        elif adapter == "legacy_universal_commercial":
            actual = _legacy_order(case, case.commissions_a)
            invariant = actual == _legacy_order(case, case.commissions_b)
            statuses = {candidate.entity_ref: "RANKED" for candidate in case.candidates}
            evidence_ok = False
        else:
            raise ProductRankingBenchmarkError("benchmark adapter is unknown")
        exact += actual == case.expected_order
        top1 += bool(actual) and bool(case.expected_order) and actual[0] == case.expected_order[0]
        ineligible_ranked += sum(
            candidate.eligibility_status != "ELIGIBLE" and statuses.get(candidate.entity_ref) == "RANKED"
            for candidate in case.candidates
        )
        unknown_ranked += sum(
            any(fact.state != "known" for fact in candidate.dimensions.values())
            and statuses.get(candidate.entity_ref) == "RANKED"
            for candidate in case.candidates
        )
        affiliate_failures += not invariant
        provenance_complete += evidence_ok
        identity.append({"case_id": case.case_id, "expected": case.expected_order, "actual": actual})
    lower, upper = _wilson(exact, len(cases))
    top1_rate = top1 / len(cases)
    provenance_rate = provenance_complete / len(cases)
    support = {
        "total_cases": len(cases),
        "unknown_cases": sum(case.scenario == "unknown_dimension" for case in cases),
        "ineligible_cases": sum(case.scenario == "excluded_reentry" for case in cases),
        "affiliate_mutation_cases": sum(case.scenario == "commission_mutation" for case in cases),
    }
    support_ok = all(
        support[key] >= minimum for key, minimum in manifest["minimum_statistical_support"].items()
    )
    gates = manifest["engineering_gates"]
    engineering_gates = {
        "order_accuracy_ci95_lower_min": lower >= gates["order_accuracy_ci95_lower_min"],
        "top1_accuracy_min": top1_rate >= gates["top1_accuracy_min"],
        "ineligible_ranked_max": ineligible_ranked <= gates["ineligible_ranked_max"],
        "unknown_ranked_max": unknown_ranked <= gates["unknown_ranked_max"],
        "affiliate_invariance_failures_max": affiliate_failures <= gates["affiliate_invariance_failures_max"],
        "provenance_completeness_min": provenance_rate >= gates["provenance_completeness_min"],
    }
    engineering_passed = support_ok and all(engineering_gates.values())
    phase_gate_passed = engineering_passed
    return {
        "schema_version": SCHEMA_VERSION,
        "adapter": adapter,
        "limitation": LIMITATION,
        "support": support,
        "metrics": {
            "order_accuracy": {"successes": exact, "cases": len(cases), "rate": round(exact / len(cases), 8), "ci95_lower": round(lower, 8), "ci95_upper": round(upper, 8)},
            "top1_accuracy": round(top1_rate, 8),
            "ineligible_ranked": ineligible_ranked,
            "unknown_ranked": unknown_ranked,
            "affiliate_invariance_failures": affiliate_failures,
            "provenance_completeness": round(provenance_rate, 8),
        },
        "engineering_gates": engineering_gates,
        "engineering_passed": engineering_passed,
        "quality_status": {
            "autonomous_quality_lab": "PASS" if engineering_passed else "FAIL",
            "external_human_ground_truth": "NO_EXTERNAL_HUMAN_GROUND_TRUTH",
            "subjective_dimensions": "NOT_INDEPENDENTLY_VALIDATED",
            "human_validation_required": False,
            "external_limitation_blocking": False,
        },
        "phase_gate_passed": phase_gate_passed,
        "passed": phase_gate_passed,
        "evaluation_id": "sha256:" + hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Benchmark autonome Product Ranking Phase 7")
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--adapter", choices=("product_ranking", "legacy_universal_commercial"), default="product_ranking")
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
