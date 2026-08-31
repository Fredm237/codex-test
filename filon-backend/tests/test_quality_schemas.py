from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
QUALITY = ROOT / "quality"
SHA_A = "sha256:" + "a" * 64
SHA_B = "sha256:" + "b" * 64


def _schema(name: str) -> dict[str, Any]:
    return json.loads(
        (QUALITY / "schemas" / name).read_text(encoding="utf-8")
    )


def _errors(schema: dict[str, Any], value: Any) -> list[Any]:
    return list(Draft202012Validator(schema).iter_errors(value))


def _record(dataset: str, input_value: dict[str, Any], label: dict[str, Any]) -> dict[str, Any]:
    input_value = deepcopy(input_value)
    input_value.setdefault(
        "strata",
        {
            "scenario_type": "exact_product",
            "language": "fr",
            "vertical": "smartphones",
        },
    )
    label = deepcopy(label)
    if dataset == "retrieval":
        is_exact_match = (
            input_value["strata"]["scenario_type"] == "exact_product"
            and label.get("resolution") == "matched"
        )
        relevant = label.get("relevant_product_ids")
        label.setdefault(
            "exact_product_ids",
            [relevant[0]]
            if is_exact_match and isinstance(relevant, list) and relevant
            else [],
        )
    return {
        "record_version": "0.5.0",
        "dataset": dataset,
        "case_id": f"{dataset}-case-1",
        "group_id": f"{dataset}-group-1",
        "split": "test",
        "split_policy_version": "sha256-prefix32-mod100-70-15-15-v1",
        "input": input_value,
        "gold": deepcopy(label),
        "annotations": [
            {
                "annotator_id": "human-a",
                "label": deepcopy(label),
                "confidence": "certain",
            },
            {
                "annotator_id": "human-b",
                "label": deepcopy(label),
                "confidence": "certain",
            },
        ],
        "source_pack_fingerprints": [SHA_A, SHA_B],
        "schema_fingerprint": SHA_A,
        "case_fingerprint": SHA_B,
    }


def _prediction(dataset: str, prediction: dict[str, Any]) -> dict[str, Any]:
    return {
        "record_version": "0.5.0",
        "dataset": dataset,
        "case_id": f"{dataset}-case-1",
        "case_fingerprint": SHA_A,
        "run_id": "run-1",
        "confidence": 0.9,
        "prediction": prediction,
    }


def _decision_input() -> dict[str, Any]:
    return {
        "request": {
            "query": "ordinateur portable sous 500 €",
            "locale": "fr",
            "reference_time": "2026-08-29T10:00:00Z",
            "offers": [
                {
                    "candidate_id": "item-1",
                    "offer_id": 1,
                    "catalog_product_id": 101,
                    "name": "Ordinateur portable étudiant",
                    "brand": "Test",
                    "filon_category": "Informatique",
                    "filon_subcategory": "Ordinateurs portables",
                    "offer_kind": "physical_product",
                    "price": 450.0,
                    "currency": "EUR",
                    "availability": "in_stock",
                    "merchant_id": 7,
                    "merchant_name": "Marchand test",
                    "merchant_region": "BE",
                    "observed_at": "2026-08-29T09:00:00Z",
                    "evidence_refs": ["catalog:item-1"],
                }
            ],
        },
        "candidate_ids": ["item-1"],
        "evidence": [
            {
                "evidence_ref": "catalog:item-1",
                "source_ref": "catalog-snapshot-1",
            }
        ],
    }


def test_quality_contract_schemas_are_valid_draft_2020_12() -> None:
    for name in (
        "decision.schema.json",
        "entity-resolution.schema.json",
        "taxonomy.schema.json",
        "retrieval.schema.json",
        "offer-attachment.schema.json",
        "offer-truth.schema.json",
        "variant-resolution.schema.json",
        "prediction.schema.json",
        "manifest.schema.json",
        "run-manifest.schema.json",
    ):
        Draft202012Validator.check_schema(_schema(name))


