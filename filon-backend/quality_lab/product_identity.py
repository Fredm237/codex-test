"""Benchmark autonome Phase 1 pour l'identité produit exacte.

Les cas sont déterministes, multi-seed et aveugles au développement. Ils ne
remplacent pas une ground truth humaine. Ils prouvent les invariants qui ont
un oracle calculable : GTIN exact, abstention, variantes distinctes et
attachement d'offre sans fallback lexical.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

from app.product_graph.resolution import (
    attach_offer_to_candidates,
    resolve_entity_pair,
    resolve_variant_observation,
)

from .integrity import atomic_write_text, canonical_json


SCHEMA_VERSION = "product-identity-benchmark/v1"
MANIFEST_VERSION = "product-identity-benchmark-manifest/v1"
GENERATOR_VERSION = "filon-product-identity-holdout/v1"
LIMITATION = "NO_EXTERNAL_HUMAN_GROUND_TRUTH"
VERTICALS = (
    "smartphones",
    "laptops",
    "tv",
    "headphones_audio",
    "appliances",
)


class ProductIdentityBenchmarkError(ValueError):
    """Manifest ou regression hors contrat : le benchmark échoue fermé."""


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    vertical: str
    kind: str
    expected: Any
    actual: Any
    passed: bool
    truth_basis: str
    quality_status: str = "DETERMINISTICALLY_VERIFIED"


def _valid_ean(rng: random.Random) -> str:
    prefix = "".join(str(rng.randrange(10)) for _ in range(12))
    total = sum(
        int(character) * (3 if index % 2 == 0 else 1)
        for index, character in enumerate(reversed(prefix))
    )
    return prefix + str((10 - total % 10) % 10)


def _different_ean(rng: random.Random, current: str) -> str:
    value = _valid_ean(rng)
    while value == current:
        value = _valid_ean(rng)
    return value


def _check(
    case_id: str,
    vertical: str,
    kind: str,
    *,
    expected: Any,
    actual: Any,
    truth_basis: str,
) -> CaseResult:
    return CaseResult(
        case_id=case_id,
        vertical=vertical,
        kind=kind,
        expected=expected,
        actual=actual,
        passed=actual == expected,
        truth_basis=truth_basis,
    )


def _wilson(successes: int, total: int, *, z: float = 1.959963984540054) -> tuple[float, float]:
    if total <= 0:
        raise ProductIdentityBenchmarkError("metric denominator must be positive")
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


def _load_json(path: Path, error: str) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProductIdentityBenchmarkError(error) from exc
    if not isinstance(value, Mapping):
        raise ProductIdentityBenchmarkError(error)
    return value


def _load_manifest(path: Path) -> Mapping[str, Any]:
    manifest = _load_json(path, "product identity manifest is unreadable")
    if manifest.get("schema_version") != MANIFEST_VERSION:
        raise ProductIdentityBenchmarkError("unsupported product identity manifest")
    if manifest.get("limitation") != LIMITATION:
        raise ProductIdentityBenchmarkError("human-ground-truth limitation is missing")
    generator = manifest.get("generator")
    if not isinstance(generator, Mapping):
        raise ProductIdentityBenchmarkError("generator configuration is missing")
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
        raise ProductIdentityBenchmarkError("generator configuration is invalid")
    if manifest.get("verticals") != list(VERTICALS):
        raise ProductIdentityBenchmarkError("vertical roster is invalid")
    gates = manifest.get("gates")
    required_gates = {
        "exact_product_accuracy_ci95_lower_min",
        "variant_resolution_accuracy_ci95_lower_min",
        "offer_attachment_accuracy_ci95_lower_min",
        "false_merge_rate_ci95_upper_max",
        "blocking_failures_max",
    }
    if not isinstance(gates, Mapping) or set(gates) != required_gates:
        raise ProductIdentityBenchmarkError("benchmark gates are invalid")
    for key in required_gates - {"blocking_failures_max"}:
        value = gates[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= float(value) <= 1:
            raise ProductIdentityBenchmarkError("benchmark threshold is invalid")
    if gates["blocking_failures_max"] != 0:
        raise ProductIdentityBenchmarkError("blocking failure budget must remain zero")
    regression = manifest.get("regression_ground_truth")
    if not isinstance(regression, str) or Path(regression).name != regression:
        raise ProductIdentityBenchmarkError("regression path is invalid")
    return manifest


def _regression_checks(manifest_path: Path, manifest: Mapping[str, Any]) -> list[CaseResult]:
    regression_path = manifest_path.parent / str(manifest["regression_ground_truth"])
    regression = _load_json(regression_path, "product identity regressions are unreadable")
    if (
        regression.get("schema_version") != "product-identity-regressions/v1"
        or regression.get("truth_basis") != "REGRESSION_GROUND_TRUTH"
        or regression.get("limitation") != LIMITATION
        or not isinstance(regression.get("cases"), list)
    ):
        raise ProductIdentityBenchmarkError("product identity regressions are invalid")
    checks: list[CaseResult] = []
    case_ids: set[str] = set()
    for case in regression["cases"]:
        if not isinstance(case, Mapping):
            raise ProductIdentityBenchmarkError("regression case is invalid")
        case_id = case.get("case_id")
        vertical = case.get("vertical")
        if (
            not isinstance(case_id, str)
            or not case_id
            or case_id in case_ids
            or vertical not in VERTICALS
            or not isinstance(case.get("left"), Mapping)
            or not isinstance(case.get("right"), Mapping)
            or not isinstance(case.get("expected"), Mapping)
        ):
            raise ProductIdentityBenchmarkError("regression case is invalid")
        case_ids.add(case_id)
        checks.append(
            _check(
                f"regression:{case_id}",
                str(vertical),
                "regression",
                expected=case["expected"],
                actual=resolve_entity_pair(case["left"], case["right"]).prediction(),
                truth_basis="REGRESSION_GROUND_TRUTH",
            )
        )
    if {check.vertical for check in checks} != set(VERTICALS):
        raise ProductIdentityBenchmarkError("regressions must cover every vertical")
    return checks


def _vertical_surfaces(vertical: str, index: int) -> tuple[str, str, str]:
    values = {
        "smartphones": ("Phone Pro", "Phone Pro case", "storage"),
        "laptops": ("Notebook Air", "Notebook Air sleeve", "memory"),
        "tv": ("OLED television", "OLED computer monitor", "size"),
        "headphones_audio": ("Wireless headphones", "Bicycle helmet", "color"),
        "appliances": ("Bagless vacuum", "Replacement vacuum filter", "capacity"),
    }
    primary, negative, attribute = values[vertical]
    return f"{primary} {index}", f"{negative} {index}", attribute


def _generated_checks(*, seed: int, samples: int) -> list[CaseResult]:
    rng = random.Random(seed)
    checks: list[CaseResult] = []
    for vertical in VERTICALS:
        for index in range(samples):
            first = _valid_ean(rng)
            second = _different_ean(rng, first)
            title, hard_negative_title, attribute = _vertical_surfaces(vertical, index)
            base = f"holdout:{seed}:{vertical}:{index}"
            same = {"product_relation": "same", "variant_relation": "same"}
            ambiguous = {
                "product_relation": "ambiguous",
                "variant_relation": "ambiguous",
            }
            checks.extend(
                [
                    _check(
                        f"{base}:exact-product",
                        vertical,
                        "exact_product",
                        expected=same,
                        actual=resolve_entity_pair(
                            {
                                "name": title,
                                "brand": "Example Brand",
                                "identifiers": {"ean": first},
                            },
                            {
                                "name": title.lower(),
                                "brand": "EXAMPLE BRAND",
                                "identifiers": {"gtin": first},
                            },
                        ).prediction(),
                        truth_basis="EXACT_GLOBAL_IDENTIFIER",
                    ),
                    _check(
                        f"{base}:distinct-gtin",
                        vertical,
                        "hard_negative",
                        expected=ambiguous,
                        actual=resolve_entity_pair(
                            {"name": title, "identifiers": {"ean": first}},
                            {"name": title, "identifiers": {"ean": second}},
                        ).prediction(),
                        truth_basis="DISTINCT_GLOBAL_IDENTIFIERS",
                    ),
                    _check(
                        f"{base}:role-hard-negative",
                        vertical,
                        "hard_negative",
                        expected=ambiguous,
                        actual=resolve_entity_pair(
                            {
                                "name": title,
                                "product_role": "primary_product",
                                "identifiers": {"ean": first},
                            },
                            {
                                "name": hard_negative_title,
                                "product_role": "accessory",
                                "identifiers": {"ean": second},
                            },
                        ).prediction(),
                        truth_basis="PRODUCT_ROLE_AND_DISTINCT_IDENTIFIER",
                    ),
                    _check(
                        f"{base}:variant-attribute",
                        vertical,
                        "hard_negative",
                        expected=ambiguous,
                        actual=resolve_entity_pair(
                            {
                                "identifiers": {"ean": first},
                                "attributes": {attribute: "A"},
                            },
                            {
                                "identifiers": {"ean": second},
                                "attributes": {attribute: "B"},
                            },
                        ).prediction(),
                        truth_basis="DISTINCT_VARIANT_IDENTIFIERS",
                    ),
                    _check(
                        f"{base}:exact-variant",
                        vertical,
                        "variant_resolution",
                        expected="resolved",
                        actual=resolve_variant_observation(
                            {"identifiers": {"ean": first}}
                        ).resolution,
                        truth_basis="EXACT_GLOBAL_IDENTIFIER",
                    ),
                    _check(
                        f"{base}:conflicting-variant",
                        vertical,
                        "variant_resolution",
                        expected="ambiguous",
                        actual=resolve_variant_observation(
                            {"identifiers": {"ean": first, "gtin": second}}
                        ).resolution,
                        truth_basis="CONTRADICTORY_GLOBAL_IDENTIFIERS",
                    ),
                    _check(
                        f"{base}:missing-variant",
                        vertical,
                        "variant_resolution",
                        expected="insufficient_evidence",
                        actual=resolve_variant_observation(
                            {"identifiers": {}}
                        ).resolution,
                        truth_basis="MISSING_IDENTIFIER",
                    ),
                ]
            )
            bad = first[:-1] + str((int(first[-1]) + 1) % 10)
            checks.append(
                _check(
                    f"{base}:invalid-variant",
                    vertical,
                    "variant_resolution",
                    expected="insufficient_evidence",
                    actual=resolve_variant_observation(
                        {"identifiers": {"ean": bad}}
                    ).resolution,
                    truth_basis="GTIN_CHECKSUM",
                )
            )
            candidates = [
                {"variant_id": "variant-a", "identifiers": {"gtin": first}},
                {"variant_id": "variant-b", "identifiers": {"gtin": second}},
            ]
            checks.extend(
                [
                    _check(
                        f"{base}:offer-exact",
                        vertical,
                        "offer_attachment",
                        expected={
                            "expected_variant_id": "variant-a",
                            "eligibility": "eligible",
                        },
                        actual=attach_offer_to_candidates(
                            {
                                "identifiers": {"ean": first},
                                "variant_candidates": candidates,
                            }
                        ).prediction(),
                        truth_basis="EXACT_GLOBAL_IDENTIFIER",
                    ),
                    _check(
                        f"{base}:offer-mismatch",
                        vertical,
                        "offer_attachment",
                        expected={
                            "expected_variant_id": None,
                            "eligibility": "reject",
                        },
                        actual=attach_offer_to_candidates(
                            {
                                "identifiers": {"ean": _different_ean(rng, second)},
                                "variant_candidates": candidates,
                            }
                        ).prediction(),
                        truth_basis="CANDIDATE_MISMATCH",
                    ),
                    _check(
                        f"{base}:offer-missing",
                        vertical,
                        "offer_attachment",
                        expected={
                            "expected_variant_id": None,
                            "eligibility": "quarantine",
                        },
                        actual=attach_offer_to_candidates(
                            {
                                "identifiers": {},
                                "variant_candidates": candidates,
                            }
                        ).prediction(),
                        truth_basis="MISSING_IDENTIFIER",
                    ),
                ]
            )
    return checks


def _accuracy(checks: Sequence[CaseResult]) -> dict[str, Any]:
    passed = sum(check.passed for check in checks)
    lower, upper = _wilson(passed, len(checks))
    return {
        "cases": len(checks),
        "passed": passed,
        "rate": round(passed / len(checks), 8),
        "ci95_lower": round(lower, 8),
        "ci95_upper": round(upper, 8),
    }


def build_report(manifest_path: str | Path) -> dict[str, Any]:
    path = Path(manifest_path).resolve()
    manifest = _load_manifest(path)
    checks = _regression_checks(path, manifest)
    generator = manifest["generator"]
    for seed in generator["seeds"]:
        checks.extend(
            _generated_checks(
                seed=seed,
                samples=generator["samples_per_vertical_seed"],
            )
        )

    exact = [check for check in checks if check.kind == "exact_product"]
    variants = [check for check in checks if check.kind == "variant_resolution"]
    attachments = [check for check in checks if check.kind == "offer_attachment"]
    hard_negatives = [check for check in checks if check.kind == "hard_negative"]
    false_merges = sum(
        isinstance(check.actual, Mapping)
        and check.actual.get("product_relation") == "same"
        for check in hard_negatives
    )
    false_merge_lower, false_merge_upper = _wilson(false_merges, len(hard_negatives))
    metrics = {
        "exact_product_accuracy": _accuracy(exact),
        "variant_resolution_accuracy": _accuracy(variants),
        "offer_attachment_accuracy": _accuracy(attachments),
        "false_merge_rate": {
            "cases": len(hard_negatives),
            "false_merges": false_merges,
            "rate": round(false_merges / len(hard_negatives), 8),
            "ci95_lower": round(false_merge_lower, 8),
            "ci95_upper": round(false_merge_upper, 8),
        },
    }
    failed = [check for check in checks if not check.passed]
    gates = manifest["gates"]
    gate_results = {
        "exact_product_accuracy_ci95_lower_min": metrics["exact_product_accuracy"]["ci95_lower"]
        >= gates["exact_product_accuracy_ci95_lower_min"],
        "variant_resolution_accuracy_ci95_lower_min": metrics["variant_resolution_accuracy"]["ci95_lower"]
        >= gates["variant_resolution_accuracy_ci95_lower_min"],
        "offer_attachment_accuracy_ci95_lower_min": metrics["offer_attachment_accuracy"]["ci95_lower"]
        >= gates["offer_attachment_accuracy_ci95_lower_min"],
        "false_merge_rate_ci95_upper_max": metrics["false_merge_rate"]["ci95_upper"]
        <= gates["false_merge_rate_ci95_upper_max"],
        "blocking_failures_max": len(failed) <= gates["blocking_failures_max"],
    }
    report = {
        "schema_version": SCHEMA_VERSION,
        "benchmark_version": manifest["benchmark_version"],
        "limitation": LIMITATION,
        "quality_status": "DETERMINISTICALLY_VERIFIED",
        "generator": generator,
        "verticals": list(VERTICALS),
        "summary": {
            "status": "PASS" if all(gate_results.values()) else "FAIL",
            "cases": len(checks),
            "passed": len(checks) - len(failed),
            "failed": len(failed),
            "gate_results": gate_results,
        },
        "metrics": metrics,
        "by_vertical": {
            vertical: _accuracy(
                [check for check in checks if check.vertical == vertical]
            )
            for vertical in VERTICALS
        },
        "regressions": {
            "cases": sum(check.kind == "regression" for check in checks),
            "failed": [
                check.case_id
                for check in failed
                if check.kind == "regression"
            ],
        },
        "failures": [asdict(check) for check in failed],
    }
    report["evaluation_id"] = "sha256:" + hashlib.sha256(
        canonical_json({"manifest": manifest, "report": report}).encode("utf-8")
    ).hexdigest()
    report["generated_at"] = datetime.now(UTC).isoformat()
    return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Benchmark Product Identity FILON")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output")
    parser.add_argument("--strict", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        report = build_report(args.manifest)
    except ProductIdentityBenchmarkError as exc:
        print(json.dumps({"status": "INVALID", "error": str(exc)}))
        return 2
    payload = canonical_json(report) + "\n"
    if args.output:
        atomic_write_text(args.output, payload)
        print(
            canonical_json(
                {
                    "evaluation_id": report["evaluation_id"],
                    "summary": report["summary"],
                    "metrics": report["metrics"],
                }
            )
        )
    else:
        print(payload, end="")
    return int(args.strict and report["summary"]["status"] != "PASS")


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
