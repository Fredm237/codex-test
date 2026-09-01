"""Ajoute la persistance Hybrid Retrieval shadow.

Revision ID: f7c5e9a1b3d6
Revises: e6b4d8f0a2c5
Create Date: 2026-09-01 17:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f7c5e9a1b3d6"
down_revision: Union[str, None] = "e6b4d8f0a2c5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "hybrid_retrieval_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("run_key", sa.String(length=64), nullable=False),
        sa.Column("query_ref", sa.String(length=128), nullable=False),
        sa.Column("query_digest", sa.String(length=71), nullable=False),
        sa.Column("raw_query_retained", sa.Boolean(), nullable=False),
        sa.Column("locale", sa.String(length=2), nullable=False),
        sa.Column("country_code", sa.String(length=2), nullable=True),
        sa.Column("intent_json", sa.JSON(), nullable=False),
        sa.Column("sources_json", sa.JSON(), nullable=False),
        sa.Column("outcome", sa.String(length=16), nullable=False),
        sa.Column("reason_codes_json", sa.JSON(), nullable=False),
        sa.Column("retrieval_version", sa.String(length=64), nullable=False),
        sa.Column("fusion_version", sa.String(length=64), nullable=False),
        sa.Column("index_versions_json", sa.JSON(), nullable=False),
        sa.Column("snapshot_ref", sa.String(length=128), nullable=False),
        sa.Column("result_digest", sa.String(length=71), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.CheckConstraint("length(run_key) = 64", name="ck_hybrid_retrieval_run_key_sha256"),
        sa.CheckConstraint("length(query_digest) = 71", name="ck_hybrid_retrieval_query_digest"),
        sa.CheckConstraint("raw_query_retained = false", name="ck_hybrid_retrieval_no_raw_query"),
        sa.CheckConstraint("locale IN ('fr', 'nl', 'en')", name="ck_hybrid_retrieval_locale"),
        sa.CheckConstraint("outcome IN ('CANDIDATES', 'NO_MATCH', 'AMBIGUOUS', 'ERROR')", name="ck_hybrid_retrieval_outcome"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_key", name="uq_hybrid_retrieval_run_key"),
        sa.UniqueConstraint("query_digest", "retrieval_version", "fusion_version", "snapshot_ref", "evaluated_at", name="uq_hybrid_retrieval_run_evaluation"),
    )
    with op.batch_alter_table("hybrid_retrieval_runs") as batch_op:
        for column in ("query_digest", "locale", "outcome", "retrieval_version", "fusion_version", "snapshot_ref", "result_digest"):
            batch_op.create_index(batch_op.f(f"ix_hybrid_retrieval_runs_{column}"), [column], unique=False)
        batch_op.create_index("ix_hybrid_retrieval_outcome_evaluated", ["outcome", "evaluated_at"], unique=False)

    op.create_table(
        "hybrid_retrieval_candidates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("candidate_rank", sa.Integer(), nullable=False),
        sa.Column("candidate_status", sa.String(length=24), nullable=False),
        sa.Column("entity_type", sa.String(length=16), nullable=False),
        sa.Column("entity_ref", sa.String(length=191), nullable=False),
        sa.Column("group_key", sa.String(length=191), nullable=False),
        sa.Column("rrf_score", sa.String(length=32), nullable=False),
        sa.Column("offer_ids_json", sa.JSON(), nullable=False),
        sa.Column("source_evidence_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.CheckConstraint("candidate_rank > 0", name="ck_hybrid_candidate_rank_positive"),
        sa.CheckConstraint("candidate_status IN ('ELIGIBLE_SHADOW', 'QUARANTINED')", name="ck_hybrid_candidate_status"),
        sa.CheckConstraint("entity_type IN ('PRODUCT', 'MODEL', 'VARIANT')", name="ck_hybrid_candidate_entity_type"),
        sa.ForeignKeyConstraint(["run_id"], ["hybrid_retrieval_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_id", "candidate_rank", name="uq_hybrid_candidate_rank"),
        sa.UniqueConstraint("run_id", "entity_ref", name="uq_hybrid_candidate_entity"),
    )
    with op.batch_alter_table("hybrid_retrieval_candidates") as batch_op:
        for column in ("run_id", "candidate_status", "entity_type", "entity_ref"):
            batch_op.create_index(batch_op.f(f"ix_hybrid_retrieval_candidates_{column}"), [column], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("hybrid_retrieval_candidates") as batch_op:
        for column in reversed(("run_id", "candidate_status", "entity_type", "entity_ref")):
            batch_op.drop_index(batch_op.f(f"ix_hybrid_retrieval_candidates_{column}"))
    op.drop_table("hybrid_retrieval_candidates")
    with op.batch_alter_table("hybrid_retrieval_runs") as batch_op:
        batch_op.drop_index("ix_hybrid_retrieval_outcome_evaluated")
        for column in reversed(("query_digest", "locale", "outcome", "retrieval_version", "fusion_version", "snapshot_ref", "result_digest")):
            batch_op.drop_index(batch_op.f(f"ix_hybrid_retrieval_runs_{column}"))
    op.drop_table("hybrid_retrieval_runs")
