"""Holdout synthétique indépendant Offer Optimization Phase 8."""

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

from app.offer_optimization.engine import (
    AvailabilityFact,
    MoneyFact,
    OfferCandidateFacts,
    OptimizationRequest,
    ReturnPolicyFact,
    ScoreFact,
    optimize_offers,
)


SCHEMA_VERSION = "offer-optimization-benchmark/v2"
MANIFEST_VERSION = "offer-optimization-benchmark-manifest/v1"
GENERATOR_VERSION = "filon-offer-optimization-holdout/v2"
LIMITATION = "NO_EXTERNAL_HUMAN_OFFER_PREFERENCE_GROUND_TRUTH"
VERTICALS = ("smartphones", "laptops", "audio", "fashion", "appliances_hvac", "tyres")
LOCALES = ("fr", "nl", "en")
SCENARIOS = (
    "exact_objective",
    "unknown_shipping",
    "unknown_cashback",
    "unknown_returns",
    "cashback_currency_conflict",
    "stale_offer",
    "out_of_stock",
    "returns_not_accepted",
    "commission_mutation",
    "tie_stability",
)


class OfferOptimizationBenchmarkError(ValueError):
    """Manifest ou corpus Offer Optimization hors contrat."""


@dataclass(frozen=True)
class BenchmarkCase:
    case_id: str
    scenario: str
    product_ref: str
    candidates: tuple[OfferCandidateFacts, ...]
    expected_offer_ref: str | None
    commissions_a: Mapping[str, Decimal]
    commissions_b: Mapping[str, Decimal]


def _wilson(successes: int, total: int, *, z: float = 1.959963984540054) -> tuple[float, float]:
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
        raise OfferOptimizationBenchmarkError("offer optimization manifest is unreadable") from exc
    if not isinstance(manifest, Mapping) or manifest.get("schema_version") != MANIFEST_VERSION:
        raise OfferOptimizationBenchmarkError("unsupported offer optimization manifest")
    if manifest.get("limitation") != LIMITATION:
        raise OfferOptimizationBenchmarkError("ground truth limitation is missing")
    if manifest.get("policy") != "ranked_product_verified_offer_user_value_no_commission":
        raise OfferOptimizationBenchmarkError("optimization policy is invalid")
    if manifest.get("verticals") != list(VERTICALS) or manifest.get("locales") != list(LOCALES):
        raise OfferOptimizationBenchmarkError("benchmark roster is invalid")
    if manifest.get("scenarios") != list(SCENARIOS):
        raise OfferOptimizationBenchmarkError("scenario roster is invalid")
    generator = manifest.get("generator")
    if not isinstance(generator, Mapping):
        raise OfferOptimizationBenchmarkError("generator configuration is missing")
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
        raise OfferOptimizationBenchmarkError("generator configuration is invalid")
    if manifest.get("minimum_statistical_support") != {
        "total_cases": 5700,
        "unknown_cases": 2200,
        "ineligible_cases": 1700,
        "affiliate_mutation_cases": 500,
    }:
        raise OfferOptimizationBenchmarkError("minimum statistical support is invalid")
    if manifest.get("engineering_gates") != {
        "selection_accuracy_ci95_lower_min": 0.995,
        "ineligible_selected_max": 0,
        "unknown_selected_max": 0,
        "affiliate_invariance_failures_max": 0,
        "provenance_completeness_min": 1.0,
    }:
        raise OfferOptimizationBenchmarkError("engineering gates are not ratified")
    if manifest.get("evaluation_governance") != {
        "mode": "AUTONOMOUS_QUALITY_LAB",
        "progression_gate": "engineering_gates",
        "external_human_ground_truth": "NO_EXTERNAL_HUMAN_GROUND_TRUTH",
        "subjective_quality_status": "NOT_INDEPENDENTLY_VALIDATED",
        "human_validation_required": False,
    }:
        raise OfferOptimizationBenchmarkError("autonomous evaluation governance is invalid")
    return manifest


