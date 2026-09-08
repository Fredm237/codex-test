"""Lie chaque observation canary au reçu de promotion exact.

Revision ID: 1c9e3b5d7f0a
Revises: 0b8d2f4a6c9e
Create Date: 2026-09-08 10:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "1c9e3b5d7f0a"
down_revision: Union[str, None] = "0b8d2f4a6c9e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("v2_canary_read_observations") as batch_op:
        batch_op.add_column(
            sa.Column("receipt_evaluation_id", sa.String(length=71), nullable=True)
        )
        batch_op.create_check_constraint(
            "ck_v2_canary_receipt_evaluation_digest",
            "receipt_evaluation_id IS NULL OR length(receipt_evaluation_id) = 71",
        )
        batch_op.create_index(
            "ix_v2_canary_read_observations_receipt_evaluation_id",
            ["receipt_evaluation_id"],
            unique=False,
        )
        batch_op.create_index(
            "ix_v2_canary_receipt_evaluated",
            ["receipt_evaluation_id", "evaluated_at"],
            unique=False,
        )

    with op.batch_alter_table("v2_promotion_receipts") as batch_op:
        batch_op.add_column(
            sa.Column(
                "source_receipt_evaluation_id",
                sa.String(length=71),
                nullable=True,
            )
        )
        batch_op.create_check_constraint(
            "ck_v2_promotion_source_receipt_digest",
            "source_receipt_evaluation_id IS NULL OR "
            "length(source_receipt_evaluation_id) = 71",
        )
        batch_op.create_index(
            "ix_v2_promotion_receipts_source_receipt_evaluation_id",
            ["source_receipt_evaluation_id"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("v2_promotion_receipts") as batch_op:
        batch_op.drop_index(
            "ix_v2_promotion_receipts_source_receipt_evaluation_id"
        )
        batch_op.drop_constraint(
            "ck_v2_promotion_source_receipt_digest", type_="check"
        )
        batch_op.drop_column("source_receipt_evaluation_id")

    with op.batch_alter_table("v2_canary_read_observations") as batch_op:
        batch_op.drop_index("ix_v2_canary_receipt_evaluated")
        batch_op.drop_index(
            "ix_v2_canary_read_observations_receipt_evaluation_id"
        )
        batch_op.drop_constraint(
            "ck_v2_canary_receipt_evaluation_digest", type_="check"
        )
        batch_op.drop_column("receipt_evaluation_id")
