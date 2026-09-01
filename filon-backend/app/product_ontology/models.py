"""Persistance append-only des assertions Product Ontology Phase 4."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    JSON,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db import models as core_models  # noqa: F401
from app.db.base import Base
from app.observations import models as observation_models  # noqa: F401
from app.product_graph import models as product_graph_models  # noqa: F401


class ProductOntologySnapshot(Base):
    """Assertion temporelle immuable ; les JSON restent sous contrat v1."""

    __tablename__ = "product_ontology_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "raw_source_record_id",
            "projection_version",
            "policy_version",
            "evaluated_at",
            name="uq_product_ontology_snapshot_evaluation",
        ),
        CheckConstraint(
            "length(snapshot_key) = 64",
            name="ck_product_ontology_snapshot_key_sha256",
        ),
        CheckConstraint(
            "ontology_status IN ('VERIFIED', 'PARTIAL', 'QUARANTINED', 'INVALID')",
            name="ck_product_ontology_snapshot_status",
        ),
        CheckConstraint(
            "(ontology_status = 'QUARANTINED' AND variant_id IS NULL) OR "
            "(ontology_status <> 'QUARANTINED' AND variant_id IS NOT NULL)",
            name="ck_product_ontology_snapshot_variant_state",
        ),
        Index(
            "ix_product_ontology_status_evaluated",
            "ontology_status",
            "evaluated_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    snapshot_key: Mapped[str] = mapped_column(String(64), unique=True)
    raw_source_record_id: Mapped[int] = mapped_column(
        ForeignKey("raw_source_records.id"), index=True
    )
    offer_id: Mapped[int] = mapped_column(ForeignKey("offers.id"), index=True)
    variant_id: Mapped[int | None] = mapped_column(
        ForeignKey("graph_variants.id"), nullable=True, index=True
    )
    ontology_status: Mapped[str] = mapped_column(String(16), index=True)
    classification_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    product_role_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    attributes_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    relationships_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    facets_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    legacy_taxonomy_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    reason_codes_json: Mapped[list[str]] = mapped_column(JSON)
    projection_version: Mapped[str] = mapped_column(String(64), index=True)
    policy_version: Mapped[str] = mapped_column(String(64), index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
