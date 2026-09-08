"""Bind V2 executions to an explicit country and immutable raw upper bound.

Revision ID: 2d0f4a6c8e1b
Revises: 1c9e3b5d7f0a
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2d0f4a6c8e1b"
down_revision: Union[str, None] = "1c9e3b5d7f0a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("v2_chain_executions") as batch_op:
        batch_op.add_column(
            sa.Column("country_code", sa.String(length=2), nullable=True)
        )
        batch_op.add_column(
            sa.Column("raw_id_upper_bound", sa.Integer(), nullable=True)
        )
        batch_op.create_index(
            "ix_v2_chain_executions_country_code",
            ["country_code"],
            unique=False,
        )
        batch_op.create_check_constraint(
            "ck_v2_chain_execution_country_scope",
            "(country_code IS NULL AND raw_id_upper_bound IS NULL) OR "
            "(length(country_code) = 2 AND country_code = upper(country_code) "
            "AND raw_id_upper_bound > after_raw_id)",
        )


def downgrade() -> None:
    with op.batch_alter_table("v2_chain_executions") as batch_op:
        batch_op.drop_constraint(
            "ck_v2_chain_execution_country_scope", type_="check"
        )
        batch_op.drop_index("ix_v2_chain_executions_country_code")
        batch_op.drop_column("raw_id_upper_bound")
        batch_op.drop_column("country_code")
