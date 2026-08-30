"""Résolution conservative du Product/Variant Graph shadow.

La v1 n'effectue aucun rapprochement lexical. Une variante est résolue
uniquement lorsqu'une observation contient exactement un GTIN/EAN valide et
non contradictoire. Tout le reste reste ambigu, en quarantaine ou rejeté selon
la quantité de preuve disponible.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import select

from app.product_graph import models
from app.services.catalog_grouping import normalize_ean


RESOLVER_VERSION = "exact-gtin-shadow-v1"
_GLOBAL_IDENTIFIER_KEYS = ("gtin", "ean", "ean13", "upc")
_MAX_ATTRIBUTES = 32
_MAX_ATTRIBUTE_KEY_LENGTH = 64
_MAX_ATTRIBUTE_VALUE_LENGTH = 191
_MAX_CANDIDATES = 100


class ProductGraphResolutionError(ValueError):
    """Entrée hors contrat : le moteur doit échouer fermé."""


@dataclass(frozen=True)
class VariantResolution:
    variant_key: str | None
    attributes: Mapping[str, Any]
    resolution: str
    reason_code: str
    gtin: str | None

    def prediction(self) -> dict[str, Any]:
        return {
            "expected_variant": {
                "variant_key": self.variant_key,
                "attributes": dict(self.attributes),
                "resolution": self.resolution,
            }
        }


@dataclass(frozen=True)
class OfferAttachment:
    expected_variant_id: str | None
    eligibility: str
    reason_code: str

    def prediction(self) -> dict[str, Any]:
        return {
            "expected_variant_id": self.expected_variant_id,
            "eligibility": self.eligibility,
        }


@dataclass(frozen=True)
class EntityRelation:
    product_relation: str
    variant_relation: str

    def prediction(self) -> dict[str, str]:
        return {
            "product_relation": self.product_relation,
            "variant_relation": self.variant_relation,
        }


@dataclass(frozen=True)
class GraphCaptureResult:
    variant_created: bool
    identifier_created: bool
    evidence_created: bool
    link_created: bool
    resolution: str


def _mapping(value: Any, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ProductGraphResolutionError(f"{field_name} must be an object")
    return value


def _identifier_values(observation: Mapping[str, Any]) -> tuple[set[str], bool]:
    raw_identifiers = observation.get("identifiers")
    if raw_identifiers is None:
        return set(), False
    identifiers = _mapping(raw_identifiers, "identifiers")
    valid: set[str] = set()
    supplied = False
    for key in _GLOBAL_IDENTIFIER_KEYS:
        if key not in identifiers or identifiers[key] is None:
            continue
        raw = identifiers[key]
        if isinstance(raw, bool) or not isinstance(raw, (str, int)):
            raise ProductGraphResolutionError(f"identifier {key} is invalid")
        text = str(raw).strip()
        if not text:
            continue
        supplied = True
        normalized = normalize_ean(text)
        if normalized is not None:
            valid.add(normalized)
    return valid, supplied


def _attributes(observation: Mapping[str, Any]) -> dict[str, Any]:
    raw_attributes = observation.get("attributes")
    if raw_attributes is None:
        return {}
    attributes = _mapping(raw_attributes, "attributes")
    if len(attributes) > _MAX_ATTRIBUTES:
        raise ProductGraphResolutionError("attributes contains too many fields")
    checked: dict[str, Any] = {}
    for raw_key in sorted(attributes, key=lambda item: str(item)):
        if not isinstance(raw_key, str):
            raise ProductGraphResolutionError("attribute keys must be strings")
        key = raw_key.strip()
        if not key or len(key) > _MAX_ATTRIBUTE_KEY_LENGTH:
            raise ProductGraphResolutionError("attribute key is invalid")
        value = attributes[raw_key]
        if value is None:
            # Une valeur inconnue reste absente plutôt que de devenir un fait.
            continue
        if isinstance(value, str):
            value = value.strip()
            if not value:
                continue
            if len(value) > _MAX_ATTRIBUTE_VALUE_LENGTH:
                raise ProductGraphResolutionError("attribute value is too long")
        elif isinstance(value, bool) or isinstance(value, int):
            pass
        elif isinstance(value, float):
            if not math.isfinite(value):
                raise ProductGraphResolutionError("attribute value must be finite")
        else:
            raise ProductGraphResolutionError(
                "attribute values must be scalar JSON values"
            )
        checked[key] = value
    return checked


def resolve_variant_observation(observation: Mapping[str, Any]) -> VariantResolution:
    """Résout une observation sans marque, titre ou similarité implicite."""

    checked = _mapping(observation, "observation")
    attributes = _attributes(checked)
    gtins, supplied = _identifier_values(checked)
    if len(gtins) > 1:
        return VariantResolution(
            variant_key=None,
            attributes=attributes,
            resolution="ambiguous",
            reason_code="conflicting_gtin",
            gtin=None,
        )
    if not gtins:
        return VariantResolution(
            variant_key=None,
            attributes=attributes,
            resolution="insufficient_evidence",
            reason_code="invalid_gtin" if supplied else "missing_gtin",
            gtin=None,
        )
    gtin = next(iter(gtins))
    return VariantResolution(
        variant_key=f"gtin:{gtin}",
        attributes=attributes,
        resolution="resolved",
        reason_code="exact_gtin",
        gtin=gtin,
    )


def resolve_entity_pair(
    left: Mapping[str, Any],
    right: Mapping[str, Any],
) -> EntityRelation:
    """Prouve seulement l'identité exacte d'une même variante.

    Deux GTIN différents peuvent représenter deux variantes du même modèle :
    la v1 refuse donc d'en déduire deux produits différents sans preuve de
    modèle. Cette abstention protège à la fois des faux splits et faux merges.
    """

    left_resolution = resolve_variant_observation(left)
    right_resolution = resolve_variant_observation(right)
    if (
        left_resolution.resolution == "resolved"
        and right_resolution.resolution == "resolved"
        and left_resolution.variant_key == right_resolution.variant_key
    ):
        return EntityRelation(
            product_relation="same",
            variant_relation="same",
        )
    return EntityRelation(
        product_relation="ambiguous",
        variant_relation="ambiguous",
    )


def attach_offer_to_candidates(offer: Mapping[str, Any]) -> OfferAttachment:
    """Attache une offre à un roster explicite de variantes exactes.

    L'absence de roster est une entrée invalide : le moteur ne confond jamais
    « aucun candidat fourni » avec « aucun produit n'existe ».
    """

    checked = _mapping(offer, "offer")
    resolution = resolve_variant_observation(checked)
    raw_candidates = checked.get("variant_candidates")
    if not isinstance(raw_candidates, Sequence) or isinstance(
        raw_candidates, (str, bytes, bytearray)
    ):
        raise ProductGraphResolutionError("offer.variant_candidates must be an array")
    if not raw_candidates or len(raw_candidates) > _MAX_CANDIDATES:
        raise ProductGraphResolutionError(
            "offer.variant_candidates must contain 1-100 variants"
        )

    candidates: dict[str, str] = {}
    for index, raw_candidate in enumerate(raw_candidates):
        candidate = _mapping(raw_candidate, f"variant candidate {index}")
        variant_id = candidate.get("variant_id")
        if not isinstance(variant_id, str) or not variant_id.strip():
            raise ProductGraphResolutionError(
                f"variant candidate {index} variant_id is invalid"
            )
        variant_id = variant_id.strip()
        if variant_id in candidates:
            raise ProductGraphResolutionError("variant candidate ids must be unique")
        candidate_resolution = resolve_variant_observation(candidate)
        if candidate_resolution.resolution != "resolved" or candidate_resolution.gtin is None:
            raise ProductGraphResolutionError(
                f"variant candidate {index} lacks one exact GTIN"
            )
        candidates[variant_id] = candidate_resolution.gtin

    if resolution.resolution != "resolved" or resolution.gtin is None:
        return OfferAttachment(
            expected_variant_id=None,
            eligibility="quarantine",
            reason_code=resolution.reason_code,
        )
    matches = sorted(
        variant_id
        for variant_id, candidate_gtin in candidates.items()
        if candidate_gtin == resolution.gtin
    )
    if len(matches) == 1:
        return OfferAttachment(
            expected_variant_id=matches[0],
            eligibility="eligible",
            reason_code="exact_gtin",
        )
    if len(matches) > 1:
        return OfferAttachment(
            expected_variant_id=None,
            eligibility="quarantine",
            reason_code="conflicting_gtin",
        )
    return OfferAttachment(
        expected_variant_id=None,
        eligibility="reject",
        reason_code="candidate_mismatch",
    )


def project_awin_variant(row: Mapping[str, Any]) -> VariantResolution:
    """Projette uniquement le GTIN fort d'une ligne Awin vers le Graph."""

    checked = _mapping(row, "awin row")
    return resolve_variant_observation(
        {
            "identifiers": {"ean": checked.get("ean")},
            "attributes": {},
        }
    )


