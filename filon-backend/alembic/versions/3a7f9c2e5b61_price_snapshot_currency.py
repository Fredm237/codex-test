"""Ajoute la devise source aux relevés de prix.

Revision ID: 3a7f9c2e5b61
Revises: d75faf1f6a94
Create Date: 2026-08-29 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "3a7f9c2e5b61"
down_revision: Union[str, None] = "d75faf1f6a94"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Aucun backfill : la devise d'un ancien montant n'est pas déductible de
    # l'offre courante. Ces lignes restent donc explicitement inconnues.
    with op.batch_alter_table("price_snapshots", schema=None) as batch_op:
        batch_op.add_column(sa.Column("currency", sa.String(length=8), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("price_snapshots", schema=None) as batch_op:
        batch_op.drop_column("currency")