@pytest.mark.parametrize(
    ("schema_name", "definition"),
    [
        ("decision.schema.json", "nonblank_id"),
        ("entity-resolution.schema.json", "nonblank_id"),
        ("taxonomy.schema.json", "nonblank_id"),
        ("offer-attachment.schema.json", "nonblank_id"),
        ("offer-truth.schema.json", "nonblank_id"),
        ("retrieval.schema.json", "nonblank_id"),
        ("variant-resolution.schema.json", "nonblank_id"),
        ("manifest.schema.json", "nonblank_string"),
        ("prediction.schema.json", "nonblank_string"),
        ("run-manifest.schema.json", "nonblank_string"),
    ],
)
def test_nonblank_contracts_use_absolute_string_boundaries(
    schema_name: str,
    definition: str,
) -> None:
    contract = _schema(schema_name)["$defs"][definition]
    validator = Draft202012Validator(contract)

    assert list(validator.iter_errors("identifiant")) == []
    assert list(validator.iter_errors("ligne\ninterne")) == []
    for invalid in (
        "",
        " ",
        "\nidentifiant",
        "\ridentifiant",
        "\u2028identifiant",
        "identifiant\n",
        "identifiant\r",
        "identifiant\u2028",
    ):
        assert list(validator.iter_errors(invalid)), (schema_name, invalid)


@pytest.mark.parametrize(
    "schema_name",
    [
        "decision.schema.json",
        "entity-resolution.schema.json",
        "taxonomy.schema.json",
        "offer-attachment.schema.json",
        "offer-truth.schema.json",
        "retrieval.schema.json",
        "variant-resolution.schema.json",
        "manifest.schema.json",
        "prediction.schema.json",
        "run-manifest.schema.json",
    ],
)
def test_sha256_contracts_use_absolute_string_boundaries(schema_name: str) -> None:
    contract = _schema(schema_name)["$defs"]["sha256"]
    validator = Draft202012Validator(contract)

    assert list(validator.iter_errors(SHA_A)) == []
    for suffix in ("\n", "\r", "\u2028"):
        assert list(validator.iter_errors(SHA_A + suffix)), (
            schema_name,
            repr(suffix),
        )


def test_manifest_requires_measurement_support_and_accepts_both_statuses() -> None:
    schema = _schema("manifest.schema.json")
    manifest = json.loads((QUALITY / "manifest.json").read_text(encoding="utf-8"))

    assert _errors(schema, manifest) == []
    ready_manifest = deepcopy(manifest)
    ready_manifest["status"] = "ready"
    assert _errors(schema, ready_manifest) == []

    missing_support = deepcopy(manifest)
    del missing_support["measurement_support"]
    assert _errors(schema, missing_support)

    invalid_status = deepcopy(manifest)
    invalid_status["status"] = "unknown"
    assert _errors(schema, invalid_status)

    assert manifest["measurement_support"] == {
        "taxonomy_cases_min": 500,
        "entity_different_pairs_min": 800,
        "entity_same_pairs_min": 200,
        "entity_variant_pairs_min": 200,
        "variant_cases_min": 200,
        "offer_eligible_cases_min": 200,
        "offer_all_cases_min": 500,
        "offer_noneligible_cases_min": 200,
        "offer_truth_cases_min": 500,
        "retrieval_queries_min": 1300,
        "retrieval_answerable_queries_min": 475,
        "retrieval_exact_product_queries_min": 300,
        "retrieval_no_match_queries_min": 600,
        "retrieval_ambiguous_queries_min": 225,
        "decision_cases_min": 500,
        "decision_non_abstain_min": 381,
        "calibration_cases_min": 1000,
        "scenario_exact_product_cases_min": 25,
        "scenario_generic_product_cases_min": 25,
        "scenario_use_case_cases_min": 25,
        "scenario_constraint_heavy_cases_min": 25,
        "scenario_accessory_cases_min": 25,
        "scenario_replacement_part_cases_min": 25,
        "scenario_variant_sensitive_cases_min": 25,
        "scenario_multi_product_cases_min": 25,
        "scenario_ambiguous_cases_min": 25,
        "scenario_no_match_cases_min": 25,
        "language_fr_cases_min": 100,
        "language_nl_cases_min": 100,
        "language_en_cases_min": 100,
        "vertical_smartphones_cases_min": 50,
        "vertical_laptops_cases_min": 50,
        "vertical_tv_cases_min": 50,
        "vertical_headphones_audio_cases_min": 50,
        "vertical_appliances_cases_min": 50,
    }
    assert {
        dataset: config["minimum_test_cases"]
        for dataset, config in manifest["datasets"].items()
    } == {
        "taxonomy": 500,
        "entity_resolution": 1000,
        "variant_resolution": 200,
        "offer_attachment": 500,
        "offer_truth": 500,
        "retrieval": 1300,
        "decision": 500,
    }


