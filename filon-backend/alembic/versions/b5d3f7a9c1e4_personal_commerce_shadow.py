"""Ajoute le journal et les reçus d'effacement Personal Commerce shadow.

Revision ID: b5d3f7a9c1e4
Revises: a4e2c6f8b0d3
Create Date: 2026-09-02 16:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b5d3f7a9c1e4"
down_revision: Union[str, None] = "a4e2c6f8b0d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "personal_commerce_decision_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("run_key", sa.String(length=64), nullable=False),
        sa.Column("buy_wait_run_id", sa.Integer(), nullable=False),
        sa.Column("subject_digest", sa.String(length=71), nullable=True),
        sa.Column("personalization_consent", sa.Boolean(), nullable=False),
        sa.Column("retention_expires_at", sa.DateTime(), nullable=True),
        sa.Column("objective_digest", sa.String(length=71), nullable=False),
        sa.Column("raw_context_retained", sa.Boolean(), nullable=False),
        sa.Column("policy_version", sa.String(length=64), nullable=False),
        sa.Column("outcome", sa.String(length=24), nullable=False),
        sa.Column("action", sa.String(length=24), nullable=False),
        sa.Column("selected_solution_ref", sa.String(length=191), nullable=True),
        sa.Column("selected_solution_kind", sa.String(length=32), nullable=True),
        sa.Column("matched_preference_count", sa.Integer(), nullable=False),
        sa.Column("eligible_count", sa.Integer(), nullable=False),
        sa.Column("rejected_count", sa.Integer(), nullable=False),
        sa.Column("measurement_status", sa.String(length=32), nullable=False),
        sa.Column("reason_codes_json", sa.JSON(), nullable=False),
        sa.Column("result_digest", sa.String(length=71), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.CheckConstraint("length(run_key) = 64", name="ck_personal_commerce_run_key_sha256"),
        sa.CheckConstraint("length(objective_digest) = 71", name="ck_personal_commerce_objective_digest"),
        sa.CheckConstraint("subject_digest IS NULL OR length(subject_digest) = 71", name="ck_personal_commerce_subject_digest"),
        sa.CheckConstraint("length(result_digest) = 71", name="ck_personal_commerce_result_digest"),
        sa.CheckConstraint("raw_context_retained = false", name="ck_personal_commerce_no_raw_context"),
        sa.CheckConstraint(
            "(personalization_consent = true AND subject_digest IS NOT NULL "
            "AND retention_expires_at IS NOT NULL) OR "
            "(personalization_consent = false AND subject_digest IS NULL "
            "AND retention_expires_at IS NULL)",
            name="ck_personal_commerce_consent_subject",
        ),
        sa.CheckConstraint("outcome IN ('SOLUTION_SELECTED', 'ABSTAINED')", name="ck_personal_commerce_outcome"),
        sa.CheckConstraint("action IN ('USE_WHAT_YOU_OWN', 'BUY', 'WAIT', 'ABSTAIN')", name="ck_personal_commerce_action"),
        sa.CheckConstraint(
            "(outcome = 'SOLUTION_SELECTED' AND personalization_consent = true "
            "AND action <> 'ABSTAIN' AND selected_solution_ref IS NOT NULL "
            "AND selected_solution_kind IS NOT NULL) OR "
            "(outcome = 'ABSTAINED' AND action = 'ABSTAIN' "
            "AND selected_solution_ref IS NULL AND selected_solution_kind IS NULL)",
            name="ck_personal_commerce_decision_shape",
        ),
        sa.CheckConstraint(
            "matched_preference_count >= 0 AND eligible_count >= 0 AND rejected_count >= 0",
            name="ck_personal_commerce_counts",
        ),
        sa.CheckConstraint("measurement_status = 'not_calibrated'", name="ck_personal_commerce_no_score"),
        sa.ForeignKeyConstraint(["buy_wait_run_id"], ["buy_wait_decision_runs.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_key", name="uq_personal_commerce_run_key"),
    )
    with op.batch_alter_table("personal_commerce_decision_runs") as batch_op:
        for column in (
            "buy_wait_run_id", "subject_digest", "retention_expires_at", "objective_digest", "policy_version",
            "outcome", "action", "result_digest",
        ):
            batch_op.create_index(batch_op.f(f"ix_personal_commerce_decision_runs_{column}"), [column], unique=False)
        batch_op.create_index("ix_personal_commerce_outcome_evaluated", ["outcome", "evaluated_at"], unique=False)

    op.create_table(
        "personal_commerce_erasure_receipts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("request_key", sa.String(length=64), nullable=False),
        sa.Column("erased_records", sa.Integer(), nullable=False),
        sa.Column("verified_empty", sa.Boolean(), nullable=False),
        sa.Column("raw_context_retained", sa.Boolean(), nullable=False),
        sa.Column("erased_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.CheckConstraint("length(request_key) = 64", name="ck_personal_commerce_erasure_key_sha256"),
        sa.CheckConstraint("erased_records >= 0", name="ck_personal_commerce_erased_records"),
        sa.CheckConstraint("verified_empty = true", name="ck_personal_commerce_erasure_verified"),
        sa.CheckConstraint("raw_context_retained = false", name="ck_personal_commerce_erasure_no_raw"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("request_key", name="uq_personal_commerce_erasure_request"),
    )
    with op.batch_alter_table("personal_commerce_erasure_receipts") as batch_op:
        batch_op.create_index(batch_op.f("ix_personal_commerce_erasure_receipts_erased_at"), ["erased_at"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("personal_commerce_erasure_receipts") as batch_op:
        batch_op.drop_index(batch_op.f("ix_personal_commerce_erasure_receipts_erased_at"))
    op.drop_table("personal_commerce_erasure_receipts")
    with op.batch_alter_table("personal_commerce_decision_runs") as batch_op:
        batch_op.drop_index("ix_personal_commerce_outcome_evaluated")
        for column in reversed((
            "buy_wait_run_id", "subject_digest", "retention_expires_at", "objective_digest", "policy_version",
            "outcome", "action", "result_digest",
        )):
            batch_op.drop_index(batch_op.f(f"ix_personal_commerce_decision_runs_{column}"))
    op.drop_table("personal_commerce_decision_runs")
