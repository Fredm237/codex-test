"""Projection Product Ontology shadow-only."""

from .extraction import (
    EXTRACTOR_VERSION,
    POLICY_VERSION,
    ProductOntologyExtractionError,
    extract_product_ontology,
)

__all__ = [
    "EXTRACTOR_VERSION",
    "POLICY_VERSION",
    "ProductOntologyExtractionError",
    "extract_product_ontology",
]
