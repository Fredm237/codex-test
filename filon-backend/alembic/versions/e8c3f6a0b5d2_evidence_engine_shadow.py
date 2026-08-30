"""Ajoute les claims et l'éligibilité décisionnelle shadow.

Revision ID: e8c3f6a0b5d2
Revises: d7b2e5f9a4c1
Create Date: 2026-08-31 01:10:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e8c3f6a0b5d2"
down_revision: Union[str, None] = "d7b2e5f9a4c1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "evidence_claim_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("raw_source_record_id", sa.Integer(), nullable=False),
        sa.Column("offer_observation_id", sa.Integer(), nullable=False),
        sa.Column("subject_type", sa.String(length=24), nullable=False),
        sa.Column("subject_ref", sa.String(length=96), nullable=False),
        sa.Column("claim_code", sa.String(length=48), nullable=False),
        sa.Column("value_json", sa.JSON(none_as_null=True), nullable=True),
        sa.Column("knowledge_status", sa.String(length=16), nullable=False),
        sa.Column("source_type", sa.String(length=48), nullable=False),
        sa.Column("source_ref", sa.String(length=96), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("observed_at", sa.DateTime(), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(), nullable=False),
        sa.Column("valid_until", sa.DateTime(), nullable=True),
        sa.Column("eligibility", sa.String(length=16), nullable=False),
        sa.Column("reason_code", sa.String(length=48), nullable=False),
        sa.Column("policy_version", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "knowledge_status IN ('VERIFIED', 'INFERRED', 'UNKNOWN')",
            name="ck_evidence_claim_knowledge",
        ),
        sa.CheckConstraint(
            "eligibility IN ('eligible', 'ineligible', 'unknown')",
            name="ck_evidence_claim_eligibility",
        ),
        sa.CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="ck_evidence_claim_confidence",
        ),
        sa.CheckConstraint(
            "(eligibility = 'eligible' AND knowledge_status = 'VERIFIED' "
            "AND value_json IS NOT NULL) OR eligibility <> 'eligible'",
            name="ck_evidence_claim_eligible_value",
        ),
        sa.CheckConstraint(
            "(knowledge_status = 'UNKNOWN' AND value_json IS NULL) OR "
            "knowledge_status <> 'UNKNOWN'",
            name="ck_evidence_claim_unknown_value",
        ),
        sa.ForeignKeyConstraint(
            ["raw_source_record_id"],
            ["raw_source_records.id"],
        ),
        sa.ForeignKeyConstraint(
            ["offer_observation_id"],
            ["graph_offer_observations.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "offer_observation_id",
            "claim_code",
            "policy_version",
            "evaluated_at",
            name="uq_evidence_claim_evaluation",
        ),
    )
    with op.batch_alter_table("evidence_claim_records", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_evidence_claim_records_claim_code"),
            ["claim_code"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_evidence_claim_records_eligibility"),
            ["eligibility"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_evidence_claim_records_offer_observation_id"),
            ["offer_observation_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_evidence_claim_records_raw_source_record_id"),
            ["raw_source_record_id"],
            unique=False,
        )
        batch_op.create_index(
            "ix_evidence_claim_policy_state",
            ["claim_code", "eligibility"],
            unique=False,
        )

    op.create_table(
        "decision_eligibility_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("raw_source_record_id", sa.Integer(), nullable=False),
        sa.Column("offer_observation_id", sa.Integer(), nullable=False),
        sa.Column("offer_id", sa.Integer(), nullable=False),
        sa.Column("highest_stage", sa.String(length=24), nullable=False),
        sa.Column("decision_eligible", sa.Boolean(), nullable=False),
        sa.Column("blocker_reason", sa.String(length=48), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(), nullable=False),
        sa.Column("policy_version", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "highest_stage IN ('DISCOVERABLE', 'COMPARABLE', 'RANKABLE', "
            "'DECISION_ELIGIBLE')",
            name="ck_decision_eligibility_stage",
        ),
        sa.CheckConstraint(
            "(decision_eligible IS TRUE AND highest_stage = 'DECISION_ELIGIBLE') OR "
            "(decision_eligible IS FALSE AND highest_stage <> 'DECISION_ELIGIBLE')",
            name="ck_decision_eligibility_consistency",
        ),
        sa.ForeignKeyConstraint(
            ["raw_source_record_id"],
            ["raw_source_records.id"],
        ),
        sa.ForeignKeyConstraint(
            ["offer_observation_id"],
            ["graph_offer_observations.id"],
        ),
        sa.ForeignKeyConstraint(["offer_id"], ["offers.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "offer_observation_id",
            "policy_version",
            "evaluated_at",
            name="uq_decision_eligibility_evaluation",
        ),
    )
    with op.batch_alter_table("decision_eligibility_records", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_decision_eligibility_records_highest_stage"),
            ["highest_stage"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_decision_eligibility_records_offer_id"),
            ["offer_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_decision_eligibility_records_offer_observation_id"),
            ["offer_observation_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_decision_eligibility_records_raw_source_record_id"),
            ["raw_source_record_id"],
            unique=False,
        )
        batch_op.create_index(
            "ix_decision_eligibility_stage",
            ["highest_stage", "evaluated_at"],
            unique=False,
        )


def downgrade() -> None:
    op.drop_table("decision_eligibility_records")
    op.drop_table("evidence_claim_records")
