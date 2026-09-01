from __future__ import annotations

import pytest

from app.product_ranking.engine import (
    ProductRankingError,
    RankingCandidateFacts,
    RankingRequest,
    ScoreFact,
    rank_products,
)


def _fact(value: str, name: str) -> ScoreFact:
    return ScoreFact("known", value, (f"evidence:{name}",))


def _candidate(
    entity_ref: str = "variant:101",
    *,
    eligibility: str = "ELIGIBLE",
    need_fit: ScoreFact | None = None,
    quality: ScoreFact | None = None,
    value: ScoreFact | None = None,
    evidence: ScoreFact | None = None,
) -> RankingCandidateFacts:
    return RankingCandidateFacts(
        entity_ref,
        eligibility,
        {
            "need_fit": need_fit or _fact("0.8", "need-fit"),
            "product_quality": quality or _fact("0.7", "quality"),
            "value": value or _fact("0.6", "value"),
            "evidence": evidence or _fact("0.9", "evidence"),
        },
    )


def test_ranks_only_complete_eligible_candidates() -> None:
    result = rank_products(RankingRequest("ctx", "smartphones"), [_candidate()])
    assert result.outcome == "RANKED_PRODUCTS"
    assert result.ranked_entity_refs == ("variant:101",)
    assert result.candidates[0].status == "RANKED"
    assert result.candidates[0].rank == 1
    assert result.raw_context_retained is False


@pytest.mark.parametrize("eligibility", ["EXCLUDED", "UNKNOWN"])
def test_constraint_status_can_never_be_reintroduced(eligibility: str) -> None:
    candidate = _candidate(eligibility=eligibility)
    result = rank_products(RankingRequest("ctx", "smartphones"), [candidate])
    assert result.outcome == "NO_ELIGIBLE_PRODUCT"
    assert result.ranked_entity_refs == ()
    assert result.candidates[0].status == "INELIGIBLE"


def test_unknown_or_unsourced_dimension_abstains() -> None:
    unknown = _candidate(need_fit=ScoreFact("unknown"))
    unsourced = _candidate("variant:102", quality=ScoreFact("known", "0.7"))
    result = rank_products(RankingRequest("ctx", "smartphones"), [unknown, unsourced])
    assert result.outcome == "ABSTAINED"
    assert result.ranked_entity_refs == ()
    assert {item.status for item in result.candidates} == {"UNRANKABLE"}


def test_vertical_weights_are_not_universal() -> None:
    need_first = _candidate(
        "variant:need",
        need_fit=_fact("1", "need"),
        quality=_fact("0", "quality"),
        value=_fact("1", "value"),
        evidence=_fact("1", "evidence"),
    )
    quality_first = _candidate(
        "variant:quality",
        need_fit=_fact("0", "need"),
        quality=_fact("1", "quality"),
        value=_fact("1", "value"),
        evidence=_fact("1", "evidence"),
    )
    phone = rank_products(RankingRequest("ctx", "smartphones"), [need_first, quality_first])
    audio = rank_products(RankingRequest("ctx", "audio"), [need_first, quality_first])
    assert phone.ranked_entity_refs[0] == "variant:need"
    assert audio.ranked_entity_refs[0] == "variant:quality"


def test_tie_break_is_stable_and_commission_is_outside_the_contract() -> None:
    candidates = [_candidate("variant:b"), _candidate("variant:a")]
    commissions_a = {"variant:a": "0.20", "variant:b": "0.00"}
    commissions_b = {"variant:a": "0.00", "variant:b": "0.20"}
    first = rank_products(RankingRequest("ctx", "laptops"), candidates)
    second = rank_products(RankingRequest("ctx", "laptops"), candidates)
    assert commissions_a != commissions_b
    assert first.ranked_entity_refs == second.ranked_entity_refs == ("variant:a", "variant:b")
    assert first.result_digest == second.result_digest


def test_invalid_scores_and_dimensions_fail_closed() -> None:
    invalid = _candidate(need_fit=_fact("NaN", "need"))
    result = rank_products(RankingRequest("ctx", "fashion"), [invalid])
    assert result.outcome == "ABSTAINED"
    assert result.candidates[0].status == "UNRANKABLE"
    with pytest.raises(ProductRankingError, match="dimensions"):
        RankingCandidateFacts("variant:1", "ELIGIBLE", {"need_fit": _fact("1", "x")})
    with pytest.raises(ProductRankingError, match="vertical"):
        RankingRequest("ctx", "universal")


def test_same_inputs_produce_same_digest() -> None:
    request = RankingRequest("ctx", "tyres")
    first = rank_products(request, [_candidate()])
    second = rank_products(request, [_candidate()])
    assert first.context_digest == second.context_digest
    assert first.result_digest == second.result_digest
