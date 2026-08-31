"""Qualification du Quality Lab autonome, sans fausse ground truth humaine."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from quality_lab import autonomous


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "quality" / "autonomous-manifest.json"


def test_autonomous_lab_passes_only_objective_gates():
    report = autonomous.build_report(MANIFEST)

    assert report["mandate_status"] == "AUTONOMOUS_QUALITY_LAB"
    assert report["limitation"] == "NO_EXTERNAL_HUMAN_GROUND_TRUTH"
    assert report["summary"] == {
        "checks": 571,
        "passed": 571,
        "failed": 0,
        "unresolved": 1,
        "blocking_failures": 0,
        "deterministic_pass_rate": 1.0,
        "gate_failures": [],
        "status": "PASS",
    }
    assert report["phase_gate"] == {
        "p0_2": "PASS",
        "blocking": False,
        "human_annotation_required": False,
        "immersive_gate_changed": False,
    }
    assert report["model_judgment"]["used"] is False
    assert "HUMAN_VALIDATED" not in json.dumps(report)


def test_seeded_holdout_is_reproducible_but_not_a_fixed_single_list():
    first = autonomous.build_report(MANIFEST)
    second = autonomous.build_report(MANIFEST)

    assert first["evaluation_id"] == second["evaluation_id"]
    assert first["holdout"]["generator_version"] == (
        "filon-adversarial-holdout/v1"
    )
    assert len(first["holdout"]["seeds"]) == 3
    seeded_ids = [
        check["case_id"]
        for check in first["checks"]
        if check["case_id"].startswith("seed-")
    ]
    assert any("same-exact-identity" in case_id for case_id in seeded_ids)
    assert any("different-storage-no-merge" in case_id for case_id in seeded_ids)
    assert any("invalid-attachment-quarantine" in case_id for case_id in seeded_ids)


def test_cross_source_agreement_and_conflict_remain_distinct():
    agreement = autonomous.cross_source_consistency(
        [
            {"source_ref": "a", "price": "99,00", "currency": "EUR", "stock": "yes"},
            {"source_ref": "b", "price": "99.00", "currency": "eur", "stock": "in stock"},
        ]
    )
    conflict = autonomous.cross_source_consistency(
        [
            {"source_ref": "a", "price": "99", "currency": "EUR", "stock": "yes"},
            {"source_ref": "b", "price": "120", "currency": "GBP", "stock": "no"},
        ]
    )

    assert agreement == {
        "SOURCE_COUNT": 2,
        "SOURCE_AGREEMENT": True,
        "SOURCE_CONFLICT": False,
        "quality_status": "CROSS_SOURCE_VERIFIED",
        "signal": "SOURCE_AGREEMENT",
    }
    assert conflict["SOURCE_CONFLICT"] is True
    assert conflict["quality_status"] == "UNRESOLVED"


def test_duplicate_cross_source_identity_is_rejected():
    with pytest.raises(autonomous.AutonomousQualityError, match="unique sources"):
        autonomous.cross_source_consistency(
            [
                {"source_ref": "same", "price": "1", "currency": "EUR", "stock": "yes"},
                {"source_ref": "same", "price": "1", "currency": "EUR", "stock": "yes"},
            ]
        )


def test_missing_limitation_fails_closed(tmp_path: Path):
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest.pop("limitation")
    invalid = tmp_path / "manifest.json"
    invalid.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(
        autonomous.AutonomousQualityError,
        match="human-ground-truth limitation",
    ):
        autonomous.build_report(invalid)


def test_engine_regression_becomes_a_blocking_failure(monkeypatch):
    monkeypatch.setattr(autonomous, "normalize_ean", lambda _value: None)

    report = autonomous.build_report(MANIFEST)

    assert report["summary"]["status"] == "FAIL"
    assert report["summary"]["blocking_failures"] > 0
    assert report["summary"]["deterministic_pass_rate"] < 1.0
    assert report["phase_gate"]["blocking"] is True


def test_cli_writes_an_auditable_report(tmp_path: Path, capsys):
    output = tmp_path / "report.json"

    assert autonomous.main(
        ["--manifest", str(MANIFEST), "--output", str(output), "--strict"]
    ) == 0
    report = json.loads(output.read_text(encoding="utf-8"))
    receipt = json.loads(capsys.readouterr().out)

    assert receipt["evaluation_id"] == report["evaluation_id"]
    assert receipt["summary"]["status"] == "PASS"
