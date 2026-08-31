from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from quality_lab.integrity import DATASETS, canonical_json
from quality_lab.regression import compare_scorecards, main
from quality_lab.scorecard import GATE_CONTRACT


SHA_A = "sha256:" + "a" * 64
SHA_B = "sha256:" + "b" * 64
SHA_C = "sha256:" + "c" * 64


def _scorecard(
    *,
    run_id: str,
    system_version: str,
    value: float = 0.95,
    threshold: float = 0.90,
    gate_name: str = "category_accuracy_min",
    operator: str | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    gates: list[dict[str, Any]] = []
    metrics: dict[str, float] = {}
    for name, (metric, canonical_operator) in GATE_CONTRACT.items():
        effective_operator = (
            operator
            if name == gate_name and operator is not None
            else canonical_operator
        )
        if name == gate_name:
            measured = value
            configured_threshold = threshold
        elif canonical_operator == "min":
            measured = 1.0
            configured_threshold = 0.0
        elif canonical_operator == "lt":
            measured = 0.0
            configured_threshold = 1.0
        else:
            measured = 0.0
            configured_threshold = 0.0
        if effective_operator == "min":
            passed = measured >= configured_threshold
        elif effective_operator == "lt":
            passed = measured < configured_threshold
        else:
            passed = measured <= configured_threshold
        metrics[metric] = measured
        gates.append(
            {
                "gate": name,
                "metric": metric,
                "operator": effective_operator,
                "threshold": configured_threshold,
                "value": measured,
                "passed": passed,
            }
        )
    computed_status = "pass" if all(gate["passed"] for gate in gates) else "fail"
    return {
        "schema_version": "quality-scorecard/v1",
        "evaluator_version": "0.5.0",
        "run_id": run_id,
        "system_version": system_version,
        "gold_manifest_sha256": SHA_A,
        "manifest_fingerprint": SHA_B,
        "holdout_fingerprint": SHA_C,
        "status": status or computed_status,
        "measurable": True,
        "holdout": {
            dataset: {
                "gold_cases": 1,
                "prediction_cases": 1,
                "joined_cases": 1,
            }
            for dataset in DATASETS
        },
        "adapters": {
            dataset: {
                "engine_id": f"app.quality.{dataset}",
                "engine_version": system_version,
            }
            for dataset in DATASETS
        },
        "metrics": metrics,
        "gates": gates,
        "errors": [],
    }


def _write(path: Path, value: Any) -> Path:
    path.write_text(canonical_json(value) + "\n", encoding="utf-8")
    return path


def _pair(tmp_path: Path, baseline: dict[str, Any], candidate: dict[str, Any]):
    return (
        _write(tmp_path / "baseline.json", baseline),
        _write(tmp_path / "candidate.json", candidate),
    )


def _gate_delta(report: dict[str, Any], gate_name: str) -> dict[str, Any]:
    return next(
        gate for gate in report["gate_deltas"] if gate["gate"] == gate_name
    )


def test_regression_report_is_deterministic_and_records_input_digests(tmp_path: Path):
    baseline, candidate = _pair(
        tmp_path,
        _scorecard(run_id="run-base", system_version="git-base", value=0.94),
        _scorecard(run_id="run-next", system_version="git-next", value=0.97),
    )

    first = compare_scorecards(baseline, candidate)
    second = compare_scorecards(baseline, candidate)

    assert first == second
    assert first["status"] == "pass"
    assert first["measurable"] is True
    assert first["regression"] is False
    assert len(first["gate_deltas"]) == len(GATE_CONTRACT)
    assert _gate_delta(first, "category_accuracy_min") == {
        "gate": "category_accuracy_min",
        "metric": "category_accuracy_ci95_lower",
        "operator": "min",
        "threshold": 0.9,
        "baseline_value": 0.94,
        "candidate_value": 0.97,
        "delta": pytest.approx(0.03),
        "directional_delta": pytest.approx(0.03),
        "movement": "improved",
        "baseline_passed": True,
        "candidate_passed": True,
        "gate_regression": False,
    }
    assert first["baseline"]["scorecard_sha256"] == (
        "sha256:" + hashlib.sha256(baseline.read_bytes()).hexdigest()
    )
    assert first["candidate"]["scorecard_sha256"] == (
        "sha256:" + hashlib.sha256(candidate.read_bytes()).hexdigest()
    )


def test_pass_to_fail_and_any_candidate_fail_are_blocking_regressions(tmp_path: Path):
    baseline, candidate = _pair(
        tmp_path,
        _scorecard(run_id="run-base", system_version="git-base", value=0.95),
        _scorecard(run_id="run-next", system_version="git-next", value=0.89),
    )
    report = compare_scorecards(baseline, candidate)
    assert report["status"] == "fail"
    assert report["regression"] is True
    assert _gate_delta(report, "category_accuracy_min")["gate_regression"] is True

    _write(
        baseline,
        _scorecard(run_id="run-base", system_version="git-base", value=0.80),
    )
    _write(
        candidate,
        _scorecard(run_id="run-next", system_version="git-next", value=0.85),
    )
    still_failing = compare_scorecards(baseline, candidate)
    assert still_failing["status"] == "fail"
    assert still_failing["regression"] is True
    assert _gate_delta(still_failing, "category_accuracy_min")["movement"] == "improved"


def test_fail_to_pass_is_a_measurable_improvement(tmp_path: Path):
    baseline, candidate = _pair(
        tmp_path,
        _scorecard(run_id="run-base", system_version="git-base", value=0.89),
        _scorecard(run_id="run-next", system_version="git-next", value=0.91),
    )
    report = compare_scorecards(baseline, candidate)
    assert report["status"] == "pass"
    assert report["regression"] is False
    assert _gate_delta(report, "category_accuracy_min")["movement"] == "improved"


@pytest.mark.parametrize(
    ("gate_name", "operator"),
    [
        ("false_merge_rate_max", "max"),
        ("absurd_result_rate_max", "lt"),
    ],
)
def test_lower_is_better_operators_use_the_correct_direction(
    tmp_path: Path, gate_name: str, operator: str
):
    baseline, candidate = _pair(
        tmp_path,
        _scorecard(
            run_id="run-base",
            system_version="git-base",
            value=0.009,
            threshold=0.01,
            gate_name=gate_name,
        ),
        _scorecard(
            run_id="run-next",
            system_version="git-next",
            value=0.004,
            threshold=0.01,
            gate_name=gate_name,
        ),
    )
    report = compare_scorecards(baseline, candidate)
    delta = _gate_delta(report, gate_name)
    assert report["status"] == "pass"
    assert delta["operator"] == operator
    assert delta["delta"] == pytest.approx(-0.005)
    assert delta["directional_delta"] == pytest.approx(0.005)
    assert delta["movement"] == "improved"


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("manifest_fingerprint", "sha256:" + "d" * 64),
        ("gold_manifest_sha256", "sha256:" + "d" * 64),
        ("holdout_fingerprint", "sha256:" + "e" * 64),
    ],
)
def test_identity_or_holdout_drift_is_not_measurable(
    tmp_path: Path, field: str, replacement: Any
):
    base = _scorecard(run_id="run-base", system_version="git-base")
    next_card = _scorecard(run_id="run-next", system_version="git-next")
    next_card[field] = replacement
    baseline, candidate = _pair(tmp_path, base, next_card)
    report = compare_scorecards(baseline, candidate)
    assert report["status"] == "not_measurable"
    assert report["measurable"] is False
    assert report["regression"] is None
    assert {error["code"] for error in report["errors"]} == {
        "QR002_SCORECARDS_INCOMPATIBLE"
    }


