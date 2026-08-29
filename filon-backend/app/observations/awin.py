"""Projection Awin déterministe vers RawSource, Observation et Quarantine."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Mapping

from sqlalchemy import func, select

from app.core.error_taxonomy import ProductErrorCode
from app.core.observability import traced_pipeline_stage
from app.observations import models
from app.services.catalog_grouping import normalize_ean
from app.services.source_normalization import parse_price, parse_tristate_bool


SOURCE_TYPE = "awin_feed"
SCHEMA_VERSION = "awin-create-a-feed-v1"
TRANSFORMATION = "awin_offer_observation"
TRANSFORMATION_VERSION = "v1"

_SENSITIVE_KEY_PARTS = (
    "api_key",
    "apikey",
    "authorization",
    "password",
    "secret",
    "token",
)


@dataclass(frozen=True)
class ProjectedObservation:
    field: str
    value: Any | None
    status: str
    confidence: float


@dataclass(frozen=True)
class ProjectedIssue:
    error_code: ProductErrorCode
    stage: str
    field: str | None
    rejected_value: Any | None
    reason: str
    details: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.error_code, ProductErrorCode):
            raise TypeError("ProjectedIssue.error_code doit être un ProductErrorCode")


@dataclass(frozen=True)
class AwinProjection:
    source_ref: str
    source_record_key: str
    subject_ref: str
    context: dict[str, Any]
    payload: dict[str, Any]
    payload_checksum: str
    replay_key: str
    observed_at: datetime
    transformation_version: str
    observations: tuple[ProjectedObservation, ...]
    issues: tuple[ProjectedIssue, ...]


@dataclass(frozen=True)
class CaptureResult:
    raw_source_record_id: int
    raw_created: bool
    observations_created: int
    quarantine_created: int


def _utc_naive(value: datetime | None) -> datetime:
    current = value or datetime.now(UTC)
    if current.tzinfo is not None:
        current = current.astimezone(UTC).replace(tzinfo=None)
    return current


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return str(value)


def _safe_payload(row: Mapping[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for raw_key in sorted(row, key=lambda key: str(key)):
        key = str(raw_key)
        lowered = key.lower()
        payload[key] = (
            "[REDACTED]"
            if any(part in lowered for part in _SENSITIVE_KEY_PARTS)
            else _json_safe(row[raw_key])
        )
    return payload


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _text(payload: Mapping[str, Any], field: str) -> str | None:
    value = payload.get(field)
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _observed_text(
    payload: Mapping[str, Any],
    source_field: str,
    observation_field: str,
) -> ProjectedObservation:
    value = _text(payload, source_field)
    return ProjectedObservation(
        field=observation_field,
        value=value,
        status="verified" if value is not None else "unknown",
        confidence=1.0 if value is not None else 0.0,
    )


def project_awin_row(
    row: Mapping[str, Any],
    *,
    feed_id: str,
    merchant_id: int,
    merchant_name: str | None = None,
    observed_at: datetime | None = None,
    transformation_version: str = TRANSFORMATION_VERSION,
) -> AwinProjection:
    """Produit une projection pure et rejouable d'une ligne Awin."""
    payload = _safe_payload(row)
    payload_checksum = _sha256(_canonical_json(payload))
    timestamp = _utc_naive(observed_at)
    source_ref = f"awin-feed:{feed_id}"
    external_id = _text(payload, "aw_product_id")
    source_record_key = f"{merchant_id}:{external_id or 'unknown-' + payload_checksum[:16]}"
    subject_ref = f"awin-offer:{source_record_key}"
    context = {
        "feed_id": str(feed_id),
        "merchant_id": merchant_id,
        "merchant_name": merchant_name,
    }
    replay_material = {
        "source_type": SOURCE_TYPE,
        "source_ref": source_ref,
        "source_record_key": source_record_key,
        "payload_checksum": payload_checksum,
        "observed_at": timestamp.isoformat(timespec="microseconds"),
    }
    replay_key = _sha256(_canonical_json(replay_material))

    observations: list[ProjectedObservation] = [
        _observed_text(payload, "aw_product_id", "external_id"),
        _observed_text(payload, "product_name", "name"),
        _observed_text(payload, "brand_name", "brand"),
        _observed_text(payload, "merchant_category", "merchant_category"),
        _observed_text(payload, "merchant_image_url", "image_url"),
        _observed_text(payload, "aw_deep_link", "deep_link"),
    ]
    issues: list[ProjectedIssue] = []

    if external_id is None:
        issues.append(
            ProjectedIssue(
                error_code=ProductErrorCode.SCHEMA_INVALID,
                stage="schema_validation",
                field="aw_product_id",
                rejected_value=None,
                reason="Identifiant produit source absent.",
            )
        )
    if _text(payload, "product_name") is None:
        issues.append(
            ProjectedIssue(
                error_code=ProductErrorCode.SCHEMA_INVALID,
                stage="schema_validation",
                field="product_name",
                rejected_value=None,
                reason="Nom produit source absent.",
            )
        )

    raw_ean = _text(payload, "ean")
    normalized_ean = normalize_ean(raw_ean)
    observations.append(
        ProjectedObservation(
            field="gtin",
            value=normalized_ean,
            status="verified" if normalized_ean is not None else "unknown",
            confidence=1.0 if normalized_ean is not None else 0.0,
        )
    )
    if raw_ean is not None and normalized_ean is None:
        issues.append(
            ProjectedIssue(
                error_code=ProductErrorCode.INVALID_IDENTIFIER,
                stage="identifier_validation",
                field="ean",
                rejected_value=raw_ean,
                reason="GTIN/EAN absent du jeu de longueurs valides ou checksum invalide.",
            )
        )

    raw_currency = _text(payload, "currency")
    currency = raw_currency.upper() if raw_currency else None
    currency_valid = bool(currency and len(currency) == 3 and currency.isalpha())
    observations.append(
        ProjectedObservation(
            field="currency",
            value=currency if currency_valid else None,
            status="verified" if currency_valid else "unknown",
            confidence=1.0 if currency_valid else 0.0,
        )
    )
    if raw_currency is not None and not currency_valid:
        issues.append(
            ProjectedIssue(
                error_code=ProductErrorCode.CURRENCY_MISMATCH,
                stage="currency_validation",
                field="currency",
                rejected_value=raw_currency,
                reason="Code devise source invalide.",
            )
        )

    raw_price = _text(payload, "search_price")
    amount = parse_price(raw_price)
    price_valid = amount is not None and amount > 0 and currency_valid
    observations.append(
        ProjectedObservation(
            field="price",
            value=(
                {"amount": f"{amount:.2f}", "currency": currency}
                if price_valid
                else None
            ),
            status="verified" if price_valid else "unknown",
            confidence=1.0 if price_valid else 0.0,
        )
    )
    if raw_price is not None and (amount is None or amount <= 0):
        issues.append(
            ProjectedIssue(
                error_code=ProductErrorCode.WRONG_PRICE,
                stage="price_validation",
                field="search_price",
                rejected_value=raw_price,
                reason="Prix source non analysable ou non positif.",
            )
        )
    elif amount is not None and amount > 0 and not currency_valid:
        issues.append(
            ProjectedIssue(
                error_code=ProductErrorCode.CURRENCY_MISMATCH,
                stage="price_validation",
                field="search_price",
                rejected_value=raw_price,
                reason="Prix inexploitable sans devise ISO explicite.",
                details={"parsed_amount": f"{amount:.2f}"},
            )
        )

    raw_stock = _text(payload, "in_stock")
    in_stock = parse_tristate_bool(raw_stock)
    observations.append(
        ProjectedObservation(
            field="availability",
            value=(
                "in_stock"
                if in_stock is True
                else "out_of_stock"
                if in_stock is False
                else None
            ),
            status="verified" if in_stock is not None else "unknown",
            confidence=1.0 if in_stock is not None else 0.0,
        )
    )
    if raw_stock is not None and in_stock is None:
        issues.append(
            ProjectedIssue(
                error_code=ProductErrorCode.WRONG_STOCK,
                stage="availability_validation",
                field="in_stock",
                rejected_value=raw_stock,
                reason="Disponibilité source non reconnue ; valeur conservée comme inconnue.",
            )
        )

    return AwinProjection(
        source_ref=source_ref,
        source_record_key=source_record_key,
        subject_ref=subject_ref,
        context=context,
        payload=payload,
        payload_checksum=payload_checksum,
        replay_key=replay_key,
        observed_at=timestamp,
        transformation_version=transformation_version,
        observations=tuple(observations),
        issues=tuple(issues),
    )


