"""Moteur déterministe de contraintes Phase 6.

Ce module filtre les candidats Hybrid Retrieval. Il n'attribue aucun score et
ne choisit aucune offre. Toute vérité manquante sur une contrainte requise est
une abstention locale au candidat.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping, Sequence


CONSTRAINT_POLICY_VERSION = "constraint-engine-policy/v1"
SUPPORTED_HARD_KINDS = {
    "BUDGET_MAX",
    "COUNTRY_ALLOWED",
    "AVAILABILITY_REQUIRED",
    "ATTRIBUTE_EQUALS",
    "ADULT_SAFETY",
    "EXPLICIT_EXCLUSION",
}
FACT_STATES = {"known", "unknown", "invalid", "conflict"}


class ConstraintEngineError(ValueError):
    """Entrée hors contrat ou résultat impossible à prouver."""


@dataclass(frozen=True)
class Fact:
    state: str
    value: Any = None
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.state not in FACT_STATES:
            raise ConstraintEngineError("fact state is invalid")
        if self.state == "known" and self.value is None:
            raise ConstraintEngineError("known fact requires a value")
        if self.state != "known" and self.value is not None:
            raise ConstraintEngineError("non-known fact cannot carry a value")
        if any(not isinstance(item, str) or not item for item in self.evidence_refs):
            raise ConstraintEngineError("evidence refs must be non-empty strings")
        if len(set(self.evidence_refs)) != len(self.evidence_refs):
            raise ConstraintEngineError("evidence refs must be unique")


@dataclass(frozen=True)
class HardConstraint:
    constraint_id: str
    kind: str
    parameters: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not self.constraint_id:
            raise ConstraintEngineError("constraint id is required")
        if self.kind not in SUPPORTED_HARD_KINDS:
            raise ConstraintEngineError("hard constraint kind is unsupported")


@dataclass(frozen=True)
class Preference:
    preference_id: str
    fact_key: str
    preferred_value: Any

    def __post_init__(self) -> None:
        if not self.preference_id or not self.fact_key or self.preferred_value is None:
            raise ConstraintEngineError("preference is invalid")


@dataclass(frozen=True)
class ConstraintRequest:
    context_ref: str
    hard_constraints: tuple[HardConstraint, ...]
    preferences: tuple[Preference, ...] = ()

    def __post_init__(self) -> None:
        if not self.context_ref:
            raise ConstraintEngineError("context ref is required")
        identifiers = [item.constraint_id for item in self.hard_constraints]
        identifiers.extend(item.preference_id for item in self.preferences)
        if len(set(identifiers)) != len(identifiers):
            raise ConstraintEngineError("constraint and preference ids must be unique")


@dataclass(frozen=True)
class CandidateFacts:
    entity_ref: str
    price: Fact
    countries: Fact
    availability: Fact
    adult_restricted: Fact
    attributes: Mapping[str, Fact]
    preference_facts: Mapping[str, Fact]

    def __post_init__(self) -> None:
        prefix, separator, suffix = self.entity_ref.partition(":")
        if not separator or prefix not in {"product", "model", "variant"} or not suffix:
            raise ConstraintEngineError("candidate entity ref is invalid")
        if any(not key or not isinstance(value, Fact) for key, value in self.attributes.items()):
            raise ConstraintEngineError("candidate attributes are invalid")
        if any(not key or not isinstance(value, Fact) for key, value in self.preference_facts.items()):
            raise ConstraintEngineError("candidate preference facts are invalid")


@dataclass(frozen=True)
class EvaluationResult:
    constraint_id: str
    kind: str
    status: str
    reason_code: str
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True)
class CandidateEvaluation:
    entity_ref: str
    status: str
    hard_constraints: tuple[EvaluationResult, ...]
    preferences: tuple[EvaluationResult, ...]
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class ConstraintEvaluation:
    schema_version: str
    policy_version: str
    context_digest: str
    raw_context_retained: bool
    outcome: str
    candidates: tuple[CandidateEvaluation, ...]
    result_digest: str


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _unknown(constraint: HardConstraint, fact: Fact, reason: str) -> EvaluationResult:
    return EvaluationResult(
        constraint.constraint_id,
        constraint.kind,
        "UNKNOWN",
        reason,
        fact.evidence_refs,
    )


def _comparison(
    constraint: HardConstraint,
    fact: Fact,
    satisfied: bool,
    *,
    satisfied_reason: str,
    unsatisfied_reason: str,
) -> EvaluationResult:
    return EvaluationResult(
        constraint.constraint_id,
        constraint.kind,
        "SATISFIED" if satisfied else "UNSATISFIED",
        satisfied_reason if satisfied else unsatisfied_reason,
        fact.evidence_refs,
    )


def _money(value: Any) -> tuple[Decimal, str] | None:
    if not isinstance(value, Mapping):
        return None
    amount = value.get("amount")
    currency = value.get("currency")
    if not isinstance(amount, str) or not isinstance(currency, str) or len(currency) != 3:
        return None
    try:
        parsed = Decimal(amount)
    except InvalidOperation:
        return None
    if not parsed.is_finite() or parsed < 0 or currency.upper() != currency:
        return None
    return parsed, currency


def _evaluate_hard(constraint: HardConstraint, candidate: CandidateFacts) -> EvaluationResult:
    parameters = constraint.parameters
    if constraint.kind == "EXPLICIT_EXCLUSION":
        refs = parameters.get("entity_refs")
        if not isinstance(refs, Sequence) or isinstance(refs, (str, bytes)):
            raise ConstraintEngineError("explicit exclusion entity_refs are invalid")
        excluded = candidate.entity_ref in refs
        return EvaluationResult(
            constraint.constraint_id,
            constraint.kind,
            "UNSATISFIED" if excluded else "SATISFIED",
            "entity_explicitly_excluded" if excluded else "entity_not_excluded",
            (),
        )

    if constraint.kind == "BUDGET_MAX":
        fact = candidate.price
        if fact.state != "known":
            return _unknown(constraint, fact, f"price_{fact.state}")
        actual = _money(fact.value)
        maximum = _money(parameters.get("maximum"))
        if maximum is None:
            raise ConstraintEngineError("budget maximum is invalid")
        if actual is None:
            return _unknown(constraint, Fact("invalid", evidence_refs=fact.evidence_refs), "price_invalid")
        if actual[1] != maximum[1]:
            return _unknown(constraint, fact, "currency_not_comparable")
        return _comparison(
            constraint,
            fact,
            actual[0] <= maximum[0],
            satisfied_reason="budget_satisfied",
            unsatisfied_reason="budget_exceeded",
        )

    if constraint.kind == "COUNTRY_ALLOWED":
        fact = candidate.countries
        expected = parameters.get("country_code")
        if not isinstance(expected, str) or len(expected) != 2 or expected.upper() != expected:
            raise ConstraintEngineError("country code is invalid")
        if fact.state != "known":
            return _unknown(constraint, fact, f"countries_{fact.state}")
        if not isinstance(fact.value, Sequence) or isinstance(fact.value, (str, bytes)):
            return _unknown(constraint, Fact("invalid", evidence_refs=fact.evidence_refs), "countries_invalid")
        return _comparison(
            constraint,
            fact,
            expected in fact.value,
            satisfied_reason="country_allowed",
            unsatisfied_reason="country_not_allowed",
        )

    if constraint.kind == "AVAILABILITY_REQUIRED":
        fact = candidate.availability
        expected = parameters.get("value")
        if expected not in {"in_stock", "preorder"}:
            raise ConstraintEngineError("required availability is invalid")
        if fact.state != "known":
            return _unknown(constraint, fact, f"availability_{fact.state}")
        if fact.value not in {"in_stock", "out_of_stock", "preorder"}:
            return _unknown(constraint, Fact("invalid", evidence_refs=fact.evidence_refs), "availability_invalid")
        return _comparison(
            constraint,
            fact,
            fact.value == expected,
            satisfied_reason="availability_satisfied",
            unsatisfied_reason="availability_unsatisfied",
        )

    if constraint.kind == "ATTRIBUTE_EQUALS":
        key = parameters.get("attribute_key")
        expected = parameters.get("value")
        if not isinstance(key, str) or not key or expected is None:
            raise ConstraintEngineError("attribute constraint is invalid")
        fact = candidate.attributes.get(key, Fact("unknown"))
        if fact.state != "known":
            return _unknown(constraint, fact, f"attribute_{fact.state}")
        return _comparison(
            constraint,
            fact,
            fact.value == expected,
            satisfied_reason="attribute_satisfied",
            unsatisfied_reason="attribute_unsatisfied",
        )

    if constraint.kind == "ADULT_SAFETY":
        fact = candidate.adult_restricted
        adult_allowed = parameters.get("adult_allowed")
        if not isinstance(adult_allowed, bool):
            raise ConstraintEngineError("adult safety parameter is invalid")
        if fact.state != "known":
            return _unknown(constraint, fact, f"adult_restriction_{fact.state}")
        if not isinstance(fact.value, bool):
            return _unknown(constraint, Fact("invalid", evidence_refs=fact.evidence_refs), "adult_restriction_invalid")
        satisfied = adult_allowed or not fact.value
        return _comparison(
            constraint,
            fact,
            satisfied,
            satisfied_reason="adult_safety_satisfied",
            unsatisfied_reason="adult_content_excluded",
        )

    raise ConstraintEngineError("hard constraint kind is unsupported")


def _evaluate_preference(preference: Preference, candidate: CandidateFacts) -> EvaluationResult:
    fact = candidate.preference_facts.get(preference.fact_key, Fact("unknown"))
    if fact.state != "known":
        return EvaluationResult(
            preference.preference_id,
            "PREFERENCE",
            "UNKNOWN",
            f"preference_{fact.state}",
            fact.evidence_refs,
        )
    satisfied = fact.value == preference.preferred_value
    return EvaluationResult(
        preference.preference_id,
        "PREFERENCE",
        "SATISFIED" if satisfied else "UNSATISFIED",
        "preference_observed" if satisfied else "preference_not_observed",
        fact.evidence_refs,
    )


def evaluate_constraints(
    request: ConstraintRequest,
    candidates: Sequence[CandidateFacts],
) -> ConstraintEvaluation:
    refs = [item.entity_ref for item in candidates]
    if len(set(refs)) != len(refs):
        raise ConstraintEngineError("candidate entity refs must be unique")
    evaluated: list[CandidateEvaluation] = []
    for candidate in candidates:
        hard = tuple(_evaluate_hard(item, candidate) for item in request.hard_constraints)
        preferences = tuple(_evaluate_preference(item, candidate) for item in request.preferences)
        hard_statuses = {item.status for item in hard}
        if "UNSATISFIED" in hard_statuses:
            status = "EXCLUDED"
            reasons = ("hard_constraint_unsatisfied",)
        elif "UNKNOWN" in hard_statuses:
            status = "UNKNOWN"
            reasons = ("required_constraint_unknown",)
        else:
            status = "ELIGIBLE"
            reasons = ("all_hard_constraints_satisfied",)
        evaluated.append(
            CandidateEvaluation(candidate.entity_ref, status, hard, preferences, reasons)
        )
    eligible = sum(item.status == "ELIGIBLE" for item in evaluated)
    unknown = sum(item.status == "UNKNOWN" for item in evaluated)
    outcome = (
        "ELIGIBLE_CANDIDATES"
        if eligible
        else "ABSTAINED"
        if unknown
        else "NO_ELIGIBLE_CANDIDATE"
    )
    context_digest = _digest(
        {
            "context_ref": request.context_ref,
            "hard_constraints": [asdict(item) for item in request.hard_constraints],
            "preferences": [asdict(item) for item in request.preferences],
        }
    )
    result_payload = {
        "policy_version": CONSTRAINT_POLICY_VERSION,
        "context_digest": context_digest,
        "outcome": outcome,
        "candidates": [asdict(item) for item in evaluated],
    }
    return ConstraintEvaluation(
        schema_version="constraint-evaluation/v1",
        policy_version=CONSTRAINT_POLICY_VERSION,
        context_digest=context_digest,
        raw_context_retained=False,
        outcome=outcome,
        candidates=tuple(evaluated),
        result_digest=_digest(result_payload),
    )
