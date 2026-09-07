"""Autorise la sortie V2 factuelle dans les journaux dark et canary.

Revision ID: 0b8d2f4a6c9e
Revises: f9c7d1e3a5b8
Create Date: 2026-09-07 12:00:00.000000
"""

from typing import Sequence, Union

from alembic import op


revision: str = "0b8d2f4a6c9e"
down_revision: Union[str, None] = "f9c7d1e3a5b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("v2_live_dark_read_observations") as batch_op:
        batch_op.drop_constraint("ck_v2_live_dark_v2_outcome", type_="check")
        batch_op.create_check_constraint(
            "ck_v2_live_dark_v2_outcome",
            "v2_outcome IN ('BUY_NOW', 'WAIT', 'ABSTAIN', 'FACTUAL_OPTIONS', "
            "'ERROR', 'UNSUPPORTED')",
        )

    with op.batch_alter_table("v2_canary_read_observations") as batch_op:
        batch_op.drop_constraint("ck_v2_canary_response_type", type_="check")
        batch_op.create_check_constraint(
            "ck_v2_canary_response_type",
            "response_type IN ('CORE', 'ABSTAIN', 'FACTUAL_OPTIONS', "
            "'BUY_NOW', 'WAIT')",
        )


def downgrade() -> None:
    # Le downgrade est volontairement fail-closed : PostgreSQL refusera de
    # resserrer la contrainte si des observations FACTUAL_OPTIONS existent.
    # L'historique n'est jamais effacé automatiquement pour rendre le rollback
    # artificiellement vert.
    with op.batch_alter_table("v2_canary_read_observations") as batch_op:
        batch_op.drop_constraint("ck_v2_canary_response_type", type_="check")
        batch_op.create_check_constraint(
            "ck_v2_canary_response_type",
            "response_type IN ('CORE', 'ABSTAIN', 'BUY_NOW', 'WAIT')",
        )

    with op.batch_alter_table("v2_live_dark_read_observations") as batch_op:
        batch_op.drop_constraint("ck_v2_live_dark_v2_outcome", type_="check")
        batch_op.create_check_constraint(
            "ck_v2_live_dark_v2_outcome",
            "v2_outcome IN ('BUY_NOW', 'WAIT', 'ABSTAIN', 'ERROR', "
            "'UNSUPPORTED')",
        )
