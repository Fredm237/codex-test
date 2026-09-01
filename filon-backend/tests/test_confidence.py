from __future__ import annotations

import pytest

from app.confidence.engine import (
    PROBABILITY_DIMENSIONS,
    ConfidenceError,
    ConfidenceRequest,
    CoverageInput,
    DimensionSignal,
    EmpiricalBin,
    EmpiricalCalibrationProfile,
    calibrate_confidence,
)


def _profile(dimension: str, *, support: int = 100) -> EmpiricalCalibrationProfile:
    return EmpiricalCalibrationProfile(
        dimension,
        f"profile:{dimension.lower()}:v1",
        "calibrator/v1",
        50,
        support,
        "0.010000",
        "0.160000",
        (EmpiricalBin("0", "1", "0.700000", support, int(support * 0.7)),),
        (f"holdout:{dimension}",),
    )


def test_dimensions_are_calibrated_independently_without_additive_score() -> None:
    signals = tuple(
        DimensionSignal(dimension, "0.8", (f"evidence:{dimension}",))
        for dimension in PROBABILITY_DIMENSIONS
    )
    profiles = tuple(_profile(dimension) for dimension in PROBABILITY_DIMENSIONS)
    report = calibrate_confidence(
        ConfidenceRequest("case:1", signals, CoverageInput(5, 4, ("e1", "e2", "e3", "e4"))),
        profiles,
    )
    assert report.outcome == "CONFIDENCE_CALIBRATED"
    assert {item.probability_decimal for item in report.dimensions} == {"0.700000"}
    assert report.evidence_coverage.ratio_decimal == "0.800000"
    assert report.raw_context_retained is False


def test_decision_confidence_is_never_derived_from_other_dimensions() -> None:
    signals = tuple(
        DimensionSignal(dimension, "0.9", (f"evidence:{dimension}",))
        for dimension in PROBABILITY_DIMENSIONS
        if dimension != "DECISION_CONFIDENCE"
    )
    profiles = tuple(
        _profile(dimension)
        for dimension in PROBABILITY_DIMENSIONS
        if dimension != "DECISION_CONFIDENCE"
    )
    report = calibrate_confidence(
        ConfidenceRequest("case:2", signals, CoverageInput(4, 4, ("e1", "e2", "e3", "e4"))),
        profiles,
    )
    decision = next(item for item in report.dimensions if item.dimension == "DECISION_CONFIDENCE")
    assert decision.state == "UNKNOWN"
    assert decision.probability_decimal is None
    assert report.outcome == "PARTIAL_CONFIDENCE"


def test_missing_profile_missing_provenance_and_low_support_fail_closed() -> None:
    no_profile = calibrate_confidence(
        ConfidenceRequest(
            "case:3",
            (DimensionSignal("RETRIEVAL_CONFIDENCE", "0.9", ("evidence:1",)),),
            CoverageInput(0, 0),
        ),
        (),
    )
    retrieval = no_profile.dimensions[0]
    assert retrieval.state == "UNKNOWN" and retrieval.probability_decimal is None
    no_provenance = calibrate_confidence(
        ConfidenceRequest(
            "case:4",
            (DimensionSignal("RETRIEVAL_CONFIDENCE", "0.9"),),
            CoverageInput(0, 0),
        ),
        (_profile("RETRIEVAL_CONFIDENCE"),),
    )
    assert no_provenance.dimensions[0].state == "INVALID"
    low = EmpiricalCalibrationProfile(
        "RETRIEVAL_CONFIDENCE",
        "profile:low",
        "v1",
        50,
        10,
        "0.1",
        "0.2",
        (EmpiricalBin("0", "1", "0.7", 10, 7),),
        ("holdout:low",),
    )
    low_report = calibrate_confidence(
        ConfidenceRequest(
            "case:5",
            (DimensionSignal("RETRIEVAL_CONFIDENCE", "0.9", ("evidence:1",)),),
            CoverageInput(0, 0),
        ),
        (low,),
    )
    assert low_report.dimensions[0].state == "INSUFFICIENT_SUPPORT"
    assert low_report.dimensions[0].probability_decimal is None


def test_invalid_probabilities_counts_and_coverage_are_rejected() -> None:
    with pytest.raises(ConfidenceError, match="between 0 and 1"):
        DimensionSignal("RETRIEVAL_CONFIDENCE", "1.1", ("e",))
    with pytest.raises(ConfidenceError, match="observed frequency"):
        EmpiricalBin("0", "1", "0.9", 10, 8)
    with pytest.raises(ConfidenceError, match="exceed"):
        CoverageInput(1, 2, ("e1", "e2"))
    with pytest.raises(ConfidenceError, match="unique"):
        ConfidenceRequest(
            "case",
            (
                DimensionSignal("RETRIEVAL_CONFIDENCE", None),
                DimensionSignal("RETRIEVAL_CONFIDENCE", None),
            ),
            CoverageInput(0, 0),
        )