def test_valid_holdout_count_drift_is_not_measurable(tmp_path: Path):
    base = _scorecard(run_id="run-base", system_version="git-base")
    next_card = _scorecard(run_id="run-next", system_version="git-next")
    next_card["holdout"]["taxonomy"] = {
        "gold_cases": 2,
        "prediction_cases": 2,
        "joined_cases": 2,
    }
    baseline, candidate = _pair(tmp_path, base, next_card)

    report = compare_scorecards(baseline, candidate)

    assert report["status"] == "not_measurable"
    assert any(error["path"] == "holdout" for error in report["errors"])


@pytest.mark.parametrize("drift", ["threshold", "operator", "metric", "roster"])
def test_gate_contract_drift_is_not_measurable(tmp_path: Path, drift: str):
    base = _scorecard(run_id="run-base", system_version="git-base")
    next_card = _scorecard(run_id="run-next", system_version="git-next")
    gate = next_card["gates"][0]
    if drift == "threshold":
        gate["threshold"] = 0.91
    elif drift == "operator":
        gate["operator"] = "max"
        gate["passed"] = False
        next_card["status"] = "fail"
    elif drift == "metric":
        gate["metric"] = "subcategory_accuracy_ci95_lower"
        next_card["metrics"] = {"subcategory_accuracy_ci95_lower": gate["value"]}
    else:
        gate["gate"] = "subcategory_accuracy_min"
    baseline, candidate = _pair(tmp_path, base, next_card)
    report = compare_scorecards(baseline, candidate)
    assert report["status"] == "not_measurable"
    assert any("gates" in error.get("path", "") for error in report["errors"])


def test_adapter_roster_drift_is_not_measurable_but_versions_may_change(tmp_path: Path):
    base = _scorecard(run_id="run-base", system_version="git-base")
    next_card = _scorecard(run_id="run-next", system_version="git-next")
    baseline, candidate = _pair(tmp_path, base, next_card)
    assert compare_scorecards(baseline, candidate)["status"] == "pass"

    next_card["adapters"].pop("retrieval")
    _write(candidate, next_card)
    report = compare_scorecards(baseline, candidate)
    assert report["status"] == "not_measurable"
    assert any(
        error.get("path", "").endswith("/adapters") for error in report["errors"]
    )


