"""Gate autonome exact-product de Phase 1."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from quality_lab.product_identity import (
    LIMITATION,
    ProductIdentityBenchmarkError,
    VERTICALS,
    build_report,
)


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "quality" / "product-identity-manifest.json"


def test_product_identity_benchmark_passes_every_deterministic_gate():
    report = build_report(MANIFEST)
    assert report["summary"]["status"] == "PASS"
    assert report["summary"]["failed"] == 0
    assert all(report["summary"]["gate_results"].values())
    assert report["limitation"] == LIMITATION
    assert report["quality_status"] == "DETERMINISTICALLY_VERIFIED"
    assert report["generator"]["development_engine_input"] is False


def test_product_identity_benchmark_has_statistical_support_and_all_verticals():
    report = build_report(MANIFEST)
    metrics = report["metrics"]
    assert metrics["exact_product_accuracy"]["cases"] >= 900
    assert metrics["variant_resolution_accuracy"]["cases"] >= 3_800
    assert metrics["offer_attachment_accuracy"]["cases"] >= 2_800
    assert metrics["false_merge_rate"]["cases"] >= 2_800
    assert metrics["false_merge_rate"]["false_merges"] == 0
    assert metrics["false_merge_rate"]["ci95_upper"] <= 0.005
    assert set(report["by_vertical"]) == set(VERTICALS)
    assert all(
        report["by_vertical"][vertical]["cases"] >= 1_900
        for vertical in VERTICALS
    )


def test_product_identity_benchmark_is_reproducible():
    first = build_report(MANIFEST)
    second = build_report(MANIFEST)
    assert first["evaluation_id"] == second["evaluation_id"]
    assert first["summary"] == second["summary"]
    assert first["metrics"] == second["metrics"]


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value.update(limitation="HUMAN_VALIDATED"),
        lambda value: value["generator"].update(development_engine_input=True),
        lambda value: value["generator"].update(samples_per_vertical_seed=1),
        lambda value: value["gates"].update(blocking_failures_max=1),
        lambda value: value.update(verticals=["smartphones"]),
    ],
)
def test_product_identity_manifest_fails_closed(tmp_path: Path, mutation):
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    mutation(manifest)
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ProductIdentityBenchmarkError):
        build_report(path)


def test_regression_truth_cannot_silently_drop_a_vertical(tmp_path: Path):
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    regressions_path = ROOT / "quality" / manifest["regression_ground_truth"]
    regressions = json.loads(regressions_path.read_text(encoding="utf-8"))
    regressions["cases"] = [
        case for case in regressions["cases"] if case["vertical"] != "tv"
    ]
    (tmp_path / "regressions.json").write_text(
        json.dumps(regressions), encoding="utf-8"
    )
    manifest["regression_ground_truth"] = "regressions.json"
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ProductIdentityBenchmarkError, match="every vertical"):
        build_report(path)


def test_evaluation_identity_changes_when_manifest_changes(tmp_path: Path):
    original = build_report(MANIFEST)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    changed = deepcopy(manifest)
    changed["generator"]["seeds"] = [20260831, 31415926, 27182818, 16180339]
    regressions = ROOT / "quality" / changed["regression_ground_truth"]
    (tmp_path / regressions.name).write_text(
        regressions.read_text(encoding="utf-8"), encoding="utf-8"
    )
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(changed), encoding="utf-8")
    assert build_report(path)["evaluation_id"] != original["evaluation_id"]
