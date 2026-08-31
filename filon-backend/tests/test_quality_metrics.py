from __future__ import annotations

import math

import pytest

from quality_lab.metrics import (
    attachment_metrics,
    calibration_metrics,
    decision_safety_metrics,
    entity_resolution_metrics,
    offer_truth_metrics,
    retrieval_metrics,
    strata_metrics,
    taxonomy_metrics,
    variant_resolution_metrics,
)


def test_entity_abstentions_are_fail_closed_on_determinate_gold():
    metrics = entity_resolution_metrics(
        [
            {"actual": "different", "predicted": "ambiguous"},
            {"actual": "different", "predicted": "abstain"},
            {"actual": "different"},
            {"actual": "same", "predicted": "ambiguous"},
            {"actual": "ambiguous", "predicted": "same"},
        ]
    )

    assert metrics["evaluated"] == 4
    assert metrics["excluded_ambiguous"] == 1
    assert metrics["abstained_predictions"] == 4
    assert metrics["false_merges"] == 3
    assert metrics["false_merge_rate"] == 1.0
    assert metrics["false_splits"] == 1
    assert metrics["false_split_rate"] == 1.0
    assert metrics["entity_match_accuracy"] == 0.0


def test_taxonomy_dimensions_are_measured_independently():
    metrics = taxonomy_metrics(
        [
            {
                "expected": {
                    "category": "electronics",
                    "subcategory": "smartphones",
                    "product_role": "primary_product",
                },
                "predicted": {
                    "category": "electronics",
                    "subcategory": "laptops",
                    "product_role": "primary_product",
                },
            }
        ]
    )

    assert metrics["category_accuracy"] == 1.0
    assert metrics["subcategory_accuracy"] == 0.0
    assert metrics["product_role_accuracy"] == 1.0
    assert metrics["category_accuracy_ci95"] is not None


def test_offer_truth_dimensions_use_exact_unknown_safe_values():
    metrics = offer_truth_metrics(
        [
            {
                "expected": {
                    "price": {"amount_minor": 10000, "currency": "EUR"},
                    "stock": "in_stock",
                    "shipping": None,
                    "affiliate_link": None,
                },
                "predicted": {
                    "price": {"amount_minor": 9999, "currency": "EUR"},
                    "stock": "in_stock",
                    "shipping": None,
                    "affiliate_link": "https://merchant.example/item",
                },
            }
        ]
    )

    assert metrics["price_accuracy"] == 0.0
    assert metrics["stock_accuracy"] == 1.0
    assert metrics["shipping_accuracy"] == 1.0
    assert metrics["affiliate_link_accuracy"] == 0.0


def test_strata_support_counts_scenario_language_and_vertical_fail_closed():
    metrics = strata_metrics(
        [
            {
                "scenario_type": "exact_product",
                "language": "fr",
                "vertical": "smartphones",
            },
            {
                "scenario_type": "no_match",
                "language": "nl",
                "vertical": "laptops",
            },
        ]
    )

    assert metrics["scenario_counts"]["exact_product"] == 1
    assert metrics["scenario_counts"]["no_match"] == 1
    assert metrics["language_counts"]["en"] == 0
    assert metrics["vertical_counts"]["smartphones"] == 1
    with pytest.raises(ValueError, match="unsupported language"):
        strata_metrics(
            [
                {
                    "scenario_type": "exact_product",
                    "language": "de",
                    "vertical": "smartphones",
                }
            ]
        )


def test_entity_variant_relation_is_measured_and_invalid_gold_is_rejected():
    metrics = entity_resolution_metrics(
        [
            {
                "actual": "same",
                "predicted": "same",
                "actual_variant": "different",
                "predicted_variant": "same",
            }
        ]
    )

    assert metrics["variant_pairs"] == 1
    assert metrics["variant_relation_accuracy"] == 0.0
    with pytest.raises(ValueError, match="field 'actual'"):
        entity_resolution_metrics([{"actual": "typo", "predicted": "same"}])


