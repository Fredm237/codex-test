"""Curation humaine traçable des inventaires publics du Quality Lab.

Le moteur ne remplit aucun jugement. Le workflow lie un curateur, un inventaire
immuable et chaque décision avant de produire des cas candidats encore sans
gold. Les annotations indépendantes restent la responsabilité de
``annotation_workflow``.
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

from .annotation_workflow import prepare_pack
from .candidate_inventory import (
    MAX_INVENTORY_BYTES,
    MAX_RECEIPT_BYTES,
    publish_immutable,
    verify_catalog_inventory,
)
from .integrity import (
    FINGERPRINT_PATTERN,
    LANGUAGES,
    SCENARIO_TYPES,
    VERTICALS,
    canonical_json,
    require_identifier,
    sha256_value,
    strict_load_jsonl,
    strict_loads,
)


CURATION_VERSION = "quality-candidate-curation/v1"
CURATION_PACK_RECEIPT_VERSION = "quality-candidate-curation-pack-receipt/v1"
CURATION_RECEIPT_VERSION = "quality-candidate-curation-receipt/v1"
CATALOG_DATASETS = ("taxonomy", "variant_resolution")
_TASK_DOMAIN = "filon.quality.candidate-curation.task.v1"
_PACK_DOMAIN = "filon.quality.candidate-curation.pack.v1"
_COMPLETED_PACK_DOMAIN = "filon.quality.candidate-curation.completed-pack.v1"
_CASE_DOMAIN = "filon.quality.candidate-curation.case.v1"
_OUTPUT_DOMAIN = "filon.quality.candidate-curation.output.v1"

_DECISION_KEYS = {
    "include",
    "language",
    "scenario_type",
    "vertical",
    "datasets",
}
_TASK_KEYS = {
    "curation_version",
    "inventory_fingerprint",
    "candidate_ref",
    "record_fingerprint",
    "sampling_vertical",
    "observation",
    "curator_id",
    "allowed_datasets",
    "decision",
    "task_fingerprint",
    "pack_fingerprint",
}


def _clone(value: Any) -> Any:
    return strict_loads(canonical_json(value), source="<curation-value>")


def _task_core(
    record: Mapping[str, Any],
    *,
    inventory_fingerprint: str,
    curator_id: str,
) -> dict[str, Any]:
    curator = require_identifier(curator_id, "curator_id")
    return {
        "curation_version": CURATION_VERSION,
        "inventory_fingerprint": inventory_fingerprint,
        "candidate_ref": record["candidate_ref"],
        "record_fingerprint": record["record_fingerprint"],
        "sampling_vertical": record["sampling_vertical"],
        "observation": _clone(record["observation"]),
        "curator_id": curator,
        "allowed_datasets": list(CATALOG_DATASETS),
    }


def prepare_curation_pack(
    records: Iterable[Mapping[str, Any]],
    receipt: Mapping[str, Any],
    *,
    curator_id: str,
) -> list[dict[str, Any]]:
    """Prépare un roster complet lié à l'inventaire brut vérifié."""

    materialized = list(records)
    verify_catalog_inventory(materialized, receipt)
    inventory_fingerprint = receipt["inventory_fingerprint"]
    tasks: list[dict[str, Any]] = []
    for record in materialized:
        core = _task_core(
            record,
            inventory_fingerprint=inventory_fingerprint,
            curator_id=curator_id,
        )
        task = {
            **core,
            "decision": {
                "include": None,
                "language": None,
                "scenario_type": None,
                "vertical": None,
                "datasets": [],
            },
            "task_fingerprint": sha256_value(_TASK_DOMAIN, core),
        }
        tasks.append(task)
    if not tasks:
        raise ValueError("un pack de curation ne peut pas être vide")
    pack_fingerprint = sha256_value(
        _PACK_DOMAIN,
        {
            "curation_version": CURATION_VERSION,
            "inventory_fingerprint": inventory_fingerprint,
            "curator_id": require_identifier(curator_id, "curator_id"),
            "task_fingerprints": [task["task_fingerprint"] for task in tasks],
        },
    )
    for task in tasks:
        task["pack_fingerprint"] = pack_fingerprint
    return tasks


