"""Ajoute la persistance Constraint Engine shadow.

Revision ID: a8d6f0b2c4e7
Revises: f7c5e9a1b3d6
Create Date: 2026-09-01 19:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a8d6f0b2c4e7"
down_revision: Union[str, None] = "f7c5e9a1b3d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "constraint_evaluation_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("run_key", sa.String(length=64), nullable=False),
        sa.Column("retrieval_run_id", sa.Integer(), nullable=False),
        sa.Column("context_digest", sa.String(length=71), nullable=False),
        sa.Column("raw_context_retained", sa.Boolean(), nullable=False),
        sa.Column("policy_version", sa.String(length=64), nullable=False),
        sa.Column("outcome", sa.String(length=32), nullable=False),
        sa.Column("candidate_count", sa.Integer(), nullable=False),
        sa.Column("eligible_count", sa.Integer(), nullable=False),
        sa.Column("excluded_count", sa.Integer(), nullable=False),
        sa.Column("unknown_count", sa.Integer(), nullable=False),
        sa.Column("result_digest", sa.String(length=71), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.CheckConstraint("length(run_key) = 64", name="ck_constraint_run_key_sha256"),
        sa.CheckConstraint("length(context_digest) = 71", name="ck_constraint_context_digest"),
        sa.CheckConstraint("length(result_digest) = 71", name="ck_constraint_result_digest"),
        sa.CheckConstraint("raw_context_retained = false", name="ck_constraint_no_raw_context"),
        sa.CheckConstraint("outcome IN ('ELIGIBLE_CANDIDATES', 'NO_ELIGIBLE_CANDIDATE', 'ABSTAINED')", name="ck_constraint_evaluation_outcome"),
        sa.CheckConstraint("candidate_count >= 0", name="ck_constraint_candidate_count"),
        sa.CheckConstraint("eligible_count >= 0", name="ck_constraint_eligible_count"),
        sa.CheckConstraint("excluded_count >= 0", name="ck_constraint_excluded_count"),
        sa.CheckConstraint("unknown_count >= 0", name="ck_constraint_unknown_count"),
        sa.ForeignKeyConstraint(["retrieval_run_id"], ["hybrid_retrieval_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_key", name="uq_constraint_evaluation_run_key"),
        sa.UniqueConstraint("retrieval_run_id", "context_digest", "policy_version", "evaluated_at", name="uq_constraint_evaluation_identity"),
    )
    with op.batch_alter_table("constraint_evaluation_runs") as batch_op:
        for column in ("retrieval_run_id", "context_digest", "policy_version", "outcome", "result_digest"):
            batch_op.create_index(batch_op.f(f"ix_constraint_evaluation_runs_{column}"), [column], unique=False)
        batch_op.create_index("ix_constraint_outcome_evaluated", ["outcome", "evaluated_at"], unique=False)

    op.create_table(
        "constraint_candidate_evaluations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("retrieval_candidate_id", sa.Integer(), nullable=False),
        sa.Column("entity_type", sa.String(length=16), nullable=False),
        sa.Column("entity_ref", sa.String(length=191), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("hard_results_json", sa.JSON(), nullable=False),
        sa.Column("preference_results_json", sa.JSON(), nullable=False),
        sa.Column("reason_codes_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.CheckConstraint("status IN ('ELIGIBLE', 'EXCLUDED', 'UNKNOWN')", name="ck_constraint_candidate_status"),
        sa.CheckConstraint("entity_type IN ('PRODUCT', 'MODEL', 'VARIANT')", name="ck_constraint_candidate_entity_type"),
        sa.ForeignKeyConstraint(["retrieval_candidate_id"], ["hybrid_retrieval_candidates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["run_id"], ["constraint_evaluation_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_id", "retrieval_candidate_id", name="uq_constraint_candidate_evaluation"),
    )
    with op.batch_alter_table("constraint_candidate_evaluations") as batch_op:
        for column in ("run_id", "retrieval_candidate_id", "entity_type", "entity_ref", "status"):
            batch_op.create_index(batch_op.f(f"ix_constraint_candidate_evaluations_{column}"), [column], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("constraint_candidate_evaluations") as batch_op:
        for column in reversed(("run_id", "retrieval_candidate_id", "entity_type", "entity_ref", "status")):
            batch_op.drop_index(batch_op.f(f"ix_constraint_candidate_evaluations_{column}"))
    op.drop_table("constraint_candidate_evaluations")
    with op.batch_alter_table("constraint_evaluation_runs") as batch_op:
        batch_op.drop_index("ix_constraint_outcome_evaluated")
        for column in reversed(("retrieval_run_id", "context_digest", "policy_version", "outcome", "result_digest")):
            batch_op.drop_index(batch_op.f(f"ix_constraint_evaluation_runs_{column}"))
    op.drop_table("constraint_evaluation_runs")
