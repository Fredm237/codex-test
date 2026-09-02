from pathlib import Path

from quality_lab.fashion_v1 import evaluate_manifest


def test_fashion_v1_engineering_benchmark_is_fail_closed():
    manifest = Path(__file__).parents[2] / "quality" / "fashion-v1-manifest.json"
    report = evaluate_manifest(manifest)

    assert report["status"] == "PASS"
    assert report["limitation"] == "NO_EXTERNAL_HUMAN_GROUND_TRUTH"
    assert report["metrics"] == {
        "total_cases": 10,
        "decision_accuracy": 1.0,
        "selected_identity_accuracy": 1.0,
        "false_recommendations": 0,
        "uncalibrated_output_completeness": 1.0,
    }
    assert all(outcome["passed"] for outcome in report["outcomes"])
