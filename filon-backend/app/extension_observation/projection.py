"""Projection déterministe et persistance append-only d'une observation de page.

Ce module ne définit aucun transport HTTP. Il reçoit uniquement le contrat
déjà borné, refuse les champs ou URLs hors périmètre et projette vers le store
Observation existant. L'Entity Resolution reste propriétaire de l'identité.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping
from urllib.parse import urlsplit

from sqlalchemy import select

from app.observations import models
from app.services.catalog_grouping import normalize_ean


SOURCE_TYPE = "browser_extension_page"
SCHEMA_VERSION = "page-product-observation/v1"
TRANSFORMATION = "extension_product_observation"
TRANSFORMATION_VERSION = "v1"
MAX_CLOCK_SKEW = timedelta(minutes=5)
_ALLOWED_PAGE_FIELDS = {
    "url",
    "merchant",
    "title",
    "brand",
    "sku",
    "mpn",
    "gtin",
    "price",
    "availability",
    "variant",
    "json_ld",
}
_ALLOWED_VARIANT_FIELDS = {"model", "color", "size"}
_ALLOWED_JSON_LD_FIELDS = {
    "name",
    "brand",
    "sku",
    "mpn",
    "gtin",
    "gtin8",
    "gtin12",
    "gtin13",
    "gtin14",
    "model",
    "color",
    "size",
    "offers.price",
    "offers.priceCurrency",
    "offers.availability",
}
_ALLOWED_AVAILABILITY = {
    "in_stock",
    "out_of_stock",
    "preorder",
    "backorder",
    "unknown",
}


class ExtensionObservationError(ValueError):
    """Contrat impossible à projeter sans supposition."""


@dataclass(frozen=True)
class ProjectedField:
    field: str
    value: Any | None
    status: str
    confidence: float


@dataclass(frozen=True)
class PageObservationProjection:
    source_ref: str
    source_record_key: str
    subject_ref: str
    context: dict[str, Any]
    payload: dict[str, Any]
    payload_checksum: str
    replay_key: str
    observed_at: datetime
    observations: tuple[ProjectedField, ...]


@dataclass(frozen=True)
class CaptureResult:
    raw_source_record_id: int
    observation_id: str
    raw_created: bool
    observations_created: int


def _canonical(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ExtensionObservationError(f"{field} must be an object")
    return value


def _text(value: Any, field: str, *, minimum: int = 1, maximum: int) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ExtensionObservationError(f"{field} must be a string or null")
    normalized = " ".join(value.split())
    if not minimum <= len(normalized) <= maximum:
        raise ExtensionObservationError(f"{field} length is invalid")
    return normalized


def _timestamp(value: Any, *, received_at: datetime) -> datetime:
    if not isinstance(value, str):
        raise ExtensionObservationError("observed_at must be a date-time string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ExtensionObservationError("observed_at must be a date-time string") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ExtensionObservationError("observed_at must include an offset")
    observed = parsed.astimezone(UTC)
    reference = received_at.astimezone(UTC) if received_at.tzinfo else received_at.replace(tzinfo=UTC)
    if observed > reference + MAX_CLOCK_SKEW:
        raise ExtensionObservationError("observed_at is in the future")
    return observed.replace(tzinfo=None)


def _url(value: Any) -> tuple[str, str]:
    if not isinstance(value, str) or not value or len(value) > 2048:
        raise ExtensionObservationError("page.url is invalid")
    parsed = urlsplit(value)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise ExtensionObservationError("page.url must be an HTTPS origin and path")
    canonical = f"https://{parsed.netloc.lower()}{parsed.path or '/'}"
    if canonical != value:
        raise ExtensionObservationError("page.url must already be canonical")
    return canonical, parsed.hostname.lower()


def _price(value: Any) -> dict[str, str] | None:
    if value is None:
        return None
    price = _mapping(value, "page.price")
    if set(price) != {"amount", "currency"}:
        raise ExtensionObservationError("page.price fields are invalid")
    amount_raw = price["amount"]
    currency = price["currency"]
    if not isinstance(amount_raw, str) or not isinstance(currency, str):
        raise ExtensionObservationError("page.price amount and currency must be strings")
    try:
        amount = Decimal(amount_raw)
    except InvalidOperation as exc:
        raise ExtensionObservationError("page.price amount is invalid") from exc
    if not amount.is_finite() or amount <= 0 or amount.as_tuple().exponent < -4:
        raise ExtensionObservationError("page.price amount is invalid")
    if len(currency) != 3 or not currency.isascii() or not currency.isalpha() or currency != currency.upper():
        raise ExtensionObservationError("page.price currency is invalid")
    return {"amount": amount_raw, "currency": currency}


def _field(name: str, value: Any | None) -> ProjectedField:
    known = value is not None
    return ProjectedField(
        field=name,
        value=value if known else None,
        status="verified" if known else "unknown",
        confidence=1.0 if known else 0.0,
    )


def project_page_observation(
    payload: Mapping[str, Any],
    *,
    received_at: datetime | None = None,
) -> PageObservationProjection:
    """Valide puis projette un payload v1 sans conserver de champ inattendu."""

    checked = _mapping(payload, "payload")
    if set(checked) != {"contract_version", "capture_mode", "page", "observed_at"}:
        raise ExtensionObservationError("payload fields are invalid")
    if checked["contract_version"] != "1.0.0":
        raise ExtensionObservationError("contract_version is unsupported")
    if checked["capture_mode"] != "explicit_user_action":
        raise ExtensionObservationError("capture_mode must be explicit_user_action")

    page = _mapping(checked["page"], "page")
    if set(page) != _ALLOWED_PAGE_FIELDS:
        raise ExtensionObservationError("page fields are invalid")
    url, host = _url(page["url"])
    merchant = _text(page["merchant"], "page.merchant", maximum=253)
    if merchant is None or merchant.lower() != host:
        raise ExtensionObservationError("page.merchant must match page.url")
    merchant = merchant.lower()
    title = _text(page["title"], "page.title", minimum=3, maximum=300)
    assert title is not None
    brand = _text(page["brand"], "page.brand", maximum=191)
    sku = _text(page["sku"], "page.sku", maximum=191)
    mpn = _text(page["mpn"], "page.mpn", maximum=191)

    supplied_gtin = page["gtin"]
    if supplied_gtin is not None and not isinstance(supplied_gtin, str):
        raise ExtensionObservationError("page.gtin must be a string or null")
    gtin = normalize_ean(supplied_gtin)
    if supplied_gtin is not None and gtin is None:
        raise ExtensionObservationError("page.gtin checksum is invalid")

    price = _price(page["price"])
    availability = page["availability"]
    if availability not in _ALLOWED_AVAILABILITY:
        raise ExtensionObservationError("page.availability is invalid")

    variant = _mapping(page["variant"], "page.variant")
    if set(variant) != _ALLOWED_VARIANT_FIELDS:
        raise ExtensionObservationError("page.variant fields are invalid")
    model = _text(variant["model"], "page.variant.model", maximum=191)
    color = _text(variant["color"], "page.variant.color", maximum=128)
    size = _text(variant["size"], "page.variant.size", maximum=128)

    json_ld = _mapping(page["json_ld"], "page.json_ld")
    if set(json_ld) != {"present", "source_fields"}:
        raise ExtensionObservationError("page.json_ld fields are invalid")
    if not isinstance(json_ld["present"], bool):
        raise ExtensionObservationError("page.json_ld.present must be boolean")
    source_fields = json_ld["source_fields"]
    if (
        not isinstance(source_fields, list)
        or len(source_fields) > 16
        or len(source_fields) != len(set(source_fields))
        or any(not isinstance(item, str) or not item for item in source_fields)
        or any(item not in _ALLOWED_JSON_LD_FIELDS for item in source_fields)
    ):
        raise ExtensionObservationError("page.json_ld.source_fields is invalid")

    now = received_at or datetime.now(UTC)
    observed_at = _timestamp(checked["observed_at"], received_at=now)
    safe_page = {
        "url": url,
        "merchant": merchant,
        "title": title,
        "brand": brand,
        "sku": sku,
        "mpn": mpn,
        "gtin": gtin,
        "price": price,
        "availability": availability,
        "variant": {"model": model, "color": color, "size": size},
        "json_ld": {
            "present": json_ld["present"],
            "source_fields": sorted(source_fields),
        },
    }
    safe_payload = {
        "contract_version": "1.0.0",
        "capture_mode": "explicit_user_action",
        "page": safe_page,
        "observed_at": observed_at.replace(tzinfo=UTC).isoformat().replace("+00:00", "Z"),
    }
    payload_checksum = _digest(safe_payload)
    source_ref = f"extension:{merchant}"
    source_record_key = _digest({"url": url, "identifier": gtin or mpn or sku or title})
    subject_ref = f"merchant-page:{source_record_key}"
    replay_key = _digest(
        {
            "source_type": SOURCE_TYPE,
            "source_ref": source_ref,
            "source_record_key": source_record_key,
            "payload_checksum": payload_checksum,
            "observed_at": safe_payload["observed_at"],
        }
    )
    observations = (
        _field("page_url", url),
        _field("merchant", merchant),
        _field("name", title),
        _field("brand", brand),
        _field("sku", sku),
        _field("mpn", mpn),
        _field("gtin", gtin),
        _field("price", price),
        _field("availability", availability if availability != "unknown" else None),
        _field("model", model),
        _field("color", color),
        _field("size", size),
    )
    if any(not math.isfinite(item.confidence) for item in observations):
        raise ExtensionObservationError("observation confidence is invalid")
    return PageObservationProjection(
        source_ref=source_ref,
        source_record_key=source_record_key,
        subject_ref=subject_ref,
        context={"merchant": merchant, "capture_mode": "explicit_user_action"},
        payload=safe_payload,
        payload_checksum=payload_checksum,
        replay_key=replay_key,
        observed_at=observed_at,
        observations=observations,
    )


async def persist_page_observation(session, projection: PageObservationProjection) -> CaptureResult:
    """Persiste une preuve append-only ; un replay identique ne duplique rien."""

    raw = await session.scalar(
        select(models.RawSourceRecord).where(
            models.RawSourceRecord.replay_key == projection.replay_key
        )
    )
    raw_created = raw is None
    if raw is None:
        raw = models.RawSourceRecord(
            source_type=SOURCE_TYPE,
            source_ref=projection.source_ref,
            source_record_key=projection.source_record_key,
            schema_version=SCHEMA_VERSION,
            context_json=projection.context,
            payload_json=projection.payload,
            payload_checksum=projection.payload_checksum,
            replay_key=projection.replay_key,
            sync_run_id=None,
            observed_at=projection.observed_at,
        )
        session.add(raw)
        await session.flush()

    existing = set(
        (
            await session.execute(
                select(models.Observation.field).where(
                    models.Observation.raw_source_record_id == raw.id,
                    models.Observation.transformation_version == TRANSFORMATION_VERSION,
                )
            )
        ).scalars()
    )
    created = 0
    for item in projection.observations:
        if item.field in existing:
            continue
        session.add(
            models.Observation(
                raw_source_record_id=raw.id,
                subject_type="merchant_page_product",
                subject_ref=projection.subject_ref,
                offer_id=None,
                field=item.field,
                value_json=item.value,
                status=item.status,
                source_type=SOURCE_TYPE,
                source_ref=projection.source_ref,
                observed_at=projection.observed_at,
                transformation=TRANSFORMATION,
                transformation_version=TRANSFORMATION_VERSION,
                confidence=item.confidence,
            )
        )
        created += 1
    await session.flush()
    return CaptureResult(
        raw_source_record_id=raw.id,
        observation_id=projection.replay_key,
        raw_created=raw_created,
        observations_created=created,
    )
