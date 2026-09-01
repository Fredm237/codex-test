"""Ajoute les assertions Product Ontology shadow.

Revision ID: e6b4d8f0a2c5
Revises: d5a3c7e9f1b4
Create Date: 2026-09-01 13:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e6b4d8f0a2c5"
down_revision: Union[str, None] = "d5a3c7e9f1b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "product_ontology_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("snapshot_key", sa.String(length=64), nullable=False),
        sa.Column("raw_source_record_id", sa.Integer(), nullable=False),
        sa.Column("offer_id", sa.Integer(), nullable=False),
        sa.Column("variant_id", sa.Integer(), nullable=True),
        sa.Column("ontology_status", sa.String(length=16), nullable=False),
        sa.Column("classification_json", sa.JSON(), nullable=False),
        sa.Column("product_role_json", sa.JSON(), nullable=False),
        sa.Column("attributes_json", sa.JSON(), nullable=False),
        sa.Column("relationships_json", sa.JSON(), nullable=False),
        sa.Column("facets_json", sa.JSON(), nullable=False),
        sa.Column("legacy_taxonomy_json", sa.JSON(), nullable=False),
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
            name="ck_product_ontology_snapshot_key_sha256",
        ),
        sa.CheckConstraint(
            "ontology_status IN ('VERIFIED', 'PARTIAL', 'QUARANTINED', 'INVALID')",
            name="ck_product_ontology_snapshot_status",
        ),
        sa.CheckConstraint(
            "(ontology_status = 'QUARANTINED' AND variant_id IS NULL) OR "
            "(ontology_status <> 'QUARANTINED' AND variant_id IS NOT NULL)",
            name="ck_product_ontology_snapshot_variant_state",
        ),
        sa.ForeignKeyConstraint(["offer_id"], ["offers.id"]),
        sa.ForeignKeyConstraint(["raw_source_record_id"], ["raw_source_records.id"]),
        sa.ForeignKeyConstraint(["variant_id"], ["graph_variants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "snapshot_key", name="uq_product_ontology_snapshot_key"
        ),
        sa.UniqueConstraint(
            "raw_source_record_id",
            "projection_version",
            "policy_version",
            "evaluated_at",
            name="uq_product_ontology_snapshot_evaluation",
        ),
    )
    with op.batch_alter_table("product_ontology_snapshots") as batch_op:
        for column in (
            "raw_source_record_id",
            "offer_id",
            "variant_id",
            "ontology_status",
            "projection_version",
            "policy_version",
        ):
            batch_op.create_index(
                batch_op.f(f"ix_product_ontology_snapshots_{column}"),
                [column],
                unique=False,
            )
        batch_op.create_index(
            "ix_product_ontology_status_evaluated",
            ["ontology_status", "evaluated_at"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("product_ontology_snapshots") as batch_op:
        batch_op.drop_index("ix_product_ontology_status_evaluated")
        for column in reversed(
            (
                "raw_source_record_id",
                "offer_id",
                "variant_id",
                "ontology_status",
                "projection_version",
                "policy_version",
            )
        ):
            batch_op.drop_index(
                batch_op.f(f"ix_product_ontology_snapshots_{column}")
            )
    op.drop_table("product_ontology_snapshots")