def test_entity_variant_support_excludes_not_applicable_product_pairs():
    metrics = entity_resolution_metrics(
        [
            {
                "actual": "different",
                "predicted": "different",
                "actual_variant": "not_applicable",
                "predicted_variant": "not_applicable",
            }
        ]
    )

    assert metrics["variant_pairs"] == 0
    assert metrics["variant_excluded_not_applicable"] == 1
    assert metrics["variant_relation_accuracy"] is None


def test_attachment_scores_only_gold_eligible_offers():
    metrics = attachment_metrics(
        [
            {
                "eligibility": "eligible",
                "expected_variant_id": "v1",
                "predicted_variant_id": "wrong",
            },
            {
                "eligibility": "quarantine",
                "expected_variant_id": None,
                "predicted_variant_id": None,
                "predicted_eligibility": "quarantine",
            },
            {
                "eligibility": "reject",
                "expected_variant_id": None,
                "predicted_variant_id": None,
                "predicted_eligibility": "reject",
            },
        ]
    )

    assert metrics["evaluated"] == 1
    assert metrics["correct"] == 0
    assert metrics["accuracy"] == 0.0
    assert metrics["offers"] == 3
    assert metrics["eligibility_accuracy"] == 1.0
    assert metrics["false_eligible_offers"] == 0


def test_attachment_without_eligible_gold_is_not_green():
    metrics = attachment_metrics(
        [
            {
                "eligibility": "reject",
                "expected_variant_id": None,
                "predicted_variant_id": None,
                "predicted_eligibility": "reject",
            }
        ]
    )

    assert metrics["evaluated"] == 0
    assert metrics["accuracy"] is None
    assert metrics["offers"] == 1
    assert metrics["eligibility_accuracy"] == 1.0
    assert metrics["noneligible_offers"] == 1
    assert metrics["false_eligible_offers"] == 0


def test_attachment_requires_the_prediction_to_keep_an_eligible_offer_eligible():
    metrics = attachment_metrics(
        [
            {
                "eligibility": "eligible",
                "expected_variant_id": "v1",
                "predicted_variant_id": "v1",
                "predicted_eligibility": "quarantine",
            }
        ]
    )

    assert metrics["evaluated"] == 1
    assert metrics["accuracy"] == 0.0


def test_attachment_counts_false_eligible_noneligible_offers():
    metrics = attachment_metrics(
        [
            {
                "eligibility": "reject",
                "expected_variant_id": None,
                "predicted_variant_id": "invented",
                "predicted_eligibility": "eligible",
            }
        ]
    )

    assert metrics["offers"] == 1
    assert metrics["eligibility_accuracy"] == 0.0
    assert metrics["false_eligible_offers"] == 1


def test_variant_resolution_requires_an_exact_structured_match():
    expected = {
        "variant_key": "shoe-black-42",
        "attributes": {"colour": "black", "size": "42"},
        "resolution": "resolved",
    }
    metrics = variant_resolution_metrics(
        [
            {"expected_variant": expected, "predicted_variant": dict(expected)},
            {
                "expected_variant": expected,
                "predicted_variant": {
                    **expected,
                    "attributes": {"colour": "black", "size": "43"},
                },
            },
        ]
    )

    assert metrics["evaluated"] == 2
    assert metrics["exact_matches"] == 1
    assert metrics["exact_match_accuracy"] == 0.5
    assert metrics["exact_match_ci95"] is not None
    assert variant_resolution_metrics([])["exact_match_accuracy"] is None


def test_variant_resolution_exact_match_does_not_coerce_booleans_to_numbers():
    metrics = variant_resolution_metrics(
        [
            {
                "expected_variant": {
                    "variant_key": "v1",
                    "attributes": {"size": 1},
                    "resolution": "resolved",
                },
                "predicted_variant": {
                    "variant_key": "v1",
                    "attributes": {"size": True},
                    "resolution": "resolved",
                },
            }
        ]
    )

    assert metrics["exact_matches"] == 0
    assert metrics["exact_match_accuracy"] == 0.0


