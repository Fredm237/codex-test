"""Constraint Engine Phase 6, strictement shadow."""

from .engine import (
    CONSTRAINT_POLICY_VERSION,
    CandidateFacts,
    ConstraintRequest,
    Fact,
    HardConstraint,
    Preference,
    evaluate_constraints,
)

__all__ = [
    "CONSTRAINT_POLICY_VERSION",
    "CandidateFacts",
    "ConstraintRequest",
    "Fact",
    "HardConstraint",
    "Preference",
    "evaluate_constraints",
]
