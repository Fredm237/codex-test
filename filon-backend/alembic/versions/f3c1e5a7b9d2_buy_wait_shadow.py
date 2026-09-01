"""Ajoute la persistance BUY/WAIT V2 shadow.

Revision ID: f3c1e5a7b9d2
Revises: e2b0d4f6a8c1
Create Date: 2026-09-02 09:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f3c1e5a7b9d2"
down_revision: Union[str, None] = "e2b0d4f6a8c1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "buy_wait_decision_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("run_key", sa.String(length=64), nullable=False),
        sa.Column("confidence_run_id", sa.Integer(), nullable=False),
        sa.Column("context_digest", sa.String(length=71), nullable=False),
        sa.Column("raw_context_retained", sa.Boolean(), nullable=False),
        sa.Column("policy_version", sa.String(length=64), nullable=False),
        sa.Column("outcome", sa.String(length=16), nullable=False),
        sa.Column("selected_offer_ref", sa.String(length=191), nullable=True),
        sa.Column("selected_product_ref", sa.String(length=191), nullable=True),
        sa.Column("current_price_decimal", sa.String(length=32), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=True),
        sa.Column("history_samples", sa.Integer(), nullable=False),
        sa.Column("tracked_days", sa.Integer(), nullable=False),
        sa.Column("current_percentile_decimal", sa.String(length=16), nullable=True),
        sa.Column("decision_confidence_decimal", sa.String(length=16), nullable=True),
        sa.Column("backtest_profile_ref", sa.String(length=191), nullable=True),
        sa.Column("future_observations_used", sa.Boolean(), nullable=False),
        sa.Column("reason_codes_json", sa.JSON(), nullable=False),
        sa.Column("claims_json", sa.JSON(), nullable=False),
        sa.Column("evidence_refs_json", sa.JSON(), nullable=False),
        sa.Column("result_digest", sa.String(length=71), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.CheckConstraint("length(run_key) = 64", name="ck_buy_wait_run_key_sha256"),
        sa.CheckConstraint("length(context_digest) = 71", name="ck_buy_wait_context_digest"),
        sa.CheckConstraint("length(result_digest) = 71", name="ck_buy_wait_result_digest"),
        sa.CheckConstraint("raw_context_retained = false", name="ck_buy_wait_no_raw_context"),
        sa.CheckConstraint("future_observations_used = false", name="ck_buy_wait_no_future"),
        sa.CheckConstraint("outcome IN ('BUY_NOW', 'WAIT', 'ABSTAIN')", name="ck_buy_wait_outcome"),
        sa.CheckConstraint("history_samples >= 0 AND tracked_days >= 0", name="ck_buy_wait_support"),
        sa.CheckConstraint(
            "(outcome IN ('BUY_NOW', 'WAIT') AND selected_offer_ref IS NOT NULL "
            "AND selected_product_ref IS NOT NULL AND current_price_decimal IS NOT NULL "
            "AND currency IS NOT NULL AND history_samples >= 8 AND tracked_days >= 14 "
            "AND current_percentile_decimal IS NOT NULL AND decision_confidence_decimal IS NOT NULL "
            "AND backtest_profile_ref IS NOT NULL) OR "
            "(outcome = 'ABSTAIN' AND backtest_profile_ref IS NULL)",
            name="ck_buy_wait_decision_shape",
        ),
        sa.ForeignKeyConstraint(["confidence_run_id"], ["confidence_calibration_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_key", name="uq_buy_wait_run_key"),
        sa.UniqueConstraint("confidence_run_id", "policy_version", "evaluated_at", name="uq_buy_wait_identity"),
    )
    with op.batch_alter_table("buy_wait_decision_runs") as batch_op:
        for column in ("confidence_run_id", "context_digest", "policy_version", "outcome", "result_digest"):
            batch_op.create_index(batch_op.f(f"ix_buy_wait_decision_runs_{column}"), [column], unique=False)
        batch_op.create_index("ix_buy_wait_outcome_evaluated", ["outcome", "evaluated_at"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("buy_wait_decision_runs") as batch_op:
        batch_op.drop_index("ix_buy_wait_outcome_evaluated")
        for column in reversed(("confidence_run_id", "context_digest", "policy_version", "outcome", "result_digest")):
            batch_op.drop_index(batch_op.f(f"ix_buy_wait_decision_runs_{column}"))
    op.drop_table("buy_wait_decision_runs")
