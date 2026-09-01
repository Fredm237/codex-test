"""Moteur Confidence Phase 9.

Une probabilité n'est émise qu'à partir d'un bucket empirique dédié à la
dimension évaluée. Les dimensions ne sont jamais additionnées, moyennées ni
converties en un score composite. La couverture des preuves reste un ratio de
complétude et n'est jamais présentée comme une probabilité de justesse.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Sequence


CONFIDENCE_POLICY_VERSION = "confidence-policy/v1"
PROBABILITY_DIMENSIONS = (
    "RETRIEVAL_CONFIDENCE",
    "ENTITY_MATCH_CONFIDENCE",
    "ATTRIBUTE_CONFIDENCE",
    "OFFER_CONFIDENCE",
    "DECISION_CONFIDENCE",
)
DIMENSION_STATES = {"CALIBRATED", "UNKNOWN", "INVALID", "INSUFFICIENT_SUPPORT"}


class ConfidenceError(ValueError):
    """Entrée hors contrat ou probabilité impossible à défendre."""


def _probability(value: str, *, field: str) -> Decimal:
    try:
        parsed = Decimal(value)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ConfidenceError(f"{field} must be a decimal string") from exc
    if not parsed.is_finite() or not Decimal("0") <= parsed <= Decimal("1"):
        raise ConfidenceError(f"{field} must be between 0 and 1")
    return parsed


def _refs(refs: tuple[str, ...]) -> None:
    if any(not isinstance(ref, str) or not ref for ref in refs):
        raise ConfidenceError("evidence refs must be non-empty strings")
    if len(refs) != len(set(refs)):
        raise ConfidenceError("evidence refs must be unique")


@dataclass(frozen=True)
class EmpiricalBin:
    lower_inclusive: str
    upper_inclusive: str
    empirical_probability: str
    sample_size: int
    positive_count: int

    def __post_init__(self) -> None:
        lower = _probability(self.lower_inclusive, field="lower_inclusive")
        upper = _probability(self.upper_inclusive, field="upper_inclusive")
        probability = _probability(
            self.empirical_probability, field="empirical_probability"
        )
        if lower > upper:
            raise ConfidenceError("calibration bin lower bound exceeds upper bound")
        if isinstance(self.sample_size, bool) or not isinstance(self.sample_size, int):
            raise ConfidenceError("sample_size must be an integer")
        if isinstance(self.positive_count, bool) or not isinstance(self.positive_count, int):
            raise ConfidenceError("positive_count must be an integer")
        if self.sample_size < 1 or not 0 <= self.positive_count <= self.sample_size:
            raise ConfidenceError("calibration bin counts are invalid")
        observed = Decimal(self.positive_count) / Decimal(self.sample_size)
        if probability != observed:
            raise ConfidenceError("empirical probability must equal observed frequency")


@dataclass(frozen=True)
class EmpiricalCalibrationProfile:
    dimension: str
    profile_ref: str
    version: str
    minimum_bin_support: int
    evaluated_cases: int
    expected_calibration_error: str
    brier_score: str
    bins: tuple[EmpiricalBin, ...]
    provenance_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.dimension not in PROBABILITY_DIMENSIONS:
            raise ConfidenceError("calibration profile dimension is invalid")
        if not self.profile_ref or not self.version:
            raise ConfidenceError("calibration profile identity is required")
        if (
            isinstance(self.minimum_bin_support, bool)
            or not isinstance(self.minimum_bin_support, int)
            or self.minimum_bin_support < 1
        ):
            raise ConfidenceError("minimum_bin_support must be positive")
        if (
            isinstance(self.evaluated_cases, bool)
            or not isinstance(self.evaluated_cases, int)
            or self.evaluated_cases < 1
        ):
            raise ConfidenceError("evaluated_cases must be positive")
        _probability(self.expected_calibration_error, field="expected_calibration_error")
        _probability(self.brier_score, field="brier_score")
        if not self.bins or sum(item.sample_size for item in self.bins) != self.evaluated_cases:
            raise ConfidenceError("calibration profile support is inconsistent")
        previous_upper: Decimal | None = None
        for item in self.bins:
            lower = Decimal(item.lower_inclusive)
            upper = Decimal(item.upper_inclusive)
            if previous_upper is not None and lower <= previous_upper:
                raise ConfidenceError("calibration bins must be ordered and non-overlapping")
            previous_upper = upper
        _refs(self.provenance_refs)
        if not self.provenance_refs:
            raise ConfidenceError("calibration profile provenance is required")


@dataclass(frozen=True)
class DimensionSignal:
    dimension: str
    raw_score: str | None
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.dimension not in PROBABILITY_DIMENSIONS:
            raise ConfidenceError("confidence signal dimension is invalid")
        if self.raw_score is not None:
            _probability(self.raw_score, field="raw_score")
        _refs(self.evidence_refs)


@dataclass(frozen=True)
class CoverageInput:
    required_evidence_count: int
    observed_evidence_count: int
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name, value in (
            ("required_evidence_count", self.required_evidence_count),
            ("observed_evidence_count", self.observed_evidence_count),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ConfidenceError(f"{name} must be a non-negative integer")
        if self.observed_evidence_count > self.required_evidence_count:
            raise ConfidenceError("observed evidence cannot exceed required evidence")
        _refs(self.evidence_refs)
        if self.observed_evidence_count and not self.evidence_refs:
            raise ConfidenceError("observed evidence requires provenance")


@dataclass(frozen=True)
class ConfidenceRequest:
    context_ref: str
    signals: tuple[DimensionSignal, ...]
    evidence_coverage: CoverageInput

    def __post_init__(self) -> None:
        if not self.context_ref:
            raise ConfidenceError("context_ref is required")
        dimensions = [signal.dimension for signal in self.signals]
        if len(dimensions) != len(set(dimensions)):
            raise ConfidenceError("confidence signals must be unique per dimension")


@dataclass(frozen=True)
class DimensionConfidence:
    dimension: str
    state: str
    probability_decimal: str | None
    sample_size: int
    profile_ref: str | None
    reason_codes: tuple[str, ...]
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True)
class EvidenceCoverage:
    state: str
    ratio_decimal: str | None
    observed_evidence_count: int
    required_evidence_count: int
    reason_codes: tuple[str, ...]
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True)
class ConfidenceReport:
    schema_version: str
    policy_version: str
    context_digest: str
    raw_context_retained: bool
    outcome: str
    dimensions: tuple[DimensionConfidence, ...]
    evidence_coverage: EvidenceCoverage
    result_digest: str


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _calibrate(
    dimension: str,
    signal: DimensionSignal | None,
    profile: EmpiricalCalibrationProfile | None,
) -> DimensionConfidence:
    if signal is None or signal.raw_score is None:
        return DimensionConfidence(
            dimension, "UNKNOWN", None, 0, None, ("signal_unknown",), ()
        )
    if not signal.evidence_refs:
        return DimensionConfidence(
            dimension, "INVALID", None, 0, None, ("signal_provenance_missing",), ()
        )
    if profile is None:
        return DimensionConfidence(
            dimension,
            "UNKNOWN",
            None,
            0,
            None,
            ("empirical_profile_missing",),
            signal.evidence_refs,
        )
    score = Decimal(signal.raw_score)
    selected = next(
        (
            item
            for item in profile.bins
            if Decimal(item.lower_inclusive) <= score <= Decimal(item.upper_inclusive)
        ),
        None,
    )
    if selected is None:
        return DimensionConfidence(
            dimension,
            "INVALID",
            None,
            0,
            profile.profile_ref,
            ("calibration_bucket_missing",),
            signal.evidence_refs,
        )
    refs = tuple(dict.fromkeys((*signal.evidence_refs, *profile.provenance_refs)))
    if selected.sample_size < profile.minimum_bin_support:
        return DimensionConfidence(
            dimension,
            "INSUFFICIENT_SUPPORT",
            None,
            selected.sample_size,
            profile.profile_ref,
            ("calibration_bucket_support_below_minimum",),
            refs,
        )
    return DimensionConfidence(
        dimension,
        "CALIBRATED",
        selected.empirical_probability,
        selected.sample_size,
        profile.profile_ref,
        (),
        refs,
    )


def _coverage(value: CoverageInput) -> EvidenceCoverage:
    if value.required_evidence_count == 0:
        return EvidenceCoverage(
            "UNKNOWN",
            None,
            value.observed_evidence_count,
            value.required_evidence_count,
            ("evidence_requirements_unknown",),
            value.evidence_refs,
        )
    ratio = Decimal(value.observed_evidence_count) / Decimal(value.required_evidence_count)
    return EvidenceCoverage(
        "MEASURED",
        format(ratio.quantize(Decimal("0.000001")), "f"),
        value.observed_evidence_count,
        value.required_evidence_count,
        (),
        value.evidence_refs,
    )


def calibrate_confidence(
    request: ConfidenceRequest,
    profiles: Sequence[EmpiricalCalibrationProfile],
) -> ConfidenceReport:
    """Calibre chaque dimension indépendamment, sans agrégation implicite."""

    profile_map = {profile.dimension: profile for profile in profiles}
    if len(profile_map) != len(profiles):
        raise ConfidenceError("calibration profiles must be unique per dimension")
    signal_map = {signal.dimension: signal for signal in request.signals}
    dimensions = tuple(
        _calibrate(dimension, signal_map.get(dimension), profile_map.get(dimension))
        for dimension in PROBABILITY_DIMENSIONS
    )
    coverage = _coverage(request.evidence_coverage)
    decision = next(item for item in dimensions if item.dimension == "DECISION_CONFIDENCE")
    calibrated_count = sum(item.state == "CALIBRATED" for item in dimensions)
    if decision.state == "CALIBRATED" and coverage.state == "MEASURED":
        outcome = "CONFIDENCE_CALIBRATED"
    elif calibrated_count:
        outcome = "PARTIAL_CONFIDENCE"
    else:
        outcome = "ABSTAINED"
    context_digest = _digest({"context_ref": request.context_ref})
    payload = {
        "schema_version": "confidence-report/v1",
        "policy_version": CONFIDENCE_POLICY_VERSION,
        "context_digest": context_digest,
        "raw_context_retained": False,
        "outcome": outcome,
        "dimensions": [asdict(item) for item in dimensions],
        "evidence_coverage": asdict(coverage),
    }
    return ConfidenceReport(
        schema_version="confidence-report/v1",
        policy_version=CONFIDENCE_POLICY_VERSION,
        context_digest=context_digest,
        raw_context_retained=False,
        outcome=outcome,
        dimensions=dimensions,
        evidence_coverage=coverage,
        result_digest=_digest(payload),
    )
