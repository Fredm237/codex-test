"""Ajoute la persistance Confidence shadow.

Revision ID: e2b0d4f6a8c1
Revises: d1a9c3e5f7b0
Create Date: 2026-09-02 00:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e2b0d4f6a8c1"
down_revision: Union[str, None] = "d1a9c3e5f7b0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "confidence_calibration_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("run_key", sa.String(length=64), nullable=False),
        sa.Column("offer_optimization_run_id", sa.Integer(), nullable=False),
        sa.Column("context_digest", sa.String(length=71), nullable=False),
        sa.Column("raw_context_retained", sa.Boolean(), nullable=False),
        sa.Column("policy_version", sa.String(length=64), nullable=False),
        sa.Column("outcome", sa.String(length=32), nullable=False),
        sa.Column("dimension_count", sa.Integer(), nullable=False),
        sa.Column("calibrated_dimension_count", sa.Integer(), nullable=False),
        sa.Column("evidence_coverage_state", sa.String(length=16), nullable=False),
        sa.Column("evidence_coverage_ratio", sa.String(length=16), nullable=True),
        sa.Column("evidence_observed_count", sa.Integer(), nullable=False),
        sa.Column("evidence_required_count", sa.Integer(), nullable=False),
        sa.Column("evidence_refs_json", sa.JSON(), nullable=False),
        sa.Column("result_digest", sa.String(length=71), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.CheckConstraint("length(run_key) = 64", name="ck_confidence_run_key_sha256"),
        sa.CheckConstraint("length(context_digest) = 71", name="ck_confidence_context_digest"),
        sa.CheckConstraint("length(result_digest) = 71", name="ck_confidence_result_digest"),
        sa.CheckConstraint("raw_context_retained = false", name="ck_confidence_no_raw_context"),
        sa.CheckConstraint(
            "outcome IN ('CONFIDENCE_CALIBRATED', 'PARTIAL_CONFIDENCE', 'ABSTAINED')",
            name="ck_confidence_outcome",
        ),
        sa.CheckConstraint("dimension_count = 5", name="ck_confidence_dimension_count"),
        sa.CheckConstraint(
            "calibrated_dimension_count >= 0 AND calibrated_dimension_count <= dimension_count",
            name="ck_confidence_calibrated_count",
        ),
        sa.CheckConstraint(
            "evidence_coverage_state IN ('MEASURED', 'UNKNOWN')",
            name="ck_confidence_coverage_state",
        ),
        sa.CheckConstraint(
            "(evidence_coverage_state = 'MEASURED' AND evidence_coverage_ratio IS NOT NULL "
            "AND evidence_required_count > 0) OR "
            "(evidence_coverage_state = 'UNKNOWN' AND evidence_coverage_ratio IS NULL "
            "AND evidence_required_count = 0 AND evidence_observed_count = 0)",
            name="ck_confidence_coverage_shape",
        ),
        sa.CheckConstraint(
            "evidence_observed_count >= 0 AND evidence_required_count >= 0 "
            "AND evidence_observed_count <= evidence_required_count",
            name="ck_confidence_coverage_counts",
        ),
        sa.ForeignKeyConstraint(
            ["offer_optimization_run_id"], ["offer_optimization_runs.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_key", name="uq_confidence_calibration_run_key"),
        sa.UniqueConstraint(
            "offer_optimization_run_id", "policy_version", "evaluated_at",
            name="uq_confidence_calibration_identity",
        ),
    )
    with op.batch_alter_table("confidence_calibration_runs") as batch_op:
        for column in (
            "offer_optimization_run_id", "context_digest", "policy_version", "outcome",
            "evidence_coverage_state", "result_digest"
        ):
            batch_op.create_index(
                batch_op.f(f"ix_confidence_calibration_runs_{column}"), [column], unique=False
            )
        batch_op.create_index(
            "ix_confidence_outcome_evaluated", ["outcome", "evaluated_at"], unique=False
        )

    op.create_table(
        "confidence_dimension_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("dimension", sa.String(length=32), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("probability_decimal", sa.String(length=16), nullable=True),
        sa.Column("sample_size", sa.Integer(), nullable=False),
        sa.Column("profile_ref", sa.String(length=191), nullable=True),
        sa.Column("reason_codes_json", sa.JSON(), nullable=False),
        sa.Column("evidence_refs_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.CheckConstraint(
            "dimension IN ('RETRIEVAL_CONFIDENCE', 'ENTITY_MATCH_CONFIDENCE', "
            "'ATTRIBUTE_CONFIDENCE', 'OFFER_CONFIDENCE', 'DECISION_CONFIDENCE')",
            name="ck_confidence_dimension",
        ),
        sa.CheckConstraint(
            "state IN ('CALIBRATED', 'UNKNOWN', 'INVALID', 'INSUFFICIENT_SUPPORT')",
            name="ck_confidence_dimension_state",
        ),
        sa.CheckConstraint(
            "(state = 'CALIBRATED' AND probability_decimal IS NOT NULL "
            "AND sample_size > 0 AND profile_ref IS NOT NULL) OR "
            "(state <> 'CALIBRATED' AND probability_decimal IS NULL)",
            name="ck_confidence_dimension_shape",
        ),
        sa.CheckConstraint("sample_size >= 0", name="ck_confidence_dimension_sample_size"),
        sa.ForeignKeyConstraint(
            ["run_id"], ["confidence_calibration_runs.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_id", "dimension", name="uq_confidence_dimension"),
    )
    with op.batch_alter_table("confidence_dimension_records") as batch_op:
        for column in ("run_id", "dimension", "state"):
            batch_op.create_index(
                batch_op.f(f"ix_confidence_dimension_records_{column}"), [column], unique=False
            )


def downgrade() -> None:
    with op.batch_alter_table("confidence_dimension_records") as batch_op:
        for column in reversed(("run_id", "dimension", "state")):
            batch_op.drop_index(batch_op.f(f"ix_confidence_dimension_records_{column}"))
    op.drop_table("confidence_dimension_records")
    with op.batch_alter_table("confidence_calibration_runs") as batch_op:
        batch_op.drop_index("ix_confidence_outcome_evaluated")
        for column in reversed(
            (
                "offer_optimization_run_id", "context_digest", "policy_version", "outcome",
                "evidence_coverage_state", "result_digest",
            )
        ):
            batch_op.drop_index(batch_op.f(f"ix_confidence_calibration_runs_{column}"))
    op.drop_table("confidence_calibration_runs")
