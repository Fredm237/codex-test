"""Gate P2G des deux reçus de replay Entity Resolution en production.

Le vérificateur ne lance aucun replay et ne contacte aucune base. Il compare
deux reçus expurgés produits par le même lot : premier apply puis replay
idempotent. Toute clé absente, valeur inattendue ou divergence échoue fermée.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

from app.product_graph.entity_replay import REPLAY_REPORT_SCHEMA_VERSION
from app.product_graph.entity_resolution import POLICY_VERSION, RESOLVER_VERSION
from app.product_graph.entity_signals import EXTRACTOR_VERSION

from .integrity import atomic_write_text, canonical_json


MANIFEST_VERSION = "entity-resolution-production-gate-manifest/v1"
RECEIPT_VERSION = "entity-resolution-production-gate-receipt/v1"
LIMITATION = "NO_EXTERNAL_HUMAN_GROUND_TRUTH"
STATES = (
    "exact_verified",
    "high_confidence",
    "probable",
    "ambiguous",
    "unresolved",
)
REQUIRED_REPORT_KEYS = {
    "schema_version",
    "extractor_version",
    "resolver_version",
    "policy_version",
    "mode",
    "after_raw_id",
    "limit",
    "scanned",
    "projected",
    "missing_offer_links",
    "candidate_profiles",
    *STATES,
    "signal_projections_created",
    "signal_projections_existing",
    "decisions_created",
    "decisions_existing",
    "last_raw_source_id",
    "evaluation_id",
}


class EntityResolutionReplayGateError(ValueError):
    """Manifest ou reçu de production hors contrat."""


def _load(path: Path, message: str) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EntityResolutionReplayGateError(message) from exc
    if not isinstance(value, Mapping):
        raise EntityResolutionReplayGateError(message)
    return value


def _integer(value: Any, *, minimum: int = 0) -> bool:
    return not isinstance(value, bool) and isinstance(value, int) and value >= minimum


def _manifest(path: Path) -> Mapping[str, Any]:
    manifest = _load(path, "production gate manifest is unreadable")
    if (
        set(manifest)
        != {
            "schema_version",
            "gate_version",
            "status",
            "source_baseline",
            "limitation",
            "corpus",
            "gates",
        }
        or manifest.get("schema_version") != MANIFEST_VERSION
        or manifest.get("gate_version") != "1.0.0"
        or manifest.get("status") != "active"
        or manifest.get("source_baseline") != "phase1-awin-shadow-2026-08-31"
        or manifest.get("limitation") != LIMITATION
    ):
        raise EntityResolutionReplayGateError("production gate manifest is invalid")
    corpus = manifest.get("corpus")
    expected_corpus = {
        "after_raw_id": 0,
        "limit": 1000,
        "expected_scanned": 1000,
        "expected_projected": 1000,
        "expected_last_raw_source_id": 1000,
        "expected_candidate_profiles": 321,
        "expected_exact_verified": 330,
    }
    if corpus != expected_corpus:
        raise EntityResolutionReplayGateError("production corpus baseline is invalid")
    gates = manifest.get("gates")
    if gates != {
        "missing_offer_links_max": 0,
        "high_confidence_max": 0,
        "canonical_non_gtin_max": 0,
        "first_apply_existing_max": 0,
        "replay_created_max": 0,
    }:
        raise EntityResolutionReplayGateError("production gates are invalid")
    return manifest


def _report(path: Path, *, label: str) -> Mapping[str, Any]:
    report = _load(path, f"{label} replay report is unreadable")
    if set(report) != REQUIRED_REPORT_KEYS:
        raise EntityResolutionReplayGateError(f"{label} replay report keys are invalid")
    if (
        report.get("schema_version") != REPLAY_REPORT_SCHEMA_VERSION
        or report.get("extractor_version") != EXTRACTOR_VERSION
        or report.get("resolver_version") != RESOLVER_VERSION
        or report.get("policy_version") != POLICY_VERSION
        or report.get("mode") != "apply"
        or any(not _integer(report.get(key)) for key in REQUIRED_REPORT_KEYS - {
            "schema_version",
            "extractor_version",
            "resolver_version",
            "policy_version",
            "mode",
            "evaluation_id",
            "last_raw_source_id",
        })
        or not _integer(report.get("last_raw_source_id"), minimum=1)
        or not isinstance(report.get("evaluation_id"), str)
        or len(str(report["evaluation_id"])) != 71
        or not str(report["evaluation_id"]).startswith("sha256:")
    ):
        raise EntityResolutionReplayGateError(f"{label} replay report is invalid")
    try:
        int(str(report["evaluation_id"])[7:], 16)
    except ValueError as exc:
        raise EntityResolutionReplayGateError(
            f"{label} evaluation id is invalid"
        ) from exc
    if sum(int(report[state]) for state in STATES) != report["projected"]:
        raise EntityResolutionReplayGateError(f"{label} state totals are invalid")
    return report


def verify_receipts(
    manifest_path: Path,
    first_path: Path,
    replay_path: Path,
) -> dict[str, Any]:
    manifest = _manifest(manifest_path)
    first = _report(first_path, label="first")
    replay = _report(replay_path, label="idempotent")
    corpus = manifest["corpus"]
    gates = manifest["gates"]

    stable_fields = {
        "schema_version",
        "extractor_version",
        "resolver_version",
        "policy_version",
        "after_raw_id",
        "limit",
        "scanned",
        "projected",
        "missing_offer_links",
        "candidate_profiles",
        *STATES,
        "last_raw_source_id",
        "evaluation_id",
    }
    gate_results = {
        "bounded_window": (
            first["after_raw_id"] == corpus["after_raw_id"]
            and first["limit"] == corpus["limit"]
        ),
        "corpus_preserved": (
            first["scanned"] == corpus["expected_scanned"]
            and first["projected"] == corpus["expected_projected"]
            and first["last_raw_source_id"]
            == corpus["expected_last_raw_source_id"]
        ),
        "offer_provenance_complete": (
            first["missing_offer_links"] <= gates["missing_offer_links_max"]
        ),
        "candidate_baseline_preserved": (
            first["candidate_profiles"]
            == corpus["expected_candidate_profiles"]
        ),
        "exact_gtin_preserved": (
            first["exact_verified"] == corpus["expected_exact_verified"]
        ),
        "no_unproved_canonical_promotion": (
            first["high_confidence"] <= gates["high_confidence_max"]
            and first["high_confidence"]
            <= gates["canonical_non_gtin_max"]
        ),
        "first_apply_complete": (
            first["signal_projections_created"] == first["projected"]
            and first["decisions_created"] == first["projected"]
            and first["signal_projections_existing"]
            <= gates["first_apply_existing_max"]
            and first["decisions_existing"]
            <= gates["first_apply_existing_max"]
        ),
        "same_replay_truth": all(first[field] == replay[field] for field in stable_fields),
        "idempotent_replay": (
            replay["signal_projections_created"] <= gates["replay_created_max"]
            and replay["decisions_created"] <= gates["replay_created_max"]
            and replay["signal_projections_existing"] == replay["projected"]
            and replay["decisions_existing"] == replay["projected"]
        ),
    }
    status = "PASS" if all(gate_results.values()) else "FAIL"
    receipt_input = {
        "manifest": manifest,
        "first": first,
        "replay": replay,
        "gate_results": gate_results,
    }
    return {
        "schema_version": RECEIPT_VERSION,
        "generated_at": datetime.now(UTC).isoformat(),
        "limitation": LIMITATION,
        "source_baseline": manifest["source_baseline"],
        "evaluation_id": "sha256:"
        + hashlib.sha256(canonical_json(receipt_input).encode("utf-8")).hexdigest(),
        "status": status,
        "gate_results": gate_results,
        "first_report_evaluation_id": first["evaluation_id"],
        "replay_report_evaluation_id": replay["evaluation_id"],
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Vérifie deux reçus de replay Entity Resolution production",
    )
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--first", type=Path, required=True)
    parser.add_argument("--replay", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--strict", action="store_true")
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        receipt = verify_receipts(args.manifest, args.first, args.replay)
    except EntityResolutionReplayGateError as exc:
        print(json.dumps({"status": "INVALID", "error": str(exc)}, sort_keys=True))
        return 2
    payload = json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        atomic_write_text(args.output, payload)
    else:
        print(payload, end="")
    return 1 if args.strict and receipt["status"] != "PASS" else 0


if __name__ == "__main__":
    raise SystemExit(main())