def test_variant_resolution_exact_match_unifies_json_number_representations():
    metrics = variant_resolution_metrics(
        [
            {
                "expected_variant": {
                    "variant_key": "v1",
                    "attributes": {"size": 1},
                    "resolution": "resolved",
                },
                "predicted_variant": {
                    "variant_key": "v1",
                    "attributes": {"size": 1.0},
                    "resolution": "resolved",
                },
            }
        ]
    )

    assert metrics["exact_matches"] == 1
    assert metrics["exact_match_accuracy"] == 1.0


@pytest.mark.parametrize(
    "case",
    [
        {"retrieved_product_ids": []},
        {"relevant_product_ids": ["p1"]},
    ],
)
def test_retrieval_requires_both_gold_and_ranking_fields(case):
    with pytest.raises(ValueError, match="missing required field"):
        retrieval_metrics([case])


def test_retrieval_rejects_duplicate_rankings_instead_of_inflating_ndcg():
    with pytest.raises(ValueError, match="must not contain duplicates"):
        retrieval_metrics(
            [
                {
                    "actual_resolution": "matched",
                    "predicted_resolution": "matched",
                    "relevant_product_ids": ["p1"],
                    "exact_product_ids": [],
                    "retrieved_product_ids": ["p1", "p1"],
                    "constraint_violating_product_ids": [],
                    "scenario_type": "generic_product",
                }
            ]
        )


def test_retrieval_rejects_relevant_constraint_overlap():
    with pytest.raises(ValueError, match="must be disjoint"):
        retrieval_metrics(
            [
                {
                    "actual_resolution": "matched",
                    "predicted_resolution": "matched",
                    "relevant_product_ids": ["p1"],
                    "exact_product_ids": [],
                    "retrieved_product_ids": ["p1"],
                    "constraint_violating_product_ids": ["p1"],
                    "scenario_type": "generic_product",
                }
            ]
        )


def test_retrieval_ndcg_is_bounded_and_empty_gold_is_not_green():
    metrics = retrieval_metrics(
        [
            {
                "actual_resolution": "matched",
                "predicted_resolution": "matched",
                "relevant_product_ids": ["p1", "p2"],
                "exact_product_ids": [],
                "retrieved_product_ids": ["p2", "x", "p1"],
                "constraint_violating_product_ids": [],
                "scenario_type": "generic_product",
            }
        ],
        ndcg_k=3,
    )
    empty = retrieval_metrics(
        [
            {
                "actual_resolution": "no_match",
                "predicted_resolution": "no_match",
                "relevant_product_ids": [],
                "exact_product_ids": [],
                "retrieved_product_ids": [],
                "constraint_violating_product_ids": [],
                "scenario_type": "no_match",
            }
        ]
    )

    assert 0.0 <= metrics["ndcg_at_3"] <= 1.0
    assert empty["queries"] == 0
    assert empty["precision_at_1"] is None
    assert empty["precision_at_3"] is None
    assert empty["precision_at_5"] is None
    assert empty["recall_at_10"] is None
    assert empty["recall_at_50"] is None
    assert empty["recall_at_50_ci95"] is None
    assert empty["ndcg_at_10"] is None
    assert empty["ndcg_at_10_ci95"] is None
    assert empty["constraint_violations_at_10"] == 0
    assert empty["no_match_accuracy"] == 1.0


def test_retrieval_counts_gold_backed_constraint_violations_at_10():
    metrics = retrieval_metrics(
        [
            {
                "actual_resolution": "matched",
                "predicted_resolution": "matched",
                "relevant_product_ids": ["p1"],
                "exact_product_ids": [],
                "retrieved_product_ids": ["p1", "forbidden", "allowed"],
                "constraint_violating_product_ids": ["forbidden"],
                "scenario_type": "constraint_heavy",
            }
        ]
    )

    assert metrics["recall_at_50"] == 1.0
    assert metrics["constraint_violations_at_10"] == 1


