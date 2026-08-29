"""Workflow humain aveugle, versionné et fail-closed du FILON Quality Lab."""

from __future__ import annotations

import argparse
import os
import tempfile
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, Mapping

from jsonschema import Draft202012Validator

from .integrity import (
    DATASETS,
    FINGERPRINT_PATTERN,
    INPUT_FIELDS,
    PACK_VERSION,
    RECORD_VERSION,
    SPLIT_POLICY_VERSION,
    canonical_json,
    case_fingerprint,
    completed_pack_fingerprint,
    disagreement_fingerprint,
    ensure_no_reserved_fields,
    input_fingerprint,
    label_invariant_errors,
    normalize_label,
    pack_fingerprint,
    project_blind_input,
    read_json,
    read_jsonl,
    require_identifier,
    schema_fingerprint,
    sha256_value,
    split_for_group,
    strict_loads,
)


LABEL_FIELDS: dict[str, tuple[str, ...]] = {
    "taxonomy": ("category", "subcategory", "product_role"),
    "entity_resolution": ("product_relation", "variant_relation"),
    "variant_resolution": ("expected_variant",),
    "offer_attachment": ("expected_variant_id", "eligibility"),
    "offer_truth": ("price", "stock", "shipping", "affiliate_link"),
    "retrieval": ("relevant_product_ids", "constraint_violating_product_ids"),
    "decision": ("acceptable_outcomes", "forbidden_claims", "claim_evidence"),
}

_SCHEMA_FILES = {
    "taxonomy": "taxonomy.schema.json",
    "entity_resolution": "entity-resolution.schema.json",
    "variant_resolution": "variant-resolution.schema.json",
    "offer_attachment": "offer-attachment.schema.json",
    "offer_truth": "offer-truth.schema.json",
    "retrieval": "retrieval.schema.json",
    "decision": "decision.schema.json",
}
_PACK_KEYS = {
    "pack_version",
    "dataset",
    "schema_fingerprint",
    "split_policy_version",
    "case_id",
    "group_id",
    "split",
    "input",
    "input_fingerprint",
    "pack_fingerprint",
    "annotation",
}
_ANNOTATION_KEYS = {"annotator_id", "label", "confidence"}
_ADJUDICATION_KEYS = {"adjudicator_id", "label", "confidence", "rationale"}
_ADJUDICATION_TASK_KEYS = {
    "record_version",
    "dataset",
    "schema_fingerprint",
    "split_policy_version",
    "case_id",
    "group_id",
    "split",
    "input",
    "input_fingerprint",
    "disagreement_fingerprint",
    "adjudicator_id",
    "adjudication",
    "adjudication_task_fingerprint",
}
_DISAGREEMENT_KEYS = {
    "record_version",
    "dataset",
    "schema_fingerprint",
    "split_policy_version",
    "case_id",
    "group_id",
    "split",
    "input",
    "input_fingerprint",
    "annotations",
    "source_pack_fingerprints",
    "status",
    "disagreement_fingerprint",
}


@dataclass(frozen=True)
class MergeResult:
    accepted: tuple[dict[str, Any], ...]
    disagreements: tuple[dict[str, Any], ...]
    errors: tuple[str, ...]


@dataclass(frozen=True)
class AdjudicationResult:
    accepted: tuple[dict[str, Any], ...]
    errors: tuple[str, ...]


def _clone(value: Any) -> Any:
    return strict_loads(canonical_json(value), source="in-memory value")


def _quality_root() -> Path:
    return Path(__file__).resolve().parents[2] / "quality"


@lru_cache(maxsize=None)
def _label_validator(dataset: str) -> Draft202012Validator:
    if dataset not in DATASETS:
        raise ValueError(f"dataset inconnu : {dataset}")
    schema = read_json(_quality_root() / "schemas" / _SCHEMA_FILES[dataset])
    # Conserver la racine des ``$defs`` : certains labels réutilisent des
    # références internes (nonblank_id, expected_variant).
    label_schema = {
        "$schema": schema.get(
            "$schema", "https://json-schema.org/draft/2020-12/schema"
        ),
        "$defs": schema["$defs"],
        "$ref": "#/$defs/label",
    }
    Draft202012Validator.check_schema(label_schema)
    return Draft202012Validator(label_schema)


@lru_cache(maxsize=None)
def _record_validator(dataset: str) -> Draft202012Validator:
    schema = read_json(_quality_root() / "schemas" / _SCHEMA_FILES[dataset])
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


@lru_cache(maxsize=None)
def _input_validator(dataset: str) -> Draft202012Validator:
    schema = read_json(_quality_root() / "schemas" / _SCHEMA_FILES[dataset])
    input_schema = {
        "$schema": schema.get(
            "$schema", "https://json-schema.org/draft/2020-12/schema"
        ),
        "$defs": schema["$defs"],
        "$ref": "#/$defs/input",
    }
    Draft202012Validator.check_schema(input_schema)
    return Draft202012Validator(input_schema)


