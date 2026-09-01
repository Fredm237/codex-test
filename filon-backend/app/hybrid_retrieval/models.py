"""Persistance append-only Hybrid Retrieval Phase 5."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
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

from app.db.base import Base


class HybridRetrievalRun(Base):
    __tablename__ = "hybrid_retrieval_runs"
    __table_args__ = (
        UniqueConstraint("run_key", name="uq_hybrid_retrieval_run_key"),
        UniqueConstraint(
            "query_digest",
            "retrieval_version",
            "fusion_version",
            "snapshot_ref",
            "evaluated_at",
            name="uq_hybrid_retrieval_run_evaluation",
        ),
        CheckConstraint("length(run_key) = 64", name="ck_hybrid_retrieval_run_key_sha256"),
        CheckConstraint("length(query_digest) = 71", name="ck_hybrid_retrieval_query_digest"),
        CheckConstraint("raw_query_retained = false", name="ck_hybrid_retrieval_no_raw_query"),
        CheckConstraint("locale IN ('fr', 'nl', 'en')", name="ck_hybrid_retrieval_locale"),
        CheckConstraint(
            "outcome IN ('CANDIDATES', 'NO_MATCH', 'AMBIGUOUS', 'ERROR')",
            name="ck_hybrid_retrieval_outcome",
        ),
        Index("ix_hybrid_retrieval_outcome_evaluated", "outcome", "evaluated_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    run_key: Mapped[str] = mapped_column(String(64))
    query_ref: Mapped[str] = mapped_column(String(128))
    query_digest: Mapped[str] = mapped_column(String(71), index=True)
    raw_query_retained: Mapped[bool] = mapped_column(Boolean, default=False)
    locale: Mapped[str] = mapped_column(String(2), index=True)
    country_code: Mapped[str | None] = mapped_column(String(2), nullable=True)
    intent_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    sources_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    outcome: Mapped[str] = mapped_column(String(16), index=True)
    reason_codes_json: Mapped[list[str]] = mapped_column(JSON)
    retrieval_version: Mapped[str] = mapped_column(String(64), index=True)
    fusion_version: Mapped[str] = mapped_column(String(64), index=True)
    index_versions_json: Mapped[dict[str, str]] = mapped_column(JSON)
    snapshot_ref: Mapped[str] = mapped_column(String(128), index=True)
    result_digest: Mapped[str] = mapped_column(String(71), index=True)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class HybridRetrievalCandidate(Base):
    __tablename__ = "hybrid_retrieval_candidates"
    __table_args__ = (
        UniqueConstraint("run_id", "candidate_rank", name="uq_hybrid_candidate_rank"),
        UniqueConstraint("run_id", "entity_ref", name="uq_hybrid_candidate_entity"),
        CheckConstraint("candidate_rank > 0", name="ck_hybrid_candidate_rank_positive"),
        CheckConstraint(
            "candidate_status IN ('ELIGIBLE_SHADOW', 'QUARANTINED')",
            name="ck_hybrid_candidate_status",
        ),
        CheckConstraint(
            "entity_type IN ('PRODUCT', 'MODEL', 'VARIANT')",
            name="ck_hybrid_candidate_entity_type",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("hybrid_retrieval_runs.id", ondelete="CASCADE"), index=True
    )
    candidate_rank: Mapped[int]
    candidate_status: Mapped[str] = mapped_column(String(24), index=True)
    entity_type: Mapped[str] = mapped_column(String(16), index=True)
    entity_ref: Mapped[str] = mapped_column(String(191), index=True)
    group_key: Mapped[str] = mapped_column(String(191))
    rrf_score: Mapped[str] = mapped_column(String(32))
    offer_ids_json: Mapped[list[int]] = mapped_column(JSON)
    source_evidence_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
