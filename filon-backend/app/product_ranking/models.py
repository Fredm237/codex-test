"""Persistance append-only Product Ranking Phase 7."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, JSON, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ProductRankingRun(Base):
    __tablename__ = "product_ranking_runs"
    __table_args__ = (
        UniqueConstraint("run_key", name="uq_product_ranking_run_key"),
        UniqueConstraint(
            "constraint_run_id", "context_digest", "policy_version", "evaluated_at",
            name="uq_product_ranking_identity",
        ),
        CheckConstraint("length(run_key) = 64", name="ck_product_ranking_run_key_sha256"),
        CheckConstraint("length(context_digest) = 71", name="ck_product_ranking_context_digest"),
        CheckConstraint("length(result_digest) = 71", name="ck_product_ranking_result_digest"),
        CheckConstraint("raw_context_retained = false", name="ck_product_ranking_no_raw_context"),
        CheckConstraint(
            "vertical IN ('smartphones', 'laptops', 'audio', 'fashion', 'appliances_hvac', 'tyres')",
            name="ck_product_ranking_vertical",
        ),
        CheckConstraint(
            "outcome IN ('RANKED_PRODUCTS', 'ABSTAINED', 'NO_ELIGIBLE_PRODUCT')",
            name="ck_product_ranking_outcome",
        ),
        CheckConstraint("candidate_count >= 0", name="ck_product_ranking_candidate_count"),
        CheckConstraint("ranked_count >= 0", name="ck_product_ranking_ranked_count"),
        CheckConstraint("unrankable_count >= 0", name="ck_product_ranking_unrankable_count"),
        CheckConstraint("ineligible_count >= 0", name="ck_product_ranking_ineligible_count"),
        Index("ix_product_ranking_outcome_evaluated", "outcome", "evaluated_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    run_key: Mapped[str] = mapped_column(String(64))
    constraint_run_id: Mapped[int] = mapped_column(
        ForeignKey("constraint_evaluation_runs.id", ondelete="CASCADE"), index=True
    )
    context_digest: Mapped[str] = mapped_column(String(71), index=True)
    raw_context_retained: Mapped[bool] = mapped_column(Boolean, default=False)
    policy_version: Mapped[str] = mapped_column(String(64), index=True)
    vertical: Mapped[str] = mapped_column(String(32), index=True)
    outcome: Mapped[str] = mapped_column(String(32), index=True)
    candidate_count: Mapped[int]
    ranked_count: Mapped[int]
    unrankable_count: Mapped[int]
    ineligible_count: Mapped[int]
    result_digest: Mapped[str] = mapped_column(String(71), index=True)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ProductRankingCandidate(Base):
    __tablename__ = "product_ranking_candidates"
    __table_args__ = (
        UniqueConstraint("run_id", "constraint_candidate_id", name="uq_product_ranking_candidate"),
        UniqueConstraint("run_id", "product_rank", name="uq_product_ranking_position"),
        CheckConstraint(
            "status IN ('RANKED', 'UNRANKABLE', 'INELIGIBLE')",
            name="ck_product_ranking_candidate_status",
        ),
        CheckConstraint(
            "entity_type IN ('PRODUCT', 'MODEL', 'VARIANT')",
            name="ck_product_ranking_candidate_entity_type",
        ),
        CheckConstraint(
            "(status = 'RANKED' AND product_rank IS NOT NULL AND product_rank > 0 AND utility IS NOT NULL) OR "
            "(status <> 'RANKED' AND product_rank IS NULL AND utility IS NULL)",
            name="ck_product_ranking_position_shape",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("product_ranking_runs.id", ondelete="CASCADE"), index=True
    )
    constraint_candidate_id: Mapped[int] = mapped_column(
        ForeignKey("constraint_candidate_evaluations.id", ondelete="CASCADE"), index=True
    )
    entity_type: Mapped[str] = mapped_column(String(16), index=True)
    entity_ref: Mapped[str] = mapped_column(String(191), index=True)
    status: Mapped[str] = mapped_column(String(16), index=True)
    product_rank: Mapped[int | None] = mapped_column(nullable=True, index=True)
    utility: Mapped[str | None] = mapped_column(String(32), nullable=True)
    dimensions_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    reason_codes_json: Mapped[list[str]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
