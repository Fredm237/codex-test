"""Modèles append-only du pipeline d'observation shadow.

Ils restent parallèles au Core v1 : aucun endpoint public ne les lit tant que
les gates de replay et de qualité ne sont pas validés.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RawSourceRecord(Base):
    """Payload source immuable et dédupliqué par sa clé de replay."""

    __tablename__ = "raw_source_records"
    __table_args__ = (
        UniqueConstraint("replay_key", name="uq_raw_source_replay_key"),
        CheckConstraint(
            "length(payload_checksum) = 64",
            name="ck_raw_source_checksum_sha256",
        ),
        CheckConstraint(
            "length(replay_key) = 64",
            name="ck_raw_source_replay_key_sha256",
        ),
        Index(
            "ix_raw_source_lookup",
            "source_type",
            "source_ref",
            "source_record_key",
        ),
        Index("ix_raw_source_observed_at", "observed_at"),
        Index(
            "ix_raw_source_sync_feed_record",
            "sync_run_id",
            "source_ref",
            "source_record_key",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source_type: Mapped[str] = mapped_column(String(48))
    source_ref: Mapped[str] = mapped_column(String(191))
    source_record_key: Mapped[str] = mapped_column(String(255))
    schema_version: Mapped[str] = mapped_column(String(64))
    context_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    payload_checksum: Mapped[str] = mapped_column(String(64), index=True)
    replay_key: Mapped[str] = mapped_column(String(64))
    sync_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("catalog_sync_runs.id"),
        nullable=True,
        index=True,
    )
    observed_at: Mapped[datetime] = mapped_column(DateTime)
    received_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
    )


class Observation(Base):
    """Fait champ-par-champ, versionné et relié au payload qui le justifie."""

    __tablename__ = "observations"
    __table_args__ = (
        UniqueConstraint(
            "raw_source_record_id",
            "subject_type",
            "subject_ref",
            "field",
            "transformation_version",
            name="uq_observation_projection_field_version",
        ),
        CheckConstraint(
            "status IN ('verified', 'inferred', 'unknown')",
            name="ck_observation_status",
        ),
        CheckConstraint(
            "confidence >= 0 AND confidence <= 1",
            name="ck_observation_confidence",
        ),
        Index("ix_observation_subject", "subject_type", "subject_ref"),
        Index("ix_observation_field_status", "field", "status"),
        Index("ix_observation_observed_at", "observed_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    raw_source_record_id: Mapped[int] = mapped_column(
        ForeignKey("raw_source_records.id"),
        index=True,
    )
    subject_type: Mapped[str] = mapped_column(String(48))
    subject_ref: Mapped[str] = mapped_column(String(255))
    offer_id: Mapped[int | None] = mapped_column(
        ForeignKey("offers.id"),
        nullable=True,
        index=True,
    )
    field: Mapped[str] = mapped_column(String(64))
    value_json: Mapped[Any | None] = mapped_column(
        JSON(none_as_null=True),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(16))
    source_type: Mapped[str] = mapped_column(String(48))
    source_ref: Mapped[str] = mapped_column(String(255))
    observed_at: Mapped[datetime] = mapped_column(DateTime)
    transformation: Mapped[str] = mapped_column(String(64))
    transformation_version: Mapped[str] = mapped_column(String(64))
    confidence: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
    )


class QuarantineRecord(Base):
    """Anomalie structurée, résolvable sans supprimer sa preuve source."""

    __tablename__ = "quarantine_records"
    __table_args__ = (
        UniqueConstraint("issue_key", name="uq_quarantine_issue_key"),
        CheckConstraint(
            "status IN ('open', 'released', 'discarded')",
            name="ck_quarantine_status",
        ),
        Index("ix_quarantine_status_error", "status", "error_code"),
        Index("ix_quarantine_stage", "stage"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    raw_source_record_id: Mapped[int] = mapped_column(
        ForeignKey("raw_source_records.id"),
        index=True,
    )
    issue_key: Mapped[str] = mapped_column(String(64))
    error_code: Mapped[str] = mapped_column(String(64))
    stage: Mapped[str] = mapped_column(String(64))
    field: Mapped[str | None] = mapped_column(String(64), nullable=True)
    rejected_value_json: Mapped[Any | None] = mapped_column(
        JSON(none_as_null=True),
        nullable=True,
    )
    reason: Mapped[str] = mapped_column(String(255))
    details_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON(none_as_null=True),
        nullable=True,
    )
    transformation_version: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(16), default="open")
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
