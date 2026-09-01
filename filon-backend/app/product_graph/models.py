"""Modèles expand-only du Product/Variant Graph shadow.

Les nœuds v2 vivent à côté de ``catalog_products`` et ``offers``. Une
identité forte peut donc être observée et rejouée sans modifier les lectures
Core v1 ni transformer une hypothèse en vérité publique.
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
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

# Les modèles Graph référencent des tables Core et Observation. Les importer ici
# garantit que ces tables appartiennent à la même ``MetaData`` même lorsqu'un
# worker de maintenance charge directement ce module, sans passer par l'app web.
from app.db import models as core_models  # noqa: F401
from app.db.base import Base
from app.observations import models as observation_models  # noqa: F401


class GraphBrand(Base):
    """Marque canonique créée seulement à partir d'une preuve forte future."""

    __tablename__ = "graph_brands"

    id: Mapped[int] = mapped_column(primary_key=True)
    brand_key: Mapped[str] = mapped_column(String(96), unique=True, index=True)
    canonical_name: Mapped[str] = mapped_column(String(191))
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
    )

class GraphBrandAlias(Base):
    """Alias sourcé ; un libellé seul ne crée jamais une marque."""

    __tablename__ = "graph_brand_aliases"
    __table_args__ = (
        UniqueConstraint(
            "brand_id",
            "raw_source_record_id",
            "normalized_alias",
            name="uq_graph_brand_alias_evidence",
        ),
        Index("ix_graph_brand_alias_normalized", "normalized_alias"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    brand_id: Mapped[int] = mapped_column(
        ForeignKey("graph_brands.id"),
        index=True,
    )
    raw_source_record_id: Mapped[int] = mapped_column(
        ForeignKey("raw_source_records.id"),
        index=True,
    )
    alias: Mapped[str] = mapped_column(String(191))
    normalized_alias: Mapped[str] = mapped_column(String(191))
    source_ref: Mapped[str] = mapped_column(String(255))
    observed_at: Mapped[datetime] = mapped_column(DateTime)


class GraphProductFamily(Base):
    """Gamme d'une marque ; aucune famille n'est déduite du titre marchand."""

    __tablename__ = "graph_product_families"
    __table_args__ = (
        UniqueConstraint("brand_id", "family_key", name="uq_graph_family_brand_key"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    family_key: Mapped[str] = mapped_column(String(128), index=True)
    brand_id: Mapped[int] = mapped_column(
        ForeignKey("graph_brands.id"),
        index=True,
    )
    canonical_name: Mapped[str] = mapped_column(String(255))
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
    )


class GraphProductModel(Base):
    """Modèle produit ; ``family_id`` peut rester inconnu sans fallback."""

    __tablename__ = "graph_product_models"

    id: Mapped[int] = mapped_column(primary_key=True)
    model_key: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    family_id: Mapped[int | None] = mapped_column(
        ForeignKey("graph_product_families.id"),
        nullable=True,
        index=True,
    )
    canonical_name: Mapped[str] = mapped_column(String(255))
    model_code: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
    )


class GraphVariant(Base):
    """Variante canonique issue d'un identifiant global exact."""

    __tablename__ = "graph_variants"
    __table_args__ = (
        CheckConstraint(
            "status IN ('shadow', 'reviewed', 'retired')",
            name="ck_graph_variant_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    variant_key: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    model_id: Mapped[int | None] = mapped_column(
        ForeignKey("graph_product_models.id"),
        nullable=True,
        index=True,
    )
    attributes_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(16), default="shadow", index=True)
    resolver_version: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
    )


class GraphIdentifier(Base):
    """Identifiant normalisé, scoped et relié à une seule variante."""

    __tablename__ = "graph_identifiers"
    __table_args__ = (
        UniqueConstraint(
            "namespace",
            "scope",
            "normalized_value",
            name="uq_graph_identifier_scope_value",
        ),
        CheckConstraint(
            "namespace IN ('gtin')",
            name="ck_graph_identifier_namespace_v1",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    variant_id: Mapped[int] = mapped_column(
        ForeignKey("graph_variants.id"),
        index=True,
    )
    namespace: Mapped[str] = mapped_column(String(24))
    scope: Mapped[str] = mapped_column(String(96))
    normalized_value: Mapped[str] = mapped_column(String(191), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
    )


class GraphIdentifierEvidence(Base):
    """Provenance append-only d'un identifiant de variante."""

    __tablename__ = "graph_identifier_evidence"
    __table_args__ = (
        UniqueConstraint(
            "identifier_id",
            "raw_source_record_id",
            name="uq_graph_identifier_raw_evidence",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    identifier_id: Mapped[int] = mapped_column(
        ForeignKey("graph_identifiers.id"),
        index=True,
    )
    raw_source_record_id: Mapped[int] = mapped_column(
        ForeignKey("raw_source_records.id"),
        index=True,
    )
    source_type: Mapped[str] = mapped_column(String(48))
    source_ref: Mapped[str] = mapped_column(String(255))
    observed_at: Mapped[datetime] = mapped_column(DateTime)


class GraphOfferVariantLink(Base):
    """Résolution versionnée d'une offre vers une variante, jamais servie v1."""

    __tablename__ = "graph_offer_variant_links"
    __table_args__ = (
        UniqueConstraint(
            "raw_source_record_id",
            "resolver_version",
            name="uq_graph_offer_resolution_version",
        ),
        CheckConstraint(
            "resolution IN ('resolved', 'quarantine', 'rejected')",
            name="ck_graph_offer_resolution",
        ),
        CheckConstraint(
            "reason_code IN ('exact_gtin', 'missing_gtin', 'invalid_gtin', "
            "'conflicting_gtin', 'candidate_mismatch')",
            name="ck_graph_offer_resolution_reason",
        ),
        CheckConstraint(
            "(resolution = 'resolved' AND variant_id IS NOT NULL) OR "
            "(resolution <> 'resolved' AND variant_id IS NULL)",
            name="ck_graph_offer_resolution_variant",
        ),
        Index("ix_graph_offer_resolution_state", "resolution", "reason_code"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    raw_source_record_id: Mapped[int] = mapped_column(
        ForeignKey("raw_source_records.id"),
        index=True,
    )
    offer_id: Mapped[int] = mapped_column(ForeignKey("offers.id"), index=True)
    variant_id: Mapped[int | None] = mapped_column(
        ForeignKey("graph_variants.id"),
        nullable=True,
        index=True,
    )
    resolution: Mapped[str] = mapped_column(String(16), index=True)
    reason_code: Mapped[str] = mapped_column(String(32))
    resolver_version: Mapped[str] = mapped_column(String(64))
    observed_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
    )


class GraphIdentityAssertion(Base):
    """Fait d'identité sourcé, antérieur à toute promotion canonique.

    Une assertion observée ou validée ne remplit jamais implicitement Brand,
    Family ou Model. Elle préserve la valeur source, son scope et sa version
    afin qu'un resolver futur puisse la rejouer ou l'abstenir.
    """

    __tablename__ = "graph_identity_assertions"
    __table_args__ = (
        UniqueConstraint(
            "assertion_key",
            name="uq_graph_identity_assertion_key",
        ),
        CheckConstraint(
            "length(assertion_key) = 64",
            name="ck_graph_identity_assertion_key_sha256",
        ),
        CheckConstraint(
            "subject_type IN ('brand', 'product_family', 'product_model', 'variant')",
            name="ck_graph_identity_assertion_subject",
        ),
        CheckConstraint(
            "status IN ('observed', 'validated', 'conflict', 'quarantine')",
            name="ck_graph_identity_assertion_status",
        ),
        CheckConstraint(
            "identifier_namespace IS NULL OR identifier_namespace IN "
            "('gtin', 'mpn', 'merchant_sku', 'source_product_id')",
            name="ck_graph_identity_assertion_namespace",
        ),
        CheckConstraint(
            "(identifier_namespace IS NULL AND identifier_scope IS NULL) OR "
            "(identifier_namespace IS NOT NULL AND identifier_scope IS NOT NULL)",
            name="ck_graph_identity_assertion_scope",
        ),
        Index(
            "ix_graph_identity_assertion_subject",
            "subject_type",
            "subject_ref",
        ),
        Index(
            "ix_graph_identity_assertion_field_status",
            "field",
            "status",
        ),
        Index(
            "ix_graph_identity_assertion_identifier",
            "identifier_namespace",
            "identifier_scope",
            "normalized_value",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    assertion_key: Mapped[str] = mapped_column(String(64))
    raw_source_record_id: Mapped[int] = mapped_column(
        ForeignKey("raw_source_records.id"),
        index=True,
    )
    offer_id: Mapped[int] = mapped_column(ForeignKey("offers.id"), index=True)
    subject_type: Mapped[str] = mapped_column(String(32))
    subject_ref: Mapped[str] = mapped_column(String(255))
    field: Mapped[str] = mapped_column(String(64))
    value_json: Mapped[Any] = mapped_column(JSON)
    normalized_value: Mapped[str | None] = mapped_column(
        String(191),
        nullable=True,
    )
    identifier_namespace: Mapped[str | None] = mapped_column(
        String(24),
        nullable=True,
    )
    identifier_scope: Mapped[str | None] = mapped_column(
        String(191),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(16), index=True)
    source_type: Mapped[str] = mapped_column(String(48))
    source_ref: Mapped[str] = mapped_column(String(255))
    observed_at: Mapped[datetime] = mapped_column(DateTime)
    transformation: Mapped[str] = mapped_column(String(96))
    transformation_version: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
    )


class GraphEntitySignalProjection(Base):
    """Profil de signaux rejouable, isolé des lecteurs Product Graph v1."""

    __tablename__ = "graph_entity_signal_projections"
    __table_args__ = (
        UniqueConstraint(
            "raw_source_record_id",
            "extractor_version",
            name="uq_graph_entity_signal_projection_version",
        ),
        UniqueConstraint(
            "projection_key",
            name="uq_graph_entity_signal_projection_key",
        ),
        CheckConstraint(
            "length(projection_key) = 64",
            name="ck_graph_entity_signal_projection_key_sha256",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    projection_key: Mapped[str] = mapped_column(String(64))
    raw_source_record_id: Mapped[int] = mapped_column(
        ForeignKey("raw_source_records.id"),
        index=True,
    )
    source_type: Mapped[str] = mapped_column(String(48))
    source_ref: Mapped[str] = mapped_column(String(255))
    observed_at: Mapped[datetime] = mapped_column(DateTime)
    extractor_version: Mapped[str] = mapped_column(String(64), index=True)
    profile_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
    )


class GraphEntityResolutionDecision(Base):
    """Décision Entity Resolution append-only et explicable en shadow."""

    __tablename__ = "graph_entity_resolution_decisions"
    __table_args__ = (
        UniqueConstraint(
            "raw_source_record_id",
            "resolver_version",
            "policy_version",
            name="uq_graph_entity_resolution_decision_version",
        ),
        UniqueConstraint(
            "decision_key",
            name="uq_graph_entity_resolution_decision_key",
        ),
        CheckConstraint(
            "length(decision_key) = 64",
            name="ck_graph_entity_resolution_decision_key_sha256",
        ),
        CheckConstraint(
            "resolution IN ('EXACT_VERIFIED', 'HIGH_CONFIDENCE', 'PROBABLE', "
            "'AMBIGUOUS', 'UNRESOLVED')",
            name="ck_graph_entity_resolution_state",
        ),
        CheckConstraint(
            "(resolution IN ('EXACT_VERIFIED', 'HIGH_CONFIDENCE') "
            "AND canonical_variant_id IS NOT NULL) OR "
            "(resolution IN ('PROBABLE', 'AMBIGUOUS', 'UNRESOLVED') "
            "AND canonical_variant_id IS NULL)",
            name="ck_graph_entity_resolution_canonical",
        ),
        Index(
            "ix_graph_entity_resolution_state",
            "resolution",
            "resolver_version",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    decision_key: Mapped[str] = mapped_column(String(64))
    raw_source_record_id: Mapped[int] = mapped_column(
        ForeignKey("raw_source_records.id"),
        index=True,
    )
    offer_id: Mapped[int] = mapped_column(ForeignKey("offers.id"), index=True)
    subject_type: Mapped[str] = mapped_column(String(32))
    resolution: Mapped[str] = mapped_column(String(24), index=True)
    canonical_variant_id: Mapped[int | None] = mapped_column(
        ForeignKey("graph_variants.id"),
        nullable=True,
        index=True,
    )
    candidate_ids_json: Mapped[list[int]] = mapped_column(JSON)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    reason_codes_json: Mapped[list[str]] = mapped_column(JSON)
    evidence_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    conflicts_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    extractor_version: Mapped[str] = mapped_column(String(64))
    resolver_version: Mapped[str] = mapped_column(String(64))
    policy_version: Mapped[str] = mapped_column(String(64))
    observed_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
    )
