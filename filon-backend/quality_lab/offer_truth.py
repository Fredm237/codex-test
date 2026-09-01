"""Benchmark autonome Phase 3 pour les claims Offer Truth.

Le benchmark fixe l'oracle déterministe et les budgets fail-closed avant le
writer shadow. Il mesure l'exactitude sur des cas synthétiques et de
régression ; il ne prétend pas mesurer la vérité marchande externe.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping, Sequence

from .integrity import atomic_write_text, canonical_json
from app.offer_truth.extraction import EXTRACTOR_VERSION, extract_awin_offer_truth


SCHEMA_VERSION = "offer-truth-benchmark/v1"
MANIFEST_VERSION = "offer-truth-benchmark-manifest/v1"
GENERATOR_VERSION = "filon-offer-truth-holdout/v1"
POLICY_VERSION = "offer-truth-contract-oracle/v1"
LIMITATION = "NO_EXTERNAL_HUMAN_GROUND_TRUTH"
CLAIMS = ("price", "stock", "shipping", "returns", "warranty", "merchant", "freshness")


class OfferTruthBenchmarkError(ValueError):
    """Entrée benchmark hors contrat : l'évaluation échoue fermée."""


@dataclass(frozen=True)
class BenchmarkCase:
    case_id: str
    claim: str
    kind: str
    payload: Mapping[str, Any]
    expected_state: str
    expected_value: Any
    truth_basis: str


@dataclass(frozen=True)
class ClaimResult:
    state: str
    value: Any
    has_evidence: bool


def _wilson(successes: int, total: int, *, z: float = 1.959963984540054) -> tuple[float, float]:
    if total <= 0:
        raise OfferTruthBenchmarkError("metric denominator must be positive")
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
        raise OfferTruthBenchmarkError(message) from exc
    if not isinstance(value, Mapping):
        raise OfferTruthBenchmarkError(message)
    return value


