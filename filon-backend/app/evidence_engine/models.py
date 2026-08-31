"""Registre append-only des claims et de l'éligibilité décisionnelle."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    JSON,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EvidenceClaimRecord(Base):
    """Claim versionné ; une preuve absente ne peut porter de valeur."""

    __tablename__ = "evidence_claim_records"
    __table_args__ = (
        UniqueConstraint(
            "offer_observation_id",
            "claim_code",
            "policy_version",
            "evaluated_at",
            name="uq_evidence_claim_evaluation",
        ),
        CheckConstraint(
            "knowledge_status IN ('VERIFIED', 'INFERRED', 'UNKNOWN')",
            name="ck_evidence_claim_knowledge",
        ),
        CheckConstraint(
            "eligibility IN ('eligible', 'ineligible', 'unknown')",
            name="ck_evidence_claim_eligibility",
        ),
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="ck_evidence_claim_confidence",
        ),
        CheckConstraint(
            "(eligibility = 'eligible' AND knowledge_status = 'VERIFIED' "
            "AND value_json IS NOT NULL) OR eligibility <> 'eligible'",
            name="ck_evidence_claim_eligible_value",
        ),
        CheckConstraint(
            "(knowledge_status = 'UNKNOWN' AND value_json IS NULL) OR "
            "knowledge_status <> 'UNKNOWN'",
            name="ck_evidence_claim_unknown_value",
        ),
        Index("ix_evidence_claim_policy_state", "claim_code", "eligibility"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    raw_source_record_id: Mapped[int] = mapped_column(
        ForeignKey("raw_source_records.id"),
        index=True,
    )
    offer_observation_id: Mapped[int] = mapped_column(
        ForeignKey("graph_offer_observations.id"),
        index=True,
    )
    subject_type: Mapped[str] = mapped_column(String(24))
    subject_ref: Mapped[str] = mapped_column(String(96))
    claim_code: Mapped[str] = mapped_column(String(48), index=True)
    value_json: Mapped[Any | None] = mapped_column(JSON(none_as_null=True), nullable=True)
    knowledge_status: Mapped[str] = mapped_column(String(16))
    source_type: Mapped[str] = mapped_column(String(48))
    source_ref: Mapped[str] = mapped_column(String(96))
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    eligibility: Mapped[str] = mapped_column(String(16), index=True)
    reason_code: Mapped[str] = mapped_column(String(48))
    policy_version: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class DecisionEligibilityRecord(Base):
    """Plus haut niveau autorisé, sans verdict fort implicite."""

    __tablename__ = "decision_eligibility_records"
    __table_args__ = (
        UniqueConstraint(
            "offer_observation_id",
            "policy_version",
            "evaluated_at",
            name="uq_decision_eligibility_evaluation",
        ),
        CheckConstraint(
            "highest_stage IN ('DISCOVERABLE', 'COMPARABLE', 'RANKABLE', "
            "'DECISION_ELIGIBLE')",
            name="ck_decision_eligibility_stage",
        ),
        CheckConstraint(
            "(decision_eligible IS TRUE AND highest_stage = 'DECISION_ELIGIBLE') OR "
            "(decision_eligible IS FALSE AND highest_stage <> 'DECISION_ELIGIBLE')",
            name="ck_decision_eligibility_consistency",
        ),
        Index("ix_decision_eligibility_stage", "highest_stage", "evaluated_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    raw_source_record_id: Mapped[int] = mapped_column(
        ForeignKey("raw_source_records.id"),
        index=True,
    )
    offer_observation_id: Mapped[int] = mapped_column(
        ForeignKey("graph_offer_observations.id"),
        index=True,
    )
    offer_id: Mapped[int] = mapped_column(ForeignKey("offers.id"), index=True)
    highest_stage: Mapped[str] = mapped_column(String(24), index=True)
    decision_eligible: Mapped[bool] = mapped_column(Boolean)
    blocker_reason: Mapped[str] = mapped_column(String(48))
    evaluated_at: Mapped[datetime] = mapped_column(DateTime)
    policy_version: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
