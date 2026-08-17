"""Contrats internes de lecture et de provenance de la couche Intelligence."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Literal

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
    confidence: float
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
        if self.price is None or not self.currency:
            return Evidence(
                field="price",
                value="unknown",
                status="unknown",
                source_type="core",
                source_ref=f"offer:{self.offer_id}",
                confidence=0.0,
                observed_at=self._observed_at_iso,
            )
        return Evidence(
            field="price",
            value=f"{self.price:.2f} {self.currency}",
            status="verified",
            source_type="core",
            source_ref=f"offer:{self.offer_id}",
            confidence=1.0,
            observed_at=self._observed_at_iso,
        )

    @property
    def availability_evidence(self) -> Evidence:
        status: KnowledgeStatus = "verified" if self.availability != "unknown" else "unknown"
        return Evidence(
            field="availability",
            value=self.availability,
            status=status,
            source_type="core",
            source_ref=f"offer:{self.offer_id}",
            confidence=1.0 if status == "verified" else 0.0,
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
