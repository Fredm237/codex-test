"""Projection shadow des faits temporels d'une offre FILON."""

from .extraction import (
    EXTRACTOR_VERSION,
    FRESHNESS_POLICY_VERSION,
    OFFER_TRUTH_POLICY_VERSION,
    OfferTruthExtractionError,
    extract_awin_offer_truth,
)

__all__ = [
    "EXTRACTOR_VERSION",
    "FRESHNESS_POLICY_VERSION",
    "OFFER_TRUTH_POLICY_VERSION",
    "OfferTruthExtractionError",
    "extract_awin_offer_truth",
]