def test_retrieval_no_match_hallucination_and_ambiguity_are_measured_fail_closed():
    metrics = retrieval_metrics(
        [
            {
                "actual_resolution": "no_match",
                "predicted_resolution": "matched",
                "relevant_product_ids": [],
                "exact_product_ids": [],
                "retrieved_product_ids": ["hallucinated"],
                "constraint_violating_product_ids": [],
                "scenario_type": "no_match",
            },
            {
                "actual_resolution": "ambiguous",
                "predicted_resolution": "ambiguous",
                "relevant_product_ids": [],
                "exact_product_ids": [],
                "retrieved_product_ids": [],
                "constraint_violating_product_ids": [],
                "scenario_type": "ambiguous",
            },
        ]
    )

    assert metrics["total_queries"] == 2
    assert metrics["answerable_queries"] == 0
    assert metrics["resolution_accuracy"] == 0.5
    assert metrics["no_match_accuracy"] == 0.0
    assert metrics["no_match_false_positive_queries"] == 1
    assert metrics["ambiguous_accuracy"] == 1.0


def test_retrieval_measures_exact_top1_and_absurd_results_with_wilson_bounds():
    metrics = retrieval_metrics(
        [
            {
                "actual_resolution": "matched",
                "predicted_resolution": "matched",
                "relevant_product_ids": ["p1"],
                "exact_product_ids": ["p1"],
                "retrieved_product_ids": ["p1"],
                "constraint_violating_product_ids": [],
                "scenario_type": "exact_product",
            },
            {
                "actual_resolution": "matched",
                "predicted_resolution": "matched",
                "relevant_product_ids": ["p2"],
                "exact_product_ids": ["p2"],
                "retrieved_product_ids": ["other", "p2"],
                "constraint_violating_product_ids": [],
                "scenario_type": "exact_product",
            },
            {
                "actual_resolution": "no_match",
                "predicted_resolution": "matched",
                "relevant_product_ids": [],
                "exact_product_ids": [],
                "retrieved_product_ids": ["absurd"],
                "constraint_violating_product_ids": [],
                "scenario_type": "no_match",
            },
            {
                "actual_resolution": "no_match",
                "predicted_resolution": "no_match",
                "relevant_product_ids": [],
                "exact_product_ids": [],
                "retrieved_product_ids": [],
                "constraint_violating_product_ids": [],
                "scenario_type": "no_match",
            },
        ]
    )

    assert metrics["exact_product_queries"] == 2
    assert metrics["exact_product_top1_correct"] == 1
    assert metrics["exact_product_match_accuracy"] == 0.5
    assert metrics["exact_product_match_accuracy_ci95"] is not None
    assert metrics["absurd_result_rate"] == 0.5
    assert metrics["absurd_result_rate_ci95"] is not None
    assert metrics["top_3_relevance_hits"] == 2
    assert metrics["top_3_relevance"] == 1.0
    assert metrics["top_3_relevance_ci95"] is not None


def test_retrieval_exact_top1_uses_only_closed_exact_equivalents():
    metrics = retrieval_metrics(
        [
            {
                "actual_resolution": "matched",
                "predicted_resolution": "matched",
                "relevant_product_ids": ["target", "substitute"],
                "exact_product_ids": ["target"],
                "retrieved_product_ids": ["substitute", "target"],
                "constraint_violating_product_ids": [],
                "scenario_type": "exact_product",
            }
        ]
    )

    assert metrics["exact_product_match_accuracy"] == 0.0
    assert metrics["top_3_relevance"] == 1.0


