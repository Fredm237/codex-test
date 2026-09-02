from pathlib import Path

from quality_lab.solution_composer import evaluate_manifest


def test_solution_composer_benchmark_is_fail_closed() -> None:
    manifest = Path(__file__).parents[2] / "quality" / "solution-composer-manifest.json"
    report = evaluate_manifest(manifest)

    assert report["status"] == "PASS"
    assert report["metrics"] == {
        "total_cases": 12,
        "pass_rate": 1.0,
        "false_compositions": 0,
        "owned_first_violations": 0,
        "scores_published": 0,
    }
    assert all(outcome["passed"] for outcome in report["outcomes"])