def _decision_errors(decision: Any) -> list[str]:
    if not isinstance(decision, Mapping) or set(decision) != _DECISION_KEYS:
        return ["decision incompatible"]
    include = decision.get("include")
    datasets = decision.get("datasets")
    if include is False:
        if decision != {
            "include": False,
            "language": None,
            "scenario_type": None,
            "vertical": None,
            "datasets": [],
        }:
            return ["une exclusion ne peut porter ni strate ni dataset"]
        return []
    if include is not True:
        return ["include doit être explicitement true ou false"]
    errors: list[str] = []
    if decision.get("language") not in LANGUAGES:
        errors.append("language invalide")
    if decision.get("scenario_type") not in SCENARIO_TYPES:
        errors.append("scenario_type invalide")
    if decision.get("vertical") not in VERTICALS:
        errors.append("vertical invalide")
    if (
        not isinstance(datasets, list)
        or not datasets
        or datasets != sorted(set(datasets))
        or any(dataset not in CATALOG_DATASETS for dataset in datasets)
    ):
        errors.append("datasets doivent être un sous-ensemble canonique non vide")
    return errors


def _completed_pack(
    records: list[Mapping[str, Any]],
    receipt: Mapping[str, Any],
    tasks: Iterable[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], str, str]:
    materialized = list(tasks)
    if len(materialized) != len(records):
        raise ValueError("le pack doit couvrir exactement tout l'inventaire")
    by_ref = {record["candidate_ref"]: record for record in records}
    if len(by_ref) != len(records):
        raise ValueError("candidate_ref dupliqué dans l'inventaire")
    seen_refs: set[str] = set()
    pack_ids: set[str] = set()
    curator_ids: set[str] = set()
    verified: list[dict[str, Any]] = []
    errors: list[str] = []

    for index, task in enumerate(materialized, 1):
        prefix = f"record {index}"
        if not isinstance(task, Mapping) or set(task) != _TASK_KEYS:
            errors.append(f"{prefix}: structure de tâche incompatible")
            continue
        ref = task.get("candidate_ref")
        if not isinstance(ref, str) or ref not in by_ref:
            errors.append(f"{prefix}: candidate_ref inconnu")
            continue
        if ref in seen_refs:
            errors.append(f"{prefix}: candidate_ref dupliqué")
            continue
        seen_refs.add(ref)
        source = by_ref[ref]
        try:
            curator = require_identifier(task.get("curator_id"), "curator_id")
        except ValueError as exc:
            errors.append(f"{prefix}: {exc}")
            continue
        curator_ids.add(curator)
        if task.get("pack_fingerprint") is not None:
            pack_ids.add(str(task.get("pack_fingerprint")))
        expected_core = _task_core(
            source,
            inventory_fingerprint=receipt["inventory_fingerprint"],
            curator_id=curator,
        )
        actual_core = {key: task.get(key) for key in expected_core}
        if canonical_json(actual_core) != canonical_json(expected_core):
            errors.append(f"{prefix}: contenu source ou affectation altéré")
        expected_task = sha256_value(_TASK_DOMAIN, expected_core)
        if task.get("task_fingerprint") != expected_task:
            errors.append(f"{prefix}: task_fingerprint invalide")
        decision_errors = _decision_errors(task.get("decision"))
        errors.extend(f"{prefix}: {error}" for error in decision_errors)
        verified.append(_clone(task))

    if seen_refs != set(by_ref):
        errors.append("le pack ne couvre pas exactement les candidate_ref")
    if len(curator_ids) != 1:
        errors.append("exactement un curator_id est requis")
    if len(pack_ids) != 1:
        errors.append("exactement un pack_fingerprint est requis")
    if errors:
        raise ValueError("; ".join(sorted(set(errors))))

    curator = next(iter(curator_ids))
    expected_pack = sha256_value(
        _PACK_DOMAIN,
        {
            "curation_version": CURATION_VERSION,
            "inventory_fingerprint": receipt["inventory_fingerprint"],
            "curator_id": curator,
            "task_fingerprints": [
                sha256_value(
                    _TASK_DOMAIN,
                    _task_core(
                        record,
                        inventory_fingerprint=receipt["inventory_fingerprint"],
                        curator_id=curator,
                    ),
                )
                for record in records
            ],
        },
    )
    if next(iter(pack_ids)) != expected_pack:
        raise ValueError("pack_fingerprint invalide")
    verified.sort(key=lambda task: task["candidate_ref"])
    completed = sha256_value(
        _COMPLETED_PACK_DOMAIN,
        {
            "pack_fingerprint": expected_pack,
            "decisions": [
                {
                    "candidate_ref": task["candidate_ref"],
                    "decision": task["decision"],
                }
                for task in verified
            ],
        },
    )
    return verified, curator, completed