def _schema_errors(validator: Draft202012Validator, value: Any) -> list[str]:
    messages: list[str] = []
    for violation in sorted(
        validator.iter_errors(value),
        key=lambda error: ([str(part) for part in error.absolute_path], error.message),
    ):
        location = "/".join(str(part) for part in violation.absolute_path)
        messages.append(f"{location or '<root>'}: {violation.message}")
    return messages


def _label_errors(dataset: str, label: Any, input_value: Any = None) -> list[str]:
    if not isinstance(label, dict):
        return ["label structuré absent"]
    errors = _schema_errors(_label_validator(dataset), label)
    errors.extend(label_invariant_errors(dataset, label, input_value))
    return errors


def _task_core(
    dataset: str,
    case: Mapping[str, Any],
    *,
    annotator_id: str,
) -> dict[str, Any]:
    if dataset not in DATASETS:
        raise ValueError(f"dataset inconnu : {dataset}")
    annotator = require_identifier(annotator_id, "annotator_id")
    case_id = require_identifier(case.get("case_id"), "case_id")
    group_id = require_identifier(case.get("group_id"), "group_id")
    visible = project_blind_input(dataset, case)
    input_errors = _schema_errors(_input_validator(dataset), visible)
    if input_errors:
        raise ValueError("input candidat invalide: " + "; ".join(input_errors))
    split = split_for_group(group_id)
    current_schema = schema_fingerprint(dataset)
    current_input = input_fingerprint(dataset, case_id, group_id, split, visible)
    return {
        "pack_version": PACK_VERSION,
        "dataset": dataset,
        "schema_fingerprint": current_schema,
        "split_policy_version": SPLIT_POLICY_VERSION,
        "case_id": case_id,
        "group_id": group_id,
        "split": split,
        "input": visible,
        "input_fingerprint": current_input,
        "annotation": {
            "annotator_id": annotator,
            "label": None,
            "confidence": None,
        },
    }


def prepare_pack(
    dataset: str,
    cases: Iterable[Mapping[str, Any]],
    *,
    annotator_id: str,
) -> list[dict[str, Any]]:
    """Crée un pack complet dont l'empreinte lie tous les cas à un humain."""
    tasks = [_task_core(dataset, case, annotator_id=annotator_id) for case in cases]
    if not tasks:
        raise ValueError("un pack d'annotation ne peut pas être vide")
    tasks.sort(key=lambda task: task["case_id"])
    case_ids = [task["case_id"] for task in tasks]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("case_id dupliqué dans le pack candidat")
    fingerprint = pack_fingerprint(
        dataset,
        tasks[0]["annotation"]["annotator_id"],
        tasks[0]["schema_fingerprint"],
        [task["input_fingerprint"] for task in tasks],
    )
    for task in tasks:
        task["pack_fingerprint"] = fingerprint
    return tasks


def prepare_blind_task(
    dataset: str,
    case: Mapping[str, Any],
    *,
    annotator_id: str,
) -> dict[str, Any]:
    """Compatibilité pratique : prépare un pack aveugle d'un seul cas."""
    return prepare_pack(dataset, [case], annotator_id=annotator_id)[0]


