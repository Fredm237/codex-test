"""Catalog Quality Funnel descriptif, interne et sans score synthétique.

La classification est qualifiée par les invariants et régressions du Quality
Lab autonome, mais reste explicitement provisoire sur les données observées :
la présence de champs ne prouve pas une exactitude humaine indépendante. Le
funnel continue jusqu'aux véritables limites techniques sans inventer les
coûts rendus, la calibration ou une confiance subjective.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from collections import defaultdict
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any, Iterable

from sqlalchemy import select

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.db import models as core_models
from app.db import session as db
from app.evidence_engine.models import DecisionEligibilityRecord
from app.evidence_engine.policy import POLICY_VERSION as EVIDENCE_POLICY_VERSION
from app.observations.models import RawSourceRecord
from app.offer_graph.models import GraphOfferObservation
from app.offer_graph.projection import PROJECTION_VERSION as OFFER_PROJECTION_VERSION
from app.product_graph.models import (
    GraphOfferVariantLink,
    GraphProductModel,
    GraphVariant,
)
from app.product_graph.resolution import RESOLVER_VERSION


log = get_logger("catalog_quality.funnel")
POLICY_VERSION = "catalog-quality-funnel-autonomous-v2"
MAX_FUNNEL_ROWS = 10_000
OFFER_FRESHNESS = timedelta(hours=72)
HISTORY_WINDOW = timedelta(days=30)

FUNNEL_STAGES = (
    "RAW_OFFERS",
    "ACTIVE_OFFERS",
    "VALID_PRICE",
    "VALID_MERCHANT",
    "CORRECTLY_CLASSIFIED",
    "RESOLVED_PRODUCT",
    "RESOLVED_VARIANT",
    "MULTI_MERCHANT_COMPARABLE",
    "30D_HISTORY",
    "COMPLETE_LANDED_COST",
    "DECISION_ELIGIBLE",
    "HIGH_CONFIDENCE_DECISION",
)


@dataclass(frozen=True)
class FunnelStage:
    code: str
    status: str
    qualified_count: int | None
    denominator_count: int | None
    reason_code: str


@dataclass(frozen=True)
class TechnicalSignal:
    code: str
    status: str
    observed_count: int | None
    denominator_count: int | None
    reason_code: str


@dataclass(frozen=True)
class CatalogQualityFunnelReport:
    policy_version: str
    evaluated_at: str
    after_raw_id: int
    limit: int
    last_raw_source_id: int | None
    source_unit: str
    raw_source_records: int
    offer_observations: int
    current_offer_observations: int
    stages: tuple[FunnelStage, ...]
    technical_signals: tuple[TechnicalSignal, ...]
    launch_gate_eligible: bool
    report_fingerprint: str


def parse_evaluated_at(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("evaluated_at must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("evaluated_at must include an explicit UTC offset")
    return parsed.astimezone(UTC).replace(tzinfo=None)


def _window(after_raw_id: int, limit: int) -> tuple[int, int]:
    if isinstance(after_raw_id, bool) or not isinstance(after_raw_id, int):
        raise ValueError("after_raw_id must be a non-negative integer")
    if after_raw_id < 0:
        raise ValueError("after_raw_id must be a non-negative integer")
    if isinstance(limit, bool) or not isinstance(limit, int):
        raise ValueError(f"limit must be between 1 and {MAX_FUNNEL_ROWS}")
    if not 1 <= limit <= MAX_FUNNEL_ROWS:
        raise ValueError(f"limit must be between 1 and {MAX_FUNNEL_ROWS}")
    return after_raw_id, limit


def _ensure_utc_naive(value: datetime) -> None:
    if not isinstance(value, datetime) or value.tzinfo is not None:
        raise ValueError("evaluated_at must be UTC-naive internally")


def _latest_by(
    rows: Iterable[Any],
    *,
    key,
    order,
) -> dict[int, Any]:
    latest: dict[int, Any] = {}
    for row in rows:
        item_key = key(row)
        current = latest.get(item_key)
        if current is None or order(row) > order(current):
            latest[item_key] = row
    return latest


def _fresh(observation: GraphOfferObservation, evaluated_at: datetime) -> bool:
    return (
        observation.observed_at <= evaluated_at
        and evaluated_at <= observation.observed_at + OFFER_FRESHNESS
    )


def _valid_currency(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 3
        and value.isascii()
        and value.isalpha()
        and value == value.upper()
    )


def _valid_price(observation: GraphOfferObservation) -> bool:
    if (
        observation.price_state != "known"
        or observation.price_amount is None
        or not _valid_currency(observation.price_currency)
    ):
        return False
    try:
        return Decimal(observation.price_amount) > 0
    except (ArithmeticError, TypeError, ValueError):
        return False


def _canonical_payload(report: CatalogQualityFunnelReport) -> dict[str, Any]:
    payload = asdict(report)
    payload.pop("report_fingerprint", None)
    return payload


def _fingerprint(report: CatalogQualityFunnelReport) -> str:
    payload = json.dumps(
        _canonical_payload(report),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    digest = hashlib.sha256(
        b"filon.catalog-quality-funnel.report.v1\0" + payload
    ).hexdigest()
    return f"sha256:{digest}"


async def build_catalog_quality_funnel(
    session,
    *,
    evaluated_at: datetime,
    after_raw_id: int = 0,
    limit: int = 1_000,
) -> CatalogQualityFunnelReport:
    """Mesure un lot borné sans écrire ni déduire une correction humaine."""

    _ensure_utc_naive(evaluated_at)
    after_raw_id, limit = _window(after_raw_id, limit)
    raws = (
        (
            await session.execute(
                select(RawSourceRecord)
                .where(
                    RawSourceRecord.source_type == "awin_feed",
                    RawSourceRecord.id > after_raw_id,
                )
                .order_by(RawSourceRecord.id)
                .limit(limit)
            )
        )
        .scalars()
        .all()
    )
    raw_ids = [raw.id for raw in raws]
    observations: list[GraphOfferObservation] = []
    if raw_ids:
        observations = (
            (
                await session.execute(
                    select(GraphOfferObservation)
                    .where(
                        GraphOfferObservation.raw_source_record_id.in_(raw_ids),
                        GraphOfferObservation.projection_version
                        == OFFER_PROJECTION_VERSION,
                    )
                    .order_by(
                        GraphOfferObservation.offer_id,
                        GraphOfferObservation.observed_at,
                        GraphOfferObservation.id,
                    )
                )
            )
            .scalars()
            .all()
        )
    current = _latest_by(
        observations,
        key=lambda row: row.offer_id,
        order=lambda row: (row.observed_at, row.raw_source_record_id, row.id),
    )
    current_rows = list(current.values())
    offer_ids = sorted(current)

    offers: dict[int, core_models.Offer] = {}
    merchants: dict[int, core_models.Merchant] = {}
    if offer_ids:
        offer_rows = (
            (
                await session.execute(
                    select(core_models.Offer).where(core_models.Offer.id.in_(offer_ids))
                )
            )
            .scalars()
            .all()
        )
        offers = {offer.id: offer for offer in offer_rows}
        merchant_ids = sorted({offer.merchant_id for offer in offer_rows})
        if merchant_ids:
            merchant_rows = (
                (
                    await session.execute(
                        select(core_models.Merchant).where(
                            core_models.Merchant.id.in_(merchant_ids)
                        )
                    )
                )
                .scalars()
                .all()
            )
            merchants = {merchant.id: merchant for merchant in merchant_rows}

    active = {
        row.id: row
        for row in current_rows
        if _fresh(row, evaluated_at) and row.availability == "in_stock"
    }
    valid_price = {row_id: row for row_id, row in active.items() if _valid_price(row)}
    valid_merchant: dict[int, GraphOfferObservation] = {}
    for row_id, row in valid_price.items():
        offer = offers.get(row.offer_id)
        merchant = merchants.get(offer.merchant_id) if offer is not None else None
        if (
            offer is not None
            and merchant is not None
            and merchant.joined is True
            and row.merchant_url_state == "known"
            and isinstance(row.merchant_url, str)
            and bool(row.merchant_url)
        ):
            valid_merchant[row_id] = row

    link_ids = sorted(
        {
            row.offer_variant_link_id
            for row in valid_merchant.values()
            if row.offer_variant_link_id is not None
        }
    )
    links: dict[int, GraphOfferVariantLink] = {}
    variants: dict[int, GraphVariant] = {}
    models: dict[int, GraphProductModel] = {}
    if link_ids:
        link_rows = (
            (
                await session.execute(
                    select(GraphOfferVariantLink).where(
                        GraphOfferVariantLink.id.in_(link_ids)
                    )
                )
            )
            .scalars()
            .all()
        )
        links = {link.id: link for link in link_rows}
        variant_ids = sorted(
            {link.variant_id for link in link_rows if link.variant_id is not None}
        )
        if variant_ids:
            variant_rows = (
                (
                    await session.execute(
                        select(GraphVariant).where(GraphVariant.id.in_(variant_ids))
                    )
                )
                .scalars()
                .all()
            )
            variants = {variant.id: variant for variant in variant_rows}
            model_ids = sorted(
                {
                    variant.model_id
                    for variant in variant_rows
                    if variant.model_id is not None
                }
            )
            if model_ids:
                model_rows = (
                    (
                        await session.execute(
                            select(GraphProductModel).where(
                                GraphProductModel.id.in_(model_ids)
                            )
                        )
                    )
                    .scalars()
                    .all()
                )
                models = {model.id: model for model in model_rows}

    resolved_variant: dict[int, tuple[GraphOfferObservation, int]] = {}
    resolved_product: set[int] = set()
    for row_id, row in valid_merchant.items():
        link = links.get(row.offer_variant_link_id)
        if (
            link is None
            or link.resolution != "resolved"
            or link.variant_id is None
            or link.raw_source_record_id != row.raw_source_record_id
            or link.offer_id != row.offer_id
            or link.resolver_version != RESOLVER_VERSION
            or link.variant_id not in variants
        ):
            continue
        resolved_variant[row_id] = (row, link.variant_id)
        variant = variants[link.variant_id]
        if variant.model_id is not None and variant.model_id in models:
            resolved_product.add(row_id)

    comparable_groups: dict[tuple[int, str], set[int]] = defaultdict(set)
    for row, variant_id in resolved_variant.values():
        offer = offers[row.offer_id]
        assert row.price_currency is not None
        comparable_groups[(variant_id, row.price_currency)].add(offer.merchant_id)
    comparable_keys = {
        key for key, merchant_ids in comparable_groups.items() if len(merchant_ids) >= 2
    }
    multi_merchant = {
        row_id
        for row_id, (row, variant_id) in resolved_variant.items()
        if (variant_id, row.price_currency) in comparable_keys
    }

    history_30d: set[int] = set()
    if valid_merchant:
        threshold = evaluated_at - HISTORY_WINDOW
        history_rows = (
            (
                await session.execute(
                    select(
                        core_models.PriceSnapshot.offer_id,
                        core_models.PriceSnapshot.currency,
                    )
                    .where(
                        core_models.PriceSnapshot.offer_id.in_(
                            sorted(row.offer_id for row in valid_merchant.values())
                        ),
                        core_models.PriceSnapshot.captured_at <= threshold,
                        core_models.PriceSnapshot.price > 0,
                        core_models.PriceSnapshot.currency.in_(
                            sorted(
                                {
                                    row.price_currency
                                    for row in valid_merchant.values()
                                    if row.price_currency is not None
                                }
                            )
                        ),
                    )
                    .distinct()
                )
            )
            .all()
        )
        historical_pairs = {
            (offer_id, currency) for offer_id, currency in history_rows
        }
        for row_id, row in valid_merchant.items():
            if (row.offer_id, row.price_currency) in historical_pairs:
                history_30d.add(row_id)

    classification_present = {
        row_id
        for row_id, row in valid_merchant.items()
        if (offer := offers.get(row.offer_id)) is not None
        and bool(offer.filon_category)
        and bool(offer.filon_subcategory)
        and bool(offer.offer_kind)
    }
    resolved_product_qualified = resolved_product & classification_present
    resolved_variant_qualified = (
        set(resolved_variant) & resolved_product_qualified
    )
    multi_merchant_qualified = multi_merchant & resolved_variant_qualified
    history_qualified = history_30d & multi_merchant_qualified

    decision_eligible: set[int] = set()
    if valid_merchant:
        decision_rows = (
            (
                await session.execute(
                    select(DecisionEligibilityRecord).where(
                        DecisionEligibilityRecord.offer_observation_id.in_(
                            sorted(valid_merchant)
                        ),
                        DecisionEligibilityRecord.evaluated_at <= evaluated_at,
                        DecisionEligibilityRecord.policy_version
                        == EVIDENCE_POLICY_VERSION,
                    )
                )
            )
            .scalars()
            .all()
        )
        latest_decisions = _latest_by(
            decision_rows,
            key=lambda row: row.offer_observation_id,
            order=lambda row: (row.evaluated_at, row.id),
        )
        for observation_id, decision in latest_decisions.items():
            observation = valid_merchant[observation_id]
            if (
                decision.decision_eligible is True
                and decision.highest_stage == "DECISION_ELIGIBLE"
                and decision.raw_source_record_id == observation.raw_source_record_id
                and decision.offer_id == observation.offer_id
            ):
                decision_eligible.add(observation_id)

    stages = (
        FunnelStage("RAW_OFFERS", "measured", len(raws), len(raws), "bounded_raw_window"),
        FunnelStage(
            "ACTIVE_OFFERS",
            "measured",
            len(active),
            len(raws),
            "latest_fresh_in_stock_observation",
        ),
        FunnelStage(
            "VALID_PRICE",
            "measured",
            len(valid_price),
            len(active),
            "positive_decimal_and_explicit_currency",
        ),
        FunnelStage(
            "VALID_MERCHANT",
            "measured",
            len(valid_merchant),
            len(valid_price),
            "joined_merchant_and_public_link",
        ),
        FunnelStage(
            "CORRECTLY_CLASSIFIED",
            "provisional",
            len(classification_present),
            len(valid_merchant),
            "autonomous_regressions_passed_fields_present_not_independently_validated",
        ),
        FunnelStage(
            "RESOLVED_PRODUCT",
            "measured",
            len(resolved_product_qualified),
            len(classification_present),
            "exact_identifier_graph_model_link",
        ),
        FunnelStage(
            "RESOLVED_VARIANT",
            "measured",
            len(resolved_variant_qualified),
            len(resolved_product_qualified),
            "exact_gtin_variant_link",
        ),
        FunnelStage(
            "MULTI_MERCHANT_COMPARABLE",
            "measured",
            len(multi_merchant_qualified),
            len(resolved_variant_qualified),
            "same_variant_and_currency_two_joined_merchants",
        ),
        FunnelStage(
            "30D_HISTORY",
            "measured",
            len(history_qualified),
            len(multi_merchant_qualified),
            "same_currency_history_spans_thirty_days",
        ),
        FunnelStage(
            "COMPLETE_LANDED_COST",
            "not_supported",
            None,
            len(history_qualified),
            "shipping_tax_and_destination_not_modeled",
        ),
        FunnelStage(
            "DECISION_ELIGIBLE",
            "not_supported",
            None,
            None,
            "complete_landed_cost_unavailable",
        ),
        FunnelStage(
            "HIGH_CONFIDENCE_DECISION",
            "not_supported",
            None,
            None,
            "confidence_not_independently_calibrated",
        ),
    )
    technical_signals = (
        TechnicalSignal(
            "OFFER_GRAPH_OBSERVED",
            "technical_signal_only",
            len(observations),
            len(raws),
            "shadow_projection_presence_not_quality",
        ),
        TechnicalSignal(
            "CURRENT_OFFER_OBSERVATIONS",
            "technical_signal_only",
            len(current_rows),
            len(raws),
            "latest_observation_per_offer_in_window",
        ),
        TechnicalSignal(
            "CLASSIFICATION_FIELDS_PRESENT",
            "technical_signal_only",
            len(classification_present),
            len(valid_merchant),
            "presence_is_not_correctness",
        ),
        TechnicalSignal(
            "RESOLVED_PRODUCT",
            "technical_signal_only",
            len(resolved_product),
            len(valid_merchant),
            "graph_model_link_before_funnel_cascade",
        ),
        TechnicalSignal(
            "RESOLVED_VARIANT",
            "technical_signal_only",
            len(resolved_variant),
            len(valid_merchant),
            "exact_graph_link_before_funnel_cascade",
        ),
        TechnicalSignal(
            "MULTI_MERCHANT_COMPARABLE",
            "technical_signal_only",
            len(multi_merchant),
            len(valid_merchant),
            "same_variant_currency_two_joined_merchants",
        ),
        TechnicalSignal(
            "30D_HISTORY",
            "technical_signal_only",
            len(history_30d),
            len(valid_merchant),
            "same_currency_observation_spans_thirty_days",
        ),
        TechnicalSignal(
            "COMPLETE_LANDED_COST",
            "not_supported",
            None,
            len(valid_merchant),
            "shipping_tax_and_destination_not_modeled",
        ),
        TechnicalSignal(
            "DECISION_ELIGIBLE",
            "technical_signal_only",
            len(decision_eligible),
            len(valid_merchant),
            "evidence_policy_record_before_landed_cost_gate",
        ),
    )
    report = CatalogQualityFunnelReport(
        policy_version=POLICY_VERSION,
        evaluated_at=evaluated_at.replace(tzinfo=UTC).isoformat().replace("+00:00", "Z"),
        after_raw_id=after_raw_id,
        limit=limit,
        last_raw_source_id=raws[-1].id if raws else None,
        source_unit="bounded_raw_records_then_latest_offer_observation",
        raw_source_records=len(raws),
        offer_observations=len(observations),
        current_offer_observations=len(current_rows),
        stages=stages,
        technical_signals=technical_signals,
        launch_gate_eligible=False,
        report_fingerprint="",
    )
    return replace(report, report_fingerprint=_fingerprint(report))


async def _run(args: argparse.Namespace) -> CatalogQualityFunnelReport:
    settings = get_settings()
    configure_logging(settings.debug)
    if settings.database_schema_mode != "alembic":
        raise RuntimeError("Catalog Quality Funnel requires read-only Alembic mode")
    if not db.is_enabled():
        raise RuntimeError("DATABASE_URL is required")
    await db.prepare_schema()
    async with db.session_scope() as session:
        if session is None:
            raise RuntimeError("database session unavailable")
        return await build_catalog_quality_funnel(
            session,
            evaluated_at=parse_evaluated_at(args.evaluated_at),
            after_raw_id=args.after_raw_id,
            limit=args.limit,
        )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Catalog Quality Funnel shadow")
    parser.add_argument("--evaluated-at", required=True)
    parser.add_argument("--after-raw-id", type=int, default=0)
    parser.add_argument("--limit", type=int, default=1_000)
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        report = asyncio.run(_run(_parser().parse_args(argv)))
    except Exception as exc:
        log.error("Catalog Quality Funnel refusé (error_type=%s)", type(exc).__name__)
        return 1
    print(json.dumps(asdict(report), sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
