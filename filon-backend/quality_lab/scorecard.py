"""Scorecard holdout exécutable et fail-closed du FILON Quality Lab."""

from __future__ import annotations

import argparse
import hashlib
import math
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

from .integrity import (
    DATASETS,
    LAB_VERSION,
    atomic_write_text,
    canonical_json,
    case_fingerprint,
    label_invariant_errors,
    manifest_fingerprint,
    read_json,
    require_identifier,
    sha256_value,
    split_for_group,
    strict_loads,
)
from .metrics import (
    attachment_metrics,
    calibration_metrics,
    decision_safety_metrics,
    entity_resolution_metrics,
    exact_json_value,
    offer_truth_metrics,
    retrieval_metrics,
    strata_metrics,
    taxonomy_metrics,
    variant_resolution_metrics,
)
from .readiness import build_readiness_report
from .run_identity import quality_run_id


ERROR_CODES = {
    "manifest_invalid": "QL001_MANIFEST_INVALID",
    "gold_not_ready": "QL002_GOLD_NOT_READY",
    "split_mismatch": "QL003_HOLDOUT_SPLIT_MISMATCH",
    "gold_digest": "QL004_GOLD_DIGEST_MISMATCH",
    "run_invalid": "QL005_RUN_SCHEMA_INVALID",
    "prediction_invalid": "QL006_PREDICTION_SCHEMA_INVALID",
    "duplicate": "QL007_DUPLICATE_CASE_ID",
    "missing": "QL008_MISSING_CASE_ID",
    "unexpected": "QL009_UNEXPECTED_CASE_ID",
    "fingerprint": "QL010_CASE_FINGERPRINT_MISMATCH",
    "confidence": "QL011_CONFIDENCE_INVALID",
    "ranking_duplicate": "QL012_DUPLICATE_RANKED_ID",
    "not_measurable": "QL013_METRIC_NOT_MEASURABLE",
    "metric_range": "QL014_METRIC_OUT_OF_RANGE",
    "gate_missing": "QL015_REQUIRED_GATE_MISSING",
}

GATE_CONTRACT: dict[str, tuple[str, str]] = {
    "category_accuracy_min": ("category_accuracy_ci95_lower", "min"),
    "subcategory_accuracy_min": ("subcategory_accuracy_ci95_lower", "min"),
    "product_role_accuracy_min": ("product_role_accuracy_ci95_lower", "min"),
    "entity_match_accuracy_min": ("entity_match_accuracy_ci95_lower", "min"),
    "false_merge_rate_max": ("false_merge_rate_ci95_upper", "max"),
    "false_split_rate_max": ("false_split_rate_ci95_upper", "max"),
    "entity_variant_relation_accuracy_min": (
        "entity_variant_relation_accuracy_ci95_lower",
        "min",
    ),
    "variant_resolution_accuracy_min": (
        "variant_resolution_accuracy_ci95_lower",
        "min",
    ),
    "offer_attachment_accuracy_min": (
        "offer_attachment_accuracy_ci95_lower",
        "min",
    ),
    "offer_eligibility_accuracy_min": (
        "offer_eligibility_accuracy_ci95_lower",
        "min",
    ),
    "false_eligible_offers_max": ("false_eligible_offers", "max"),
    "price_accuracy_min": ("price_accuracy_ci95_lower", "min"),
    "stock_accuracy_min": ("stock_accuracy_ci95_lower", "min"),
    "shipping_accuracy_min": ("shipping_accuracy_ci95_lower", "min"),
    "affiliate_link_accuracy_min": (
        "affiliate_link_accuracy_ci95_lower",
        "min",
    ),
    "retrieval_top_3_relevance_min": (
        "retrieval_top_3_relevance_ci95_lower",
        "min",
    ),
    "exact_product_match_accuracy_min": (
        "exact_product_match_accuracy_ci95_lower",
        "min",
    ),
    "absurd_result_rate_max": ("absurd_result_rate_ci95_upper", "lt"),
    "retrieval_recall_at_50_min": (
        "retrieval_recall_at_50_ci95_lower",
        "min",
    ),
    "retrieval_ndcg_at_10_min": ("retrieval_ndcg_at_10_ci95_lower", "min"),
    "retrieval_no_match_accuracy_min": (
        "retrieval_no_match_accuracy_ci95_lower",
        "min",
    ),
    "retrieval_ambiguous_accuracy_min": (
        "retrieval_ambiguous_accuracy_ci95_lower",
        "min",
    ),
    "retrieval_constraint_violations_at_10_max": (
        "retrieval_constraint_violations_at_10",
        "max",
    ),
    "constraint_violations_max": ("constraint_violations", "max"),
    "unsupported_claims_max": ("unsupported_claims", "max"),
    "calibration_ece_max": ("calibration_ece_ci95_upper", "max"),
    "sourced_explanation_coverage_min": (
        "sourced_explanation_coverage_ci95_lower",
        "min",
    ),
}
# Alias historique conservé pour les tests et consommateurs internes existants.
_GATE_METRICS = GATE_CONTRACT
_HOLDOUT_FINGERPRINT_DOMAIN = (
    f"filon.quality.holdout.v{LAB_VERSION.removesuffix('.0')}"
)
_RATIO_METRICS = {
    "category_accuracy_ci95_lower",
    "subcategory_accuracy_ci95_lower",
    "product_role_accuracy_ci95_lower",
    "entity_match_accuracy_ci95_lower",
    "false_merge_rate_ci95_upper",
    "false_split_rate_ci95_upper",
    "entity_variant_relation_accuracy_ci95_lower",
    "variant_resolution_accuracy_ci95_lower",
    "offer_attachment_accuracy_ci95_lower",
    "offer_eligibility_accuracy_ci95_lower",
    "price_accuracy_ci95_lower",
    "stock_accuracy_ci95_lower",
    "shipping_accuracy_ci95_lower",
    "affiliate_link_accuracy_ci95_lower",
    "retrieval_top_3_relevance_ci95_lower",
    "exact_product_match_accuracy_ci95_lower",
    "absurd_result_rate_ci95_upper",
    "retrieval_recall_at_50_ci95_lower",
    "retrieval_ndcg_at_10_ci95_lower",
    "retrieval_no_match_accuracy_ci95_lower",
    "retrieval_ambiguous_accuracy_ci95_lower",
    "calibration_ece_ci95_upper",
    "sourced_explanation_coverage_ci95_lower",
}

