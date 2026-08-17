"""Modèles persistants de la FILON Intelligence Layer.

Ces tables sont volontairement parallèles au FILON Core. Elles peuvent relier une
inférence à une offre, un produit regroupé ou une décision, sans jamais modifier
les données marchandes, les prix ou la taxonomie qui alimentent le catalogue.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class IntelligenceProductFact(Base):
    """Attribut parallèle et versionné attaché à une offre ou un produit Core.

    Une valeur est toujours accompagnée de son statut de connaissance et de sa
    provenance. Le Fashion Expert peut donc exploiter une couleur ou un rôle
    sans transformer une inférence en colonne canonique du catalogue.
    """

    __tablename__ = "intelligence_product_facts"
    __table_args__ = (
        UniqueConstraint(
            "offer_id", "catalog_product_id", "field", "extractor_version",
            name="uq_intelligence_fact_target_field_version",
        ),
        Index("ix_intelligence_fact_offer_field", "offer_id", "field"),
        Index("ix_intelligence_fact_product_field", "catalog_product_id", "field"),
        Index("ix_intelligence_fact_status", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    offer_id: Mapped[int | None] = mapped_column(ForeignKey("offers.id"), nullable=True, index=True)
    catalog_product_id: Mapped[int | None] = mapped_column(
        ForeignKey("catalog_products.id"), nullable=True, index=True
    )
    field: Mapped[str] = mapped_column(String(64), index=True)
    value_json: Mapped[dict[str, Any] | list[Any] | str | int | float | bool | None] = mapped_column(JSON, nullable=True)
    # verified | inferred | unknown — jamais de valeur implicite.
    status: Mapped[str] = mapped_column(String(16), default="unknown", index=True)
    # core | merchant | product_description | deterministic_rule | model | human_review
    source_type: Mapped[str] = mapped_column(String(48), default="core")
    source_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    extractor_version: Mapped[str] = mapped_column(String(64), default="v1")
    observed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class IntelligenceRelation(Base):
    """Relation explicitement justifiée entre deux offres ou produits Core."""

    __tablename__ = "intelligence_relations"
    __table_args__ = (
        UniqueConstraint(
            "source_offer_id", "target_offer_id", "relation_type", "version",
            name="uq_intelligence_relation_offer_version",
        ),
        Index("ix_intelligence_relation_source_type", "source_offer_id", "relation_type"),
        Index("ix_intelligence_relation_target_type", "target_offer_id", "relation_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source_offer_id: Mapped[int | None] = mapped_column(ForeignKey("offers.id"), nullable=True, index=True)
    target_offer_id: Mapped[int | None] = mapped_column(ForeignKey("offers.id"), nullable=True, index=True)
    source_catalog_product_id: Mapped[int | None] = mapped_column(
        ForeignKey("catalog_products.id"), nullable=True, index=True
    )
    target_catalog_product_id: Mapped[int | None] = mapped_column(
        ForeignKey("catalog_products.id"), nullable=True, index=True
    )
    # compatible_with | complements | alternative_to | similar_to | contrasts_with
    relation_type: Mapped[str] = mapped_column(String(48), index=True)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(16), default="unknown", index=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_type: Mapped[str] = mapped_column(String(48), default="deterministic_rule")
    source_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    version: Mapped[str] = mapped_column(String(64), default="v1")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class IntelligenceTrace(Base):
    """Trace d’une décision, destinée à l’explicabilité et à la revue interne."""

    __tablename__ = "intelligence_traces"
    __table_args__ = (
        UniqueConstraint("trace_key", name="uq_intelligence_trace_key"),
        Index("ix_intelligence_trace_domain_status", "domain", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    trace_key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    domain: Mapped[str] = mapped_column(String(48), index=True)
    status: Mapped[str] = mapped_column(String(24), index=True)
    request_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    intent_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    candidates_json: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True)
    filters_json: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True)
    result_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    rules_version: Mapped[str] = mapped_column(String(64), default="v1")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class IntelligenceFeedback(Base):
    """Feedback utilisateur ou revue humaine, sans réécriture silencieuse du Core."""

    __tablename__ = "intelligence_feedback"
    __table_args__ = (Index("ix_intelligence_feedback_trace_action", "trace_id", "action"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    trace_id: Mapped[int | None] = mapped_column(
        ForeignKey("intelligence_traces.id"), nullable=True, index=True
    )
    recommendation_key: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    # keep | reject | too_expensive | wrong_style | wrong_context | approve | correct
    action: Mapped[str] = mapped_column(String(48), index=True)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class IntelligenceBenchmark(Base):
    """Cas de référence versionné, séparé des données utilisateurs et du Core."""

    __tablename__ = "intelligence_benchmarks"
    __table_args__ = (
        UniqueConstraint("domain", "case_key", "version", name="uq_intelligence_benchmark_version"),
        Index("ix_intelligence_benchmark_domain_status", "domain", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    domain: Mapped[str] = mapped_column(String(48), index=True)
    case_key: Mapped[str] = mapped_column(String(64), index=True)
    version: Mapped[str] = mapped_column(String(64), default="v1")
    status: Mapped[str] = mapped_column(String(24), default="draft", index=True)
    input_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    expected_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
