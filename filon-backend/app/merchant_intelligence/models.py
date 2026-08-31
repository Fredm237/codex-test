"""Snapshots mesurés et append-only de qualité marchand."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MerchantQualitySnapshot(Base):
    """Compteurs bruts ; aucun score de fiabilité n'est déduit."""

    __tablename__ = "merchant_quality_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "merchant_id",
            "window_first_raw_id",
            "window_last_raw_id",
            "policy_version",
            name="uq_merchant_quality_window_policy",
        ),
        CheckConstraint(
            "merchant_status IN ('INDEXED', 'AFFILIATED', 'DIRECT_PARTNER', "
            "'MARKETPLACE', 'UNVERIFIED')",
            name="ck_merchant_quality_status",
        ),
        CheckConstraint(
            "window_first_raw_id <= window_last_raw_id",
            name="ck_merchant_quality_window",
        ),
        CheckConstraint(
            "source_record_count > 0 AND offer_observation_count >= 0 "
            "AND gtin_known_count >= 0 AND price_known_count >= 0 "
            "AND price_fresh_count >= 0 AND stock_known_count >= 0 "
            "AND merchant_link_known_count >= 0 AND invalid_link_count >= 0 "
            "AND identity_resolved_count >= 0 AND eligible_offer_count >= 0",
            name="ck_merchant_quality_nonnegative",
        ),
        CheckConstraint(
            "offer_observation_count <= source_record_count "
            "AND gtin_known_count <= source_record_count "
            "AND price_known_count <= source_record_count "
            "AND price_fresh_count <= price_known_count "
            "AND stock_known_count <= source_record_count "
            "AND merchant_link_known_count <= source_record_count "
            "AND invalid_link_count <= source_record_count "
            "AND identity_resolved_count <= source_record_count "
            "AND eligible_offer_count <= source_record_count",
            name="ck_merchant_quality_bounded",
        ),
        CheckConstraint(
            "feed_age_seconds IS NULL OR feed_age_seconds >= 0",
            name="ck_merchant_quality_feed_age",
        ),
        Index("ix_merchant_quality_status_time", "merchant_status", "evaluated_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), index=True)
    merchant_status: Mapped[str] = mapped_column(String(24))
    window_first_raw_id: Mapped[int] = mapped_column(Integer)
    window_last_raw_id: Mapped[int] = mapped_column(Integer)
    source_record_count: Mapped[int] = mapped_column(Integer)
    offer_observation_count: Mapped[int] = mapped_column(Integer)
    gtin_known_count: Mapped[int] = mapped_column(Integer)
    price_known_count: Mapped[int] = mapped_column(Integer)
    price_fresh_count: Mapped[int] = mapped_column(Integer)
    stock_known_count: Mapped[int] = mapped_column(Integer)
    merchant_link_known_count: Mapped[int] = mapped_column(Integer)
    invalid_link_count: Mapped[int] = mapped_column(Integer)
    identity_resolved_count: Mapped[int] = mapped_column(Integer)
    eligible_offer_count: Mapped[int] = mapped_column(Integer)
    latest_observed_at: Mapped[datetime] = mapped_column(DateTime)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime)
    feed_age_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    measurement_states_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    policy_version: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
    )