def test_decision_gold_requires_source_backed_claims() -> None:
    schema = _schema("decision.schema.json")
    label = {
        "acceptable_outcomes": ["recommend"],
        "forbidden_claims": [],
        "claim_evidence": [
            {"claim": "Disponible en noir", "evidence_refs": ["catalog:item-1"]}
        ],
    }
    record = _record(
        "decision",
        _decision_input(),
        label,
    )
    assert _errors(schema, record) == []

    for invalid_label in (
        {"acceptable_outcomes": ["recommend"], "forbidden_claims": []},
        {
            **label,
            "claim_evidence": [{"claim": "Disponible", "evidence_refs": []}],
        },
        {
            **label,
            "claim_evidence": [
                {
                    "claim": "Disponible",
                    "evidence_refs": ["catalog:item-1"],
                    "self_attested": True,
                }
            ],
        },
    ):
        invalid = deepcopy(record)
        invalid["gold"] = deepcopy(invalid_label)
        invalid["annotations"][0]["label"] = deepcopy(invalid_label)
        invalid["annotations"][1]["label"] = deepcopy(invalid_label)
        assert _errors(schema, invalid)


def test_decision_input_requires_closed_source_evidence() -> None:
    schema = _schema("decision.schema.json")
    label = {
        "acceptable_outcomes": ["abstain"],
        "forbidden_claims": [],
        "claim_evidence": [],
    }
    input_value = _decision_input()
    record = _record("decision", input_value, label)
    assert _errors(schema, record) == []

    missing = deepcopy(record)
    del missing["input"]["evidence"]
    assert _errors(schema, missing)

    extra = deepcopy(record)
    extra["input"]["evidence"][0]["self_attested"] = True
    assert _errors(schema, extra)

    for field in ("evidence_ref", "source_ref"):
        blank = deepcopy(record)
        blank["input"]["evidence"][0][field] = " "
        assert _errors(schema, blank)


@pytest.mark.parametrize(
    ("acceptable_outcomes", "claim_evidence", "valid"),
    [
        (["recommend"], [], False),
        (["wait"], [], False),
        (["recommend", "abstain"], [], False),
        (["wait", "abstain"], [], False),
        (["abstain"], [], True),
        (
            ["recommend"],
            [{"claim": "Disponible", "evidence_refs": ["catalog:item-1"]}],
            True,
        ),
        (
            ["wait"],
            [{"claim": "Prix inconnu", "evidence_refs": ["catalog:item-1"]}],
            True,
        ),
    ],
)
def test_decision_gold_non_abstain_outcomes_require_evidence(
    acceptable_outcomes: list[str],
    claim_evidence: list[dict[str, Any]],
    valid: bool,
) -> None:
    schema = _schema("decision.schema.json")
    label = {
        "acceptable_outcomes": acceptable_outcomes,
        "forbidden_claims": [],
        "claim_evidence": claim_evidence,
    }
    record = _record(
        "decision",
        _decision_input(),
        label,
    )
    assert (_errors(schema, record) == []) is valid