@pytest.mark.parametrize("surface", ["holdout", "adapters", "gates"])
def test_truncated_canonical_scorecard_never_turns_green(
    tmp_path: Path, surface: str
):
    base = _scorecard(run_id="run-base", system_version="git-base")
    next_card = _scorecard(run_id="run-next", system_version="git-next")
    for card in (base, next_card):
        if surface in {"holdout", "adapters"}:
            card[surface].pop("decision")
        else:
            card["gates"].pop()
    baseline, candidate = _pair(tmp_path, base, next_card)

    report = compare_scorecards(baseline, candidate)

    assert report["status"] == "not_measurable"
    assert report["measurable"] is False
    assert any(
        error["code"] == "QR001_SCORECARD_INVALID"
        and surface in error.get("path", "")
        for error in report["errors"]
    )


def test_identical_run_cannot_be_presented_as_a_regression_comparison(tmp_path: Path):
    baseline, candidate = _pair(
        tmp_path,
        _scorecard(run_id="same-run", system_version="git-base"),
        _scorecard(run_id="same-run", system_version="git-next"),
    )
    report = compare_scorecards(baseline, candidate)
    assert report["status"] == "not_measurable"
    assert any(error["path"] == "run_id" for error in report["errors"])


def test_non_measurable_or_internally_inconsistent_scorecard_never_turns_green(
    tmp_path: Path,
):
    base = _scorecard(run_id="run-base", system_version="git-base")
    next_card = _scorecard(run_id="run-next", system_version="git-next")
    next_card["status"] = "not_measurable"
    next_card["measurable"] = False
    baseline, candidate = _pair(tmp_path, base, next_card)
    report = compare_scorecards(baseline, candidate)
    assert report["status"] == "not_measurable"
    assert any(
        error["code"] == "QR003_SCORECARD_NOT_MEASURABLE"
        for error in report["errors"]
    )

    next_card = _scorecard(run_id="run-next", system_version="git-next")
    next_card["gates"][0]["passed"] = False
    _write(candidate, next_card)
    inconsistent = compare_scorecards(baseline, candidate)
    assert inconsistent["status"] == "not_measurable"
    assert any(
        "contradicts" in error["message"] for error in inconsistent["errors"]
    )

    next_card = _scorecard(run_id="run-next", system_version="git-next")
    next_card["metrics"]["category_accuracy_ci95_lower"] = 0.99
    _write(candidate, next_card)
    metric_tamper = compare_scorecards(baseline, candidate)
    assert metric_tamper["status"] == "not_measurable"
    assert any(
        "must equal" in error["message"] for error in metric_tamper["errors"]
    )


@pytest.mark.parametrize(
    "payload",
    [
        '{"schema_version":"quality-scorecard/v1","schema_version":"duplicate"}',
        '{"schema_version":"quality-scorecard/v1","metrics":{"x":NaN}}',
        "[" * 1200 + "0" + "]" * 1200,
    ],
)
def test_strict_json_rejects_duplicate_nonfinite_and_excessive_nesting(
    tmp_path: Path, payload: str
):
    baseline = tmp_path / "baseline.json"
    baseline.write_text(payload, encoding="utf-8")
    candidate = _write(
        tmp_path / "candidate.json",
        _scorecard(run_id="run-next", system_version="git-next"),
    )
    report = compare_scorecards(baseline, candidate)
    assert report["status"] == "not_measurable"
    assert any(error["code"] == "QR001_SCORECARD_INVALID" for error in report["errors"])


def test_cli_exit_codes_and_atomic_output_preserve_inputs(tmp_path: Path, capsys):
    baseline, candidate = _pair(
        tmp_path,
        _scorecard(run_id="run-base", system_version="git-base", value=0.95),
        _scorecard(run_id="run-next", system_version="git-next", value=0.96),
    )
    output = tmp_path / "regression.json"
    assert main(
        [
            "--baseline",
            str(baseline),
            "--candidate",
            str(candidate),
            "--output",
            str(output),
        ]
    ) == 0
    assert json.loads(output.read_text(encoding="utf-8"))["status"] == "pass"
    assert json.loads(capsys.readouterr().out)["status"] == "pass"

    original = baseline.read_bytes()
    assert main(
        [
            "--baseline",
            str(baseline),
            "--candidate",
            str(candidate),
            "--output",
            str(baseline),
        ]
    ) == 2
    assert baseline.read_bytes() == original
    assert json.loads(capsys.readouterr().out)["status"] == "not_measurable"

    _write(
        candidate,
        _scorecard(run_id="run-next", system_version="git-next", value=0.80),
    )
    assert main(["--baseline", str(baseline), "--candidate", str(candidate)]) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "fail"
