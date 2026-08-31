"""Laboratoire autonome, déterministe et transparent de qualité FILON.

Ce laboratoire ne remplace pas une vérité humaine indépendante. Il qualifie
uniquement ce qui possède un oracle calculable : contrats, identifiants,
normalisations, contraintes et comportements d'abstention. Les dimensions
subjectives restent explicitement provisoires et non bloquantes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Mapping, Sequence

from app.intelligence.contracts import CoreOfferSnapshot
from app.intelligence.general_decision import compose_general_plan
from app.intelligence.intent_resolution import resolve_intent
from app.product_graph.resolution import (
    attach_offer_to_candidates,
    resolve_entity_pair,
    resolve_variant_observation,
)
from app.services import product_role, taxonomy
from app.services.catalog_grouping import normalize_ean
from app.services.currency import normalize_currency_code
from app.services.freshness import offer_observation_is_fresh
from app.services.source_normalization import parse_price, parse_tristate_bool

from .integrity import atomic_write_text, canonical_json


SCHEMA_VERSION = "autonomous-quality-report/v1"
GENERATOR_VERSION = "filon-adversarial-holdout/v1"
LIMITATION = "NO_EXTERNAL_HUMAN_GROUND_TRUTH"
ALLOWED_QUALITY_STATUSES = frozenset(
    {
        "DETERMINISTICALLY_VERIFIED",
        "CROSS_SOURCE_VERIFIED",
        "MODEL_JUDGED",
        "PROVISIONAL",
        "UNRESOLVED",
    }
)


class AutonomousQualityError(ValueError):
    """Erreur de contrat qui doit fermer la gate autonome."""


@dataclass(frozen=True)
class Check:
    case_id: str
    expected: Any
    actual: Any
    passed: bool
    truth_basis: str
    quality_status: str


def _check(
    case_id: str,
    *,
    expected: Any,
    actual: Any,
    truth_basis: str,
    quality_status: str = "DETERMINISTICALLY_VERIFIED",
) -> Check:
    if quality_status not in ALLOWED_QUALITY_STATUSES:
        raise AutonomousQualityError("unknown quality status")
    return Check(
        case_id=case_id,
        expected=expected,
        actual=actual,
        passed=actual == expected,
        truth_basis=truth_basis,
        quality_status=quality_status,
    )


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


def _regression_checks(backend_root: Path) -> list[Check]:
    path = backend_root / "tests" / "data" / "golden_catalog_v1.json"
    try:
        golden = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AutonomousQualityError("regression ground truth is unreadable") from exc
    if golden.get("version") != "1.0.0" or not isinstance(golden.get("cases"), list):
        raise AutonomousQualityError("regression ground truth contract is invalid")

    checks: list[Check] = []
    for case in golden["cases"]:
        case_id = str(case["id"])
        expected = case["expected_current"]
        actual = {
            "category": taxonomy.classify(
                case.get("merchant_category"),
                case.get("name"),
                case.get("brand"),
                case.get("merchant_name"),
            ),
            "offer_kind": taxonomy.classify_offer_kind(
                case.get("merchant_category"),
                case.get("name"),
                case.get("brand"),
                case.get("merchant_name"),
            ),
        }
        for field, expected_value in expected.items():
            checks.append(
                _check(
                    f"regression:{case_id}:{field}",
                    expected=expected_value,
                    actual=actual[field],
                    truth_basis="REGRESSION_GROUND_TRUTH",
                )
            )
        target = case.get("semantic_target", {})
        if "product_role" in target:
            understanding = product_role.understand_offer(
                name=case.get("name"),
                merchant_category=case.get("merchant_category"),
                brand=case.get("brand"),
                offer_kind=expected.get("offer_kind"),
            )
            checks.append(
                _check(
                    f"regression:{case_id}:product_role",
                    expected=target["product_role"],
                    actual=understanding["product_role"],
                    truth_basis="REGRESSION_GROUND_TRUTH",
                )
            )
    return checks


def _identifier_checks(*, seed: int, samples: int) -> list[Check]:
    rng = random.Random(seed)
    checks: list[Check] = []
    for index in range(samples):
        first = _valid_ean(rng)
        second = _different_ean(rng, first)
        base = f"seed-{seed}:identifier-{index}"
        checks.extend(
            [
                _check(
                    f"{base}:checksum",
                    expected=first,
                    actual=normalize_ean(first),
                    truth_basis="GTIN_CHECKSUM",
                ),
                _check(
                    f"{base}:same-exact-identity",
                    expected={"product_relation": "same", "variant_relation": "same"},
                    actual=resolve_entity_pair(
                        {"identifiers": {"ean": first}},
                        {"identifiers": {"gtin": first}},
                    ).prediction(),
                    truth_basis="EXACT_GLOBAL_IDENTIFIER",
                ),
                _check(
                    f"{base}:different-storage-no-merge",
                    expected={
                        "product_relation": "ambiguous",
                        "variant_relation": "ambiguous",
                    },
                    actual=resolve_entity_pair(
                        {
                            "identifiers": {"ean": first},
                            "attributes": {"storage": "128GB", "color": "black"},
                        },
                        {
                            "identifiers": {"ean": second},
                            "attributes": {"storage": "256GB", "color": "blue"},
                        },
                    ).prediction(),
                    truth_basis="DISTINCT_EXACT_IDENTIFIERS_NO_FALSE_MERGE",
                ),
                _check(
                    f"{base}:conflicting-identifiers",
                    expected="ambiguous",
                    actual=resolve_variant_observation(
                        {"identifiers": {"ean": first, "gtin": second}}
                    ).resolution,
                    truth_basis="CONTRADICTORY_EXACT_IDENTIFIERS",
                ),
            ]
        )

        bad = first[:-1] + str((int(first[-1]) + 1) % 10)
        checks.append(
            _check(
                f"{base}:invalid-checksum",
                expected="insufficient_evidence",
                actual=resolve_variant_observation(
                    {"identifiers": {"ean": bad}}
                ).resolution,
                truth_basis="GTIN_CHECKSUM",
            )
        )

        candidates = [
            {"variant_id": "variant-a", "identifiers": {"ean": first}},
            {"variant_id": "variant-b", "identifiers": {"ean": second}},
        ]
        checks.extend(
            [
                _check(
                    f"{base}:exact-attachment",
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
                    f"{base}:invalid-attachment-quarantine",
                    expected={
                        "expected_variant_id": None,
                        "eligibility": "quarantine",
                    },
                    actual=attach_offer_to_candidates(
                        {
                            "identifiers": {"ean": bad},
                            "variant_candidates": candidates,
                        }
                    ).prediction(),
                    truth_basis="GTIN_CHECKSUM",
                ),
            ]
        )
    return checks


def _normalization_checks() -> list[Check]:
    fixtures = [
        ("price:decimal-dot", 799.9, parse_price("799.90 EUR")),
        ("price:decimal-comma", 1299.0, parse_price("1.299,00 €")),
        ("price:thousands-comma", 1299.0, parse_price("1,299.00")),
        ("price:unknown", None, parse_price("unknown")),
        ("currency:lowercase", "EUR", normalize_currency_code(" eur ")),
        ("currency:wrong", None, normalize_currency_code("XYZ")),
        ("stock:yes", True, parse_tristate_bool("in stock")),
        ("stock:no", False, parse_tristate_bool("sold out")),
        ("stock:unknown", None, parse_tristate_bool("backorder maybe")),
    ]
    checks = [
        _check(
            case_id,
            expected=expected,
            actual=actual,
            truth_basis="PARSER_CONTRACT",
        )
        for case_id, expected, actual in fixtures
    ]
    now = datetime(2026, 8, 31, 12, 0, tzinfo=UTC)
    checks.extend(
        [
            _check(
                "freshness:current",
                expected=True,
                actual=offer_observation_is_fresh(now - timedelta(hours=1), now=now),
                truth_basis="TEMPORAL_INVARIANT",
            ),
            _check(
                "freshness:stale",
                expected=False,
                actual=offer_observation_is_fresh(now - timedelta(hours=80), now=now),
                truth_basis="TEMPORAL_INVARIANT",
            ),
            _check(
                "freshness:future",
                expected=False,
                actual=offer_observation_is_fresh(now + timedelta(minutes=1), now=now),
                truth_basis="TEMPORAL_INVARIANT",
            ),
        ]
    )
    return checks


def _offer(
    *,
    offer_id: int,
    price: float,
    currency: str | None,
    availability: str,
    observed_at: datetime,
) -> CoreOfferSnapshot:
    return CoreOfferSnapshot(
        offer_id=offer_id,
        catalog_product_id=offer_id,
        name="Samsung Galaxy S25 256GB",
        brand="Samsung",
        filon_category=taxonomy.TELEPHONIE,
        filon_subcategory="Smartphones",
        offer_kind=taxonomy.PHYSICAL_PRODUCT,
        price=price,
        currency=currency,
        availability=availability,
        image_url=None,
        deep_link="https://merchant.example/product",
        merchant_id=offer_id,
        merchant_name=f"Merchant {offer_id}",
        merchant_region="BE",
        observed_at=observed_at,
    )


def _decision_checks() -> list[Check]:
    now = datetime(2026, 8, 31, 12, 0, tzinfo=UTC)
    intent = resolve_intent("smartphone sous 500 EUR")
    scenarios = {
        "within-budget": _offer(
            offer_id=1,
            price=449.0,
            currency="EUR",
            availability="in_stock",
            observed_at=now - timedelta(hours=1),
        ),
        "above-budget": _offer(
            offer_id=2,
            price=649.0,
            currency="EUR",
            availability="in_stock",
            observed_at=now - timedelta(hours=1),
        ),
        "wrong-currency": _offer(
            offer_id=3,
            price=449.0,
            currency="GBP",
            availability="in_stock",
            observed_at=now - timedelta(hours=1),
        ),
        "unknown-currency": _offer(
            offer_id=4,
            price=449.0,
            currency=None,
            availability="in_stock",
            observed_at=now - timedelta(hours=1),
        ),
        "stale": _offer(
            offer_id=5,
            price=449.0,
            currency="EUR",
            availability="in_stock",
            observed_at=now - timedelta(hours=80),
        ),
        "out-of-stock": _offer(
            offer_id=6,
            price=449.0,
            currency="EUR",
            availability="out_of_stock",
            observed_at=now - timedelta(hours=1),
        ),
    }
    checks: list[Check] = []
    for name, offer in scenarios.items():
        result = compose_general_plan(intent, [offer], now=now)
        expected = "recommend" if name == "within-budget" else "abstain"
        checks.append(
            _check(
                f"decision:{name}",
                expected=expected,
                actual=result["decision"],
                truth_basis="BUDGET_CURRENCY_STOCK_FRESHNESS_CONSTRAINTS",
            )
        )
        checks.append(
            _check(
                f"decision:{name}:delivery-not-invented",
                expected="unknown",
                actual=result["delivery"],
                truth_basis="UNKNOWN_SHIPPING_INVARIANT",
            )
        )
    return checks


def cross_source_consistency(
    readings: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Expose la concordance sans transformer le consensus en preuve absolue."""

    sources = {str(reading.get("source_ref", "")).strip() for reading in readings}
    sources.discard("")
    if len(sources) != len(readings):
        raise AutonomousQualityError("cross-source readings require unique sources")
    facts = {
        (
            parse_price(str(reading.get("price", ""))),
            normalize_currency_code(reading.get("currency")),
            parse_tristate_bool(str(reading.get("stock", ""))),
        )
        for reading in readings
    }
    if not readings:
        status = "UNRESOLVED"
        signal = "SOURCE_CONFLICT"
    elif len(facts) == 1 and len(readings) >= 2:
        status = "CROSS_SOURCE_VERIFIED"
        signal = "SOURCE_AGREEMENT"
    else:
        status = "UNRESOLVED"
        signal = "SOURCE_CONFLICT"
    return {
        "SOURCE_COUNT": len(sources),
        "SOURCE_AGREEMENT": signal == "SOURCE_AGREEMENT",
        "SOURCE_CONFLICT": signal == "SOURCE_CONFLICT",
        "quality_status": status,
        "signal": signal,
    }


