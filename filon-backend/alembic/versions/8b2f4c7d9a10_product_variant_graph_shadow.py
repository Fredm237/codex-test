"""Ajoute le Product/Variant Graph shadow exact-GTIN.

Revision ID: 8b2f4c7d9a10
Revises: f4c81a9d2e70
Create Date: 2026-08-30 20:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8b2f4c7d9a10"
down_revision: Union[str, None] = "f4c81a9d2e70"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Expand-only : aucune table Core v1 n'est modifiée et aucun backfill n'est
    # lancé pendant la migration.
    op.create_table(
        "graph_brands",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("brand_key", sa.String(length=96), nullable=False),
        sa.Column("canonical_name", sa.String(length=191), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("graph_brands", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_graph_brands_brand_key"),
            ["brand_key"],
            unique=True,
        )

    op.create_table(
        "graph_product_families",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("family_key", sa.String(length=128), nullable=False),
        sa.Column("brand_id", sa.Integer(), nullable=False),
        sa.Column("canonical_name", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["brand_id"], ["graph_brands.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "brand_id",
            "family_key",
            name="uq_graph_family_brand_key",
        ),
    )
    with op.batch_alter_table("graph_product_families", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_graph_product_families_brand_id"),
            ["brand_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_graph_product_families_family_key"),
            ["family_key"],
            unique=False,
        )

    op.create_table(
        "graph_product_models",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("model_key", sa.String(length=128), nullable=False),
        sa.Column("family_id", sa.Integer(), nullable=True),
        sa.Column("canonical_name", sa.String(length=255), nullable=False),
        sa.Column("model_code", sa.String(length=128), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["family_id"], ["graph_product_families.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("graph_product_models", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_graph_product_models_family_id"),
            ["family_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_graph_product_models_model_key"),
            ["model_key"],
            unique=True,
        )

    op.create_table(
        "graph_variants",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("variant_key", sa.String(length=128), nullable=False),
        sa.Column("model_id", sa.Integer(), nullable=True),
        sa.Column("attributes_json", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("resolver_version", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('shadow', 'reviewed', 'retired')",
            name="ck_graph_variant_status",
        ),
        sa.ForeignKeyConstraint(["model_id"], ["graph_product_models.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("graph_variants", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_graph_variants_model_id"),
            ["model_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_graph_variants_status"),
            ["status"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_graph_variants_variant_key"),
            ["variant_key"],
            unique=True,
        )

    op.create_table(
        "graph_brand_aliases",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("brand_id", sa.Integer(), nullable=False),
        sa.Column("raw_source_record_id", sa.Integer(), nullable=False),
        sa.Column("alias", sa.String(length=191), nullable=False),
        sa.Column("normalized_alias", sa.String(length=191), nullable=False),
        sa.Column("source_ref", sa.String(length=255), nullable=False),
        sa.Column("observed_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["brand_id"], ["graph_brands.id"]),
        sa.ForeignKeyConstraint(
            ["raw_source_record_id"],
            ["raw_source_records.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "brand_id",
            "raw_source_record_id",
            "normalized_alias",
            name="uq_graph_brand_alias_evidence",
        ),
    )
    with op.batch_alter_table("graph_brand_aliases", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_graph_brand_aliases_brand_id"),
            ["brand_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_graph_brand_aliases_raw_source_record_id"),
            ["raw_source_record_id"],
            unique=False,
        )
        batch_op.create_index(
            "ix_graph_brand_alias_normalized",
            ["normalized_alias"],
            unique=False,
        )

    op.create_table(
        "graph_identifiers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("variant_id", sa.Integer(), nullable=False),
        sa.Column("namespace", sa.String(length=24), nullable=False),
        sa.Column("scope", sa.String(length=96), nullable=False),
        sa.Column("normalized_value", sa.String(length=191), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "namespace IN ('gtin')",
            name="ck_graph_identifier_namespace_v1",
        ),
        sa.ForeignKeyConstraint(["variant_id"], ["graph_variants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "namespace",
            "scope",
            "normalized_value",
            name="uq_graph_identifier_scope_value",
        ),
    )
    with op.batch_alter_table("graph_identifiers", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_graph_identifiers_normalized_value"),
            ["normalized_value"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_graph_identifiers_variant_id"),
            ["variant_id"],
            unique=False,
        )

    op.create_table(
        "graph_identifier_evidence",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("identifier_id", sa.Integer(), nullable=False),
        sa.Column("raw_source_record_id", sa.Integer(), nullable=False),
        sa.Column("source_type", sa.String(length=48), nullable=False),
        sa.Column("source_ref", sa.String(length=255), nullable=False),
        sa.Column("observed_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["identifier_id"], ["graph_identifiers.id"]),
        sa.ForeignKeyConstraint(
            ["raw_source_record_id"],
            ["raw_source_records.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "identifier_id",
            "raw_source_record_id",
            name="uq_graph_identifier_raw_evidence",
        ),
    )
    with op.batch_alter_table("graph_identifier_evidence", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_graph_identifier_evidence_identifier_id"),
            ["identifier_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_graph_identifier_evidence_raw_source_record_id"),
            ["raw_source_record_id"],
            unique=False,
        )

    op.create_table(
        "graph_offer_variant_links",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("raw_source_record_id", sa.Integer(), nullable=False),
        sa.Column("offer_id", sa.Integer(), nullable=False),
        sa.Column("variant_id", sa.Integer(), nullable=True),
        sa.Column("resolution", sa.String(length=16), nullable=False),
        sa.Column("reason_code", sa.String(length=32), nullable=False),
        sa.Column("resolver_version", sa.String(length=64), nullable=False),
        sa.Column("observed_at", sa.DateTime(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "resolution IN ('resolved', 'quarantine', 'rejected')",
            name="ck_graph_offer_resolution",
        ),
        sa.CheckConstraint(
            "reason_code IN ('exact_gtin', 'missing_gtin', 'invalid_gtin', "
            "'conflicting_gtin', 'candidate_mismatch')",
            name="ck_graph_offer_resolution_reason",
        ),
        sa.CheckConstraint(
            "(resolution = 'resolved' AND variant_id IS NOT NULL) OR "
            "(resolution <> 'resolved' AND variant_id IS NULL)",
            name="ck_graph_offer_resolution_variant",
        ),
        sa.ForeignKeyConstraint(["offer_id"], ["offers.id"]),
        sa.ForeignKeyConstraint(
            ["raw_source_record_id"],
            ["raw_source_records.id"],
        ),
        sa.ForeignKeyConstraint(["variant_id"], ["graph_variants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "raw_source_record_id",
            "resolver_version",
            name="uq_graph_offer_resolution_version",
        ),
    )
    with op.batch_alter_table("graph_offer_variant_links", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_graph_offer_variant_links_offer_id"),
            ["offer_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_graph_offer_variant_links_raw_source_record_id"),
            ["raw_source_record_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_graph_offer_variant_links_resolution"),
            ["resolution"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_graph_offer_variant_links_variant_id"),
            ["variant_id"],
            unique=False,
        )
        batch_op.create_index(
            "ix_graph_offer_resolution_state",
            ["resolution", "reason_code"],
            unique=False,
        )


def downgrade() -> None:
    # Downgrade structurel réservé aux bases de test ou à une fenêtre de
    # rollback explicitement sauvegardée. Le rollback normal coupe le writer.
    op.drop_table("graph_offer_variant_links")
    op.drop_table("graph_identifier_evidence")
    op.drop_table("graph_identifiers")
    op.drop_table("graph_brand_aliases")
    op.drop_table("graph_variants")
    op.drop_table("graph_product_models")
    op.drop_table("graph_product_families")
    op.drop_table("graph_brands")
