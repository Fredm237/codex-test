"""Journal opérationnel de la chaîne V2 shadow, sans payload brut."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class V2ChainExecution(Base):
    """Une exécution bornée et traçable de la chaîne V2."""

    __tablename__ = "v2_chain_executions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('running', 'succeeded', 'failed', 'interrupted')",
            name="ck_v2_chain_execution_status",
        ),
        CheckConstraint(
            "mode IN ('dry_run', 'apply')",
            name="ck_v2_chain_execution_mode",
        ),
        CheckConstraint(
            "after_raw_id >= 0 AND row_limit >= 1 AND row_limit <= 100",
            name="ck_v2_chain_execution_window",
        ),
        CheckConstraint(
            "(campaign_id IS NULL AND execution_kind IS NULL "
            "AND source_execution_id IS NULL) OR "
            "(length(campaign_id) = 71 "
            "AND execution_kind IN ('progression', 'replay', 'recovery') "
            "AND ((execution_kind = 'progression' AND source_execution_id IS NULL) "
            "OR (execution_kind IN ('replay', 'recovery') "
            "AND source_execution_id IS NOT NULL)))",
            name="ck_v2_chain_execution_campaign",
        ),
        Index("ix_v2_chain_executions_started", "started_at"),
        Index(
            "ix_v2_chain_campaign_execution",
            "campaign_id",
            "execution_kind",
            "id",
        ),
        Index(
            "uq_v2_chain_executions_running",
            "status",
            unique=True,
            postgresql_where=text("status = 'running'"),
            sqlite_where=text("status = 'running'"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    execution_key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    mode: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(16), default="running", index=True)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime)
    vertical: Mapped[str] = mapped_column(String(64))
    after_raw_id: Mapped[int] = mapped_column(Integer)
    row_limit: Mapped[int] = mapped_column(Integer)
    last_raw_source_id: Mapped[int] = mapped_column(Integer)
    checkpoints_json: Mapped[dict[str, int]] = mapped_column(JSON)
    completed_stages_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    campaign_id: Mapped[str | None] = mapped_column(String(71), nullable=True)
    execution_kind: Mapped[str | None] = mapped_column(String(16), nullable=True)
    source_execution_id: Mapped[int | None] = mapped_column(
        ForeignKey("v2_chain_executions.id", ondelete="RESTRICT"), nullable=True
    )
    window_metrics_json: Mapped[dict[str, object] | None] = mapped_column(
        JSON, nullable=True
    )
    report_evaluation_id: Mapped[str | None] = mapped_column(
        String(71), nullable=True
    )
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    heartbeat_at: Mapped[datetime] = mapped_column(DateTime)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)


class V2LiveDarkReadObservation(Base):
    """Comparaison d'une requête réelle, agrégée et sans texte utilisateur."""

    __tablename__ = "v2_live_dark_read_observations"
    __table_args__ = (
        CheckConstraint(
            "length(observation_key) = 64",
            name="ck_v2_live_dark_observation_key",
        ),
        CheckConstraint(
            "length(campaign_id) = 71",
            name="ck_v2_live_dark_campaign",
        ),
        CheckConstraint(
            "surface IN ('advise', 'advise_stream')",
            name="ck_v2_live_dark_surface",
        ),
        CheckConstraint(
            "core_outcome IN ('CANDIDATES', 'NO_MATCH', 'ERROR')",
            name="ck_v2_live_dark_core_outcome",
        ),
        CheckConstraint(
            "v2_outcome IN ('BUY_NOW', 'WAIT', 'ABSTAIN', 'ERROR', 'UNSUPPORTED')",
            name="ck_v2_live_dark_v2_outcome",
        ),
        CheckConstraint(
            "classification IN ('V2_IMPROVEMENT', 'V1_IMPROVEMENT', "
            "'BOTH_VALID', 'V2_ABSTAINS_CORRECTLY', 'V2_UNSUPPORTED', "
            "'DATA_PROBLEM', 'ENGINE_PROBLEM', 'AMBIGUOUS')",
            name="ck_v2_live_dark_classification",
        ),
        CheckConstraint(
            "core_candidate_count >= 0 AND v2_candidate_count >= 0 "
            "AND core_latency_us >= 0 AND v2_latency_us >= 0",
            name="ck_v2_live_dark_counts_latency",
        ),
        CheckConstraint(
            "safety_state IN ('SAFE', 'ABSTAIN', 'INVALID', 'UNSUPPORTED')",
            name="ck_v2_live_dark_safety_state",
        ),
        CheckConstraint(
            "raw_query_retained = false",
            name="ck_v2_live_dark_no_raw_query",
        ),
        Index(
            "ix_v2_live_dark_classification_evaluated",
            "campaign_id",
            "classification",
            "evaluated_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    observation_key: Mapped[str] = mapped_column(
        String(64), unique=True, index=True
    )
    campaign_id: Mapped[str] = mapped_column(String(71))
    comparison_version: Mapped[str] = mapped_column(String(64))
    surface: Mapped[str] = mapped_column(String(32))
    vertical: Mapped[str | None] = mapped_column(String(32), nullable=True)
    locale: Mapped[str] = mapped_column(String(8))
    country_code: Mapped[str | None] = mapped_column(String(2), nullable=True)
    core_outcome: Mapped[str] = mapped_column(String(16))
    v2_outcome: Mapped[str] = mapped_column(String(16))
    classification: Mapped[str] = mapped_column(String(32))
    core_candidate_count: Mapped[int] = mapped_column(Integer)
    v2_candidate_count: Mapped[int] = mapped_column(Integer)
    core_latency_us: Mapped[int] = mapped_column(Integer)
    v2_latency_us: Mapped[int] = mapped_column(Integer)
    chain_complete: Mapped[bool] = mapped_column(Boolean)
    safety_state: Mapped[str] = mapped_column(String(16))
    provenance_complete: Mapped[bool] = mapped_column(Boolean)
    raw_query_retained: Mapped[bool] = mapped_column(Boolean, default=False)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class V2DarkReadObservation(Base):
    """Comparaison agrégée V2/Core, sans requête ni payload brut."""

    __tablename__ = "v2_dark_read_observations"
    __table_args__ = (
        UniqueConstraint(
            "hybrid_run_id",
            "comparison_version",
            "evaluated_at",
            name="uq_v2_dark_read_evaluation",
        ),
        CheckConstraint(
            "length(observation_key) = 64",
            name="ck_v2_dark_read_observation_key_sha256",
        ),
        CheckConstraint(
            "length(query_digest) = 71",
            name="ck_v2_dark_read_query_digest",
        ),
        CheckConstraint(
            "raw_query_retained = false",
            name="ck_v2_dark_read_no_raw_query",
        ),
        CheckConstraint(
            "core_outcome IN ('CANDIDATES', 'NO_MATCH', 'INVALID')",
            name="ck_v2_dark_read_core_outcome",
        ),
        CheckConstraint(
            "v2_outcome IN ('CANDIDATES', 'NO_MATCH', 'AMBIGUOUS', 'ERROR')",
            name="ck_v2_dark_read_v2_outcome",
        ),
        CheckConstraint(
            "top1_state IN ('MATCH', 'MISMATCH', 'UNKNOWN')",
            name="ck_v2_dark_read_top1_state",
        ),
        CheckConstraint(
            "terminal_offer_state IN ('MATCH', 'MISMATCH', 'UNKNOWN')",
            name="ck_v2_dark_read_terminal_offer_state",
        ),
        CheckConstraint(
            "terminal_outcome IN ('BUY_NOW', 'WAIT', 'ABSTAIN', 'INCOMPLETE')",
            name="ck_v2_dark_read_terminal_outcome",
        ),
        CheckConstraint(
            "safety_state IN ('SAFE', 'ABSTAIN', 'INVALID', 'INCOMPLETE')",
            name="ck_v2_dark_read_safety_state",
        ),
        CheckConstraint(
            "core_candidate_count >= 0 AND v2_candidate_count >= 0 "
            "AND intersection_count >= 0",
            name="ck_v2_dark_read_candidate_counts",
        ),
        CheckConstraint(
            "overlap_ppm >= 0 AND overlap_ppm <= 1000000",
            name="ck_v2_dark_read_overlap_ppm",
        ),
        Index(
            "ix_v2_dark_read_safety_evaluated",
            "safety_state",
            "evaluated_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    observation_key: Mapped[str] = mapped_column(
        String(64), unique=True, index=True
    )
    hybrid_run_id: Mapped[int] = mapped_column(
        ForeignKey("hybrid_retrieval_runs.id", ondelete="CASCADE"),
        index=True,
    )
    query_digest: Mapped[str] = mapped_column(String(71), index=True)
    raw_query_retained: Mapped[bool] = mapped_column(Boolean, default=False)
    comparison_version: Mapped[str] = mapped_column(String(64), index=True)
    core_outcome: Mapped[str] = mapped_column(String(16), index=True)
    v2_outcome: Mapped[str] = mapped_column(String(16), index=True)
    core_candidate_count: Mapped[int] = mapped_column(Integer)
    v2_candidate_count: Mapped[int] = mapped_column(Integer)
    intersection_count: Mapped[int] = mapped_column(Integer)
    overlap_ppm: Mapped[int] = mapped_column(Integer)
    top1_state: Mapped[str] = mapped_column(String(16), index=True)
    chain_complete: Mapped[bool] = mapped_column(Boolean, index=True)
    terminal_outcome: Mapped[str] = mapped_column(String(16), index=True)
    terminal_offer_state: Mapped[str] = mapped_column(String(16), index=True)
    safety_state: Mapped[str] = mapped_column(String(16), index=True)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class V2CanaryReadObservation(Base):
    """Télémétrie canary agrégée, sans requête ni identité."""

    __tablename__ = "v2_canary_read_observations"
    __table_args__ = (
        CheckConstraint(
            "length(observation_key) = 64",
            name="ck_v2_canary_observation_key_sha256",
        ),
        CheckConstraint(
            "length(gate_evaluation_id) = 71",
            name="ck_v2_canary_gate_evaluation_digest",
        ),
        CheckConstraint(
            "eligibility_evaluation_id IS NULL OR "
            "length(eligibility_evaluation_id) = 71",
            name="ck_v2_canary_eligibility_digest",
        ),
        CheckConstraint(
            "(eligibility_evaluation_id IS NULL AND eligibility_status IS NULL "
            "AND vertical IS NULL AND locale IS NULL AND decision_type IS NULL) OR "
            "(eligibility_evaluation_id IS NOT NULL "
            "AND eligibility_status IN ('eligible', 'ineligible') "
            "AND vertical IS NOT NULL AND locale IS NOT NULL "
            "AND decision_type IS NOT NULL)",
            name="ck_v2_canary_eligibility_bundle",
        ),
        CheckConstraint(
            "cohort IN ('core', 'canary')",
            name="ck_v2_canary_cohort",
        ),
        CheckConstraint(
            "source IN ('core_v1', 'v2')",
            name="ck_v2_canary_source",
        ),
        CheckConstraint(
            "response_type IN ('CORE', 'ABSTAIN', 'BUY_NOW', 'WAIT')",
            name="ck_v2_canary_response_type",
        ),
        CheckConstraint(
            "safety_state IS NULL OR safety_state IN ('SAFE', 'ABSTAIN', 'INVALID')",
            name="ck_v2_canary_safety_state",
        ),
        CheckConstraint(
            "core_latency_us >= 0 AND total_latency_us >= core_latency_us "
            "AND (v2_latency_us IS NULL OR v2_latency_us >= 0)",
            name="ck_v2_canary_latency",
        ),
        CheckConstraint(
            "raw_query_retained = false",
            name="ck_v2_canary_no_raw_query",
        ),
        CheckConstraint(
            "(source = 'core_v1' AND response_type = 'CORE' "
            "AND fallback_reason IS NOT NULL) OR "
            "(source = 'v2' AND cohort = 'canary' AND response_type != 'CORE' "
            "AND fallback_reason IS NULL AND v2_latency_us IS NOT NULL "
            "AND eligibility_status = 'eligible' "
            "AND chain_complete = true AND provenance_complete = true "
            "AND safety_state IN ('SAFE', 'ABSTAIN'))",
            name="ck_v2_canary_atomic_source",
        ),
        Index(
            "ix_v2_canary_source_evaluated",
            "source",
            "evaluated_at",
        ),
        Index(
            "ix_v2_canary_gate_evaluated",
            "gate_evaluation_id",
            "evaluated_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    observation_key: Mapped[str] = mapped_column(
        String(64), unique=True, index=True
    )
    gate_evaluation_id: Mapped[str] = mapped_column(String(71), index=True)
    cohort: Mapped[str] = mapped_column(String(16), index=True)
    assignment_reason: Mapped[str] = mapped_column(String(64))
    eligibility_evaluation_id: Mapped[str | None] = mapped_column(
        String(71), nullable=True, index=True
    )
    eligibility_status: Mapped[str | None] = mapped_column(String(16), nullable=True)
    vertical: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    locale: Mapped[str | None] = mapped_column(String(8), nullable=True, index=True)
    decision_type: Mapped[str | None] = mapped_column(
        String(32), nullable=True, index=True
    )
    source: Mapped[str] = mapped_column(String(16), index=True)
    response_type: Mapped[str] = mapped_column(String(16), index=True)
    fallback_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)
    core_latency_us: Mapped[int] = mapped_column(Integer)
    v2_latency_us: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_latency_us: Mapped[int] = mapped_column(Integer)
    chain_complete: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    safety_state: Mapped[str | None] = mapped_column(String(16), nullable=True)
    provenance_complete: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    raw_query_retained: Mapped[bool] = mapped_column(Boolean, default=False)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class V2PromotionReceipt(Base):
    """Reçu append-only d'une décision de promotion V2."""

    __tablename__ = "v2_promotion_receipts"
    __table_args__ = (
        CheckConstraint(
            "promotion_stage IN ('shadow_to_canary', 'canary_to_public')",
            name="ck_v2_promotion_stage",
        ),
        CheckConstraint(
            "(promotion_stage = 'shadow_to_canary' "
            "AND status IN ('CANARY_HOLD', 'CANARY_AUTHORIZED')) OR "
            "(promotion_stage = 'canary_to_public' "
            "AND status IN ('PUBLIC_HOLD', 'PUBLIC_AUTHORIZED'))",
            name="ck_v2_promotion_stage_status",
        ),
        CheckConstraint(
            "length(evaluation_id) = 71 AND length(gate_evaluation_id) = 71",
            name="ck_v2_promotion_evaluation_digests",
        ),
        CheckConstraint(
            "(promotion_stage = 'shadow_to_canary' "
            "AND source_gate_evaluation_id IS NULL) OR "
            "(promotion_stage = 'canary_to_public' "
            "AND length(source_gate_evaluation_id) = 71)",
            name="ck_v2_promotion_source_gate",
        ),
        CheckConstraint(
            "raw_payload_retained = false",
            name="ck_v2_promotion_no_raw_payload",
        ),
        Index(
            "ix_v2_promotion_stage_evaluated",
            "promotion_stage",
            "evaluated_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    evaluation_id: Mapped[str] = mapped_column(String(71), unique=True, index=True)
    gate_evaluation_id: Mapped[str] = mapped_column(String(71), index=True)
    source_gate_evaluation_id: Mapped[str | None] = mapped_column(
        String(71), nullable=True, index=True
    )
    promotion_stage: Mapped[str] = mapped_column(String(32), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    authorized_response_types_json: Mapped[list[str]] = mapped_column(JSON)
    blocked_response_types_json: Mapped[list[str]] = mapped_column(JSON)
    gates_json: Mapped[dict[str, bool]] = mapped_column(JSON)
    metrics_json: Mapped[dict[str, object]] = mapped_column(JSON)
    proof_refs_json: Mapped[dict[str, str]] = mapped_column(JSON)
    policy_json: Mapped[dict[str, object]] = mapped_column(JSON)
    raw_payload_retained: Mapped[bool] = mapped_column(Boolean, default=False)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class V2PromotionProof(Base):
    """Référence append-only vers un artefact externe vérifié, sans contenu brut."""

    __tablename__ = "v2_promotion_proofs"
    __table_args__ = (
        CheckConstraint(
            "length(proof_ref) = 71 AND length(scope_ref) = 71 "
            "AND length(artifact_digest) = 71",
            name="ck_v2_promotion_proof_digests",
        ),
        CheckConstraint(
            "verification_status IN ('VERIFIED', 'REJECTED')",
            name="ck_v2_promotion_proof_status",
        ),
        CheckConstraint(
            "raw_payload_retained = false",
            name="ck_v2_promotion_proof_no_raw_payload",
        ),
        Index(
            "ix_v2_promotion_proof_scope_kind_verified",
            "scope_ref",
            "proof_kind",
            "verified_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    proof_ref: Mapped[str] = mapped_column(String(71), unique=True, index=True)
    scope_ref: Mapped[str] = mapped_column(String(71), index=True)
    proof_kind: Mapped[str] = mapped_column(String(64), index=True)
    artifact_ref: Mapped[str] = mapped_column(String(512))
    artifact_digest: Mapped[str] = mapped_column(String(71))
    verifier_version: Mapped[str] = mapped_column(String(64))
    verification_status: Mapped[str] = mapped_column(String(16), index=True)
    raw_payload_retained: Mapped[bool] = mapped_column(Boolean, default=False)
    verified_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
