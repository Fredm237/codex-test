"""Ajoute l'Offer Graph shadow append-only.

Revision ID: c6a1d4e8f2b3
Revises: 8b2f4c7d9a10
Create Date: 2026-08-30 22:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c6a1d4e8f2b3"
down_revision: Union[str, None] = "8b2f4c7d9a10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "graph_offer_observations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("raw_source_record_id", sa.Integer(), nullable=False),
        sa.Column("offer_id", sa.Integer(), nullable=False),
        sa.Column("offer_variant_link_id", sa.Integer(), nullable=True),
        sa.Column("price_amount", sa.Numeric(precision=20, scale=6), nullable=True),
        sa.Column("price_currency", sa.String(length=3), nullable=True),
        sa.Column("price_state", sa.String(length=16), nullable=False),
        sa.Column("availability", sa.String(length=16), nullable=False),
        sa.Column("merchant_url", sa.Text(), nullable=True),
        sa.Column("merchant_url_state", sa.String(length=16), nullable=False),
        sa.Column("eligibility", sa.String(length=16), nullable=False),
        sa.Column("reason_code", sa.String(length=32), nullable=False),
        sa.Column("projection_version", sa.String(length=64), nullable=False),
        sa.Column("observed_at", sa.DateTime(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "price_state IN ('known', 'unknown', 'invalid')",
            name="ck_graph_offer_price_state",
        ),
        sa.CheckConstraint(
            "(price_state = 'known' AND price_amount IS NOT NULL "
            "AND price_currency IS NOT NULL) OR "
            "(price_state <> 'known' AND price_amount IS NULL "
            "AND price_currency IS NULL)",
            name="ck_graph_offer_money_pair",
        ),
        sa.CheckConstraint(
            "availability IN ('in_stock', 'out_of_stock', 'unknown')",
            name="ck_graph_offer_availability",
        ),
        sa.CheckConstraint(
            "merchant_url_state IN ('known', 'unknown', 'invalid')",
            name="ck_graph_offer_url_state",
        ),
        sa.CheckConstraint(
            "(merchant_url_state = 'known' AND merchant_url IS NOT NULL) OR "
            "(merchant_url_state <> 'known' AND merchant_url IS NULL)",
            name="ck_graph_offer_url_value",
        ),
        sa.CheckConstraint(
            "eligibility IN ('eligible', 'ineligible', 'unknown', 'quarantine')",
            name="ck_graph_offer_eligibility",
        ),
        sa.CheckConstraint(
            "reason_code IN ('eligible_exact', 'identity_unresolved', "
            "'missing_price', 'invalid_price', 'missing_currency', "
            "'invalid_currency', 'availability_unknown', 'out_of_stock', "
            "'missing_link', 'invalid_link')",
            name="ck_graph_offer_reason",
        ),
        sa.ForeignKeyConstraint(["offer_id"], ["offers.id"]),
        sa.ForeignKeyConstraint(
            ["offer_variant_link_id"],
            ["graph_offer_variant_links.id"],
        ),
        sa.ForeignKeyConstraint(
            ["raw_source_record_id"],
            ["raw_source_records.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "raw_source_record_id",
            "projection_version",
            name="uq_graph_offer_observation_projection",
        ),
    )
    with op.batch_alter_table("graph_offer_observations", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_graph_offer_observations_eligibility"),
            ["eligibility"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_graph_offer_observations_offer_id"),
            ["offer_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_graph_offer_observations_offer_variant_link_id"),
            ["offer_variant_link_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_graph_offer_observations_raw_source_record_id"),
            ["raw_source_record_id"],
            unique=False,
        )
        batch_op.create_index(
            "ix_graph_offer_observation_state",
            ["eligibility", "reason_code"],
            unique=False,
        )


def downgrade() -> None:
    op.drop_table("graph_offer_observations")
