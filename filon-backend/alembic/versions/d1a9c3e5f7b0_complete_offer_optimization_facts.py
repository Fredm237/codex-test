"""Complète Offer Optimization avec cashback, coût livré et retours.

Revision ID: d1a9c3e5f7b0
Revises: c0f8b2d4e6a9
Create Date: 2026-09-01 18:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d1a9c3e5f7b0"
down_revision: Union[str, None] = "c0f8b2d4e6a9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_V2_SHAPE = (
    "(status = 'SELECTED' AND selection_rank = 1 AND total_cost IS NOT NULL "
    "AND cashback_amount IS NOT NULL AND landed_cost IS NOT NULL AND currency IS NOT NULL "
    "AND return_period_days IS NOT NULL) OR "
    "(status = 'ELIGIBLE' AND selection_rank IS NULL AND total_cost IS NOT NULL "
    "AND cashback_amount IS NOT NULL AND landed_cost IS NOT NULL AND currency IS NOT NULL "
    "AND return_period_days IS NOT NULL) OR "
    "(status IN ('UNOPTIMIZABLE', 'INELIGIBLE') AND selection_rank IS NULL "
    "AND total_cost IS NULL AND cashback_amount IS NULL AND landed_cost IS NULL "
    "AND currency IS NULL AND return_period_days IS NULL)"
)

_V1_SHAPE = (
    "(status = 'SELECTED' AND selection_rank = 1 AND total_cost IS NOT NULL AND currency IS NOT NULL) OR "
    "(status = 'ELIGIBLE' AND selection_rank IS NULL AND total_cost IS NOT NULL AND currency IS NOT NULL) OR "
    "(status IN ('UNOPTIMIZABLE', 'INELIGIBLE') AND selection_rank IS NULL "
    "AND total_cost IS NULL AND currency IS NULL)"
)


def upgrade() -> None:
    with op.batch_alter_table("offer_optimization_candidates") as batch_op:
        batch_op.add_column(sa.Column("cashback_amount", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("landed_cost", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("return_period_days", sa.Integer(), nullable=True))
        batch_op.drop_constraint("ck_offer_optimization_candidate_shape", type_="check")
        batch_op.create_check_constraint("ck_offer_optimization_candidate_shape", _V2_SHAPE)


def downgrade() -> None:
    with op.batch_alter_table("offer_optimization_candidates") as batch_op:
        batch_op.drop_constraint("ck_offer_optimization_candidate_shape", type_="check")
        batch_op.create_check_constraint("ck_offer_optimization_candidate_shape", _V1_SHAPE)
        batch_op.drop_column("return_period_days")
        batch_op.drop_column("landed_cost")
        batch_op.drop_column("cashback_amount")
