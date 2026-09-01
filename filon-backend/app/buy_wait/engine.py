"""Moteur Buy/Wait v2 Phase 10.

Le moteur n'effectue aucune prédiction de prix. Il applique une politique
historique versionnée uniquement lorsque l'offre, l'historique, la confiance de
décision et le profil de backtest sont tous prouvés. Toute inconnue produit une
abstention explicite.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from statistics import median
from typing import Any, Sequence


BUY_WAIT_POLICY_VERSION = "buy-wait-policy/v2"
MIN_HISTORY_SAMPLES = 8
MIN_TRACKED_DAYS = 14
MAX_CURRENT_AGE_HOURS = 48
MIN_DECISION_CONFIDENCE = Decimal("0.800000")
MATERIAL_GAP = Decimal("0.050000")
LOW_PERCENTILE_MAX = Decimal("0.250000")
HIGH_PERCENTILE_MIN = Decimal("0.750000")


class BuyWaitError(ValueError):
    """Entrée hors contrat ou décision impossible à défendre."""


def _decimal(value: str, *, field: str, allow_zero: bool = False) -> Decimal:
    try:
        parsed = Decimal(value)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise BuyWaitError(f"{field} must be a decimal string") from exc
    if not parsed.is_finite() or parsed < 0 or (not allow_zero and parsed == 0):
        raise BuyWaitError(f"{field} must be finite and positive")
    return parsed


def _probability(value: str, *, field: str) -> Decimal:
    parsed = _decimal(value, field=field, allow_zero=True)
    if parsed > 1:
        raise BuyWaitError(f"{field} must be between 0 and 1")
    return parsed


def _aware(value: datetime, *, field: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise BuyWaitError(f"{field} must include a timezone")
    return value.astimezone(timezone.utc)


def _refs(refs: tuple[str, ...]) -> None:
    if any(not isinstance(ref, str) or not ref for ref in refs):
        raise BuyWaitError("evidence refs must be non-empty strings")
    if len(refs) != len(set(refs)):
        raise BuyWaitError("evidence refs must be unique")


def _entity_ref(value: str | None, prefixes: set[str], *, field: str) -> None:
    if value is None:
        return
    prefix, separator, suffix = value.partition(":")
    if not separator or prefix not in prefixes or not suffix:
        raise BuyWaitError(f"{field} is invalid")


@dataclass(frozen=True)
class PriceObservation:
    amount_decimal: str
    currency: str
    observed_at: datetime
    in_stock: bool
    evidence_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        _decimal(self.amount_decimal, field="amount_decimal")
        if (
            len(self.currency) != 3
            or not self.currency.isascii()
            or not self.currency.isupper()
        ):
            raise BuyWaitError("currency is invalid")
        _aware(self.observed_at, field="observed_at")
        if not isinstance(self.in_stock, bool):
            raise BuyWaitError("in_stock must be a boolean")
        _refs(self.evidence_refs)
        if not self.evidence_refs:
            raise BuyWaitError("price observation provenance is required")


@dataclass(frozen=True)
class DecisionConfidence:
    state: str
    probability_decimal: str | None
    sample_size: int
    profile_ref: str | None
    evidence_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.state not in {
            "CALIBRATED", "UNKNOWN", "INVALID", "INSUFFICIENT_SUPPORT"
        }:
            raise BuyWaitError("decision confidence state is invalid")
        if (
            isinstance(self.sample_size, bool)
            or not isinstance(self.sample_size, int)
            or self.sample_size < 0
        ):
            raise BuyWaitError("decision confidence sample size is invalid")
        _refs(self.evidence_refs)
        if self.state == "CALIBRATED":
            if self.probability_decimal is None:
                raise BuyWaitError("calibrated decision confidence requires a probability")
            _probability(self.probability_decimal, field="decision confidence")
            if self.sample_size < 1 or not self.profile_ref or not self.evidence_refs:
                raise BuyWaitError("calibrated decision confidence requires support and provenance")
        elif self.probability_decimal is not None:
            raise BuyWaitError("uncalibrated decision confidence cannot carry a probability")


@dataclass(frozen=True)
class BuyWaitRequest:
    context_ref: str
    evaluated_at: datetime
    selected_offer_ref: str | None
    selected_product_ref: str | None
    current: PriceObservation | None
    history: tuple[PriceObservation, ...]
    decision_confidence: DecisionConfidence
    backtest_profile_ref: str | None

    def __post_init__(self) -> None:
        if not self.context_ref:
            raise BuyWaitError("context_ref is required")
        _aware(self.evaluated_at, field="evaluated_at")
        _entity_ref(self.selected_offer_ref, {"offer"}, field="selected_offer_ref")
        _entity_ref(
            self.selected_product_ref,
            {"product", "model", "variant"},
            field="selected_product_ref",
        )
        if (self.selected_offer_ref is None) != (self.selected_product_ref is None):
            raise BuyWaitError("offer and product refs must be present together")
        if self.selected_offer_ref is not None and self.current is None:
            raise BuyWaitError("selected offer requires a current observation")
        if self.backtest_profile_ref is not None and not self.backtest_profile_ref:
            raise BuyWaitError("backtest_profile_ref is invalid")


@dataclass(frozen=True)
class DecisionClaim:
    claim: str
    value: str
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True)
class BuyWaitDecision:
    schema_version: str
    policy_version: str
    trace_id: str
    context_digest: str
    raw_context_retained: bool
    outcome: str
    selected_offer_ref: str | None
    selected_product_ref: str | None
    current_price_decimal: str | None
    currency: str | None
    history_samples: int
    tracked_days: int
    current_percentile_decimal: str | None
    decision_confidence_decimal: str | None
    backtest_profile_ref: str | None
    future_observations_used: bool
    reason_codes: tuple[str, ...]
    claims: tuple[DecisionClaim, ...]
    evidence_refs: tuple[str, ...]
    result_digest: str


def _canonical(value: Any) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    )

def _digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _format_decimal(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.000001")), "f")


def _decision(
    request: BuyWaitRequest,
    *,
    outcome: str,
    reasons: Sequence[str],
    samples: int = 0,
    tracked_days: int = 0,
    percentile: Decimal | None = None,
    claims: Sequence[DecisionClaim] = (),
    evidence_refs: Sequence[str] = (),
) -> BuyWaitDecision:
    current = request.current
    probability = (
        request.decision_confidence.probability_decimal
        if request.decision_confidence.state == "CALIBRATED"
        else None
    )
    payload = {
        "schema_version": "buy-wait-decision/v2",
        "policy_version": BUY_WAIT_POLICY_VERSION,
        "context_digest": _digest({"context_ref": request.context_ref}),
        "raw_context_retained": False,
        "outcome": outcome,
        "selected_offer_ref": request.selected_offer_ref,
        "selected_product_ref": request.selected_product_ref,
        "current_price_decimal": current.amount_decimal if current else None,
        "currency": current.currency if current else None,
        "history_samples": samples,
        "tracked_days": tracked_days,
        "current_percentile_decimal": _format_decimal(percentile) if percentile is not None else None,
        "decision_confidence_decimal": probability,
        "backtest_profile_ref": request.backtest_profile_ref if outcome != "ABSTAIN" else None,
        "future_observations_used": False,
        "reason_codes": list(dict.fromkeys(reasons)),
        "claims": [asdict(item) for item in claims],
        "evidence_refs": list(dict.fromkeys(evidence_refs)),
    }
    trace_id = _digest({"trace": payload})
    result_digest = _digest({**payload, "trace_id": trace_id})
    return BuyWaitDecision(
        trace_id=trace_id,
        result_digest=result_digest,
        claims=tuple(claims),
        evidence_refs=tuple(dict.fromkeys(evidence_refs)),
        reason_codes=tuple(dict.fromkeys(reasons)),
        current_percentile_decimal=payload["current_percentile_decimal"],
        backtest_profile_ref=payload["backtest_profile_ref"],
        **{
            key: value
            for key, value in payload.items()
            if key not in {
                "reason_codes", "claims", "evidence_refs",
                "current_percentile_decimal", "backtest_profile_ref",
            }
        },
    )


def decide_buy_wait(request: BuyWaitRequest) -> BuyWaitDecision:
    """Décide BUY_NOW, WAIT ou ABSTAIN sans jamais lire le futur."""

    if request.selected_offer_ref is None or request.current is None:
        return _decision(request, outcome="ABSTAIN", reasons=("source_selection_missing",))

    evaluated_at = _aware(request.evaluated_at, field="evaluated_at")
    current_at = _aware(request.current.observed_at, field="observed_at")
    if current_at > evaluated_at:
        return _decision(request, outcome="ABSTAIN", reasons=("future_observation_rejected",))
    age_hours = (evaluated_at - current_at).total_seconds() / 3600
    if age_hours > MAX_CURRENT_AGE_HOURS:
        return _decision(request, outcome="ABSTAIN", reasons=("current_observation_stale",))
    if request.current.in_stock is not True:
        return _decision(request, outcome="ABSTAIN", reasons=("current_offer_not_in_stock",))

    confidence = request.decision_confidence
    if confidence.state != "CALIBRATED" or confidence.probability_decimal is None:
        return _decision(request, outcome="ABSTAIN", reasons=("decision_confidence_not_calibrated",))
    probability = _probability(confidence.probability_decimal, field="decision confidence")
    if probability < MIN_DECISION_CONFIDENCE:
        return _decision(request, outcome="ABSTAIN", reasons=("decision_confidence_below_policy",))
    if not request.backtest_profile_ref:
        return _decision(request, outcome="ABSTAIN", reasons=("historical_backtest_profile_missing",))

    usable: list[PriceObservation] = []
    rejected_future = False
    for observation in request.history:
        observed_at = _aware(observation.observed_at, field="observed_at")
        if observed_at > evaluated_at:
            rejected_future = True
            continue
        if observation.currency != request.current.currency or observation.in_stock is not True:
            continue
        usable.append(observation)
    if rejected_future:
        return _decision(request, outcome="ABSTAIN", reasons=("future_observation_rejected",))
    usable.sort(key=lambda item: _aware(item.observed_at, field="observed_at"))
    matches_current = any(
        item.observed_at == request.current.observed_at
        and Decimal(item.amount_decimal) == Decimal(request.current.amount_decimal)
        for item in usable
    )
    if not matches_current or not usable or usable[-1].observed_at != request.current.observed_at:
        return _decision(
            request,
            outcome="ABSTAIN",
            reasons=("current_observation_missing_from_history",),
            samples=len(usable),
        )
    samples = len(usable)
    tracked_days = max(
        0,
        (
            _aware(usable[-1].observed_at, field="observed_at")
            - _aware(usable[0].observed_at, field="observed_at")
        ).days,
    )
    if samples < MIN_HISTORY_SAMPLES:
        return _decision(
            request,
            outcome="ABSTAIN",
            reasons=("history_samples_below_policy",),
            samples=samples,
            tracked_days=tracked_days,
        )
    if tracked_days < MIN_TRACKED_DAYS:
        return _decision(
            request,
            outcome="ABSTAIN",
            reasons=("history_window_below_policy",),
            samples=samples,
            tracked_days=tracked_days,
        )

    prices = [Decimal(item.amount_decimal) for item in usable]
    current_price = Decimal(request.current.amount_decimal)
    historical_median = Decimal(str(median(prices)))
    percentile = Decimal(sum(value <= current_price for value in prices)) / Decimal(samples)
    price_refs = tuple(
        dict.fromkeys(ref for item in usable for ref in item.evidence_refs)
    )
    all_refs = tuple(dict.fromkeys((*price_refs, *confidence.evidence_refs)))
    common_claims = (
        DecisionClaim("current_price_percentile", _format_decimal(percentile), price_refs),
        DecisionClaim("historical_median_price", _format_decimal(historical_median), price_refs),
        DecisionClaim("decision_confidence", confidence.probability_decimal, confidence.evidence_refs),
    )
    if (
        percentile <= LOW_PERCENTILE_MAX
        and current_price <= historical_median * (Decimal("1") - MATERIAL_GAP)
    ):
        return _decision(
            request,
            outcome="BUY_NOW",
            reasons=("current_price_materially_low", "historical_backtest_policy_passed"),
            samples=samples,
            tracked_days=tracked_days,
            percentile=percentile,
            claims=common_claims,
            evidence_refs=all_refs,
        )
    if (
        percentile >= HIGH_PERCENTILE_MIN
        and current_price >= historical_median * (Decimal("1") + MATERIAL_GAP)
    ):
        return _decision(
            request,
            outcome="WAIT",
            reasons=("current_price_materially_high", "historical_backtest_policy_passed"),
            samples=samples,
            tracked_days=tracked_days,
            percentile=percentile,
            claims=common_claims,
            evidence_refs=all_refs,
        )
    return _decision(
        request,
        outcome="ABSTAIN",
        reasons=("price_position_not_actionable",),
        samples=samples,
        tracked_days=tracked_days,
        percentile=percentile,
    )
