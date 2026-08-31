"""Readiness fail-closed des datasets indépendants du FILON Quality Lab."""

from __future__ import annotations

import hashlib
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

from app.services import taxonomy

from .integrity import (
    DATASETS,
    LAB_VERSION,
    PACK_VERSION,
    RECORD_VERSION,
    SPLIT_POLICY_VERSION,
    SPLIT_SALT,
    canonical_json,
    case_fingerprint,
    ensure_no_reserved_fields,
    label_invariant_errors,
    manifest_fingerprint,
    normalize_label,
    read_json,
    require_identifier,
    schema_value_fingerprint,
    sha256_value,
    split_for_group,
    strict_load_jsonl,
    strict_loads,
)


def _schema_messages(validator: Draft202012Validator, value: Any) -> list[str]:
    messages: list[str] = []
    for violation in sorted(
        validator.iter_errors(value),
        key=lambda error: ([str(part) for part in error.absolute_path], error.message),
    ):
        location = "/".join(str(part) for part in violation.absolute_path)
        messages.append(f"{location or '<root>'}: {violation.message}")
    return messages


def _invalid_manifest_report(
    manifest_file: Path,
    errors: list[str],
    manifest: Mapping[str, Any] | None = None,
    *,
    manifest_display: str | None = None,
) -> dict[str, Any]:
    report_errors = list(errors)
    fingerprint: str | None = None
    if manifest is not None:
        try:
            fingerprint = manifest_fingerprint(manifest)
        except (TypeError, ValueError, RecursionError) as exc:
            report_errors.append(f"manifest fingerprint unavailable: {exc}")
    return {
        "lab_version": manifest.get("lab_version") if manifest else None,
        "integrity_valid": False,
        "ready": False,
        "status": "invalid_manifest",
        "status_authority": "computed_readiness_is_authoritative",
        "manifest_declared_status": manifest.get("status") if manifest else None,
        "manifest_status_warning": None,
        "manifest_path": manifest_display or str(manifest_file),
        "manifest_fingerprint": fingerprint,
        "manifest_errors": sorted(set(report_errors)),
        "datasets": {},
        "duplicate_case_ids": [],
        "duplicate_input_fingerprints": [],
        "leakage_groups": [],
        "measurement_support": {"ready": False, "requirements": {}},
        "bootstrap": {
            "exists": False,
            "eligible_for_launch_gate": False,
            "cases": 0,
        },
        "gates": {},
    }


def _load_manifest(manifest_file: Path) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    try:
        value = read_json(manifest_file)
    except ValueError as exc:
        return None, [str(exc)]
    if not isinstance(value, dict):
        return None, ["manifest root must be an object"]

    schema_file = manifest_file.parent / "schemas" / "manifest.schema.json"
    try:
        manifest_schema = read_json(schema_file)
        if not isinstance(manifest_schema, dict):
            raise ValueError("manifest schema root must be an object")
        Draft202012Validator.check_schema(manifest_schema)
        errors.extend(
            f"manifest schema violation at {message}"
            for message in _schema_messages(
                Draft202012Validator(manifest_schema), value
            )
        )
    except (ValueError, SchemaError) as exc:
        errors.append(f"invalid manifest schema: {exc}")

    datasets = value.get("datasets")
    if not isinstance(datasets, dict) or set(datasets) != set(DATASETS):
        errors.append("manifest dataset roster must contain exactly the seven v0.5 datasets")
    if value.get("lab_version") != LAB_VERSION:
        errors.append(f"lab_version must be {LAB_VERSION}")
    if value.get("record_version") != RECORD_VERSION:
        errors.append(f"record_version must be {RECORD_VERSION}")
    if value.get("pack_version") != PACK_VERSION:
        errors.append(f"pack_version must be {PACK_VERSION}")
    split_policy = value.get("split_policy")
    if not isinstance(split_policy, dict):
        errors.append("split_policy must be an object")
    else:
        if split_policy.get("version") != SPLIT_POLICY_VERSION:
            errors.append(f"split_policy.version must be {SPLIT_POLICY_VERSION}")
        if split_policy.get("salt") != SPLIT_SALT:
            errors.append(f"split_policy.salt must be {SPLIT_SALT}")
    return value, sorted(set(errors))


