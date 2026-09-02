"""Composeur déterministe multi-domaine Phase 17.

Le moteur assemble les rôles obligatoires d'une solution. Il réemploie les
éléments possédés avant toute offre et ne produit aucun score de qualité.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Sequence


SOLUTION_COMPOSER_POLICY_VERSION = "solution-composer-policy/v1"
SOLUTION_KINDS = {"outfit", "setup", "kit", "routine"}


class SolutionComposerError(ValueError):
    """Entrée hors contrat ou composition impossible à défendre."""


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


def _refs(refs: tuple[str, ...]) -> None:
    if not refs or any(not isinstance(ref, str) or not ref for ref in refs):
        raise SolutionComposerError("evidence refs must be non-empty strings")
    if len(set(refs)) != len(refs):
        raise SolutionComposerError("evidence refs must be unique")


@dataclass(frozen=True)
class CompositionRequest:
    context_ref: str
    solution_kind: str
    required_slots: tuple[str, ...]
    maximum_budget: str | None
    currency: str | None

    def __post_init__(self) -> None:
        if not self.context_ref:
            raise SolutionComposerError("context ref is required")
        if self.solution_kind not in SOLUTION_KINDS:
            raise SolutionComposerError("solution kind is invalid")
        if not self.required_slots or any(not slot for slot in self.required_slots):
            raise SolutionComposerError("required slots are invalid")
        if len(set(self.required_slots)) != len(self.required_slots):
            raise SolutionComposerError("required slots must be unique")
        budget = _decimal(self.maximum_budget, allow_zero=False)
        if self.maximum_budget is not None and budget is None:
            raise SolutionComposerError("maximum budget is invalid")
        if self.currency is not None and (
            len(self.currency) != 3 or not self.currency.isascii() or not self.currency.isupper()
        ):
            raise SolutionComposerError("currency is invalid")
        if (self.maximum_budget is None) != (self.currency is None):
            raise SolutionComposerError("budget and currency must be provided together")


@dataclass(frozen=True)
class ComponentCandidate:
    component_ref: str
    slot: str
    source: str
    constraint_status: str
    amount: str | None
    currency: str | None
    offer_ref: str | None
    offer_truth_status: str | None
    duplicate_with_owned: bool | None
    evidence_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        prefix, separator, suffix = self.component_ref.partition(":")
        if not separator or prefix not in {"owned", "product", "model", "variant"} or not suffix:
            raise SolutionComposerError("component ref is invalid")
        if not self.slot:
            raise SolutionComposerError("slot is required")
        if self.source not in {"owned", "catalogue"}:
            raise SolutionComposerError("component source is invalid")
        if self.constraint_status not in {"ELIGIBLE", "EXCLUDED", "UNKNOWN"}:
            raise SolutionComposerError("constraint status is invalid")
        _refs(self.evidence_refs)
        if self.source == "owned":
            if prefix != "owned" or any(
                value is not None
                for value in (self.amount, self.currency, self.offer_ref, self.offer_truth_status, self.duplicate_with_owned)
            ):
                raise SolutionComposerError("owned component shape is invalid")
            return
        if prefix == "owned" or not self.offer_ref or not self.offer_ref.startswith("offer:"):
            raise SolutionComposerError("catalogue component refs are invalid")
        if self.offer_truth_status not in {"VERIFIED", "PARTIAL", "STALE", "INVALID", "QUARANTINED"}:
            raise SolutionComposerError("offer truth status is invalid")
        if _decimal(self.amount, allow_zero=False) is None:
            raise SolutionComposerError("catalogue amount is invalid")
        if self.currency is None or len(self.currency) != 3 or not self.currency.isupper():
            raise SolutionComposerError("catalogue currency is invalid")
        if not isinstance(self.duplicate_with_owned, bool):
            raise SolutionComposerError("catalogue duplicate evidence is required")


@dataclass(frozen=True)
class SelectedComponent:
    slot: str
    component_ref: str
    source: str
    offer_ref: str | None
    amount: str
    currency: str | None
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True)
class CompositionResult:
    schema_version: str
    policy_version: str
    context_digest: str
    raw_context_retained: bool
    solution_kind: str
    outcome: str
    reason_code: str
    selected: tuple[SelectedComponent, ...]
    owned_count: int
    purchase_count: int
    total_cost: str | None
    currency: str | None
    utility_score: None
    measurement_status: str
    result_digest: str


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _eligible_catalogue(candidate: ComponentCandidate, request: CompositionRequest) -> bool:
    return (
        candidate.source == "catalogue"
        and candidate.constraint_status == "ELIGIBLE"
        and candidate.offer_truth_status == "VERIFIED"
        and candidate.duplicate_with_owned is False
        and request.currency is not None
        and candidate.currency == request.currency
    )


def _abstain(request: CompositionRequest, reason: str) -> CompositionResult:
    context_digest = _digest(asdict(request))
    body = {
        "schema_version": "solution-composer/v1",
        "policy_version": SOLUTION_COMPOSER_POLICY_VERSION,
        "context_digest": context_digest,
        "raw_context_retained": False,
        "solution_kind": request.solution_kind,
        "outcome": "ABSTAINED",
        "reason_code": reason,
        "selected": (),
        "owned_count": 0,
        "purchase_count": 0,
        "total_cost": None,
        "currency": None,
        "utility_score": None,
        "measurement_status": "not_calibrated",
    }
    return CompositionResult(**body, result_digest=_digest(body))


def compose_solution(
    request: CompositionRequest,
    candidates: Sequence[ComponentCandidate],
) -> CompositionResult:
    refs = [candidate.component_ref for candidate in candidates]
    if len(refs) != len(set(refs)):
        raise SolutionComposerError("candidate component refs must be unique")

    selected: list[ComponentCandidate] = []
    for slot in request.required_slots:
        owned = sorted(
            (
                candidate
                for candidate in candidates
                if candidate.slot == slot
                and candidate.source == "owned"
                and candidate.constraint_status == "ELIGIBLE"
            ),
            key=lambda candidate: candidate.component_ref,
        )
        if owned:
            selected.append(owned[0])
            continue
        catalogue = sorted(
            (candidate for candidate in candidates if candidate.slot == slot and _eligible_catalogue(candidate, request)),
            key=lambda candidate: (_decimal(candidate.amount) or Decimal("Infinity"), candidate.component_ref),
        )
        if not catalogue:
            return _abstain(request, f"required_slot_unavailable:{slot}")
        selected.append(catalogue[0])

    purchases = [candidate for candidate in selected if candidate.source == "catalogue"]
    if purchases and request.maximum_budget is None:
        return _abstain(request, "purchase_budget_unspecified")
    total = sum((_decimal(candidate.amount) or Decimal("0") for candidate in purchases), Decimal("0"))
    maximum = _decimal(request.maximum_budget)
    if maximum is not None and total > maximum:
        return _abstain(request, "solution_budget_exceeded")

    components = tuple(
        SelectedComponent(
            slot=candidate.slot,
            component_ref=candidate.component_ref,
            source=candidate.source,
            offer_ref=candidate.offer_ref,
            amount="0" if candidate.source == "owned" else str(_decimal(candidate.amount)),
            currency=None if candidate.source == "owned" else candidate.currency,
            evidence_refs=candidate.evidence_refs,
        )
        for candidate in selected
    )
    context_digest = _digest(asdict(request))
    body = {
        "schema_version": "solution-composer/v1",
        "policy_version": SOLUTION_COMPOSER_POLICY_VERSION,
        "context_digest": context_digest,
        "raw_context_retained": False,
        "solution_kind": request.solution_kind,
        "outcome": "SOLUTION_COMPOSED",
        "reason_code": "owned_first_constraints_satisfied",
        "selected": components,
        "owned_count": len(components) - len(purchases),
        "purchase_count": len(purchases),
        "total_cost": str(total),
        "currency": request.currency if purchases else None,
        "utility_score": None,
        "measurement_status": "not_calibrated",
    }
    digest_body = {**body, "selected": tuple(asdict(component) for component in components)}
    return CompositionResult(**body, result_digest=_digest(digest_body))
