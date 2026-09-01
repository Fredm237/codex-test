"""Persistance append-only des snapshots Offer Truth Phase 3."""

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


class OfferTruthSnapshot(Base):
    """Snapshot temporel immuable ; le JSON reste sous contrat v1."""

    __tablename__ = "offer_truth_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "raw_source_record_id",
            "projection_version",
            "policy_version",
            "evaluated_at",
            name="uq_offer_truth_snapshot_evaluation",
        ),
        CheckConstraint(
            "length(snapshot_key) = 64",
            name="ck_offer_truth_snapshot_key_sha256",
        ),
        CheckConstraint(
            "offer_status IN ('VERIFIED', 'PARTIAL', 'STALE', 'INVALID', 'QUARANTINED')",
            name="ck_offer_truth_snapshot_status",
        ),
        CheckConstraint(
            "(offer_status = 'QUARANTINED' AND variant_id IS NULL) OR "
            "(offer_status <> 'QUARANTINED' AND variant_id IS NOT NULL)",
            name="ck_offer_truth_snapshot_variant_state",
        ),
        Index(
            "ix_offer_truth_status_evaluated",
            "offer_status",
            "evaluated_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    snapshot_key: Mapped[str] = mapped_column(String(64), unique=True)
    raw_source_record_id: Mapped[int] = mapped_column(
        ForeignKey("raw_source_records.id"),
        index=True,
    )
    offer_id: Mapped[int] = mapped_column(ForeignKey("offers.id"), index=True)
    variant_id: Mapped[int | None] = mapped_column(
        ForeignKey("graph_variants.id"),
        nullable=True,
        index=True,
    )
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), index=True)
    offer_status: Mapped[str] = mapped_column(String(16), index=True)
    claims_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    reason_codes_json: Mapped[list[str]] = mapped_column(JSON)
    projection_version: Mapped[str] = mapped_column(String(64), index=True)
    policy_version: Mapped[str] = mapped_column(String(64), index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
    )