_MEASUREMENT_SUPPORT: dict[str, str] = {
    "taxonomy_cases_min": "taxonomy_cases",
    "entity_different_pairs_min": "entity_different_pairs",
    "entity_same_pairs_min": "entity_same_pairs",
    "entity_variant_pairs_min": "entity_variant_pairs",
    "variant_cases_min": "variant_cases",
    "offer_eligible_cases_min": "offer_eligible_cases",
    "offer_all_cases_min": "offer_all_cases",
    "offer_noneligible_cases_min": "offer_noneligible_cases",
    "offer_truth_cases_min": "offer_truth_cases",
    "retrieval_queries_min": "retrieval_queries",
    "retrieval_answerable_queries_min": "retrieval_answerable_queries",
    "retrieval_exact_product_queries_min": "retrieval_exact_product_queries",
    "retrieval_no_match_queries_min": "retrieval_no_match_queries",
    "retrieval_ambiguous_queries_min": "retrieval_ambiguous_queries",
    "decision_cases_min": "decision_cases",
    "decision_non_abstain_min": "decision_non_abstain",
    "calibration_cases_min": "calibration_cases",
    "scenario_exact_product_cases_min": "scenario_exact_product_cases",
    "scenario_generic_product_cases_min": "scenario_generic_product_cases",
    "scenario_use_case_cases_min": "scenario_use_case_cases",
    "scenario_constraint_heavy_cases_min": "scenario_constraint_heavy_cases",
    "scenario_accessory_cases_min": "scenario_accessory_cases",
    "scenario_replacement_part_cases_min": "scenario_replacement_part_cases",
    "scenario_variant_sensitive_cases_min": "scenario_variant_sensitive_cases",
    "scenario_multi_product_cases_min": "scenario_multi_product_cases",
    "scenario_ambiguous_cases_min": "scenario_ambiguous_cases",
    "scenario_no_match_cases_min": "scenario_no_match_cases",
    "language_fr_cases_min": "language_fr_cases",
    "language_nl_cases_min": "language_nl_cases",
    "language_en_cases_min": "language_en_cases",
    "vertical_smartphones_cases_min": "vertical_smartphones_cases",
    "vertical_laptops_cases_min": "vertical_laptops_cases",
    "vertical_tv_cases_min": "vertical_tv_cases",
    "vertical_headphones_audio_cases_min": "vertical_headphones_audio_cases",
    "vertical_appliances_cases_min": "vertical_appliances_cases",
}


def _error(
    code: str,
    message: str,
    *,
    dataset: str | None = None,
    case_id: str | None = None,
    path: str | None = None,
) -> dict[str, Any]:
    value: dict[str, Any] = {"code": code, "message": message}
    if dataset is not None:
        value["dataset"] = dataset
    if case_id is not None:
        value["case_id"] = case_id
    if path is not None:
        value["path"] = path
    return value