def _issue_key(projection: AwinProjection, issue: ProjectedIssue) -> str:
    return _sha256(
        _canonical_json(
            {
                "replay_key": projection.replay_key,
                "transformation_version": projection.transformation_version,
                "error_code": issue.error_code.value,
                "stage": issue.stage,
                "field": issue.field,
                "rejected_value": issue.rejected_value,
            }
        )
    )


async def persist_projection(
    session,
    projection: AwinProjection,
    *,
    offer_id: int | None,
    sync_run_id: int | None,
) -> CaptureResult:
    """Persiste une projection sans modifier un raw déjà capturé."""
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
            sync_run_id=sync_run_id,
            observed_at=projection.observed_at,
        )
        session.add(raw)
        await session.flush()

    existing_fields = set(
        (
            await session.execute(
                select(models.Observation.field).where(
                    models.Observation.raw_source_record_id == raw.id,
                    models.Observation.transformation_version
                    == projection.transformation_version,
                )
            )
        ).scalars()
    )
    observations_created = 0
    for observation in projection.observations:
        if observation.field in existing_fields:
            continue
        session.add(
            models.Observation(
                raw_source_record_id=raw.id,
                subject_type="merchant_offer",
                subject_ref=projection.subject_ref,
                offer_id=offer_id,
                field=observation.field,
                value_json=observation.value,
                status=observation.status,
                source_type=SOURCE_TYPE,
                source_ref=projection.source_ref,
                observed_at=projection.observed_at,
                transformation=TRANSFORMATION,
                transformation_version=projection.transformation_version,
                confidence=observation.confidence,
            )
        )
        observations_created += 1

    existing_issue_keys = set(
        (
            await session.execute(
                select(models.QuarantineRecord.issue_key).where(
                    models.QuarantineRecord.raw_source_record_id == raw.id,
                    models.QuarantineRecord.transformation_version
                    == projection.transformation_version,
                )
            )
        ).scalars()
    )
    quarantine_created = 0
    for issue in projection.issues:
        issue_key = _issue_key(projection, issue)
        if issue_key in existing_issue_keys:
            continue
        session.add(
            models.QuarantineRecord(
                raw_source_record_id=raw.id,
                issue_key=issue_key,
                error_code=issue.error_code.value,
                stage=issue.stage,
                field=issue.field,
                rejected_value_json=issue.rejected_value,
                reason=issue.reason,
                details_json=issue.details,
                transformation_version=projection.transformation_version,
                status="open",
                retry_count=0,
            )
        )
        quarantine_created += 1

    await session.flush()
    return CaptureResult(
        raw_source_record_id=raw.id,
        raw_created=raw_created,
        observations_created=observations_created,
        quarantine_created=quarantine_created,
    )


