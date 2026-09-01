"""Persistance append-only Offer Optimization Phase 8."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, JSON, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.offer_truth import models as offer_truth_models  # noqa: F401
from app.product_ranking import models as product_ranking_models  # noqa: F401


class OfferOptimizationRun(Base):
    __tablename__ = "offer_optimization_runs"
    __table_args__ = (
        UniqueConstraint("run_key", name="uq_offer_optimization_run_key"),
        UniqueConstraint(
            "product_ranking_run_id", "context_digest", "policy_version", "evaluated_at",
            name="uq_offer_optimization_identity",
        ),
        CheckConstraint("length(run_key) = 64", name="ck_offer_optimization_run_key_sha256"),
        CheckConstraint("length(context_digest) = 71", name="ck_offer_optimization_context_digest"),
        CheckConstraint("length(result_digest) = 71", name="ck_offer_optimization_result_digest"),
        CheckConstraint("raw_context_retained = false", name="ck_offer_optimization_no_raw_context"),
        CheckConstraint(
            "outcome IN ('OFFER_SELECTED', 'ABSTAINED', 'NO_ELIGIBLE_OFFER')",
            name="ck_offer_optimization_outcome",
        ),
        CheckConstraint("candidate_count >= 0", name="ck_offer_optimization_candidate_count"),
        CheckConstraint("selected_count IN (0, 1)", name="ck_offer_optimization_selected_count"),
        CheckConstraint("eligible_count >= 0", name="ck_offer_optimization_eligible_count"),
        CheckConstraint("unoptimizable_count >= 0", name="ck_offer_optimization_unoptimizable_count"),
        CheckConstraint("ineligible_count >= 0", name="ck_offer_optimization_ineligible_count"),
        CheckConstraint(
            "candidate_count = selected_count + eligible_count + "
            "unoptimizable_count + ineligible_count",
            name="ck_offer_optimization_candidate_count_sum",
        ),
        CheckConstraint(
            "(outcome = 'OFFER_SELECTED' AND selected_product_ref IS NOT NULL "
            "AND selected_offer_ref IS NOT NULL AND selected_count = 1) OR "
            "(outcome <> 'OFFER_SELECTED' AND selected_offer_ref IS NULL AND selected_count = 0)",
            name="ck_offer_optimization_selection_shape",
        ),
        Index("ix_offer_optimization_outcome_evaluated", "outcome", "evaluated_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    run_key: Mapped[str] = mapped_column(String(64))
    product_ranking_run_id: Mapped[int] = mapped_column(
        ForeignKey("product_ranking_runs.id", ondelete="CASCADE"), index=True
    )
    context_digest: Mapped[str] = mapped_column(String(71), index=True)
    raw_context_retained: Mapped[bool] = mapped_column(Boolean, default=False)
    policy_version: Mapped[str] = mapped_column(String(64), index=True)
    outcome: Mapped[str] = mapped_column(String(32), index=True)
    selected_product_ref: Mapped[str | None] = mapped_column(String(191), nullable=True, index=True)
    selected_offer_ref: Mapped[str | None] = mapped_column(String(191), nullable=True, index=True)
    candidate_count: Mapped[int]
    selected_count: Mapped[int]
    eligible_count: Mapped[int]
    unoptimizable_count: Mapped[int]
    ineligible_count: Mapped[int]
    result_digest: Mapped[str] = mapped_column(String(71), index=True)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class OfferOptimizationCandidate(Base):
    __tablename__ = "offer_optimization_candidates"
    __table_args__ = (
        UniqueConstraint("run_id", "offer_truth_snapshot_id", name="uq_offer_optimization_candidate"),
        UniqueConstraint("run_id", "selection_rank", name="uq_offer_optimization_selection_rank"),
        CheckConstraint(
            "status IN ('SELECTED', 'ELIGIBLE', 'UNOPTIMIZABLE', 'INELIGIBLE')",
            name="ck_offer_optimization_candidate_status",
        ),
        CheckConstraint(
            "(status = 'SELECTED' AND selection_rank = 1 AND total_cost IS NOT NULL AND currency IS NOT NULL) OR "
            "(status = 'ELIGIBLE' AND selection_rank IS NULL AND total_cost IS NOT NULL AND currency IS NOT NULL) OR "
            "(status IN ('UNOPTIMIZABLE', 'INELIGIBLE') AND selection_rank IS NULL "
            "AND total_cost IS NULL AND currency IS NULL)",
            name="ck_offer_optimization_candidate_shape",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("offer_optimization_runs.id", ondelete="CASCADE"), index=True
    )
    offer_truth_snapshot_id: Mapped[int] = mapped_column(
        ForeignKey("offer_truth_snapshots.id", ondelete="CASCADE"), index=True
    )
    offer_ref: Mapped[str] = mapped_column(String(191), index=True)
    product_ref: Mapped[str] = mapped_column(String(191), index=True)
    status: Mapped[str] = mapped_column(String(16), index=True)
    selection_rank: Mapped[int | None] = mapped_column(nullable=True, index=True)
    total_cost: Mapped[str | None] = mapped_column(String(32), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    merchant_reliability: Mapped[str | None] = mapped_column(String(32), nullable=True)
    freshness: Mapped[str | None] = mapped_column(String(32), nullable=True)
    reason_codes_json: Mapped[list[str]] = mapped_column(JSON)
    evidence_refs_json: Mapped[list[str]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
