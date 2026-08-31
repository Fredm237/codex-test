"""Contrat et invariants de la taxonomie d'erreurs produit v1."""

from __future__ import annotations

import ast
import json
import re
from dataclasses import replace
from datetime import datetime
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

from app.core.error_taxonomy import (
    PRODUCT_ERROR_CODES,
    ProductErrorCode,
    decode_product_error_code,
)
from app.observations.awin import ProjectedIssue, _issue_key, project_awin_row


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "filon-backend"
TAXONOMY = ROOT / "contracts" / "taxonomies" / "v1"
ERROR_LITERAL = re.compile(r"E\d{3}_[A-Z0-9_]+")
EXPECTED_V1_WIRE_VALUES = (
    "E001_WRONG_CATEGORY",
    "E002_WRONG_PRODUCT_ROLE",
    "E003_FALSE_PRODUCT_MERGE",
    "E004_FALSE_PRODUCT_SPLIT",
    "E005_WRONG_VARIANT",
    "E006_IRRELEVANT_RETRIEVAL",
    "E007_HARD_CONSTRAINT_VIOLATION",
    "E008_WRONG_PRICE",
    "E009_STALE_PRICE",
    "E010_WRONG_STOCK",
    "E011_WRONG_SHIPPING",
    "E012_UNSUPPORTED_CLAIM",
    "E013_WRONG_VERDICT",
    "E014_OVERCONFIDENT_DECISION",
    "E015_DUPLICATE_PRODUCT",
    "E016_SCHEMA_INVALID",
    "E017_INVALID_IDENTIFIER",
    "E018_CURRENCY_MISMATCH",
)


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_registry_enum_and_json_schema_are_exactly_aligned():
    registry = _json(TAXONOMY / "product-error-codes.json")
    schema = _json(TAXONOMY / "product-error-code.schema.json")
    manifest = _json(TAXONOMY / "manifest.json")

    Draft202012Validator.check_schema(schema)
    registry_values = [entry["wire_value"] for entry in registry]
    assert PRODUCT_ERROR_CODES == EXPECTED_V1_WIRE_VALUES
    assert registry_values == list(PRODUCT_ERROR_CODES)
    assert schema["enum"] == registry_values
    assert len(registry_values) == len(set(registry_values)) == 18
    assert manifest["taxonomy_version"] == "1.0.0"
    assert manifest["scope"] == "internal_product_quality"
    assert {entry["domain"] for entry in registry} <= set(
        manifest["vocabularies"]["domain"]
    )
    assert {entry["origin"] for entry in registry} == set(
        manifest["vocabularies"]["origin"]
    )
    assert next(entry for entry in registry if entry["id"] == "E007")[
        "domain"
    ] == "constraint"
    for group in ("artifacts", "schemas"):
        for relative in manifest[group].values():
            assert (TAXONOMY / relative).is_file(), relative

    validator = Draft202012Validator(schema)
    for value in registry_values:
        validator.validate(value)
    with pytest.raises(ValidationError):
        validator.validate("E999_UNKNOWN")


def test_ids_are_contiguous_and_names_cannot_drift_from_wire_values():
    registry = _json(TAXONOMY / "product-error-codes.json")

    for number, (entry, enum_member) in enumerate(
        zip(registry, ProductErrorCode, strict=True),
        start=1,
    ):
        expected_id = f"E{number:03d}"
        assert entry["id"] == expected_id
        assert entry["name"] == enum_member.name
        assert entry["wire_value"] == f"{expected_id}_{entry['name']}"
        assert enum_member.number == number
        assert entry["origin"] == (
            "mandate" if number <= 15 else "filon_ingestion_extension"
        )
        assert str(enum_member) == entry["wire_value"]
        assert json.loads(json.dumps(enum_member)) == entry["wire_value"]

    with pytest.raises(ValueError):
        ProductErrorCode("E999_UNKNOWN")


def test_cross_version_reader_preserves_and_flags_unknown_values():
    known = decode_product_error_code(ProductErrorCode.WRONG_PRICE.value)
    future = decode_product_error_code("E999_FUTURE_CODE")

    assert known.is_known is True
    assert known.known is ProductErrorCode.WRONG_PRICE
    assert known.raw_value == ProductErrorCode.WRONG_PRICE.value
    assert future.is_known is False
    assert future.known is None
    assert future.raw_value == "E999_FUTURE_CODE"


