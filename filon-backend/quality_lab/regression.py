"""Comparaison fail-closed de deux scorecards du FILON Quality Lab.

Une comparaison n'est mesurable que si les deux scorecards sont elles-memes
des preuves mesurables, portent sur le meme holdout et exposent exactement le
meme contrat de gates. Une incompatibilite produit ``not_measurable`` : elle ne
peut jamais etre transformee en faux succes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from .integrity import (
    DATASETS,
    FINGERPRINT_PATTERN,
    LAB_VERSION,
    atomic_write_text,
    canonical_json,
    require_identifier,
    strict_loads,
)
from .scorecard import GATE_CONTRACT, ensure_output_is_distinct


REGRESSION_SCHEMA_VERSION = "quality-regression/v1"
SCORECARD_SCHEMA_VERSION = "quality-scorecard/v1"
_OPERATORS = frozenset({"min", "max", "lt"})

ERROR_CODES = {
    "input": "QR001_SCORECARD_INVALID",
    "incompatible": "QR002_SCORECARDS_INCOMPATIBLE",
    "not_measurable": "QR003_SCORECARD_NOT_MEASURABLE",
    "output": "QR004_OUTPUT_INVALID",
}


def _error(code: str, message: str, *, path: str | None = None) -> dict[str, str]:
    value = {"code": code, "message": message}
    if path is not None:
        value["path"] = path
    return value


def _sort_errors(errors: Sequence[dict[str, str]]) -> list[dict[str, str]]:
    unique = {canonical_json(error): error for error in errors}
    return sorted(
        unique.values(),
        key=lambda error: (
            error.get("code", ""),
            error.get("path", ""),
            error.get("message", ""),
        ),
    )


def _sha256_bytes(payload: bytes) -> str:
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def _base_report() -> dict[str, Any]:
    return {
        "schema_version": REGRESSION_SCHEMA_VERSION,
        "evaluator_version": LAB_VERSION,
        "status": "not_measurable",
        "measurable": False,
        "regression": None,
        "baseline": {},
        "candidate": {},
        "gate_deltas": [],
        "errors": [],
    }


def _finite_number(value: Any) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(float(value))
    )


def _read_scorecard(path: str | Path, role: str) -> tuple[Any, str | None, list[dict[str, str]]]:
    try:
        file_path = Path(path).resolve()
    except (OSError, TypeError, ValueError):
        return None, None, [
            _error(ERROR_CODES["input"], f"{role} path is invalid", path=role)
        ]
    try:
        payload = file_path.read_bytes()
    except OSError:
        return None, None, [
            _error(
                ERROR_CODES["input"],
                f"{role} scorecard cannot be read",
                path=role,
            )
        ]
    try:
        value = strict_loads(payload, source=role)
    except ValueError as exc:
        return None, _sha256_bytes(payload), [
            _error(ERROR_CODES["input"], str(exc), path=role)
        ]
    return value, _sha256_bytes(payload), []


def _checked_adapters(
    value: Any, role: str, errors: list[dict[str, str]]
) -> dict[str, dict[str, str]]:
    if not isinstance(value, Mapping) or not value:
        errors.append(
            _error(
                ERROR_CODES["input"],
                f"{role} adapters must be a non-empty object",
                path=f"{role}/adapters",
            )
        )
        return {}
    if set(value) != set(DATASETS):
        errors.append(
            _error(
                ERROR_CODES["input"],
                f"{role} adapters must contain exactly the seven canonical datasets",
                path=f"{role}/adapters",
            )
        )
    checked: dict[str, dict[str, str]] = {}
    for dataset, config in value.items():
        try:
            checked_dataset = require_identifier(dataset, "adapter dataset")
        except ValueError as exc:
            errors.append(
                _error(ERROR_CODES["input"], str(exc), path=f"{role}/adapters")
            )
            continue
        if not isinstance(config, Mapping) or set(config) != {
            "engine_id",
            "engine_version",
        }:
            errors.append(
                _error(
                    ERROR_CODES["input"],
                    "adapter must contain only engine_id and engine_version",
                    path=f"{role}/adapters/{checked_dataset}",
                )
            )
            continue
        try:
            checked[checked_dataset] = {
                "engine_id": require_identifier(config.get("engine_id"), "engine_id"),
                "engine_version": require_identifier(
                    config.get("engine_version"), "engine_version"
                ),
            }
        except ValueError as exc:
            errors.append(
                _error(
                    ERROR_CODES["input"],
                    str(exc),
                    path=f"{role}/adapters/{checked_dataset}",
                )
            )
    return checked


def _checked_holdout(
    value: Any, role: str, errors: list[dict[str, str]]
) -> dict[str, dict[str, int]]:
    if not isinstance(value, Mapping) or set(value) != set(DATASETS):
        errors.append(
            _error(
                ERROR_CODES["input"],
                f"{role} holdout must contain exactly the seven canonical datasets",
                path=f"{role}/holdout",
            )
        )
        return {}
    checked: dict[str, dict[str, int]] = {}
    expected_fields = {"gold_cases", "prediction_cases", "joined_cases"}
    for dataset in DATASETS:
        counts = value[dataset]
        location = f"{role}/holdout/{dataset}"
        if not isinstance(counts, Mapping) or set(counts) != expected_fields:
            errors.append(
                _error(
                    ERROR_CODES["input"],
                    "holdout entry must contain only gold, prediction, "
                    "and joined counts",
                    path=location,
                )
            )
            continue
        if any(
            isinstance(counts[field], bool)
            or not isinstance(counts[field], int)
            or counts[field] <= 0
            for field in expected_fields
        ):
            errors.append(
                _error(
                    ERROR_CODES["input"],
                    "measurable holdout counts must be positive integers",
                    path=location,
                )
            )
            continue
        if len({counts[field] for field in expected_fields}) != 1:
            errors.append(
                _error(
                    ERROR_CODES["input"],
                    "measurable holdout counts must join exactly",
                    path=location,
                )
            )
            continue
        checked[dataset] = {
            field: counts[field] for field in sorted(expected_fields)
        }
    return checked


def _gate_passed(operator: str, value: float | int, threshold: float | int) -> bool:
    if operator == "min":
        return value >= threshold
    if operator == "lt":
        return value < threshold
    return value <= threshold


def _checked_gates(
    value: Any,
    metrics: Any,
    role: str,
    errors: list[dict[str, str]],
) -> dict[str, dict[str, Any]]:
    if not isinstance(value, list) or not value:
        errors.append(
            _error(
                ERROR_CODES["input"],
                f"{role} gates must be a non-empty array",
                path=f"{role}/gates",
            )
        )
        return {}
    if not isinstance(metrics, Mapping):
        errors.append(
            _error(
                ERROR_CODES["input"],
                f"{role} metrics must be an object",
                path=f"{role}/metrics",
            )
        )
        metrics = {}
    checked: dict[str, dict[str, Any]] = {}
    for index, gate in enumerate(value):
        location = f"{role}/gates/{index}"
        if not isinstance(gate, Mapping):
            errors.append(
                _error(ERROR_CODES["input"], "gate must be an object", path=location)
            )
            continue
        try:
            name = require_identifier(gate.get("gate"), "gate")
            metric = require_identifier(gate.get("metric"), "metric")
        except ValueError as exc:
            errors.append(_error(ERROR_CODES["input"], str(exc), path=location))
            continue
        if name in checked:
            errors.append(
                _error(
                    ERROR_CODES["input"],
                    f"duplicate gate {name!r}",
                    path=location,
                )
            )
            continue
        expected_contract = GATE_CONTRACT.get(name)
        if expected_contract is None:
            errors.append(
                _error(
                    ERROR_CODES["input"],
                    f"unknown canonical gate {name!r}",
                    path=location,
                )
            )
            continue
        operator = gate.get("operator")
        threshold = gate.get("threshold")
        measured = gate.get("value")
        passed = gate.get("passed")
        if operator not in _OPERATORS:
            errors.append(
                _error(ERROR_CODES["input"], "gate operator is invalid", path=location)
            )
            continue
        if (metric, operator) != expected_contract:
            errors.append(
                _error(
                    ERROR_CODES["input"],
                    "gate metric or operator differs from the canonical contract",
                    path=location,
                )
            )
            continue
        if not _finite_number(threshold) or not _finite_number(measured):
            errors.append(
                _error(
                    ERROR_CODES["input"],
                    "gate threshold and value must be finite numbers",
                    path=location,
                )
            )
            continue
        if not isinstance(passed, bool):
            errors.append(
                _error(ERROR_CODES["input"], "gate passed must be boolean", path=location)
            )
            continue
        metric_value = metrics.get(metric)
        if not _finite_number(metric_value) or float(metric_value) != float(measured):
            errors.append(
                _error(
                    ERROR_CODES["input"],
                    "gate value must equal its scorecard metric",
                    path=location,
                )
            )
            continue
        if passed != _gate_passed(operator, measured, threshold):
            errors.append(
                _error(
                    ERROR_CODES["input"],
                    "gate passed flag contradicts its operator and threshold",
                    path=location,
                )
            )
            continue
        checked[name] = {
            "gate": name,
            "metric": metric,
            "operator": operator,
            "threshold": threshold,
            "value": measured,
            "passed": passed,
        }
    if set(checked) != set(GATE_CONTRACT):
        errors.append(
            _error(
                ERROR_CODES["input"],
                f"{role} gates must contain the complete canonical gate roster",
                path=f"{role}/gates",
            )
        )
    return checked


def _validate_scorecard(
    value: Any, role: str
) -> tuple[dict[str, Any] | None, dict[str, dict[str, Any]], list[dict[str, str]]]:
    errors: list[dict[str, str]] = []
    if not isinstance(value, dict):
        return None, {}, [
            _error(
                ERROR_CODES["input"],
                f"{role} scorecard root must be an object",
                path=role,
            )
        ]
    if value.get("schema_version") != SCORECARD_SCHEMA_VERSION:
        errors.append(
            _error(
                ERROR_CODES["input"],
                f"{role} schema_version must be {SCORECARD_SCHEMA_VERSION}",
                path=f"{role}/schema_version",
            )
        )
    if value.get("evaluator_version") != LAB_VERSION:
        errors.append(
            _error(
                ERROR_CODES["input"],
                f"{role} evaluator_version must be {LAB_VERSION}",
                path=f"{role}/evaluator_version",
            )
        )
    for field in ("run_id", "system_version"):
        try:
            require_identifier(value.get(field), field)
        except ValueError as exc:
            errors.append(
                _error(ERROR_CODES["input"], str(exc), path=f"{role}/{field}")
            )
    for field in (
        "gold_manifest_sha256",
        "manifest_fingerprint",
        "holdout_fingerprint",
    ):
        field_value = value.get(field)
        if not isinstance(field_value, str) or not FINGERPRINT_PATTERN.fullmatch(
            field_value
        ):
            errors.append(
                _error(
                    ERROR_CODES["input"],
                    f"{role} {field} is invalid",
                    path=f"{role}/{field}",
                )
            )
    status = value.get("status")
    measurable = value.get("measurable")
    if status not in {"pass", "fail"} or measurable is not True:
        errors.append(
            _error(
                ERROR_CODES["not_measurable"],
                f"{role} must be a measurable pass or fail scorecard",
                path=f"{role}/status",
            )
        )
    scorecard_errors = value.get("errors")
    if not isinstance(scorecard_errors, list) or scorecard_errors:
        errors.append(
            _error(
                ERROR_CODES["input"],
                f"{role} measurable scorecard must have no errors",
                path=f"{role}/errors",
            )
        )
    _checked_holdout(value.get("holdout"), role, errors)
    _checked_adapters(value.get("adapters"), role, errors)
    gates = _checked_gates(value.get("gates"), value.get("metrics"), role, errors)
    if status == "pass" and gates and not all(gate["passed"] for gate in gates.values()):
        errors.append(
            _error(
                ERROR_CODES["input"],
                f"{role} pass status contradicts a failed gate",
                path=f"{role}/status",
            )
        )
    if status == "fail" and gates and all(gate["passed"] for gate in gates.values()):
        errors.append(
            _error(
                ERROR_CODES["input"],
                f"{role} fail status requires at least one failed gate",
                path=f"{role}/status",
            )
        )
    return value, gates, errors


def _identity(scorecard: Mapping[str, Any], digest: str) -> dict[str, Any]:
    return {
        "scorecard_sha256": digest,
        "run_id": scorecard["run_id"],
        "system_version": scorecard["system_version"],
        "status": scorecard["status"],
        "holdout_fingerprint": scorecard["holdout_fingerprint"],
        "adapters": scorecard["adapters"],
    }


def _gate_contract(gates: Mapping[str, Mapping[str, Any]]) -> dict[str, tuple[Any, ...]]:
    return {
        name: (
            gate["metric"],
            gate["operator"],
            gate["threshold"],
        )
        for name, gate in gates.items()
    }


def compare_scorecards(
    baseline_path: str | Path,
    candidate_path: str | Path,
) -> dict[str, Any]:
    """Compare deux snapshots stricts et retourne un rapport deterministe."""

    report = _base_report()
    baseline_raw, baseline_sha256, baseline_read_errors = _read_scorecard(
        baseline_path, "baseline"
    )
    candidate_raw, candidate_sha256, candidate_read_errors = _read_scorecard(
        candidate_path, "candidate"
    )
    baseline, baseline_gates, baseline_errors = _validate_scorecard(
        baseline_raw, "baseline"
    )
    candidate, candidate_gates, candidate_errors = _validate_scorecard(
        candidate_raw, "candidate"
    )
    errors = [
        *baseline_read_errors,
        *candidate_read_errors,
        *baseline_errors,
        *candidate_errors,
    ]
    if baseline is not None and baseline_sha256 is not None:
        report["baseline"] = {
            "scorecard_sha256": baseline_sha256,
            "run_id": baseline.get("run_id"),
            "system_version": baseline.get("system_version"),
            "status": baseline.get("status"),
        }
    if candidate is not None and candidate_sha256 is not None:
        report["candidate"] = {
            "scorecard_sha256": candidate_sha256,
            "run_id": candidate.get("run_id"),
            "system_version": candidate.get("system_version"),
            "status": candidate.get("status"),
        }
    if errors:
        report["errors"] = _sort_errors(errors)
        return report
    assert baseline is not None and candidate is not None
    assert baseline_sha256 is not None and candidate_sha256 is not None

    incompatibilities: list[dict[str, str]] = []
    for field in (
        "schema_version",
        "evaluator_version",
        "gold_manifest_sha256",
        "manifest_fingerprint",
        "holdout_fingerprint",
        "holdout",
    ):
        try:
            equal = canonical_json(baseline[field]) == canonical_json(candidate[field])
        except (KeyError, ValueError):
            equal = False
        if not equal:
            incompatibilities.append(
                _error(
                    ERROR_CODES["incompatible"],
                    f"baseline and candidate {field} differ",
                    path=field,
                )
            )
    if set(baseline["adapters"]) != set(candidate["adapters"]):
        incompatibilities.append(
            _error(
                ERROR_CODES["incompatible"],
                "baseline and candidate adapter rosters differ",
                path="adapters",
            )
        )
    if baseline["run_id"] == candidate["run_id"]:
        incompatibilities.append(
            _error(
                ERROR_CODES["incompatible"],
                "baseline and candidate must identify distinct runs",
                path="run_id",
            )
        )
    if _gate_contract(baseline_gates) != _gate_contract(candidate_gates):
        incompatibilities.append(
            _error(
                ERROR_CODES["incompatible"],
                "baseline and candidate gate contracts differ",
                path="gates",
            )
        )
    report["baseline"] = _identity(baseline, baseline_sha256)
    report["candidate"] = _identity(candidate, candidate_sha256)
    if incompatibilities:
        report["errors"] = _sort_errors(incompatibilities)
        return report

    deltas: list[dict[str, Any]] = []
    for name in sorted(baseline_gates):
        before = baseline_gates[name]
        after = candidate_gates[name]
        raw_delta = float(after["value"]) - float(before["value"])
        directional_delta = raw_delta if before["operator"] == "min" else -raw_delta
        if directional_delta > 0:
            movement = "improved"
        elif directional_delta < 0:
            movement = "degraded"
        else:
            movement = "unchanged"
        deltas.append(
            {
                "gate": name,
                "metric": before["metric"],
                "operator": before["operator"],
                "threshold": before["threshold"],
                "baseline_value": before["value"],
                "candidate_value": after["value"],
                "delta": raw_delta,
                "directional_delta": directional_delta,
                "movement": movement,
                "baseline_passed": before["passed"],
                "candidate_passed": after["passed"],
                "gate_regression": before["passed"] and not after["passed"],
            }
        )
    report["gate_deltas"] = deltas
    report["measurable"] = True
    report["regression"] = candidate["status"] == "fail"
    report["status"] = "fail" if report["regression"] else "pass"
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compare deux scorecards FILON sans masquer les incompatibilites"
    )
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)

    report = compare_scorecards(args.baseline, args.candidate)
    if args.output:
        try:
            ensure_output_is_distinct(
                args.output,
                {Path(args.baseline).resolve(), Path(args.candidate).resolve()},
            )
            atomic_write_text(args.output, canonical_json(report) + "\n")
        except (OSError, TypeError, ValueError) as exc:
            report = _base_report()
            report["errors"] = [
                _error(ERROR_CODES["output"], str(exc), path="output")
            ]
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    if report["status"] == "pass":
        return 0
    if report["status"] == "fail":
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