def _sort_errors(errors: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    unique = {
        canonical_json(error): error
        for error in errors
    }
    return sorted(
        unique.values(),
        key=lambda error: (
            error.get("code", ""),
            error.get("dataset", ""),
            error.get("case_id", ""),
            error.get("path", ""),
            error.get("message", ""),
        ),
    )


def _base_report(run_id: str | None = None) -> dict[str, Any]:
    return {
        "schema_version": "quality-scorecard/v1",
        "evaluator_version": LAB_VERSION,
        "run_id": run_id,
        "status": "not_measurable",
        "measurable": False,
        "holdout": {},
        "holdout_fingerprint": None,
        "adapters": {},
        "metrics": {},
        "gates": [],
        "errors": [],
    }


def _holdout_content_fingerprint(
    joined: Mapping[str, list[tuple[dict[str, Any], dict[str, Any]]]],
) -> str:
    """Engage le roster et le contenu exact du holdout test validé.

    Le ``case_fingerprint`` engage déjà l'entrée, le gold, les annotations et
    leur provenance. Le couple dataset/case_id rend en plus la structure du
    roster explicite. Les prédictions et le ``run_id`` restent volontairement
    hors de cette empreinte afin que deux versions système soient comparables.
    """

    if set(joined) != set(DATASETS):
        raise ValueError("holdout roster must contain exactly seven datasets")
    roster: dict[str, list[dict[str, str]]] = {}
    for dataset in DATASETS:
        cases: list[dict[str, str]] = []
        for gold, _prediction in joined[dataset]:
            case_id = require_identifier(gold.get("case_id"), "case_id")
            fingerprint = gold.get("case_fingerprint")
            if not isinstance(fingerprint, str):
                raise ValueError("holdout case_fingerprint must be a string")
            cases.append(
                {
                    "case_id": case_id,
                    "case_fingerprint": fingerprint,
                }
            )
        roster[dataset] = sorted(cases, key=lambda case: case["case_id"])
    return sha256_value(_HOLDOUT_FINGERPRINT_DOMAIN, roster)


def _schema_messages(validator: Draft202012Validator, value: Any) -> list[str]:
    messages: list[str] = []
    for violation in sorted(
        validator.iter_errors(value),
        key=lambda error: ([str(part) for part in error.absolute_path], error.message),
    ):
        location = "/".join(str(part) for part in violation.absolute_path)
        messages.append(f"{location or '<root>'}: {violation.message}")
    return messages


def _validator(path: Path) -> Draft202012Validator:
    schema = read_json(path)
    if not isinstance(schema, dict):
        raise ValueError(f"{path}: schema root must be an object")
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _sha256_bytes(payload: bytes) -> str:
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def _snapshot_bytes(path: Path, label: str) -> bytes:
    try:
        return path.read_bytes()
    except OSError:
        raise ValueError(f"{label} cannot be read: {path}") from None


def _snapshot_json(path: Path, label: str) -> tuple[Any, str]:
    payload = _snapshot_bytes(path, label)
    return strict_loads(payload, source=str(path)), _sha256_bytes(payload)


def _snapshot_jsonl(path: Path, label: str) -> tuple[list[dict[str, Any]], str]:
    payload = _snapshot_bytes(path, label)
    rows: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(payload.split(b"\n"), 1):
        if not raw_line.strip():
            continue
        source = f"{path}:{line_number}"
        value = strict_loads(raw_line, source=source)
        if not isinstance(value, dict):
            raise ValueError(f"{source}: JSONL record must be an object")
        rows.append(value)
    return rows, _sha256_bytes(payload)


def _safe_relative_path(root: Path, relative: Any, label: str) -> Path:
    if not isinstance(relative, str):
        raise ValueError(f"{label} path must be a string")
    candidate = (root / relative).resolve()
    resolved_root = root.resolve()
    if candidate != resolved_root and resolved_root not in candidate.parents:
        raise ValueError(f"{label} path escapes the run root")
    return candidate


def quality_input_paths(manifest_path: str | Path) -> set[Path]:
    """Retourne les artefacts Quality qu'un rapport ne doit jamais écraser."""

    manifest_file = Path(manifest_path).resolve()
    protected = {
        manifest_file,
        manifest_file.parent / "schemas/manifest.schema.json",
        manifest_file.parent / "schemas/prediction.schema.json",
        manifest_file.parent / "schemas/run-manifest.schema.json",
    }
    try:
        manifest = read_json(manifest_file)
    except ValueError:
        return {path.resolve() for path in protected}
    if not isinstance(manifest, Mapping):
        return {path.resolve() for path in protected}
    datasets = manifest.get("datasets")
    if isinstance(datasets, Mapping):
        for config in datasets.values():
            if not isinstance(config, Mapping):
                continue
            for field in ("path", "schema"):
                relative = config.get(field)
                if isinstance(relative, str):
                    protected.add((manifest_file.parent / relative).resolve())
    bootstrap = manifest.get("bootstrap")
    if isinstance(bootstrap, Mapping) and isinstance(bootstrap.get("path"), str):
        protected.add((manifest_file.parent / bootstrap["path"]).resolve())
    return {path.resolve() for path in protected}


def scorecard_input_paths(
    manifest_path: str | Path,
    run_manifest_path: str | Path,
) -> set[Path]:
    protected = quality_input_paths(manifest_path)
    run_file = Path(run_manifest_path).resolve()
    protected.add(run_file)
    try:
        run = read_json(run_file)
    except ValueError:
        return protected
    if not isinstance(run, Mapping):
        return protected
    datasets = run.get("datasets")
    if isinstance(datasets, Mapping):
        for config in datasets.values():
            if isinstance(config, Mapping) and isinstance(config.get("path"), str):
                protected.add((run_file.parent / config["path"]).resolve())
    return protected


def ensure_output_is_distinct(output: str | Path, inputs: Iterable[Path]) -> None:
    output_path = Path(output).resolve()
    output_key = unicodedata.normalize("NFC", str(output_path)).casefold()
    for input_path in inputs:
        candidate = Path(input_path).resolve()
        candidate_key = unicodedata.normalize("NFC", str(candidate)).casefold()
        if output_path == candidate or output_key == candidate_key:
            raise ValueError(f"output would overwrite input artifact: {candidate}")
        if output_path.exists() and candidate.exists():
            try:
                aliases = output_path.samefile(candidate)
            except OSError:
                aliases = False
            if aliases:
                raise ValueError(f"output aliases input artifact: {candidate}")


def _confidence_valid(value: Any) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        numeric = float(value)
    except (OverflowError, TypeError, ValueError):
        return False
    return math.isfinite(numeric) and 0.0 <= numeric <= 1.0


def _prediction_preflight(
    dataset: str,
    rows: list[dict[str, Any]],
    run_id: str | None,
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    for index, row in enumerate(rows, 1):
        path = f"record:{index}"
        case_id = row.get("case_id") if isinstance(row.get("case_id"), str) else None
        if case_id is not None:
            counts[case_id] += 1
            try:
                require_identifier(case_id, "case_id")
            except ValueError as exc:
                errors.append(
                    _error(
                        ERROR_CODES["prediction_invalid"],
                        str(exc),
                        dataset=dataset,
                        case_id=case_id,
                        path=f"{path}/case_id",
                    )
                )
        if row.get("dataset") != dataset or row.get("run_id") != run_id:
            errors.append(
                _error(
                    ERROR_CODES["prediction_invalid"],
                    "prediction dataset or run_id does not match its run manifest",
                    dataset=dataset,
                    case_id=case_id,
                    path=path,
                )
            )
        if not _confidence_valid(row.get("confidence")):
            errors.append(
                _error(
                    ERROR_CODES["confidence"],
                    "confidence must be a finite number between 0 and 1",
                    dataset=dataset,
                    case_id=case_id,
                    path=f"{path}/confidence",
                )
            )
        prediction = row.get("prediction")
        if dataset == "retrieval" and isinstance(prediction, dict):
            ranked = prediction.get("retrieved_product_ids")
            if isinstance(ranked, list) and len(ranked) != len(
                {canonical_json(item) for item in ranked}
            ):
                errors.append(
                    _error(
                        ERROR_CODES["ranking_duplicate"],
                        "retrieved_product_ids contains duplicate ranked ids",
                        dataset=dataset,
                        case_id=case_id,
                        path=f"{path}/prediction/retrieved_product_ids",
                    )
                )
    for case_id, count in sorted(counts.items()):
        if count > 1:
            errors.append(
                _error(
                    ERROR_CODES["duplicate"],
                    f"prediction case_id occurs {count} times",
                    dataset=dataset,
                    case_id=case_id,
                )
            )
    return errors


def _join_holdout(
    dataset: str,
    gold_rows: list[dict[str, Any]],
    prediction_rows: list[dict[str, Any]],
) -> tuple[list[tuple[dict[str, Any], dict[str, Any]]], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    test_rows: list[dict[str, Any]] = []
    for row in gold_rows:
        group_id = row.get("group_id")
        if isinstance(group_id, str):
            try:
                expected_split = split_for_group(group_id)
            except ValueError:
                expected_split = None
            if row.get("split") != expected_split:
                errors.append(
                    _error(
                        ERROR_CODES["split_mismatch"],
                        "gold split does not match the canonical group split",
                        dataset=dataset,
                        case_id=row.get("case_id"),
                    )
                )
        if row.get("split") == "test":
            test_rows.append(row)

    gold_counts = Counter(
        row.get("case_id") for row in test_rows if isinstance(row.get("case_id"), str)
    )
    for case_id, count in sorted(gold_counts.items()):
        if count > 1:
            errors.append(
                _error(
                    ERROR_CODES["duplicate"],
                    f"gold case_id occurs {count} times",
                    dataset=dataset,
                    case_id=case_id,
                )
            )
    gold_by_id = {
        row["case_id"]: row
        for row in test_rows
        if isinstance(row.get("case_id"), str) and gold_counts[row["case_id"]] == 1
    }
    prediction_by_id = {
        row["case_id"]: row
        for row in prediction_rows
        if isinstance(row.get("case_id"), str)
    }
    for case_id in sorted(set(gold_by_id) - set(prediction_by_id)):
        errors.append(
            _error(
                ERROR_CODES["missing"],
                "holdout prediction is missing",
                dataset=dataset,
                case_id=case_id,
            )
        )
    for case_id in sorted(set(prediction_by_id) - set(gold_by_id)):
        errors.append(
            _error(
                ERROR_CODES["unexpected"],
                "prediction does not belong to the holdout",
                dataset=dataset,
                case_id=case_id,
            )
        )

    joined: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for case_id in sorted(set(gold_by_id) & set(prediction_by_id)):
        gold = gold_by_id[case_id]
        prediction = prediction_by_id[case_id]
        try:
            expected_fingerprint = case_fingerprint(gold)
        except ValueError as exc:
            errors.append(
                _error(
                    ERROR_CODES["fingerprint"],
                    f"gold case_fingerprint cannot be computed: {exc}",
                    dataset=dataset,
                    case_id=case_id,
                )
            )
            continue
        if gold.get("case_fingerprint") != expected_fingerprint:
            errors.append(
                _error(
                    ERROR_CODES["fingerprint"],
                    "gold case_fingerprint is invalid",
                    dataset=dataset,
                    case_id=case_id,
                )
            )
        if prediction.get("case_fingerprint") != expected_fingerprint:
            errors.append(
                _error(
                    ERROR_CODES["fingerprint"],
                    "prediction case_fingerprint does not match gold",
                    dataset=dataset,
                    case_id=case_id,
                )
            )
        else:
            joined.append((gold, prediction))
    return joined, errors


def _derived_rows(
    joined: Mapping[str, list[tuple[dict[str, Any], dict[str, Any]]]],
) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    rows: dict[str, list[dict[str, Any]]] = {dataset: [] for dataset in DATASETS}
    rows["strata"] = []
    calibration: list[dict[str, Any]] = []
    for dataset in DATASETS:
        for gold, prediction_record in joined[dataset]:
            prediction = prediction_record["prediction"]
            case_id = gold["case_id"]
            confidence = prediction_record["confidence"]
            invariant_errors = label_invariant_errors(
                dataset,
                gold.get("gold"),
                gold.get("input"),
            )
            if invariant_errors:
                errors.extend(
                    _error(
                        ERROR_CODES["gold_not_ready"],
                        message,
                        dataset=dataset,
                        case_id=case_id,
                        path="gold",
                    )
                    for message in invariant_errors
                )
                continue
            strata = gold["input"]["strata"]
            if dataset == "taxonomy":
                rows[dataset].append(
                    {"expected": gold["gold"], "predicted": prediction}
                )
                correct = exact_json_value(gold["gold"], prediction)
            elif dataset == "entity_resolution":
                rows[dataset].append(
                    {
                        "actual": gold["gold"]["product_relation"],
                        "predicted": prediction["product_relation"],
                        "actual_variant": gold["gold"]["variant_relation"],
                        "predicted_variant": prediction["variant_relation"],
                    }
                )
                correct = canonical_json(gold["gold"]) == canonical_json(prediction)
            elif dataset == "variant_resolution":
                expected = gold["gold"]["expected_variant"]
                predicted = prediction["expected_variant"]
                rows[dataset].append(
                    {"expected_variant": expected, "predicted_variant": predicted}
                )
                correct = exact_json_value(expected, predicted)
            elif dataset == "offer_attachment":
                rows[dataset].append(
                    {
                        "eligibility": gold["gold"]["eligibility"],
                        "expected_variant_id": gold["gold"]["expected_variant_id"],
                        "predicted_variant_id": prediction["expected_variant_id"],
                        "predicted_eligibility": prediction["eligibility"],
                    }
                )
                correct = canonical_json(gold["gold"]) == canonical_json(prediction)
            elif dataset == "offer_truth":
                rows[dataset].append(
                    {"expected": gold["gold"], "predicted": prediction}
                )
                correct = exact_json_value(gold["gold"], prediction)
            elif dataset == "retrieval":
                rows["strata"].append(dict(strata))
                actual_resolution = gold["gold"]["resolution"]
                predicted_resolution = prediction["resolution"]
                relevant = gold["gold"]["relevant_product_ids"]
                retrieved = prediction["retrieved_product_ids"]
                rows[dataset].append(
                    {
                        "scenario_type": strata["scenario_type"],
                        "actual_resolution": actual_resolution,
                        "predicted_resolution": predicted_resolution,
                        "relevant_product_ids": relevant,
                        "exact_product_ids": gold["gold"]["exact_product_ids"],
                        "retrieved_product_ids": retrieved,
                        "constraint_violating_product_ids": gold["gold"][
                            "constraint_violating_product_ids"
                        ],
                    }
                )
                violating = set(gold["gold"]["constraint_violating_product_ids"])
                if actual_resolution == "matched":
                    correct = (
                        predicted_resolution == "matched"
                        and set(relevant).issubset(set(retrieved[:50]))
                        and not (violating & set(retrieved[:10]))
                    )
                    if strata["scenario_type"] == "exact_product":
                        correct = (
                            correct
                            and bool(retrieved)
                            and retrieved[0]
                            in set(gold["gold"]["exact_product_ids"])
                        )
                else:
                    correct = (
                        predicted_resolution == actual_resolution and not retrieved
                    )
            elif dataset == "decision":
                claims = prediction["claims"]
                claim_names = [claim["claim"] for claim in claims]
                if len(claim_names) != len(set(claim_names)):
                    errors.append(
                        _error(
                            ERROR_CODES["prediction_invalid"],
                            "decision claims must have unique claim identifiers",
                            dataset=dataset,
                            case_id=case_id,
                            path="prediction/claims",
                        )
                    )
                    continue
                evidence_entries = gold["gold"]["claim_evidence"]
                gold_claim_names = [entry["claim"] for entry in evidence_entries]
                if len(gold_claim_names) != len(set(gold_claim_names)):
                    errors.append(
                        _error(
                            ERROR_CODES["gold_not_ready"],
                            "gold claim_evidence must have unique claim identifiers",
                            dataset=dataset,
                            case_id=case_id,
                            path="gold/claim_evidence",
                        )
                    )
                    continue
                gold_input = gold.get("input")
                input_evidence = (
                    gold_input.get("evidence")
                    if isinstance(gold_input, Mapping)
                    else None
                )
                if not isinstance(input_evidence, list):
                    errors.append(
                        _error(
                            ERROR_CODES["gold_not_ready"],
                            "decision input must inventory source evidence",
                            dataset=dataset,
                            case_id=case_id,
                            path="input/evidence",
                        )
                    )
                    continue
                available_evidence_refs = [
                    entry.get("evidence_ref")
                    for entry in input_evidence
                    if isinstance(entry, Mapping)
                ]
                if (
                    len(available_evidence_refs) != len(input_evidence)
                    or any(
                        not isinstance(reference, str)
                        for reference in available_evidence_refs
                    )
                    or len(available_evidence_refs) != len(set(available_evidence_refs))
                ):
                    errors.append(
                        _error(
                            ERROR_CODES["gold_not_ready"],
                            "decision input evidence_ref values must be unique strings",
                            dataset=dataset,
                            case_id=case_id,
                            path="input/evidence",
                        )
                    )
                    continue
                unresolvable_gold_refs = sorted(
                    {
                        evidence_ref
                        for entry in evidence_entries
                        for evidence_ref in entry["evidence_refs"]
                    }
                    - set(available_evidence_refs)
                )
                if unresolvable_gold_refs:
                    errors.append(
                        _error(
                            ERROR_CODES["gold_not_ready"],
                            "gold claim_evidence references evidence absent from input",
                            dataset=dataset,
                            case_id=case_id,
                            path="gold/claim_evidence",
                        )
                    )
                    continue
                allowed_evidence = {
                    entry["claim"]: set(entry["evidence_refs"])
                    for entry in evidence_entries
                }
                forbidden = set(gold["gold"]["forbidden_claims"])
                outcome_violation = int(
                    prediction["outcome"] not in gold["gold"]["acceptable_outcomes"]
                )
                forbidden_violations = len(set(claim_names) & forbidden)
                unsupported = sum(
                    claim["claim"] not in allowed_evidence
                    or not set(claim["evidence_refs"]).issubset(
                        allowed_evidence.get(claim["claim"], set())
                    )
                    for claim in claims
                )
                coverage_eligible = prediction["outcome"] != "abstain"
                correct = (
                    outcome_violation + forbidden_violations == 0
                    and unsupported == 0
                )
                rows[dataset].append(
                    {
                        "constraint_violations": outcome_violation
                        + forbidden_violations,
                        "unsupported_claims": unsupported,
                        "explanation_sourced": bool(claim_names) and unsupported == 0,
                        "coverage_eligible": coverage_eligible,
                        "outcome": prediction["outcome"],
                        "correct": correct,
                    }
                )
            else:  # pragma: no cover - roster fermé et testé
                raise ValueError(f"unsupported dataset {dataset!r}")
            calibration.append({"confidence": confidence, "correct": correct})
    rows["calibration"] = calibration
    return rows, errors


def _compute_metrics(
    rows: Mapping[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    taxonomy = taxonomy_metrics(rows["taxonomy"])
    entity = entity_resolution_metrics(rows["entity_resolution"])
    variant = variant_resolution_metrics(rows["variant_resolution"])
    attachment = attachment_metrics(rows["offer_attachment"])
    offer_truth = offer_truth_metrics(rows["offer_truth"])
    retrieval = retrieval_metrics(rows["retrieval"])
    decision = decision_safety_metrics(rows["decision"])
    calibration = calibration_metrics(rows["calibration"])
    strata = strata_metrics(rows["strata"])

    def lower(interval: Any) -> float | None:
        return interval[0] if isinstance(interval, list) and len(interval) == 2 else None

    def upper(interval: Any) -> float | None:
        return interval[1] if isinstance(interval, list) and len(interval) == 2 else None

    stratum_support = {
        **{
            f"scenario_{name}_cases": count
            for name, count in strata["scenario_counts"].items()
        },
        **{
            f"language_{name}_cases": count
            for name, count in strata["language_counts"].items()
        },
        **{
            f"vertical_{name}_cases": count
            for name, count in strata["vertical_counts"].items()
        },
    }

    return {
        "category_accuracy": taxonomy["category_accuracy"],
        "category_accuracy_ci95_lower": lower(taxonomy["category_accuracy_ci95"]),
        "category_accuracy_ci95_upper": upper(taxonomy["category_accuracy_ci95"]),
        "subcategory_accuracy": taxonomy["subcategory_accuracy"],
        "subcategory_accuracy_ci95_lower": lower(
            taxonomy["subcategory_accuracy_ci95"]
        ),
        "subcategory_accuracy_ci95_upper": upper(
            taxonomy["subcategory_accuracy_ci95"]
        ),
        "product_role_accuracy": taxonomy["product_role_accuracy"],
        "product_role_accuracy_ci95_lower": lower(
            taxonomy["product_role_accuracy_ci95"]
        ),
        "product_role_accuracy_ci95_upper": upper(
            taxonomy["product_role_accuracy_ci95"]
        ),
        "entity_match_accuracy": entity["entity_match_accuracy"],
        "entity_match_accuracy_ci95_lower": lower(
            entity["entity_match_accuracy_ci95"]
        ),
        "entity_match_accuracy_ci95_upper": upper(
            entity["entity_match_accuracy_ci95"]
        ),
        "false_merge_rate": entity["false_merge_rate"],
        "false_merge_rate_ci95_upper": upper(entity["false_merge_ci95"]),
        "false_split_rate": entity["false_split_rate"],
        "false_split_rate_ci95_upper": upper(entity["false_split_ci95"]),
        "entity_variant_relation_accuracy": entity["variant_relation_accuracy"],
        "entity_variant_relation_accuracy_ci95_lower": lower(
            entity["variant_relation_accuracy_ci95"]
        ),
        "variant_resolution_accuracy": variant["exact_match_accuracy"],
        "variant_resolution_accuracy_ci95_lower": lower(
            variant["exact_match_ci95"]
        ),
        "offer_attachment_accuracy": attachment["accuracy"],
        "offer_attachment_accuracy_ci95_lower": lower(attachment["accuracy_ci95"]),
        "offer_eligibility_accuracy": attachment["eligibility_accuracy"],
        "offer_eligibility_accuracy_ci95_lower": lower(
            attachment["eligibility_accuracy_ci95"]
        ),
        "false_eligible_offers": attachment["false_eligible_offers"],
        "price_accuracy": offer_truth["price_accuracy"],
        "price_accuracy_ci95_lower": lower(offer_truth["price_accuracy_ci95"]),
        "price_accuracy_ci95_upper": upper(offer_truth["price_accuracy_ci95"]),
        "stock_accuracy": offer_truth["stock_accuracy"],
        "stock_accuracy_ci95_lower": lower(offer_truth["stock_accuracy_ci95"]),
        "stock_accuracy_ci95_upper": upper(offer_truth["stock_accuracy_ci95"]),
        "shipping_accuracy": offer_truth["shipping_accuracy"],
        "shipping_accuracy_ci95_lower": lower(
            offer_truth["shipping_accuracy_ci95"]
        ),
        "shipping_accuracy_ci95_upper": upper(
            offer_truth["shipping_accuracy_ci95"]
        ),
        "affiliate_link_accuracy": offer_truth["affiliate_link_accuracy"],
        "affiliate_link_accuracy_ci95_lower": lower(
            offer_truth["affiliate_link_accuracy_ci95"]
        ),
        "affiliate_link_accuracy_ci95_upper": upper(
            offer_truth["affiliate_link_accuracy_ci95"]
        ),
        "retrieval_precision_at_1": retrieval["precision_at_1"],
        "retrieval_precision_at_3": retrieval["precision_at_3"],
        "retrieval_precision_at_3_ci95_lower": lower(
            retrieval["precision_at_3_ci95"]
        ),
        "retrieval_precision_at_3_ci95_upper": upper(
            retrieval["precision_at_3_ci95"]
        ),
        "retrieval_top_3_relevance": retrieval["top_3_relevance"],
        "retrieval_top_3_relevance_hits": retrieval["top_3_relevance_hits"],
        "retrieval_top_3_relevance_ci95_lower": lower(
            retrieval["top_3_relevance_ci95"]
        ),
        "retrieval_top_3_relevance_ci95_upper": upper(
            retrieval["top_3_relevance_ci95"]
        ),
        "exact_product_match_accuracy": retrieval[
            "exact_product_match_accuracy"
        ],
        "exact_product_match_accuracy_ci95_lower": lower(
            retrieval["exact_product_match_accuracy_ci95"]
        ),
        "exact_product_match_accuracy_ci95_upper": upper(
            retrieval["exact_product_match_accuracy_ci95"]
        ),
        "absurd_result_rate": retrieval["absurd_result_rate"],
        "absurd_result_rate_ci95_lower": lower(
            retrieval["absurd_result_rate_ci95"]
        ),
        "absurd_result_rate_ci95_upper": upper(
            retrieval["absurd_result_rate_ci95"]
        ),
        "retrieval_precision_at_5": retrieval["precision_at_5"],
        "retrieval_recall_at_10": retrieval["recall_at_10"],
        "retrieval_recall_at_50": retrieval["recall_at_50"],
        "retrieval_recall_at_50_ci95_lower": lower(
            retrieval["recall_at_50_ci95"]
        ),
        "retrieval_recall_at_50_ci95_upper": upper(
            retrieval["recall_at_50_ci95"]
        ),
        "retrieval_ndcg_at_10": retrieval["ndcg_at_10"],
        "retrieval_ndcg_at_10_ci95_lower": lower(retrieval["ndcg_at_10_ci95"]),
        "retrieval_ndcg_at_10_ci95_upper": upper(retrieval["ndcg_at_10_ci95"]),
        "retrieval_resolution_accuracy": retrieval["resolution_accuracy"],
        "retrieval_resolution_accuracy_ci95_lower": lower(
            retrieval["resolution_accuracy_ci95"]
        ),
        "retrieval_resolution_accuracy_ci95_upper": upper(
            retrieval["resolution_accuracy_ci95"]
        ),
        "retrieval_no_match_accuracy": retrieval["no_match_accuracy"],
        "retrieval_no_match_accuracy_ci95_lower": lower(
            retrieval["no_match_accuracy_ci95"]
        ),
        "retrieval_no_match_accuracy_ci95_upper": upper(
            retrieval["no_match_accuracy_ci95"]
        ),
        "retrieval_no_match_false_positive_queries": retrieval[
            "no_match_false_positive_queries"
        ],
        "retrieval_ambiguous_accuracy": retrieval["ambiguous_accuracy"],
        "retrieval_ambiguous_accuracy_ci95_lower": lower(
            retrieval["ambiguous_accuracy_ci95"]
        ),
        "retrieval_ambiguous_accuracy_ci95_upper": upper(
            retrieval["ambiguous_accuracy_ci95"]
        ),
        "retrieval_constraint_violations_at_10": retrieval[
            "constraint_violations_at_10"
        ],
        "constraint_violations": decision["constraint_violations"],
        "unsupported_claims": decision["unsupported_claims"],
        "calibration_ece": calibration["ece"],
        "calibration_ece_ci95_lower": lower(calibration["ece_ci95"]),
        "calibration_ece_ci95_upper": upper(calibration["ece_ci95"]),
        "calibration_brier_score": calibration["brier_score"],
        "decision_correct_answer": decision["correct_answer"],
        "decision_correct_abstention": decision["correct_abstention"],
        "decision_wrong_answer": decision["wrong_answer"],
        "decision_wrong_abstention": decision["wrong_abstention"],
        "decision_outcome_matrix_total": decision["outcome_matrix_total"],
        "sourced_explanation_coverage": decision[
            "sourced_explanation_coverage"
        ],
        "sourced_explanation_coverage_ci95_lower": lower(
            decision["sourced_explanation_coverage_ci95"]
        ),
        "taxonomy_cases": taxonomy["evaluated"],
        "entity_different_pairs": entity["different_pairs"],
        "entity_same_pairs": entity["same_pairs"],
        "entity_variant_pairs": entity["variant_pairs"],
        "variant_cases": variant["evaluated"],
        "offer_eligible_cases": attachment["evaluated"],
        "offer_all_cases": attachment["offers"],
        "offer_noneligible_cases": attachment["noneligible_offers"],
        "offer_truth_cases": offer_truth["evaluated"],
        "retrieval_queries": retrieval["total_queries"],
        "retrieval_answerable_queries": retrieval["answerable_queries"],
        "retrieval_exact_product_queries": retrieval["exact_product_queries"],
        "retrieval_no_match_queries": retrieval["no_match_queries"],
        "retrieval_ambiguous_queries": retrieval["ambiguous_queries"],
        "decision_cases": decision["decisions"],
        "decision_non_abstain": decision["coverage_eligible_decisions"],
        "calibration_cases": calibration["evaluated"],
        **stratum_support,
        "details": {
            "taxonomy": taxonomy,
            "entity_resolution": entity,
            "variant_resolution": variant,
            "offer_attachment": attachment,
            "offer_truth": offer_truth,
            "retrieval": retrieval,
            "decision": decision,
            "calibration": calibration,
            "strata": strata,
        },
    }


def _evaluate_measurement_support(
    manifest: Mapping[str, Any],
    metrics: Mapping[str, Any],
) -> list[dict[str, Any]]:
    configured = manifest.get("measurement_support")
    errors: list[dict[str, Any]] = []
    if not isinstance(configured, Mapping):
        return [
            _error(
                ERROR_CODES["not_measurable"],
                "measurement_support configuration is missing",
                path="measurement_support",
            )
        ]
    for support_name, metric_name in _MEASUREMENT_SUPPORT.items():
        required = configured.get(support_name)
        actual = metrics.get(metric_name)
        if (
            isinstance(required, bool)
            or not isinstance(required, int)
            or required <= 0
        ):
            errors.append(
                _error(
                    ERROR_CODES["not_measurable"],
                    f"measurement support {support_name} must be a positive integer",
                    path=f"measurement_support/{support_name}",
                )
            )
            continue
        if isinstance(actual, bool) or not isinstance(actual, int) or actual < required:
            errors.append(
                _error(
                    ERROR_CODES["not_measurable"],
                    f"{metric_name} support {actual!r} is below required {required}",
                    path=f"metrics/{metric_name}",
                )
            )
    return errors


def _evaluate_gates(
    manifest: Mapping[str, Any],
    metrics: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    gates: list[dict[str, Any]] = []
    configured = manifest.get("gates")
    if not isinstance(configured, Mapping):
        configured = {}
    for gate_name, (metric_name, operator) in _GATE_METRICS.items():
        if gate_name not in configured:
            errors.append(
                _error(
                    ERROR_CODES["gate_missing"],
                    f"required gate {gate_name} is missing",
                    path=f"gates/{gate_name}",
                )
            )
            continue
        value = metrics.get(metric_name)
        threshold = configured[gate_name]
        if value is None:
            errors.append(
                _error(
                    ERROR_CODES["not_measurable"],
                    f"metric {metric_name} has no measurable denominator",
                    path=f"metrics/{metric_name}",
                )
            )
            passed: bool | None = None
        elif (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            or (metric_name in _RATIO_METRICS and not 0.0 <= float(value) <= 1.0)
            or (
                metric_name not in _RATIO_METRICS
                and (not isinstance(value, int) or value < 0)
            )
        ):
            errors.append(
                _error(
                    ERROR_CODES["metric_range"],
                    f"metric {metric_name} is outside its valid range",
                    path=f"metrics/{metric_name}",
                )
            )
            passed = None
        else:
            if operator == "max":
                passed = value <= threshold
            elif operator == "lt":
                passed = value < threshold
            else:
                passed = value >= threshold
        gates.append(
            {
                "gate": gate_name,
                "metric": metric_name,
                "operator": operator,
                "threshold": threshold,
                "value": value,
                "passed": passed,
            }
        )
    return gates, errors


def score_holdout(
    manifest: Mapping[str, Any],
    gold_by_dataset: Mapping[str, list[dict[str, Any]]],
    predictions_by_dataset: Mapping[str, list[dict[str, Any]]],
    *,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Joint et mesure un holdout déjà chargé, sans jamais publier un run partiel."""
    if run_id is None:
        discovered_run_ids = {
            row.get("run_id")
            for rows in predictions_by_dataset.values()
            for row in rows
            if isinstance(row, dict) and isinstance(row.get("run_id"), str)
        }
        run_id = next(iter(discovered_run_ids)) if len(discovered_run_ids) == 1 else None
    report = _base_report(run_id)
    errors: list[dict[str, Any]] = []
    if set(gold_by_dataset) != set(DATASETS) or set(predictions_by_dataset) != set(
        DATASETS
    ):
        errors.append(
            _error(
                ERROR_CODES["run_invalid"],
                "gold and prediction rosters must contain exactly seven datasets",
            )
        )
        report["errors"] = _sort_errors(errors)
        return report
    try:
        require_identifier(run_id, "run_id")
    except ValueError as exc:
        report["errors"] = [
            _error(ERROR_CODES["run_invalid"], str(exc), path="run_id")
        ]
        return report
    if run_id is None:
        report["errors"] = [
            _error(
                ERROR_CODES["run_invalid"],
                "predictions must commit to exactly one non-empty run_id",
            )
        ]
        return report

    try:
        prediction_validator = _validator(
            Path(__file__).resolve().parents[2]
            / "quality"
            / "schemas"
            / "prediction.schema.json"
        )
    except (ValueError, SchemaError) as exc:
        report["errors"] = [
            _error(ERROR_CODES["prediction_invalid"], str(exc))
        ]
        return report

    joined: dict[str, list[tuple[dict[str, Any], dict[str, Any]]]] = {}
    holdout: dict[str, dict[str, int]] = {}
    for dataset in DATASETS:
        prediction_rows = predictions_by_dataset[dataset]
        preflight_errors = _prediction_preflight(dataset, prediction_rows, run_id)
        errors.extend(preflight_errors)
        for index, row in enumerate(prediction_rows, 1):
            specialised = {
                error["code"]
                for error in preflight_errors
                if error.get("path", "").startswith(f"record:{index}")
            }
            if specialised & {
                ERROR_CODES["confidence"],
                ERROR_CODES["ranking_duplicate"],
            }:
                continue
            for message in _schema_messages(prediction_validator, row):
                errors.append(
                    _error(
                        ERROR_CODES["prediction_invalid"],
                        message,
                        dataset=dataset,
                        case_id=(
                            row.get("case_id")
                            if isinstance(row.get("case_id"), str)
                            else None
                        ),
                        path=f"record:{index}",
                    )
                )
        pairs, join_errors = _join_holdout(
            dataset, gold_by_dataset[dataset], prediction_rows
        )
        errors.extend(join_errors)
        joined[dataset] = pairs
        holdout[dataset] = {
            "gold_cases": sum(
                row.get("split") == "test" for row in gold_by_dataset[dataset]
            ),
            "prediction_cases": len(prediction_rows),
            "joined_cases": len(pairs),
        }
    report["holdout"] = holdout
    if errors:
        report["errors"] = _sort_errors(errors)
        return report

    try:
        report["holdout_fingerprint"] = _holdout_content_fingerprint(joined)
    except ValueError as exc:
        report["errors"] = [
            _error(
                ERROR_CODES["fingerprint"],
                f"holdout fingerprint cannot be computed: {exc}",
                path="holdout",
            )
        ]
        return report

    try:
        derived, derived_errors = _derived_rows(joined)
    except (KeyError, TypeError, ValueError) as exc:
        report["errors"] = [
            _error(
                ERROR_CODES["prediction_invalid"],
                f"prediction derivation rejected: {exc}",
            )
        ]
        return report
    if derived_errors:
        report["errors"] = _sort_errors(derived_errors)
        return report
    try:
        metrics = _compute_metrics(derived)
    except (TypeError, ValueError) as exc:
        report["errors"] = [
            _error(
                ERROR_CODES["prediction_invalid"],
                f"metric input rejected: {exc}",
            )
        ]
        return report
    support_errors = _evaluate_measurement_support(manifest, metrics)
    gates, gate_errors = _evaluate_gates(manifest, metrics)
    report["metrics"] = metrics
    report["gates"] = gates
    report["errors"] = _sort_errors([*support_errors, *gate_errors])
    if support_errors or gate_errors:
        return report
    report["measurable"] = True
    report["status"] = "pass" if all(gate["passed"] for gate in gates) else "fail"
    return report


def build_scorecard(
    manifest_path: str | Path,
    run_manifest_path: str | Path,
) -> dict[str, Any]:
    """Valide les artefacts, charge le holdout et exécute tous les gates."""
    manifest_file = Path(manifest_path).resolve()
    run_file = Path(run_manifest_path).resolve()
    report = _base_report()
    try:
        raw_manifest, manifest_sha256 = _snapshot_json(
            manifest_file, "gold manifest"
        )
    except ValueError:
        raw_manifest = None
        manifest_sha256 = None
    report["gold_manifest_sha256"] = manifest_sha256
    if isinstance(raw_manifest, dict):
        configured_gates = raw_manifest.get("gates")
        missing_gates = sorted(
            set(_GATE_METRICS)
            - (set(configured_gates) if isinstance(configured_gates, dict) else set())
        )
        if missing_gates:
            report["errors"] = [
                _error(
                    ERROR_CODES["gate_missing"],
                    f"required gate {gate_name} is missing",
                    path=f"gates/{gate_name}",
                )
                for gate_name in missing_gates
            ]
            return report
    readiness = build_readiness_report(manifest_file)
    report["manifest_fingerprint"] = readiness.get("manifest_fingerprint")
    if readiness.get("status") == "invalid_manifest":
        report["errors"] = [
            _error(
                ERROR_CODES["manifest_invalid"],
                "quality manifest is invalid: "
                + "; ".join(readiness.get("manifest_errors", [])),
                path=str(manifest_file),
            )
        ]
        return report
    if not readiness.get("ready"):
        errors = [
            _error(
                ERROR_CODES["gold_not_ready"],
                "gold datasets do not satisfy readiness",
                path=str(manifest_file),
            )
        ]
        for dataset, dataset_report in readiness.get("datasets", {}).items():
            if any(
                "differs from canonical" in message
                for message in dataset_report.get("errors", [])
            ):
                errors.append(
                    _error(
                        ERROR_CODES["split_mismatch"],
                        "gold contains a non-canonical holdout split",
                        dataset=dataset,
                    )
                )
        report["errors"] = _sort_errors(errors)
        return report

    if not isinstance(raw_manifest, dict):
        report["errors"] = [
            _error(
                ERROR_CODES["manifest_invalid"],
                "quality manifest root must be an object",
                path=str(manifest_file),
            )
        ]
        return report
    try:
        initial_manifest_fingerprint = manifest_fingerprint(raw_manifest)
    except ValueError as exc:
        report["errors"] = [
            _error(ERROR_CODES["manifest_invalid"], str(exc), path=str(manifest_file))
        ]
        return report
    if readiness.get("manifest_fingerprint") != initial_manifest_fingerprint:
        report["errors"] = [
            _error(
                ERROR_CODES["gold_digest"],
                "gold manifest changed during readiness validation",
                path=str(manifest_file),
            )
        ]
        return report

    quality_root = manifest_file.parent
    try:
        manifest = raw_manifest
        run_manifest, _ = _snapshot_json(run_file, "run manifest")
        run_validator = _validator(quality_root / "schemas" / "run-manifest.schema.json")
    except (ValueError, SchemaError) as exc:
        report["errors"] = [
            _error(
                ERROR_CODES["run_invalid"],
                str(exc),
                path=str(run_file),
            )
        ]
        return report
    if not isinstance(run_manifest, dict):
        report["errors"] = [
            _error(ERROR_CODES["run_invalid"], "run manifest root must be an object")
        ]
        return report
    run_errors = _schema_messages(run_validator, run_manifest)
    for field in ("run_id", "system_version"):
        try:
            require_identifier(run_manifest.get(field), field)
        except ValueError as exc:
            run_errors.append(str(exc))
    if run_errors:
        report["errors"] = [
            _error(
                ERROR_CODES["run_invalid"],
                message,
                path=str(run_file),
            )
            for message in run_errors
        ]
        return report
    run_id = run_manifest["run_id"]
    report["run_id"] = run_id
    if run_manifest["gold_manifest_sha256"] != manifest_sha256:
        report["errors"] = [
            _error(
                ERROR_CODES["gold_digest"],
                "gold manifest digest does not match the run commitment",
                path=str(manifest_file),
            )
        ]
        return report

    try:
        prediction_validator = _validator(
            quality_root / "schemas" / "prediction.schema.json"
        )
    except (ValueError, SchemaError) as exc:
        report["errors"] = [
            _error(ERROR_CODES["prediction_invalid"], str(exc))
        ]
        return report

    prediction_rows: dict[str, list[dict[str, Any]]] = {}
    errors: list[dict[str, Any]] = []
    run_binding_message = "prediction dataset or run_id does not match its run manifest"
    for dataset in DATASETS:
        config = run_manifest["datasets"][dataset]
        try:
            path = _safe_relative_path(run_file.parent, config["path"], dataset)
        except ValueError as exc:
            errors.append(
                _error(ERROR_CODES["run_invalid"], str(exc), dataset=dataset)
            )
            continue
        if not path.is_file():
            errors.append(
                _error(
                    ERROR_CODES["run_invalid"],
                    "prediction file is missing or its digest does not match",
                    dataset=dataset,
                    path=str(path),
                )
            )
            continue
        try:
            rows, prediction_sha256 = _snapshot_jsonl(path, "prediction file")
        except ValueError as exc:
            errors.append(
                _error(
                    ERROR_CODES["prediction_invalid"],
                    str(exc),
                    dataset=dataset,
                    path=str(path),
                )
            )
            continue
        if prediction_sha256 != config["sha256"]:
            errors.append(
                _error(
                    ERROR_CODES["run_invalid"],
                    "prediction file digest does not match",
                    dataset=dataset,
                    path=str(path),
                )
            )
            continue
        prediction_rows[dataset] = rows
        preflight_errors = _prediction_preflight(dataset, rows, run_id)
        errors.extend(preflight_errors)
        for index, row in enumerate(rows, 1):
            specialised = {
                error["code"]
                for error in preflight_errors
                if error.get("path", "").startswith(f"record:{index}")
            }
            if specialised & {
                ERROR_CODES["confidence"],
                ERROR_CODES["ranking_duplicate"],
            }:
                # Les codes spécialisés sont autoritaires et évitent de
                # doubler la même cause par un QL006 générique issu de oneOf.
                continue
            for message in _schema_messages(prediction_validator, row):
                errors.append(
                    _error(
                        ERROR_CODES["prediction_invalid"],
                        message,
                        dataset=dataset,
                        case_id=(
                            row.get("case_id")
                            if isinstance(row.get("case_id"), str)
                            else None
                        ),
                        path=f"{path}:{index}",
                    )
                )
    binding_errors = [
        error
        for error in errors
        if error.get("code") == ERROR_CODES["prediction_invalid"]
        and error.get("message") == run_binding_message
    ]
    expected_run_id: str | None = None
    identity_error: str | None = None
    if not errors or len(binding_errors) == len(errors):
        try:
            expected_run_id = quality_run_id(
                system_version=run_manifest["system_version"],
                evaluator_version=run_manifest["evaluator_version"],
                gold_manifest_sha256=run_manifest["gold_manifest_sha256"],
                outputs=prediction_rows,
                adapters=run_manifest["adapters"],
            )
        except ValueError as exc:
            identity_error = f"run identity cannot be recomputed: {exc}"
    if errors:
        if len(binding_errors) == len(errors) and (
            identity_error is not None or expected_run_id != run_id
        ):
            report["errors"] = [
                _error(
                    ERROR_CODES["run_invalid"],
                    identity_error
                    or "run_id does not match predictions, adapters, and version commitments",
                    path=str(run_file),
                )
            ]
            return report
        report["errors"] = _sort_errors(errors)
        return report

    gold_rows: dict[str, list[dict[str, Any]]] = {}
    for dataset in DATASETS:
        gold_path = quality_root / manifest["datasets"][dataset]["path"]
        try:
            rows, gold_sha256 = _snapshot_jsonl(gold_path, "gold dataset")
        except ValueError as exc:
            errors.append(
                _error(
                    ERROR_CODES["gold_not_ready"],
                    str(exc),
                    dataset=dataset,
                    path=str(gold_path),
                )
            )
            continue
        if gold_sha256 != readiness["datasets"][dataset]["dataset_sha256"]:
            errors.append(
                _error(
                    ERROR_CODES["gold_digest"],
                    "gold dataset changed after readiness validation",
                    dataset=dataset,
                    path=str(gold_path),
                )
            )
            continue
        gold_rows[dataset] = rows
    if errors:
        report["errors"] = _sort_errors(errors)
        return report

    scored = score_holdout(
        manifest,
        gold_rows,
        prediction_rows,
        run_id=run_id,
    )
    if not scored["errors"] and (
        identity_error is not None or expected_run_id != run_id
    ):
        report["errors"] = [
            _error(
                ERROR_CODES["run_invalid"],
                identity_error
                or "run_id does not match predictions, adapters, and version commitments",
                path=str(run_file),
            )
        ]
        return report
    scored["gold_manifest_sha256"] = manifest_sha256
    scored["manifest_fingerprint"] = readiness["manifest_fingerprint"]
    scored["system_version"] = run_manifest["system_version"]
    scored["adapters"] = run_manifest["adapters"]
    return scored


def main() -> int:
    parser = argparse.ArgumentParser(description="Score le holdout FILON Quality Lab")
    parser.add_argument("--manifest", default="../quality/manifest.json")
    parser.add_argument("--run", required=True, help="manifeste d'un run de prédictions")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.output:
        try:
            ensure_output_is_distinct(
                args.output,
                scorecard_input_paths(args.manifest, args.run),
            )
        except ValueError as exc:
            parser.error(str(exc))
    report = build_scorecard(args.manifest, args.run)
    payload = canonical_json(report)
    print(payload)
    if args.output:
        try:
            atomic_write_text(args.output, payload + "\n")
        except (OSError, ValueError) as exc:
            parser.error(f"unable to write output: {exc}")
    if report["status"] == "pass":
        return 0
    if report["status"] == "fail":
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
