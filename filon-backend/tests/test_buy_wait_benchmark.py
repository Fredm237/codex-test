from __future__ import annotations

import json
from pathlib import Path

import pytest

from quality_lab.buy_wait import BuyWaitBenchmarkError, run_benchmark


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "quality" / "buy-wait-v2-manifest.json"


def test_buy_wait_temporal_backtest_passes_fail_closed_gates() -> None:
    report = run_benchmark(MANIFEST)
    assert report["support"] == {"total_cases": 7200, "actionable_cases": 3600}
    assert report["metrics"]["action_accuracy"] == 1.0
    assert report["metrics"]["action_accuracy_wilson_lower"] >= 0.995
    assert report["metrics"]["wrong_direction"] == 0
    assert report["metrics"]["unsupported_action"] == 0
    assert report["metrics"]["future_leakage"] == 0
    assert report["metrics"]["provenance_completeness"] == 1.0
    assert report["engineering_passed"] is True
    assert report["quality_status"]["human_validation_required"] is False


def test_buy_wait_backtest_is_deterministic() -> None:
    assert run_benchmark(MANIFEST)["evaluation_id"] == run_benchmark(MANIFEST)["evaluation_id"]


@pytest.mark.parametrize(
    ("key", "value", "message"),
    [
        ("limitation", None, "limitation"),
        ("policy_version", "legacy", "policy version"),
        ("generator", {}, "generator configuration"),
        ("engineering_gates", {}, "engineering gates"),
        ("evaluation_governance", {}, "autonomous evaluation governance"),
    ],
)
def test_buy_wait_manifest_mutations_fail_closed(
    tmp_path: Path, key: str, value, message: str
) -> None:
    payload = json.loads(MANIFEST.read_text())
    if value is None:
        payload.pop(key)
    else:
        payload[key] = value
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(payload))
    with pytest.raises(BuyWaitBenchmarkError, match=message):
        run_benchmark(path)