def test_retrieval_top_3_relevance_is_a_binary_hit_for_a_single_target():
    metrics = retrieval_metrics(
        [
            {
                "actual_resolution": "matched",
                "predicted_resolution": "matched",
                "relevant_product_ids": ["target"],
                "exact_product_ids": [],
                "retrieved_product_ids": ["noise-1", "noise-2", "target"],
                "constraint_violating_product_ids": [],
                "scenario_type": "generic_product",
            }
        ]
    )

    assert metrics["precision_at_3"] == pytest.approx(1 / 3)
    assert metrics["top_3_relevance_hits"] == 1
    assert metrics["top_3_relevance"] == 1.0


def test_retrieval_wilson_boundaries_match_declared_exact_and_no_match_supports():
    def exact_cases(correct: int) -> list[dict[str, object]]:
        return [
            {
                "actual_resolution": "matched",
                "predicted_resolution": "matched",
                "relevant_product_ids": [f"target-{index}"],
                "exact_product_ids": [f"target-{index}"],
                "retrieved_product_ids": (
                    [f"target-{index}"]
                    if index < correct
                    else [f"substitute-{index}", f"target-{index}"]
                ),
                "constraint_violating_product_ids": [],
                "scenario_type": "exact_product",
            }
            for index in range(300)
        ]

    exact_299 = retrieval_metrics(exact_cases(299))
    exact_298 = retrieval_metrics(exact_cases(298))
    assert exact_299["exact_product_match_accuracy_ci95"][0] >= 0.98
    assert exact_298["exact_product_match_accuracy_ci95"][0] < 0.98

    no_match_cases = [
        {
            "actual_resolution": "no_match",
            "predicted_resolution": "no_match" if index < 599 else "matched",
            "relevant_product_ids": [],
            "exact_product_ids": [],
            "retrieved_product_ids": [] if index < 599 else ["absurd"],
            "constraint_violating_product_ids": [],
            "scenario_type": "no_match",
        }
        for index in range(600)
    ]
    no_match_599 = retrieval_metrics(no_match_cases)
    assert no_match_599["no_match_accuracy_ci95"][0] >= 0.99
    assert no_match_599["absurd_result_rate_ci95"][1] < 0.01


def test_retrieval_rejects_an_unknown_scenario_type():
    with pytest.raises(ValueError, match="unsupported scenario_type"):
        retrieval_metrics(
            [
                {
                    "actual_resolution": "matched",
                    "predicted_resolution": "matched",
                    "relevant_product_ids": ["p1"],
                    "exact_product_ids": [],
                    "retrieved_product_ids": ["p1"],
                    "constraint_violating_product_ids": [],
                    "scenario_type": "invented",
                }
            ]
        )


@pytest.mark.parametrize(
    "case",
    [
        {
            "actual_resolution": "no_match",
            "predicted_resolution": "no_match",
            "relevant_product_ids": ["p1"],
            "exact_product_ids": [],
            "retrieved_product_ids": [],
            "constraint_violating_product_ids": [],
            "scenario_type": "no_match",
        },
        {
            "actual_resolution": "matched",
            "predicted_resolution": "ambiguous",
            "relevant_product_ids": ["p1"],
            "exact_product_ids": [],
            "retrieved_product_ids": ["p1"],
            "constraint_violating_product_ids": [],
            "scenario_type": "generic_product",
        },
    ],
)
def test_retrieval_rejects_resolution_ranking_contradictions(case):
    with pytest.raises(ValueError, match="resolution contradicts"):
        retrieval_metrics([case])


def test_retrieval_reports_macro_precision_with_fixed_denominators_and_recall_at_10():
    metrics = retrieval_metrics(
        [
            {
                "actual_resolution": "matched",
                "predicted_resolution": "matched",
                "relevant_product_ids": ["p1", "p2"],
                "exact_product_ids": [],
                "retrieved_product_ids": ["p1", "x", "p2"],
                "constraint_violating_product_ids": [],
                "scenario_type": "generic_product",
            },
            {
                "actual_resolution": "matched",
                "predicted_resolution": "matched",
                "relevant_product_ids": ["p3", "p4"],
                "exact_product_ids": [],
                "retrieved_product_ids": ["x", "p3"],
                "constraint_violating_product_ids": [],
                "scenario_type": "generic_product",
            },
        ]
    )

    assert metrics["precision_at_1"] == pytest.approx(0.5)
    assert metrics["precision_at_3"] == pytest.approx(0.5)
    assert metrics["precision_at_5"] == pytest.approx(0.3)
    assert metrics["recall_at_10"] == pytest.approx(0.75)


