"""Ajoute la persistance Entity Resolution shadow.

Revision ID: c4f2b8d5e0a3
Revises: b3e1a7c4d9f2
Create Date: 2026-09-01 01:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4f2b8d5e0a3"
down_revision: Union[str, None] = "b3e1a7c4d9f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Expand-only : aucun lecteur Core/Product Graph existant n'est modifié et
    # aucun replay n'est déclenché par la migration.
    op.create_table(
        "graph_entity_signal_projections",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("projection_key", sa.String(length=64), nullable=False),
        sa.Column("raw_source_record_id", sa.Integer(), nullable=False),
        sa.Column("source_type", sa.String(length=48), nullable=False),
        sa.Column("source_ref", sa.String(length=255), nullable=False),
        sa.Column("observed_at", sa.DateTime(), nullable=False),
        sa.Column("extractor_version", sa.String(length=64), nullable=False),
        sa.Column("profile_json", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "length(projection_key) = 64",
            name="ck_graph_entity_signal_projection_key_sha256",
        ),
        sa.ForeignKeyConstraint(
            ["raw_source_record_id"],
            ["raw_source_records.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "projection_key",
            name="uq_graph_entity_signal_projection_key",
        ),
        sa.UniqueConstraint(
            "raw_source_record_id",
            "extractor_version",
            name="uq_graph_entity_signal_projection_version",
        ),
    )
    with op.batch_alter_table("graph_entity_signal_projections") as batch_op:
        batch_op.create_index(
            batch_op.f("ix_graph_entity_signal_projections_raw_source_record_id"),
            ["raw_source_record_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_graph_entity_signal_projections_extractor_version"),
            ["extractor_version"],
            unique=False,
        )

    op.create_table(
        "graph_entity_resolution_decisions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("decision_key", sa.String(length=64), nullable=False),
        sa.Column("raw_source_record_id", sa.Integer(), nullable=False),
        sa.Column("offer_id", sa.Integer(), nullable=False),
        sa.Column("subject_type", sa.String(length=32), nullable=False),
        sa.Column("resolution", sa.String(length=24), nullable=False),
        sa.Column("canonical_variant_id", sa.Integer(), nullable=True),
        sa.Column("candidate_ids_json", sa.JSON(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("reason_codes_json", sa.JSON(), nullable=False),
        sa.Column("evidence_json", sa.JSON(), nullable=False),
        sa.Column("conflicts_json", sa.JSON(), nullable=False),
        sa.Column("extractor_version", sa.String(length=64), nullable=False),
        sa.Column("resolver_version", sa.String(length=64), nullable=False),
        sa.Column("policy_version", sa.String(length=64), nullable=False),
        sa.Column("observed_at", sa.DateTime(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "length(decision_key) = 64",
            name="ck_graph_entity_resolution_decision_key_sha256",
        ),
        sa.CheckConstraint(
            "resolution IN ('EXACT_VERIFIED', 'HIGH_CONFIDENCE', 'PROBABLE', "
            "'AMBIGUOUS', 'UNRESOLVED')",
            name="ck_graph_entity_resolution_state",
        ),
        sa.CheckConstraint(
            "(resolution IN ('EXACT_VERIFIED', 'HIGH_CONFIDENCE') "
            "AND canonical_variant_id IS NOT NULL) OR "
            "(resolution IN ('PROBABLE', 'AMBIGUOUS', 'UNRESOLVED') "
            "AND canonical_variant_id IS NULL)",
            name="ck_graph_entity_resolution_canonical",
        ),
        sa.ForeignKeyConstraint(["canonical_variant_id"], ["graph_variants.id"]),
        sa.ForeignKeyConstraint(["offer_id"], ["offers.id"]),
        sa.ForeignKeyConstraint(
            ["raw_source_record_id"],
            ["raw_source_records.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "decision_key",
            name="uq_graph_entity_resolution_decision_key",
        ),
        sa.UniqueConstraint(
            "raw_source_record_id",
            "resolver_version",
            "policy_version",
            name="uq_graph_entity_resolution_decision_version",
        ),
    )
    with op.batch_alter_table("graph_entity_resolution_decisions") as batch_op:
        batch_op.create_index(
            batch_op.f("ix_graph_entity_resolution_decisions_raw_source_record_id"),
            ["raw_source_record_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_graph_entity_resolution_decisions_offer_id"),
            ["offer_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_graph_entity_resolution_decisions_resolution"),
            ["resolution"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_graph_entity_resolution_decisions_canonical_variant_id"),
            ["canonical_variant_id"],
            unique=False,
        )
        batch_op.create_index(
            "ix_graph_entity_resolution_state",
            ["resolution", "resolver_version"],
            unique=False,
        )


def downgrade() -> None:
    # Destructif uniquement pour le shadow P2F. Le rollback opérationnel normal
    # désactive le flag et conserve les preuves ; aucune table Core n'est touchée.
    with op.batch_alter_table("graph_entity_resolution_decisions") as batch_op:
        batch_op.drop_index("ix_graph_entity_resolution_state")
        batch_op.drop_index(
            batch_op.f("ix_graph_entity_resolution_decisions_canonical_variant_id")
        )
        batch_op.drop_index(
            batch_op.f("ix_graph_entity_resolution_decisions_resolution")
        )
        batch_op.drop_index(batch_op.f("ix_graph_entity_resolution_decisions_offer_id"))
        batch_op.drop_index(
            batch_op.f("ix_graph_entity_resolution_decisions_raw_source_record_id")
        )
    op.drop_table("graph_entity_resolution_decisions")

    with op.batch_alter_table("graph_entity_signal_projections") as batch_op:
        batch_op.drop_index(
            batch_op.f("ix_graph_entity_signal_projections_extractor_version")
        )
        batch_op.drop_index(
            batch_op.f("ix_graph_entity_signal_projections_raw_source_record_id")
        )
    op.drop_table("graph_entity_signal_projections")