async def capture_awin_row(
    session,
    row: Mapping[str, Any],
    *,
    feed_id: str,
    merchant_id: int,
    merchant_name: str | None,
    offer_id: int | None,
    sync_run_id: int | None,
    observed_at: datetime | None = None,
) -> CaptureResult:
    projection = project_awin_row(
        row,
        feed_id=feed_id,
        merchant_id=merchant_id,
        merchant_name=merchant_name,
        observed_at=observed_at,
    )
    return await persist_projection(
        session,
        projection,
        offer_id=offer_id,
        sync_run_id=sync_run_id,
    )


@traced_pipeline_stage("observation")
async def replay_raw_source(
    session,
    raw_source_record_id: int,
    *,
    transformation_version: str = TRANSFORMATION_VERSION,
) -> CaptureResult:
    """Rejoue un raw avec sa date et son contexte d'origine."""
    raw = await session.get(models.RawSourceRecord, raw_source_record_id)
    if raw is None:
        raise LookupError(f"Raw source introuvable : {raw_source_record_id}")
    merchant_id = int(raw.context_json["merchant_id"])
    projection = project_awin_row(
        raw.payload_json,
        feed_id=str(raw.context_json["feed_id"]),
        merchant_id=merchant_id,
        merchant_name=raw.context_json.get("merchant_name"),
        observed_at=raw.observed_at,
        transformation_version=transformation_version,
    )
    if projection.payload_checksum != raw.payload_checksum:
        raise RuntimeError("Le payload raw a été modifié après sa capture.")
    if projection.replay_key != raw.replay_key:
        raise RuntimeError("Le contexte raw ne reproduit plus la clé de replay.")
    offer_id = await session.scalar(
        select(models.Observation.offer_id).where(
            models.Observation.raw_source_record_id == raw.id,
            models.Observation.offer_id.is_not(None),
        ).limit(1)
    )
    return await persist_projection(
        session,
        projection,
        offer_id=offer_id,
        sync_run_id=raw.sync_run_id,
    )


async def shadow_counts(session) -> dict[str, int]:
    """Compte les preuves shadow sans exposer leur contenu brut."""
    return {
        "raw_sources": int(
            await session.scalar(select(func.count()).select_from(models.RawSourceRecord))
            or 0
        ),
        "observations": int(
            await session.scalar(select(func.count()).select_from(models.Observation))
            or 0
        ),
        "quarantine_open": int(
            await session.scalar(
                select(func.count())
                .select_from(models.QuarantineRecord)
                .where(models.QuarantineRecord.status == "open")
            )
            or 0
        ),
    }