def _load_manifest(path: Path) -> Mapping[str, Any]:
    manifest = _load_json(path, "offer truth manifest is unreadable")
    if manifest.get("schema_version") != MANIFEST_VERSION:
        raise OfferTruthBenchmarkError("unsupported offer truth manifest")
    if manifest.get("limitation") != LIMITATION:
        raise OfferTruthBenchmarkError("human-ground-truth limitation is missing")
    if manifest.get("claims") != list(CLAIMS):
        raise OfferTruthBenchmarkError("claim roster is invalid")

    generator = manifest.get("generator")
    if not isinstance(generator, Mapping):
        raise OfferTruthBenchmarkError("generator configuration is missing")
    seeds = generator.get("seeds")
    samples = generator.get("samples_per_seed")
    if (
        generator.get("version") != GENERATOR_VERSION
        or generator.get("development_engine_input") is not False
        or not isinstance(seeds, list)
        or len(seeds) < 3
        or any(isinstance(seed, bool) or not isinstance(seed, int) for seed in seeds)
        or isinstance(samples, bool)
        or not isinstance(samples, int)
        or not 128 <= samples <= 2_000
    ):
        raise OfferTruthBenchmarkError("generator configuration is invalid")

    required_gates = {
        "overall_correctness_ci95_lower_min",
        "known_claim_accuracy_ci95_lower_min",
        "safe_abstention_accuracy_ci95_lower_min",
        "provenance_accuracy_ci95_lower_min",
        "dangerous_fallback_rate_ci95_upper_max",
        "blocking_failures_max",
    }
    gates = manifest.get("gates")
    if not isinstance(gates, Mapping) or set(gates) != required_gates:
        raise OfferTruthBenchmarkError("benchmark gates are invalid")
    for key in required_gates - {"blocking_failures_max"}:
        value = gates[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= float(value) <= 1:
            raise OfferTruthBenchmarkError("benchmark threshold is invalid")
    if gates["blocking_failures_max"] != 0:
        raise OfferTruthBenchmarkError("blocking failure budget must remain zero")
    if float(gates["dangerous_fallback_rate_ci95_upper_max"]) > 0.005:
        raise OfferTruthBenchmarkError("dangerous fallback target cannot exceed 0.5 percent")

    expected_support = {
        "total_cases": 10_000,
        "known_cases": 3_000,
        "safe_abstention_cases": 5_000,
        "dangerous_fallback_cases": 5_000,
    }
    if manifest.get("minimum_statistical_support") != expected_support:
        raise OfferTruthBenchmarkError("minimum statistical support is invalid")
    regression = manifest.get("regression_ground_truth")
    if not isinstance(regression, str) or Path(regression).name != regression:
        raise OfferTruthBenchmarkError("regression path is invalid")
    return manifest


def _decimal(value: Any, *, allow_zero: bool) -> str | None:
    if isinstance(value, bool) or value is None:
        return None
    text = str(value).strip().replace(" ", "").replace(",", ".")
    try:
        number = Decimal(text)
    except (InvalidOperation, ValueError):
        return None
    if not number.is_finite() or number < 0 or (not allow_zero and number == 0):
        return None
    normalized = format(number, "f")
    if "." in normalized:
        normalized = normalized.rstrip("0").rstrip(".")
    return normalized


def _money(payload: Mapping[str, Any], *, allow_zero: bool) -> ClaimResult:
    if not payload or payload.get("amount") in (None, ""):
        return ClaimResult("unknown", None, False)
    amount = _decimal(payload.get("amount"), allow_zero=allow_zero)
    currency = payload.get("currency")
    if currency is None or (isinstance(currency, str) and not currency.strip()):
        return ClaimResult("unknown", None, False)
    if not isinstance(currency, str) or len(currency.strip()) != 3 or not currency.strip().isalpha():
        return ClaimResult("invalid", None, False)
    if amount is None:
        return ClaimResult("invalid", None, False)
    return ClaimResult("known", {"amount_decimal": amount, "currency": currency.strip().upper()}, True)


def _project(case: BenchmarkCase) -> ClaimResult:
    payload = case.payload
    if case.claim == "price":
        return _money(payload, allow_zero=False)
    if case.claim == "shipping":
        return _money(payload, allow_zero=True)
    if case.claim == "stock":
        raw = payload.get("value")
        if raw in (None, ""):
            return ClaimResult("unknown", None, False)
        if not isinstance(raw, str):
            return ClaimResult("invalid", None, False)
        value = raw.strip().lower().replace(" ", "_").replace("-", "_")
        aliases = {
            "available": "in_stock",
            "in_stock": "in_stock",
            "unavailable": "out_of_stock",
            "out_of_stock": "out_of_stock",
            "preorder": "preorder",
            "pre_order": "preorder",
        }
        normalized = aliases.get(value)
        return ClaimResult("known", normalized, True) if normalized else ClaimResult("invalid", None, False)
    if case.claim == "returns":
        if not payload:
            return ClaimResult("unknown", None, False)
        accepted, period = payload.get("accepted"), payload.get("period_days")
        if not isinstance(accepted, bool) or (
            period is not None and (isinstance(period, bool) or not isinstance(period, int) or not 0 <= period <= 3650)
        ):
            return ClaimResult("invalid", None, False)
        return ClaimResult("known", {"accepted": accepted, "period_days": period}, True)
    if case.claim == "warranty":
        if not payload:
            return ClaimResult("unknown", None, False)
        duration, description = payload.get("duration_months"), payload.get("description")
        if duration is None and (description is None or (isinstance(description, str) and not description.strip())):
            return ClaimResult("unknown", None, False)
        valid_duration = isinstance(duration, int) and not isinstance(duration, bool) and 0 <= duration <= 1200
        valid_description = isinstance(description, str) and bool(description.strip()) and len(description.strip()) <= 512
        if not valid_duration and not valid_description:
            return ClaimResult("invalid", None, False)
        return ClaimResult("known", {
            "duration_months": duration if valid_duration else None,
            "description": description.strip() if valid_description else None,
        }, True)
    if case.claim == "merchant":
        if not payload:
            return ClaimResult("unknown", None, False)
        merchant_id = payload.get("merchant_id")
        status = payload.get("merchant_status")
        relationship = payload.get("relationship_type")
        seller_type = payload.get("seller_type")
        allowed = {"INDEXED", "AFFILIATED", "DIRECT_PARTNER", "MARKETPLACE", "UNVERIFIED"}
        if (
            isinstance(merchant_id, bool)
            or not isinstance(merchant_id, int)
            or merchant_id < 1
            or status not in allowed
            or relationship not in allowed
            or relationship != status
            or seller_type not in {"direct", "marketplace", "unknown"}
        ):
            return ClaimResult("invalid", None, False)
        return ClaimResult("known", dict(payload), True)
    if case.claim == "freshness":
        age, ttl = payload.get("age_seconds"), payload.get("ttl_seconds")
        if age is None or ttl is None:
            return ClaimResult("unknown", None, False)
        if (
            isinstance(age, bool)
            or isinstance(ttl, bool)
            or not isinstance(age, int)
            or not isinstance(ttl, int)
            or ttl < 1
        ):
            return ClaimResult("invalid_future" if isinstance(age, int) and age < 0 else "unknown", None, False)
        if age < 0:
            return ClaimResult("invalid_future", None, False)
        state = "fresh" if age <= ttl else "stale"
        return ClaimResult(state, {"age_seconds": age, "ttl_seconds": ttl}, True)
    raise OfferTruthBenchmarkError("unknown claim")


def _extractor_project(case: BenchmarkCase) -> ClaimResult:
    """Adapte l'extracteur réel au corpus sans lui exposer l'oracle attendu."""

    row: dict[str, Any] = {
        "search_price": "99.90",
        "currency": "EUR",
        "in_stock": "yes",
    }
    merchant = {
        "merchant_id": 7,
        "merchant_status": "AFFILIATED",
        "relationship_type": "AFFILIATED",
        "seller_type": "direct",
    }
    evaluated_at = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)
    observed_at = evaluated_at - timedelta(hours=1)
    ttl_seconds = 259_200

    if case.claim == "price":
        row.pop("search_price")
        row.pop("currency")
        if "amount" in case.payload:
            row["search_price"] = case.payload["amount"]
        if "currency" in case.payload:
            row["currency"] = case.payload["currency"]
    elif case.claim == "stock":
        row.pop("in_stock")
        if "value" in case.payload:
            row["in_stock"] = case.payload["value"]
    elif case.claim == "shipping":
        if "amount" in case.payload:
            row["shipping_cost"] = case.payload["amount"]
        if "currency" in case.payload:
            row["shipping_currency"] = case.payload["currency"]
    elif case.claim == "returns":
        if "accepted" in case.payload:
            row["returns_accepted"] = case.payload["accepted"]
        if "period_days" in case.payload and case.payload["period_days"] is not None:
            row["return_period"] = case.payload["period_days"]
    elif case.claim == "warranty":
        if "duration_months" in case.payload and case.payload["duration_months"] is not None:
            row["warranty_months"] = case.payload["duration_months"]
        if "description" in case.payload and case.payload["description"] is not None:
            row["warranty"] = case.payload["description"]
    elif case.claim == "merchant":
        merchant["merchant_status"] = None
        merchant["relationship_type"] = None
        merchant["seller_type"] = "unknown"
        merchant.update(case.payload)
    elif case.claim == "freshness":
        age_seconds = case.payload.get("age_seconds")
        ttl = case.payload.get("ttl_seconds")
        if isinstance(age_seconds, int) and not isinstance(age_seconds, bool):
            observed_at = evaluated_at - timedelta(seconds=age_seconds)
        if isinstance(ttl, int) and not isinstance(ttl, bool):
            ttl_seconds = ttl

    snapshot = extract_awin_offer_truth(
        row,
        raw_source_record_id=1,
        source_ref="benchmark:1",
        observed_at=observed_at,
        evaluated_at=evaluated_at,
        offer_id=1,
        variant_id=1,
        ttl_seconds=ttl_seconds,
        **merchant,
    )
    claim = snapshot["claims"][case.claim]
    return ClaimResult(
        state=claim["state"],
        value=claim["value"],
        has_evidence=bool(claim["evidence"]),
    )