def test_projected_issue_rejects_an_unregistered_producer_value():
    with pytest.raises(TypeError, match="ProductErrorCode"):
        ProjectedIssue(
            error_code="E999_INVENTED",  # type: ignore[arg-type]
            stage="test",
            field=None,
            rejected_value=None,
            reason="test",
        )


def test_product_taxonomy_stays_outside_the_frozen_public_v1_manifest():
    path = ROOT / "contracts" / "v1" / "manifest.json"
    manifest = _json(path)

    assert manifest["contract_version"] == "1.0.0"
    assert manifest["status"] == "frozen"
    assert manifest["compatibility"]["additive_changes"] == (
        "allowed_with_examples_and_consumer_tests"
    )
    assert "taxonomy" not in json.dumps(manifest).lower()


def test_awin_projection_emits_enum_and_keeps_the_existing_issue_key():
    projection = project_awin_row(
        {
            "aw_product_id": "x",
            "product_name": "X",
            "search_price": "-1",
            "currency": "EUR",
            "in_stock": "yes",
        },
        feed_id="42",
        merchant_id=7,
        observed_at=datetime(2026, 8, 28, 18, 30, 0),
    )

    assert len(projection.issues) == 1
    issue = projection.issues[0]
    assert issue.error_code is ProductErrorCode.WRONG_PRICE
    assert projection.replay_key == (
        "bdd2019c08474cc5e9d22bb2039382ae62144053f9bfbc375523173f036069f5"
    )
    assert _issue_key(projection, issue) == (
        "468b570d8c049945781ef93a659da995f8be4e55764dd2f09fd3417d6a784ed9"
    )
    assert _issue_key(
        projection,
        replace(issue, reason="nouveau libellé", details={"context": "new"}),
    ) == _issue_key(projection, issue)


def test_awin_currency_failure_keeps_both_direct_and_downstream_scopes():
    invalid = project_awin_row(
        {
            "aw_product_id": "x",
            "product_name": "X",
            "search_price": "12.50",
            "currency": "EURO",
            "in_stock": "yes",
        },
        feed_id="42",
        merchant_id=7,
        observed_at=datetime(2026, 8, 28, 18, 30, 0),
    )
    missing = project_awin_row(
        {
            "aw_product_id": "x",
            "product_name": "X",
            "search_price": "12.50",
            "in_stock": "yes",
        },
        feed_id="42",
        merchant_id=7,
        observed_at=datetime(2026, 8, 28, 18, 30, 0),
    )

    assert [
        (
            issue.error_code,
            issue.stage,
            issue.field,
            issue.rejected_value,
            issue.details,
        )
        for issue in invalid.issues
    ] == [
        (
            ProductErrorCode.CURRENCY_MISMATCH,
            "currency_validation",
            "currency",
            "EURO",
            None,
        ),
        (
            ProductErrorCode.CURRENCY_MISMATCH,
            "price_validation",
            "search_price",
            "12.50",
            {"parsed_amount": "12.50"},
        ),
    ]
    assert [
        (issue.error_code, issue.stage, issue.field, issue.details)
        for issue in missing.issues
    ] == [
        (
            ProductErrorCode.CURRENCY_MISMATCH,
            "price_validation",
            "search_price",
            {"parsed_amount": "12.50"},
        )
    ]


def test_application_contains_no_ad_hoc_product_error_literals():
    canonical = BACKEND / "app" / "core" / "error_taxonomy.py"
    violations: list[str] = []

    for path in sorted((BACKEND / "app").rglob("*.py")):
        if path == canonical:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and ERROR_LITERAL.fullmatch(node.value)
            ):
                violations.append(
                    f"{path.relative_to(BACKEND)}:{node.lineno}:{node.value}"
                )

    assert violations == []


def test_operational_health_codes_stay_outside_product_taxonomy():
    path = BACKEND / "app" / "api" / "routes" / "health.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    operational_codes: set[str] = set()

    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        for key, value in zip(node.keys, node.values, strict=True):
            if (
                isinstance(key, ast.Constant)
                and key.value == "error_code"
                and isinstance(value, ast.Constant)
                and isinstance(value.value, str)
            ):
                operational_codes.add(value.value)

    assert {
        "database_probe_failed",
        "redis_probe_failed",
        "schema_revision_invalid",
    } <= operational_codes
    assert all(ERROR_LITERAL.fullmatch(code) is None for code in operational_codes)
