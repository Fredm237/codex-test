"""Ajoute la provenance des fenêtres et les dark reads de trafic réel.

Revision ID: f9c7d1e3a5b8
Revises: e8b6c0d2f4a7
Create Date: 2026-09-04 12:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f9c7d1e3a5b8"
down_revision: Union[str, None] = "e8b6c0d2f4a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("v2_chain_executions") as batch_op:
        batch_op.add_column(sa.Column("campaign_id", sa.String(71), nullable=True))
        batch_op.add_column(sa.Column("execution_kind", sa.String(16), nullable=True))
        batch_op.add_column(sa.Column("source_execution_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("window_metrics_json", sa.JSON(), nullable=True))
        batch_op.create_foreign_key(
            "fk_v2_chain_execution_source",
            "v2_chain_executions",
            ["source_execution_id"],
            ["id"],
            ondelete="RESTRICT",
        )
        batch_op.create_check_constraint(
            "ck_v2_chain_execution_campaign",
            "(campaign_id IS NULL AND execution_kind IS NULL "
            "AND source_execution_id IS NULL) OR "
            "(length(campaign_id) = 71 "
            "AND execution_kind IN ('progression', 'replay', 'recovery') "
            "AND ((execution_kind = 'progression' AND source_execution_id IS NULL) "
            "OR (execution_kind IN ('replay', 'recovery') "
            "AND source_execution_id IS NOT NULL)))",
        )
        batch_op.create_index(
            "ix_v2_chain_campaign_execution",
            ["campaign_id", "execution_kind", "id"],
            unique=False,
        )

    with op.batch_alter_table("v2_canary_read_observations") as batch_op:
        batch_op.drop_constraint("ck_v2_canary_atomic_source", type_="check")
        batch_op.add_column(
            sa.Column("eligibility_evaluation_id", sa.String(71), nullable=True)
        )
        batch_op.add_column(sa.Column("eligibility_status", sa.String(16), nullable=True))
        batch_op.add_column(sa.Column("vertical", sa.String(32), nullable=True))
        batch_op.add_column(sa.Column("locale", sa.String(8), nullable=True))
        batch_op.add_column(sa.Column("decision_type", sa.String(32), nullable=True))
        batch_op.create_check_constraint(
            "ck_v2_canary_eligibility_digest",
            "eligibility_evaluation_id IS NULL OR length(eligibility_evaluation_id) = 71",
        )
        batch_op.create_check_constraint(
            "ck_v2_canary_eligibility_bundle",
            "(eligibility_evaluation_id IS NULL AND eligibility_status IS NULL "
            "AND vertical IS NULL AND locale IS NULL AND decision_type IS NULL) OR "
            "(eligibility_evaluation_id IS NOT NULL "
            "AND eligibility_status IN ('eligible', 'ineligible') "
            "AND vertical IS NOT NULL AND locale IS NOT NULL "
            "AND decision_type IS NOT NULL)",
        )
        batch_op.create_check_constraint(
            "ck_v2_canary_atomic_source",
            "(source = 'core_v1' AND response_type = 'CORE' "
            "AND fallback_reason IS NOT NULL) OR "
            "(source = 'v2' AND cohort = 'canary' AND response_type != 'CORE' "
            "AND fallback_reason IS NULL AND v2_latency_us IS NOT NULL "
            "AND eligibility_status = 'eligible' "
            "AND chain_complete = true AND provenance_complete = true "
            "AND safety_state IN ('SAFE', 'ABSTAIN'))",
        )
        for column in (
            "eligibility_evaluation_id",
            "vertical",
            "locale",
            "decision_type",
        ):
            batch_op.create_index(
                batch_op.f(f"ix_v2_canary_read_observations_{column}"),
                [column],
                unique=False,
            )

    op.create_table(
        "v2_live_dark_read_observations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("observation_key", sa.String(64), nullable=False),
        sa.Column("campaign_id", sa.String(71), nullable=False),
        sa.Column("comparison_version", sa.String(64), nullable=False),
        sa.Column("surface", sa.String(32), nullable=False),
        sa.Column("vertical", sa.String(32), nullable=True),
        sa.Column("locale", sa.String(8), nullable=False),
        sa.Column("country_code", sa.String(2), nullable=True),
        sa.Column("core_outcome", sa.String(16), nullable=False),
        sa.Column("v2_outcome", sa.String(16), nullable=False),
        sa.Column("classification", sa.String(32), nullable=False),
        sa.Column("core_candidate_count", sa.Integer(), nullable=False),
        sa.Column("v2_candidate_count", sa.Integer(), nullable=False),
        sa.Column("core_latency_us", sa.Integer(), nullable=False),
        sa.Column("v2_latency_us", sa.Integer(), nullable=False),
        sa.Column("chain_complete", sa.Boolean(), nullable=False),
        sa.Column("safety_state", sa.String(16), nullable=False),
        sa.Column("provenance_complete", sa.Boolean(), nullable=False),
        sa.Column("raw_query_retained", sa.Boolean(), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "length(observation_key) = 64",
            name="ck_v2_live_dark_observation_key",
        ),
        sa.CheckConstraint(
            "length(campaign_id) = 71",
            name="ck_v2_live_dark_campaign",
        ),
        sa.CheckConstraint(
            "surface IN ('advise', 'advise_stream')",
            name="ck_v2_live_dark_surface",
        ),
        sa.CheckConstraint(
            "core_outcome IN ('CANDIDATES', 'NO_MATCH', 'ERROR')",
            name="ck_v2_live_dark_core_outcome",
        ),
        sa.CheckConstraint(
            "v2_outcome IN ('BUY_NOW', 'WAIT', 'ABSTAIN', 'ERROR', 'UNSUPPORTED')",
            name="ck_v2_live_dark_v2_outcome",
        ),
        sa.CheckConstraint(
            "classification IN ('V2_IMPROVEMENT', 'V1_IMPROVEMENT', "
            "'BOTH_VALID', 'V2_ABSTAINS_CORRECTLY', 'V2_UNSUPPORTED', "
            "'DATA_PROBLEM', 'ENGINE_PROBLEM', 'AMBIGUOUS')",
            name="ck_v2_live_dark_classification",
        ),
        sa.CheckConstraint(
            "core_candidate_count >= 0 AND v2_candidate_count >= 0 "
            "AND core_latency_us >= 0 AND v2_latency_us >= 0",
            name="ck_v2_live_dark_counts_latency",
        ),
        sa.CheckConstraint(
            "safety_state IN ('SAFE', 'ABSTAIN', 'INVALID', 'UNSUPPORTED')",
            name="ck_v2_live_dark_safety_state",
        ),
        sa.CheckConstraint(
            "raw_query_retained = false",
            name="ck_v2_live_dark_no_raw_query",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("v2_live_dark_read_observations") as batch_op:
        batch_op.create_index(
            batch_op.f("ix_v2_live_dark_read_observations_observation_key"),
            ["observation_key"],
            unique=True,
        )
        batch_op.create_index(
            "ix_v2_live_dark_classification_evaluated",
            ["campaign_id", "classification", "evaluated_at"],
            unique=False,
        )

    op.create_table(
        "v2_promotion_proofs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("proof_ref", sa.String(71), nullable=False),
        sa.Column("scope_ref", sa.String(71), nullable=False),
        sa.Column("proof_kind", sa.String(64), nullable=False),
        sa.Column("artifact_ref", sa.String(512), nullable=False),
        sa.Column("artifact_digest", sa.String(71), nullable=False),
        sa.Column("verifier_version", sa.String(64), nullable=False),
        sa.Column("verification_status", sa.String(16), nullable=False),
        sa.Column("raw_payload_retained", sa.Boolean(), nullable=False),
        sa.Column("verified_at", sa.DateTime(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "length(proof_ref) = 71 AND length(scope_ref) = 71 "
            "AND length(artifact_digest) = 71",
            name="ck_v2_promotion_proof_digests",
        ),
        sa.CheckConstraint(
            "verification_status IN ('VERIFIED', 'REJECTED')",
            name="ck_v2_promotion_proof_status",
        ),
        sa.CheckConstraint(
            "raw_payload_retained = false",
            name="ck_v2_promotion_proof_no_raw_payload",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("v2_promotion_proofs") as batch_op:
        batch_op.create_index(
            batch_op.f("ix_v2_promotion_proofs_proof_ref"),
            ["proof_ref"],
            unique=True,
        )
        batch_op.create_index(
            batch_op.f("ix_v2_promotion_proofs_scope_ref"),
            ["scope_ref"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_v2_promotion_proofs_proof_kind"),
            ["proof_kind"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_v2_promotion_proofs_verification_status"),
            ["verification_status"],
            unique=False,
        )
        batch_op.create_index(
            "ix_v2_promotion_proof_scope_kind_verified",
            ["scope_ref", "proof_kind", "verified_at"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("v2_promotion_proofs") as batch_op:
        batch_op.drop_index("ix_v2_promotion_proof_scope_kind_verified")
        batch_op.drop_index(
            batch_op.f("ix_v2_promotion_proofs_verification_status")
        )
        batch_op.drop_index(batch_op.f("ix_v2_promotion_proofs_proof_kind"))
        batch_op.drop_index(batch_op.f("ix_v2_promotion_proofs_scope_ref"))
        batch_op.drop_index(batch_op.f("ix_v2_promotion_proofs_proof_ref"))
    op.drop_table("v2_promotion_proofs")

    with op.batch_alter_table("v2_live_dark_read_observations") as batch_op:
        batch_op.drop_index("ix_v2_live_dark_classification_evaluated")
        batch_op.drop_index(
            batch_op.f("ix_v2_live_dark_read_observations_observation_key")
        )
    op.drop_table("v2_live_dark_read_observations")

    with op.batch_alter_table("v2_canary_read_observations") as batch_op:
        batch_op.drop_constraint("ck_v2_canary_atomic_source", type_="check")
        for column in reversed(
            (
                "eligibility_evaluation_id",
                "vertical",
                "locale",
                "decision_type",
            )
        ):
            batch_op.drop_index(
                batch_op.f(f"ix_v2_canary_read_observations_{column}")
            )
        batch_op.drop_constraint("ck_v2_canary_eligibility_bundle", type_="check")
        batch_op.drop_constraint("ck_v2_canary_eligibility_digest", type_="check")
        batch_op.drop_column("decision_type")
        batch_op.drop_column("locale")
        batch_op.drop_column("vertical")
        batch_op.drop_column("eligibility_status")
        batch_op.drop_column("eligibility_evaluation_id")
        batch_op.create_check_constraint(
            "ck_v2_canary_atomic_source",
            "(source = 'core_v1' AND response_type = 'CORE' "
            "AND fallback_reason IS NOT NULL) OR "
            "(source = 'v2' AND cohort = 'canary' AND response_type != 'CORE' "
            "AND fallback_reason IS NULL AND v2_latency_us IS NOT NULL "
            "AND chain_complete = true AND provenance_complete = true "
            "AND safety_state IN ('SAFE', 'ABSTAIN'))",
        )

    with op.batch_alter_table("v2_chain_executions") as batch_op:
        batch_op.drop_index("ix_v2_chain_campaign_execution")
        batch_op.drop_constraint("ck_v2_chain_execution_campaign", type_="check")
        batch_op.drop_constraint("fk_v2_chain_execution_source", type_="foreignkey")
        batch_op.drop_column("window_metrics_json")
        batch_op.drop_column("source_execution_id")
        batch_op.drop_column("execution_kind")
        batch_op.drop_column("campaign_id")
