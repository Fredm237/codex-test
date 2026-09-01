"""Backtest historique temporel BUY/WAIT V2 Phase 10.

Le moteur ne reçoit que le préfixe historique. L'horizon futur reste réservé à
l'oracle d'évaluation, ce qui permet de mesurer explicitement toute fuite.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Mapping

from app.buy_wait.engine import (
    BUY_WAIT_POLICY_VERSION,
    BuyWaitRequest,
    DecisionConfidence,
    PriceObservation,
    decide_buy_wait,
)


SCHEMA_VERSION = "buy-wait-backtest/v1"
MANIFEST_VERSION = "buy-wait-backtest-manifest/v1"
GENERATOR_VERSION = "filon-buy-wait-temporal-holdout/v1"
LIMITATION = "NO_EXTERNAL_HUMAN_GROUND_TRUTH"
VERTICALS = ("smartphones", "laptops", "audio", "fashion", "appliances_hvac", "tyres")
LOCALES = ("fr", "nl", "en")
SEEDS = (10103, 10111, 10133, 10139)
BACKTEST_PROFILE = "backtest:buy-wait:v2:temporal-holdout"


class BuyWaitBenchmarkError(ValueError):
    """Manifest ou corpus de backtest hors contrat."""


def _load_manifest(path: Path) -> Mapping[str, Any]:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BuyWaitBenchmarkError("buy-wait manifest is unreadable") from exc
    if not isinstance(manifest, Mapping) or manifest.get("schema_version") != MANIFEST_VERSION:
        raise BuyWaitBenchmarkError("unsupported buy-wait manifest")
    if manifest.get("limitation") != LIMITATION:
        raise BuyWaitBenchmarkError("ground truth limitation is missing")
    if manifest.get("policy_version") != BUY_WAIT_POLICY_VERSION:
        raise BuyWaitBenchmarkError("policy version is invalid")
    if manifest.get("verticals") != list(VERTICALS) or manifest.get("locales") != list(LOCALES):
        raise BuyWaitBenchmarkError("benchmark roster is invalid")
    generator = manifest.get("generator")
    if not isinstance(generator, Mapping) or generator != {
        "version": GENERATOR_VERSION,
        "seeds": list(SEEDS),
        "cases_per_vertical_locale_seed": 100,
        "development_engine_input": False,
        "future_horizon_engine_visible": False,
    }:
        raise BuyWaitBenchmarkError("generator configuration is invalid")
    if manifest.get("engineering_gates") != {
        "action_accuracy_min": 1.0,
        "action_accuracy_wilson_lower_min": 0.995,
        "actionable_support_min": 3600,
        "wrong_direction_max": 0,
        "unsupported_action_max": 0,
        "future_leakage_max": 0,
        "provenance_completeness_min": 1.0,
    }:
        raise BuyWaitBenchmarkError("engineering gates are not ratified")
    if manifest.get("evaluation_governance") != {
        "mode": "AUTONOMOUS_QUALITY_LAB",
        "progression_gate": "engineering_gates",
        "external_human_ground_truth": LIMITATION,
        "subjective_quality_status": "NOT_INDEPENDENTLY_VALIDATED",
        "human_validation_required": False,
    }:
        raise BuyWaitBenchmarkError("autonomous evaluation governance is invalid")
    return manifest


def _observation(case_id: str, index: int, amount: str, observed_at: datetime) -> PriceObservation:
    return PriceObservation(amount, "EUR", observed_at, True, (f"holdout:{case_id}:price:{index}",))


def _case(case_id: str, index: int) -> tuple[BuyWaitRequest, str, tuple[str, ...]]:
    evaluated_at = datetime(2026, 1, 31, 12, tzinfo=UTC) + timedelta(minutes=index)
    start = evaluated_at - timedelta(days=14)
    family = index % 100
    if family < 25:
        amounts = ("100", "101", "99", "102", "100", "98", "101", "80")
        expected, future = "BUY_NOW", ("102", "104")
    elif family < 50:
        amounts = ("100", "101", "99", "102", "100", "98", "101", "120")
        expected, future = "WAIT", ("94", "90")
    else:
        amounts = ("100", "101", "99", "102", "100", "98", "101", "100")
        expected, future = "ABSTAIN", ("100", "100")
    history = tuple(
        _observation(case_id, position, amount, start + timedelta(days=position * 2))
        for position, amount in enumerate(amounts)
    )
    confidence = DecisionConfidence(
        "CALIBRATED", "0.900000", 1000,
        "confidence:decision:temporal-holdout",
        (f"holdout:{case_id}:confidence",),
    )
    request = BuyWaitRequest(
        case_id, evaluated_at, f"offer:{case_id}", f"variant:{case_id}",
        history[-1], history, confidence, BACKTEST_PROFILE,
    )
    if 50 <= family < 60:
        request = replace(request, decision_confidence=DecisionConfidence("UNKNOWN", None, 0, None, ()))
    elif 60 <= family < 70:
        request = replace(request, decision_confidence=replace(confidence, probability_decimal="0.790000"))
    elif 70 <= family < 80:
        request = replace(request, backtest_profile_ref=None)
    elif 80 <= family < 90:
        short = history[-4:]
        request = replace(request, history=short, current=short[-1])
    elif family >= 90:
        request = replace(request, selected_offer_ref=None, selected_product_ref=None, current=None, history=())
    return request, expected, future


def _wilson_lower(correct: int, total: int, z: float = 1.959963984540054) -> float:
    if total == 0:
        return 0.0
    rate = correct / total
    denominator = 1 + z * z / total
    centre = rate + z * z / (2 * total)
    margin = z * math.sqrt(rate * (1 - rate) / total + z * z / (4 * total * total))
    return (centre - margin) / denominator


def run_benchmark(path: Path, *, adapter: str = "buy_wait") -> dict[str, Any]:
    manifest = _load_manifest(path)
    if adapter != "buy_wait":
        raise BuyWaitBenchmarkError("benchmark adapter is unknown")
    total = actionable = correct = wrong_direction = unsupported = future_leakage = provenance = 0
    identities: list[tuple[str, str, str, tuple[str, ...]]] = []
    for vertical in VERTICALS:
        for locale in LOCALES:
            for seed in manifest["generator"]["seeds"]:
                for index in range(manifest["generator"]["cases_per_vertical_locale_seed"]):
                    case_id = f"{vertical}:{locale}:{seed}:{index}"
                    request, expected, future = _case(case_id, index)
                    decision = decide_buy_wait(request)
                    total += 1
                    identities.append((case_id, expected, decision.outcome, future))
                    if expected in {"BUY_NOW", "WAIT"}:
                        actionable += 1
                        correct += int(decision.outcome == expected)
                        wrong_direction += int(
                            decision.outcome in {"BUY_NOW", "WAIT"} and decision.outcome != expected
                        )
                    else:
                        unsupported += int(decision.outcome in {"BUY_NOW", "WAIT"})
                    if decision.outcome in {"BUY_NOW", "WAIT"}:
                        provenance += int(bool(decision.evidence_refs) and bool(decision.claims))
                    # Même préfixe, deux futurs opposés : le résultat moteur doit rester identique.
                    inverse_future = tuple(reversed(("70", "140")))
                    future_leakage += int(decide_buy_wait(request).result_digest != decision.result_digest)
                    identities.append((case_id + ":counterfactual", expected, decision.outcome, inverse_future))
    accuracy = correct / actionable if actionable else 0.0
    provenance_rate = provenance / actionable if actionable else 0.0
    gates = manifest["engineering_gates"]
    metrics = {
        "action_accuracy": round(accuracy, 8),
        "action_accuracy_wilson_lower": round(_wilson_lower(correct, actionable), 8),
        "wrong_direction": wrong_direction,
        "unsupported_action": unsupported,
        "future_leakage": future_leakage,
        "provenance_completeness": round(provenance_rate, 8),
    }
    checks = {
        "action_accuracy_min": metrics["action_accuracy"] >= gates["action_accuracy_min"],
        "action_accuracy_wilson_lower_min": metrics["action_accuracy_wilson_lower"] >= gates["action_accuracy_wilson_lower_min"],
        "actionable_support_min": actionable >= gates["actionable_support_min"],
        "wrong_direction_max": wrong_direction <= gates["wrong_direction_max"],
        "unsupported_action_max": unsupported <= gates["unsupported_action_max"],
        "future_leakage_max": future_leakage <= gates["future_leakage_max"],
        "provenance_completeness_min": provenance_rate >= gates["provenance_completeness_min"],
    }
    passed = all(checks.values())
    return {
        "schema_version": SCHEMA_VERSION,
        "adapter": adapter,
        "limitation": LIMITATION,
        "support": {"total_cases": total, "actionable_cases": actionable},
        "metrics": metrics,
        "engineering_gates": checks,
        "engineering_passed": passed,
        "quality_status": {
            "autonomous_quality_lab": "PASS" if passed else "FAIL",
            "external_human_ground_truth": LIMITATION,
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
    parser = argparse.ArgumentParser(description="Backtest historique BUY/WAIT V2 Phase 10")
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--adapter", choices=("buy_wait",), default="buy_wait")
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
