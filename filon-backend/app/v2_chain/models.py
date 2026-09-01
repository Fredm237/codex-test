"""Journal opérationnel de la chaîne V2 shadow, sans payload brut."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Index,
    Integer,
    JSON,
    String,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class V2ChainExecution(Base):
    """Une exécution bornée et traçable de la chaîne V2."""

    __tablename__ = "v2_chain_executions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('running', 'succeeded', 'failed', 'interrupted')",
            name="ck_v2_chain_execution_status",
        ),
        CheckConstraint(
            "mode IN ('dry_run', 'apply')",
            name="ck_v2_chain_execution_mode",
        ),
        CheckConstraint(
            "after_raw_id >= 0 AND row_limit >= 1 AND row_limit <= 100",
            name="ck_v2_chain_execution_window",
        ),
        Index("ix_v2_chain_executions_started", "started_at"),
        Index(
            "uq_v2_chain_executions_running",
            "status",
            unique=True,
            postgresql_where=text("status = 'running'"),
            sqlite_where=text("status = 'running'"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    execution_key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    mode: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(16), default="running", index=True)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime)
    vertical: Mapped[str] = mapped_column(String(64))
    after_raw_id: Mapped[int] = mapped_column(Integer)
    row_limit: Mapped[int] = mapped_column(Integer)
    last_raw_source_id: Mapped[int] = mapped_column(Integer)
    checkpoints_json: Mapped[dict[str, int]] = mapped_column(JSON)
    completed_stages_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    report_evaluation_id: Mapped[str | None] = mapped_column(
        String(71), nullable=True
    )
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    heartbeat_at: Mapped[datetime] = mapped_column(DateTime)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)