async def persist_awin_graph_projection(
    session,
    *,
    projection: VariantResolution,
    raw_source_record_id: int,
    offer_id: int,
    source_ref: str,
    observed_at: datetime,
) -> GraphCaptureResult:
    """Persiste une résolution shadow idempotente et sa provenance."""

    if raw_source_record_id <= 0 or offer_id <= 0:
        raise ProductGraphResolutionError("graph persistence ids must be positive")
    existing_link = await session.scalar(
        select(models.GraphOfferVariantLink).where(
            models.GraphOfferVariantLink.raw_source_record_id
            == raw_source_record_id,
            models.GraphOfferVariantLink.resolver_version == RESOLVER_VERSION,
        )
    )
    if existing_link is not None:
        return GraphCaptureResult(
            variant_created=False,
            identifier_created=False,
            evidence_created=False,
            link_created=False,
            resolution=existing_link.resolution,
        )

    variant = None
    identifier = None
    variant_created = False
    identifier_created = False
    evidence_created = False
    if projection.resolution == "resolved":
        if projection.gtin is None or projection.variant_key is None:
            raise ProductGraphResolutionError("resolved variant lacks a GTIN")
        identifier = await session.scalar(
            select(models.GraphIdentifier).where(
                models.GraphIdentifier.namespace == "gtin",
                models.GraphIdentifier.scope == "global",
                models.GraphIdentifier.normalized_value == projection.gtin,
            )
        )
        if identifier is not None:
            variant = await session.get(models.GraphVariant, identifier.variant_id)
            if variant is None or variant.variant_key != projection.variant_key:
                raise RuntimeError("graph identifier points to an invalid variant")
        else:
            variant = await session.scalar(
                select(models.GraphVariant).where(
                    models.GraphVariant.variant_key == projection.variant_key
                )
            )
            if variant is None:
                variant = models.GraphVariant(
                    variant_key=projection.variant_key,
                    model_id=None,
                    attributes_json=dict(projection.attributes),
                    status="shadow",
                    resolver_version=RESOLVER_VERSION,
                )
                session.add(variant)
                await session.flush()
                variant_created = True
            identifier = models.GraphIdentifier(
                variant_id=variant.id,
                namespace="gtin",
                scope="global",
                normalized_value=projection.gtin,
            )
            session.add(identifier)
            await session.flush()
            identifier_created = True

        existing_evidence = await session.scalar(
            select(models.GraphIdentifierEvidence.id).where(
                models.GraphIdentifierEvidence.identifier_id == identifier.id,
                models.GraphIdentifierEvidence.raw_source_record_id
                == raw_source_record_id,
            )
        )
        if existing_evidence is None:
            session.add(
                models.GraphIdentifierEvidence(
                    identifier_id=identifier.id,
                    raw_source_record_id=raw_source_record_id,
                    source_type="awin_feed",
                    source_ref=source_ref,
                    observed_at=observed_at,
                )
            )
            evidence_created = True

    link_resolution = (
        "resolved" if projection.resolution == "resolved" else "quarantine"
    )
    session.add(
        models.GraphOfferVariantLink(
            raw_source_record_id=raw_source_record_id,
            offer_id=offer_id,
            variant_id=variant.id if variant is not None else None,
            resolution=link_resolution,
            reason_code=projection.reason_code,
            resolver_version=RESOLVER_VERSION,
            observed_at=observed_at,
        )
    )
    await session.flush()
    return GraphCaptureResult(
        variant_created=variant_created,
        identifier_created=identifier_created,
        evidence_created=evidence_created,
        link_created=True,
        resolution=link_resolution,
    )
