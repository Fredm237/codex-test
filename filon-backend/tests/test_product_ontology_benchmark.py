"""Benchmark autonome Phase 4 Product Ontology."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from quality_lab.product_ontology import (
    LIMITATION,
    ROLES,
    VERTICALS,
    ProductOntologyBenchmarkError,
    build_report,
)


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "quality" / "product-ontology-manifest.json"


def test_product_ontology_benchmark_is_ratified_without_promoting_the_oracle():
    report = build_report(MANIFEST)
    summary = report["summary"]
    assert summary["benchmark_status"] == "RATIFIED"
    assert summary["adapter_status"] == "QUALIFIED"
    assert summary["promotion_eligible"] is False
    assert summary["blocking_failures"] == 0
    assert all(summary["gate_results"].values())
    assert all(summary["support_results"].values())
    assert report["limitation"] == LIMITATION


def test_product_ontology_benchmark_has_power_and_full_rosters():
    report = build_report(MANIFEST)
    metrics = report["metrics"]
    assert metrics["known_role_accuracy"]["cases"] >= 3_000
    assert metrics["unknown_abstention_accuracy"]["cases"] >= 3_000
    assert metrics["false_primary_product_rate"]["cases"] >= 3_000
    assert metrics["false_primary_product_rate"]["ci95_upper"] <= 0.005
    assert metrics["canonical_relation_false_promotion_rate"]["cases"] >= 3_000
    assert metrics["canonical_relation_false_promotion_rate"]["ci95_upper"] <= 0.005
    assert set(report["by_role"]) == set(ROLES)
    assert set(report["by_vertical"]) == set(VERTICALS)
    assert all(report["by_role"][role]["cases"] > 0 for role in ROLES)


def test_legacy_adapter_is_measured_as_unsafe_not_silently_promoted():
    report = build_report(MANIFEST, adapter="legacy")
    summary = report["summary"]
    assert summary["benchmark_status"] == "RATIFIED"
    assert summary["adapter_status"] == "UNSAFE"
    assert summary["promotion_eligible"] is False
    assert summary["blocking_failures"] > 0
    assert report["metrics"]["false_primary_product_rate"]["false_primary_products"] > 0
    assert report["metrics"]["canonical_relation_false_promotion_rate"]["canonical_promotions"] == 0
    assert report["by_role"]["ACCOMMODATION"]["mismatches"] > 0


def test_fail_closed_extractor_passes_the_ratified_holdout():
    report = build_report(MANIFEST, adapter="extractor")
    summary = report["summary"]
    assert summary["benchmark_status"] == "RATIFIED"
    assert summary["adapter_status"] == "QUALIFIED"
    assert summary["promotion_eligible"] is True
    assert summary["blocking_failures"] == 0
    assert all(summary["gate_results"].values())


def test_product_ontology_benchmark_is_reproducible():
    first = build_report(MANIFEST)
    second = build_report(MANIFEST)
    assert first["evaluation_id"] == second["evaluation_id"]
    assert first["corpus_sha256"] == second["corpus_sha256"]
    assert first["summary"] == second["summary"]


@pytest.mark.parametrize(
    "mutation, message",
    [
        (lambda value: value.update(limitation="HUMAN_VALIDATED"), "limitation"),
        (lambda value: value["generator"].update(development_engine_input=True), "generator"),
        (lambda value: value["generator"].update(samples_per_vertical_seed=1), "generator"),
        (lambda value: value["gates"].update(false_primary_product_rate_ci95_upper_max=0.01), "0.5 percent"),
        (lambda value: value["gates"].update(blocking_failures_max=1), "failure budget"),
        (lambda value: value.update(roles=["PRIMARY_PRODUCT", "UNKNOWN"]), "roster"),
    ],
)
def test_product_ontology_manifest_fails_closed(tmp_path: Path, mutation, message):
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    mutation(manifest)
    regressions = ROOT / "quality" / manifest["regression_ground_truth"]
    (tmp_path / regressions.name).write_text(regressions.read_text(encoding="utf-8"), encoding="utf-8")
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ProductOntologyBenchmarkError, match=message):
        build_report(path)


def test_product_ontology_regressions_cannot_drop_a_role(tmp_path: Path):
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    source = ROOT / "quality" / manifest["regression_ground_truth"]
    regressions = json.loads(source.read_text(encoding="utf-8"))
    regressions["cases"] = [case for case in regressions["cases"] if case["expected_role"] != "BUNDLE"]
    (tmp_path / source.name).write_text(json.dumps(regressions), encoding="utf-8")
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ProductOntologyBenchmarkError, match="every role"):
        build_report(tmp_path / "manifest.json")


def test_evaluation_identity_commits_to_regression_content(tmp_path: Path):
    original = build_report(MANIFEST)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    source = ROOT / "quality" / manifest["regression_ground_truth"]
    regressions = json.loads(source.read_text(encoding="utf-8"))
    changed = deepcopy(regressions)
    changed["cases"][0]["truth_basis"] = "EXPLICIT_SOLD_OBJECT_V2"
    (tmp_path / source.name).write_text(json.dumps(changed), encoding="utf-8")
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    assert build_report(tmp_path / "manifest.json")["evaluation_id"] != original["evaluation_id"]
