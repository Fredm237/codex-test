from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from quality_lab import evaluate as evaluate_module
from quality_lab import scorecard as scorecard_module
from quality_lab.annotation_workflow import merge_completed_packs, prepare_pack
from quality_lab.integrity import (
    DATASETS,
    FINGERPRINT_PATTERN,
    LANGUAGES,
    RECORD_VERSION,
    SCHEMA_FILES,
    SCENARIO_TYPES,
    VERTICALS,
    atomic_write_text,
    canonical_json,
    case_fingerprint,
    schema_value_fingerprint,
    sha256_file,
    split_for_group,
)
from quality_lab.scorecard import (
    ERROR_CODES,
    _evaluate_gates,
    build_scorecard,
    ensure_output_is_distinct,
    quality_input_paths,
    score_holdout,
)
from quality_lab.run_identity import quality_run_id


ROOT = Path(__file__).resolve().parents[2]
QUALITY = ROOT / "quality"
MANIFEST = json.loads((QUALITY / "manifest.json").read_text(encoding="utf-8"))
UNIT_MANIFEST = deepcopy(MANIFEST)
UNIT_MANIFEST["measurement_support"] = {
    key: 1 for key in MANIFEST["measurement_support"]
}
UNIT_MANIFEST["gates"].update(
    {
        "category_accuracy_min": 0.0,
        "subcategory_accuracy_min": 0.0,
        "product_role_accuracy_min": 0.0,
        "entity_match_accuracy_min": 0.0,
        "false_merge_rate_max": 1.0,
        "false_split_rate_max": 1.0,
        "entity_variant_relation_accuracy_min": 0.0,
        "variant_resolution_accuracy_min": 0.0,
        "offer_attachment_accuracy_min": 0.0,
        "offer_eligibility_accuracy_min": 0.0,
        "price_accuracy_min": 0.0,
        "stock_accuracy_min": 0.0,
        "shipping_accuracy_min": 0.0,
        "affiliate_link_accuracy_min": 0.0,
        "retrieval_top_3_relevance_min": 0.0,
        "exact_product_match_accuracy_min": 0.0,
        "absurd_result_rate_max": 1.0,
        "retrieval_recall_at_50_min": 0.0,
        "retrieval_ndcg_at_10_min": 0.0,
        "retrieval_no_match_accuracy_min": 0.0,
        "retrieval_ambiguous_accuracy_min": 0.0,
        "calibration_ece_max": 1.0,
        "sourced_explanation_coverage_min": 0.0,
    }
)
RUN_ID = "quality-run-test"


def _test_group(prefix: str) -> str:
    for index in range(10_000):
        group_id = f"{prefix}-{index}"
        if split_for_group(group_id) == "test":
            return group_id
    raise AssertionError("no test group found")


def _decision_input(
    *,
    language: str,
    candidate_id: str = "product-1",
    evidence_ref: str = "catalog:p1",
    include_candidate: bool = True,
    offer_id: int = 1,
) -> dict[str, Any]:
    offers: list[dict[str, Any]] = []
    evidence: list[dict[str, str]] = []
    candidate_ids: list[str] = []
    if include_candidate:
        offers.append(
            {
                "candidate_id": candidate_id,
                "offer_id": offer_id,
                "catalog_product_id": offer_id,
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
                "evidence_refs": [evidence_ref],
            }
        )
        candidate_ids.append(candidate_id)
        evidence.append(
            {"evidence_ref": evidence_ref, "source_ref": f"offer:{offer_id}"}
        )
    return {
        "request": {
            "query": "ordinateur portable sous 500 €",
            "locale": language,
            "reference_time": "2026-08-29T10:00:00Z",
            "offers": offers,
        },
        "candidate_ids": candidate_ids,
        "evidence": evidence,
    }


def _minimal_gold(
    dataset: str,
    case_id: str,
    gold: dict[str, Any],
    input_value: dict[str, Any] | None = None,
    *,
    stratum_index: int | None = None,
) -> dict[str, Any]:
    input_payload = deepcopy(input_value or {})
    if stratum_index is None:
        suffix = case_id.rpartition("-")[2]
        stratum_index = int(suffix) if suffix.isdigit() else 0
    strata = {
        "scenario_type": SCENARIO_TYPES[stratum_index % len(SCENARIO_TYPES)],
        "language": LANGUAGES[stratum_index % len(LANGUAGES)],
        "vertical": VERTICALS[stratum_index % len(VERTICALS)],
    }
    input_payload.setdefault("strata", strata)
    if dataset == "retrieval":
        input_payload.setdefault("locale", input_payload["strata"]["language"])
    gold_payload = deepcopy(gold)
    if dataset == "retrieval":
        is_exact_match = (
            input_payload["strata"]["scenario_type"] == "exact_product"
            and gold_payload.get("resolution") == "matched"
        )
        relevant = gold_payload.get("relevant_product_ids")
        gold_payload.setdefault(
            "exact_product_ids",
            [relevant[0]]
            if is_exact_match and isinstance(relevant, list) and relevant
            else [],
        )
    record = {
        "dataset": dataset,
        "case_id": case_id,
        "group_id": _test_group(case_id),
        "split": "test",
        "input": input_payload,
        "gold": gold_payload,
    }
    record["case_fingerprint"] = case_fingerprint(record)
    return record


def _prediction(gold: dict[str, Any], prediction: dict[str, Any]) -> dict[str, Any]:
    return {
        "record_version": RECORD_VERSION,
        "dataset": gold["dataset"],
        "case_id": gold["case_id"],
        "case_fingerprint": gold["case_fingerprint"],
        "run_id": RUN_ID,
        "confidence": 1.0,
        "prediction": deepcopy(prediction),
    }


