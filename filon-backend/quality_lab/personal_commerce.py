"""Independent engineering benchmark for Personal Commerce Phase 18."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from app.personal_commerce import ExplicitPreference, PersonalCommerceCandidate, PersonalCommerceRequest, decide_personal_commerce


class PersonalCommerceBenchmarkError(ValueError):
    """Benchmark manifest outside the ratified contract."""


def evaluate_manifest(path: Path) -> dict[str, Any]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != "personal-commerce-benchmark/v1" or manifest.get("development_engine_input") is not False:
        raise PersonalCommerceBenchmarkError("unsupported or non-independent manifest")
    cases = manifest.get("cases")
    if not isinstance(cases, list) or len(cases) < 10:
        raise PersonalCommerceBenchmarkError("at least ten cases are required")
    outcomes = []
    consent_bypasses = false_actions = scores_published = 0
    for case in cases:
        preferences = tuple(ExplicitPreference(item["id"], item["key"], item["value"], item["polarity"], "personal_commerce", f"user:{item['id']}") for item in case.get("preferences", []))
        request = PersonalCommerceRequest(f"objective:{case['id']}", case.get("consent", True), tuple(case.get("allowed", ["outfit", "setup", "kit", "routine"])), case.get("budget", "200"), "EUR", preferences)
        candidates = []
        for item in case.get("candidates", []):
            purchases = item.get("purchases", 0)
            action = item.get("action")
            candidates.append(PersonalCommerceCandidate(
                f"solution:{item['id']}", item["kind"], item.get("composition", "SOLUTION_COMPOSED"), item.get("constraint", "ELIGIBLE"),
                item.get("owned", 1), purchases, item.get("cost", "0"), item.get("currency", "EUR") if purchases else None,
                action, f"buy-wait:{item['id']}" if action else None, item.get("attributes", {}), (f"composition:{item['id']}",),
            ))
        result = decide_personal_commerce(request, candidates)
        passed = result.action == case["expected_action"] and ("expected_ref" not in case or result.selected_solution_ref == case["expected_ref"])
        consent_bypasses += int(not case.get("consent", True) and result.action != "ABSTAIN")
        false_actions += int(not passed and result.action != "ABSTAIN")
        scores_published += int(result.utility_score is not None)
        outcomes.append({"case_id": case["id"], "passed": passed, "action": result.action})
    total = len(cases)
    metrics = {"total_cases": total, "pass_rate": sum(item["passed"] for item in outcomes) / total, "consent_bypasses": consent_bypasses, "false_actions": false_actions, "scores_published": scores_published}
    gates = manifest["engineering_gates"]
    passed = metrics["pass_rate"] >= gates["pass_rate_min"] and consent_bypasses <= gates["consent_bypasses_max"] and false_actions <= gates["false_actions_max"] and scores_published <= gates["scores_published_max"]
    return {"benchmark": "personal-commerce-v1", "status": "PASS" if passed else "FAIL", "metrics": metrics, "outcomes": outcomes}


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
