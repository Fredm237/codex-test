"""Persistance append-only Constraint Engine Phase 6."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, JSON, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ConstraintEvaluationRun(Base):
    __tablename__ = "constraint_evaluation_runs"
    __table_args__ = (
        UniqueConstraint("run_key", name="uq_constraint_evaluation_run_key"),
        UniqueConstraint(
            "retrieval_run_id", "context_digest", "policy_version", "evaluated_at",
            name="uq_constraint_evaluation_identity",
        ),
        CheckConstraint("length(run_key) = 64", name="ck_constraint_run_key_sha256"),
        CheckConstraint("length(context_digest) = 71", name="ck_constraint_context_digest"),
        CheckConstraint("length(result_digest) = 71", name="ck_constraint_result_digest"),
        CheckConstraint("raw_context_retained = false", name="ck_constraint_no_raw_context"),
        CheckConstraint(
            "outcome IN ('ELIGIBLE_CANDIDATES', 'NO_ELIGIBLE_CANDIDATE', 'ABSTAINED')",
            name="ck_constraint_evaluation_outcome",
        ),
        CheckConstraint("candidate_count >= 0", name="ck_constraint_candidate_count"),
        CheckConstraint("eligible_count >= 0", name="ck_constraint_eligible_count"),
        CheckConstraint("excluded_count >= 0", name="ck_constraint_excluded_count"),
        CheckConstraint("unknown_count >= 0", name="ck_constraint_unknown_count"),
        Index("ix_constraint_outcome_evaluated", "outcome", "evaluated_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    run_key: Mapped[str] = mapped_column(String(64))
    retrieval_run_id: Mapped[int] = mapped_column(
        ForeignKey("hybrid_retrieval_runs.id", ondelete="CASCADE"), index=True
    )
    context_digest: Mapped[str] = mapped_column(String(71), index=True)
    raw_context_retained: Mapped[bool] = mapped_column(Boolean, default=False)
    policy_version: Mapped[str] = mapped_column(String(64), index=True)
    outcome: Mapped[str] = mapped_column(String(32), index=True)
    candidate_count: Mapped[int]
    eligible_count: Mapped[int]
    excluded_count: Mapped[int]
    unknown_count: Mapped[int]
    result_digest: Mapped[str] = mapped_column(String(71), index=True)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ConstraintCandidateEvaluation(Base):
    __tablename__ = "constraint_candidate_evaluations"
    __table_args__ = (
        UniqueConstraint("run_id", "retrieval_candidate_id", name="uq_constraint_candidate_evaluation"),
        CheckConstraint(
            "status IN ('ELIGIBLE', 'EXCLUDED', 'UNKNOWN')",
            name="ck_constraint_candidate_status",
        ),
        CheckConstraint(
            "entity_type IN ('PRODUCT', 'MODEL', 'VARIANT')",
            name="ck_constraint_candidate_entity_type",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("constraint_evaluation_runs.id", ondelete="CASCADE"), index=True
    )
    retrieval_candidate_id: Mapped[int] = mapped_column(
        ForeignKey("hybrid_retrieval_candidates.id", ondelete="CASCADE"), index=True
    )
    entity_type: Mapped[str] = mapped_column(String(16), index=True)
    entity_ref: Mapped[str] = mapped_column(String(191), index=True)
    status: Mapped[str] = mapped_column(String(16), index=True)
    hard_results_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    preference_results_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    reason_codes_json: Mapped[list[str]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
