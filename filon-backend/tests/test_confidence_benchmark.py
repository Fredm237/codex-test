from __future__ import annotations

import json
from pathlib import Path

import pytest

from quality_lab.confidence import ConfidenceBenchmarkError, run_benchmark


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "quality" / "confidence-manifest.json"


def test_confidence_passes_ece_brier_bucket_and_fail_closed_gates() -> None:
    report = run_benchmark(MANIFEST)
    assert report["support"] == {
        "total_predictions": 18000,
        "minimum_bucket_support": 3600,
    }
    assert report["metrics"]["expected_calibration_error"] == 0.0
    assert report["metrics"]["brier_score"] == 0.17
    assert report["metrics"]["unknown_promoted"] == 0
    assert report["metrics"]["synthetic_decision_confidence"] == 0
    assert report["metrics"]["provenance_completeness"] == 1.0
    assert report["engineering_passed"] is True
    assert report["quality_status"]["human_validation_required"] is False


def test_confidence_benchmark_is_deterministic() -> None:
    assert run_benchmark(MANIFEST)["evaluation_id"] == run_benchmark(MANIFEST)["evaluation_id"]


@pytest.mark.parametrize(
    ("key", "value", "message"),
    [
        ("limitation", None, "limitation"),
        ("dimensions", [], "dimensions"),
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
    with pytest.raises(ConfidenceBenchmarkError, match=message):
        run_benchmark(path)