def test_retrieval_recall_at_10_is_distinct_from_recall_at_50():
    metrics = retrieval_metrics(
        [
            {
                "actual_resolution": "matched",
                "predicted_resolution": "matched",
                "relevant_product_ids": ["p1", "p2"],
                "exact_product_ids": [],
                "retrieved_product_ids": ["p1"]
                + [f"x{index}" for index in range(9)]
                + ["p2"],
                "constraint_violating_product_ids": [],
                "scenario_type": "generic_product",
            }
        ]
    )

    assert metrics["recall_at_10"] == 0.5
    assert metrics["recall_at_50"] == 1.0


def test_retrieval_reports_order_invariant_conservative_intervals():
    cases = [
        {
            "actual_resolution": "matched",
            "predicted_resolution": "matched" if index < 480 else "no_match",
            "relevant_product_ids": [f"p{index}"],
            "exact_product_ids": [],
            "retrieved_product_ids": [f"p{index}"] if index < 480 else [],
            "constraint_violating_product_ids": [],
            "scenario_type": "generic_product",
        }
        for index in range(500)
    ]

    forward = retrieval_metrics(cases)
    reverse = retrieval_metrics(list(reversed(cases)))

    assert forward["recall_at_50"] == pytest.approx(0.96)
    assert forward["recall_at_50_ci95"] == reverse["recall_at_50_ci95"]
    assert forward["ndcg_at_10_ci95"] == reverse["ndcg_at_10_ci95"]
    assert forward["recall_at_50_ci95"][0] < forward["recall_at_50"]
    assert forward["recall_at_50_ci95"][1] >= forward["recall_at_50"]


def test_retrieval_refuse_un_gold_impossible_a_couvrir_a_50():
    with pytest.raises(ValueError, match="more than 50"):
        retrieval_metrics(
            [
                {
                    "actual_resolution": "matched",
                    "predicted_resolution": "matched",
                    "relevant_product_ids": [f"p{index}" for index in range(51)],
                    "exact_product_ids": [],
                    "retrieved_product_ids": [f"p{index}" for index in range(51)],
                    "constraint_violating_product_ids": [],
                    "scenario_type": "generic_product",
                }
            ]
        )


@pytest.mark.parametrize(
    "field", ["constraint_violations", "unsupported_claims", "explanation_sourced"]
)
def test_decision_requires_every_measurement_field(field):
    case = {
        "constraint_violations": 0,
        "unsupported_claims": 0,
        "explanation_sourced": True,
    }
    del case[field]

    with pytest.raises(ValueError, match="missing required field"):
        decision_safety_metrics([case])


@pytest.mark.parametrize("value", [True, -1, 1.5, "1"])
@pytest.mark.parametrize("field", ["constraint_violations", "unsupported_claims"])
def test_decision_counters_are_non_negative_strict_integers(field, value):
    case = {
        "constraint_violations": 0,
        "unsupported_claims": 0,
        "explanation_sourced": True,
    }
    case[field] = value

    with pytest.raises((TypeError, ValueError)):
        decision_safety_metrics([case])


@pytest.mark.parametrize("value", [0, 1, "true", None])
def test_decision_sourced_flag_is_a_strict_boolean(value):
    with pytest.raises(TypeError, match="must be a boolean"):
        decision_safety_metrics(
            [
                {
                    "constraint_violations": 0,
                    "unsupported_claims": 0,
                    "explanation_sourced": value,
                }
            ]
        )


