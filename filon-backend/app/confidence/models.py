"""Persistance append-only Confidence Phase 9."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, JSON, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.offer_optimization import models as offer_optimization_models  # noqa: F401


class ConfidenceCalibrationRun(Base):
    __tablename__ = "confidence_calibration_runs"
    __table_args__ = (
        UniqueConstraint("run_key", name="uq_confidence_calibration_run_key"),
        UniqueConstraint(
            "offer_optimization_run_id", "policy_version", "evaluated_at",
            name="uq_confidence_calibration_identity",
        ),
        CheckConstraint("length(run_key) = 64", name="ck_confidence_run_key_sha256"),
        CheckConstraint("length(context_digest) = 71", name="ck_confidence_context_digest"),
        CheckConstraint("length(result_digest) = 71", name="ck_confidence_result_digest"),
        CheckConstraint("raw_context_retained = false", name="ck_confidence_no_raw_context"),
        CheckConstraint(
            "outcome IN ('CONFIDENCE_CALIBRATED', 'PARTIAL_CONFIDENCE', 'ABSTAINED')",
            name="ck_confidence_outcome",
        ),
        CheckConstraint("dimension_count = 5", name="ck_confidence_dimension_count"),
        CheckConstraint(
            "calibrated_dimension_count >= 0 AND calibrated_dimension_count <= dimension_count",
            name="ck_confidence_calibrated_count",
        ),
        CheckConstraint(
            "evidence_coverage_state IN ('MEASURED', 'UNKNOWN')",
            name="ck_confidence_coverage_state",
        ),
        CheckConstraint(
            "(evidence_coverage_state = 'MEASURED' AND evidence_coverage_ratio IS NOT NULL "
            "AND evidence_required_count > 0) OR "
            "(evidence_coverage_state = 'UNKNOWN' AND evidence_coverage_ratio IS NULL "
            "AND evidence_required_count = 0 AND evidence_observed_count = 0)",
            name="ck_confidence_coverage_shape",
        ),
        CheckConstraint(
            "evidence_observed_count >= 0 AND evidence_required_count >= 0 "
            "AND evidence_observed_count <= evidence_required_count",
            name="ck_confidence_coverage_counts",
        ),
        Index("ix_confidence_outcome_evaluated", "outcome", "evaluated_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    run_key: Mapped[str] = mapped_column(String(64))
    offer_optimization_run_id: Mapped[int] = mapped_column(
        ForeignKey("offer_optimization_runs.id", ondelete="CASCADE"), index=True
    )
    context_digest: Mapped[str] = mapped_column(String(71), index=True)
    raw_context_retained: Mapped[bool] = mapped_column(Boolean, default=False)
    policy_version: Mapped[str] = mapped_column(String(64), index=True)
    outcome: Mapped[str] = mapped_column(String(32), index=True)
    dimension_count: Mapped[int]
    calibrated_dimension_count: Mapped[int]
    evidence_coverage_state: Mapped[str] = mapped_column(String(16), index=True)
    evidence_coverage_ratio: Mapped[str | None] = mapped_column(String(16), nullable=True)
    evidence_observed_count: Mapped[int]
    evidence_required_count: Mapped[int]
    evidence_refs_json: Mapped[list[str]] = mapped_column(JSON)
    result_digest: Mapped[str] = mapped_column(String(71), index=True)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ConfidenceDimensionRecord(Base):
    __tablename__ = "confidence_dimension_records"
    __table_args__ = (
        UniqueConstraint("run_id", "dimension", name="uq_confidence_dimension"),
        CheckConstraint(
            "dimension IN ('RETRIEVAL_CONFIDENCE', 'ENTITY_MATCH_CONFIDENCE', "
            "'ATTRIBUTE_CONFIDENCE', 'OFFER_CONFIDENCE', 'DECISION_CONFIDENCE')",
            name="ck_confidence_dimension",
        ),
        CheckConstraint(
            "state IN ('CALIBRATED', 'UNKNOWN', 'INVALID', 'INSUFFICIENT_SUPPORT')",
            name="ck_confidence_dimension_state",
        ),
        CheckConstraint(
            "(state = 'CALIBRATED' AND probability_decimal IS NOT NULL "
            "AND sample_size > 0 AND profile_ref IS NOT NULL) OR "
            "(state <> 'CALIBRATED' AND probability_decimal IS NULL)",
            name="ck_confidence_dimension_shape",
        ),
        CheckConstraint("sample_size >= 0", name="ck_confidence_dimension_sample_size"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("confidence_calibration_runs.id", ondelete="CASCADE"), index=True
    )
    dimension: Mapped[str] = mapped_column(String(32), index=True)
    state: Mapped[str] = mapped_column(String(32), index=True)
    probability_decimal: Mapped[str | None] = mapped_column(String(16), nullable=True)
    sample_size: Mapped[int]
    profile_ref: Mapped[str | None] = mapped_column(String(191), nullable=True)
    reason_codes_json: Mapped[list[str]] = mapped_column(JSON)
    evidence_refs_json: Mapped[list[str]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
