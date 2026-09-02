from __future__ import annotations

import pytest

from app.solution_composer import (
    ComponentCandidate,
    CompositionRequest,
    SolutionComposerError,
    compose_solution,
)


def request(
    *,
    kind: str = "kit",
    slots: tuple[str, ...] = ("core", "support"),
    budget: str | None = "100.00",
    currency: str | None = "EUR",
) -> CompositionRequest:
    return CompositionRequest("context:test", kind, slots, budget, currency)


def owned(ref: str, slot: str, *, status: str = "ELIGIBLE") -> ComponentCandidate:
    return ComponentCandidate(ref, slot, "owned", status, None, None, None, None, None, (f"user:{ref}",))


def offer(
    ref: str,
    slot: str,
    amount: str,
    *,
    status: str = "ELIGIBLE",
    truth: str = "VERIFIED",
    duplicate: bool = False,
    currency: str = "EUR",
) -> ComponentCandidate:
    suffix = ref.split(":", 1)[1]
    return ComponentCandidate(ref, slot, "catalogue", status, amount, currency, f"offer:{suffix}", truth, duplicate, (f"snapshot:{suffix}",))


@pytest.mark.parametrize("kind", ["outfit", "setup", "kit", "routine"])
def test_composes_every_supported_domain_owned_first(kind: str) -> None:
    result = compose_solution(request(kind=kind), [owned("owned:a", "core"), owned("owned:b", "support"), offer("product:c", "core", "1.00")])

    assert result.outcome == "SOLUTION_COMPOSED"
    assert result.solution_kind == kind
    assert result.owned_count == 2
    assert result.purchase_count == 0
    assert result.total_cost == "0"
    assert result.currency is None
    assert result.utility_score is None
    assert result.raw_context_retained is False


def test_fills_only_a_missing_slot_with_the_cheapest_verified_offer() -> None:
    result = compose_solution(request(), [owned("owned:a", "core"), offer("product:z", "support", "80.00"), offer("product:b", "support", "60.00")])

    assert result.outcome == "SOLUTION_COMPOSED"
    assert result.owned_count == 1
    assert result.purchase_count == 1
    assert result.total_cost == "60.00"
    assert [item.component_ref for item in result.selected] == ["owned:a", "product:b"]


@pytest.mark.parametrize(
    ("candidate", "reason"),
    [
        (offer("product:partial", "support", "10", truth="PARTIAL"), "required_slot_unavailable:support"),
        (offer("product:unknown", "support", "10", status="UNKNOWN"), "required_slot_unavailable:support"),
        (offer("product:duplicate", "support", "10", duplicate=True), "required_slot_unavailable:support"),
        (offer("product:usd", "support", "10", currency="USD"), "required_slot_unavailable:support"),
    ],
)
def test_fail_closes_unproved_catalogue_components(candidate: ComponentCandidate, reason: str) -> None:
    result = compose_solution(request(), [owned("owned:a", "core"), candidate])

    assert result.outcome == "ABSTAINED"
    assert result.reason_code == reason
    assert result.selected == ()


def test_rejects_a_solution_over_budget_without_partial_selection() -> None:
    result = compose_solution(request(budget="50"), [owned("owned:a", "core"), offer("product:b", "support", "60")])

    assert result.outcome == "ABSTAINED"
    assert result.reason_code == "solution_budget_exceeded"
    assert result.selected == ()


def test_requires_budget_and_currency_together() -> None:
    with pytest.raises(SolutionComposerError, match="provided together"):
        request(budget="100", currency=None)


def test_rejects_duplicate_candidate_identity() -> None:
    candidate = owned("owned:a", "core")
    with pytest.raises(SolutionComposerError, match="must be unique"):
        compose_solution(request(slots=("core",)), [candidate, candidate])


def test_result_is_deterministic_and_digest_changes_with_context() -> None:
    candidates = [owned("owned:a", "core"), offer("product:b", "support", "60")]
    first = compose_solution(request(), candidates)
    second = compose_solution(request(), list(reversed(candidates)))
    other = compose_solution(CompositionRequest("context:other", "kit", ("core", "support"), "100.00", "EUR"), candidates)

    assert first == second
    assert first.result_digest == second.result_digest
    assert first.context_digest != other.context_digest
