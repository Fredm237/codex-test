"""Ajoute les checkpoints reprenables par feed catalogue.

Revision ID: a2d7e9f4c1b6
Revises: f9a4c7d1e2b3
Create Date: 2026-08-31 10:35:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a2d7e9f4c1b6"
down_revision: Union[str, None] = "f9a4c7d1e2b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("catalog_sync_runs", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("resumed_from_run_id", sa.Integer(), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_catalog_sync_runs_resumed_from",
            "catalog_sync_runs",
            ["resumed_from_run_id"],
            ["id"],
        )
        batch_op.create_index(
            batch_op.f("ix_catalog_sync_runs_resumed_from_run_id"),
            ["resumed_from_run_id"],
            unique=False,
        )

    op.create_table(
        "catalog_sync_feed_checkpoints",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sync_run_id", sa.Integer(), nullable=False),
        sa.Column("feed_id", sa.String(length=191), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("rows_count", sa.Integer(), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "heartbeat_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["sync_run_id"],
            ["catalog_sync_runs.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "sync_run_id",
            "feed_id",
            name="uq_catalog_sync_feed_checkpoint",
        ),
    )
    with op.batch_alter_table(
        "catalog_sync_feed_checkpoints",
        schema=None,
    ) as batch_op:
        batch_op.create_index(
            "ix_catalog_sync_feed_checkpoint_status",
            ["sync_run_id", "status"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_catalog_sync_feed_checkpoints_sync_run_id"),
            ["sync_run_id"],
            unique=False,
        )

    # Accélère la reprise idempotente d'un feed partiellement traité sans
    # modifier les preuves historiques déjà capturées.
    with op.batch_alter_table("raw_source_records", schema=None) as batch_op:
        batch_op.create_index(
            "ix_raw_source_sync_feed_record",
            ["sync_run_id", "source_ref", "source_record_key"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("raw_source_records", schema=None) as batch_op:
        batch_op.drop_index("ix_raw_source_sync_feed_record")
    with op.batch_alter_table(
        "catalog_sync_feed_checkpoints",
        schema=None,
    ) as batch_op:
        batch_op.drop_index(
            batch_op.f("ix_catalog_sync_feed_checkpoints_sync_run_id")
        )
        batch_op.drop_index("ix_catalog_sync_feed_checkpoint_status")
    op.drop_table("catalog_sync_feed_checkpoints")
    with op.batch_alter_table("catalog_sync_runs", schema=None) as batch_op:
        batch_op.drop_index(
            batch_op.f("ix_catalog_sync_runs_resumed_from_run_id")
        )
        batch_op.drop_constraint(
            "fk_catalog_sync_runs_resumed_from",
            type_="foreignkey",
        )
        batch_op.drop_column("resumed_from_run_id")
