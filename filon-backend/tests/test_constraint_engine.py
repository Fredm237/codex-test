from __future__ import annotations

from dataclasses import replace

import pytest

from app.constraint_engine.engine import (
    CandidateFacts,
    ConstraintEngineError,
    ConstraintRequest,
    Fact,
    HardConstraint,
    Preference,
    evaluate_constraints,
)


def _candidate(**overrides):
    values = {
        "entity_ref": "variant:101",
        "price": Fact("known", {"amount": "99.99", "currency": "EUR"}, ("offer-truth:1:price",)),
        "countries": Fact("known", ("BE", "FR"), ("merchant:1:countries",)),
        "availability": Fact("known", "in_stock", ("offer-truth:1:stock",)),
        "adult_restricted": Fact("known", False, ("offer:1:adult",)),
        "attributes": {"size": Fact("known", "M", ("ontology:1:size",))},
        "preference_facts": {"color": Fact("known", "black", ("ontology:1:color",))},
    }
    values.update(overrides)
    return CandidateFacts(**values)


def _request():
    return ConstraintRequest(
        "synthetic-context",
        (
            HardConstraint("budget", "BUDGET_MAX", {"maximum": {"amount": "100.00", "currency": "EUR"}}),
            HardConstraint("country", "COUNTRY_ALLOWED", {"country_code": "BE"}),
            HardConstraint("stock", "AVAILABILITY_REQUIRED", {"value": "in_stock"}),
            HardConstraint("size", "ATTRIBUTE_EQUALS", {"attribute_key": "size", "value": "M"}),
            HardConstraint("adult", "ADULT_SAFETY", {"adult_allowed": False}),
            HardConstraint("exclude", "EXPLICIT_EXCLUSION", {"entity_refs": []}),
        ),
        (Preference("prefer-black", "color", "black"),),
    )


def test_all_hard_constraints_satisfied_and_preferences_are_not_scores():
    result = evaluate_constraints(_request(), [_candidate()])
    candidate = result.candidates[0]
    assert result.outcome == "ELIGIBLE_CANDIDATES"
    assert candidate.status == "ELIGIBLE"
    assert {item.status for item in candidate.hard_constraints} == {"SATISFIED"}
    assert candidate.preferences[0].status == "SATISFIED"
    assert not hasattr(candidate.preferences[0], "score")
    assert result.raw_context_retained is False


@pytest.mark.parametrize(
    ("candidate", "reason"),
    [
        (_candidate(price=Fact("known", {"amount": "100.01", "currency": "EUR"}, ("price",))), "budget_exceeded"),
        (_candidate(countries=Fact("known", ("FR",), ("country",))), "country_not_allowed"),
        (_candidate(availability=Fact("known", "out_of_stock", ("stock",))), "availability_unsatisfied"),
        (_candidate(attributes={"size": Fact("known", "XL", ("size",))}), "attribute_unsatisfied"),
        (_candidate(adult_restricted=Fact("known", True, ("adult",))), "adult_content_excluded"),
    ],
)
def test_each_hard_conflict_excludes(candidate, reason):
    result = evaluate_constraints(_request(), [candidate])
    assert result.outcome == "NO_ELIGIBLE_CANDIDATE"
    assert result.candidates[0].status == "EXCLUDED"
    assert reason in {item.reason_code for item in result.candidates[0].hard_constraints}


@pytest.mark.parametrize(
    "field",
    ["price", "countries", "availability", "adult_restricted"],
)
def test_unknown_required_fact_abstains(field):
    result = evaluate_constraints(_request(), [_candidate(**{field: Fact("unknown")})])
    assert result.outcome == "ABSTAINED"
    assert result.candidates[0].status == "UNKNOWN"


def test_missing_attribute_and_currency_mismatch_abstain():
    missing = evaluate_constraints(_request(), [_candidate(attributes={})])
    mismatch = evaluate_constraints(
        _request(),
        [_candidate(price=Fact("known", {"amount": "90.00", "currency": "USD"}, ("price",)))],
    )
    assert missing.candidates[0].status == "UNKNOWN"
    assert mismatch.candidates[0].status == "UNKNOWN"
    assert "currency_not_comparable" in {item.reason_code for item in mismatch.candidates[0].hard_constraints}


def test_preference_never_reintroduces_excluded_or_unknown_candidate():
    preferred = _candidate(
        availability=Fact("known", "out_of_stock", ("stock",)),
        preference_facts={"color": Fact("known", "black", ("color",))},
    )
    result = evaluate_constraints(_request(), [preferred])
    assert result.candidates[0].preferences[0].status == "SATISFIED"
    assert result.candidates[0].status == "EXCLUDED"


def test_explicit_exclusion_and_duplicate_candidates_fail_closed():
    request = replace(
        _request(),
        hard_constraints=(HardConstraint("exclude", "EXPLICIT_EXCLUSION", {"entity_refs": ["variant:101"]}),),
    )
    assert evaluate_constraints(request, [_candidate()]).candidates[0].status == "EXCLUDED"
    with pytest.raises(ConstraintEngineError, match="unique"):
        evaluate_constraints(_request(), [_candidate(), _candidate()])


def test_malformed_facts_and_parameters_are_rejected_or_unknown():
    with pytest.raises(ConstraintEngineError, match="known fact"):
        Fact("known")
    invalid_price = _candidate(price=Fact("known", {"amount": "NaN", "currency": "EUR"}, ("price",)))
    assert evaluate_constraints(_request(), [invalid_price]).candidates[0].status == "UNKNOWN"
    broken = ConstraintRequest("ctx", (HardConstraint("country", "COUNTRY_ALLOWED", {"country_code": "bel"}),))
    with pytest.raises(ConstraintEngineError, match="country code"):
        evaluate_constraints(broken, [_candidate()])


def test_same_inputs_produce_same_digest():
    first = evaluate_constraints(_request(), [_candidate()])
    second = evaluate_constraints(_request(), [_candidate()])
    assert first.context_digest == second.context_digest
    assert first.result_digest == second.result_digest