def test_decision_request_and_offer_contracts_are_closed() -> None:
    schema = _schema("decision.schema.json")
    label = {
        "acceptable_outcomes": ["abstain"],
        "forbidden_claims": [],
        "claim_evidence": [],
    }
    record = _record("decision", _decision_input(), label)
    assert _errors(schema, record) == []

    missing_reference = deepcopy(record)
    del missing_reference["input"]["request"]["reference_time"]
    assert _errors(schema, missing_reference)

    naive_reference = deepcopy(record)
    naive_reference["input"]["request"]["reference_time"] = "2026-08-29T10:00:00"
    assert _errors(schema, naive_reference)

    extra_request_field = deepcopy(record)
    extra_request_field["input"]["request"]["intent"] = "buy"
    assert _errors(schema, extra_request_field)

    extra_offer_field = deepcopy(record)
    extra_offer_field["input"]["request"]["offers"][0]["engine_score"] = 0.99
    assert _errors(schema, extra_offer_field)

    invalid_offer_kind = deepcopy(record)
    invalid_offer_kind["input"]["request"]["offers"][0]["offer_kind"] = "ad"
    assert _errors(schema, invalid_offer_kind)

    too_many = deepcopy(record)
    template = too_many["input"]["request"]["offers"][0]
    too_many["input"]["request"]["offers"] = [
        {
            **template,
            "candidate_id": f"item-{index}",
            "offer_id": index,
        }
        for index in range(1, 52)
    ]
    too_many["input"]["candidate_ids"] = [
        f"item-{index}" for index in range(1, 52)
    ]
    assert _errors(schema, too_many)


@pytest.mark.parametrize(
    ("product_relation", "variant_relation", "valid"),
    [
        ("different", "not_applicable", True),
        ("different", "same", False),
        ("same", "same", True),
        ("same", "different", True),
        ("same", "ambiguous", True),
        ("same", "not_applicable", False),
        ("ambiguous", "ambiguous", True),
        ("ambiguous", "same", False),
        ("ambiguous", "different", False),
        ("ambiguous", "not_applicable", False),
    ],
)
def test_entity_gold_relations_are_semantically_consistent(
    product_relation: str,
    variant_relation: str,
    valid: bool,
) -> None:
    schema = _schema("entity-resolution.schema.json")
    label = {
        "product_relation": product_relation,
        "variant_relation": variant_relation,
    }
    record = _record(
        "entity_resolution",
        {
            "left": {"source_ref": "left-1", "name": "Produit"},
            "right": {"source_ref": "right-1", "name": "Produit"},
        },
        label,
    )
    assert (_errors(schema, record) == []) is valid


@pytest.mark.parametrize(
    ("resolution", "variant_key", "valid"),
    [
        ("resolved", "variant-1", True),
        ("resolved", None, False),
        ("resolved", " ", False),
        ("ambiguous", None, True),
        ("ambiguous", "variant-1", False),
        ("insufficient_evidence", None, True),
        ("insufficient_evidence", "variant-1", False),
    ],
)
def test_variant_gold_key_follows_resolution(
    resolution: str,
    variant_key: str | None,
    valid: bool,
) -> None:
    schema = _schema("variant-resolution.schema.json")
    label = {
        "expected_variant": {
            "variant_key": variant_key,
            "attributes": {},
            "resolution": resolution,
        }
    }
    record = _record(
        "variant_resolution",
        {"observation": {"name": "Produit"}},
        label,
    )
    assert (_errors(schema, record) == []) is valid


@pytest.mark.parametrize(
    ("product_relation", "variant_relation", "valid"),
    [
        ("different", "not_applicable", True),
        ("different", "same", False),
        ("same", "same", True),
        ("same", "different", True),
        ("same", "ambiguous", True),
        ("same", "not_applicable", False),
        ("ambiguous", "ambiguous", True),
        ("ambiguous", "same", False),
        ("ambiguous", "different", False),
        ("ambiguous", "not_applicable", False),
    ],
)
def test_entity_prediction_relations_are_semantically_consistent(
    product_relation: str,
    variant_relation: str,
    valid: bool,
) -> None:
    schema = _schema("prediction.schema.json")
    prediction = _prediction(
        "entity_resolution",
        {
            "product_relation": product_relation,
            "variant_relation": variant_relation,
        },
    )
    assert (_errors(schema, prediction) == []) is valid


