from __future__ import annotations

import json
from pathlib import Path

import pytest

from quality_lab.offer_optimization import (
    OfferOptimizationBenchmarkError,
    _load_manifest,
    generate_cases,
    run_benchmark,
)


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "quality" / "offer-optimization-manifest.json"


def test_offer_optimization_passes_autonomous_engineering_gate() -> None:
    report = run_benchmark(MANIFEST)
    assert report["support"] == {
        "total_cases": 4608,
        "unknown_cases": 864,
        "ineligible_cases": 1440,
        "affiliate_mutation_cases": 720,
    }
    assert report["metrics"]["ineligible_selected"] == 0
    assert report["metrics"]["unknown_selected"] == 0
    assert report["metrics"]["affiliate_invariance_failures"] == 0
    assert report["metrics"]["provenance_completeness"] == 1.0
    assert report["engineering_passed"] is True
    assert report["quality_status"]["external_human_ground_truth"] == "NO_EXTERNAL_HUMAN_GROUND_TRUTH"
    assert report["quality_status"]["human_validation_required"] is False


def test_legacy_commercial_optimizer_is_detected_as_unsafe() -> None:
    report = run_benchmark(MANIFEST, adapter="legacy_commercial")
    assert report["metrics"]["ineligible_selected"] > 0
    assert report["metrics"]["unknown_selected"] > 0
    assert report["metrics"]["affiliate_invariance_failures"] > 0
    assert report["engineering_passed"] is False


def test_holdout_is_reproducible_and_stratified() -> None:
    manifest = _load_manifest(MANIFEST)
    first = generate_cases(manifest)
    second = generate_cases(manifest)
    assert first == second
    assert {case.scenario for case in first} == set(manifest["scenarios"])
    assert run_benchmark(MANIFEST)["evaluation_id"] == run_benchmark(MANIFEST)["evaluation_id"]


@pytest.mark.parametrize(
    ("key", "value", "message"),
    [
        ("limitation", None, "limitation"),
        ("policy", "commercial_first", "policy"),
        ("engineering_gates", {}, "engineering gates"),
        ("evaluation_governance", {}, "autonomous evaluation governance"),
    ],
)
def test_manifest_mutations_fail_closed(tmp_path: Path, key: str, value, message: str) -> None:
    payload = json.loads(MANIFEST.read_text())
    if value is None:
        payload.pop(key)
    else:
        payload[key] = value
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(payload))
    with pytest.raises(OfferOptimizationBenchmarkError, match=message):
        run_benchmark(path)
