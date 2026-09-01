"""Ajoute les snapshots Offer Truth shadow.

Revision ID: d5a3c7e9f1b4
Revises: c4f2b8d5e0a3
Create Date: 2026-09-01 12:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d5a3c7e9f1b4"
down_revision: Union[str, None] = "c4f2b8d5e0a3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Expand-only : aucun lecteur Core/Graph n'est modifié et aucun replay ne
    # démarre avec la migration.
    op.create_table(
        "offer_truth_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("snapshot_key", sa.String(length=64), nullable=False),
        sa.Column("raw_source_record_id", sa.Integer(), nullable=False),
        sa.Column("offer_id", sa.Integer(), nullable=False),
        sa.Column("variant_id", sa.Integer(), nullable=True),
        sa.Column("merchant_id", sa.Integer(), nullable=False),
        sa.Column("offer_status", sa.String(length=16), nullable=False),
        sa.Column("claims_json", sa.JSON(), nullable=False),
        sa.Column("reason_codes_json", sa.JSON(), nullable=False),
        sa.Column("projection_version", sa.String(length=64), nullable=False),
        sa.Column("policy_version", sa.String(length=64), nullable=False),
        sa.Column("observed_at", sa.DateTime(), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "length(snapshot_key) = 64",
            name="ck_offer_truth_snapshot_key_sha256",
        ),
        sa.CheckConstraint(
            "offer_status IN ('VERIFIED', 'PARTIAL', 'STALE', 'INVALID', 'QUARANTINED')",
            name="ck_offer_truth_snapshot_status",
        ),
        sa.CheckConstraint(
            "(offer_status = 'QUARANTINED' AND variant_id IS NULL) OR "
            "(offer_status <> 'QUARANTINED' AND variant_id IS NOT NULL)",
            name="ck_offer_truth_snapshot_variant_state",
        ),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"]),
        sa.ForeignKeyConstraint(["offer_id"], ["offers.id"]),
        sa.ForeignKeyConstraint(["raw_source_record_id"], ["raw_source_records.id"]),
        sa.ForeignKeyConstraint(["variant_id"], ["graph_variants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("snapshot_key", name="uq_offer_truth_snapshot_key"),
        sa.UniqueConstraint(
            "raw_source_record_id",
            "projection_version",
            "policy_version",
            "evaluated_at",
            name="uq_offer_truth_snapshot_evaluation",
        ),
    )
    with op.batch_alter_table("offer_truth_snapshots") as batch_op:
        batch_op.create_index(
            batch_op.f("ix_offer_truth_snapshots_raw_source_record_id"),
            ["raw_source_record_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_offer_truth_snapshots_offer_id"),
            ["offer_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_offer_truth_snapshots_variant_id"),
            ["variant_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_offer_truth_snapshots_merchant_id"),
            ["merchant_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_offer_truth_snapshots_offer_status"),
            ["offer_status"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_offer_truth_snapshots_projection_version"),
            ["projection_version"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_offer_truth_snapshots_policy_version"),
            ["policy_version"],
            unique=False,
        )
        batch_op.create_index(
            "ix_offer_truth_status_evaluated",
            ["offer_status", "evaluated_at"],
            unique=False,
        )


def downgrade() -> None:
    # Destructif uniquement pour le shadow P3E. Le rollback opérationnel normal
    # coupe le flag et conserve les snapshots ; aucune table Core n'est touchée.
    with op.batch_alter_table("offer_truth_snapshots") as batch_op:
        batch_op.drop_index("ix_offer_truth_status_evaluated")
        batch_op.drop_index(batch_op.f("ix_offer_truth_snapshots_policy_version"))
        batch_op.drop_index(batch_op.f("ix_offer_truth_snapshots_projection_version"))
        batch_op.drop_index(batch_op.f("ix_offer_truth_snapshots_offer_status"))
        batch_op.drop_index(batch_op.f("ix_offer_truth_snapshots_merchant_id"))
        batch_op.drop_index(batch_op.f("ix_offer_truth_snapshots_variant_id"))
        batch_op.drop_index(batch_op.f("ix_offer_truth_snapshots_offer_id"))
        batch_op.drop_index(
            batch_op.f("ix_offer_truth_snapshots_raw_source_record_id")
        )
    op.drop_table("offer_truth_snapshots")