def _cross_source_checks() -> tuple[list[Check], list[dict[str, Any]]]:
    agreement = cross_source_consistency(
        [
            {"source_ref": "merchant:a", "price": "449.00", "currency": "EUR", "stock": "yes"},
            {"source_ref": "merchant:b", "price": "449,00", "currency": "eur", "stock": "in stock"},
        ]
    )
    conflict = cross_source_consistency(
        [
            {"source_ref": "merchant:a", "price": "449.00", "currency": "EUR", "stock": "yes"},
            {"source_ref": "merchant:b", "price": "549.00", "currency": "GBP", "stock": "no"},
        ]
    )
    checks = [
        _check(
            "cross-source:agreement",
            expected="CROSS_SOURCE_VERIFIED",
            actual=agreement["quality_status"],
            truth_basis="INDEPENDENT_SOURCE_CONCORDANCE",
            quality_status="CROSS_SOURCE_VERIFIED",
        ),
        _check(
            "cross-source:conflict-remains-unresolved",
            expected="UNRESOLVED",
            actual=conflict["quality_status"],
            truth_basis="SOURCE_CONFLICT_MUST_NOT_BE_RESOLVED",
            quality_status="UNRESOLVED",
        ),
    ]
    return checks, [agreement, conflict]


def _load_manifest(path: Path) -> dict[str, Any]:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AutonomousQualityError("autonomous manifest is unreadable") from exc
    if manifest.get("schema_version") != "autonomous-quality-manifest/v1":
        raise AutonomousQualityError("unsupported autonomous manifest")
    if manifest.get("limitation") != LIMITATION:
        raise AutonomousQualityError("human-ground-truth limitation is missing")
    holdout = manifest.get("holdout")
    if not isinstance(holdout, Mapping):
        raise AutonomousQualityError("holdout configuration is missing")
    seeds = holdout.get("seeds")
    samples = holdout.get("samples_per_seed")
    if (
        not isinstance(seeds, list)
        or not seeds
        or any(isinstance(seed, bool) or not isinstance(seed, int) for seed in seeds)
        or isinstance(samples, bool)
        or not isinstance(samples, int)
        or not 1 <= samples <= 1000
    ):
        raise AutonomousQualityError("holdout seeds or sample count are invalid")
    if holdout.get("generator_version") != GENERATOR_VERSION:
        raise AutonomousQualityError("holdout generator version is invalid")
    gates = manifest.get("gates")
    if not isinstance(gates, Mapping):
        raise AutonomousQualityError("autonomous gates are missing")
    pass_rate = gates.get("deterministic_checks_pass_rate_min")
    failure_max = gates.get("blocking_failures_max")
    if (
        isinstance(pass_rate, bool)
        or not isinstance(pass_rate, (int, float))
        or not 0.0 <= float(pass_rate) <= 1.0
        or isinstance(failure_max, bool)
        or not isinstance(failure_max, int)
        or failure_max < 0
        or gates.get("source_conflicts_must_remain_unresolved") is not True
    ):
        raise AutonomousQualityError("autonomous gates are invalid")
    model_policy = manifest.get("model_judgment")
    if not isinstance(model_policy, Mapping):
        raise AutonomousQualityError("model judgment policy is missing")
    required_fields = model_policy.get("required_audit_fields")
    if required_fields != [
        "judge_model",
        "judge_version",
        "prompt",
        "input",
        "output",
        "confidence",
    ]:
        raise AutonomousQualityError("model judgment audit fields are incomplete")
    return manifest


