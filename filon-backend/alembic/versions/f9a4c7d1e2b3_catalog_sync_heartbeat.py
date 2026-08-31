"""Ajoute une preuve de vie persistante aux synchronisations catalogue.

Revision ID: f9a4c7d1e2b3
Revises: e8c3f6a0b5d2
Create Date: 2026-08-31 09:35:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f9a4c7d1e2b3"
down_revision: Union[str, None] = "e8c3f6a0b5d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("catalog_sync_runs", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("heartbeat_at", sa.DateTime(), nullable=True)
        )

    # Les cycles historiques terminés reçoivent leur fin comme dernière preuve
    # de vie ; un cycle encore running conserve son début. Aucun statut ni
    # compteur existant n'est réécrit.
    op.execute(
        "UPDATE catalog_sync_runs "
        "SET heartbeat_at = COALESCE(finished_at, started_at, CURRENT_TIMESTAMP)"
    )

    with op.batch_alter_table("catalog_sync_runs", schema=None) as batch_op:
        batch_op.alter_column(
            "heartbeat_at",
            existing_type=sa.DateTime(),
            nullable=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("catalog_sync_runs", schema=None) as batch_op:
        batch_op.drop_column("heartbeat_at")