def _perfect_holdout() -> tuple[
    dict[str, list[dict[str, Any]]],
    dict[str, list[dict[str, Any]]],
]:
    taxonomy = _minimal_gold(
        "taxonomy",
        "taxonomy-case",
        {
            "category": "electronics",
            "subcategory": "smartphones",
            "product_role": "primary_product",
        },
        {"observation": {"name": "Téléphone modèle 1"}},
        stratum_index=7,
    )
    entity_same = _minimal_gold(
        "entity_resolution",
        "entity-same",
        {"product_relation": "same", "variant_relation": "same"},
        stratum_index=1,
    )
    entity_different = _minimal_gold(
        "entity_resolution",
        "entity-different",
        {"product_relation": "different", "variant_relation": "not_applicable"},
        stratum_index=2,
    )
    variant = _minimal_gold(
        "variant_resolution",
        "variant-case",
        {
            "expected_variant": {
                "variant_key": "variant-42",
                "attributes": {"size": "42"},
                "resolution": "resolved",
            }
        },
        stratum_index=3,
    )
    offer = _minimal_gold(
        "offer_attachment",
        "offer-case",
        {"expected_variant_id": "variant-42", "eligibility": "eligible"},
        stratum_index=4,
    )
    rejected_offer = _minimal_gold(
        "offer_attachment",
        "offer-rejected",
        {"expected_variant_id": None, "eligibility": "reject"},
        stratum_index=5,
    )
    offer_truth = _minimal_gold(
        "offer_truth",
        "offer-truth-case",
        {
            "price": {"amount_minor": 99900, "currency": "EUR"},
            "stock": "in_stock",
            "shipping": {"amount_minor": 0, "currency": "EUR"},
            "affiliate_link": "https://merchant.example/item-1",
        },
        {"offer": {"source_ref": "merchant:item-1"}},
        stratum_index=6,
    )
    retrieval = _minimal_gold(
        "retrieval",
        "retrieval-case",
        {
            "resolution": "matched",
            "relevant_product_ids": ["product-1"],
            "constraint_violating_product_ids": [],
        },
        stratum_index=0,
    )
    retrieval_scenarios = [
        _minimal_gold(
            "retrieval",
            f"retrieval-{SCENARIO_TYPES[index]}",
            {
                "resolution": "matched",
                "relevant_product_ids": [f"product-{index}"],
                "constraint_violating_product_ids": [],
            },
            stratum_index=index,
        )
        for index in range(1, 8)
    ]
    retrieval_no_match = _minimal_gold(
        "retrieval",
        "retrieval-no-match",
        {
            "resolution": "no_match",
            "relevant_product_ids": [],
            "constraint_violating_product_ids": [],
        },
        stratum_index=9,
    )
    retrieval_ambiguous = _minimal_gold(
        "retrieval",
        "retrieval-ambiguous",
        {
            "resolution": "ambiguous",
            "relevant_product_ids": [],
            "constraint_violating_product_ids": [],
        },
        stratum_index=8,
    )
    decision = _minimal_gold(
        "decision",
        "decision-case",
        {
            "acceptable_outcomes": ["recommend"],
            "forbidden_claims": ["unsafe"],
            "claim_evidence": [
                {"claim": "source-confirmed", "evidence_refs": ["catalog:p1"]}
            ],
        },
        {
            **_decision_input(language=LANGUAGES[10 % len(LANGUAGES)]),
        },
        stratum_index=10,
    )
    gold = {
        "taxonomy": [taxonomy],
        "entity_resolution": [entity_same, entity_different],
        "variant_resolution": [variant],
        "offer_attachment": [offer, rejected_offer],
        "offer_truth": [offer_truth],
        "retrieval": [
            retrieval,
            *retrieval_scenarios,
            retrieval_no_match,
            retrieval_ambiguous,
        ],
        "decision": [decision],
    }
    predictions = {
        "taxonomy": [_prediction(taxonomy, taxonomy["gold"])],
        "entity_resolution": [
            _prediction(entity_same, entity_same["gold"]),
            _prediction(entity_different, entity_different["gold"]),
        ],
        "variant_resolution": [_prediction(variant, variant["gold"])],
        "offer_attachment": [
            _prediction(offer, offer["gold"]),
            _prediction(rejected_offer, rejected_offer["gold"]),
        ],
        "offer_truth": [_prediction(offer_truth, offer_truth["gold"])],
        "retrieval": [
            _prediction(
                retrieval,
                {
                    "resolution": "matched",
                    "retrieved_product_ids": ["product-1"],
                },
            ),
            *[
                _prediction(
                    scenario,
                    {
                        "resolution": "matched",
                        "retrieved_product_ids": scenario["gold"][
                            "relevant_product_ids"
                        ],
                    },
                )
                for scenario in retrieval_scenarios
            ],
            _prediction(
                retrieval_no_match,
                {"resolution": "no_match", "retrieved_product_ids": []},
            ),
            _prediction(
                retrieval_ambiguous,
                {"resolution": "ambiguous", "retrieved_product_ids": []},
            ),
        ],
        "decision": [
            _prediction(
                decision,
                {
                    "outcome": "recommend",
                    "claims": [
                        {
                            "claim": "source-confirmed",
                            "evidence_refs": ["catalog:p1"],
                        }
                    ],
                },
            )
        ],
    }
    return gold, predictions


def test_scorecard_parfait_execute_tous_les_gates():
    gold, predictions = _perfect_holdout()
    report = score_holdout(UNIT_MANIFEST, gold, predictions, run_id=RUN_ID)

    assert report["status"] == "pass"
    assert report["measurable"] is True
    assert report["errors"] == []
    assert FINGERPRINT_PATTERN.fullmatch(report["holdout_fingerprint"])
    assert len(report["gates"]) == 27
    assert all(gate["passed"] is True for gate in report["gates"])
    assert report["metrics"]["false_merge_rate"] == 0.0
    assert report["metrics"]["retrieval_precision_at_1"] == 1.0
    assert report["metrics"]["retrieval_precision_at_3"] == pytest.approx(1 / 3)
    assert report["metrics"]["retrieval_precision_at_5"] == pytest.approx(1 / 5)
    assert report["metrics"]["retrieval_top_3_relevance"] == 1.0
    assert report["metrics"]["exact_product_match_accuracy"] == 1.0
    assert report["metrics"]["absurd_result_rate"] == 0.0
    assert report["metrics"]["retrieval_recall_at_10"] == 1.0
    assert report["metrics"]["retrieval_recall_at_50_ci95_lower"] == 0.0
    assert report["metrics"]["retrieval_ndcg_at_10"] == 1.0
    assert report["metrics"]["retrieval_ndcg_at_10_ci95_lower"] == 0.0
    assert report["metrics"]["calibration_ece"] == 0.0
    assert report["metrics"]["calibration_ece_ci95_upper"] == 0.0
    assert report["metrics"]["calibration_brier_score"] == 0.0
    assert report["metrics"]["decision_correct_answer"] == 1
    assert report["metrics"]["decision_correct_abstention"] == 0
    assert report["metrics"]["decision_wrong_answer"] == 0
    assert report["metrics"]["decision_wrong_abstention"] == 0
    assert report["metrics"]["decision_outcome_matrix_total"] == 1
    assert report["metrics"]["details"]["decision"]["outcome_matrix_total"] == 1
    assert report["metrics"]["details"]["calibration"]["brier_score"] == 0.0


def test_holdout_fingerprint_is_order_independent_and_binds_case_content():
    gold, predictions = _perfect_holdout()
    original = score_holdout(UNIT_MANIFEST, gold, predictions, run_id=RUN_ID)

    reordered_gold = {
        dataset: list(reversed(rows)) for dataset, rows in deepcopy(gold).items()
    }
    reordered_predictions = {
        dataset: list(reversed(rows))
        for dataset, rows in deepcopy(predictions).items()
    }
    reordered = score_holdout(
        UNIT_MANIFEST,
        reordered_gold,
        reordered_predictions,
        run_id=RUN_ID,
    )
    assert reordered["holdout_fingerprint"] == original["holdout_fingerprint"]

    changed_gold = deepcopy(gold)
    changed_predictions = deepcopy(predictions)
    changed_case = changed_gold["taxonomy"][0]
    changed_case["input"]["observation"]["name"] = "Téléphone modèle 2"
    changed_case["case_fingerprint"] = case_fingerprint(changed_case)
    changed_predictions["taxonomy"][0]["case_fingerprint"] = changed_case[
        "case_fingerprint"
    ]
    changed = score_holdout(
        UNIT_MANIFEST,
        changed_gold,
        changed_predictions,
        run_id=RUN_ID,
    )

    assert changed["status"] == "pass"
    assert changed["holdout"] == original["holdout"]
    assert changed["holdout_fingerprint"] != original["holdout_fingerprint"]


