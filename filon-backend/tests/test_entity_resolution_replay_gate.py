"""Gate P2G fail-closed des reçus de replay Entity Resolution."""

from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest

from app.product_graph.entity_replay import REPLAY_REPORT_SCHEMA_VERSION
from app.product_graph.entity_resolution import POLICY_VERSION, RESOLVER_VERSION
from app.product_graph.entity_signals import EXTRACTOR_VERSION
from quality_lab.entity_resolution_replay import (
    LIMITATION,
    EntityResolutionReplayGateError,
    main,
    verify_receipts,
)


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "quality" / "entity-resolution-production-gate.json"


def _report(*, replay: bool = False) -> dict:
    return {
        "schema_version": REPLAY_REPORT_SCHEMA_VERSION,
        "extractor_version": EXTRACTOR_VERSION,
        "resolver_version": RESOLVER_VERSION,
        "policy_version": POLICY_VERSION,
        "mode": "apply",
        "after_raw_id": 0,
        "limit": 1000,
        "scanned": 1000,
        "projected": 1000,
        "missing_offer_links": 0,
        "candidate_profiles": 321,
        "exact_verified": 330,
        "high_confidence": 0,
        "probable": 0,
        "ambiguous": 0,
        "unresolved": 670,
        "signal_projections_created": 0 if replay else 1000,
        "signal_projections_existing": 1000 if replay else 0,
        "decisions_created": 0 if replay else 1000,
        "decisions_existing": 1000 if replay else 0,
        "last_raw_source_id": 1000,
        "evaluation_id": "sha256:" + "a" * 64,
    }


def _write_pair(tmp_path: Path, first: dict, replay: dict) -> tuple[Path, Path]:
    first_path = tmp_path / "first.json"
    replay_path = tmp_path / "replay.json"
    first_path.write_text(json.dumps(first), encoding="utf-8")
    replay_path.write_text(json.dumps(replay), encoding="utf-8")
    return first_path, replay_path


def test_two_production_receipts_pass_every_gate_and_are_reproducible(tmp_path):
    first_path, replay_path = _write_pair(tmp_path, _report(), _report(replay=True))
    first_receipt = verify_receipts(MANIFEST, first_path, replay_path)
    second_receipt = verify_receipts(MANIFEST, first_path, replay_path)

    assert first_receipt["status"] == "PASS"
    assert all(first_receipt["gate_results"].values())
    assert first_receipt["limitation"] == LIMITATION
    assert first_receipt["evaluation_id"] == second_receipt["evaluation_id"]
    assert first_receipt["generated_at"] != ""


@pytest.mark.parametrize(
    "mutation, failed_gate",
    [
        (
            lambda first, replay: first.update(missing_offer_links=1),
            "offer_provenance_complete",
        ),
        (
            lambda first, replay: (
                first.update(exact_verified=329, unresolved=671)
            ),
            "exact_gtin_preserved",
        ),
        (
            lambda first, replay: (
                first.update(high_confidence=1, unresolved=669)
            ),
            "no_unproved_canonical_promotion",
        ),
        (
            lambda first, replay: replay.update(
                evaluation_id="sha256:" + "b" * 64
            ),
            "same_replay_truth",
        ),
        (
            lambda first, replay: replay.update(
                signal_projections_created=1,
                signal_projections_existing=999,
            ),
            "idempotent_replay",
        ),
    ],
)
def test_gate_rejects_silent_loss_promotion_or_replay_drift(
    tmp_path,
    mutation,
    failed_gate,
):
    first = _report()
    replay = _report(replay=True)
    mutation(first, replay)
    first_path, replay_path = _write_pair(tmp_path, first, replay)
    receipt = verify_receipts(MANIFEST, first_path, replay_path)
    assert receipt["status"] == "FAIL"
    assert receipt["gate_results"][failed_gate] is False


def test_report_shape_and_state_totals_fail_closed(tmp_path):
    first = _report()
    first["unexpected"] = "not allowed"
    first_path, replay_path = _write_pair(tmp_path, first, _report(replay=True))
    with pytest.raises(EntityResolutionReplayGateError, match="keys"):
        verify_receipts(MANIFEST, first_path, replay_path)

    first = _report()
    first["unresolved"] = 669
    first_path, replay_path = _write_pair(tmp_path, first, _report(replay=True))
    with pytest.raises(EntityResolutionReplayGateError, match="state totals"):
        verify_receipts(MANIFEST, first_path, replay_path)


def test_manifest_cannot_relax_the_ratified_production_baseline(tmp_path):
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    changed = deepcopy(manifest)
    changed["corpus"]["expected_exact_verified"] = 0
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(changed), encoding="utf-8")
    first_path, replay_path = _write_pair(tmp_path, _report(), _report(replay=True))
    with pytest.raises(EntityResolutionReplayGateError, match="baseline"):
        verify_receipts(manifest_path, first_path, replay_path)


def test_strict_cli_writes_only_a_derived_receipt(tmp_path, monkeypatch):
    first_path, replay_path = _write_pair(tmp_path, _report(), _report(replay=True))
    output = tmp_path / "receipt.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "entity-resolution-replay-gate",
            "--manifest",
            str(MANIFEST),
            "--first",
            str(first_path),
            "--replay",
            str(replay_path),
            "--strict",
            "--output",
            str(output),
        ],
    )
    assert main() == 0
    receipt = json.loads(output.read_text(encoding="utf-8"))
    assert receipt["status"] == "PASS"
    assert set(receipt) == {
        "schema_version",
        "generated_at",
        "limitation",
        "source_baseline",
        "evaluation_id",
        "status",
        "gate_results",
        "first_report_evaluation_id",
        "replay_report_evaluation_id",
    }
