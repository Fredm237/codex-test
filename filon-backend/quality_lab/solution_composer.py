"""Independent engineering benchmark for Solution Composer Phase 17."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from app.solution_composer import ComponentCandidate, CompositionRequest, compose_solution


class SolutionComposerBenchmarkError(ValueError):
    """Benchmark manifest outside the ratified contract."""


def evaluate_manifest(path: Path) -> dict[str, Any]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != "solution-composer-benchmark/v1":
        raise SolutionComposerBenchmarkError("unsupported manifest")
    if manifest.get("development_engine_input") is not False:
        raise SolutionComposerBenchmarkError("independent cases are required")
    cases = manifest.get("cases")
    if not isinstance(cases, list) or len(cases) < 10:
        raise SolutionComposerBenchmarkError("at least ten cases are required")

    outcomes = []
    false_compositions = 0
    owned_first_violations = 0
    scores_published = 0
    for case in cases:
        request = CompositionRequest(
            f"benchmark:{case['id']}", case["kind"], tuple(case["slots"]),
            case.get("budget", "100"), "EUR",
        )
        candidates = [
            ComponentCandidate(f"owned:{case['id']}:{index}", slot, "owned", "ELIGIBLE", None, None, None, None, None, (f"user:{index}",))
            for index, slot in enumerate(case.get("owned", []))
        ]
        for index, item in enumerate(case.get("offers", [])):
            candidates.append(ComponentCandidate(
                f"product:{case['id']}:{index}", item["slot"], "catalogue",
                item.get("constraint", "ELIGIBLE"), item["amount"], item.get("currency", "EUR"),
                f"offer:{case['id']}:{index}", item.get("truth", "VERIFIED"), item.get("duplicate", False),
                (f"snapshot:{index}",),
            ))
        result = compose_solution(request, candidates)
        passed = result.outcome == case["expected"]
        if result.outcome == "ABSTAINED":
            passed = passed and result.reason_code == case.get("reason")
        else:
            passed = passed and result.purchase_count == case.get("purchases")
            passed = passed and ("total" not in case or result.total_cost == case["total"])
        false_compositions += int(result.outcome == "SOLUTION_COMPOSED" and case["expected"] == "ABSTAINED")
        owned_slots = set(case.get("owned", []))
        owned_first_violations += sum(item.source == "catalogue" and item.slot in owned_slots for item in result.selected)
        scores_published += int(result.utility_score is not None)
        outcomes.append({"case_id": case["id"], "passed": passed, "outcome": result.outcome})

    total = len(cases)
    metrics = {
        "total_cases": total,
        "pass_rate": sum(item["passed"] for item in outcomes) / total,
        "false_compositions": false_compositions,
        "owned_first_violations": owned_first_violations,
        "scores_published": scores_published,
    }
    gates = manifest["engineering_gates"]
    passed = metrics["pass_rate"] >= gates["pass_rate_min"] and false_compositions <= gates["false_compositions_max"] and owned_first_violations <= gates["owned_first_violations_max"] and scores_published <= gates["scores_published_max"]
    return {"benchmark": "solution-composer-v1", "status": "PASS" if passed else "FAIL", "metrics": metrics, "outcomes": outcomes}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    report = evaluate_manifest(args.manifest)
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(f"{rendered}\n", encoding="utf-8")
    else:
        print(rendered)
    return 1 if args.strict and report["status"] != "PASS" else 0


if __name__ == "__main__":
    raise SystemExit(main())
