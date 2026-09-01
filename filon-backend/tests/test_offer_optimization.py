from __future__ import annotations

from dataclasses import replace

import pytest

from app.offer_optimization.engine import (
    AvailabilityFact,
    MoneyFact,
    OfferCandidateFacts,
    OfferOptimizationError,
    OptimizationRequest,
    ReturnPolicyFact,
    ScoreFact,
    optimize_offers,
)


def _offer(
    ref: str,
    *,
    product_ref: str = "variant:101",
    price: str = "100",
    shipping: str = "5",
    cashback: str = "0",
    return_days: int = 30,
    reliability: str = "0.9",
    freshness: str = "0.8",
    truth: str = "VERIFIED",
) -> OfferCandidateFacts:
    return OfferCandidateFacts(
        offer_ref=ref,
        product_ref=product_ref,
        truth_status=truth,
        price=MoneyFact("known", price, "EUR", (f"price:{ref}",)),
        shipping=MoneyFact("known", shipping, "EUR", (f"shipping:{ref}",)),
        cashback=MoneyFact("known", cashback, "EUR", (f"cashback:{ref}",)),
        availability=AvailabilityFact("known", "in_stock", (f"stock:{ref}",)),
        returns=ReturnPolicyFact("known", True, return_days, (f"returns:{ref}",)),
        merchant_reliability=ScoreFact("known", reliability, (f"reliability:{ref}",)),
        freshness=ScoreFact("known", freshness, (f"freshness:{ref}",)),
    )


def _request() -> OptimizationRequest:
    return OptimizationRequest("ctx", "RANKED_PRODUCTS", "variant:101", 1)


def test_selects_lowest_landed_cost_then_reliability_returns_and_freshness() -> None:
    result = optimize_offers(
        _request(),
        [
            _offer("offer:a", price="100", shipping="10", cashback="5", reliability="1"),
            _offer("offer:b", price="102", shipping="2", cashback="1", reliability="0.7"),
            _offer("offer:c", price="102", shipping="2", cashback="1", reliability="0.9"),
        ],
    )
    assert result.outcome == "OFFER_SELECTED"
    assert result.selected_offer_ref == "offer:c"
    assert result.evaluations[0].status == "SELECTED"
    assert result.evaluations[0].total_cost == "104"
    assert result.evaluations[0].cashback_amount == "1"
    assert result.evaluations[0].landed_cost == "103"
    assert result.raw_context_retained is False


def test_unknown_shipping_or_reliability_abstains_without_fallback() -> None:
    candidate = _offer("offer:a")
    candidate = replace(
        candidate,
        shipping=MoneyFact("unknown"),
        merchant_reliability=ScoreFact("unknown"),
    )
    result = optimize_offers(_request(), [candidate])
    assert result.outcome == "ABSTAINED"
    assert result.selected_offer_ref is None
    assert result.evaluations[0].status == "UNOPTIMIZABLE"
    assert "shipping_unknown_or_unsourced" in result.evaluations[0].reason_codes


def test_currency_conflict_and_invalid_scores_never_receive_a_fallback() -> None:
    candidate = _offer("offer:a")
    candidate = replace(
        candidate,
        shipping=MoneyFact("known", "5", "USD", ("shipping",)),
        merchant_reliability=ScoreFact("known", "1.01", ("merchant-quality",)),
    )
    result = optimize_offers(_request(), [candidate])
    assert result.outcome == "ABSTAINED"
    assert result.selected_offer_ref is None
    assert result.evaluations[0].status == "UNOPTIMIZABLE"
    assert set(result.evaluations[0].reason_codes) >= {
        "currency_conflict",
        "merchant_reliability_unknown_or_unsourced",
    }
    assert result.evaluations[0].total_cost is None
    assert result.evaluations[0].currency is None


def test_known_eligible_offer_wins_without_hiding_unoptimizable_candidate() -> None:
    unknown = _offer("offer:a", price="1")
    unknown = replace(unknown, shipping=MoneyFact("unknown"))
    result = optimize_offers(_request(), [unknown, _offer("offer:b")])
    assert result.outcome == "OFFER_SELECTED"
    assert result.selected_offer_ref == "offer:b"
    assert {item.offer_ref: item.status for item in result.evaluations} == {
        "offer:b": "SELECTED",
        "offer:a": "UNOPTIMIZABLE",
    }


