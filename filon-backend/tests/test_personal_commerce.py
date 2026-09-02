from __future__ import annotations

import pytest

from app.personal_commerce import (
    ExplicitPreference,
    PersonalCommerceCandidate,
    PersonalCommerceError,
    PersonalCommerceRequest,
    decide_personal_commerce,
)


def preference(identifier: str, key: str, value: str, polarity: str = "LIKE") -> ExplicitPreference:
    return ExplicitPreference(identifier, key, value, polarity, "personal_commerce", f"user:{identifier}")


def request(*, consent: bool = True, preferences: tuple[ExplicitPreference, ...] = ()) -> PersonalCommerceRequest:
    return PersonalCommerceRequest("objective:test", consent, ("outfit", "setup", "kit", "routine"), "200", "EUR", preferences)


def candidate(
    identifier: str,
    *,
    kind: str = "kit",
    owned: int = 1,
    purchases: int = 0,
    cost: str = "0",
    currency: str | None = None,
    action: str | None = None,
    composition: str = "SOLUTION_COMPOSED",
    constraint: str = "ELIGIBLE",
    attributes: dict[str, str] | None = None,
) -> PersonalCommerceCandidate:
    return PersonalCommerceCandidate(
        f"solution:{identifier}", kind, composition, constraint, owned, purchases,
        cost, currency, action, f"buy-wait:{identifier}" if action else None,
        attributes or {}, (f"composition:{identifier}",),
    )


def test_requires_personalization_consent() -> None:
    result = decide_personal_commerce(request(consent=False), [candidate("owned")])

    assert result.outcome == "ABSTAINED"
    assert result.action == "ABSTAIN"
    assert result.selected_solution_ref is None
    assert result.reason_codes == ("personalization_consent_missing",)


def test_prefers_use_what_you_own_across_domains() -> None:
    buy = candidate("buy", kind="setup", owned=2, purchases=1, cost="30", currency="EUR", action="BUY")
    owned = candidate("owned", kind="routine", owned=2)

    result = decide_personal_commerce(request(), [buy, owned])

    assert result.outcome == "SOLUTION_SELECTED"
    assert result.action == "USE_WHAT_YOU_OWN"
    assert result.selected_solution_ref == "solution:owned"
    assert result.utility_score is None
    assert result.raw_context_retained is False


def test_explicit_like_breaks_a_tie_after_ownership() -> None:
    preferences = (preference("pref-blue", "color", "blue"),)
    red = candidate("red", attributes={"color": "red"})
    blue = candidate("blue", attributes={"color": "blue"})

    result = decide_personal_commerce(request(preferences=preferences), [red, blue])

    assert result.selected_solution_ref == "solution:blue"
    assert result.matched_preference_ids == ("pref-blue",)


def test_explicit_dislike_excludes_a_candidate() -> None:
    preferences = (preference("no-wool", "material", "wool", "DISLIKE"),)
    wool = candidate("wool", attributes={"material": "wool"})
    cotton = candidate("cotton", attributes={"material": "cotton"})

    result = decide_personal_commerce(request(preferences=preferences), [wool, cotton])

    assert result.selected_solution_ref == "solution:cotton"
    assert result.rejected_count == 1


@pytest.mark.parametrize("action", ["BUY", "WAIT"])
def test_preserves_the_evidenced_purchase_action(action: str) -> None:
    result = decide_personal_commerce(request(), [candidate("purchase", purchases=1, cost="80", currency="EUR", action=action)])

    assert result.action == action
    assert result.reason_codes == ("verified_solution_selected", "explicit_preferences_only", "no_commercial_priority")


@pytest.mark.parametrize(
    "invalid",
    [
        candidate("abstained", composition="ABSTAINED"),
        candidate("unknown", constraint="UNKNOWN"),
        candidate("expensive", purchases=1, cost="250", currency="EUR", action="BUY"),
        candidate("foreign", purchases=1, cost="50", currency="USD", action="BUY"),
    ],
)
def test_fail_closes_invalid_or_incomparable_solutions(invalid: PersonalCommerceCandidate) -> None:
    result = decide_personal_commerce(request(), [invalid])

    assert result.outcome == "ABSTAINED"
    assert result.action == "ABSTAIN"


def test_rejects_conflicting_explicit_preferences() -> None:
    with pytest.raises(PersonalCommerceError, match="polarity conflict"):
        request(preferences=(preference("like", "brand", "A"), preference("dislike", "brand", "A", "DISLIKE")))


def test_decision_is_deterministic_and_context_scoped() -> None:
    candidates = [candidate("b"), candidate("a")]
    first = decide_personal_commerce(request(), candidates)
    second = decide_personal_commerce(request(), list(reversed(candidates)))
    other = decide_personal_commerce(PersonalCommerceRequest("objective:other", True, ("kit",), "200", "EUR"), candidates)

    assert first == second
    assert first.selected_solution_ref == "solution:a"
    assert first.result_digest == second.result_digest
    assert first.objective_digest != other.objective_digest
