"""Politique personnelle, déterministe et sans score arbitraire Phase 18."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping, Sequence


PERSONAL_COMMERCE_POLICY_VERSION = "personal-commerce-policy/v1"
SOLUTION_KINDS = {"outfit", "setup", "kit", "routine"}


class PersonalCommerceError(ValueError):
    """Entrée hors contrat ou préférence personnelle ambiguë."""


def _decimal(value: str | None, *, allow_zero: bool = True) -> Decimal | None:
    if value is None:
        return None
    try:
        parsed = Decimal(value)
    except (InvalidOperation, ValueError):
        return None
    if not parsed.is_finite() or parsed < 0 or (not allow_zero and parsed == 0):
        return None
    return parsed


@dataclass(frozen=True)
class ExplicitPreference:
    preference_id: str
    attribute_key: str
    value: str
    polarity: str
    consent_scope: str
    evidence_ref: str

    def __post_init__(self) -> None:
        if not self.preference_id or not self.attribute_key or not self.value or not self.evidence_ref:
            raise PersonalCommerceError("preference fields are required")
        if self.polarity not in {"LIKE", "DISLIKE"}:
            raise PersonalCommerceError("preference polarity is invalid")
        if self.consent_scope != "personal_commerce":
            raise PersonalCommerceError("preference consent scope is invalid")


@dataclass(frozen=True)
class PersonalCommerceRequest:
    objective_ref: str
    personalization_consent: bool
    allowed_solution_kinds: tuple[str, ...]
    maximum_budget: str | None
    currency: str | None
    preferences: tuple[ExplicitPreference, ...] = ()

    def __post_init__(self) -> None:
        if not self.objective_ref:
            raise PersonalCommerceError("objective ref is required")
        if not self.allowed_solution_kinds or any(kind not in SOLUTION_KINDS for kind in self.allowed_solution_kinds):
            raise PersonalCommerceError("allowed solution kinds are invalid")
        if len(set(self.allowed_solution_kinds)) != len(self.allowed_solution_kinds):
            raise PersonalCommerceError("allowed solution kinds must be unique")
        if self.maximum_budget is not None and _decimal(self.maximum_budget, allow_zero=False) is None:
            raise PersonalCommerceError("maximum budget is invalid")
        if self.currency is not None and (len(self.currency) != 3 or not self.currency.isascii() or not self.currency.isupper()):
            raise PersonalCommerceError("currency is invalid")
        if (self.maximum_budget is None) != (self.currency is None):
            raise PersonalCommerceError("budget and currency must be provided together")
        ids = [preference.preference_id for preference in self.preferences]
        if len(ids) != len(set(ids)):
            raise PersonalCommerceError("preference ids must be unique")
        signatures = [(preference.attribute_key, preference.value) for preference in self.preferences]
        for signature in set(signatures):
            polarities = {preference.polarity for preference in self.preferences if (preference.attribute_key, preference.value) == signature}
            if len(polarities) > 1:
                raise PersonalCommerceError("preference polarity conflict")


@dataclass(frozen=True)
class PersonalCommerceCandidate:
    solution_ref: str
    solution_kind: str
    composition_outcome: str
    constraint_status: str
    owned_count: int
    purchase_count: int
    total_cost: str
    currency: str | None
    purchase_action: str | None
    purchase_action_evidence_ref: str | None
    attributes: Mapping[str, str]
    evidence_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.solution_ref.startswith("solution:") or not self.solution_ref.removeprefix("solution:"):
            raise PersonalCommerceError("solution ref is invalid")
        if self.solution_kind not in SOLUTION_KINDS:
            raise PersonalCommerceError("solution kind is invalid")
        if self.composition_outcome not in {"SOLUTION_COMPOSED", "ABSTAINED"}:
            raise PersonalCommerceError("composition outcome is invalid")
        if self.constraint_status not in {"ELIGIBLE", "EXCLUDED", "UNKNOWN"}:
            raise PersonalCommerceError("constraint status is invalid")
        if isinstance(self.owned_count, bool) or self.owned_count < 0 or isinstance(self.purchase_count, bool) or self.purchase_count < 0:
            raise PersonalCommerceError("component counts are invalid")
        total = _decimal(self.total_cost)
        if total is None:
            raise PersonalCommerceError("total cost is invalid")
        if not self.evidence_refs or any(not ref for ref in self.evidence_refs) or len(set(self.evidence_refs)) != len(self.evidence_refs):
            raise PersonalCommerceError("evidence refs are invalid")
        if any(not key or not isinstance(value, str) or not value for key, value in self.attributes.items()):
            raise PersonalCommerceError("candidate attributes are invalid")
        if self.purchase_count == 0:
            if total != 0 or self.currency is not None or self.purchase_action is not None or self.purchase_action_evidence_ref is not None:
                raise PersonalCommerceError("owned-only candidate shape is invalid")
        else:
            if total <= 0 or self.currency is None or self.purchase_action not in {"BUY", "WAIT"} or not self.purchase_action_evidence_ref:
                raise PersonalCommerceError("purchase candidate shape is invalid")


@dataclass(frozen=True)
class PersonalCommerceResult:
    schema_version: str
    policy_version: str
    objective_digest: str
    raw_context_retained: bool
    outcome: str
    action: str
    selected_solution_ref: str | None
    selected_solution_kind: str | None
    matched_preference_ids: tuple[str, ...]
    eligible_count: int
    rejected_count: int
    utility_score: None
    measurement_status: str
    reason_codes: tuple[str, ...]
    result_digest: str


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _preference_matches(candidate: PersonalCommerceCandidate, preferences: Sequence[ExplicitPreference], polarity: str) -> tuple[str, ...]:
    return tuple(sorted(
        preference.preference_id
        for preference in preferences
        if preference.polarity == polarity and candidate.attributes.get(preference.attribute_key) == preference.value
    ))


def _result(request: PersonalCommerceRequest, *, outcome: str, action: str, selected: PersonalCommerceCandidate | None, matched: tuple[str, ...], eligible_count: int, rejected_count: int, reasons: tuple[str, ...]) -> PersonalCommerceResult:
    objective_digest = _digest(asdict(request))
    body = {
        "schema_version": "personal-commerce/v1",
        "policy_version": PERSONAL_COMMERCE_POLICY_VERSION,
        "objective_digest": objective_digest,
        "raw_context_retained": False,
        "outcome": outcome,
        "action": action,
        "selected_solution_ref": selected.solution_ref if selected else None,
        "selected_solution_kind": selected.solution_kind if selected else None,
        "matched_preference_ids": matched,
        "eligible_count": eligible_count,
        "rejected_count": rejected_count,
        "utility_score": None,
        "measurement_status": "not_calibrated",
        "reason_codes": reasons,
    }
    return PersonalCommerceResult(**body, result_digest=_digest(body))


def decide_personal_commerce(
    request: PersonalCommerceRequest,
    candidates: Sequence[PersonalCommerceCandidate],
) -> PersonalCommerceResult:
    refs = [candidate.solution_ref for candidate in candidates]
    if len(refs) != len(set(refs)):
        raise PersonalCommerceError("candidate solution refs must be unique")
    if not request.personalization_consent:
        return _result(request, outcome="ABSTAINED", action="ABSTAIN", selected=None, matched=(), eligible_count=0, rejected_count=len(candidates), reasons=("personalization_consent_missing",))

    maximum = _decimal(request.maximum_budget)
    eligible: list[tuple[PersonalCommerceCandidate, tuple[str, ...]]] = []
    rejected_count = 0
    for candidate in candidates:
        total = _decimal(candidate.total_cost) or Decimal("0")
        structurally_eligible = (
            candidate.solution_kind in request.allowed_solution_kinds
            and candidate.composition_outcome == "SOLUTION_COMPOSED"
            and candidate.constraint_status == "ELIGIBLE"
            and (
                candidate.purchase_count == 0
                or (
                    maximum is not None
                    and candidate.currency == request.currency
                    and total <= maximum
                    and candidate.purchase_action in {"BUY", "WAIT"}
                )
            )
        )
        disliked = _preference_matches(candidate, request.preferences, "DISLIKE")
        if not structurally_eligible or disliked:
            rejected_count += 1
            continue
        eligible.append((candidate, _preference_matches(candidate, request.preferences, "LIKE")))

    if not eligible:
        return _result(request, outcome="ABSTAINED", action="ABSTAIN", selected=None, matched=(), eligible_count=0, rejected_count=rejected_count, reasons=("no_personally_eligible_solution",))

    eligible.sort(key=lambda item: (
        item[0].purchase_count,
        -item[0].owned_count,
        -len(item[1]),
        _decimal(item[0].total_cost) or Decimal("0"),
        item[0].solution_ref,
    ))
    selected, matched = eligible[0]
    action = "USE_WHAT_YOU_OWN" if selected.purchase_count == 0 else selected.purchase_action or "ABSTAIN"
    reasons = (
        "owned_solution_preferred" if action == "USE_WHAT_YOU_OWN" else "verified_solution_selected",
        "explicit_preferences_only",
        "no_commercial_priority",
    )
    return _result(request, outcome="SOLUTION_SELECTED", action=action, selected=selected, matched=matched, eligible_count=len(eligible), rejected_count=rejected_count, reasons=reasons)
