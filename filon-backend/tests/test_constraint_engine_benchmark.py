from __future__ import annotations

import json
from pathlib import Path

import pytest

from quality_lab.constraint_engine import (
    ConstraintBenchmarkError,
    _load_manifest,
    generate_cases,
    run_benchmark,
)


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "quality" / "constraint-engine-manifest.json"


def test_constraint_engine_passes_ratified_holdout():
    report = run_benchmark(MANIFEST)
    assert report["support"] == {
        "total_cases": 4608,
        "eligible_cases": 1584,
        "exclusion_cases": 2304,
        "unknown_cases": 720,
        "preference_cases": 720,
    }
    assert report["metrics"]["false_eligible"] == 0
    assert report["metrics"]["unknown_satisfied"] == 0
    assert report["metrics"]["preference_reintroductions"] == 0
    assert report["metrics"]["provenance_completeness"] == 1.0
    assert report["passed"] is True
    assert all(report["gates"].values())


def test_legacy_preference_first_is_detected_as_unsafe():
    report = run_benchmark(MANIFEST, adapter="legacy_preference_first")
    assert report["metrics"]["false_eligible"] > 0
    assert report["metrics"]["unknown_satisfied"] > 0
    assert report["metrics"]["preference_reintroductions"] > 0
    assert report["passed"] is False


def test_holdout_is_reproducible_and_stratified():
    manifest = _load_manifest(MANIFEST)
    first = generate_cases(manifest)
    second = generate_cases(manifest)
    assert first == second
    assert {case.vertical for case in first} == set(manifest["verticals"])
    assert {case.locale for case in first} == set(manifest["locales"])
    assert {case.scenario for case in first} == set(manifest["scenarios"])
    assert run_benchmark(MANIFEST)["evaluation_id"] == run_benchmark(MANIFEST)["evaluation_id"]


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (("limitation", None), "limitation"),
        (("policy", "preferences_first"), "policy"),
        (("gates", {}), "gates"),
    ],
)
def test_manifest_mutations_fail_closed(tmp_path: Path, mutation, message):
    payload = json.loads(MANIFEST.read_text())
    key, value = mutation
    if value is None:
        payload.pop(key)
    else:
        payload[key] = value
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(payload))
    with pytest.raises(ConstraintBenchmarkError, match=message):
        run_benchmark(path)
