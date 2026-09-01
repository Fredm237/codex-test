from __future__ import annotations

import json
from pathlib import Path

import pytest

from quality_lab.product_ranking import (
    ProductRankingBenchmarkError,
    _load_manifest,
    generate_cases,
    run_benchmark,
)


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "quality" / "product-ranking-manifest.json"


def test_product_ranking_passes_engineering_holdout_without_faking_human_labels() -> None:
    report = run_benchmark(MANIFEST)
    assert report["support"] == {
        "total_cases": 4608,
        "unknown_cases": 720,
        "ineligible_cases": 720,
        "affiliate_mutation_cases": 720,
    }
    assert report["metrics"]["ineligible_ranked"] == 0
    assert report["metrics"]["unknown_ranked"] == 0
    assert report["metrics"]["affiliate_invariance_failures"] == 0
    assert report["metrics"]["provenance_completeness"] == 1.0
    assert report["engineering_passed"] is True
    assert report["human_preference"] == {
        "external_labels": 0,
        "minimum_required": 200,
        "status": "PENDING_EXTERNAL_GROUND_TRUTH",
    }
    assert report["phase_gate_passed"] is False
    assert report["passed"] is False


def test_legacy_universal_commercial_ranking_is_detected_as_unsafe() -> None:
    report = run_benchmark(MANIFEST, adapter="legacy_universal_commercial")
    assert report["metrics"]["ineligible_ranked"] > 0
    assert report["metrics"]["unknown_ranked"] > 0
    assert report["metrics"]["affiliate_invariance_failures"] > 0
    assert report["engineering_passed"] is False


def test_holdout_is_reproducible_and_stratified() -> None:
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
        (("policy", "commercial_first"), "policy"),
        (("engineering_gates", {}), "engineering gates"),
        (("phase_gate", {}), "human preference phase gate"),
    ],
)
def test_manifest_mutations_fail_closed(tmp_path: Path, mutation, message: str) -> None:
    payload = json.loads(MANIFEST.read_text())
    key, value = mutation
    if value is None:
        payload.pop(key)
    else:
        payload[key] = value
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(payload))
    with pytest.raises(ProductRankingBenchmarkError, match=message):
        run_benchmark(path)
