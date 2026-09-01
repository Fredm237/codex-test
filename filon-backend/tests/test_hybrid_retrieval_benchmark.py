"""Benchmark autonome Phase 5 Hybrid Retrieval."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from quality_lab.hybrid_retrieval import (
    LIMITATION,
    LOCALES,
    SCENARIOS,
    VERTICALS,
    HybridRetrievalBenchmarkError,
    build_report,
)


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "quality" / "hybrid-retrieval-manifest.json"


def test_hybrid_retrieval_benchmark_is_ratified_without_promoting_oracle():
    report = build_report(MANIFEST)
    summary = report["summary"]
    assert summary["benchmark_status"] == "RATIFIED"
    assert summary["adapter_status"] == "QUALIFIED"
    assert summary["promotion_eligible"] is False
    assert summary["blocking_failures"] == 0
    assert all(summary["gate_results"].values())
    assert all(summary["support_results"].values())
    assert report["limitation"] == LIMITATION


def test_hybrid_retrieval_benchmark_has_power_and_all_strata():
    report = build_report(MANIFEST)
    metrics = report["metrics"]
    assert metrics["recall_at_50"]["cases"] >= 4_000
    assert metrics["no_match_accuracy"]["cases"] >= 2_000
    assert metrics["ambiguous_accuracy"]["cases"] >= 2_000
    assert metrics["constraint_violation_rate_top10"]["cases"] >= 1_000
    assert metrics["false_product_grouping_rate"]["cases"] >= 1_000
    assert metrics["semantic_only_false_resolution_rate"]["cases"] >= 1_000
    assert set(report["by_vertical"]) == set(VERTICALS)
    assert set(report["by_locale"]) == set(LOCALES)
    assert set(report["by_scenario"]) == set(SCENARIOS)
    assert all(report["by_vertical"][value]["cases"] > 0 for value in VERTICALS)
    assert all(report["by_locale"][value]["cases"] > 0 for value in LOCALES)


def test_legacy_offer_first_adapter_is_detected_as_unsafe():
    report = build_report(MANIFEST, adapter="legacy_offer_first")
    summary = report["summary"]
    assert summary["benchmark_status"] == "RATIFIED"
    assert summary["adapter_status"] == "UNSAFE"
    assert summary["promotion_eligible"] is False
    assert summary["blocking_failures"] > 0
    assert report["metrics"]["no_match_accuracy"]["rate"] == 0.0
    assert report["metrics"]["ambiguous_accuracy"]["rate"] == 0.0
    assert report["metrics"]["constraint_violation_rate_top10"]["violations"] > 0
    assert report["metrics"]["false_product_grouping_rate"]["false_groupings"] > 0
    assert report["metrics"]["semantic_only_false_resolution_rate"]["false_resolutions"] > 0


def test_lexical_adapter_is_safe_and_explicitly_incomplete_without_semantic_stage():
    report = build_report(MANIFEST, adapter="lexical")
    summary = report["summary"]
    assert summary["benchmark_status"] == "RATIFIED"
    assert summary["adapter_status"] == "SAFE_INCOMPLETE"
    assert summary["promotion_eligible"] is False
    assert summary["blocking_failures"] == 0
    assert report["metrics"]["recall_at_50"]["rate"] >= 0.95
    assert report["metrics"]["no_match_accuracy"]["ci95_lower"] >= 0.99
    assert report["metrics"]["constraint_violation_rate_top10"]["violations"] == 0
    assert report["metrics"]["false_product_grouping_rate"]["false_groupings"] == 0
    assert report["metrics"]["semantic_only_false_resolution_rate"]["false_resolutions"] == 0


def test_expand_only_adapter_passes_without_promoting_semantic_identity():
    report = build_report(MANIFEST, adapter="expanded")
    summary = report["summary"]
    assert summary["benchmark_status"] == "RATIFIED"
    assert summary["adapter_status"] == "QUALIFIED"
    assert summary["promotion_eligible"] is True
    assert summary["blocking_failures"] == 0
    assert summary["mismatches"] == 0
    assert all(summary["gate_results"].values())
    assert report["metrics"]["semantic_only_false_resolution_rate"]["false_resolutions"] == 0


def test_fused_adapter_passes_same_holdout_product_first():
    report = build_report(MANIFEST, adapter="fused")
    summary = report["summary"]
    assert summary["benchmark_status"] == "RATIFIED"
    assert summary["adapter_status"] == "QUALIFIED"
    assert summary["promotion_eligible"] is True
    assert summary["mismatches"] == 0
    assert summary["blocking_failures"] == 0
    assert all(summary["gate_results"].values())


def test_hybrid_retrieval_benchmark_is_reproducible():
    first = build_report(MANIFEST)
    second = build_report(MANIFEST)
    assert first["evaluation_id"] == second["evaluation_id"]
    assert first["corpus_sha256"] == second["corpus_sha256"]
    assert first["summary"] == second["summary"]
    assert first["metrics"] == second["metrics"]


@pytest.mark.parametrize(
    "mutation, message",
    [
        (lambda value: value.update(limitation="HUMAN_VALIDATED"), "limitation"),
        (lambda value: value["generator"].update(development_engine_input=True), "generator"),
        (lambda value: value["generator"].update(samples_per_vertical_seed=1), "generator"),
        (lambda value: value["gates"].update(recall_at_50_min=0.8), "ratified gates"),
        (lambda value: value["gates"].update(constraint_violations_max=1), "ratified gates"),
        (lambda value: value.update(verticals=["smartphones"]), "roster"),
    ],
)
def test_hybrid_retrieval_manifest_fails_closed(tmp_path: Path, mutation, message):
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    mutation(manifest)
    regression = ROOT / "quality" / manifest["regression_ground_truth"]
    (tmp_path / regression.name).write_text(regression.read_text(encoding="utf-8"), encoding="utf-8")
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(HybridRetrievalBenchmarkError, match=message):
        build_report(path)


def test_regressions_cannot_drop_scenario_locale_or_vertical(tmp_path: Path):
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    source = ROOT / "quality" / manifest["regression_ground_truth"]
    regressions = json.loads(source.read_text(encoding="utf-8"))
    regressions["cases"] = [case for case in regressions["cases"] if case["scenario"] != "semantic_only_unresolved"]
    (tmp_path / source.name).write_text(json.dumps(regressions), encoding="utf-8")
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(HybridRetrievalBenchmarkError, match="every scenario"):
        build_report(tmp_path / "manifest.json")