@pytest.mark.parametrize(
    ("resolution", "variant_key", "valid"),
    [
        ("resolved", "variant-1", True),
        ("resolved", None, False),
        ("resolved", " ", False),
        ("ambiguous", None, True),
        ("ambiguous", "variant-1", False),
        ("insufficient_evidence", None, True),
        ("insufficient_evidence", "variant-1", False),
    ],
)
def test_variant_prediction_key_follows_resolution(
    resolution: str,
    variant_key: str | None,
    valid: bool,
) -> None:
    schema = _schema("prediction.schema.json")
    prediction = _prediction(
        "variant_resolution",
        {
            "expected_variant": {
                "variant_key": variant_key,
                "attributes": {},
                "resolution": resolution,
            }
        },
    )
    assert (_errors(schema, prediction) == []) is valid


def test_decision_prediction_rejects_self_attested_supported_claims() -> None:
    schema = _schema("prediction.schema.json")
    valid = _prediction(
        "decision",
        {
            "outcome": "recommend",
            "claims": [
                {"claim": "Disponible en noir", "evidence_refs": ["catalog:item-1"]}
            ],
        },
    )
    assert _errors(schema, valid) == []

    legacy = deepcopy(valid)
    legacy["prediction"] = {
        "outcome": "recommend",
        "claims": ["Disponible en noir"],
        "supported_claims": ["Disponible en noir"],
    }
    assert _errors(schema, legacy)


@pytest.mark.parametrize(
    ("outcome", "claims", "valid"),
    [
        ("recommend", [], False),
        ("wait", [], False),
        ("abstain", [], True),
        (
            "recommend",
            [{"claim": "Disponible", "evidence_refs": ["catalog:item-1"]}],
            True,
        ),
        (
            "wait",
            [{"claim": "Prix inconnu", "evidence_refs": ["catalog:item-1"]}],
            True,
        ),
    ],
)
def test_decision_prediction_non_abstain_outcomes_require_claims(
    outcome: str,
    claims: list[dict[str, Any]],
    valid: bool,
) -> None:
    schema = _schema("prediction.schema.json")
    prediction = _prediction(
        "decision",
        {"outcome": outcome, "claims": claims},
    )
    assert (_errors(schema, prediction) == []) is valid


def test_retrieval_gold_requires_explicit_constraint_violators() -> None:
    schema = _schema("retrieval.schema.json")
    label = {
        "resolution": "matched",
        "relevant_product_ids": ["item-1"],
        "constraint_violating_product_ids": [],
    }
    record = _record(
        "retrieval",
        {"locale": "fr", "query": "noir", "hard_constraints": {"colour": "black"}},
        label,
    )
    assert _errors(schema, record) == []

    missing = deepcopy(record)
    del missing["gold"]["constraint_violating_product_ids"]
    assert _errors(schema, missing)

    blank = deepcopy(record)
    blank["gold"]["constraint_violating_product_ids"] = [" "]
    assert _errors(schema, blank)


def test_retrieval_gold_requires_closed_exact_product_ids_only_for_exact_match() -> None:
    schema = _schema("retrieval.schema.json")
    exact = _record(
        "retrieval",
        {"locale": "fr", "query": "modèle exact", "hard_constraints": {}},
        {
            "resolution": "matched",
            "relevant_product_ids": ["target", "substitute"],
            "exact_product_ids": ["target"],
            "constraint_violating_product_ids": [],
        },
    )
    assert _errors(schema, exact) == []

    missing = deepcopy(exact)
    del missing["gold"]["exact_product_ids"]
    assert _errors(schema, missing)

    empty = deepcopy(exact)
    empty["gold"]["exact_product_ids"] = []
    assert _errors(schema, empty)

    generic = deepcopy(exact)
    generic["input"]["strata"]["scenario_type"] = "generic_product"
    assert _errors(schema, generic)
    generic["gold"]["exact_product_ids"] = []
    assert _errors(schema, generic) == []


