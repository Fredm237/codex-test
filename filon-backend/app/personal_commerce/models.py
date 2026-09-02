"""Journal shadow Personal Commerce Phase 18, sans contexte personnel brut."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, JSON, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.buy_wait import models as buy_wait_models  # noqa: F401
from app.db.base import Base


class PersonalCommerceDecisionRun(Base):
    __tablename__ = "personal_commerce_decision_runs"
    __table_args__ = (
        UniqueConstraint("run_key", name="uq_personal_commerce_run_key"),
        CheckConstraint("length(run_key) = 64", name="ck_personal_commerce_run_key_sha256"),
        CheckConstraint("length(objective_digest) = 71", name="ck_personal_commerce_objective_digest"),
        CheckConstraint("subject_digest IS NULL OR length(subject_digest) = 71", name="ck_personal_commerce_subject_digest"),
        CheckConstraint("length(result_digest) = 71", name="ck_personal_commerce_result_digest"),
        CheckConstraint("raw_context_retained = false", name="ck_personal_commerce_no_raw_context"),
        CheckConstraint(
            "(personalization_consent = true AND subject_digest IS NOT NULL "
            "AND retention_expires_at IS NOT NULL) OR "
            "(personalization_consent = false AND subject_digest IS NULL "
            "AND retention_expires_at IS NULL)",
            name="ck_personal_commerce_consent_subject",
        ),
        CheckConstraint("outcome IN ('SOLUTION_SELECTED', 'ABSTAINED')", name="ck_personal_commerce_outcome"),
        CheckConstraint("action IN ('USE_WHAT_YOU_OWN', 'BUY', 'WAIT', 'ABSTAIN')", name="ck_personal_commerce_action"),
        CheckConstraint(
            "(outcome = 'SOLUTION_SELECTED' AND personalization_consent = true "
            "AND action <> 'ABSTAIN' AND selected_solution_ref IS NOT NULL "
            "AND selected_solution_kind IS NOT NULL) OR "
            "(outcome = 'ABSTAINED' AND action = 'ABSTAIN' "
            "AND selected_solution_ref IS NULL AND selected_solution_kind IS NULL)",
            name="ck_personal_commerce_decision_shape",
        ),
        CheckConstraint(
            "matched_preference_count >= 0 AND eligible_count >= 0 AND rejected_count >= 0",
            name="ck_personal_commerce_counts",
        ),
        CheckConstraint("measurement_status = 'not_calibrated'", name="ck_personal_commerce_no_score"),
        Index("ix_personal_commerce_outcome_evaluated", "outcome", "evaluated_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    run_key: Mapped[str] = mapped_column(String(64))
    buy_wait_run_id: Mapped[int] = mapped_column(
        ForeignKey("buy_wait_decision_runs.id", ondelete="RESTRICT"), index=True
    )
    subject_digest: Mapped[str | None] = mapped_column(String(71), nullable=True, index=True)
    personalization_consent: Mapped[bool] = mapped_column(Boolean)
    retention_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    objective_digest: Mapped[str] = mapped_column(String(71), index=True)
    raw_context_retained: Mapped[bool] = mapped_column(Boolean, default=False)
    policy_version: Mapped[str] = mapped_column(String(64), index=True)
    outcome: Mapped[str] = mapped_column(String(24), index=True)
    action: Mapped[str] = mapped_column(String(24), index=True)
    selected_solution_ref: Mapped[str | None] = mapped_column(String(191), nullable=True)
    selected_solution_kind: Mapped[str | None] = mapped_column(String(32), nullable=True)
    matched_preference_count: Mapped[int] = mapped_column(Integer)
    eligible_count: Mapped[int] = mapped_column(Integer)
    rejected_count: Mapped[int] = mapped_column(Integer)
    measurement_status: Mapped[str] = mapped_column(String(32))
    reason_codes_json: Mapped[list[str]] = mapped_column(JSON)
    result_digest: Mapped[str] = mapped_column(String(71), index=True)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class PersonalCommerceErasureReceipt(Base):
    __tablename__ = "personal_commerce_erasure_receipts"
    __table_args__ = (
        UniqueConstraint("request_key", name="uq_personal_commerce_erasure_request"),
        CheckConstraint("length(request_key) = 64", name="ck_personal_commerce_erasure_key_sha256"),
        CheckConstraint("erased_records >= 0", name="ck_personal_commerce_erased_records"),
        CheckConstraint("verified_empty = true", name="ck_personal_commerce_erasure_verified"),
        CheckConstraint("raw_context_retained = false", name="ck_personal_commerce_erasure_no_raw"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    request_key: Mapped[str] = mapped_column(String(64))
    erased_records: Mapped[int] = mapped_column(Integer)
    verified_empty: Mapped[bool] = mapped_column(Boolean, default=True)
    raw_context_retained: Mapped[bool] = mapped_column(Boolean, default=False)
    erased_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