def _validate_pack(
    dataset: str,
    pack_id: str,
    tasks: list[dict[str, Any]],
) -> tuple[list[str], str | None, dict[str, dict[str, Any]]]:
    errors: list[str] = []
    annotators: set[str] = set()
    by_case: dict[str, dict[str, Any]] = {}
    fingerprints: list[str] = []
    current_schema = schema_fingerprint(dataset)

    for index, task in enumerate(tasks, 1):
        prefix = f"pack {pack_id} record {index}"
        if not isinstance(task, dict):
            errors.append(f"{prefix}: objet attendu")
            continue
        extra = sorted(set(task) - _PACK_KEYS)
        missing = sorted(_PACK_KEYS - set(task))
        if extra or missing:
            if extra:
                errors.append(f"{prefix}: champs interdits: {', '.join(extra)}")
            if missing:
                errors.append(f"{prefix}: champs absents: {', '.join(missing)}")
            continue
        if task.get("pack_version") != PACK_VERSION:
            errors.append(f"{prefix}: pack_version incompatible")
        if task.get("dataset") != dataset:
            errors.append(f"{prefix}: dataset inattendu")
        if task.get("schema_fingerprint") != current_schema:
            errors.append(f"{prefix}: schema_fingerprint incompatible")
        if task.get("split_policy_version") != SPLIT_POLICY_VERSION:
            errors.append(f"{prefix}: split_policy_version incompatible")
        try:
            case_id = require_identifier(task.get("case_id"), "case_id")
            group_id = require_identifier(task.get("group_id"), "group_id")
        except ValueError as exc:
            errors.append(f"{prefix}: {exc}")
            continue
        if case_id in by_case:
            errors.append(f"{prefix}: case_id dupliqué dans le pack")
            continue
        expected_split = split_for_group(group_id)
        if task.get("split") != expected_split:
            errors.append(f"{prefix}: split non canonique")
        input_value = task.get("input")
        if not isinstance(input_value, dict):
            errors.append(f"{prefix}: input structuré absent")
            continue
        if set(input_value) != set(INPUT_FIELDS[dataset]):
            errors.append(f"{prefix}: projection input incompatible")
        input_schema_errors = _schema_errors(_input_validator(dataset), input_value)
        if input_schema_errors:
            errors.append(
                f"{prefix}: input invalide: {'; '.join(input_schema_errors)}"
            )
        try:
            ensure_no_reserved_fields(input_value)
            expected_input = input_fingerprint(
                dataset,
                case_id,
                group_id,
                expected_split,
                input_value,
            )
        except ValueError as exc:
            errors.append(f"{prefix}: {exc}")
            continue
        if task.get("input_fingerprint") != expected_input:
            errors.append(f"{prefix}: input_fingerprint invalide")
        fingerprints.append(expected_input)
        annotation = task.get("annotation")
        if not isinstance(annotation, dict) or set(annotation) != _ANNOTATION_KEYS:
            errors.append(f"{prefix}: annotation incompatible")
            continue
        try:
            annotator = require_identifier(annotation.get("annotator_id"), "annotator_id")
        except ValueError as exc:
            errors.append(f"{prefix}: {exc}")
            continue
        annotators.add(annotator)
        if annotation.get("confidence") not in {"certain", "probable", "unknown"}:
            errors.append(f"{prefix}: confiance invalide")
        label_errors = _label_errors(dataset, annotation.get("label"), input_value)
        if label_errors:
            errors.append(f"{prefix}: label invalide: {'; '.join(label_errors)}")
        by_case[case_id] = task

    annotator: str | None = None
    if len(annotators) != 1:
        errors.append(f"pack {pack_id}: exactement un annotateur requis")
    else:
        annotator = next(iter(annotators))
    if annotator is not None:
        expected_pack = pack_fingerprint(
            dataset,
            annotator,
            current_schema,
            sorted(fingerprints),
        )
        if pack_id != expected_pack:
            errors.append(f"pack {pack_id}: empreinte de pack invalide")
    return errors, annotator, by_case


