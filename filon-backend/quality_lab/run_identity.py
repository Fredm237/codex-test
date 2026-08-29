"""Identité canonique et auditable d'un run du FILON Quality Lab."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .integrity import (
    DATASETS,
    FINGERPRINT_PATTERN,
    LAB_VERSION,
    require_identifier,
    sha256_value,
)


RUN_SCHEMA_VERSION = "quality-run/v1"
RUN_ID_DOMAIN = f"filon.quality.engine-run.v{LAB_VERSION.removesuffix('.0')}"


def _canonical_outputs(
    outputs: Mapping[str, Sequence[Mapping[str, Any]]],
) -> dict[str, list[dict[str, Any]]]:
    if set(outputs) != set(DATASETS):
        raise ValueError("run outputs must contain exactly seven datasets")
    canonical: dict[str, list[dict[str, Any]]] = {}
    for dataset in DATASETS:
        rows = outputs[dataset]
        if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
            raise ValueError(f"{dataset} run outputs must be a sequence")
        cleaned: list[dict[str, Any]] = []
        seen_case_ids: set[str] = set()
        for row in rows:
            if not isinstance(row, Mapping):
                raise ValueError(f"{dataset} run output must be an object")
            if row.get("dataset") != dataset:
                raise ValueError(f"{dataset} run output has a mismatched dataset")
            case_id = require_identifier(row.get("case_id"), "case_id")
            if case_id in seen_case_ids:
                raise ValueError(f"duplicate {dataset} run output case_id {case_id!r}")
            seen_case_ids.add(case_id)
            value = dict(row)
            value.pop("run_id", None)
            cleaned.append(value)
        canonical[dataset] = sorted(cleaned, key=lambda row: str(row["case_id"]))
    return canonical


def _canonical_adapters(
    adapters: Mapping[str, Mapping[str, Any]],
    *,
    active_datasets: set[str],
) -> dict[str, dict[str, str]]:
    if not isinstance(adapters, Mapping):
        raise ValueError("run adapters must be an object")
    if set(adapters) != active_datasets:
        raise ValueError(
            "run adapters must match exactly the datasets with predictions"
        )
    canonical: dict[str, dict[str, str]] = {}
    for dataset in DATASETS:
        if dataset not in adapters:
            continue
        config = adapters[dataset]
        if not isinstance(config, Mapping) or set(config) != {
            "engine_id",
            "engine_version",
        }:
            raise ValueError(
                f"{dataset} adapter must contain only engine_id and engine_version"
            )
        canonical[dataset] = {
            "engine_id": require_identifier(
                config.get("engine_id"), f"{dataset} engine_id"
            ),
            "engine_version": require_identifier(
                config.get("engine_version"), f"{dataset} engine_version"
            ),
        }
    return canonical


def quality_run_id(
    *,
    system_version: str,
    evaluator_version: str,
    gold_manifest_sha256: str,
    outputs: Mapping[str, Sequence[Mapping[str, Any]]],
    adapters: Mapping[str, Mapping[str, Any]],
) -> str:
    """Calcule l'identité d'un run à partir de toutes ses preuves rejouables.

    Le champ ``run_id`` éventuellement présent dans les lignes est exclu pour
    éviter l'auto-référence. L'ordre des JSONL n'influence pas l'identité : les
    sorties sont ordonnées canoniquement par ``case_id``.
    """

    checked_system_version = require_identifier(system_version, "system_version")
    if evaluator_version != LAB_VERSION:
        raise ValueError(f"evaluator_version must be {LAB_VERSION}")
    if not isinstance(gold_manifest_sha256, str) or not FINGERPRINT_PATTERN.fullmatch(
        gold_manifest_sha256
    ):
        raise ValueError("gold_manifest_sha256 is invalid")
    canonical_outputs = _canonical_outputs(outputs)
    active_datasets = {
        dataset for dataset, rows in canonical_outputs.items() if rows
    }
    if not active_datasets:
        raise ValueError("an empty run cannot have a run_id")
    canonical_adapters = _canonical_adapters(
        adapters,
        active_datasets=active_datasets,
    )
    fingerprint = sha256_value(
        RUN_ID_DOMAIN,
        {
            "schema_version": RUN_SCHEMA_VERSION,
            "system_version": checked_system_version,
            "evaluator_version": evaluator_version,
            "gold_manifest_sha256": gold_manifest_sha256,
            "adapters": canonical_adapters,
            "outputs": canonical_outputs,
        },
    )
    return f"filon-quality-{fingerprint.removeprefix('sha256:')}"