@pytest.mark.parametrize("truth", ["PARTIAL", "STALE", "INVALID", "QUARANTINED"])
def test_non_verified_offer_can_never_be_selected(truth: str) -> None:
    result = optimize_offers(_request(), [_offer("offer:a", truth=truth)])
    assert result.outcome == "NO_ELIGIBLE_OFFER"
    assert result.evaluations[0].status == "INELIGIBLE"


def test_out_of_stock_and_different_product_are_ineligible() -> None:
    out = _offer("offer:a")
    out = replace(
        out,
        availability=AvailabilityFact("known", "out_of_stock", ("stock:a",)),
    )
    result = optimize_offers(_request(), [out, _offer("offer:b", product_ref="variant:999")])
    assert result.outcome == "NO_ELIGIBLE_OFFER"
    assert {item.status for item in result.evaluations} == {"INELIGIBLE"}


def test_ranking_abstention_propagates_to_offer_optimization() -> None:
    request = OptimizationRequest("ctx", "ABSTAINED", None, None)
    result = optimize_offers(request, [_offer("offer:a")])
    assert result.outcome == "ABSTAINED"
    assert result.selected_product_ref is None
    assert result.selected_offer_ref is None


def test_commission_is_outside_contract_and_ties_are_stable() -> None:
    candidates = [_offer("offer:b"), _offer("offer:a")]
    commissions_a = {"offer:a": "0", "offer:b": "1"}
    commissions_b = {"offer:a": "1", "offer:b": "0"}
    first = optimize_offers(_request(), candidates)
    second = optimize_offers(_request(), candidates)
    assert commissions_a != commissions_b
    assert first.selected_offer_ref == second.selected_offer_ref == "offer:a"
    assert first.result_digest == second.result_digest


def test_unknown_cashback_or_returns_abstains_without_zero_fallback() -> None:
    candidate = replace(
        _offer("offer:a", price="1"),
        cashback=MoneyFact("unknown"),
        returns=ReturnPolicyFact("unknown"),
    )
    result = optimize_offers(_request(), [candidate])
    assert result.outcome == "ABSTAINED"
    assert set(result.evaluations[0].reason_codes) >= {
        "cashback_unknown_or_unsourced",
        "returns_unknown_or_unsourced",
    }


def test_returns_refused_is_ineligible_and_cashback_cannot_exceed_total() -> None:
    refused = replace(
        _offer("offer:a"),
        returns=ReturnPolicyFact("known", False, None, ("returns:a",)),
    )
    excessive = _offer("offer:b", price="10", shipping="0", cashback="11")
    result = optimize_offers(_request(), [refused, excessive])
    assert result.outcome == "ABSTAINED"
    by_ref = {item.offer_ref: item for item in result.evaluations}
    assert by_ref["offer:a"].status == "INELIGIBLE"
    assert by_ref["offer:b"].status == "UNOPTIMIZABLE"
    assert "cashback_exceeds_total_cost" in by_ref["offer:b"].reason_codes


def test_return_window_breaks_equal_landed_cost_after_reliability() -> None:
    result = optimize_offers(
        _request(),
        [
            _offer("offer:a", return_days=14),
            _offer("offer:b", return_days=30),
        ],
    )
    assert result.selected_offer_ref == "offer:b"


def test_invalid_contract_shapes_fail_closed() -> None:
    with pytest.raises(OfferOptimizationError, match="top product"):
        OptimizationRequest("ctx", "RANKED_PRODUCTS", "variant:1", 2)
    with pytest.raises(OfferOptimizationError, match="currency"):
        MoneyFact("known", "1", "eur", ("price",))
    with pytest.raises(OfferOptimizationError, match="period"):
        ReturnPolicyFact("known", True, None, ("returns",))
    with pytest.raises(OfferOptimizationError, match="unique"):
        optimize_offers(_request(), [_offer("offer:a"), _offer("offer:a")])