def _money(amount: int, ref: str) -> MoneyFact:
    return MoneyFact("known", f"{amount / 100:.2f}", "EUR", (ref,))


def _score(value: int, ref: str) -> ScoreFact:
    return ScoreFact("known", f"{value / 100:.2f}", (ref,))


def _offer(
    ref: str,
    product_ref: str,
    *,
    price: int,
    shipping: int,
    reliability: int,
    freshness: int,
    cashback: int = 0,
    truth_status: str = "VERIFIED",
    availability: AvailabilityFact | None = None,
    shipping_fact: MoneyFact | None = None,
    cashback_fact: MoneyFact | None = None,
    returns_fact: ReturnPolicyFact | None = None,
) -> OfferCandidateFacts:
    return OfferCandidateFacts(
        ref,
        product_ref,
        truth_status,
        _money(price, f"price:{ref}"),
        shipping_fact or _money(shipping, f"shipping:{ref}"),
        cashback_fact or _money(cashback, f"cashback:{ref}"),
        availability or AvailabilityFact("known", "in_stock", (f"stock:{ref}",)),
        returns_fact or ReturnPolicyFact("known", True, 30, (f"returns:{ref}",)),
        _score(reliability, f"reliability:{ref}"),
        _score(freshness, f"freshness:{ref}"),
    )


def _oracle(candidates: tuple[OfferCandidateFacts, ...], product_ref: str) -> str | None:
    eligible: list[tuple[Decimal, Decimal, Decimal, Decimal, str]] = []
    for candidate in candidates:
        if (
            candidate.product_ref != product_ref
            or candidate.truth_status != "VERIFIED"
            or candidate.availability.state != "known"
            or candidate.availability.value != "in_stock"
            or not candidate.availability.evidence_refs
            or candidate.price.state != "known"
            or candidate.shipping.state != "known"
            or candidate.cashback.state != "known"
            or not candidate.price.evidence_refs
            or not candidate.shipping.evidence_refs
            or not candidate.cashback.evidence_refs
            or len(
                {
                    candidate.price.currency,
                    candidate.shipping.currency,
                    candidate.cashback.currency,
                }
            ) != 1
            or candidate.returns.state != "known"
            or candidate.returns.accepted is not True
            or candidate.returns.period_days is None
            or not candidate.returns.evidence_refs
            or candidate.merchant_reliability.state != "known"
            or candidate.freshness.state != "known"
            or not candidate.merchant_reliability.evidence_refs
            or not candidate.freshness.evidence_refs
        ):
            continue
        total = Decimal(candidate.price.amount_decimal or "0") + Decimal(
            candidate.shipping.amount_decimal or "0"
        )
        cashback = Decimal(candidate.cashback.amount_decimal or "0")
        if cashback > total:
            continue
        eligible.append(
            (
                total - cashback,
                -Decimal(candidate.merchant_reliability.value or "0"),
                -Decimal(candidate.returns.period_days),
                -Decimal(candidate.freshness.value or "0"),
                candidate.offer_ref,
            )
        )
    return min(eligible)[4] if eligible else None