def _case(
    case_id: str,
    claim: str,
    kind: str,
    payload: Mapping[str, Any],
    state: str,
    value: Any,
    basis: str,
) -> BenchmarkCase:
    return BenchmarkCase(case_id, claim, kind, payload, state, value, basis)


def _generated_cases(seed: int, samples: int) -> list[BenchmarkCase]:
    rng = random.Random(seed)
    cases: list[BenchmarkCase] = []
    for index in range(samples):
        cents = rng.randrange(1, 5_000_000)
        amount = f"{cents // 100},{cents % 100:02d}"
        normalized = f"{cents // 100}.{cents % 100:02d}".rstrip("0").rstrip(".")
        stock_source = rng.choice(["available", "in stock", "out-of-stock", "pre-order"])
        stock_expected = {
            "available": "in_stock",
            "in stock": "in_stock",
            "out-of-stock": "out_of_stock",
            "pre-order": "preorder",
        }[stock_source]
        age_seconds = rng.randrange(0, 259201)
        merchant_value = {"merchant_id": index + 1, "merchant_status": "AFFILIATED", "relationship_type": "AFFILIATED", "seller_type": "direct"}
        prefix = f"generated:{seed}:{index}"
        cases.extend([
            _case(f"{prefix}:price-known", "price", "known", {"amount": amount, "currency": "eur"}, "known", {"amount_decimal": normalized, "currency": "EUR"}, "SYNTHETIC_EXACT_MONEY"),
            _case(f"{prefix}:price-no-currency", "price", "safe_abstention", {"amount": amount}, "unknown", None, "ATOMIC_MONEY_REQUIRED"),
            _case(f"{prefix}:price-zero", "price", "safe_abstention", {"amount": "0", "currency": "EUR"}, "invalid", None, "ZERO_PRICE_FORBIDDEN"),
            _case(f"{prefix}:stock-known", "stock", "known", {"value": stock_source}, "known", stock_expected, "SYNTHETIC_STOCK_ENUM"),
            _case(f"{prefix}:stock-missing", "stock", "safe_abstention", {}, "unknown", None, "NO_AVAILABILITY_FALLBACK"),
            _case(f"{prefix}:shipping-zero", "shipping", "known", {"amount": "0", "currency": "EUR"}, "known", {"amount_decimal": "0", "currency": "EUR"}, "EXPLICIT_ZERO_SHIPPING"),
            _case(f"{prefix}:shipping-missing", "shipping", "safe_abstention", {}, "unknown", None, "NO_FREE_SHIPPING_FALLBACK"),
            _case(f"{prefix}:returns-missing", "returns", "safe_abstention", {}, "unknown", None, "NO_RETURNS_INFERENCE"),
            _case(f"{prefix}:warranty-missing", "warranty", "safe_abstention", {}, "unknown", None, "NO_WARRANTY_INFERENCE"),
            _case(f"{prefix}:merchant-explicit", "merchant", "known", merchant_value, "known", merchant_value, "EXPLICIT_REGISTRY_RELATIONSHIP"),
            _case(f"{prefix}:merchant-embellished", "merchant", "safe_abstention", {"merchant_id": index + 1, "merchant_status": "AFFILIATED", "relationship_type": "DIRECT_PARTNER", "seller_type": "direct"}, "invalid", None, "RELATIONSHIP_PRESERVATION"),
            _case(f"{prefix}:fresh", "freshness", "known", {"age_seconds": age_seconds, "ttl_seconds": 259200}, "fresh", {"age_seconds": age_seconds, "ttl_seconds": 259200}, "VERSIONED_TTL"),
            _case(f"{prefix}:stale", "freshness", "safe_abstention", {"age_seconds": 259201 + rng.randrange(500000), "ttl_seconds": 259200}, "stale", None, "STALE_EXCLUDED"),
            _case(f"{prefix}:future", "freshness", "safe_abstention", {"age_seconds": -1 - rng.randrange(1000), "ttl_seconds": 259200}, "invalid_future", None, "FUTURE_EXCLUDED"),
        ])
    return cases


