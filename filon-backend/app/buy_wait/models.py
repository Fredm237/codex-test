"""Persistance append-only BUY/WAIT V2 Phase 10."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, JSON, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.confidence import models as confidence_models  # noqa: F401
from app.db.base import Base


class BuyWaitDecisionRun(Base):
    __tablename__ = "buy_wait_decision_runs"
    __table_args__ = (
        UniqueConstraint("run_key", name="uq_buy_wait_run_key"),
        UniqueConstraint(
            "confidence_run_id", "policy_version", "evaluated_at",
            name="uq_buy_wait_identity",
        ),
        CheckConstraint("length(run_key) = 64", name="ck_buy_wait_run_key_sha256"),
        CheckConstraint("length(context_digest) = 71", name="ck_buy_wait_context_digest"),
        CheckConstraint("length(result_digest) = 71", name="ck_buy_wait_result_digest"),
        CheckConstraint("raw_context_retained = false", name="ck_buy_wait_no_raw_context"),
        CheckConstraint("future_observations_used = false", name="ck_buy_wait_no_future"),
        CheckConstraint("outcome IN ('BUY_NOW', 'WAIT', 'ABSTAIN')", name="ck_buy_wait_outcome"),
        CheckConstraint("history_samples >= 0 AND tracked_days >= 0", name="ck_buy_wait_support"),
        CheckConstraint(
            "(outcome IN ('BUY_NOW', 'WAIT') AND selected_offer_ref IS NOT NULL "
            "AND selected_product_ref IS NOT NULL AND current_price_decimal IS NOT NULL "
            "AND currency IS NOT NULL AND history_samples >= 8 AND tracked_days >= 14 "
            "AND current_percentile_decimal IS NOT NULL AND decision_confidence_decimal IS NOT NULL "
            "AND backtest_profile_ref IS NOT NULL) OR "
            "(outcome = 'ABSTAIN' AND backtest_profile_ref IS NULL)",
            name="ck_buy_wait_decision_shape",
        ),
        Index("ix_buy_wait_outcome_evaluated", "outcome", "evaluated_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    run_key: Mapped[str] = mapped_column(String(64))
    confidence_run_id: Mapped[int] = mapped_column(
        ForeignKey("confidence_calibration_runs.id", ondelete="CASCADE"), index=True
    )
    context_digest: Mapped[str] = mapped_column(String(71), index=True)
    raw_context_retained: Mapped[bool] = mapped_column(Boolean, default=False)
    policy_version: Mapped[str] = mapped_column(String(64), index=True)
    outcome: Mapped[str] = mapped_column(String(16), index=True)
    selected_offer_ref: Mapped[str | None] = mapped_column(String(191), nullable=True)
    selected_product_ref: Mapped[str | None] = mapped_column(String(191), nullable=True)
    current_price_decimal: Mapped[str | None] = mapped_column(String(32), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    history_samples: Mapped[int]
    tracked_days: Mapped[int]
    current_percentile_decimal: Mapped[str | None] = mapped_column(String(16), nullable=True)
    decision_confidence_decimal: Mapped[str | None] = mapped_column(String(16), nullable=True)
    backtest_profile_ref: Mapped[str | None] = mapped_column(String(191), nullable=True)
    future_observations_used: Mapped[bool] = mapped_column(Boolean, default=False)
    reason_codes_json: Mapped[list[str]] = mapped_column(JSON)
    claims_json: Mapped[list[dict[str, object]]] = mapped_column(JSON)
    evidence_refs_json: Mapped[list[str]] = mapped_column(JSON)
    result_digest: Mapped[str] = mapped_column(String(71), index=True)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
