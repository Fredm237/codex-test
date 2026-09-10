from __future__ import annotations

import json
from pathlib import Path

import pytest

from quality_lab.product_ranking_v2 import (
    ProductRankingV2BenchmarkError,
    _load_manifest,
    generate_cases,
    run_benchmark,
)


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "quality" / "product-ranking-v2-manifest.json"


def test_product_ranking_v2_passes_evidence_scoped_quality_gate() -> None:
    report = run_benchmark(MANIFEST)
    assert report["support"] == {
        "total_cases": 6048,
        "optional_unknown_cases": 672,
        "required_unknown_cases": 1344,
        "known_unsourced_required_cases": 672,
        "invalid_optional_cases": 672,
        "ineligible_cases": 672,
        "commission_mutation_cases": 672,
    }
    assert report["metrics"] == {
        "order_accuracy": {
            "successes": 6048,
            "cases": 6048,
            "rate": 1.0,
            "ci95_lower": 0.99936524,
            "ci95_upper": 1.0,
        },
        "top1_accuracy": 1.0,
        "required_unknown_ranked": 0,
        "known_unsourced_required_ranked": 0,
        "invalid_optional_ranked": 0,
        "ineligible_ranked": 0,
        "optional_unknown_disclosure": 1.0,
        "provenance_completeness": 1.0,
        "determinism_failures": 0,
        "commission_invariance_failures": 0,
    }
    assert all(report["engineering_gates"].values())
    assert report["engineering_passed"] is True
    assert report["passed"] is True
    assert report["claim_boundary"] == {
        "ranking_is_product_quality_claim": False,
        "ranking_is_offer_selection": False,
        "ranking_is_buy_wait_verdict": False,
        "unknown_dimension_receives_score": False,
    }


def test_product_ranking_v2_holdout_is_reproducible() -> None:
    manifest = _load_manifest(MANIFEST)
    assert generate_cases(manifest) == generate_cases(manifest)
    assert run_benchmark(MANIFEST)["evaluation_id"] == run_benchmark(MANIFEST)["evaluation_id"]


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (("policy", "commercial_first"), "policy"),
        (("engineering_gates", {}), "engineering gates"),
        (("claim_boundary", {}), "claim boundary"),
        (("evaluation_governance", {}), "evaluation governance"),
    ],
)
def test_product_ranking_v2_manifest_mutations_fail_closed(
    tmp_path: Path,
    mutation: tuple[str, object],
    message: str,
) -> None:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    payload[mutation[0]] = mutation[1]
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ProductRankingV2BenchmarkError, match=message):
        run_benchmark(path)
