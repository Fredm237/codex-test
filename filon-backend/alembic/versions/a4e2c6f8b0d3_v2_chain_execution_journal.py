"""Ajoute le lease et journal d'exécution de la chaîne V2.

Revision ID: a4e2c6f8b0d3
Revises: f3c1e5a7b9d2
Create Date: 2026-09-02 16:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a4e2c6f8b0d3"
down_revision: Union[str, None] = "f3c1e5a7b9d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "v2_chain_executions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("execution_key", sa.String(length=64), nullable=False),
        sa.Column("mode", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(), nullable=False),
        sa.Column("vertical", sa.String(length=64), nullable=False),
        sa.Column("after_raw_id", sa.Integer(), nullable=False),
        sa.Column("row_limit", sa.Integer(), nullable=False),
        sa.Column("last_raw_source_id", sa.Integer(), nullable=False),
        sa.Column("checkpoints_json", sa.JSON(), nullable=False),
        sa.Column("completed_stages_json", sa.JSON(), nullable=False),
        sa.Column("report_evaluation_id", sa.String(length=71), nullable=True),
        sa.Column(
            "started_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column("heartbeat_at", sa.DateTime(), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("failure_reason", sa.String(length=64), nullable=True),
        sa.CheckConstraint(
            "status IN ('running', 'succeeded', 'failed', 'interrupted')",
            name="ck_v2_chain_execution_status",
        ),
        sa.CheckConstraint(
            "mode IN ('dry_run', 'apply')",
            name="ck_v2_chain_execution_mode",
        ),
        sa.CheckConstraint(
            "after_raw_id >= 0 AND row_limit >= 1 AND row_limit <= 100",
            name="ck_v2_chain_execution_window",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("v2_chain_executions") as batch_op:
        batch_op.create_index(
            batch_op.f("ix_v2_chain_executions_execution_key"),
            ["execution_key"],
            unique=True,
        )
        batch_op.create_index(
            batch_op.f("ix_v2_chain_executions_status"),
            ["status"],
            unique=False,
        )
        batch_op.create_index(
            "ix_v2_chain_executions_started", ["started_at"], unique=False
        )
    op.create_index(
        "uq_v2_chain_executions_running",
        "v2_chain_executions",
        ["status"],
        unique=True,
        postgresql_where=sa.text("status = 'running'"),
        sqlite_where=sa.text("status = 'running'"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_v2_chain_executions_running",
        table_name="v2_chain_executions",
    )
    with op.batch_alter_table("v2_chain_executions") as batch_op:
        batch_op.drop_index("ix_v2_chain_executions_started")
        batch_op.drop_index(batch_op.f("ix_v2_chain_executions_status"))
        batch_op.drop_index(batch_op.f("ix_v2_chain_executions_execution_key"))
    op.drop_table("v2_chain_executions")