def test_retrieval_gold_caps_relevant_products_at_recall_depth() -> None:
    schema = _schema("retrieval.schema.json")

    fifty = {
        "resolution": "matched",
        "relevant_product_ids": [f"item-{index}" for index in range(50)],
        "constraint_violating_product_ids": [],
    }
    valid = _record(
        "retrieval",
        {"locale": "fr", "query": "produit", "hard_constraints": {}},
        fifty,
    )
    assert _errors(schema, valid) == []

    fifty_one = deepcopy(valid)
    fifty_one["gold"]["relevant_product_ids"].append("item-50")
    for annotation in fifty_one["annotations"]:
        annotation["label"]["relevant_product_ids"].append("item-50")
    assert _errors(schema, fifty_one)


@pytest.mark.parametrize(
    "query",
    [
        "",
        " ",
        "\nproduit",
        "\rproduit",
        "\u2028produit",
        "produit\n",
        "produit\r",
        "produit\u2028",
    ],
)
def test_retrieval_query_rejects_blank_boundaries(query: str) -> None:
    schema = _schema("retrieval.schema.json")
    label = {
        "resolution": "matched",
        "relevant_product_ids": ["item-1"],
        "constraint_violating_product_ids": [],
    }
    record = _record(
        "retrieval",
        {"locale": "fr", "query": query, "hard_constraints": {}},
        label,
    )
    assert _errors(schema, record)


@pytest.mark.parametrize("resolution", ["no_match", "ambiguous"])
def test_retrieval_nonmatched_gold_requires_an_empty_relevance_set(
    resolution: str,
) -> None:
    schema = _schema("retrieval.schema.json")
    label = {
        "resolution": resolution,
        "relevant_product_ids": [],
        "constraint_violating_product_ids": [],
    }
    record = _record(
        "retrieval",
        {"locale": "fr", "query": "introuvable", "hard_constraints": {}},
        label,
    )
    assert _errors(schema, record) == []

    contradictory = deepcopy(record)
    contradictory["gold"]["relevant_product_ids"] = ["item-1"]
    for annotation in contradictory["annotations"]:
        annotation["label"]["relevant_product_ids"] = ["item-1"]
    assert _errors(schema, contradictory)


def test_retrieval_matched_gold_requires_at_least_one_relevant_product() -> None:
    schema = _schema("retrieval.schema.json")
    label = {
        "resolution": "matched",
        "relevant_product_ids": [],
        "constraint_violating_product_ids": [],
    }
    record = _record(
        "retrieval",
        {"locale": "fr", "query": "produit", "hard_constraints": {}},
        label,
    )
    assert _errors(schema, record)


@pytest.mark.parametrize("resolution", ["no_match", "ambiguous"])
def test_retrieval_nonmatched_prediction_requires_an_empty_ranking(
    resolution: str,
) -> None:
    schema = _schema("prediction.schema.json")
    valid = _prediction(
        "retrieval",
        {"resolution": resolution, "retrieved_product_ids": []},
    )
    assert _errors(schema, valid) == []

    contradictory = deepcopy(valid)
    contradictory["prediction"]["retrieved_product_ids"] = ["item-1"]
    assert _errors(schema, contradictory)


def test_retrieval_matched_prediction_requires_a_nonempty_ranking() -> None:
    schema = _schema("prediction.schema.json")
    valid = _prediction(
        "retrieval",
        {"resolution": "matched", "retrieved_product_ids": ["item-1"]},
    )
    assert _errors(schema, valid) == []

    missing = deepcopy(valid)
    del missing["prediction"]["resolution"]
    assert _errors(schema, missing)

    empty = deepcopy(valid)
    empty["prediction"]["retrieved_product_ids"] = []
    assert _errors(schema, empty)


