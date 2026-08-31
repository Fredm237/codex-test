"""Mesure interne et fail-closed de la qualité catalogue."""

from .funnel import (
    FUNNEL_STAGES,
    POLICY_VERSION,
    CatalogQualityFunnelReport,
    build_catalog_quality_funnel,
)

__all__ = [
    "FUNNEL_STAGES",
    "POLICY_VERSION",
    "CatalogQualityFunnelReport",
    "build_catalog_quality_funnel",
]