def build_report(manifest_path: str | Path) -> dict[str, Any]:
    path = Path(manifest_path).resolve()
    manifest = _load_manifest(path)
    backend_root = Path(__file__).resolve().parents[1]
    checks: list[Check] = []
    checks.extend(_regression_checks(backend_root))
    for seed in manifest["holdout"]["seeds"]:
        checks.extend(
            _identifier_checks(
                seed=seed,
                samples=manifest["holdout"]["samples_per_seed"],
            )
        )
    checks.extend(_normalization_checks())
    checks.extend(_decision_checks())
    cross_checks, cross_signals = _cross_source_checks()
    checks.extend(cross_checks)

    failed = [check for check in checks if not check.passed]
    unresolved = [
        check for check in checks if check.quality_status == "UNRESOLVED"
    ]
    raw_blocking_failures = [
        check
        for check in failed
        if check.quality_status != "PROVISIONAL"
    ]
    deterministic = [
        check
        for check in checks
        if check.quality_status == "DETERMINISTICALLY_VERIFIED"
    ]
    deterministic_pass_rate = (
        sum(check.passed for check in deterministic) / len(deterministic)
        if deterministic
        else 0.0
    )
    gate_failures: list[str] = []
    if deterministic_pass_rate < float(
        manifest["gates"]["deterministic_checks_pass_rate_min"]
    ):
        gate_failures.append("deterministic_pass_rate_below_threshold")
    if len(raw_blocking_failures) > manifest["gates"]["blocking_failures_max"]:
        gate_failures.append("blocking_failure_budget_exceeded")
    report_core = {
        "schema_version": SCHEMA_VERSION,
        "lab_version": manifest["lab_version"],
        "mandate_status": "AUTONOMOUS_QUALITY_LAB",
        "limitation": LIMITATION,
        "holdout": manifest["holdout"],
        "summary": {
            "checks": len(checks),
            "passed": len(checks) - len(failed),
            "failed": len(failed),
            "unresolved": len(unresolved),
            "blocking_failures": len(raw_blocking_failures),
            "deterministic_pass_rate": round(deterministic_pass_rate, 6),
            "gate_failures": gate_failures,
            "status": "PASS" if not gate_failures else "FAIL",
        },
        "quality_statuses": {
            "deterministic": "DETERMINISTICALLY_VERIFIED",
            "cross_source": "CROSS_SOURCE_VERIFIED",
            "subjective_dimensions": "PROVISIONAL",
            "conflicts": "UNRESOLVED",
        },
        "model_judgment": {
            "used": False,
            "quality_status": "PROVISIONAL",
            "reason": "deterministic_oracles_are_available_for_all_blocking_checks",
        },
        "subjective_dimensions": [
            {
                "dimension": "human_perceived_relevance",
                "quality_status": "PROVISIONAL",
                "validation": "NOT_INDEPENDENTLY_VALIDATED",
                "blocking": False,
            },
            {
                "dimension": "style_and_taste",
                "quality_status": "PROVISIONAL",
                "validation": "NOT_INDEPENDENTLY_VALIDATED",
                "blocking": False,
            },
        ],
        "cross_source_signals": cross_signals,
        "checks": [asdict(check) for check in checks],
        "phase_gate": {
            "p0_2": "PASS" if not gate_failures else "FAIL",
            "blocking": bool(gate_failures),
            "human_annotation_required": False,
            "immersive_gate_changed": False,
        },
    }
    identity_payload = {
        "manifest": manifest,
        "report": report_core,
    }
    report_core["evaluation_id"] = "sha256:" + hashlib.sha256(
        canonical_json(identity_payload).encode("utf-8")
    ).hexdigest()
    report_core["generated_at"] = datetime.now(UTC).isoformat()
    return report_core


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Évalue le FILON Autonomous Quality Lab"
    )
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output")
    parser.add_argument("--strict", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        report = build_report(args.manifest)
    except AutonomousQualityError as exc:
        print(json.dumps({"status": "INVALID", "error": str(exc)}))
        return 2
    payload = canonical_json(report) + "\n"
    if args.output:
        atomic_write_text(args.output, payload)
        print(
            canonical_json(
                {
                    "evaluation_id": report["evaluation_id"],
                    "limitation": report["limitation"],
                    "summary": report["summary"],
                }
            )
        )
    else:
        print(payload, end="")
    if args.strict and report["summary"]["status"] != "PASS":
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
