"""Gate autonome Phase 3 Offer Truth."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from quality_lab.offer_truth import (
    CLAIMS,
    LIMITATION,
    OfferTruthBenchmarkError,
    build_report,
)


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "quality" / "offer-truth-manifest.json"


def test_offer_truth_benchmark_passes_every_deterministic_gate():
    report = build_report(MANIFEST)
    assert report["summary"]["status"] == "PASS"
    assert report["summary"]["promotion_eligible"] is False
    assert report["summary"]["failed"] == 0
    assert all(report["summary"]["gate_results"].values())
    assert all(report["summary"]["support_results"].values())
    assert report["limitation"] == LIMITATION


def test_offer_truth_benchmark_has_power_and_covers_every_claim():
    report = build_report(MANIFEST)
    metrics = report["metrics"]
    assert metrics["overall_correctness"]["cases"] >= 10_000
    assert metrics["known_claim_accuracy"]["cases"] >= 3_000
    assert metrics["safe_abstention_accuracy"]["cases"] >= 5_000
    assert metrics["dangerous_fallback_rate"]["dangerous_fallbacks"] == 0
    assert metrics["dangerous_fallback_rate"]["ci95_upper"] <= 0.005
    assert set(report["by_claim"]) == set(CLAIMS)
    assert all(report["by_claim"][claim]["cases"] > 0 for claim in CLAIMS)


def test_offer_truth_benchmark_is_reproducible():
    first = build_report(MANIFEST)
    second = build_report(MANIFEST)
    assert first["evaluation_id"] == second["evaluation_id"]
    assert first["summary"] == second["summary"]
    assert first["metrics"] == second["metrics"]


def test_offer_truth_extractor_passes_the_ratified_holdout():
    report = build_report(MANIFEST, adapter="extractor")
    assert report["summary"]["status"] == "PASS"
    assert report["summary"]["failed"] == 0
    assert all(report["summary"]["gate_results"].values())
    assert report["summary"]["promotion_eligible"] is False


@pytest.mark.parametrize(
    "mutation, message",
    [
        (lambda value: value.update(limitation="HUMAN_VALIDATED"), "limitation"),
        (lambda value: value["generator"].update(development_engine_input=True), "generator"),
        (lambda value: value["generator"].update(samples_per_seed=1), "generator"),
        (lambda value: value["gates"].update(blocking_failures_max=1), "failure budget"),
        (lambda value: value["gates"].update(dangerous_fallback_rate_ci95_upper_max=0.01), "0.5 percent"),
        (lambda value: value.update(claims=["price"]), "roster"),
    ],
)
def test_offer_truth_manifest_fails_closed(tmp_path: Path, mutation, message):
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    mutation(manifest)
    regressions = ROOT / "quality" / manifest["regression_ground_truth"]
    (tmp_path / regressions.name).write_text(regressions.read_text(encoding="utf-8"), encoding="utf-8")
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(OfferTruthBenchmarkError, match=message):
        build_report(path)


def test_offer_truth_regressions_cannot_drop_a_claim(tmp_path: Path):
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    source = ROOT / "quality" / manifest["regression_ground_truth"]
    regressions = json.loads(source.read_text(encoding="utf-8"))
    regressions["cases"] = [case for case in regressions["cases"] if case["claim"] != "warranty"]
    (tmp_path / source.name).write_text(json.dumps(regressions), encoding="utf-8")
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(OfferTruthBenchmarkError, match="every claim"):
        build_report(tmp_path / "manifest.json")


def test_evaluation_identity_changes_with_manifest(tmp_path: Path):
    original = build_report(MANIFEST)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    changed = deepcopy(manifest)
    changed["generator"]["seeds"] = [20260901, 31415926, 27182818, 16180339, 57721566]
    regressions = ROOT / "quality" / changed["regression_ground_truth"]
    (tmp_path / regressions.name).write_text(regressions.read_text(encoding="utf-8"), encoding="utf-8")
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(changed), encoding="utf-8")
    assert build_report(path)["evaluation_id"] != original["evaluation_id"]


def test_evaluation_identity_commits_to_regression_content(tmp_path: Path):
    original = build_report(MANIFEST)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    source = ROOT / "quality" / manifest["regression_ground_truth"]
    regressions = json.loads(source.read_text(encoding="utf-8"))
    regressions["cases"][0]["truth_basis"] = "EXPLICIT_MONEY_FIELDS_V2"
    (tmp_path / source.name).write_text(json.dumps(regressions), encoding="utf-8")
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    assert build_report(path)["evaluation_id"] != original["evaluation_id"]