def test_exact_product_top1_failure_is_also_a_calibration_failure():
    gold, predictions = _perfect_holdout()
    exact_gold = gold["retrieval"][0]
    exact_gold["gold"]["relevant_product_ids"] = ["product-1", "substitute"]
    exact_gold["case_fingerprint"] = case_fingerprint(exact_gold)
    exact_prediction = predictions["retrieval"][0]
    exact_prediction["case_fingerprint"] = exact_gold["case_fingerprint"]
    exact_prediction["prediction"]["retrieved_product_ids"] = [
        "substitute",
        "product-1",
    ]

    report = score_holdout(UNIT_MANIFEST, gold, predictions, run_id=RUN_ID)

    assert report["metrics"]["exact_product_match_accuracy"] == 0.0
    assert report["metrics"]["calibration_brier_score"] > 0.0
    assert report["metrics"]["calibration_ece"] > 0.0


def test_scorecard_decision_matrix_covers_answers_wait_and_abstentions():
    gold, predictions = _perfect_holdout()

    decision_cases = [
        (
            "correct-abstention",
            ["abstain"],
            "abstain",
            [],
        ),
        (
            "wrong-wait-answer",
            ["recommend"],
            "wait",
            [
                {
                    "claim": "source-confirmed",
                    "evidence_refs": ["catalog:p1"],
                }
            ],
        ),
        (
            "wrong-abstention",
            ["recommend"],
            "abstain",
            [],
        ),
    ]
    for case_id, acceptable_outcomes, outcome, claims in decision_cases:
        permits_answer = any(
            acceptable in {"recommend", "wait"}
            for acceptable in acceptable_outcomes
        )
        claim_evidence = (
            [
                {
                    "claim": "source-confirmed",
                    "evidence_refs": ["catalog:p1"],
                }
            ]
            if permits_answer
            else []
        )
        row = _minimal_gold(
            "decision",
            case_id,
            {
                "acceptable_outcomes": acceptable_outcomes,
                "forbidden_claims": [],
                "claim_evidence": claim_evidence,
            },
            _decision_input(language="fr", include_candidate=permits_answer),
        )
        gold["decision"].append(row)
        predictions["decision"].append(
            _prediction(row, {"outcome": outcome, "claims": claims})
        )

    report = score_holdout(UNIT_MANIFEST, gold, predictions, run_id=RUN_ID)
    metrics = report["metrics"]

    assert metrics["decision_correct_answer"] == 1
    assert metrics["decision_correct_abstention"] == 1
    assert metrics["decision_wrong_answer"] == 1
    assert metrics["decision_wrong_abstention"] == 1
    assert metrics["decision_outcome_matrix_total"] == metrics["decision_cases"] == 4
    assert metrics["details"]["decision"]["outcome_matrix_total"] == 4


def test_micro_lot_parfait_ne_prouve_pas_les_seuils_de_production():
    gold, predictions = _perfect_holdout()

    report = score_holdout(MANIFEST, gold, predictions, run_id=RUN_ID)

    assert report["status"] == "not_measurable"
    assert report["measurable"] is False
    assert report["metrics"]["false_merge_rate"] == 0.0
    assert any(
        error["code"] == "QL013_METRIC_NOT_MEASURABLE"
        and error["path"] == "metrics/entity_different_pairs"
        for error in report["errors"]
    )


def test_claim_auto_atteste_reste_non_supporte_par_le_gold():
    gold, predictions = _perfect_holdout()
    predictions["decision"][0]["prediction"]["claims"] = [
        {"claim": "invented", "evidence_refs": ["invented:self"]}
    ]

    report = score_holdout(UNIT_MANIFEST, gold, predictions, run_id=RUN_ID)

    assert report["status"] == "fail"
    assert report["metrics"]["unsupported_claims"] == 1
    assert next(
        gate for gate in report["gates"] if gate["gate"] == "unsupported_claims_max"
    )["passed"] is False


def test_preuve_gold_absente_de_l_entree_aveugle_est_refusee():
    gold, predictions = _perfect_holdout()
    decision = gold["decision"][0]
    decision["input"]["evidence"] = [
        {"evidence_ref": "catalog:other", "source_ref": "catalog:other"}
    ]
    decision["case_fingerprint"] = case_fingerprint(decision)
    predictions["decision"][0]["case_fingerprint"] = decision["case_fingerprint"]

    report = score_holdout(UNIT_MANIFEST, gold, predictions, run_id=RUN_ID)

    assert report["status"] == "not_measurable"
    assert any(
        error["code"] == "QL002_GOLD_NOT_READY"
        and error["path"] == "gold"
        for error in report["errors"]
    )


def test_offre_rejetee_predite_eligible_declenche_le_gate_de_securite():
    gold, predictions = _perfect_holdout()
    rejected = next(
        row
        for row in predictions["offer_attachment"]
        if row["case_id"] == "offer-rejected"
    )
    rejected["prediction"] = {
        "eligibility": "eligible",
        "expected_variant_id": "invented-variant",
    }

    report = score_holdout(UNIT_MANIFEST, gold, predictions, run_id=RUN_ID)

    assert report["status"] == "fail"
    assert report["metrics"]["false_eligible_offers"] == 1
    assert next(
        gate
        for gate in report["gates"]
        if gate["gate"] == "false_eligible_offers_max"
    )["passed"] is False


def test_relation_de_variante_entity_est_gatee_independamment_du_produit():
    gold, predictions = _perfect_holdout()
    predictions["entity_resolution"][0]["prediction"]["variant_relation"] = (
        "different"
    )
    manifest = deepcopy(UNIT_MANIFEST)
    manifest["gates"]["entity_variant_relation_accuracy_min"] = 0.1

    report = score_holdout(manifest, gold, predictions, run_id=RUN_ID)

    assert report["status"] == "fail"
    assert report["metrics"]["false_merge_rate"] == 0.0
    assert report["metrics"]["false_split_rate"] == 0.0
    assert report["metrics"]["entity_variant_relation_accuracy"] == 0.0
    assert next(
        gate
        for gate in report["gates"]
        if gate["gate"] == "entity_variant_relation_accuracy_min"
    )["passed"] is False


def test_retrieval_interdit_dans_le_top_10_est_une_violation():
    gold, predictions = _perfect_holdout()
    gold_row = gold["retrieval"][0]
    gold_row["gold"]["constraint_violating_product_ids"] = ["forbidden"]
    gold_row["case_fingerprint"] = case_fingerprint(gold_row)
    prediction = predictions["retrieval"][0]
    prediction["case_fingerprint"] = gold_row["case_fingerprint"]
    prediction["prediction"]["retrieved_product_ids"].append("forbidden")

    report = score_holdout(UNIT_MANIFEST, gold, predictions, run_id=RUN_ID)

    assert report["status"] == "fail"
    assert report["metrics"]["retrieval_recall_at_50"] == 1.0
    assert report["metrics"]["retrieval_constraint_violations_at_10"] == 1


def test_confiance_entier_hors_capacite_float_est_ql011():
    gold, predictions = _perfect_holdout()
    predictions["variant_resolution"][0]["confidence"] = 10**400

    report = score_holdout(UNIT_MANIFEST, gold, predictions, run_id=RUN_ID)

    assert report["status"] == "not_measurable"
    assert {error["code"] for error in report["errors"]} == {
        "QL011_CONFIDENCE_INVALID"
    }


