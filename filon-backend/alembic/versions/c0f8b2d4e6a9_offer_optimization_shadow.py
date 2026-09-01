"""Ajoute la persistance Offer Optimization shadow.

Revision ID: c0f8b2d4e6a9
Revises: b9e7a1c3d5f8
Create Date: 2026-09-01 23:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c0f8b2d4e6a9"
down_revision: Union[str, None] = "b9e7a1c3d5f8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "offer_optimization_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("run_key", sa.String(length=64), nullable=False),
        sa.Column("product_ranking_run_id", sa.Integer(), nullable=False),
        sa.Column("context_digest", sa.String(length=71), nullable=False),
        sa.Column("raw_context_retained", sa.Boolean(), nullable=False),
        sa.Column("policy_version", sa.String(length=64), nullable=False),
        sa.Column("outcome", sa.String(length=32), nullable=False),
        sa.Column("selected_product_ref", sa.String(length=191), nullable=True),
        sa.Column("selected_offer_ref", sa.String(length=191), nullable=True),
        sa.Column("candidate_count", sa.Integer(), nullable=False),
        sa.Column("selected_count", sa.Integer(), nullable=False),
        sa.Column("eligible_count", sa.Integer(), nullable=False),
        sa.Column("unoptimizable_count", sa.Integer(), nullable=False),
        sa.Column("ineligible_count", sa.Integer(), nullable=False),
        sa.Column("result_digest", sa.String(length=71), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.CheckConstraint("length(run_key) = 64", name="ck_offer_optimization_run_key_sha256"),
        sa.CheckConstraint("length(context_digest) = 71", name="ck_offer_optimization_context_digest"),
        sa.CheckConstraint("length(result_digest) = 71", name="ck_offer_optimization_result_digest"),
        sa.CheckConstraint("raw_context_retained = false", name="ck_offer_optimization_no_raw_context"),
        sa.CheckConstraint("outcome IN ('OFFER_SELECTED', 'ABSTAINED', 'NO_ELIGIBLE_OFFER')", name="ck_offer_optimization_outcome"),
        sa.CheckConstraint("candidate_count >= 0", name="ck_offer_optimization_candidate_count"),
        sa.CheckConstraint("selected_count IN (0, 1)", name="ck_offer_optimization_selected_count"),
        sa.CheckConstraint("eligible_count >= 0", name="ck_offer_optimization_eligible_count"),
        sa.CheckConstraint("unoptimizable_count >= 0", name="ck_offer_optimization_unoptimizable_count"),
        sa.CheckConstraint("ineligible_count >= 0", name="ck_offer_optimization_ineligible_count"),
        sa.CheckConstraint(
            "candidate_count = selected_count + eligible_count + "
            "unoptimizable_count + ineligible_count",
            name="ck_offer_optimization_candidate_count_sum",
        ),
        sa.CheckConstraint(
            "(outcome = 'OFFER_SELECTED' AND selected_product_ref IS NOT NULL "
            "AND selected_offer_ref IS NOT NULL AND selected_count = 1) OR "
            "(outcome <> 'OFFER_SELECTED' AND selected_offer_ref IS NULL AND selected_count = 0)",
            name="ck_offer_optimization_selection_shape",
        ),
        sa.ForeignKeyConstraint(["product_ranking_run_id"], ["product_ranking_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_key", name="uq_offer_optimization_run_key"),
        sa.UniqueConstraint(
            "product_ranking_run_id", "context_digest", "policy_version", "evaluated_at",
            name="uq_offer_optimization_identity",
        ),
    )
    with op.batch_alter_table("offer_optimization_runs") as batch_op:
        for column in (
            "product_ranking_run_id",
            "context_digest",
            "policy_version",
            "outcome",
            "selected_product_ref",
            "selected_offer_ref",
            "result_digest",
        ):
            batch_op.create_index(batch_op.f(f"ix_offer_optimization_runs_{column}"), [column], unique=False)
        batch_op.create_index("ix_offer_optimization_outcome_evaluated", ["outcome", "evaluated_at"], unique=False)

    op.create_table(
        "offer_optimization_candidates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("offer_truth_snapshot_id", sa.Integer(), nullable=False),
        sa.Column("offer_ref", sa.String(length=191), nullable=False),
        sa.Column("product_ref", sa.String(length=191), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("selection_rank", sa.Integer(), nullable=True),
        sa.Column("total_cost", sa.String(length=32), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=True),
        sa.Column("merchant_reliability", sa.String(length=32), nullable=True),
        sa.Column("freshness", sa.String(length=32), nullable=True),
        sa.Column("reason_codes_json", sa.JSON(), nullable=False),
        sa.Column("evidence_refs_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.CheckConstraint(
            "status IN ('SELECTED', 'ELIGIBLE', 'UNOPTIMIZABLE', 'INELIGIBLE')",
            name="ck_offer_optimization_candidate_status",
        ),
        sa.CheckConstraint(
            "(status = 'SELECTED' AND selection_rank = 1 AND total_cost IS NOT NULL AND currency IS NOT NULL) OR "
            "(status = 'ELIGIBLE' AND selection_rank IS NULL AND total_cost IS NOT NULL AND currency IS NOT NULL) OR "
            "(status IN ('UNOPTIMIZABLE', 'INELIGIBLE') AND selection_rank IS NULL "
            "AND total_cost IS NULL AND currency IS NULL)",
            name="ck_offer_optimization_candidate_shape",
        ),
        sa.ForeignKeyConstraint(["offer_truth_snapshot_id"], ["offer_truth_snapshots.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["run_id"], ["offer_optimization_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_id", "offer_truth_snapshot_id", name="uq_offer_optimization_candidate"),
        sa.UniqueConstraint("run_id", "selection_rank", name="uq_offer_optimization_selection_rank"),
    )
    with op.batch_alter_table("offer_optimization_candidates") as batch_op:
        for column in (
            "run_id",
            "offer_truth_snapshot_id",
            "offer_ref",
            "product_ref",
            "status",
            "selection_rank",
        ):
            batch_op.create_index(batch_op.f(f"ix_offer_optimization_candidates_{column}"), [column], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("offer_optimization_candidates") as batch_op:
        for column in reversed(
            (
                "run_id",
                "offer_truth_snapshot_id",
                "offer_ref",
                "product_ref",
                "status",
                "selection_rank",
            )
        ):
            batch_op.drop_index(batch_op.f(f"ix_offer_optimization_candidates_{column}"))
    op.drop_table("offer_optimization_candidates")
    with op.batch_alter_table("offer_optimization_runs") as batch_op:
        batch_op.drop_index("ix_offer_optimization_outcome_evaluated")
        for column in reversed(
            (
                "product_ranking_run_id",
                "context_digest",
                "policy_version",
                "outcome",
                "selected_product_ref",
                "selected_offer_ref",
                "result_digest",
            )
        ):
            batch_op.drop_index(batch_op.f(f"ix_offer_optimization_runs_{column}"))
    op.drop_table("offer_optimization_runs")