def _bootstrap_report(path: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    if not path.is_file():
        return {"exists": False, "eligible_for_launch_gate": False, "cases": 0}
    try:
        payload = read_json(path)
    except ValueError as exc:
        return {
            "exists": True,
            "eligible_for_launch_gate": False,
            "cases": 0,
            "error": str(exc),
        }
    if not isinstance(payload, dict) or not isinstance(payload.get("cases"), list):
        return {
            "exists": True,
            "eligible_for_launch_gate": False,
            "cases": 0,
            "error": "bootstrap must contain a cases array",
        }
    assertions = passed = 0
    validation_errors: list[str] = []
    case_ids: set[str] = set()
    for index, case in enumerate(payload["cases"], 1):
        prefix = f"case {index}"
        if not isinstance(case, Mapping):
            validation_errors.append(f"{prefix}: object expected")
            continue
        expected = case.get("expected_current")
        if not isinstance(expected, Mapping):
            validation_errors.append(f"{prefix}: expected_current must be an object")
            continue
        try:
            case_id = require_identifier(case.get("id"), f"{prefix} id")
        except ValueError as exc:
            validation_errors.append(str(exc))
            continue
        if case_id in case_ids:
            validation_errors.append(f"{prefix}: duplicate bootstrap id {case_id!r}")
            continue
        case_ids.add(case_id)
        expected_fields = set(expected)
        unknown_expected_fields = sorted(
            expected_fields - {"category", "offer_kind"}
        )
        if unknown_expected_fields:
            validation_errors.append(
                f"{prefix}: unknown expected_current fields: "
                + ", ".join(unknown_expected_fields)
            )
            continue
        if not expected_fields:
            validation_errors.append(
                f"{prefix}: expected_current must contain category or offer_kind"
            )
            continue
        invalid_expected_fields: list[str] = []
        for field in sorted(expected_fields):
            try:
                require_identifier(
                    expected.get(field),
                    f"{prefix} expected_current.{field}",
                )
            except ValueError:
                invalid_expected_fields.append(field)
        if invalid_expected_fields:
            validation_errors.append(
                f"{prefix}: expected_current values must be non-empty strings: "
                + ", ".join(invalid_expected_fields)
            )
            continue
        invalid_fields = [
            field
            for field in (
                "merchant_category",
                "name",
                "brand",
                "merchant_name",
            )
            if case.get(field) is not None and not isinstance(case.get(field), str)
        ]
        if invalid_fields:
            validation_errors.append(
                f"{prefix}: text fields must be strings or null: "
                + ", ".join(invalid_fields)
            )
            continue
        args = (
            case.get("merchant_category"),
            case.get("name"),
            case.get("brand"),
            case.get("merchant_name"),
        )
        try:
            if "category" in expected:
                assertions += 1
                passed += int(taxonomy.classify(*args) == expected["category"])
            if "offer_kind" in expected:
                assertions += 1
                passed += int(
                    taxonomy.classify_offer_kind(*args) == expected["offer_kind"]
                )
        except (AttributeError, TypeError, ValueError) as exc:
            validation_errors.append(
                f"{prefix}: bootstrap classification failed: {type(exc).__name__}"
            )
    report = {
        "exists": True,
        "cases": len(payload["cases"]),
        "assertions": assertions,
        "passed": passed,
        "agreement": passed / assertions if assertions else None,
        "independent": bool(config.get("independent")),
        "eligible_for_launch_gate": bool(config.get("eligible_for_launch_gate"))
        and not validation_errors,
        "warning": config.get("reason"),
    }
    if not payload["cases"]:
        validation_errors.append("bootstrap must contain at least one case")
    if validation_errors:
        report["error"] = "invalid bootstrap cases"
        report["errors"] = validation_errors
    return report


def _business_label_errors(
    dataset: str,
    label: Any,
    input_value: Any,
) -> list[str]:
    return label_invariant_errors(dataset, label, input_value)


def _annotation_integrity_errors(
    dataset: str,
    row: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []
    annotations = row.get("annotations")
    if not isinstance(annotations, list) or len(annotations) != 2:
        return ["exactly two initial annotations are required"]
    if not all(isinstance(annotation, dict) for annotation in annotations):
        return ["annotations must be objects"]
    annotator_ids: list[str] = []
    for annotation in annotations:
        try:
            annotator_ids.append(
                require_identifier(annotation.get("annotator_id"), "annotator_id")
            )
        except ValueError as exc:
            errors.append(str(exc))
    distinct_annotator_ids = set(annotator_ids)
    if len(distinct_annotator_ids) != 2:
        errors.append("two distinct initial annotators are required")
    if len(annotator_ids) == 2 and annotator_ids != sorted(annotator_ids):
        errors.append("initial annotations are not canonically ordered")
    source_packs = row.get("source_pack_fingerprints")
    if isinstance(source_packs, list) and source_packs != sorted(source_packs):
        errors.append("source_pack_fingerprints are not canonically ordered")
    labels = [annotation.get("label") for annotation in annotations]
    if not all(isinstance(label, dict) for label in labels):
        return errors + ["structured initial labels are required"]
    input_value = row.get("input")
    normalized_labels: list[dict[str, Any]] = []
    normalization_failed = False
    for label in labels:
        try:
            normalized_label = normalize_label(dataset, label)
        except ValueError as exc:
            errors.append(f"initial label cannot be normalized: {exc}")
            normalized_label = label
            normalization_failed = True
        else:
            if canonical_json(label) != canonical_json(normalized_label):
                errors.append("initial label is not semantically canonical")
        normalized_labels.append(normalized_label)
        errors.extend(_business_label_errors(dataset, label, input_value))

    gold = row.get("gold")
    try:
        normalized_gold = normalize_label(dataset, gold)
    except ValueError as exc:
        errors.append(f"gold cannot be normalized: {exc}")
        normalized_gold = gold
        normalization_failed = True
    else:
        if canonical_json(gold) != canonical_json(normalized_gold):
            errors.append("gold is not semantically canonical")
    errors.extend(_business_label_errors(dataset, gold, input_value))
    adjudication = row.get("adjudication")
    normalized_adjudication_label: Any = None
    if isinstance(adjudication, dict):
        try:
            adjudicator_id = require_identifier(
                adjudication.get("adjudicator_id"), "adjudicator_id"
            )
        except ValueError as exc:
            errors.append(str(exc))
            adjudicator_id = ""
        if adjudicator_id and adjudicator_id in distinct_annotator_ids:
            errors.append("adjudicator must be distinct from both initial annotators")
        errors.extend(
            _business_label_errors(
                dataset,
                adjudication.get("label"),
                input_value,
            )
        )
        try:
            normalized_adjudication_label = normalize_label(
                dataset,
                adjudication.get("label"),
            )
        except ValueError as exc:
            errors.append(f"adjudication label cannot be normalized: {exc}")
            normalized_adjudication_label = adjudication.get("label")
            normalization_failed = True
        else:
            if canonical_json(adjudication.get("label")) != canonical_json(
                normalized_adjudication_label
            ):
                errors.append("adjudication label is not semantically canonical")
    if normalization_failed:
        return errors
    labels_agree = canonical_json(normalized_labels[0]) == canonical_json(
        normalized_labels[1]
    )
    if labels_agree:
        if adjudication is not None:
            errors.append("adjudication is forbidden when initial labels agree")
        if canonical_json(normalized_labels[0]) != canonical_json(normalized_gold):
            errors.append("agreed human label differs from final gold")
        return errors

    if not isinstance(adjudication, dict):
        errors.append("a third-human adjudication is required when labels disagree")
        return errors
    if canonical_json(normalized_adjudication_label) != canonical_json(
        normalized_gold
    ):
        errors.append("adjudicated human label differs from final gold")
    return errors


def _safe_dataset_path(root: Path, relative: Any, label: str) -> Path:
    if not isinstance(relative, str):
        raise ValueError(f"{label} path must be a string")
    candidate = (root / relative).resolve()
    resolved_root = root.resolve()
    if candidate != resolved_root and resolved_root not in candidate.parents:
        raise ValueError(f"{label} path escapes the quality root")
    return candidate


def _count_test_measurement_support(
    dataset: str,
    row: Mapping[str, Any],
    actuals: dict[str, int],
) -> None:
    """Compte uniquement un gold test déjà intégralement validé."""

    actuals["calibration_cases_min"] += 1
    input_value = row.get("input")
    strata = input_value.get("strata") if isinstance(input_value, Mapping) else None
    if dataset == "retrieval" and isinstance(strata, Mapping):
        for dimension, value in (
            ("scenario", strata.get("scenario_type")),
            ("language", strata.get("language")),
            ("vertical", strata.get("vertical")),
        ):
            key = f"{dimension}_{value}_cases_min"
            if key in actuals:
                actuals[key] += 1
    gold = row.get("gold")
    if not isinstance(gold, Mapping):
        return
    if dataset == "taxonomy":
        actuals["taxonomy_cases_min"] += 1
    elif dataset == "entity_resolution":
        product_relation = gold.get("product_relation")
        variant_relation = gold.get("variant_relation")
        if product_relation == "different":
            actuals["entity_different_pairs_min"] += 1
        elif product_relation == "same":
            actuals["entity_same_pairs_min"] += 1
        if variant_relation in {"same", "different"}:
            actuals["entity_variant_pairs_min"] += 1
    elif dataset == "variant_resolution":
        actuals["variant_cases_min"] += 1
    elif dataset == "offer_attachment":
        actuals["offer_all_cases_min"] += 1
        if gold.get("eligibility") == "eligible":
            actuals["offer_eligible_cases_min"] += 1
        elif gold.get("eligibility") in {"quarantine", "reject"}:
            actuals["offer_noneligible_cases_min"] += 1
    elif dataset == "offer_truth":
        actuals["offer_truth_cases_min"] += 1
    elif dataset == "retrieval":
        actuals["retrieval_queries_min"] += 1
        resolution = gold.get("resolution")
        if resolution == "matched":
            actuals["retrieval_answerable_queries_min"] += 1
            if (
                isinstance(strata, Mapping)
                and strata.get("scenario_type") == "exact_product"
            ):
                actuals["retrieval_exact_product_queries_min"] += 1
        elif resolution == "no_match":
            actuals["retrieval_no_match_queries_min"] += 1
        elif resolution == "ambiguous":
            actuals["retrieval_ambiguous_queries_min"] += 1
    elif dataset == "decision":
        actuals["decision_cases_min"] += 1
        outcomes = gold.get("acceptable_outcomes")
        if isinstance(outcomes, list) and any(
            outcome in {"recommend", "wait"} for outcome in outcomes
        ):
            actuals["decision_non_abstain_min"] += 1


def build_readiness_report(manifest_path: str | Path) -> dict[str, Any]:
    manifest_reference = Path(manifest_path)
    manifest_file = manifest_reference.resolve()
    manifest_display = str(manifest_reference)
    manifest, manifest_errors = _load_manifest(manifest_file)
    if manifest is None:
        return _invalid_manifest_report(
            manifest_file,
            manifest_errors,
            manifest_display=manifest_display,
        )
    if manifest_errors:
        return _invalid_manifest_report(
            manifest_file,
            manifest_errors,
            manifest,
            manifest_display=manifest_display,
        )

    root = manifest_file.parent
    dataset_reports: dict[str, Any] = {}
    global_case_ids: Counter[str] = Counter()
    global_input_fingerprints: Counter[str] = Counter()
    global_groups: dict[str, set[str]] = defaultdict(set)
    configured_support = manifest["measurement_support"]
    support_actuals = {name: 0 for name in configured_support}

    for name in DATASETS:
        config = manifest["datasets"][name]
        errors: list[str] = []
        rows: list[dict[str, Any]] = []
        validator: Draft202012Validator | None = None
        try:
            path = _safe_dataset_path(root, config["path"], f"{name} dataset")
            schema_path = _safe_dataset_path(root, config["schema"], f"{name} schema")
        except ValueError as exc:
            dataset_reports[name] = {
                "integrity_valid": False,
                "ready": False,
                "exists": False,
                "schema_exists": False,
                "cases": 0,
                "minimum_cases": config["minimum_cases"],
                "minimum_test_cases": config["minimum_test_cases"],
                "split_counts": {},
                "annotation_failures": 0,
                "leakage_group_count": 0,
                "leakage_groups": [],
                "errors": [str(exc)],
            }
            continue

        dataset_exists = False
        dataset_sha256: str | None = None
        try:
            dataset_snapshot = path.read_bytes()
        except FileNotFoundError:
            pass
        except OSError:
            errors.append(f"{path}: unable to read JSONL file")
        else:
            dataset_exists = True
            dataset_sha256 = f"sha256:{hashlib.sha256(dataset_snapshot).hexdigest()}"
            try:
                rows = strict_load_jsonl(dataset_snapshot, source=str(path))
            except ValueError as exc:
                errors.append(str(exc))

        schema_exists = False
        current_schema_fingerprint: str | None = None
        try:
            schema_snapshot = schema_path.read_bytes()
        except FileNotFoundError:
            pass
        except OSError:
            errors.append(f"{schema_path}: unable to read annotation schema")
        else:
            schema_exists = True
            try:
                schema = strict_loads(schema_snapshot, source=str(schema_path))
                if not isinstance(schema, dict):
                    raise ValueError("schema root must be an object")
                Draft202012Validator.check_schema(schema)
                validator = Draft202012Validator(schema)
                current_schema_fingerprint = schema_value_fingerprint(name, schema)
                if config["schema_fingerprint"] != current_schema_fingerprint:
                    errors.append("manifest schema_fingerprint does not match schema")
            except (ValueError, SchemaError) as exc:
                errors.append(f"invalid annotation schema: {exc}")

        split_counts: Counter[str] = Counter()
        groups: dict[str, set[str]] = defaultdict(set)
        annotation_failures = 0
        dataset_preconditions_valid = validator is not None and not errors
        for index, row in enumerate(rows, 1):
            prefix = f"record {index}"
            error_count_before = len(errors)
            if validator is not None:
                errors.extend(
                    f"{prefix}: schema violation at {message}"
                    for message in _schema_messages(validator, row)
                )
            try:
                case_id = require_identifier(row.get("case_id"), "case_id")
            except ValueError as exc:
                errors.append(f"{prefix}: {exc}")
                case_id = ""
            try:
                group_id = require_identifier(row.get("group_id"), "group_id")
            except ValueError as exc:
                errors.append(f"{prefix}: {exc}")
                group_id = ""
            split = row.get("split")
            if case_id:
                global_case_ids[case_id] += 1
            try:
                blind_input_fingerprint = sha256_value(
                    f"filon.quality.blind-input.v{RECORD_VERSION.removesuffix('.0')}",
                    {"dataset": name, "input": row.get("input")},
                )
            except ValueError:
                pass
            else:
                global_input_fingerprints[blind_input_fingerprint] += 1
            if group_id and isinstance(split, str):
                groups[group_id].add(split)
                global_groups[group_id].add(split)
            if split in {"train", "dev", "test"}:
                split_counts[split] += 1
            if group_id:
                try:
                    canonical_split = split_for_group(group_id)
                except ValueError as exc:
                    errors.append(f"{prefix}: {exc}")
                else:
                    if split != canonical_split:
                        errors.append(
                            f"{prefix}: split {split!r} differs from canonical {canonical_split!r}"
                        )
            if row.get("record_version") != RECORD_VERSION:
                errors.append(f"{prefix}: incompatible record_version")
            if row.get("split_policy_version") != SPLIT_POLICY_VERSION:
                errors.append(f"{prefix}: incompatible split_policy_version")
            if current_schema_fingerprint is not None and row.get(
                "schema_fingerprint"
            ) != current_schema_fingerprint:
                errors.append(f"{prefix}: incompatible schema_fingerprint")
            try:
                ensure_no_reserved_fields(row.get("input"), path="input")
            except ValueError as exc:
                errors.append(f"{prefix}: {exc}")
            try:
                expected_case_fingerprint = case_fingerprint(row)
            except ValueError as exc:
                errors.append(f"{prefix}: cannot compute case_fingerprint: {exc}")
            else:
                if row.get("case_fingerprint") != expected_case_fingerprint:
                    errors.append(f"{prefix}: case_fingerprint mismatch")
            integrity_errors = _annotation_integrity_errors(name, row)
            if integrity_errors:
                annotation_failures += 1
                errors.extend(
                    f"{prefix}: annotation integrity: {error}"
                    for error in integrity_errors
                )
            if (
                dataset_preconditions_valid
                and len(errors) == error_count_before
                and split == "test"
            ):
                _count_test_measurement_support(name, row, support_actuals)

        leakage = sorted(group for group, splits in groups.items() if len(splits) > 1)
        minimum = config["minimum_cases"]
        minimum_test = config["minimum_test_cases"]
        ready = (
            dataset_exists
            and schema_exists
            and len(rows) >= minimum
            and split_counts["test"] >= minimum_test
            and not errors
            and not leakage
            and annotation_failures == 0
        )
        integrity_valid = (
            schema_exists
            and validator is not None
            and not errors
            and not leakage
            and annotation_failures == 0
        )
        dataset_reports[name] = {
            "integrity_valid": integrity_valid,
            "ready": ready,
            "exists": dataset_exists,
            "schema_exists": schema_exists,
            "schema_fingerprint": current_schema_fingerprint,
            "dataset_sha256": dataset_sha256,
            "cases": len(rows),
            "minimum_cases": minimum,
            "minimum_test_cases": minimum_test,
            "split_counts": dict(sorted(split_counts.items())),
            "annotation_failures": annotation_failures,
            "leakage_group_count": len(leakage),
            "leakage_groups": leakage[:20],
            "errors": sorted(set(errors))[:100],
        }

    duplicate_case_ids = sorted(
        case_id for case_id, count in global_case_ids.items() if count > 1
    )
    duplicate_input_fingerprints = sorted(
        fingerprint
        for fingerprint, count in global_input_fingerprints.items()
        if count > 1
    )
    leakage_groups = sorted(
        group_id for group_id, splits in global_groups.items() if len(splits) > 1
    )
    support_requirements = {
        name: {
            "required": required,
            "actual": support_actuals[name],
            "ready": support_actuals[name] >= required,
        }
        for name, required in configured_support.items()
    }
    support_ready = all(
        requirement["ready"] for requirement in support_requirements.values()
    )
    bootstrap_config = manifest["bootstrap"]
    bootstrap = _bootstrap_report(root / bootstrap_config["path"], bootstrap_config)
    content_integrity_valid = (
        all(dataset_reports[name]["integrity_valid"] for name in DATASETS)
        and not duplicate_case_ids
        and not duplicate_input_fingerprints
        and not leakage_groups
        and "error" not in bootstrap
    )
    readiness_requirements_met = (
        all(dataset_reports[name]["ready"] for name in DATASETS) and support_ready
    )
    declared_status = manifest.get("status")
    regressed_from_declared_ready = (
        declared_status == "ready"
        and not (content_integrity_valid and readiness_requirements_met)
    )
    integrity_valid = content_integrity_valid and not regressed_from_declared_ready
    ready = integrity_valid and readiness_requirements_met
    computed_status = "ready" if ready else "not_ready"
    expected_declared_status = "ready" if ready else "bootstrap_not_ready"
    manifest_status_warning = (
        None
        if declared_status == expected_declared_status
        else (
            f"manifest declares {declared_status!r} while computed readiness is "
            f"{computed_status!r}; computed status is authoritative"
        )
    )
    return {
        "lab_version": manifest["lab_version"],
        "integrity_valid": integrity_valid,
        "ready": ready,
        "status": computed_status,
        "status_authority": "computed_readiness_is_authoritative",
        "manifest_declared_status": declared_status,
        "manifest_status_warning": manifest_status_warning,
        "manifest_path": manifest_display,
        "manifest_fingerprint": manifest_fingerprint(manifest),
        "manifest_errors": [],
        "datasets": dataset_reports,
        "duplicate_case_ids": duplicate_case_ids,
        "duplicate_input_fingerprints": duplicate_input_fingerprints,
        "leakage_groups": leakage_groups,
        "measurement_support": {
            "ready": support_ready,
            "requirements": support_requirements,
        },
        "bootstrap": bootstrap,
        "gates": manifest["gates"],
    }