def test_lot_parfait_aux_supports_declares_passe_les_bornes_wilson():
    gold: dict[str, list[dict[str, Any]]] = {dataset: [] for dataset in DATASETS}
    predictions: dict[str, list[dict[str, Any]]] = {
        dataset: [] for dataset in DATASETS
    }

    for index in range(500):
        row = _minimal_gold(
            "taxonomy",
            f"taxonomy-{index}",
            {
                "category": "electronics",
                "subcategory": "smartphones",
                "product_role": "primary_product",
            },
            {"observation": {"name": f"product-{index}"}},
        )
        gold["taxonomy"].append(row)
        predictions["taxonomy"].append(_prediction(row, row["gold"]))

    for relation, count in (("different", 800), ("same", 200)):
        for index in range(count):
            variant_relation = "not_applicable" if relation == "different" else "same"
            row = _minimal_gold(
                "entity_resolution",
                f"entity-{relation}-{index}",
                {
                    "product_relation": relation,
                    "variant_relation": variant_relation,
                },
            )
            gold["entity_resolution"].append(row)
            predictions["entity_resolution"].append(_prediction(row, row["gold"]))

    expected_variant = {
        "variant_key": "variant-42",
        "attributes": {"size": "42"},
        "resolution": "resolved",
    }
    for index in range(200):
        row = _minimal_gold(
            "variant_resolution",
            f"variant-{index}",
            {"expected_variant": expected_variant},
        )
        gold["variant_resolution"].append(row)
        predictions["variant_resolution"].append(_prediction(row, row["gold"]))

    for index in range(500):
        eligible = index < 200
        label = {
            "eligibility": "eligible" if eligible else "reject",
            "expected_variant_id": f"variant-{index}" if eligible else None,
        }
        row = _minimal_gold("offer_attachment", f"offer-{index}", label)
        gold["offer_attachment"].append(row)
        predictions["offer_attachment"].append(_prediction(row, row["gold"]))

    offer_truth_label = {
        "price": {"amount_minor": 99900, "currency": "EUR"},
        "stock": "in_stock",
        "shipping": {"amount_minor": 0, "currency": "EUR"},
        "affiliate_link": "https://merchant.example/item",
    }
    for index in range(500):
        row = _minimal_gold(
            "offer_truth",
            f"offer-truth-{index}",
            offer_truth_label,
            {"offer": {"source_ref": f"merchant:item-{index}"}},
        )
        gold["offer_truth"].append(row)
        predictions["offer_truth"].append(_prediction(row, row["gold"]))

    for index in range(1300):
        if index < 475:
            resolution = "matched"
            relevant_product_ids = [f"product-{index}"]
        elif index < 1075:
            resolution = "no_match"
            relevant_product_ids = []
        else:
            resolution = "ambiguous"
            relevant_product_ids = []
        if index < 300:
            stratum_index = 0
        elif index < 475:
            stratum_index = 1 + ((index - 300) % 7)
        elif index < 1075:
            stratum_index = 9
        else:
            stratum_index = 8
        row = _minimal_gold(
            "retrieval",
            f"retrieval-{index}",
            {
                "resolution": resolution,
                "relevant_product_ids": relevant_product_ids,
                "constraint_violating_product_ids": [],
            },
            {
                "strata": {
                    "scenario_type": SCENARIO_TYPES[stratum_index],
                    "language": LANGUAGES[index % len(LANGUAGES)],
                    "vertical": VERTICALS[index % len(VERTICALS)],
                }
            },
            stratum_index=stratum_index,
        )
        gold["retrieval"].append(row)
        predictions["retrieval"].append(
            _prediction(
                row,
                {
                    "resolution": resolution,
                    "retrieved_product_ids": relevant_product_ids,
                },
            )
        )

    for index in range(500):
        claim = f"claim-{index}"
        evidence = f"catalog:product-{index}"
        row = _minimal_gold(
            "decision",
            f"decision-{index}",
            {
                "acceptable_outcomes": ["recommend"],
                "forbidden_claims": [],
                "claim_evidence": [
                    {"claim": claim, "evidence_refs": [evidence]}
                ],
            },
            _decision_input(
                language=LANGUAGES[index % len(LANGUAGES)],
                candidate_id=f"product-{index}",
                evidence_ref=evidence,
                offer_id=index + 1,
            ),
        )
        gold["decision"].append(row)
        predictions["decision"].append(
            _prediction(
                row,
                {
                    "outcome": "recommend",
                    "claims": [{"claim": claim, "evidence_refs": [evidence]}],
                },
            )
        )

    report = score_holdout(MANIFEST, gold, predictions, run_id=RUN_ID)

    assert report["status"] == "pass"
    assert report["measurable"] is True
    assert report["errors"] == []
    assert all(gate["passed"] is True for gate in report["gates"])
    assert report["metrics"]["false_merge_rate_ci95_upper"] < 0.005
    assert report["metrics"]["false_split_rate_ci95_upper"] < 0.02
    assert report["metrics"]["retrieval_recall_at_50_ci95_lower"] > 0.95
    assert report["metrics"]["retrieval_ndcg_at_10_ci95_lower"] > 0.85
    assert report["metrics"]["retrieval_precision_at_3"] == pytest.approx(1 / 3)
    assert report["metrics"]["retrieval_top_3_relevance_ci95_lower"] > 0.9
    assert report["metrics"]["exact_product_match_accuracy_ci95_lower"] >= 0.98
    assert report["metrics"]["absurd_result_rate_ci95_upper"] < 0.01
    assert report["metrics"]["retrieval_no_match_accuracy_ci95_lower"] >= 0.99
    assert report["metrics"]["calibration_ece_ci95_upper"] < 0.05
    assert report["metrics"]["sourced_explanation_coverage_ci95_lower"] > 0.99


def test_scorecard_mesurable_mais_sous_seuil_est_fail():
    gold, predictions = _perfect_holdout()
    different = next(
        row
        for row in predictions["entity_resolution"]
        if row["case_id"] == "entity-different"
    )
    different["prediction"]["product_relation"] = "same"
    different["prediction"]["variant_relation"] = "different"

    manifest = deepcopy(UNIT_MANIFEST)
    manifest["gates"]["false_merge_rate_max"] = 0.99
    report = score_holdout(manifest, gold, predictions, run_id=RUN_ID)

    assert report["status"] == "fail"
    assert report["measurable"] is True
    assert report["metrics"]["false_merge_rate"] == 1.0
    assert any(
        gate["gate"] == "false_merge_rate_max" and gate["passed"] is False
        for gate in report["gates"]
    )


def test_run_partiel_parfait_est_not_measurable_sans_metriques():
    gold, predictions = _perfect_holdout()
    predictions["entity_resolution"] = predictions["entity_resolution"][:1]

    report = score_holdout(UNIT_MANIFEST, gold, predictions, run_id=RUN_ID)

    assert report["status"] == "not_measurable"
    assert report["metrics"] == {}
    assert any(error["code"] == "QL008_MISSING_CASE_ID" for error in report["errors"])