def test_empty_decision_metrics_are_not_reported_as_zero_violations():
    metrics = decision_safety_metrics([])

    assert metrics["decisions"] == 0
    assert metrics["constraint_violations"] is None
    assert metrics["unsupported_claims"] is None
    assert metrics["coverage_eligible_decisions"] == 0
    assert metrics["sourced_explanation_coverage"] is None
    assert metrics["sourced_explanation_coverage_ci95"] is None
    assert metrics["correct_answer"] is None
    assert metrics["correct_abstention"] is None
    assert metrics["wrong_answer"] is None
    assert metrics["wrong_abstention"] is None
    assert metrics["outcome_matrix_total"] is None


def test_decision_sourced_coverage_excludes_ineligible_abstentions():
    metrics = decision_safety_metrics(
        [
            {
                "constraint_violations": 0,
                "unsupported_claims": 0,
                "explanation_sourced": False,
                "coverage_eligible": False,
            },
            {
                "constraint_violations": 0,
                "unsupported_claims": 0,
                "explanation_sourced": True,
                "coverage_eligible": True,
            },
        ]
    )

    assert metrics["decisions"] == 2
    assert metrics["sourced_explanation_coverage"] == 1.0


def test_decision_outcome_matrix_is_exhaustive_and_treats_wait_as_an_answer():
    metrics = decision_safety_metrics(
        [
            {
                "constraint_violations": 0,
                "unsupported_claims": 0,
                "explanation_sourced": True,
                "coverage_eligible": True,
                "outcome": "recommend",
                "correct": True,
            },
            {
                "constraint_violations": 0,
                "unsupported_claims": 0,
                "explanation_sourced": False,
                "coverage_eligible": False,
                "outcome": "abstain",
                "correct": True,
            },
            {
                "constraint_violations": 1,
                "unsupported_claims": 0,
                "explanation_sourced": True,
                "coverage_eligible": True,
                "outcome": "wait",
                "correct": False,
            },
            {
                "constraint_violations": 0,
                "unsupported_claims": 1,
                "explanation_sourced": False,
                "coverage_eligible": False,
                "outcome": "abstain",
                "correct": False,
            },
        ]
    )

    assert metrics["correct_answer"] == 1
    assert metrics["correct_abstention"] == 1
    assert metrics["wrong_answer"] == 1
    assert metrics["wrong_abstention"] == 1
    assert metrics["outcome_matrix_total"] == metrics["decisions"] == 4


def test_decision_gold_correctness_is_independent_from_safety_counters():
    metrics = decision_safety_metrics(
        [
            {
                "constraint_violations": 0,
                "unsupported_claims": 0,
                "explanation_sourced": True,
                "outcome": "recommend",
                "correct": False,
            }
        ]
    )

    assert metrics["constraint_violations"] == 0
    assert metrics["unsupported_claims"] == 0
    assert metrics["wrong_answer"] == 1
    assert metrics["outcome_matrix_total"] == 1


def test_decision_outcome_alone_derives_answer_coverage():
    metrics = decision_safety_metrics(
        [
            {
                "constraint_violations": 0,
                "unsupported_claims": 0,
                "explanation_sourced": False,
                "outcome": "abstain",
                "correct": True,
            }
        ]
    )

    assert metrics["coverage_eligible_decisions"] == 0
    assert metrics["correct_abstention"] == 1


@pytest.mark.parametrize(
    "case",
    [
        {
            "constraint_violations": 0,
            "unsupported_claims": 0,
            "explanation_sourced": True,
            "coverage_eligible": True,
        },
        {
            "constraint_violations": 0,
            "unsupported_claims": 0,
            "explanation_sourced": True,
            "correct": True,
        },
    ],
)
def test_decision_matrix_requires_explicit_gold_and_answer_classification(case):
    metrics = decision_safety_metrics([case])

    assert metrics["constraint_violations"] == 0
    assert metrics["coverage_eligible_decisions"] == 1
    assert metrics["correct_answer"] is None
    assert metrics["correct_abstention"] is None
    assert metrics["wrong_answer"] is None
    assert metrics["wrong_abstention"] is None
    assert metrics["outcome_matrix_total"] is None


