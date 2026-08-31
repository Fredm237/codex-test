"""Modèles append-only du shadow Offer Graph."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class GraphOfferObservation(Base):
    """Snapshot sourcé ; une valeur inconnue reste structurellement absente."""

    __tablename__ = "graph_offer_observations"
    __table_args__ = (
        UniqueConstraint(
            "raw_source_record_id",
            "projection_version",
            name="uq_graph_offer_observation_projection",
        ),
        CheckConstraint(
            "price_state IN ('known', 'unknown', 'invalid')",
            name="ck_graph_offer_price_state",
        ),
        CheckConstraint(
            "(price_state = 'known' AND price_amount IS NOT NULL "
            "AND price_currency IS NOT NULL) OR "
            "(price_state <> 'known' AND price_amount IS NULL "
            "AND price_currency IS NULL)",
            name="ck_graph_offer_money_pair",
        ),
        CheckConstraint(
            "availability IN ('in_stock', 'out_of_stock', 'unknown')",
            name="ck_graph_offer_availability",
        ),
        CheckConstraint(
            "merchant_url_state IN ('known', 'unknown', 'invalid')",
            name="ck_graph_offer_url_state",
        ),
        CheckConstraint(
            "(merchant_url_state = 'known' AND merchant_url IS NOT NULL) OR "
            "(merchant_url_state <> 'known' AND merchant_url IS NULL)",
            name="ck_graph_offer_url_value",
        ),
        CheckConstraint(
            "eligibility IN ('eligible', 'ineligible', 'unknown', 'quarantine')",
            name="ck_graph_offer_eligibility",
        ),
        CheckConstraint(
            "reason_code IN ('eligible_exact', 'identity_unresolved', "
            "'missing_price', 'invalid_price', 'missing_currency', "
            "'invalid_currency', 'availability_unknown', 'out_of_stock', "
            "'missing_link', 'invalid_link')",
            name="ck_graph_offer_reason",
        ),
        Index("ix_graph_offer_observation_state", "eligibility", "reason_code"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    raw_source_record_id: Mapped[int] = mapped_column(
        ForeignKey("raw_source_records.id"),
        index=True,
    )
    offer_id: Mapped[int] = mapped_column(ForeignKey("offers.id"), index=True)
    offer_variant_link_id: Mapped[int | None] = mapped_column(
        ForeignKey("graph_offer_variant_links.id"),
        nullable=True,
        index=True,
    )
    price_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 6),
        nullable=True,
    )
    price_currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    price_state: Mapped[str] = mapped_column(String(16))
    availability: Mapped[str] = mapped_column(String(16))
    merchant_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    merchant_url_state: Mapped[str] = mapped_column(String(16))
    eligibility: Mapped[str] = mapped_column(String(16), index=True)
    reason_code: Mapped[str] = mapped_column(String(32))
    projection_version: Mapped[str] = mapped_column(String(64))
    observed_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
    )