def finalize_curation(
    records: Iterable[Mapping[str, Any]],
    receipt: Mapping[str, Any],
    tasks: Iterable[Mapping[str, Any]],
    *,
    dataset: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Produit des cas sans gold pour un dataset catalog compatible."""

    if dataset not in CATALOG_DATASETS:
        raise ValueError("dataset non pris en charge par l'inventaire catalogue")
    inventory = list(records)
    verify_catalog_inventory(inventory, receipt)
    completed_tasks, curator_id, completed_pack = _completed_pack(
        inventory,
        receipt,
        tasks,
    )
    cases: list[dict[str, Any]] = []
    for task in completed_tasks:
        decision = task["decision"]
        if decision["include"] is not True or dataset not in decision["datasets"]:
            continue
        case_fingerprint = sha256_value(
            _CASE_DOMAIN,
            {
                "dataset": dataset,
                "inventory_fingerprint": receipt["inventory_fingerprint"],
                "record_fingerprint": task["record_fingerprint"],
                "completed_curation_fingerprint": completed_pack,
            },
        )
        cases.append(
            {
                "case_id": f"catalog-curated:{case_fingerprint[7:]}",
                "group_id": task["candidate_ref"],
                "strata": {
                    "scenario_type": decision["scenario_type"],
                    "language": decision["language"],
                    "vertical": decision["vertical"],
                },
                "observation": _clone(task["observation"]),
            }
        )
    if not cases:
        raise ValueError(f"aucun cas inclus pour {dataset}")
    cases.sort(key=lambda case: case["case_id"])
    # La même validation que le prochain maillon garantit que la sortie est
    # réellement annotable, sans fabriquer de label.
    prepare_pack(dataset, cases, annotator_id="curation-contract-check")
    strata_counts = {
        key: dict(sorted(Counter(case["strata"][key] for case in cases).items()))
        for key in ("scenario_type", "language", "vertical")
    }
    output_fingerprint = sha256_value(
        _OUTPUT_DOMAIN,
        {
            "dataset": dataset,
            "completed_curation_fingerprint": completed_pack,
            "cases": cases,
        },
    )
    curation_receipt = {
        "receipt_version": CURATION_RECEIPT_VERSION,
        "curation_version": CURATION_VERSION,
        "dataset": dataset,
        "inventory_fingerprint": receipt["inventory_fingerprint"],
        "curator_id": curator_id,
        "completed_curation_fingerprint": completed_pack,
        "rows": len(cases),
        "strata_counts": strata_counts,
        "labels_present": False,
        "ready_for_annotation": True,
        "blocked_on": ["independent_human_annotation"],
        "output_fingerprint": output_fingerprint,
    }
    return cases, curation_receipt


def verify_curated_cases(
    cases: Iterable[Mapping[str, Any]],
    receipt: Mapping[str, Any],
) -> None:
    materialized = list(cases)
    expected_keys = {
        "receipt_version",
        "curation_version",
        "dataset",
        "inventory_fingerprint",
        "curator_id",
        "completed_curation_fingerprint",
        "rows",
        "strata_counts",
        "labels_present",
        "ready_for_annotation",
        "blocked_on",
        "output_fingerprint",
    }
    if not isinstance(receipt, Mapping) or set(receipt) != expected_keys:
        raise ValueError("structure du reçu de curation incompatible")
    if receipt.get("receipt_version") != CURATION_RECEIPT_VERSION:
        raise ValueError("receipt_version de curation incompatible")
    if receipt.get("curation_version") != CURATION_VERSION:
        raise ValueError("curation_version incompatible")
    dataset = receipt.get("dataset")
    if dataset not in CATALOG_DATASETS:
        raise ValueError("dataset de curation incompatible")
    for field in (
        "inventory_fingerprint",
        "completed_curation_fingerprint",
        "output_fingerprint",
    ):
        value = receipt.get(field)
        if not isinstance(value, str) or FINGERPRINT_PATTERN.fullmatch(value) is None:
            raise ValueError(f"{field} invalide")
    require_identifier(receipt.get("curator_id"), "curator_id")
    rows = receipt.get("rows")
    if isinstance(rows, bool) or not isinstance(rows, int) or rows < 1:
        raise ValueError("rows invalide")
    if rows != len(materialized):
        raise ValueError("compte de cas incompatible")
    if receipt.get("labels_present") is not False:
        raise ValueError("les cas curés ne doivent contenir aucun label")
    if receipt.get("ready_for_annotation") is not True:
        raise ValueError("les cas curés doivent être prêts pour annotation")
    if receipt.get("blocked_on") != ["independent_human_annotation"]:
        raise ValueError("blocage de curation incompatible")
    if materialized != sorted(materialized, key=lambda case: case.get("case_id", "")):
        raise ValueError("ordre des cas non canonique")
    for index, case in enumerate(materialized, 1):
        if not isinstance(case, Mapping) or set(case) != {
            "case_id",
            "group_id",
            "strata",
            "observation",
        }:
            raise ValueError(f"record {index}: structure de cas incompatible")
    case_ids = [case.get("case_id") for case in materialized]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("case_id dupliqué")
    prepare_pack(dataset, materialized, annotator_id="curation-contract-check")
    expected_counts = {
        key: dict(
            sorted(Counter(case["strata"][key] for case in materialized).items())
        )
        for key in ("scenario_type", "language", "vertical")
    }
    if receipt.get("strata_counts") != expected_counts:
        raise ValueError("comptes de strates incompatibles")
    expected_output = sha256_value(
        _OUTPUT_DOMAIN,
        {
            "dataset": dataset,
            "completed_curation_fingerprint": receipt[
                "completed_curation_fingerprint"
            ],
            "cases": materialized,
        },
    )
    if receipt.get("output_fingerprint") != expected_output:
        raise ValueError("output_fingerprint invalide")


def _bounded_jsonl(path: Path) -> list[dict[str, Any]]:
    if path.stat().st_size > MAX_INVENTORY_BYTES:
        raise ValueError("JSONL de curation hors borne de taille")
    payload = path.read_bytes()
    if len(payload) > MAX_INVENTORY_BYTES:
        raise ValueError("JSONL de curation hors borne de taille")
    return strict_load_jsonl(payload, source=str(path))


def _bounded_json(path: Path) -> dict[str, Any]:
    if path.stat().st_size > MAX_RECEIPT_BYTES:
        raise ValueError("reçu hors borne de taille")
    payload = path.read_bytes()
    if len(payload) > MAX_RECEIPT_BYTES:
        raise ValueError("reçu hors borne de taille")
    value = strict_loads(payload, source=str(path))
    if not isinstance(value, dict):
        raise ValueError("le reçu doit être un objet")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Curation humaine traçable des candidats Quality Lab"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser("prepare")
    prepare.add_argument("--inventory", type=Path, required=True)
    prepare.add_argument("--inventory-receipt", type=Path, required=True)
    prepare.add_argument("--output", type=Path, required=True)
    prepare.add_argument("--receipt", type=Path, required=True)
    prepare.add_argument("--curator-id", required=True)

    finalize = subparsers.add_parser("finalize")
    finalize.add_argument("--inventory", type=Path, required=True)
    finalize.add_argument("--inventory-receipt", type=Path, required=True)
    finalize.add_argument("--input", type=Path, required=True)
    finalize.add_argument("--dataset", choices=CATALOG_DATASETS, required=True)
    finalize.add_argument("--output", type=Path, required=True)
    finalize.add_argument("--receipt", type=Path, required=True)

    verify = subparsers.add_parser("verify")
    verify.add_argument("--input", type=Path, required=True)
    verify.add_argument("--receipt", type=Path, required=True)

    args = parser.parse_args()
    try:
        if args.command == "prepare":
            inventory = _bounded_jsonl(args.inventory)
            inventory_receipt = _bounded_json(args.inventory_receipt)
            tasks = prepare_curation_pack(
                inventory,
                inventory_receipt,
                curator_id=args.curator_id,
            )
            pack_receipt = {
                "receipt_version": CURATION_PACK_RECEIPT_VERSION,
                "curation_version": CURATION_VERSION,
                "inventory_fingerprint": inventory_receipt["inventory_fingerprint"],
                "curator_id": require_identifier(args.curator_id, "curator_id"),
                "rows": len(tasks),
                "labels_present": False,
                "ready_for_annotation": False,
                "blocked_on": ["human_curation", "independent_human_annotation"],
                "pack_fingerprint": tasks[0]["pack_fingerprint"],
            }
            publish_immutable(args.output, args.receipt, tasks, pack_receipt)
        elif args.command == "finalize":
            cases, curation_receipt = finalize_curation(
                _bounded_jsonl(args.inventory),
                _bounded_json(args.inventory_receipt),
                _bounded_jsonl(args.input),
                dataset=args.dataset,
            )
            verify_curated_cases(cases, curation_receipt)
            publish_immutable(args.output, args.receipt, cases, curation_receipt)
        else:
            verify_curated_cases(
                _bounded_jsonl(args.input),
                _bounded_json(args.receipt),
            )
        return 0
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"erreur curation: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
