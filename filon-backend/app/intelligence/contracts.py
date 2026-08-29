"""Contrats internes de lecture et de provenance de la couche Intelligence."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Literal

from app.services.currency import normalize_currency_code
from app.services.freshness import offer_observation_is_fresh

KnowledgeStatus = Literal["verified", "inferred", "unknown"]
Availability = Literal["in_stock", "out_of_stock", "unknown"]


@dataclass(frozen=True)
class Evidence:
    """Une justification compacte, transportable jusqu’à l’interface."""

    field: str
    value: str
    status: KnowledgeStatus
    source_type: str
    source_ref: str
    # Conservé pour compatibilité de schéma, mais jamais rempli par une
    # probabilité artificielle avant calibration sur un jeu indépendant.
    confidence: float | None
    observed_at: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class CoreOfferSnapshot:
    """Vue lecture seule d’une offre réellement exploitable par un expert."""

    offer_id: int
    catalog_product_id: int | None
    name: str
    brand: str | None
    filon_category: str | None
    filon_subcategory: str | None
    offer_kind: str | None
    price: float | None
    currency: str | None
    availability: Availability
    image_url: str | None
    deep_link: str | None
    merchant_id: int
    merchant_name: str
    merchant_region: str | None
    observed_at: datetime | None

    @property
    def price_evidence(self) -> Evidence:
        currency = normalize_currency_code(self.currency)
        if (
            self.price is None
            or isinstance(self.price, bool)
            or not math.isfinite(self.price)
            or self.price <= 0
            or currency is None
            or not offer_observation_is_fresh(self.observed_at)
        ):
            return Evidence(
                field="price",
                value="unknown",
                status="unknown",
                source_type="core",
                source_ref=f"offer:{self.offer_id}",
                confidence=None,
                observed_at=self._observed_at_iso,
            )
        return Evidence(
            field="price",
            value=f"{self.price:.2f} {currency}",
            status="verified",
            source_type="core",
            source_ref=f"offer:{self.offer_id}",
            confidence=None,
            observed_at=self._observed_at_iso,
        )

    @property
    def availability_evidence(self) -> Evidence:
        status: KnowledgeStatus = (
            "verified"
            if self.availability != "unknown"
            and offer_observation_is_fresh(self.observed_at)
            else "unknown"
        )
        return Evidence(
            field="availability",
            value=self.availability if status == "verified" else "unknown",
            status=status,
            source_type="core",
            source_ref=f"offer:{self.offer_id}",
            confidence=None,
            observed_at=self._observed_at_iso,
        )

    @property
    def _observed_at_iso(self) -> str:
        return self.observed_at.isoformat() if self.observed_at else "unknown"

    def as_dict(self) -> dict[str, object]:
        return {
            "offer_id": self.offer_id,
            "catalog_product_id": self.catalog_product_id,
            "name": self.name,
            "brand": self.brand,
            "filon_category": self.filon_category,
            "filon_subcategory": self.filon_subcategory,
            "offer_kind": self.offer_kind,
            "price": self.price,
            "currency": self.currency,
            "availability": self.availability,
            "image_url": self.image_url,
            "deep_link": self.deep_link,
            "merchant": {
                "id": self.merchant_id,
                "name": self.merchant_name,
                "region": self.merchant_region,
            },
            "observed_at": self._observed_at_iso,
            "evidence": [self.price_evidence.as_dict(), self.availability_evidence.as_dict()],
        }
