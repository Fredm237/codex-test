"""Ajoute la télémétrie agrégée du lecteur canary V2.

Revision ID: d7a5b9c1e3f6
Revises: c6f4a8b0d2e5
Create Date: 2026-09-03 23:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d7a5b9c1e3f6"
down_revision: Union[str, None] = "c6f4a8b0d2e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "v2_canary_read_observations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("observation_key", sa.String(length=64), nullable=False),
        sa.Column("gate_evaluation_id", sa.String(length=71), nullable=False),
        sa.Column("cohort", sa.String(length=16), nullable=False),
        sa.Column("assignment_reason", sa.String(length=64), nullable=False),
        sa.Column("source", sa.String(length=16), nullable=False),
        sa.Column("response_type", sa.String(length=16), nullable=False),
        sa.Column("fallback_reason", sa.String(length=64), nullable=True),
        sa.Column("core_latency_us", sa.Integer(), nullable=False),
        sa.Column("v2_latency_us", sa.Integer(), nullable=True),
        sa.Column("total_latency_us", sa.Integer(), nullable=False),
        sa.Column("chain_complete", sa.Boolean(), nullable=True),
        sa.Column("safety_state", sa.String(length=16), nullable=True),
        sa.Column("provenance_complete", sa.Boolean(), nullable=True),
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
            name="ck_v2_canary_observation_key_sha256",
        ),
        sa.CheckConstraint(
            "length(gate_evaluation_id) = 71",
            name="ck_v2_canary_gate_evaluation_digest",
        ),
        sa.CheckConstraint(
            "cohort IN ('core', 'canary')",
            name="ck_v2_canary_cohort",
        ),
        sa.CheckConstraint(
            "source IN ('core_v1', 'v2')",
            name="ck_v2_canary_source",
        ),
        sa.CheckConstraint(
            "response_type IN ('CORE', 'ABSTAIN', 'BUY_NOW', 'WAIT')",
            name="ck_v2_canary_response_type",
        ),
        sa.CheckConstraint(
            "safety_state IS NULL OR safety_state IN ('SAFE', 'ABSTAIN', 'INVALID')",
            name="ck_v2_canary_safety_state",
        ),
        sa.CheckConstraint(
            "core_latency_us >= 0 AND total_latency_us >= core_latency_us "
            "AND (v2_latency_us IS NULL OR v2_latency_us >= 0)",
            name="ck_v2_canary_latency",
        ),
        sa.CheckConstraint(
            "raw_query_retained = false",
            name="ck_v2_canary_no_raw_query",
        ),
        sa.CheckConstraint(
            "(source = 'core_v1' AND response_type = 'CORE' "
            "AND fallback_reason IS NOT NULL) OR "
            "(source = 'v2' AND cohort = 'canary' AND response_type != 'CORE' "
            "AND fallback_reason IS NULL AND v2_latency_us IS NOT NULL "
            "AND chain_complete = true AND provenance_complete = true "
            "AND safety_state IN ('SAFE', 'ABSTAIN'))",
            name="ck_v2_canary_atomic_source",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("v2_canary_read_observations") as batch_op:
        for column in (
            "gate_evaluation_id",
            "cohort",
            "source",
            "response_type",
        ):
            batch_op.create_index(
                batch_op.f(f"ix_v2_canary_read_observations_{column}"),
                [column],
                unique=False,
            )
        batch_op.create_index(
            batch_op.f("ix_v2_canary_read_observations_observation_key"),
            ["observation_key"],
            unique=True,
        )
        batch_op.create_index(
            "ix_v2_canary_source_evaluated",
            ["source", "evaluated_at"],
            unique=False,
        )
        batch_op.create_index(
            "ix_v2_canary_gate_evaluated",
            ["gate_evaluation_id", "evaluated_at"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("v2_canary_read_observations") as batch_op:
        batch_op.drop_index("ix_v2_canary_gate_evaluated")
        batch_op.drop_index("ix_v2_canary_source_evaluated")
        batch_op.drop_index(
            batch_op.f("ix_v2_canary_read_observations_observation_key")
        )
        for column in reversed(
            ("gate_evaluation_id", "cohort", "source", "response_type")
        ):
            batch_op.drop_index(
                batch_op.f(f"ix_v2_canary_read_observations_{column}")
            )
    op.drop_table("v2_canary_read_observations")
