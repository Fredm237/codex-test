"""Assertions Product Identity v1, sourcées et sans promotion implicite."""

from __future__ import annotations

import hashlib
import json
import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import select

from app.product_graph import models
from app.product_graph.resolution import ProductGraphResolutionError
from app.services.catalog_grouping import normalize_ean


CONTRACT_VERSION = "1.0.0"
TRANSFORMATION = "awin_product_identity"
TRANSFORMATION_VERSION = "v1"
SOURCE_TYPE = "awin_feed"


@dataclass(frozen=True)
class IdentityAssertionProjection:
    subject_type: str
    field: str
    value: Any
    normalized_value: str | None
    identifier_namespace: str | None
    identifier_scope: str | None
    status: str


@dataclass(frozen=True)
class IdentityAssertionCapture:
    created: int
    existing: int
    observed: int
    validated: int
    quarantined: int


def _text(value: Any, field: str, *, maximum: int = 191) -> str | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise ProductGraphResolutionError(f"{field} must be textual")
    text = str(value).strip()
    if not text:
        return None
    if len(text) > maximum:
        raise ProductGraphResolutionError(f"{field} is too long")
    return text


def _normalized_label(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def project_awin_identity_assertions(
    row: Mapping[str, Any],
    *,
    merchant_id: int,
) -> tuple[IdentityAssertionProjection, ...]:
    """Projette seulement les faits structurés présents dans une ligne Awin.

    La marque reste `observed` : sa forme normalisée facilite l'audit mais ne
    crée jamais une GraphBrand. Les identifiants sont validés dans leur scope.
    Une valeur absente ne produit aucune assertion.
    """

    if not isinstance(row, Mapping):
        raise ProductGraphResolutionError("awin row must be an object")
    if isinstance(merchant_id, bool) or not isinstance(merchant_id, int) or merchant_id <= 0:
        raise ProductGraphResolutionError("merchant_id must be positive")

    projections: list[IdentityAssertionProjection] = []
    brand = _text(row.get("brand_name"), "brand_name")
    if brand is not None:
        projections.append(
            IdentityAssertionProjection(
                subject_type="brand",
                field="canonical_name_candidate",
                value=brand,
                normalized_value=_normalized_label(brand),
                identifier_namespace=None,
                identifier_scope=None,
                status="observed",
            )
        )

    raw_ean = _text(row.get("ean"), "ean")
    if raw_ean is not None:
        gtin = normalize_ean(raw_ean)
        projections.append(
            IdentityAssertionProjection(
                subject_type="variant",
                field="identifier",
                value=raw_ean,
                normalized_value=gtin,
                identifier_namespace="gtin",
                identifier_scope="global",
                status="validated" if gtin is not None else "quarantine",
            )
        )

    merchant_sku = _text(row.get("aw_product_id"), "aw_product_id")
    if merchant_sku is not None:
        projections.append(
            IdentityAssertionProjection(
                subject_type="variant",
                field="identifier",
                value=merchant_sku,
                normalized_value=merchant_sku,
                identifier_namespace="merchant_sku",
                identifier_scope=f"merchant:{merchant_id}",
                status="validated",
            )
        )
    return tuple(projections)


def _assertion_key(
    projection: IdentityAssertionProjection,
    *,
    raw_source_record_id: int,
    offer_id: int,
) -> str:
    material = {
        "contract_version": CONTRACT_VERSION,
        "raw_source_record_id": raw_source_record_id,
        "offer_id": offer_id,
        "subject_type": projection.subject_type,
        "field": projection.field,
        "value": projection.value,
        "normalized_value": projection.normalized_value,
        "identifier_namespace": projection.identifier_namespace,
        "identifier_scope": projection.identifier_scope,
        "status": projection.status,
        "transformation_version": TRANSFORMATION_VERSION,
    }
    encoded = json.dumps(
        material,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


async def persist_awin_identity_assertions(
    session,
    *,
    projections: Sequence[IdentityAssertionProjection],
    raw_source_record_id: int,
    offer_id: int,
    source_ref: str,
    observed_at: datetime,
) -> IdentityAssertionCapture:
    """Persiste les assertions de façon idempotente et append-only."""

    if raw_source_record_id <= 0 or offer_id <= 0:
        raise ProductGraphResolutionError("identity persistence ids must be positive")
    if not isinstance(source_ref, str) or not source_ref.strip():
        raise ProductGraphResolutionError("source_ref must be non-empty")
    if not isinstance(observed_at, datetime):
        raise ProductGraphResolutionError("observed_at must be a datetime")

    created = existing = observed = validated = quarantined = 0
    for projection in projections:
        key = _assertion_key(
            projection,
            raw_source_record_id=raw_source_record_id,
            offer_id=offer_id,
        )
        present = await session.scalar(
            select(models.GraphIdentityAssertion.id).where(
                models.GraphIdentityAssertion.assertion_key == key
            )
        )
        if present is not None:
            existing += 1
            continue
        session.add(
            models.GraphIdentityAssertion(
                assertion_key=key,
                raw_source_record_id=raw_source_record_id,
                offer_id=offer_id,
                subject_type=projection.subject_type,
                subject_ref=f"offer:{offer_id}",
                field=projection.field,
                value_json=projection.value,
                normalized_value=projection.normalized_value,
                identifier_namespace=projection.identifier_namespace,
                identifier_scope=projection.identifier_scope,
                status=projection.status,
                source_type=SOURCE_TYPE,
                source_ref=source_ref.strip(),
                observed_at=observed_at,
                transformation=TRANSFORMATION,
                transformation_version=TRANSFORMATION_VERSION,
            )
        )
        created += 1
        observed += int(projection.status == "observed")
        validated += int(projection.status == "validated")
        quarantined += int(projection.status == "quarantine")
    await session.flush()
    return IdentityAssertionCapture(
        created=created,
        existing=existing,
        observed=observed,
        validated=validated,
        quarantined=quarantined,
    )
