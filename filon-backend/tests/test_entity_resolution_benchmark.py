"""Benchmark autonome Phase 2 Entity Resolution."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from quality_lab.entity_resolution import (
    LIMITATION,
    VERTICALS,
    EntityResolutionBenchmarkError,
    build_report,
    exact_gtin_baseline,
)


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "quality" / "entity-resolution-manifest.json"


def test_entity_resolution_benchmark_is_ratified_but_baseline_is_not_promotable():
    report = build_report(MANIFEST)
    summary = report["summary"]
    assert summary["benchmark_status"] == "RATIFIED"
    assert summary["baseline_status"] == "SAFE_INCOMPLETE"
    assert summary["promotion_eligible"] is False
    assert all(summary["safety_gate_results"].values())
    assert not any(summary["coverage_gate_results"].values())
    assert all(summary["support_gate_results"].values())
    assert report["limitation"] == LIMITATION
    assert report["generator"]["development_engine_input"] is False


def test_entity_resolution_benchmark_has_statistical_power_and_all_verticals():
    report = build_report(MANIFEST)
    metrics = report["metrics"]
    assert metrics["false_merge_rate"]["cases"] >= 2_800
    assert metrics["false_merge_rate"]["false_merges"] == 0
    assert metrics["false_merge_rate"]["ci95_upper"] <= 0.005
    assert metrics["exact_preservation_accuracy"]["cases"] >= 900
    assert metrics["exact_preservation_accuracy"]["ci95_lower"] >= 0.98
    assert metrics["known_structured_positive_resolution"]["cases"] >= 900
    assert metrics["known_structured_positive_resolution"]["successes"] == 0
    assert metrics["known_structured_positive_abstention_rate"]["rate"] == 1.0
    assert metrics["known_structured_positive_abstention_rate"]["abstentions"] >= 900
    assert set(report["by_vertical"]) == set(VERTICALS)
    assert all(report["by_vertical"][vertical]["cases"] >= 1_300 for vertical in VERTICALS)


def test_entity_resolution_target_and_abstention_budget_are_fail_closed():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    gates = manifest["gates"]
    assert gates["false_merge_rate_ci95_upper_max"] == 0.005
    assert gates["known_conflict_promotions_max"] == 0
    assert gates["known_structured_positive_resolution_ci95_lower_min"] == 0.8
    assert gates["known_structured_positive_abstention_rate_ci95_upper_max"] == 0.2


def test_exact_gtin_baseline_never_uses_weak_or_structured_signals_as_fallback():
    structured = {
        "brand": "Example",
        "mpn": "ABC-123",
        "model": "Model Pro",
        "attributes": {"storage": "128GB"},
        "title": "Model Pro 128GB",
        "image": "https://example.test/same.jpg",
    }
    assert exact_gtin_baseline(structured, deepcopy(structured)) == "abstain"
    assert exact_gtin_baseline(
        {**structured, "identifiers": {"ean": "4006381333931"}},
        {**structured, "identifiers": {"gtin": "4006381333931"}},
    ) == "same"
    assert exact_gtin_baseline(
        {**structured, "identifiers": {"ean": "4006381333931"}},
        {**structured, "identifiers": {"ean": "9780201379624"}},
    ) == "abstain"


def test_entity_resolution_benchmark_is_reproducible():
    first = build_report(MANIFEST)
    second = build_report(MANIFEST)
    assert first["evaluation_id"] == second["evaluation_id"]
    assert first["summary"] == second["summary"]
    assert first["metrics"] == second["metrics"]


def test_multi_signal_resolver_passes_the_ratified_synthetic_holdout():
    report = build_report(MANIFEST, adapter="multi")
    summary = report["summary"]
    assert summary["benchmark_status"] == "RATIFIED"
    assert summary["baseline_status"] == "QUALIFIED"
    assert summary["promotion_eligible"] is True
    assert all(summary["safety_gate_results"].values())
    assert all(summary["coverage_gate_results"].values())
    assert report["metrics"]["false_merge_rate"]["false_merges"] == 0
    assert report["metrics"]["known_structured_positive_resolution"]["successes"] >= 900


@pytest.mark.parametrize(
    "mutation, message",
    [
        (lambda value: value.update(limitation="HUMAN_VALIDATED"), "limitation"),
        (lambda value: value["generator"].update(development_engine_input=True), "generator"),
        (lambda value: value["generator"].update(samples_per_vertical_seed=1), "generator"),
        (lambda value: value["gates"].update(false_merge_rate_ci95_upper_max=0.01), "0.5 percent"),
        (lambda value: value["gates"].update(known_conflict_promotions_max=1), "promotion budget"),
        (lambda value: value.update(verticals=["smartphones"]), "roster"),
    ],
)
def test_entity_resolution_manifest_fails_closed(tmp_path: Path, mutation, message):
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    mutation(manifest)
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(EntityResolutionBenchmarkError, match=message):
        build_report(path)


def test_entity_resolution_regressions_cannot_drop_a_vertical(tmp_path: Path):
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    regressions_path = ROOT / "quality" / manifest["regression_ground_truth"]
    regressions = json.loads(regressions_path.read_text(encoding="utf-8"))
    regressions["cases"] = [
        case for case in regressions["cases"] if case["vertical"] != "tyres"
    ]
    (tmp_path / "regressions.json").write_text(json.dumps(regressions), encoding="utf-8")
    manifest["regression_ground_truth"] = "regressions.json"
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(EntityResolutionBenchmarkError, match="every vertical"):
        build_report(path)