def test_decision_matrix_is_none_when_only_part_of_the_batch_is_explicit():
    metrics = decision_safety_metrics(
        [
            {
                "constraint_violations": 0,
                "unsupported_claims": 0,
                "explanation_sourced": True,
                "outcome": "recommend",
                "correct": True,
            },
            {
                "constraint_violations": 0,
                "unsupported_claims": 0,
                "explanation_sourced": True,
            },
        ]
    )

    assert metrics["decisions"] == 2
    assert metrics["correct_answer"] is None
    assert metrics["outcome_matrix_total"] is None


def test_decision_rejects_inconsistent_explicit_outcome_and_coverage():
    with pytest.raises(ValueError, match="outcome.*coverage_eligible"):
        decision_safety_metrics(
            [
                {
                    "constraint_violations": 0,
                    "unsupported_claims": 0,
                    "explanation_sourced": False,
                    "coverage_eligible": False,
                    "outcome": "wait",
                }
            ]
        )


@pytest.mark.parametrize("confidence", [True, "0.5"])
def test_calibration_confidence_rejects_non_numeric_values(confidence):
    with pytest.raises(TypeError, match="must be a real number"):
        calibration_metrics([{"confidence": confidence, "correct": True}])


@pytest.mark.parametrize("confidence", [math.nan, math.inf, -math.inf, -0.01, 1.01])
def test_calibration_confidence_must_be_finite_and_bounded(confidence):
    with pytest.raises(ValueError, match="finite and between 0 and 1"):
        calibration_metrics([{"confidence": confidence, "correct": True}])


def test_invalid_confidence_is_rejected_even_when_the_row_is_incomplete():
    with pytest.raises(ValueError, match="finite and between 0 and 1"):
        calibration_metrics([{"confidence": math.nan}])


@pytest.mark.parametrize("correct", [0, 1, "yes", [], {}])
def test_calibration_correct_is_a_strict_boolean(correct):
    with pytest.raises(TypeError, match="must be a boolean"):
        calibration_metrics([{"confidence": 0.5, "correct": correct}])


@pytest.mark.parametrize("bins", [0, -1, True, 1.5, "10"])
def test_calibration_bins_is_a_positive_strict_integer(bins):
    with pytest.raises((TypeError, ValueError)):
        calibration_metrics([], bins=bins)


def test_empty_calibration_is_not_green():
    assert calibration_metrics([]) == {
        "evaluated": 0,
        "ece": None,
        "ece_ci95": None,
        "brier_score": None,
        "bins": 10,
    }


def test_calibration_reports_mean_brier_score():
    metrics = calibration_metrics(
        [
            {"confidence": 0.8, "correct": True},
            {"confidence": 0.25, "correct": False},
        ]
    )

    assert metrics["brier_score"] == pytest.approx((0.2**2 + 0.25**2) / 2)


def test_calibration_bootstrap_interval_is_replayable_and_order_invariant():
    rows = []
    for bin_index in range(10):
        confidence = (bin_index + 0.5) / 10
        correct = round(confidence * 100)
        rows.extend({"confidence": confidence, "correct": True} for _ in range(correct))
        rows.extend(
            {"confidence": confidence, "correct": False}
            for _ in range(100 - correct)
        )

    forward = calibration_metrics(rows)
    reverse = calibration_metrics(list(reversed(rows)))

    assert forward["ece"] == pytest.approx(0.0)
    assert forward["ece_ci95"] == reverse["ece_ci95"]
    assert forward["ece_ci95"][0] == 0.0
    assert 0.0 < forward["ece_ci95"][1] < 0.05
