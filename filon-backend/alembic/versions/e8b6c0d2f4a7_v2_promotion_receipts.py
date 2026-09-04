"""Ajoute les reçus append-only de promotion V2.

Revision ID: e8b6c0d2f4a7
Revises: d7a5b9c1e3f6
Create Date: 2026-09-04 00:25:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e8b6c0d2f4a7"
down_revision: Union[str, None] = "d7a5b9c1e3f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "v2_promotion_receipts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("evaluation_id", sa.String(length=71), nullable=False),
        sa.Column("gate_evaluation_id", sa.String(length=71), nullable=False),
        sa.Column("source_gate_evaluation_id", sa.String(length=71), nullable=True),
        sa.Column("promotion_stage", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("authorized_response_types_json", sa.JSON(), nullable=False),
        sa.Column("blocked_response_types_json", sa.JSON(), nullable=False),
        sa.Column("gates_json", sa.JSON(), nullable=False),
        sa.Column("metrics_json", sa.JSON(), nullable=False),
        sa.Column("proof_refs_json", sa.JSON(), nullable=False),
        sa.Column("policy_json", sa.JSON(), nullable=False),
        sa.Column("raw_payload_retained", sa.Boolean(), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "promotion_stage IN ('shadow_to_canary', 'canary_to_public')",
            name="ck_v2_promotion_stage",
        ),
        sa.CheckConstraint(
            "(promotion_stage = 'shadow_to_canary' "
            "AND status IN ('CANARY_HOLD', 'CANARY_AUTHORIZED')) OR "
            "(promotion_stage = 'canary_to_public' "
            "AND status IN ('PUBLIC_HOLD', 'PUBLIC_AUTHORIZED'))",
            name="ck_v2_promotion_stage_status",
        ),
        sa.CheckConstraint(
            "length(evaluation_id) = 71 AND length(gate_evaluation_id) = 71",
            name="ck_v2_promotion_evaluation_digests",
        ),
        sa.CheckConstraint(
            "(promotion_stage = 'shadow_to_canary' "
            "AND source_gate_evaluation_id IS NULL) OR "
            "(promotion_stage = 'canary_to_public' "
            "AND length(source_gate_evaluation_id) = 71)",
            name="ck_v2_promotion_source_gate",
        ),
        sa.CheckConstraint(
            "raw_payload_retained = false",
            name="ck_v2_promotion_no_raw_payload",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("v2_promotion_receipts") as batch_op:
        batch_op.create_index(
            batch_op.f("ix_v2_promotion_receipts_evaluation_id"),
            ["evaluation_id"],
            unique=True,
        )
        for column in (
            "gate_evaluation_id",
            "source_gate_evaluation_id",
            "promotion_stage",
            "status",
        ):
            batch_op.create_index(
                batch_op.f(f"ix_v2_promotion_receipts_{column}"),
                [column],
                unique=False,
            )
        batch_op.create_index(
            "ix_v2_promotion_stage_evaluated",
            ["promotion_stage", "evaluated_at"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("v2_promotion_receipts") as batch_op:
        batch_op.drop_index("ix_v2_promotion_stage_evaluated")
        for column in reversed(
            (
                "gate_evaluation_id",
                "source_gate_evaluation_id",
                "promotion_stage",
                "status",
            )
        ):
            batch_op.drop_index(
                batch_op.f(f"ix_v2_promotion_receipts_{column}")
            )
        batch_op.drop_index(
            batch_op.f("ix_v2_promotion_receipts_evaluation_id")
        )
    op.drop_table("v2_promotion_receipts")
