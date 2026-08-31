"""Ajoute les assertions sourcées Product Identity shadow.

Revision ID: b3e1a7c4d9f2
Revises: a2d7e9f4c1b6
Create Date: 2026-08-31 18:10:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b3e1a7c4d9f2"
down_revision: Union[str, None] = "a2d7e9f4c1b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Expand-only : le Core v1 et les tables Graph existantes sont inchangés.
    # Aucun backfill n'est lancé pendant la migration.
    op.create_table(
        "graph_identity_assertions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("assertion_key", sa.String(length=64), nullable=False),
        sa.Column("raw_source_record_id", sa.Integer(), nullable=False),
        sa.Column("offer_id", sa.Integer(), nullable=False),
        sa.Column("subject_type", sa.String(length=32), nullable=False),
        sa.Column("subject_ref", sa.String(length=255), nullable=False),
        sa.Column("field", sa.String(length=64), nullable=False),
        sa.Column("value_json", sa.JSON(), nullable=False),
        sa.Column("normalized_value", sa.String(length=191), nullable=True),
        sa.Column("identifier_namespace", sa.String(length=24), nullable=True),
        sa.Column("identifier_scope", sa.String(length=191), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("source_type", sa.String(length=48), nullable=False),
        sa.Column("source_ref", sa.String(length=255), nullable=False),
        sa.Column("observed_at", sa.DateTime(), nullable=False),
        sa.Column("transformation", sa.String(length=96), nullable=False),
        sa.Column("transformation_version", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "length(assertion_key) = 64",
            name="ck_graph_identity_assertion_key_sha256",
        ),
        sa.CheckConstraint(
            "subject_type IN ('brand', 'product_family', 'product_model', 'variant')",
            name="ck_graph_identity_assertion_subject",
        ),
        sa.CheckConstraint(
            "status IN ('observed', 'validated', 'conflict', 'quarantine')",
            name="ck_graph_identity_assertion_status",
        ),
        sa.CheckConstraint(
            "identifier_namespace IS NULL OR identifier_namespace IN "
            "('gtin', 'mpn', 'merchant_sku', 'source_product_id')",
            name="ck_graph_identity_assertion_namespace",
        ),
        sa.CheckConstraint(
            "(identifier_namespace IS NULL AND identifier_scope IS NULL) OR "
            "(identifier_namespace IS NOT NULL AND identifier_scope IS NOT NULL)",
            name="ck_graph_identity_assertion_scope",
        ),
        sa.ForeignKeyConstraint(["offer_id"], ["offers.id"]),
        sa.ForeignKeyConstraint(
            ["raw_source_record_id"],
            ["raw_source_records.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "assertion_key",
            name="uq_graph_identity_assertion_key",
        ),
    )
    with op.batch_alter_table("graph_identity_assertions", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_graph_identity_assertions_offer_id"),
            ["offer_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_graph_identity_assertions_raw_source_record_id"),
            ["raw_source_record_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_graph_identity_assertions_status"),
            ["status"],
            unique=False,
        )
        batch_op.create_index(
            "ix_graph_identity_assertion_subject",
            ["subject_type", "subject_ref"],
            unique=False,
        )
        batch_op.create_index(
            "ix_graph_identity_assertion_field_status",
            ["field", "status"],
            unique=False,
        )
        batch_op.create_index(
            "ix_graph_identity_assertion_identifier",
            ["identifier_namespace", "identifier_scope", "normalized_value"],
            unique=False,
        )


def downgrade() -> None:
    # Destructif pour les seules assertions shadow ; le rollback normal coupe
    # le flag et conserve cette table. Aucun objet Core n'est touché.
    with op.batch_alter_table("graph_identity_assertions", schema=None) as batch_op:
        batch_op.drop_index("ix_graph_identity_assertion_identifier")
        batch_op.drop_index("ix_graph_identity_assertion_field_status")
        batch_op.drop_index("ix_graph_identity_assertion_subject")
        batch_op.drop_index(batch_op.f("ix_graph_identity_assertions_status"))
        batch_op.drop_index(
            batch_op.f("ix_graph_identity_assertions_raw_source_record_id")
        )
        batch_op.drop_index(batch_op.f("ix_graph_identity_assertions_offer_id"))
    op.drop_table("graph_identity_assertions")