def _regression_cases(directory: Path, manifest: Mapping[str, Any]) -> list[BenchmarkCase]:
    source = _load_json(directory / str(manifest["regression_ground_truth"]), "offer truth regressions are unreadable")
    if source.get("schema_version") != "offer-truth-regressions/v1" or source.get("limitation") != LIMITATION:
        raise OfferTruthBenchmarkError("offer truth regressions are invalid")
    raw_cases = source.get("cases")
    if not isinstance(raw_cases, list) or not raw_cases:
        raise OfferTruthBenchmarkError("offer truth regressions are empty")
    cases: list[BenchmarkCase] = []
    for raw in raw_cases:
        if not isinstance(raw, Mapping):
            raise OfferTruthBenchmarkError("offer truth regression case is invalid")
        try:
            case = BenchmarkCase(
                case_id="regression:" + str(raw["case_id"]),
                claim=str(raw["claim"]),
                kind=str(raw["kind"]),
                payload=dict(raw["payload"]),
                expected_state=str(raw["expected_state"]),
                expected_value=raw.get("expected_value"),
                truth_basis=str(raw["truth_basis"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise OfferTruthBenchmarkError("offer truth regression case is invalid") from exc
        if case.claim not in CLAIMS:
            raise OfferTruthBenchmarkError("offer truth regression claim is invalid")
        cases.append(case)
    if {case.claim for case in cases} != set(CLAIMS):
        raise OfferTruthBenchmarkError("regressions must cover every claim")
    return cases


def _matches(case: BenchmarkCase, actual: ClaimResult) -> bool:
    if actual.state != case.expected_state:
        return False
    if case.expected_value is not None and actual.value != case.expected_value:
        return False
    return True


def build_report(manifest_path: str | Path, *, adapter: str = "oracle") -> dict[str, Any]:
    path = Path(manifest_path).resolve()
    manifest = _load_manifest(path)
    cases = _regression_cases(path.parent, manifest)
    regression_source = _load_json(
        path.parent / str(manifest["regression_ground_truth"]),
        "offer truth regressions are unreadable",
    )
    regression_fingerprint = "sha256:" + hashlib.sha256(
        canonical_json(regression_source).encode("utf-8")
    ).hexdigest()
    generator = manifest["generator"]
    for seed in generator["seeds"]:
        cases.extend(_generated_cases(seed, generator["samples_per_seed"]))

    evaluated: list[tuple[BenchmarkCase, ClaimResult, bool]] = []
    for case in cases:
        if adapter == "oracle":
            first = _project(case)
            second = _project(case)
        elif adapter == "extractor":
            first = _extractor_project(case)
            second = _extractor_project(case)
        else:
            raise OfferTruthBenchmarkError("benchmark adapter is invalid")
        evaluated.append((case, first, _matches(case, first) and first == second))

    known = [item for item in evaluated if item[0].kind == "known"]
    abstentions = [item for item in evaluated if item[0].kind == "safe_abstention"]
    dangerous = [item for item in abstentions if item[1].state in {"known", "fresh"} and item[0].expected_state not in {"known", "fresh"}]
    provenance = [item for item in known if item[1].has_evidence]
    correct = sum(item[2] for item in evaluated)
    known_correct = sum(item[2] for item in known)
    abstention_correct = sum(item[2] for item in abstentions)
    metrics = {
        "overall_correctness": _metric(correct, len(evaluated)),
        "known_claim_accuracy": _metric(known_correct, len(known)),
        "safe_abstention_accuracy": _metric(abstention_correct, len(abstentions)),
        "provenance_accuracy": _metric(len(provenance), len(known)),
        "dangerous_fallback_rate": _event_metric(len(dangerous), len(abstentions), "dangerous_fallbacks"),
    }
    gates = manifest["gates"]
    gate_results = {
        "overall_correctness_ci95_lower_min": metrics["overall_correctness"]["ci95_lower"] >= gates["overall_correctness_ci95_lower_min"],
        "known_claim_accuracy_ci95_lower_min": metrics["known_claim_accuracy"]["ci95_lower"] >= gates["known_claim_accuracy_ci95_lower_min"],
        "safe_abstention_accuracy_ci95_lower_min": metrics["safe_abstention_accuracy"]["ci95_lower"] >= gates["safe_abstention_accuracy_ci95_lower_min"],
        "provenance_accuracy_ci95_lower_min": metrics["provenance_accuracy"]["ci95_lower"] >= gates["provenance_accuracy_ci95_lower_min"],
        "dangerous_fallback_rate_ci95_upper_max": metrics["dangerous_fallback_rate"]["ci95_upper"] <= gates["dangerous_fallback_rate_ci95_upper_max"],
        "blocking_failures_max": len(evaluated) - correct <= gates["blocking_failures_max"],
    }
    support = manifest["minimum_statistical_support"]
    support_results = {
        "total_cases": len(evaluated) >= support["total_cases"],
        "known_cases": len(known) >= support["known_cases"],
        "safe_abstention_cases": len(abstentions) >= support["safe_abstention_cases"],
        "dangerous_fallback_cases": len(abstentions) >= support["dangerous_fallback_cases"],
    }
    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "benchmark_version": manifest["benchmark_version"],
        "policy_version": POLICY_VERSION if adapter == "oracle" else EXTRACTOR_VERSION,
        "limitation": LIMITATION,
        "quality_status": "DETERMINISTIC_ORACLE_WITHOUT_EXTERNAL_HUMAN_GROUND_TRUTH",
        "generator": generator,
        "claims": list(CLAIMS),
        "summary": {
            "status": "PASS" if all(gate_results.values()) and all(support_results.values()) else "FAIL",
            "promotion_eligible": False,
            "cases": len(evaluated),
            "failed": len(evaluated) - correct,
            "gate_results": gate_results,
            "support_results": support_results,
        },
        "metrics": metrics,
        "by_claim": {
            claim: {
                "cases": sum(item[0].claim == claim for item in evaluated),
                "failed": sum(item[0].claim == claim and not item[2] for item in evaluated),
            }
            for claim in CLAIMS
        },
        "regressions": {
            "cases": sum(item[0].case_id.startswith("regression:") for item in evaluated),
            "fingerprint": regression_fingerprint,
            "failures": [item[0].case_id for item in evaluated if item[0].case_id.startswith("regression:") and not item[2]],
        },
        "failure_samples": [
            {"case": asdict(case), "actual": asdict(actual)}
            for case, actual, passed in evaluated if not passed
        ][:25],
    }
    report["evaluation_id"] = "sha256:" + hashlib.sha256(
        canonical_json({"manifest": manifest, "report": report}).encode("utf-8")
    ).hexdigest()
    return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Benchmark Offer Truth FILON")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output")
    parser.add_argument("--adapter", choices=("oracle", "extractor"), default="oracle")
    parser.add_argument("--require-pass", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        report = build_report(args.manifest, adapter=args.adapter)
    except OfferTruthBenchmarkError as exc:
        print(json.dumps({"status": "INVALID", "error": str(exc)}))
        return 2
    payload = canonical_json(report) + "\n"
    if args.output:
        atomic_write_text(args.output, payload)
        print(canonical_json({"evaluation_id": report["evaluation_id"], "summary": report["summary"], "metrics": report["metrics"]}))
    else:
        print(payload, end="")
    return int(args.require_pass and report["summary"]["status"] != "PASS")


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