def _case(vertical: str, locale: str, seed: int, index: int) -> BenchmarkCase:
    rng = random.Random(f"offer:{seed}:{vertical}:{locale}:{index}")
    scenario = SCENARIOS[index % len(SCENARIOS)]
    product_ref = f"variant:{vertical}-{locale}-{seed}-{index}"
    refs = tuple(f"offer:{vertical}-{locale}-{seed}-{index}-{suffix}" for suffix in "abc")
    candidates = tuple(
        _offer(
            ref,
            product_ref,
            price=rng.randint(10_000, 100_000),
            shipping=rng.randint(0, 2_000),
            cashback=rng.randint(0, 1_000),
            reliability=rng.randint(60, 99),
            freshness=rng.randint(60, 99),
        )
        for ref in refs
    )
    if scenario == "unknown_shipping":
        first = candidates[0]
        candidates = (
            _offer(
                first.offer_ref,
                product_ref,
                price=1,
                shipping=0,
                reliability=99,
                freshness=99,
                shipping_fact=MoneyFact("unknown"),
            ),
            *candidates[1:],
        )
    elif scenario == "unknown_cashback":
        first = candidates[0]
        candidates = (
            _offer(
                first.offer_ref,
                product_ref,
                price=1,
                shipping=0,
                reliability=99,
                freshness=99,
                cashback_fact=MoneyFact("unknown"),
            ),
            *candidates[1:],
        )
    elif scenario == "unknown_returns":
        first = candidates[0]
        candidates = (
            _offer(
                first.offer_ref,
                product_ref,
                price=1,
                shipping=0,
                reliability=99,
                freshness=99,
                returns_fact=ReturnPolicyFact("unknown"),
            ),
            *candidates[1:],
        )
    elif scenario == "cashback_currency_conflict":
        first = candidates[0]
        candidates = (
            _offer(
                first.offer_ref,
                product_ref,
                price=1,
                shipping=0,
                reliability=99,
                freshness=99,
                cashback_fact=MoneyFact("known", "0.01", "USD", (f"cashback:{first.offer_ref}",)),
            ),
            *candidates[1:],
        )
    elif scenario == "stale_offer":
        candidates = (
            _offer(refs[0], product_ref, price=1, shipping=0, reliability=99, freshness=99, truth_status="STALE"),
            *candidates[1:],
        )
    elif scenario == "out_of_stock":
        candidates = (
            _offer(
                refs[0],
                product_ref,
                price=1,
                shipping=0,
                reliability=99,
                freshness=99,
                availability=AvailabilityFact("known", "out_of_stock", (f"stock:{refs[0]}",)),
            ),
            *candidates[1:],
        )
    elif scenario == "returns_not_accepted":
        candidates = (
            _offer(
                refs[0],
                product_ref,
                price=1,
                shipping=0,
                reliability=99,
                freshness=99,
                returns_fact=ReturnPolicyFact("known", False, None, (f"returns:{refs[0]}",)),
            ),
            *candidates[1:],
        )
    elif scenario == "tie_stability":
        candidates = tuple(
            _offer(ref, product_ref, price=10_000, shipping=500, reliability=90, freshness=90)
            for ref in reversed(refs)
        )
    expected = _oracle(candidates, product_ref)
    return BenchmarkCase(
        f"{vertical}:{locale}:{seed}:{index}:{scenario}",
        scenario,
        product_ref,
        candidates,
        expected,
        {refs[0]: Decimal("1"), refs[1]: Decimal("0"), refs[2]: Decimal("0")},
        {refs[0]: Decimal("0"), refs[1]: Decimal("0"), refs[2]: Decimal("1")},
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


def _legacy(case: BenchmarkCase, commissions: Mapping[str, Decimal]) -> str | None:
    scored = []
    for candidate in case.candidates:
        price = Decimal(candidate.price.amount_decimal or "0")
        shipping = Decimal(candidate.shipping.amount_decimal or "0")
        score = -(price + shipping) + commissions[candidate.offer_ref] * Decimal("1000000")
        scored.append((score, candidate.offer_ref))
    return max(scored)[1] if scored else None


def run_benchmark(path: Path, *, adapter: str = "offer_optimization") -> dict[str, Any]:
    manifest = _load_manifest(path)
    cases = generate_cases(manifest)
    exact = ineligible_selected = unknown_selected = affiliate_failures = provenance_complete = 0
    identity: list[dict[str, str | None]] = []
    for case in cases:
        if adapter == "offer_optimization":
            request = OptimizationRequest(case.case_id, "RANKED_PRODUCTS", case.product_ref, 1)
            first = optimize_offers(request, case.candidates)
            second = optimize_offers(request, case.candidates)
            actual = first.selected_offer_ref
            invariant = first.result_digest == second.result_digest and actual == second.selected_offer_ref
            statuses = {item.offer_ref: item.status for item in first.evaluations}
            evidence_ok = all(
                item.status != "SELECTED" or bool(item.evidence_refs) for item in first.evaluations
            )
        elif adapter == "legacy_commercial":
            actual = _legacy(case, case.commissions_a)
            invariant = actual == _legacy(case, case.commissions_b)
            statuses = {candidate.offer_ref: "SELECTED" if candidate.offer_ref == actual else "ELIGIBLE" for candidate in case.candidates}
            evidence_ok = False
        else:
            raise OfferOptimizationBenchmarkError("benchmark adapter is unknown")
        exact += actual == case.expected_offer_ref
        ineligible_selected += sum(
            (
                candidate.truth_status != "VERIFIED"
                or candidate.availability.state != "known"
                or candidate.availability.value != "in_stock"
                or (
                    candidate.returns.state == "known"
                    and candidate.returns.accepted is False
                )
            )
            and statuses.get(candidate.offer_ref) == "SELECTED"
            for candidate in case.candidates
        )
        unknown_selected += sum(
            (
                candidate.shipping.state != "known"
                or not candidate.shipping.evidence_refs
                or candidate.cashback.state != "known"
                or not candidate.cashback.evidence_refs
                or len(
                    {
                        candidate.price.currency,
                        candidate.shipping.currency,
                        candidate.cashback.currency,
                    }
                ) != 1
                or candidate.returns.state != "known"
                or candidate.returns.accepted is not True
                or candidate.returns.period_days is None
                or not candidate.returns.evidence_refs
                or candidate.merchant_reliability.state != "known"
            )
            and statuses.get(candidate.offer_ref) == "SELECTED"
            for candidate in case.candidates
        )
        affiliate_failures += not invariant
        provenance_complete += evidence_ok
        identity.append({"case_id": case.case_id, "expected": case.expected_offer_ref, "actual": actual})
    lower, upper = _wilson(exact, len(cases))
    support = {
        "total_cases": len(cases),
        "unknown_cases": sum(
            case.scenario
            in {"unknown_shipping", "unknown_cashback", "unknown_returns", "cashback_currency_conflict"}
            for case in cases
        ),
        "ineligible_cases": sum(
            case.scenario in {"stale_offer", "out_of_stock", "returns_not_accepted"}
            for case in cases
        ),
        "affiliate_mutation_cases": sum(case.scenario == "commission_mutation" for case in cases),
    }
    support_ok = all(
        support[key] >= minimum for key, minimum in manifest["minimum_statistical_support"].items()
    )
    gates = manifest["engineering_gates"]
    provenance_rate = provenance_complete / len(cases)
    engineering_gates = {
        "selection_accuracy_ci95_lower_min": lower >= gates["selection_accuracy_ci95_lower_min"],
        "ineligible_selected_max": ineligible_selected <= gates["ineligible_selected_max"],
        "unknown_selected_max": unknown_selected <= gates["unknown_selected_max"],
        "affiliate_invariance_failures_max": affiliate_failures <= gates["affiliate_invariance_failures_max"],
        "provenance_completeness_min": provenance_rate >= gates["provenance_completeness_min"],
    }
    passed = support_ok and all(engineering_gates.values())
    return {
        "schema_version": SCHEMA_VERSION,
        "adapter": adapter,
        "limitation": LIMITATION,
        "support": support,
        "metrics": {
            "selection_accuracy": {
                "successes": exact,
                "cases": len(cases),
                "rate": round(exact / len(cases), 8),
                "ci95_lower": round(lower, 8),
                "ci95_upper": round(upper, 8),
            },
            "ineligible_selected": ineligible_selected,
            "unknown_selected": unknown_selected,
            "affiliate_invariance_failures": affiliate_failures,
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
            json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Benchmark autonome Offer Optimization Phase 8")
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--adapter", choices=("offer_optimization", "legacy_commercial"), default="offer_optimization")
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