@pytest.mark.parametrize(
    "mutation, expected_code",
    [
        ("fingerprint", "QL010_CASE_FINGERPRINT_MISMATCH"),
        ("duplicate", "QL007_DUPLICATE_CASE_ID"),
        ("extra", "QL009_UNEXPECTED_CASE_ID"),
        ("confidence", "QL011_CONFIDENCE_INVALID"),
        ("ranking", "QL012_DUPLICATE_RANKED_ID"),
    ],
)
def test_scorecard_refuse_les_artefacts_incomplets_ou_ambigus(mutation, expected_code):
    gold, predictions = _perfect_holdout()
    if mutation == "fingerprint":
        predictions["entity_resolution"][0]["case_fingerprint"] = "sha256:" + "0" * 64
    elif mutation == "duplicate":
        predictions["entity_resolution"].append(
            deepcopy(predictions["entity_resolution"][0])
        )
    elif mutation == "extra":
        extra = deepcopy(predictions["entity_resolution"][0])
        extra["case_id"] = "entity-extra"
        predictions["entity_resolution"].append(extra)
    elif mutation == "confidence":
        predictions["variant_resolution"][0]["confidence"] = True
    else:
        predictions["retrieval"][0]["prediction"]["retrieved_product_ids"] = [
            "product-1",
            "product-1",
        ]

    report = score_holdout(UNIT_MANIFEST, gold, predictions, run_id=RUN_ID)

    assert report["status"] == "not_measurable"
    assert report["metrics"] == {}
    assert any(error["code"] == expected_code for error in report["errors"])


def test_scorecard_refuse_un_claim_supporte_absent_des_claims():
    gold, predictions = _perfect_holdout()
    predictions["decision"][0]["prediction"]["supported_claims"] = ["not-claimed"]

    report = score_holdout(UNIT_MANIFEST, gold, predictions, run_id=RUN_ID)

    assert report["status"] == "not_measurable"
    assert any(
        error["code"] == "QL006_PREDICTION_SCHEMA_INVALID"
        for error in report["errors"]
    )


def test_zero_denominateur_ne_devient_jamais_vert():
    gold, predictions = _perfect_holdout()
    gold["entity_resolution"] = [gold["entity_resolution"][0]]
    predictions["entity_resolution"] = [predictions["entity_resolution"][0]]

    report = score_holdout(UNIT_MANIFEST, gold, predictions, run_id=RUN_ID)

    assert report["status"] == "not_measurable"
    assert report["measurable"] is False
    assert any(
        error["code"] == "QL013_METRIC_NOT_MEASURABLE"
        for error in report["errors"]
    )


def test_erreurs_scorecard_sont_triees_deterministiquement():
    gold, predictions = _perfect_holdout()
    predictions["entity_resolution"] = []
    predictions["variant_resolution"] = []

    report = score_holdout(UNIT_MANIFEST, gold, predictions, run_id=RUN_ID)
    keys = [
        (
            error["code"],
            error.get("dataset", ""),
            error.get("case_id", ""),
            error.get("path", ""),
        )
        for error in report["errors"]
    ]

    assert keys == sorted(keys)


def test_les_quinze_codes_erreur_sont_uniques_et_stables():
    assert list(ERROR_CODES.values()) == [
        "QL001_MANIFEST_INVALID",
        "QL002_GOLD_NOT_READY",
        "QL003_HOLDOUT_SPLIT_MISMATCH",
        "QL004_GOLD_DIGEST_MISMATCH",
        "QL005_RUN_SCHEMA_INVALID",
        "QL006_PREDICTION_SCHEMA_INVALID",
        "QL007_DUPLICATE_CASE_ID",
        "QL008_MISSING_CASE_ID",
        "QL009_UNEXPECTED_CASE_ID",
        "QL010_CASE_FINGERPRINT_MISMATCH",
        "QL011_CONFIDENCE_INVALID",
        "QL012_DUPLICATE_RANKED_ID",
        "QL013_METRIC_NOT_MEASURABLE",
        "QL014_METRIC_OUT_OF_RANGE",
        "QL015_REQUIRED_GATE_MISSING",
    ]
    assert len(set(ERROR_CODES.values())) == 15


def test_un_gate_absent_reste_ql015_pas_une_erreur_manifest_generique(tmp_path):
    manifest = deepcopy(MANIFEST)
    del manifest["gates"]["calibration_ece_max"]
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = build_scorecard(manifest_path, tmp_path / "unused-run.json")

    assert report["status"] == "not_measurable"
    assert {error["code"] for error in report["errors"]} == {
        "QL015_REQUIRED_GATE_MISSING"
    }


@pytest.mark.parametrize("value", [1.01, float("nan")])
def test_une_metrique_impossible_est_ql014_pas_un_simple_gate_rate(value):
    metrics = {
        "category_accuracy_ci95_lower": 1.0,
        "subcategory_accuracy_ci95_lower": 1.0,
        "product_role_accuracy_ci95_lower": 1.0,
        "entity_match_accuracy_ci95_lower": 1.0,
        "false_merge_rate_ci95_upper": value,
        "false_split_rate_ci95_upper": 0.0,
        "entity_variant_relation_accuracy_ci95_lower": 1.0,
        "variant_resolution_accuracy_ci95_lower": 1.0,
        "offer_attachment_accuracy_ci95_lower": 1.0,
        "offer_eligibility_accuracy_ci95_lower": 1.0,
        "false_eligible_offers": 0,
        "price_accuracy_ci95_lower": 1.0,
        "stock_accuracy_ci95_lower": 1.0,
        "shipping_accuracy_ci95_lower": 1.0,
        "affiliate_link_accuracy_ci95_lower": 1.0,
        "retrieval_top_3_relevance_ci95_lower": 1.0,
        "exact_product_match_accuracy_ci95_lower": 1.0,
        "absurd_result_rate_ci95_upper": 0.0,
        "retrieval_recall_at_50_ci95_lower": 1.0,
        "retrieval_ndcg_at_10_ci95_lower": 1.0,
        "retrieval_no_match_accuracy_ci95_lower": 1.0,
        "retrieval_ambiguous_accuracy_ci95_lower": 1.0,
        "retrieval_constraint_violations_at_10": 0,
        "constraint_violations": 0,
        "unsupported_claims": 0,
        "calibration_ece_ci95_upper": 0.0,
        "sourced_explanation_coverage_ci95_lower": 1.0,
    }

    gates, errors = _evaluate_gates(MANIFEST, metrics)

    assert any(error["code"] == "QL014_METRIC_OUT_OF_RANGE" for error in errors)
    assert next(
        gate
        for gate in gates
        if gate["metric"] == "false_merge_rate_ci95_upper"
    )["passed"] is None


