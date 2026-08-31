"""Ajoute les snapshots Merchant Intelligence shadow.

Revision ID: d7b2e5f9a4c1
Revises: c6a1d4e8f2b3
Create Date: 2026-08-31 00:10:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d7b2e5f9a4c1"
down_revision: Union[str, None] = "c6a1d4e8f2b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "merchant_quality_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("merchant_id", sa.Integer(), nullable=False),
        sa.Column("merchant_status", sa.String(length=24), nullable=False),
        sa.Column("window_first_raw_id", sa.Integer(), nullable=False),
        sa.Column("window_last_raw_id", sa.Integer(), nullable=False),
        sa.Column("source_record_count", sa.Integer(), nullable=False),
        sa.Column("offer_observation_count", sa.Integer(), nullable=False),
        sa.Column("gtin_known_count", sa.Integer(), nullable=False),
        sa.Column("price_known_count", sa.Integer(), nullable=False),
        sa.Column("price_fresh_count", sa.Integer(), nullable=False),
        sa.Column("stock_known_count", sa.Integer(), nullable=False),
        sa.Column("merchant_link_known_count", sa.Integer(), nullable=False),
        sa.Column("invalid_link_count", sa.Integer(), nullable=False),
        sa.Column("identity_resolved_count", sa.Integer(), nullable=False),
        sa.Column("eligible_offer_count", sa.Integer(), nullable=False),
        sa.Column("latest_observed_at", sa.DateTime(), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(), nullable=False),
        sa.Column("feed_age_seconds", sa.Integer(), nullable=True),
        sa.Column("measurement_states_json", sa.JSON(), nullable=False),
        sa.Column("policy_version", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "merchant_status IN ('INDEXED', 'AFFILIATED', 'DIRECT_PARTNER', "
            "'MARKETPLACE', 'UNVERIFIED')",
            name="ck_merchant_quality_status",
        ),
        sa.CheckConstraint(
            "window_first_raw_id <= window_last_raw_id",
            name="ck_merchant_quality_window",
        ),
        sa.CheckConstraint(
            "source_record_count > 0 AND offer_observation_count >= 0 "
            "AND gtin_known_count >= 0 AND price_known_count >= 0 "
            "AND price_fresh_count >= 0 AND stock_known_count >= 0 "
            "AND merchant_link_known_count >= 0 AND invalid_link_count >= 0 "
            "AND identity_resolved_count >= 0 AND eligible_offer_count >= 0",
            name="ck_merchant_quality_nonnegative",
        ),
        sa.CheckConstraint(
            "offer_observation_count <= source_record_count "
            "AND gtin_known_count <= source_record_count "
            "AND price_known_count <= source_record_count "
            "AND price_fresh_count <= price_known_count "
            "AND stock_known_count <= source_record_count "
            "AND merchant_link_known_count <= source_record_count "
            "AND invalid_link_count <= source_record_count "
            "AND identity_resolved_count <= source_record_count "
            "AND eligible_offer_count <= source_record_count",
            name="ck_merchant_quality_bounded",
        ),
        sa.CheckConstraint(
            "feed_age_seconds IS NULL OR feed_age_seconds >= 0",
            name="ck_merchant_quality_feed_age",
        ),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "merchant_id",
            "window_first_raw_id",
            "window_last_raw_id",
            "policy_version",
            name="uq_merchant_quality_window_policy",
        ),
    )
    with op.batch_alter_table("merchant_quality_snapshots", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_merchant_quality_snapshots_merchant_id"),
            ["merchant_id"],
            unique=False,
        )
        batch_op.create_index(
            "ix_merchant_quality_status_time",
            ["merchant_status", "evaluated_at"],
            unique=False,
        )


def downgrade() -> None:
    op.drop_table("merchant_quality_snapshots")