def _final_record(
    dataset: str,
    task: Mapping[str, Any],
    annotations: list[dict[str, Any]],
    source_packs: list[str],
    *,
    gold: Mapping[str, Any],
    adjudication: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_annotations = _clone(annotations)
    for annotation in normalized_annotations:
        annotation["label"] = normalize_label(dataset, annotation["label"])
    normalized_gold = normalize_label(dataset, gold)
    normalized_adjudication = _clone(adjudication) if adjudication is not None else None
    if normalized_adjudication is not None:
        normalized_adjudication["label"] = normalize_label(
            dataset,
            normalized_adjudication["label"],
        )
    record: dict[str, Any] = {
        "record_version": RECORD_VERSION,
        "dataset": dataset,
        "schema_fingerprint": task["schema_fingerprint"],
        "split_policy_version": SPLIT_POLICY_VERSION,
        "case_id": task["case_id"],
        "group_id": task["group_id"],
        "split": task["split"],
        "input": _clone(task["input"]),
        "gold": normalized_gold,
        "annotations": normalized_annotations,
        "source_pack_fingerprints": sorted(source_packs),
    }
    if normalized_adjudication is not None:
        record["adjudication"] = normalized_adjudication
    record["case_fingerprint"] = case_fingerprint(record)
    validation_errors = _schema_errors(_record_validator(dataset), record)
    for index, annotation in enumerate(normalized_annotations, 1):
        invariant_errors = label_invariant_errors(
            dataset,
            annotation.get("label") if isinstance(annotation, Mapping) else None,
            task.get("input"),
        )
        validation_errors.extend(
            f"annotation {index}: {error}" for error in invariant_errors
        )
    validation_errors.extend(
        f"gold: {error}"
        for error in label_invariant_errors(
            dataset,
            normalized_gold,
            task.get("input"),
        )
    )
    if normalized_adjudication is not None:
        validation_errors.extend(
            f"adjudication: {error}"
            for error in label_invariant_errors(
                dataset,
                normalized_adjudication.get("label"),
                task.get("input"),
            )
        )
    if validation_errors:
        raise ValueError("final record invalide: " + "; ".join(validation_errors))
    return record


def merge_completed_packs(
    dataset: str,
    records: Iterable[dict[str, Any]],
) -> MergeResult:
    """Fusionne exactement deux packs complets; toute erreur annule le lot."""
    if dataset not in DATASETS:
        raise ValueError(f"dataset inconnu : {dataset}")
    grouped_packs: dict[str, list[dict[str, Any]]] = defaultdict(list)
    errors: list[str] = []
    for index, record in enumerate(records, 1):
        if not isinstance(record, dict):
            errors.append(f"record {index}: objet attendu")
            continue
        pack_id = record.get("pack_fingerprint")
        if not isinstance(pack_id, str) or not pack_id:
            errors.append(f"record {index}: pack_fingerprint absent")
            continue
        grouped_packs[pack_id].append(record)
    if len(grouped_packs) != 2:
        errors.append("exactement deux packs complets sont requis")

    pack_maps: dict[str, dict[str, dict[str, Any]]] = {}
    pack_annotators: dict[str, str] = {}
    for pack_id in sorted(grouped_packs):
        pack_errors, annotator, by_case = _validate_pack(
            dataset, pack_id, grouped_packs[pack_id]
        )
        errors.extend(pack_errors)
        pack_maps[pack_id] = by_case
        if annotator is not None:
            pack_annotators[pack_id] = annotator
    if len(set(pack_annotators.values())) != len(pack_annotators):
        errors.append("deux annotateurs distincts sont requis")

    pack_ids = sorted(pack_maps)
    if len(pack_ids) == 2:
        left_cases = set(pack_maps[pack_ids[0]])
        right_cases = set(pack_maps[pack_ids[1]])
        if left_cases != right_cases:
            errors.append("les deux packs doivent contenir exactement les mêmes case_id")
        for case_id in sorted(left_cases & right_cases):
            left = pack_maps[pack_ids[0]][case_id]
            right = pack_maps[pack_ids[1]][case_id]
            keys = ("case_id", "group_id", "split", "input", "input_fingerprint")
            if canonical_json({key: left.get(key) for key in keys}) != canonical_json(
                {key: right.get(key) for key in keys}
            ):
                errors.append(f"case {case_id}: contenus de tâche divergents")

    if errors:
        return MergeResult((), (), tuple(sorted(set(errors))))

    completed_pack_ids: dict[str, str] = {}
    for pack_id in pack_ids:
        try:
            completed_pack_ids[pack_id] = completed_pack_fingerprint(
                pack_id,
                grouped_packs[pack_id],
            )
        except ValueError as exc:
            errors.append(f"pack {pack_id}: empreinte complétée invalide: {exc}")
    if errors:
        return MergeResult((), (), tuple(sorted(set(errors))))
    source_pack_ids = sorted(completed_pack_ids.values())

    accepted: list[dict[str, Any]] = []
    disagreements: list[dict[str, Any]] = []
    assert len(pack_ids) == 2
    for case_id in sorted(pack_maps[pack_ids[0]]):
        tasks = [pack_maps[pack_id][case_id] for pack_id in pack_ids]
        annotations = [_clone(task["annotation"]) for task in tasks]
        for annotation in annotations:
            annotation["label"] = normalize_label(dataset, annotation["label"])
        annotations.sort(key=lambda annotation: annotation["annotator_id"])
        labels = {canonical_json(annotation["label"]) for annotation in annotations}
        if len(labels) == 1:
            try:
                accepted.append(
                    _final_record(
                        dataset,
                        tasks[0],
                        annotations,
                        source_pack_ids,
                        gold=annotations[0]["label"],
                    )
                )
            except ValueError as exc:
                errors.append(f"case {case_id}: {exc}")
            continue
        disagreement: dict[str, Any] = {
            "record_version": RECORD_VERSION,
            "dataset": dataset,
            "schema_fingerprint": tasks[0]["schema_fingerprint"],
            "split_policy_version": SPLIT_POLICY_VERSION,
            "case_id": case_id,
            "group_id": tasks[0]["group_id"],
            "split": tasks[0]["split"],
            "input": _clone(tasks[0]["input"]),
            "input_fingerprint": tasks[0]["input_fingerprint"],
            "annotations": annotations,
            "source_pack_fingerprints": source_pack_ids,
            "status": "needs_adjudication",
        }
        disagreement["disagreement_fingerprint"] = disagreement_fingerprint(disagreement)
        disagreements.append(disagreement)
    if errors:
        return MergeResult((), (), tuple(sorted(set(errors))))
    return MergeResult(tuple(accepted), tuple(disagreements), ())


def _adjudication_task_fingerprint(task: Mapping[str, Any]) -> str:
    keys = (
        "record_version",
        "dataset",
        "schema_fingerprint",
        "split_policy_version",
        "case_id",
        "group_id",
        "split",
        "input",
        "input_fingerprint",
        "disagreement_fingerprint",
        "adjudicator_id",
    )
    return sha256_value(
        "filon.quality.adjudication-task.v0.5",
        {key: task[key] for key in keys},
    )


def _disagreement_errors(dataset: str, value: Any) -> list[str]:
    """Valide l'enveloppe traçable d'un désaccord avant toute projection."""

    if not isinstance(value, Mapping):
        return ["objet de désaccord attendu"]

    errors: list[str] = []
    keys = set(value)
    extra = sorted(str(key) for key in keys - _DISAGREEMENT_KEYS)
    missing = sorted(_DISAGREEMENT_KEYS - keys)
    if extra:
        errors.append(f"champs de désaccord interdits: {', '.join(extra)}")
    if missing:
        errors.append(f"champs de désaccord absents: {', '.join(missing)}")
    if value.get("record_version") != RECORD_VERSION:
        errors.append("record_version de désaccord incompatible")
    if value.get("dataset") != dataset:
        errors.append("dataset de désaccord inattendu")
    if value.get("schema_fingerprint") != schema_fingerprint(dataset):
        errors.append("schema_fingerprint de désaccord incompatible")
    if value.get("split_policy_version") != SPLIT_POLICY_VERSION:
        errors.append("split_policy_version de désaccord incompatible")
    if value.get("status") != "needs_adjudication":
        errors.append("status de désaccord invalide")

    try:
        case_id = require_identifier(value.get("case_id"), "case_id")
    except ValueError as exc:
        errors.append(str(exc))
        case_id = ""
    try:
        group_id = require_identifier(value.get("group_id"), "group_id")
    except ValueError as exc:
        errors.append(str(exc))
        group_id = ""

    expected_split = None
    if group_id:
        expected_split = split_for_group(group_id)
        if value.get("split") != expected_split:
            errors.append("split de désaccord non canonique")

    input_value = value.get("input")
    if not isinstance(input_value, dict):
        errors.append("input de désaccord structuré absent")
    else:
        if set(input_value) != set(INPUT_FIELDS[dataset]):
            errors.append("projection input de désaccord incompatible")
        input_errors = _schema_errors(_input_validator(dataset), input_value)
        if input_errors:
            errors.append("input de désaccord invalide: " + "; ".join(input_errors))
        if case_id and group_id and expected_split is not None:
            try:
                ensure_no_reserved_fields(input_value)
                expected_input = input_fingerprint(
                    dataset,
                    case_id,
                    group_id,
                    expected_split,
                    input_value,
                )
            except ValueError as exc:
                errors.append(str(exc))
            else:
                if value.get("input_fingerprint") != expected_input:
                    errors.append("input_fingerprint de désaccord invalide")

    annotations = value.get("annotations")
    annotator_ids: list[str] = []
    labels: list[str] = []
    if not isinstance(annotations, list) or len(annotations) != 2:
        errors.append("exactement deux annotations initiales sont requises")
    else:
        for index, annotation in enumerate(annotations, 1):
            prefix = f"annotation initiale {index}"
            if not isinstance(annotation, Mapping):
                errors.append(f"{prefix}: objet attendu")
                continue
            if set(annotation) != _ANNOTATION_KEYS:
                errors.append(f"{prefix}: champs incompatibles")
            try:
                annotator_ids.append(
                    require_identifier(annotation.get("annotator_id"), "annotator_id")
                )
            except ValueError as exc:
                errors.append(f"{prefix}: {exc}")
            if annotation.get("confidence") not in {
                "certain",
                "probable",
                "unknown",
            }:
                errors.append(f"{prefix}: confiance invalide")
            label_errors = _label_errors(
                dataset,
                annotation.get("label"),
                input_value,
            )
            if label_errors:
                errors.append(f"{prefix}: label invalide: {'; '.join(label_errors)}")
            else:
                labels.append(canonical_json(annotation.get("label")))
        if len(annotator_ids) == 2:
            if len(set(annotator_ids)) != 2:
                errors.append("deux annotateurs initiaux distincts sont requis")
            if annotator_ids != sorted(annotator_ids):
                errors.append("annotations initiales non canoniquement ordonnées")
        if len(labels) == 2 and len(set(labels)) != 2:
            errors.append("les annotations initiales ne sont pas en désaccord")

    source_packs = value.get("source_pack_fingerprints")
    if not isinstance(source_packs, list) or len(source_packs) != 2:
        errors.append("exactement deux source_pack_fingerprints sont requis")
    elif not all(
        isinstance(fingerprint, str)
        and FINGERPRINT_PATTERN.fullmatch(fingerprint) is not None
        for fingerprint in source_packs
    ):
        errors.append("source_pack_fingerprints invalides")
    else:
        if len(set(source_packs)) != 2:
            errors.append("source_pack_fingerprints doivent être distincts")
        if source_packs != sorted(source_packs):
            errors.append("source_pack_fingerprints non canoniquement ordonnés")

    try:
        expected_fingerprint = disagreement_fingerprint(value)
    except (KeyError, TypeError, ValueError) as exc:
        errors.append(f"désaccord non empreintable: {exc}")
    else:
        if value.get("disagreement_fingerprint") != expected_fingerprint:
            errors.append("disagreement_fingerprint invalide")
    return errors


def prepare_adjudication_pack(
    dataset: str,
    disagreements: Iterable[Mapping[str, Any]],
    *,
    adjudicator_id: str,
) -> list[dict[str, Any]]:
    """Prépare un troisième jugement aveugle sans dévoiler les deux labels."""
    if dataset not in DATASETS:
        raise ValueError(f"dataset inconnu : {dataset}")
    adjudicator = require_identifier(adjudicator_id, "adjudicator_id")
    tasks: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, disagreement in enumerate(disagreements, 1):
        validation_errors = _disagreement_errors(dataset, disagreement)
        if validation_errors:
            raise ValueError(
                f"désaccord {index} invalide: " + "; ".join(validation_errors)
            )
        assert isinstance(disagreement, Mapping)
        case_id = require_identifier(disagreement.get("case_id"), "case_id")
        if case_id in seen:
            raise ValueError("case_id dupliqué dans les désaccords")
        seen.add(case_id)
        initial_ids = {
            annotation.get("annotator_id")
            for annotation in disagreement["annotations"]
            if isinstance(annotation, Mapping)
        }
        if adjudicator in initial_ids:
            raise ValueError(f"case {case_id}: troisième humain distinct requis")
        task = {
            key: _clone(disagreement[key])
            for key in (
                "record_version",
                "dataset",
                "schema_fingerprint",
                "split_policy_version",
                "case_id",
                "group_id",
                "split",
                "input",
                "input_fingerprint",
                "disagreement_fingerprint",
            )
        }
        task["adjudicator_id"] = adjudicator
        task["adjudication"] = {
            "adjudicator_id": adjudicator,
            "label": None,
            "confidence": None,
            "rationale": None,
        }
        task["adjudication_task_fingerprint"] = _adjudication_task_fingerprint(task)
        tasks.append(task)
    if not tasks:
        raise ValueError("aucun désaccord à adjuger")
    return sorted(tasks, key=lambda task: task["case_id"])


def adjudicate_disagreements(
    dataset: str,
    disagreements: Iterable[dict[str, Any]],
    completed_tasks: Iterable[dict[str, Any]],
) -> AdjudicationResult:
    """Produit des golds après un troisième jugement humain traçable."""
    disagreement_map: dict[str, dict[str, Any]] = {}
    task_map: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    for row, target, kind in (
        *((row, disagreement_map, "désaccord") for row in disagreements),
        *((row, task_map, "adjudication") for row in completed_tasks),
    ):
        if not isinstance(row, Mapping):
            errors.append(f"{kind}: objet attendu")
            continue
        try:
            case_id = require_identifier(row.get("case_id"), "case_id")
        except ValueError:
            case_id = ""
        if not case_id or case_id in target:
            errors.append(f"{kind} avec case_id absent ou dupliqué")
        else:
            target[case_id] = dict(row)
    if set(disagreement_map) != set(task_map):
        errors.append("désaccords et adjudications doivent couvrir les mêmes case_id")

    staged: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for case_id in sorted(set(disagreement_map) & set(task_map)):
        disagreement = disagreement_map[case_id]
        task = task_map[case_id]
        case_errors = _disagreement_errors(dataset, disagreement)
        if set(task) != _ADJUDICATION_TASK_KEYS:
            case_errors.append("champs de tâche d'adjudication incompatibles")
        if disagreement.get("dataset") != dataset or task.get("dataset") != dataset:
            case_errors.append("dataset inattendu")
        try:
            expected_disagreement = disagreement_fingerprint(disagreement)
        except (KeyError, TypeError, ValueError):
            expected_disagreement = ""
        if task.get("disagreement_fingerprint") != expected_disagreement:
            case_errors.append("adjudication liée au mauvais désaccord")
        try:
            expected_task = _adjudication_task_fingerprint(task)
        except (KeyError, TypeError, ValueError):
            expected_task = ""
        if task.get("adjudication_task_fingerprint") != expected_task:
            case_errors.append("adjudication_task_fingerprint invalide")
        for key in (
            "record_version",
            "dataset",
            "schema_fingerprint",
            "split_policy_version",
            "case_id",
            "group_id",
            "split",
            "input",
            "input_fingerprint",
        ):
            try:
                unchanged = canonical_json(task.get(key)) == canonical_json(
                    disagreement.get(key)
                )
            except (TypeError, ValueError):
                unchanged = False
            if not unchanged:
                case_errors.append(f"champ d'adjudication altéré: {key}")
        adjudication = task.get("adjudication")
        if not isinstance(adjudication, dict) or set(adjudication) != _ADJUDICATION_KEYS:
            case_errors.append("adjudication incompatible")
        else:
            if adjudication.get("adjudicator_id") != task.get("adjudicator_id"):
                case_errors.append("identité adjudicateur incohérente")
            try:
                adjudicator = require_identifier(
                    adjudication.get("adjudicator_id"), "adjudicator_id"
                )
                rationale = require_identifier(adjudication.get("rationale"), "rationale")
            except ValueError as exc:
                case_errors.append(str(exc))
                adjudicator = ""
                rationale = ""
            initial_annotations = disagreement.get("annotations")
            initial_ids = (
                {
                    annotation.get("annotator_id")
                    for annotation in initial_annotations
                    if isinstance(annotation, Mapping)
                }
                if isinstance(initial_annotations, list)
                else set()
            )
            if adjudicator in initial_ids:
                case_errors.append("troisième humain distinct requis")
            if adjudication.get("confidence") not in {"certain", "probable", "unknown"}:
                case_errors.append("confiance d'adjudication invalide")
            label_errors = _label_errors(
                dataset,
                adjudication.get("label"),
                disagreement.get("input"),
            )
            if label_errors:
                case_errors.append(
                    "label d'adjudication invalide: " + "; ".join(label_errors)
                )
            if not case_errors:
                staged.append(
                    (
                        disagreement,
                        {
                            "adjudicator_id": adjudicator,
                            "label": normalize_label(
                                dataset,
                                adjudication["label"],
                            ),
                            "confidence": adjudication["confidence"],
                            "rationale": rationale,
                        },
                    )
                )
        errors.extend(f"case {case_id}: {error}" for error in case_errors)

    if errors:
        return AdjudicationResult((), tuple(sorted(set(errors))))
    accepted: list[dict[str, Any]] = []
    for disagreement, adjudication in staged:
        source = {
            "schema_fingerprint": disagreement["schema_fingerprint"],
            "case_id": disagreement["case_id"],
            "group_id": disagreement["group_id"],
            "split": disagreement["split"],
            "input": disagreement["input"],
        }
        try:
            accepted.append(
                _final_record(
                    dataset,
                    source,
                    _clone(disagreement["annotations"]),
                    list(disagreement["source_pack_fingerprints"]),
                    gold=adjudication["label"],
                    adjudication=adjudication,
                )
            )
        except ValueError as exc:
            errors.append(f"case {disagreement['case_id']}: {exc}")
    if errors:
        return AdjudicationResult((), tuple(sorted(set(errors))))
    return AdjudicationResult(tuple(accepted), ())


def _stage_bytes(path: Path, payload: bytes, *, suffix: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=suffix,
        dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return temporary


def _fsync_parent_directories(paths: Iterable[Path]) -> None:
    for parent in sorted({path.parent.resolve() for path in paths}, key=str):
        descriptor = os.open(parent, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


def _write_jsonl_batch(
    outputs: Mapping[Path, Iterable[Mapping[str, Any]]],
) -> None:
    """Publie plusieurs JSONL comme une transaction au niveau du processus.

    Tous les contenus et toutes les sauvegardes sont préparés avant le
    premier remplacement. Si un remplacement ultérieur échoue, les cibles
    déjà publiées retrouvent leur contenu initial.
    """

    items = list(outputs.items())
    if not items:
        return
    paths = [path for path, _records in items]
    if not _paths_are_distinct(paths):
        raise ValueError("les sorties JSONL batch doivent être distinctes")

    # Matérialiser et canoniser avant toute création ou modification de cible.
    payloads = {
        path: "".join(canonical_json(record) + "\n" for record in records).encode(
            "utf-8"
        )
        for path, records in items
    }
    staged: dict[Path, Path] = {}
    backups: dict[Path, Path] = {}
    existed: dict[Path, bool] = {}
    committed: list[Path] = []
    preserve_backups = False
    try:
        for path in paths:
            staged[path] = _stage_bytes(path, payloads[path], suffix=".tmp")
        for path in paths:
            existed[path] = path.exists()
            if existed[path]:
                backups[path] = _stage_bytes(
                    path,
                    path.read_bytes(),
                    suffix=".rollback",
                )
        for path in paths:
            os.replace(staged[path], path)
            committed.append(path)
        _fsync_parent_directories(paths)
    except BaseException as exc:
        rollback_errors: list[str] = []
        for path in reversed(committed):
            try:
                if existed[path]:
                    os.replace(backups[path], path)
                    backups.pop(path, None)
                else:
                    path.unlink(missing_ok=True)
            except OSError as rollback_exc:
                rollback_errors.append(f"{path}: {rollback_exc}")
        try:
            _fsync_parent_directories(committed)
        except OSError as rollback_exc:
            rollback_errors.append(f"directory fsync: {rollback_exc}")
        if rollback_errors:
            preserve_backups = True
            raise RuntimeError(
                "rollback JSONL batch incomplet: " + "; ".join(rollback_errors)
            ) from exc
        raise
    finally:
        temporary_files = list(staged.values())
        if not preserve_backups:
            temporary_files.extend(backups.values())
        for temporary in temporary_files:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass


def _write_jsonl(path: Path, records: Iterable[Mapping[str, Any]]) -> None:
    _write_jsonl_batch({path: records})


def _paths_are_distinct(paths: Iterable[Path]) -> bool:
    candidates = list(paths)
    resolved = [path.resolve() for path in candidates]
    collision_keys = [
        unicodedata.normalize("NFC", str(path)).casefold() for path in resolved
    ]
    if len(collision_keys) != len(set(collision_keys)):
        return False
    for index, left in enumerate(candidates):
        if not left.exists():
            continue
        for right in candidates[index + 1 :]:
            if right.exists() and os.path.samefile(left, right):
                return False
    return True


def _execute_command(args: argparse.Namespace) -> int:
    if args.command == "prepare":
        if not _paths_are_distinct([args.input, args.output]):
            print("les chemins input et output doivent être distincts")
            return 2
        _write_jsonl(
            args.output,
            prepare_pack(
                args.dataset,
                read_jsonl(args.input),
                annotator_id=args.annotator_id,
            ),
        )
        return 0
    if args.command == "prepare-adjudication":
        if not _paths_are_distinct([args.input, args.output]):
            print("les chemins input et output doivent être distincts")
            return 2
        _write_jsonl(
            args.output,
            prepare_adjudication_pack(
                args.dataset,
                read_jsonl(args.input),
                adjudicator_id=args.adjudicator_id,
            ),
        )
        return 0
    if args.command == "merge":
        if not _paths_are_distinct([*args.input, args.output, args.disagreements]):
            print("tous les chemins de merge doivent être distincts")
            return 2
        records = [record for path in args.input for record in read_jsonl(path)]
        result = merge_completed_packs(args.dataset, records)
        if result.errors:
            for error in result.errors:
                print(error)
            return 2
        _write_jsonl_batch(
            {
                args.output: result.accepted,
                args.disagreements: result.disagreements,
            }
        )
        return 1 if result.disagreements else 0

    if not _paths_are_distinct([args.disagreements, args.input, args.output]):
        print("tous les chemins d'adjudication doivent être distincts")
        return 2
    result = adjudicate_disagreements(
        args.dataset,
        read_jsonl(args.disagreements),
        read_jsonl(args.input),
    )
    if result.errors:
        for error in result.errors:
            print(error)
        return 2
    _write_jsonl(args.output, result.accepted)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Workflow d'annotation FILON v0.5")
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser("prepare", help="crée un pack aveugle versionné")
    prepare.add_argument("--dataset", choices=sorted(DATASETS), required=True)
    prepare.add_argument("--input", type=Path, required=True)
    prepare.add_argument("--output", type=Path, required=True)
    prepare.add_argument("--annotator-id", required=True)

    merge = subparsers.add_parser("merge", help="fusionne deux packs remplis")
    merge.add_argument("--dataset", choices=sorted(DATASETS), required=True)
    merge.add_argument("--input", type=Path, action="append", required=True)
    merge.add_argument("--output", type=Path, required=True)
    merge.add_argument("--disagreements", type=Path, required=True)

    prepare_adj = subparsers.add_parser(
        "prepare-adjudication", help="crée le pack aveugle du troisième humain"
    )
    prepare_adj.add_argument("--dataset", choices=sorted(DATASETS), required=True)
    prepare_adj.add_argument("--input", type=Path, required=True)
    prepare_adj.add_argument("--output", type=Path, required=True)
    prepare_adj.add_argument("--adjudicator-id", required=True)

    adjudicate = subparsers.add_parser(
        "adjudicate", help="fusionne les désaccords et le troisième jugement"
    )
    adjudicate.add_argument("--dataset", choices=sorted(DATASETS), required=True)
    adjudicate.add_argument("--disagreements", type=Path, required=True)
    adjudicate.add_argument("--input", type=Path, required=True)
    adjudicate.add_argument("--output", type=Path, required=True)

    args = parser.parse_args()
    try:
        return _execute_command(args)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"erreur workflow: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