def test_retrieval_and_calibration_gates_use_conservative_interval_bounds():
    metrics = {
        "category_accuracy_ci95_lower": 1.0,
        "subcategory_accuracy_ci95_lower": 1.0,
        "product_role_accuracy_ci95_lower": 1.0,
        "entity_match_accuracy_ci95_lower": 1.0,
        "false_merge_rate_ci95_upper": 0.0,
        "false_split_rate_ci95_upper": 0.0,
        "entity_variant_relation_accuracy_ci95_lower": 1.0,
        "variant_resolution_accuracy_ci95_lower": 1.0,
        "offer_attachment_accuracy_ci95_lower": 1.0,
        "offer_eligibility_accuracy_ci95_lower": 1.0,
        "false_eligible_offers": 0,
        "price_accuracy_ci95_lower": 1.0,
        "stock_accuracy_ci95_lower": 1.0,
        "shipping_accuracy_ci95_lower": 1.0,
        "affiliate_link_accuracy_ci95_lower": 1.0,
        "retrieval_top_3_relevance_ci95_lower": 1.0,
        "exact_product_match_accuracy_ci95_lower": 0.97,
        "absurd_result_rate_ci95_upper": 0.02,
        "retrieval_recall_at_50_ci95_lower": 0.94,
        "retrieval_ndcg_at_10_ci95_lower": 0.84,
        "retrieval_no_match_accuracy_ci95_lower": 1.0,
        "retrieval_ambiguous_accuracy_ci95_lower": 1.0,
        "retrieval_constraint_violations_at_10": 0,
        "constraint_violations": 0,
        "unsupported_claims": 0,
        "calibration_ece_ci95_upper": 0.06,
        "sourced_explanation_coverage_ci95_lower": 1.0,
    }

    gates, errors = _evaluate_gates(MANIFEST, metrics)

    assert errors == []
    by_name = {gate["gate"]: gate for gate in gates}
    assert by_name["retrieval_recall_at_50_min"]["passed"] is False
    assert by_name["retrieval_ndcg_at_10_min"]["passed"] is False
    assert by_name["exact_product_match_accuracy_min"]["passed"] is False
    assert by_name["absurd_result_rate_max"]["passed"] is False
    assert by_name["calibration_ece_max"]["passed"] is False
    assert by_name["exact_product_match_accuracy_min"]["metric"].endswith(
        "ci95_lower"
    )
    assert by_name["absurd_result_rate_max"]["metric"].endswith("ci95_upper")
    assert by_name["absurd_result_rate_max"]["operator"] == "lt"
    assert by_name["retrieval_recall_at_50_min"]["metric"].endswith("ci95_lower")
    assert by_name["calibration_ece_max"]["metric"].endswith("ci95_upper")


def test_absurd_result_rate_gate_is_strictly_below_one_percent():
    metrics = {
        metric_name: (0 if operator in {"max", "lt"} else 1.0)
        for metric_name, operator in scorecard_module._GATE_METRICS.values()
    }
    metrics["absurd_result_rate_ci95_upper"] = 0.01

    gates, errors = _evaluate_gates(MANIFEST, metrics)

    assert errors == []
    absurd = next(gate for gate in gates if gate["gate"] == "absurd_result_rate_max")
    assert absurd["operator"] == "lt"
    assert absurd["passed"] is False


def test_train_est_exclu_du_holdout_et_devient_extra_si_predit():
    gold, predictions = _perfect_holdout()
    group_id = next(
        f"entity-train-{index}"
        for index in range(10_000)
        if split_for_group(f"entity-train-{index}") == "train"
    )
    train = {
        "dataset": "entity_resolution",
        "case_id": "entity-train",
        "group_id": group_id,
        "split": "train",
        "gold": {"product_relation": "same", "variant_relation": "same"},
    }
    train["case_fingerprint"] = case_fingerprint(train)
    gold["entity_resolution"].append(train)

    passing = score_holdout(UNIT_MANIFEST, gold, predictions, run_id=RUN_ID)
    assert passing["status"] == "pass"
    assert passing["holdout"]["entity_resolution"]["gold_cases"] == 2

    predictions["entity_resolution"].append(_prediction(train, train["gold"]))
    rejected = score_holdout(UNIT_MANIFEST, gold, predictions, run_id=RUN_ID)
    assert rejected["status"] == "not_measurable"
    assert any(
        error["code"] == "QL009_UNEXPECTED_CASE_ID"
        and error.get("case_id") == "entity-train"
        for error in rejected["errors"]
    )


def test_build_scorecard_refuse_honnetement_le_gold_reel_absent(tmp_path):
    missing_run = tmp_path / "missing-run.json"
    report = build_scorecard(QUALITY / "manifest.json", missing_run)

    assert report["status"] == "not_measurable"
    assert report["metrics"] == {}
    assert report["errors"][0]["code"] == "QL002_GOLD_NOT_READY"


def test_scorecard_et_cli_refusent_un_manifeste_trop_profond_sans_crasher(
    tmp_path, monkeypatch, capsys
):
    manifest_path = tmp_path / "manifest.json"
    deep_value = "[" * 1_200 + "0" + "]" * 1_200
    base_manifest = (QUALITY / "manifest.json").read_text(encoding="utf-8").rstrip()
    manifest_path.write_text(
        base_manifest[:-1] + ',"extra":' + deep_value + "}",
        encoding="utf-8",
    )
    run_path = tmp_path / "run.json"
    run_path.write_text("{}", encoding="utf-8")

    report = build_scorecard(manifest_path, run_path)

    assert report["status"] == "not_measurable"
    assert {error["code"] for error in report["errors"]} == {
        "QL001_MANIFEST_INVALID"
    }

    monkeypatch.setattr(
        sys,
        "argv",
        [
            evaluate_module.__name__,
            "--manifest",
            str(manifest_path),
            "--run",
            str(run_path),
        ],
    )
    assert evaluate_module.main() == 2
    cli_report = json.loads(capsys.readouterr().out)
    assert {error["code"] for error in cli_report["errors"]} == {
        "QL001_MANIFEST_INVALID"
    }


@pytest.mark.parametrize("module", [scorecard_module, evaluate_module])
def test_cli_refuse_d_ecraser_son_run_input(tmp_path, monkeypatch, module):
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text("{}", encoding="utf-8")
    run_path = tmp_path / "run.json"
    original = '{"sentinel":"run-input"}\n'
    run_path.write_text(original, encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            module.__name__,
            "--manifest",
            str(manifest_path),
            "--run",
            str(run_path),
            "--output",
            str(run_path),
        ],
    )

    with pytest.raises(SystemExit) as exc_info:
        module.main()

    assert exc_info.value.code == 2
    assert run_path.read_text(encoding="utf-8") == original


def test_les_schemas_effectivement_lus_sont_proteges_des_outputs():
    protected = quality_input_paths(QUALITY / "manifest.json")

    assert (QUALITY / "schemas/manifest.schema.json").resolve() in protected
    assert (QUALITY / "schemas/prediction.schema.json").resolve() in protected
    assert (QUALITY / "schemas/run-manifest.schema.json").resolve() in protected


def test_collision_output_casefold_est_refusee_avant_creation(tmp_path):
    with pytest.raises(ValueError, match="overwrite input"):
        ensure_output_is_distinct(
            tmp_path / "Result.json",
            [tmp_path / "result.json"],
        )


def test_ecriture_atomique_de_rapport_preserve_la_cible_si_replace_echoue(
    tmp_path, monkeypatch
):
    from quality_lab import integrity

    output = tmp_path / "report.json"
    output.write_text("ancien\n", encoding="utf-8")

    def fail_replace(_source, _target):
        raise OSError("replace failed")

    monkeypatch.setattr(integrity.os, "replace", fail_replace)
    with pytest.raises(OSError, match="replace failed"):
        atomic_write_text(output, "nouveau\n")

    assert output.read_text(encoding="utf-8") == "ancien\n"
    assert list(tmp_path.glob(".report.json.*.tmp")) == []


