from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from app.buy_wait.engine import (
    BuyWaitError,
    BuyWaitRequest,
    DecisionConfidence,
    PriceObservation,
    decide_buy_wait,
)


NOW = datetime(2026, 9, 1, 12, tzinfo=UTC)


def _confidence(
    state: str = "CALIBRATED", probability: str | None = "0.900000"
) -> DecisionConfidence:
    if state != "CALIBRATED":
        return DecisionConfidence(state, None, 0, None, ())
    return DecisionConfidence(
        state, probability, 1000, "confidence:decision:v1", ("confidence:evidence",)
    )


def _history(prices: list[str], *, currency: str = "EUR") -> tuple[PriceObservation, ...]:
    start = NOW - timedelta(days=(len(prices) - 1) * 2)
    return tuple(
        PriceObservation(
            price,
            currency,
            start + timedelta(days=index * 2),
            True,
            (f"price:{index}",),
        )
        for index, price in enumerate(prices)
    )


def _request(prices: list[str]) -> BuyWaitRequest:
    history = _history(prices)
    return BuyWaitRequest(
        "case:1",
        NOW,
        "offer:1",
        "variant:1",
        history[-1],
        history,
        _confidence(),
        "backtest:buy-wait:v2:holdout",
    )


def test_material_historical_low_can_buy_now() -> None:
    decision = decide_buy_wait(_request(["100", "101", "99", "102", "100", "98", "101", "80"]))
    assert decision.outcome == "BUY_NOW"
    assert decision.current_percentile_decimal == "0.125000"
    assert decision.future_observations_used is False
    assert len(decision.claims) == 3
    assert decision.raw_context_retained is False


def test_material_historical_high_can_wait() -> None:
    decision = decide_buy_wait(_request(["100", "101", "99", "102", "100", "98", "101", "120"]))
    assert decision.outcome == "WAIT"
    assert decision.current_percentile_decimal == "1.000000"
    assert "current_price_materially_high" in decision.reason_codes


def test_neutral_price_abstains_instead_of_inventing_direction() -> None:
    decision = decide_buy_wait(_request(["100", "101", "99", "102", "100", "98", "101", "100"]))
    assert decision.outcome == "ABSTAIN"
    assert decision.claims == ()
    assert decision.backtest_profile_ref is None


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        (lambda request: replace(request, decision_confidence=_confidence("UNKNOWN", None)), "decision_confidence_not_calibrated"),
        (lambda request: replace(request, decision_confidence=_confidence(probability="0.79")), "decision_confidence_below_policy"),
        (lambda request: replace(request, backtest_profile_ref=None), "historical_backtest_profile_missing"),
        (
            lambda request: replace(
                request,
                evaluated_at=request.history[3].observed_at,
                history=request.history[:4],
                current=request.history[3],
            ),
            "history_samples_below_policy",
        ),
        (lambda request: replace(request, evaluated_at=NOW + timedelta(days=3)), "current_observation_stale"),
    ],
)
def test_missing_preconditions_fail_closed(mutation, reason: str) -> None:
    decision = decide_buy_wait(mutation(_request(["100", "101", "99", "102", "100", "98", "101", "80"])))
    assert decision.outcome == "ABSTAIN"
    assert reason in decision.reason_codes


def test_future_observation_is_rejected_not_silently_dropped() -> None:
    request = _request(["100", "101", "99", "102", "100", "98", "101", "80"])
    future = PriceObservation("70", "EUR", NOW + timedelta(days=1), True, ("future",))
    decision = decide_buy_wait(replace(request, history=(*request.history, future)))
    assert decision.outcome == "ABSTAIN"
    assert decision.reason_codes == ("future_observation_rejected",)


def test_currency_and_stock_mismatch_reduce_usable_history_fail_closed() -> None:
    request = _request(["100", "101", "99", "102", "100", "98", "101", "80"])
    mixed = tuple(
        replace(item, currency="USD") if index < 4 else item
        for index, item in enumerate(request.history)
    )
    decision = decide_buy_wait(replace(request, history=mixed))
    assert decision.outcome == "ABSTAIN"
    assert "history_samples_below_policy" in decision.reason_codes


def test_source_abstention_propagates() -> None:
    decision = decide_buy_wait(
        BuyWaitRequest("case:none", NOW, None, None, None, (), _confidence("UNKNOWN", None), None)
    )
    assert decision.outcome == "ABSTAIN"
    assert decision.reason_codes == ("source_selection_missing",)


def test_invalid_contract_shapes_raise() -> None:
    with pytest.raises(BuyWaitError, match="currency"):
        PriceObservation("10", "eur", NOW, True, ("price",))
    with pytest.raises(BuyWaitError, match="support"):
        DecisionConfidence("CALIBRATED", "0.9", 0, None, ())
    with pytest.raises(BuyWaitError, match="present together"):
        BuyWaitRequest("case", NOW, "offer:1", None, None, (), _confidence(), None)