@pytest.mark.parametrize(
    ("eligibility", "expected_variant_id", "valid"),
    [
        ("eligible", "variant-1", True),
        ("eligible", None, False),
        ("eligible", " ", False),
        ("quarantine", None, True),
        ("quarantine", "variant-1", False),
        ("reject", None, True),
        ("reject", "variant-1", False),
    ],
)
def test_offer_gold_variant_id_follows_eligibility(
    eligibility: str,
    expected_variant_id: str | None,
    valid: bool,
) -> None:
    schema = _schema("offer-attachment.schema.json")
    label = {
        "expected_variant_id": expected_variant_id,
        "eligibility": eligibility,
    }
    record = _record("offer_attachment", {"offer": {"sku": "sku-1"}}, label)
    assert (_errors(schema, record) == []) is valid


@pytest.mark.parametrize(
    ("eligibility", "expected_variant_id", "valid"),
    [
        ("eligible", "variant-1", True),
        ("eligible", None, False),
        ("quarantine", None, True),
        ("quarantine", "variant-1", False),
        ("reject", None, True),
        ("reject", "variant-1", False),
    ],
)
def test_offer_prediction_variant_id_follows_eligibility(
    eligibility: str,
    expected_variant_id: str | None,
    valid: bool,
) -> None:
    schema = _schema("prediction.schema.json")
    prediction = _prediction(
        "offer_attachment",
        {
            "expected_variant_id": expected_variant_id,
            "eligibility": eligibility,
        },
    )
    assert (_errors(schema, prediction) == []) is valid


def test_every_dataset_requires_closed_scenario_language_and_vertical_strata() -> None:
    schema_names = (
        "taxonomy.schema.json",
        "entity-resolution.schema.json",
        "variant-resolution.schema.json",
        "offer-attachment.schema.json",
        "offer-truth.schema.json",
        "retrieval.schema.json",
        "decision.schema.json",
    )
    for schema_name in schema_names:
        schema = _schema(schema_name)
        assert "strata" in schema["$defs"]["input"]["required"]
        validator = Draft202012Validator(schema["$defs"]["strata"])
        valid = {
            "scenario_type": "no_match",
            "language": "en",
            "vertical": "headphones_audio",
        }
        assert list(validator.iter_errors(valid)) == []
        invalid = deepcopy(valid)
        invalid["language"] = "de"
        assert list(validator.iter_errors(invalid))


def test_retrieval_locale_must_match_the_language_stratum() -> None:
    schema = _schema("retrieval.schema.json")
    record = _record(
        "retrieval",
        {"locale": "fr", "query": "produit", "hard_constraints": {}},
        {
            "resolution": "matched",
            "relevant_product_ids": ["item-1"],
            "constraint_violating_product_ids": [],
        },
    )
    assert _errors(schema, record) == []
    record["input"]["strata"]["language"] = "nl"
    assert _errors(schema, record)


def test_taxonomy_gold_and_prediction_require_all_three_dimensions() -> None:
    schema = _schema("taxonomy.schema.json")
    label = {
        "category": "electronics",
        "subcategory": "smartphones",
        "product_role": "primary_product",
    }
    record = _record("taxonomy", {"observation": {"name": "Phone"}}, label)
    assert _errors(schema, record) == []

    prediction_schema = _schema("prediction.schema.json")
    prediction = _prediction("taxonomy", label)
    assert _errors(prediction_schema, prediction) == []
    del prediction["prediction"]["subcategory"]
    assert _errors(prediction_schema, prediction)


def test_offer_truth_contract_is_integer_money_unknown_safe_and_https_only() -> None:
    schema = _schema("offer-truth.schema.json")
    label = {
        "price": {"amount_minor": 99900, "currency": "EUR"},
        "stock": "in_stock",
        "shipping": None,
        "affiliate_link": "https://merchant.example/item",
    }
    record = _record(
        "offer_truth",
        {"offer": {"source_ref": "merchant:item"}},
        label,
    )
    assert _errors(schema, record) == []

    prediction_schema = _schema("prediction.schema.json")
    prediction = _prediction("offer_truth", label)
    assert _errors(prediction_schema, prediction) == []
    prediction["prediction"]["affiliate_link"] = "http://merchant.example/item"
    assert _errors(prediction_schema, prediction)