def _source_case_label(
    dataset: str,
    suffix: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    case_id = f"{dataset}-{suffix}"
    stratum_order = {
        ("taxonomy", "case"): 7,
        ("entity_resolution", "same"): 1,
        ("entity_resolution", "different"): 2,
        ("variant_resolution", "case"): 3,
        ("offer_attachment", "eligible"): 4,
        ("offer_attachment", "reject"): 5,
        ("offer_truth", "case"): 6,
        ("retrieval", "matched"): 0,
        ("retrieval", "no-match"): 9,
        ("retrieval", "ambiguous"): 8,
        ("decision", "case"): 10,
    }
    stratum_index = stratum_order.get(
        (dataset, suffix),
        SCENARIO_TYPES.index(suffix)
        if dataset == "retrieval" and suffix in SCENARIO_TYPES
        else 0,
    )
    common = {
        "case_id": case_id,
        "group_id": _test_group(case_id),
        "strata": {
            "scenario_type": SCENARIO_TYPES[stratum_index % len(SCENARIO_TYPES)],
            "language": LANGUAGES[stratum_index % len(LANGUAGES)],
            "vertical": VERTICALS[stratum_index % len(VERTICALS)],
        },
    }
    if dataset == "taxonomy":
        return (
            {**common, "observation": {"name": "Product"}},
            {
                "category": "electronics",
                "subcategory": "smartphones",
                "product_role": "primary_product",
            },
        )
    if dataset == "entity_resolution":
        relation = "same" if suffix == "same" else "different"
        variant_relation = "same" if relation == "same" else "not_applicable"
        return (
            {
                **common,
                "left": {"source_ref": f"{case_id}-left", "name": "A"},
                "right": {"source_ref": f"{case_id}-right", "name": "B"},
            },
            {
                "product_relation": relation,
                "variant_relation": variant_relation,
            },
        )
    if dataset == "variant_resolution":
        return (
            {**common, "observation": {"name": "Variant"}},
            {
                "expected_variant": {
                    "variant_key": "variant-1",
                    "attributes": {"size": "42"},
                    "resolution": "resolved",
                }
            },
        )
    if dataset == "offer_attachment":
        if suffix == "reject":
            return (
                {**common, "offer": {"sku": "sku-reject"}},
                {"expected_variant_id": None, "eligibility": "reject"},
            )
        return (
            {**common, "offer": {"sku": "sku-1"}},
            {"expected_variant_id": "variant-1", "eligibility": "eligible"},
        )
    if dataset == "offer_truth":
        return (
            {**common, "offer": {"source_ref": "merchant:item-1"}},
            {
                "price": {"amount_minor": 99900, "currency": "EUR"},
                "stock": "in_stock",
                "shipping": {"amount_minor": 0, "currency": "EUR"},
                "affiliate_link": "https://merchant.example/item-1",
            },
        )
    if dataset == "retrieval":
        resolution = {
            "no-match": "no_match",
            "ambiguous": "ambiguous",
        }.get(suffix, "matched")
        return (
            {
                **common,
                "locale": common["strata"]["language"],
                "query": f"query {suffix}",
                "hard_constraints": {},
            },
            {
                "resolution": resolution,
                "relevant_product_ids": (
                    ["product-1"] if resolution == "matched" else []
                ),
                "exact_product_ids": (
                    ["product-1"]
                    if resolution == "matched"
                    and common["strata"]["scenario_type"] == "exact_product"
                    else []
                ),
                "constraint_violating_product_ids": [],
            },
        )
    return (
        {
            **common,
            **_decision_input(language=common["strata"]["language"]),
        },
        {
            "acceptable_outcomes": ["recommend"],
            "forbidden_claims": [],
            "claim_evidence": [
                {"claim": "source-confirmed", "evidence_refs": ["catalog:p1"]}
            ],
        },
    )


def _full_record(dataset: str, suffix: str = "case") -> dict[str, Any]:
    case, label = _source_case_label(dataset, suffix)
    packs = []
    for annotator in ("human-a", "human-b"):
        pack = prepare_pack(dataset, [case], annotator_id=f"{dataset}-{annotator}")
        pack[0]["annotation"].update(label=deepcopy(label), confidence="certain")
        packs.extend(pack)
    result = merge_completed_packs(dataset, packs)
    assert result.errors == ()
    return result.accepted[0]


def _write_ready_quality(tmp_path: Path) -> tuple[Path, dict[str, list[dict[str, Any]]]]:
    quality = tmp_path / "quality"
    (quality / "schemas").mkdir(parents=True)
    (quality / "datasets").mkdir()
    for name in (*SCHEMA_FILES.values(), "manifest.schema.json", "prediction.schema.json", "run-manifest.schema.json"):
        (quality / "schemas" / name).write_text(
            (QUALITY / "schemas" / name).read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    manifest_schema_path = quality / "schemas" / "manifest.schema.json"
    manifest_schema = json.loads(manifest_schema_path.read_text(encoding="utf-8"))
    for dataset in DATASETS:
        properties = manifest_schema["$defs"][f"{dataset}_config"]["properties"]
        properties["minimum_cases"] = {"const": 1}
        properties["minimum_test_cases"] = {"const": 1}
    manifest_schema_path.write_text(json.dumps(manifest_schema), encoding="utf-8")

    manifest = deepcopy(UNIT_MANIFEST)
    records = {dataset: [_full_record(dataset)] for dataset in DATASETS}
    records["entity_resolution"] = [
        _full_record("entity_resolution", "same"),
        _full_record("entity_resolution", "different"),
    ]
    records["offer_attachment"] = [
        _full_record("offer_attachment", "eligible"),
        _full_record("offer_attachment", "reject"),
    ]
    records["retrieval"] = [
        _full_record("retrieval", "matched"),
        *[
            _full_record("retrieval", SCENARIO_TYPES[index])
            for index in range(1, 8)
        ],
        _full_record("retrieval", "no-match"),
        _full_record("retrieval", "ambiguous"),
    ]
    for dataset in DATASETS:
        manifest["datasets"][dataset]["minimum_cases"] = 1
        manifest["datasets"][dataset]["minimum_test_cases"] = 1
        schema_path = quality / manifest["datasets"][dataset]["schema"]
        manifest["datasets"][dataset]["schema_fingerprint"] = (
            schema_value_fingerprint(
                dataset,
                json.loads(schema_path.read_text(encoding="utf-8")),
            )
        )
        dataset_path = quality / manifest["datasets"][dataset]["path"]
        dataset_path.write_text(
            "".join(canonical_json(record) + "\n" for record in records[dataset]),
            encoding="utf-8",
        )
    manifest["bootstrap"]["path"] = "datasets/missing-bootstrap.json"
    manifest_path = quality / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path, records


def _write_run(
    tmp_path: Path,
    manifest_path: Path,
    records: dict[str, list[dict[str, Any]]],
) -> Path:
    run_root = tmp_path / "run"
    run_root.mkdir()
    adapters = {
        dataset: {
            "engine_id": f"tests.{dataset}",
            "engine_version": "v1",
        }
        for dataset in DATASETS
    }
    outputs: dict[str, list[dict[str, Any]]] = {}
    for dataset in DATASETS:
        predictions: list[dict[str, Any]] = []
        for record in records[dataset]:
            gold = record["gold"]
            if dataset in {
                "taxonomy",
                "entity_resolution",
                "variant_resolution",
                "offer_attachment",
                "offer_truth",
            }:
                value = gold
            elif dataset == "retrieval":
                value = {
                    "resolution": gold["resolution"],
                    "retrieved_product_ids": gold["relevant_product_ids"],
                }
            else:
                value = {
                    "outcome": gold["acceptable_outcomes"][0],
                    "claims": [
                        {
                            "claim": "source-confirmed",
                            "evidence_refs": ["catalog:p1"],
                        }
                    ],
                }
            predictions.append(_prediction(record, value))
        outputs[dataset] = predictions
    run_id = quality_run_id(
        system_version="test-system",
        evaluator_version="0.5.0",
        gold_manifest_sha256=sha256_file(manifest_path),
        outputs=outputs,
        adapters=adapters,
    )
    configs: dict[str, dict[str, str]] = {}
    for dataset in DATASETS:
        predictions = outputs[dataset]
        for prediction in predictions:
            prediction["run_id"] = run_id
        path = run_root / f"{dataset}.jsonl"
        path.write_text(
            "".join(canonical_json(row) + "\n" for row in predictions),
            encoding="utf-8",
        )
        configs[dataset] = {"path": path.name, "sha256": sha256_file(path)}
    run = {
        "schema_version": "quality-run/v1",
        "run_id": run_id,
        "system_version": "test-system",
        "evaluator_version": "0.5.0",
        "gold_manifest_sha256": sha256_file(manifest_path),
        "adapters": adapters,
        "datasets": configs,
    }
    run_path = run_root / "run.json"
    run_path.write_text(json.dumps(run), encoding="utf-8")
    return run_path


def _mutate_prediction_file(
    run_path: Path,
    dataset: str,
    mutate,
) -> None:
    run = json.loads(run_path.read_text(encoding="utf-8"))
    path = run_path.parent / run["datasets"][dataset]["path"]
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    mutate(rows)
    path.write_text(
        "".join(canonical_json(row) + "\n" for row in rows),
        encoding="utf-8",
    )
    run["datasets"][dataset]["sha256"] = sha256_file(path)
    run_path.write_text(json.dumps(run), encoding="utf-8")


def test_build_scorecard_valide_digests_schemas_et_holdout(tmp_path):
    manifest_path, records = _write_ready_quality(tmp_path)
    run_path = _write_run(tmp_path, manifest_path, records)

    report = build_scorecard(manifest_path, run_path)

    assert report["status"] == "pass"
    assert report["system_version"] == "test-system"
    assert report["gold_manifest_sha256"] == sha256_file(manifest_path)
    assert report["run_id"].startswith("filon-quality-")
    assert FINGERPRINT_PATTERN.fullmatch(report["holdout_fingerprint"])
    assert set(report["adapters"]) == set(DATASETS)


@pytest.mark.parametrize(
    "tamper",
    [
        lambda run: run.__setitem__("system_version", "tampered-system"),
        lambda run: run.__setitem__("run_id", "tampered-run"),
        lambda run: run["adapters"]["taxonomy"].__setitem__(
            "engine_version", "tampered-engine"
        ),
        lambda run: run["adapters"].pop("taxonomy"),
    ],
    ids=["system-version", "run-id", "engine-version", "adapter-roster"],
)
def test_build_scorecard_refuse_une_provenance_run_falsifiee(tmp_path, tamper):
    manifest_path, records = _write_ready_quality(tmp_path)
    run_path = _write_run(tmp_path, manifest_path, records)
    run = json.loads(run_path.read_text(encoding="utf-8"))
    tamper(run)
    run_path.write_text(json.dumps(run), encoding="utf-8")

    report = build_scorecard(manifest_path, run_path)

    assert report["status"] == "not_measurable"
    assert {error["code"] for error in report["errors"]} == {
        "QL005_RUN_SCHEMA_INVALID"
    }


def test_build_scorecard_refuse_une_prediction_valide_reliee_a_un_ancien_run(
    tmp_path,
):
    manifest_path, records = _write_ready_quality(tmp_path)
    run_path = _write_run(tmp_path, manifest_path, records)
    _mutate_prediction_file(
        run_path,
        "taxonomy",
        lambda rows: rows[0]["prediction"].__setitem__(
            "category", "tampered-category"
        ),
    )

    report = build_scorecard(manifest_path, run_path)

    assert report["status"] == "not_measurable"
    assert {error["code"] for error in report["errors"]} == {
        "QL005_RUN_SCHEMA_INVALID"
    }


def test_build_scorecard_refuse_un_digest_gold_divergent(tmp_path):
    manifest_path, records = _write_ready_quality(tmp_path)
    run_path = _write_run(tmp_path, manifest_path, records)
    run = json.loads(run_path.read_text(encoding="utf-8"))
    run["gold_manifest_sha256"] = "sha256:" + "0" * 64
    run_path.write_text(json.dumps(run), encoding="utf-8")

    report = build_scorecard(manifest_path, run_path)

    assert report["status"] == "not_measurable"
    assert report["errors"][0]["code"] == "QL004_GOLD_DIGEST_MISMATCH"


def test_build_scorecard_refuse_un_digest_prediction_divergent(tmp_path):
    manifest_path, records = _write_ready_quality(tmp_path)
    run_path = _write_run(tmp_path, manifest_path, records)
    run = json.loads(run_path.read_text(encoding="utf-8"))
    prediction_path = run_path.parent / run["datasets"]["decision"]["path"]
    prediction_path.write_text(
        prediction_path.read_text(encoding="utf-8") + "\n",
        encoding="utf-8",
    )

    report = build_scorecard(manifest_path, run_path)

    assert report["status"] == "not_measurable"
    assert {error["code"] for error in report["errors"]} == {
        "QL005_RUN_SCHEMA_INVALID"
    }


@pytest.mark.parametrize(
    "dataset, mutate, expected_code",
    [
        (
            "variant_resolution",
            lambda rows: rows[0].__setitem__("confidence", True),
            "QL011_CONFIDENCE_INVALID",
        ),
        (
            "retrieval",
            lambda rows: rows[0]["prediction"].__setitem__(
                "retrieved_product_ids", ["product-1", "product-1"]
            ),
            "QL012_DUPLICATE_RANKED_ID",
        ),
        (
            "decision",
            lambda rows: rows[0].pop("prediction"),
            "QL006_PREDICTION_SCHEMA_INVALID",
        ),
        (
            "entity_resolution",
            lambda rows: rows.pop(),
            "QL008_MISSING_CASE_ID",
        ),
        (
            "entity_resolution",
            lambda rows: rows.append(deepcopy(rows[0])),
            "QL007_DUPLICATE_CASE_ID",
        ),
        (
            "offer_attachment",
            lambda rows: rows[0].__setitem__(
                "case_fingerprint", "sha256:" + "0" * 64
            ),
            "QL010_CASE_FINGERPRINT_MISMATCH",
        ),
    ],
)
def test_build_scorecard_codes_specialises_sont_exclusifs(
    tmp_path,
    dataset,
    mutate,
    expected_code,
):
    manifest_path, records = _write_ready_quality(tmp_path)
    run_path = _write_run(tmp_path, manifest_path, records)
    _mutate_prediction_file(run_path, dataset, mutate)

    report = build_scorecard(manifest_path, run_path)

    assert report["status"] == "not_measurable"
    assert report["metrics"] == {}
    assert report["gates"] == []
    assert {error["code"] for error in report["errors"]} == {expected_code}
