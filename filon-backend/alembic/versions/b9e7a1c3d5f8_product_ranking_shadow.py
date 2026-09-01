"""Ajoute la persistance Product Ranking shadow.

Revision ID: b9e7a1c3d5f8
Revises: a8d6f0b2c4e7
Create Date: 2026-09-01 21:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b9e7a1c3d5f8"
down_revision: Union[str, None] = "a8d6f0b2c4e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "product_ranking_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("run_key", sa.String(length=64), nullable=False),
        sa.Column("constraint_run_id", sa.Integer(), nullable=False),
        sa.Column("context_digest", sa.String(length=71), nullable=False),
        sa.Column("raw_context_retained", sa.Boolean(), nullable=False),
        sa.Column("policy_version", sa.String(length=64), nullable=False),
        sa.Column("vertical", sa.String(length=32), nullable=False),
        sa.Column("outcome", sa.String(length=32), nullable=False),
        sa.Column("candidate_count", sa.Integer(), nullable=False),
        sa.Column("ranked_count", sa.Integer(), nullable=False),
        sa.Column("unrankable_count", sa.Integer(), nullable=False),
        sa.Column("ineligible_count", sa.Integer(), nullable=False),
        sa.Column("result_digest", sa.String(length=71), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.CheckConstraint("length(run_key) = 64", name="ck_product_ranking_run_key_sha256"),
        sa.CheckConstraint("length(context_digest) = 71", name="ck_product_ranking_context_digest"),
        sa.CheckConstraint("length(result_digest) = 71", name="ck_product_ranking_result_digest"),
        sa.CheckConstraint("raw_context_retained = false", name="ck_product_ranking_no_raw_context"),
        sa.CheckConstraint("vertical IN ('smartphones', 'laptops', 'audio', 'fashion', 'appliances_hvac', 'tyres')", name="ck_product_ranking_vertical"),
        sa.CheckConstraint("outcome IN ('RANKED_PRODUCTS', 'ABSTAINED', 'NO_ELIGIBLE_PRODUCT')", name="ck_product_ranking_outcome"),
        sa.CheckConstraint("candidate_count >= 0", name="ck_product_ranking_candidate_count"),
        sa.CheckConstraint("ranked_count >= 0", name="ck_product_ranking_ranked_count"),
        sa.CheckConstraint("unrankable_count >= 0", name="ck_product_ranking_unrankable_count"),
        sa.CheckConstraint("ineligible_count >= 0", name="ck_product_ranking_ineligible_count"),
        sa.ForeignKeyConstraint(["constraint_run_id"], ["constraint_evaluation_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_key", name="uq_product_ranking_run_key"),
        sa.UniqueConstraint("constraint_run_id", "context_digest", "policy_version", "evaluated_at", name="uq_product_ranking_identity"),
    )
    with op.batch_alter_table("product_ranking_runs") as batch_op:
        for column in ("constraint_run_id", "context_digest", "policy_version", "vertical", "outcome", "result_digest"):
            batch_op.create_index(batch_op.f(f"ix_product_ranking_runs_{column}"), [column], unique=False)
        batch_op.create_index("ix_product_ranking_outcome_evaluated", ["outcome", "evaluated_at"], unique=False)

    op.create_table(
        "product_ranking_candidates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("constraint_candidate_id", sa.Integer(), nullable=False),
        sa.Column("entity_type", sa.String(length=16), nullable=False),
        sa.Column("entity_ref", sa.String(length=191), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("product_rank", sa.Integer(), nullable=True),
        sa.Column("utility", sa.String(length=32), nullable=True),
        sa.Column("dimensions_json", sa.JSON(), nullable=False),
        sa.Column("reason_codes_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.CheckConstraint("status IN ('RANKED', 'UNRANKABLE', 'INELIGIBLE')", name="ck_product_ranking_candidate_status"),
        sa.CheckConstraint("entity_type IN ('PRODUCT', 'MODEL', 'VARIANT')", name="ck_product_ranking_candidate_entity_type"),
        sa.CheckConstraint("(status = 'RANKED' AND product_rank IS NOT NULL AND product_rank > 0 AND utility IS NOT NULL) OR (status <> 'RANKED' AND product_rank IS NULL AND utility IS NULL)", name="ck_product_ranking_position_shape"),
        sa.ForeignKeyConstraint(["constraint_candidate_id"], ["constraint_candidate_evaluations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["run_id"], ["product_ranking_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_id", "constraint_candidate_id", name="uq_product_ranking_candidate"),
        sa.UniqueConstraint("run_id", "product_rank", name="uq_product_ranking_position"),
    )
    with op.batch_alter_table("product_ranking_candidates") as batch_op:
        for column in ("run_id", "constraint_candidate_id", "entity_type", "entity_ref", "status", "product_rank"):
            batch_op.create_index(batch_op.f(f"ix_product_ranking_candidates_{column}"), [column], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("product_ranking_candidates") as batch_op:
        for column in reversed(("run_id", "constraint_candidate_id", "entity_type", "entity_ref", "status", "product_rank")):
            batch_op.drop_index(batch_op.f(f"ix_product_ranking_candidates_{column}"))
    op.drop_table("product_ranking_candidates")
    with op.batch_alter_table("product_ranking_runs") as batch_op:
        batch_op.drop_index("ix_product_ranking_outcome_evaluated")
        for column in reversed(("constraint_run_id", "context_digest", "policy_version", "vertical", "outcome", "result_digest")):
            batch_op.drop_index(batch_op.f(f"ix_product_ranking_runs_{column}"))
    op.drop_table("product_ranking_runs")
