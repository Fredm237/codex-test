"""Ajoute les observations agrégées du lecteur sombre V2.

Revision ID: c6f4a8b0d2e5
Revises: b5d3f7a9c1e4
Create Date: 2026-09-03 22:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c6f4a8b0d2e5"
down_revision: Union[str, None] = "b5d3f7a9c1e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "v2_dark_read_observations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("observation_key", sa.String(length=64), nullable=False),
        sa.Column("hybrid_run_id", sa.Integer(), nullable=False),
        sa.Column("query_digest", sa.String(length=71), nullable=False),
        sa.Column("raw_query_retained", sa.Boolean(), nullable=False),
        sa.Column("comparison_version", sa.String(length=64), nullable=False),
        sa.Column("core_outcome", sa.String(length=16), nullable=False),
        sa.Column("v2_outcome", sa.String(length=16), nullable=False),
        sa.Column("core_candidate_count", sa.Integer(), nullable=False),
        sa.Column("v2_candidate_count", sa.Integer(), nullable=False),
        sa.Column("intersection_count", sa.Integer(), nullable=False),
        sa.Column("overlap_ppm", sa.Integer(), nullable=False),
        sa.Column("top1_state", sa.String(length=16), nullable=False),
        sa.Column("chain_complete", sa.Boolean(), nullable=False),
        sa.Column("terminal_outcome", sa.String(length=16), nullable=False),
        sa.Column("terminal_offer_state", sa.String(length=16), nullable=False),
        sa.Column("safety_state", sa.String(length=16), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "length(observation_key) = 64",
            name="ck_v2_dark_read_observation_key_sha256",
        ),
        sa.CheckConstraint(
            "length(query_digest) = 71",
            name="ck_v2_dark_read_query_digest",
        ),
        sa.CheckConstraint(
            "raw_query_retained = false",
            name="ck_v2_dark_read_no_raw_query",
        ),
        sa.CheckConstraint(
            "core_outcome IN ('CANDIDATES', 'NO_MATCH', 'INVALID')",
            name="ck_v2_dark_read_core_outcome",
        ),
        sa.CheckConstraint(
            "v2_outcome IN ('CANDIDATES', 'NO_MATCH', 'AMBIGUOUS', 'ERROR')",
            name="ck_v2_dark_read_v2_outcome",
        ),
        sa.CheckConstraint(
            "top1_state IN ('MATCH', 'MISMATCH', 'UNKNOWN')",
            name="ck_v2_dark_read_top1_state",
        ),
        sa.CheckConstraint(
            "terminal_offer_state IN ('MATCH', 'MISMATCH', 'UNKNOWN')",
            name="ck_v2_dark_read_terminal_offer_state",
        ),
        sa.CheckConstraint(
            "terminal_outcome IN ('BUY_NOW', 'WAIT', 'ABSTAIN', 'INCOMPLETE')",
            name="ck_v2_dark_read_terminal_outcome",
        ),
        sa.CheckConstraint(
            "safety_state IN ('SAFE', 'ABSTAIN', 'INVALID', 'INCOMPLETE')",
            name="ck_v2_dark_read_safety_state",
        ),
        sa.CheckConstraint(
            "core_candidate_count >= 0 AND v2_candidate_count >= 0 "
            "AND intersection_count >= 0",
            name="ck_v2_dark_read_candidate_counts",
        ),
        sa.CheckConstraint(
            "overlap_ppm >= 0 AND overlap_ppm <= 1000000",
            name="ck_v2_dark_read_overlap_ppm",
        ),
        sa.ForeignKeyConstraint(
            ["hybrid_run_id"],
            ["hybrid_retrieval_runs.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "hybrid_run_id",
            "comparison_version",
            "evaluated_at",
            name="uq_v2_dark_read_evaluation",
        ),
    )
    with op.batch_alter_table("v2_dark_read_observations") as batch_op:
        for column in (
            "hybrid_run_id",
            "query_digest",
            "comparison_version",
            "core_outcome",
            "v2_outcome",
            "top1_state",
            "chain_complete",
            "terminal_outcome",
            "terminal_offer_state",
            "safety_state",
        ):
            batch_op.create_index(
                batch_op.f(f"ix_v2_dark_read_observations_{column}"),
                [column],
                unique=False,
            )
        batch_op.create_index(
            batch_op.f("ix_v2_dark_read_observations_observation_key"),
            ["observation_key"],
            unique=True,
        )
        batch_op.create_index(
            "ix_v2_dark_read_safety_evaluated",
            ["safety_state", "evaluated_at"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("v2_dark_read_observations") as batch_op:
        batch_op.drop_index("ix_v2_dark_read_safety_evaluated")
        batch_op.drop_index(
            batch_op.f("ix_v2_dark_read_observations_observation_key")
        )
        for column in reversed(
            (
                "hybrid_run_id",
                "query_digest",
                "comparison_version",
                "core_outcome",
                "v2_outcome",
                "top1_state",
                "chain_complete",
                "terminal_outcome",
                "terminal_offer_state",
                "safety_state",
            )
        ):
            batch_op.drop_index(
                batch_op.f(f"ix_v2_dark_read_observations_{column}")
            )
    op.drop_table("v2_dark_read_observations")
