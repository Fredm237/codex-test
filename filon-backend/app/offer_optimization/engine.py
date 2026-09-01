"""Moteur déterministe Offer Optimization Phase 8.

Le moteur choisit une offre uniquement pour le produit classé numéro un par la
Phase 7. Il optimise une valeur utilisateur défendable et n'accepte jamais la
commission, le statut d'affiliation ou le marchand comme raccourci de qualité.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Sequence


OFFER_OPTIMIZATION_POLICY_VERSION = "offer-optimization-policy/v2"
FACT_STATES = {"known", "unknown", "invalid", "conflict"}
TRUTH_STATUSES = {"VERIFIED", "PARTIAL", "STALE", "INVALID", "QUARANTINED"}
RANKING_OUTCOMES = {"RANKED_PRODUCTS", "ABSTAINED", "NO_ELIGIBLE_PRODUCT"}


class OfferOptimizationError(ValueError):
    """Entrée hors contrat ou sélection impossible à défendre."""


def _decimal(value: str | None, *, allow_zero: bool) -> Decimal | None:
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
class MoneyFact:
    state: str
    amount_decimal: str | None = None
    currency: str | None = None
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.state not in FACT_STATES:
            raise OfferOptimizationError("money fact state is invalid")
        if self.state == "known" and (self.amount_decimal is None or self.currency is None):
            raise OfferOptimizationError("known money fact requires amount and currency")
        if self.state != "known" and (self.amount_decimal is not None or self.currency is not None):
            raise OfferOptimizationError("non-known money fact cannot carry money")
        if self.currency is not None and (
            len(self.currency) != 3 or not self.currency.isascii() or not self.currency.isupper()
        ):
            raise OfferOptimizationError("money currency is invalid")
        _validate_refs(self.evidence_refs)


@dataclass(frozen=True)
class AvailabilityFact:
    state: str
    value: str | None = None
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.state not in FACT_STATES:
            raise OfferOptimizationError("availability fact state is invalid")
        if self.state == "known" and self.value not in {"in_stock", "out_of_stock", "preorder"}:
            raise OfferOptimizationError("known availability is invalid")
        if self.state != "known" and self.value is not None:
            raise OfferOptimizationError("non-known availability cannot carry a value")
        _validate_refs(self.evidence_refs)


@dataclass(frozen=True)
class ScoreFact:
    state: str
    value: str | None = None
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.state not in FACT_STATES:
            raise OfferOptimizationError("score fact state is invalid")
        if self.state == "known" and self.value is None:
            raise OfferOptimizationError("known score fact requires a value")
        if self.state != "known" and self.value is not None:
            raise OfferOptimizationError("non-known score fact cannot carry a value")
        _validate_refs(self.evidence_refs)


@dataclass(frozen=True)
class ReturnPolicyFact:
    state: str
    accepted: bool | None = None
    period_days: int | None = None
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.state not in FACT_STATES:
            raise OfferOptimizationError("return policy fact state is invalid")
        if self.state == "known":
            if not isinstance(self.accepted, bool):
                raise OfferOptimizationError("known return policy requires accepted")
            if self.accepted and (
                isinstance(self.period_days, bool)
                or not isinstance(self.period_days, int)
                or not 0 <= self.period_days <= 3650
            ):
                raise OfferOptimizationError("accepted return policy requires a valid period")
            if self.period_days is not None and (
                isinstance(self.period_days, bool)
                or not isinstance(self.period_days, int)
                or not 0 <= self.period_days <= 3650
            ):
                raise OfferOptimizationError("return period is invalid")
        elif self.accepted is not None or self.period_days is not None:
            raise OfferOptimizationError("non-known return policy cannot carry a value")
        _validate_refs(self.evidence_refs)


def _validate_refs(refs: tuple[str, ...]) -> None:
    if any(not isinstance(ref, str) or not ref for ref in refs):
        raise OfferOptimizationError("evidence refs must be non-empty strings")
    if len(set(refs)) != len(refs):
        raise OfferOptimizationError("evidence refs must be unique")


@dataclass(frozen=True)
class OfferCandidateFacts:
    offer_ref: str
    product_ref: str
    truth_status: str
    price: MoneyFact
    shipping: MoneyFact
    cashback: MoneyFact
    availability: AvailabilityFact
    returns: ReturnPolicyFact
    merchant_reliability: ScoreFact
    freshness: ScoreFact

    def __post_init__(self) -> None:
        if not self.offer_ref.startswith("offer:") or not self.offer_ref.removeprefix("offer:"):
            raise OfferOptimizationError("offer ref is invalid")
        prefix, separator, suffix = self.product_ref.partition(":")
        if not separator or prefix not in {"product", "model", "variant"} or not suffix:
            raise OfferOptimizationError("product ref is invalid")
        if self.truth_status not in TRUTH_STATUSES:
            raise OfferOptimizationError("offer truth status is invalid")


@dataclass(frozen=True)
class OptimizationRequest:
    context_ref: str
    ranking_outcome: str
    selected_product_ref: str | None
    selected_product_rank: int | None

    def __post_init__(self) -> None:
        if not self.context_ref:
            raise OfferOptimizationError("context ref is required")
        if self.ranking_outcome not in RANKING_OUTCOMES:
            raise OfferOptimizationError("ranking outcome is invalid")
        if self.ranking_outcome == "RANKED_PRODUCTS":
            if self.selected_product_ref is None or self.selected_product_rank != 1:
                raise OfferOptimizationError("ranked outcome requires the top product")
            prefix, separator, suffix = self.selected_product_ref.partition(":")
            if not separator or prefix not in {"product", "model", "variant"} or not suffix:
                raise OfferOptimizationError("selected product ref is invalid")
        elif self.selected_product_ref is not None or self.selected_product_rank is not None:
            raise OfferOptimizationError("abstained ranking cannot select a product")


@dataclass(frozen=True)
class OfferEvaluation:
    offer_ref: str
    product_ref: str
    status: str
    selection_rank: int | None
    total_cost: str | None
    cashback_amount: str | None
    landed_cost: str | None
    currency: str | None
    return_period_days: int | None
    merchant_reliability: str | None
    freshness: str | None
    reason_codes: tuple[str, ...]
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True)
class OfferOptimization:
    schema_version: str
    policy_version: str
    context_digest: str
    raw_context_retained: bool
    outcome: str
    selected_product_ref: str | None
    selected_offer_ref: str | None
    evaluations: tuple[OfferEvaluation, ...]
    result_digest: str


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _score(fact: ScoreFact) -> Decimal | None:
    value = _decimal(fact.value, allow_zero=True) if fact.state == "known" else None
    if value is None or value > 1 or not fact.evidence_refs:
        return None
    return value


def _known_money(fact: MoneyFact, *, allow_zero: bool) -> tuple[Decimal, str] | None:
    value = _decimal(fact.amount_decimal, allow_zero=allow_zero) if fact.state == "known" else None
    if value is None or fact.currency is None or not fact.evidence_refs:
        return None
    return value, fact.currency


def _evaluate_candidate(
    request: OptimizationRequest,
    candidate: OfferCandidateFacts,
) -> tuple[OfferEvaluation, tuple[Decimal, Decimal, Decimal, Decimal, str] | None]:
    if request.ranking_outcome != "RANKED_PRODUCTS":
        return OfferEvaluation(
            offer_ref=candidate.offer_ref,
            product_ref=candidate.product_ref,
            status="INELIGIBLE",
            selection_rank=None,
            total_cost=None,
            cashback_amount=None,
            landed_cost=None,
            currency=None,
            return_period_days=None,
            merchant_reliability=None,
            freshness=None,
            reason_codes=("ranking_precondition_not_met",),
            evidence_refs=(),
        ), None
    if candidate.product_ref != request.selected_product_ref:
        return OfferEvaluation(
            offer_ref=candidate.offer_ref,
            product_ref=candidate.product_ref,
            status="INELIGIBLE",
            selection_rank=None,
            total_cost=None,
            cashback_amount=None,
            landed_cost=None,
            currency=None,
            return_period_days=None,
            merchant_reliability=None,
            freshness=None,
            reason_codes=("different_product",),
            evidence_refs=(),
        ), None
    if candidate.truth_status != "VERIFIED":
        return OfferEvaluation(
            offer_ref=candidate.offer_ref,
            product_ref=candidate.product_ref,
            status="INELIGIBLE",
            selection_rank=None,
            total_cost=None,
            cashback_amount=None,
            landed_cost=None,
            currency=None,
            return_period_days=None,
            merchant_reliability=None,
            freshness=None,
            reason_codes=(f"offer_truth_{candidate.truth_status.lower()}",),
            evidence_refs=(),
        ), None
    if candidate.availability.state == "known" and candidate.availability.value != "in_stock":
        return OfferEvaluation(
            offer_ref=candidate.offer_ref,
            product_ref=candidate.product_ref,
            status="INELIGIBLE",
            selection_rank=None,
            total_cost=None,
            cashback_amount=None,
            landed_cost=None,
            currency=None,
            return_period_days=None,
            merchant_reliability=None,
            freshness=None,
            reason_codes=(f"availability_{candidate.availability.value}",),
            evidence_refs=candidate.availability.evidence_refs,
        ), None
    if candidate.returns.state == "known" and candidate.returns.accepted is False:
        return OfferEvaluation(
            offer_ref=candidate.offer_ref,
            product_ref=candidate.product_ref,
            status="INELIGIBLE",
            selection_rank=None,
            total_cost=None,
            cashback_amount=None,
            landed_cost=None,
            currency=None,
            return_period_days=None,
            merchant_reliability=None,
            freshness=None,
            reason_codes=("returns_not_accepted",),
            evidence_refs=candidate.returns.evidence_refs,
        ), None

    price = _known_money(candidate.price, allow_zero=False)
    shipping = _known_money(candidate.shipping, allow_zero=True)
    cashback = _known_money(candidate.cashback, allow_zero=True)
    reliability = _score(candidate.merchant_reliability)
    freshness = _score(candidate.freshness)
    availability_known = (
        candidate.availability.state == "known"
        and candidate.availability.value == "in_stock"
        and bool(candidate.availability.evidence_refs)
    )
    returns_known = (
        candidate.returns.state == "known"
        and candidate.returns.accepted is True
        and isinstance(candidate.returns.period_days, int)
        and not isinstance(candidate.returns.period_days, bool)
        and bool(candidate.returns.evidence_refs)
    )
    missing: list[str] = []
    if price is None:
        missing.append("price_unknown_or_unsourced")
    if shipping is None:
        missing.append("shipping_unknown_or_unsourced")
    if cashback is None:
        missing.append("cashback_unknown_or_unsourced")
    if not availability_known:
        missing.append("availability_unknown_or_unsourced")
    if not returns_known:
        missing.append("returns_unknown_or_unsourced")
    if reliability is None:
        missing.append("merchant_reliability_unknown_or_unsourced")
    if freshness is None:
        missing.append("freshness_unknown_or_unsourced")
    currencies = {
        item[1] for item in (price, shipping, cashback) if item is not None
    }
    if len(currencies) > 1:
        missing.append("currency_conflict")
    gross = price[0] + shipping[0] if price is not None and shipping is not None else None
    if gross is not None and cashback is not None and cashback[0] > gross:
        missing.append("cashback_exceeds_total_cost")
    evidence_refs = tuple(
        sorted(
            set(
                candidate.price.evidence_refs
                + candidate.shipping.evidence_refs
                + candidate.cashback.evidence_refs
                + candidate.availability.evidence_refs
                + candidate.returns.evidence_refs
                + candidate.merchant_reliability.evidence_refs
                + candidate.freshness.evidence_refs
            )
        )
    )
    if missing:
        return OfferEvaluation(
            offer_ref=candidate.offer_ref,
            product_ref=candidate.product_ref,
            status="UNOPTIMIZABLE",
            selection_rank=None,
            total_cost=None,
            cashback_amount=None,
            landed_cost=None,
            currency=None,
            return_period_days=None,
            merchant_reliability=format(reliability, "f") if reliability is not None else None,
            freshness=format(freshness, "f") if freshness is not None else None,
            reason_codes=tuple(missing),
            evidence_refs=evidence_refs,
        ), None

    assert (
        price is not None
        and shipping is not None
        and cashback is not None
        and reliability is not None
        and freshness is not None
        and candidate.returns.period_days is not None
        and gross is not None
    )
    landed = gross - cashback[0]
    evaluation = OfferEvaluation(
        offer_ref=candidate.offer_ref,
        product_ref=candidate.product_ref,
        status="ELIGIBLE",
        selection_rank=None,
        total_cost=format(gross, "f"),
        cashback_amount=format(cashback[0], "f"),
        landed_cost=format(landed, "f"),
        currency=price[1],
        return_period_days=candidate.returns.period_days,
        merchant_reliability=format(reliability, "f"),
        freshness=format(freshness, "f"),
        reason_codes=("verified_landed_cost_returns_and_operational_evidence",),
        evidence_refs=evidence_refs,
    )
    return evaluation, (
        landed,
        -reliability,
        -Decimal(candidate.returns.period_days),
        -freshness,
        candidate.offer_ref,
    )


def optimize_offers(
    request: OptimizationRequest,
    candidates: Sequence[OfferCandidateFacts],
) -> OfferOptimization:
    refs = [candidate.offer_ref for candidate in candidates]
    if len(refs) != len(set(refs)):
        raise OfferOptimizationError("offer refs must be unique")
    evaluated: list[OfferEvaluation] = []
    eligible: list[
        tuple[tuple[Decimal, Decimal, Decimal, Decimal, str], OfferEvaluation]
    ] = []
    for candidate in candidates:
        evaluation, objective = _evaluate_candidate(request, candidate)
        evaluated.append(evaluation)
        if objective is not None:
            eligible.append((objective, evaluation))

    selected_ref = None
    if eligible:
        _objective, selected = min(eligible, key=lambda item: item[0])
        selected_ref = selected.offer_ref
        evaluated = [
            OfferEvaluation(
                offer_ref=item.offer_ref,
                product_ref=item.product_ref,
                status="SELECTED" if item.offer_ref == selected_ref else item.status,
                selection_rank=1 if item.offer_ref == selected_ref else None,
                total_cost=item.total_cost,
                cashback_amount=item.cashback_amount,
                landed_cost=item.landed_cost,
                currency=item.currency,
                return_period_days=item.return_period_days,
                merchant_reliability=item.merchant_reliability,
                freshness=item.freshness,
                reason_codes=item.reason_codes,
                evidence_refs=item.evidence_refs,
            )
            for item in evaluated
        ]
    outcome = (
        "OFFER_SELECTED"
        if selected_ref is not None
        else "ABSTAINED"
        if request.ranking_outcome != "RANKED_PRODUCTS"
        or any(item.status == "UNOPTIMIZABLE" for item in evaluated)
        else "NO_ELIGIBLE_OFFER"
    )
    context_digest = _digest(
        {
            "context_ref": request.context_ref,
            "ranking_outcome": request.ranking_outcome,
            "selected_product_ref": request.selected_product_ref,
            "selected_product_rank": request.selected_product_rank,
        }
    )
    ordered = tuple(sorted(evaluated, key=lambda item: (item.selection_rank is None, item.offer_ref)))
    result_payload = {
        "policy_version": OFFER_OPTIMIZATION_POLICY_VERSION,
        "context_digest": context_digest,
        "outcome": outcome,
        "selected_product_ref": request.selected_product_ref,
        "selected_offer_ref": selected_ref,
        "evaluations": [asdict(item) for item in ordered],
    }
    return OfferOptimization(
        "offer-optimization/v2",
        OFFER_OPTIMIZATION_POLICY_VERSION,
        context_digest,
        False,
        outcome,
        request.selected_product_ref,
        selected_ref,
        ordered,
        _digest(result_payload),
    )
