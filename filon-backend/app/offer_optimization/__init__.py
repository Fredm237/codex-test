"""Offer Optimization Phase 8, strictement shadow et fail-closed."""

from .engine import (
    AvailabilityFact,
    MoneyFact,
    OfferCandidateFacts,
    OfferOptimization,
    OfferOptimizationError,
    OptimizationRequest,
    ScoreFact,
    optimize_offers,
)

__all__ = [
    "AvailabilityFact",
    "MoneyFact",
    "OfferCandidateFacts",
    "OfferOptimization",
    "OfferOptimizationError",
    "OptimizationRequest",
    "ScoreFact",
    "optimize_offers",
]
