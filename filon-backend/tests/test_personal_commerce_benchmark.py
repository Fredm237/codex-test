from pathlib import Path

from quality_lab.personal_commerce import evaluate_manifest


def test_personal_commerce_benchmark_is_fail_closed() -> None:
    manifest = Path(__file__).parents[2] / "quality" / "personal-commerce-manifest.json"
    report = evaluate_manifest(manifest)

    assert report["status"] == "PASS"
    assert report["metrics"] == {
        "total_cases": 12,
        "pass_rate": 1.0,
        "consent_bypasses": 0,
        "false_actions": 0,
        "scores_published": 0,
    }
    assert all(outcome["passed"] for outcome in report["outcomes"])
