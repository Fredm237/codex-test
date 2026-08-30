"""Mesures marchands conservatrices, sans note ni confiance synthétique."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select

from app.db.models import Merchant
from app.merchant_intelligence import models
from app.observations.models import RawSourceRecord
from app.offer_graph.models import GraphOfferObservation
from app.product_graph.models import GraphOfferVariantLink
from app.services.catalog_grouping import normalize_ean


POLICY_VERSION = "merchant-measurement-shadow-v1"
PRICE_FRESHNESS_WINDOW = timedelta(hours=72)
_STATE_VALUES = {
    "ships_to_country": frozenset({"not_measurable"}),
    "merchant_country": frozenset({"observed", "unknown"}),
    "delivery_reliability": frozenset({"not_measurable"}),
    "return_policy": frozenset({"not_measurable"}),
    "warranty_quality": frozenset({"not_measurable"}),
    "support_quality": frozenset({"not_measurable"}),
    "payment_security": frozenset({"not_measurable"}),
    "seller_type": frozenset({"unknown"}),
    "historical_availability": frozenset({"coverage_only"}),
    "price_freshness": frozenset({"measured"}),
    "price_accuracy": frozenset({"not_measurable"}),
    "affiliate_relationship": frozenset({"observed", "unknown"}),
    "merchant_relationship_type": frozenset({"AFFILIATED", "INDEXED"}),
    "feed_freshness": frozenset({"measured", "invalid_future"}),
    "price_stability": frozenset({"not_measurable"}),
    "stock_mismatch": frozenset({"not_measurable"}),
    "shipping_coverage": frozenset({"not_measurable"}),
    "broken_link_rate": frozenset({"syntactic_only"}),
}


class MerchantMeasurementError(ValueError):
    """Fenêtre ou provenance invalide."""


@dataclass(frozen=True)
class MerchantMeasurement:
    merchant_id: int
    merchant_status: str
    window_first_raw_id: int
    window_last_raw_id: int
    source_record_count: int
    offer_observation_count: int
    gtin_known_count: int
    price_known_count: int
    price_fresh_count: int
    stock_known_count: int
    merchant_link_known_count: int
    invalid_link_count: int
    identity_resolved_count: int
    eligible_offer_count: int
    latest_observed_at: datetime
    evaluated_at: datetime
    feed_age_seconds: int | None
    measurement_states: dict[str, Any]

    def ratios(self) -> dict[str, float | None]:
        denominator = self.source_record_count
        if denominator <= 0:
            return {
                key: None
                for key in (
                    "gtin_coverage",
                    "price_coverage",
                    "price_freshness",
                    "stock_coverage",
                    "merchant_link_coverage",
                    "invalid_link_rate",
                    "identity_resolution_rate",
                    "decision_eligibility_rate",
                )
            }
        return {
            "gtin_coverage": self.gtin_known_count / denominator,
            "price_coverage": self.price_known_count / denominator,
            "price_freshness": self.price_fresh_count / denominator,
            "stock_coverage": self.stock_known_count / denominator,
            "merchant_link_coverage": self.merchant_link_known_count / denominator,
            "invalid_link_rate": self.invalid_link_count / denominator,
            "identity_resolution_rate": self.identity_resolved_count / denominator,
            "decision_eligibility_rate": self.eligible_offer_count / denominator,
        }


def _merchant_id(raw: RawSourceRecord) -> int:
    value = raw.context_json.get("merchant_id")
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise MerchantMeasurementError("raw source merchant_id is invalid")
    return value


def _validate_states(states: dict[str, Any]) -> None:
    if set(states) != set(_STATE_VALUES):
        raise MerchantMeasurementError("measurement states roster is invalid")
    for key, allowed in _STATE_VALUES.items():
        if states[key] not in allowed:
            raise MerchantMeasurementError(f"measurement state {key} is invalid")


async def measure_merchant_window(
    session,
    *,
    raws: Sequence[RawSourceRecord],
    evaluated_at: datetime,
) -> MerchantMeasurement:
    if not raws:
        raise MerchantMeasurementError("merchant window cannot be empty")
    if evaluated_at.tzinfo is not None:
        raise MerchantMeasurementError("evaluated_at must be UTC-naive internally")
    ordered = sorted(raws, key=lambda raw: raw.id)
    merchant_ids = {_merchant_id(raw) for raw in ordered}
    if len(merchant_ids) != 1:
        raise MerchantMeasurementError("merchant window mixes merchants")
    merchant_id = next(iter(merchant_ids))
    merchant = await session.get(Merchant, merchant_id)
    if merchant is None:
        raise MerchantMeasurementError("merchant does not exist")

    raw_ids = [raw.id for raw in ordered]
    offer_rows = (
        await session.execute(
            select(GraphOfferObservation, GraphOfferVariantLink.resolution)
            .outerjoin(
                GraphOfferVariantLink,
                GraphOfferVariantLink.id
                == GraphOfferObservation.offer_variant_link_id,
            )
            .where(GraphOfferObservation.raw_source_record_id.in_(raw_ids))
        )
    ).all()
    offers = {observation.raw_source_record_id: (observation, resolution) for observation, resolution in offer_rows}

    latest_observed_at = max(raw.observed_at for raw in ordered)
    feed_age_seconds = None
    feed_freshness_state = "invalid_future"
    if latest_observed_at <= evaluated_at:
        feed_age_seconds = int((evaluated_at - latest_observed_at).total_seconds())
        feed_freshness_state = "measured"

    gtin_known = 0
    price_known = price_fresh = stock_known = 0
    link_known = invalid_link = identity_resolved = eligible = 0
    for raw in ordered:
        gtin_known += int(normalize_ean(raw.payload_json.get("ean")) is not None)
        pair = offers.get(raw.id)
        if pair is None:
            continue
        observation, link_resolution = pair
        price_known += int(observation.price_state == "known")
        if (
            observation.price_state == "known"
            and observation.observed_at <= evaluated_at
            and evaluated_at - observation.observed_at <= PRICE_FRESHNESS_WINDOW
        ):
            price_fresh += 1
        stock_known += int(observation.availability != "unknown")
        link_known += int(observation.merchant_url_state == "known")
        invalid_link += int(observation.merchant_url_state == "invalid")
        identity_resolved += int(link_resolution == "resolved")
        eligible += int(observation.eligibility == "eligible")

    merchant_status = "AFFILIATED" if merchant.joined is True else "INDEXED"
    states: dict[str, Any] = {
        "ships_to_country": "not_measurable",
        "merchant_country": "observed" if merchant.region else "unknown",
        "delivery_reliability": "not_measurable",
        "return_policy": "not_measurable",
        "warranty_quality": "not_measurable",
        "support_quality": "not_measurable",
        "payment_security": "not_measurable",
        "seller_type": "unknown",
        "historical_availability": "coverage_only",
        "price_freshness": "measured",
        "price_accuracy": "not_measurable",
        "affiliate_relationship": "observed" if merchant.joined is True else "unknown",
        "merchant_relationship_type": merchant_status,
        "feed_freshness": feed_freshness_state,
        "price_stability": "not_measurable",
        "stock_mismatch": "not_measurable",
        "shipping_coverage": "not_measurable",
        "broken_link_rate": "syntactic_only",
    }
    _validate_states(states)
    return MerchantMeasurement(
        merchant_id=merchant_id,
        merchant_status=merchant_status,
        window_first_raw_id=ordered[0].id,
        window_last_raw_id=ordered[-1].id,
        source_record_count=len(ordered),
        offer_observation_count=len(offers),
        gtin_known_count=gtin_known,
        price_known_count=price_known,
        price_fresh_count=price_fresh,
        stock_known_count=stock_known,
        merchant_link_known_count=link_known,
        invalid_link_count=invalid_link,
        identity_resolved_count=identity_resolved,
        eligible_offer_count=eligible,
        latest_observed_at=latest_observed_at,
        evaluated_at=evaluated_at,
        feed_age_seconds=feed_age_seconds,
        measurement_states=states,
    )


async def persist_measurement(session, measurement: MerchantMeasurement) -> bool:
    _validate_states(measurement.measurement_states)
    existing = await session.scalar(
        select(models.MerchantQualitySnapshot.id).where(
            models.MerchantQualitySnapshot.merchant_id == measurement.merchant_id,
            models.MerchantQualitySnapshot.window_first_raw_id
            == measurement.window_first_raw_id,
            models.MerchantQualitySnapshot.window_last_raw_id
            == measurement.window_last_raw_id,
            models.MerchantQualitySnapshot.policy_version == POLICY_VERSION,
        )
    )
    if existing is not None:
        return False
    session.add(
        models.MerchantQualitySnapshot(
            merchant_id=measurement.merchant_id,
            merchant_status=measurement.merchant_status,
            window_first_raw_id=measurement.window_first_raw_id,
            window_last_raw_id=measurement.window_last_raw_id,
            source_record_count=measurement.source_record_count,
            offer_observation_count=measurement.offer_observation_count,
            gtin_known_count=measurement.gtin_known_count,
            price_known_count=measurement.price_known_count,
            price_fresh_count=measurement.price_fresh_count,
            stock_known_count=measurement.stock_known_count,
            merchant_link_known_count=measurement.merchant_link_known_count,
            invalid_link_count=measurement.invalid_link_count,
            identity_resolved_count=measurement.identity_resolved_count,
            eligible_offer_count=measurement.eligible_offer_count,
            latest_observed_at=measurement.latest_observed_at,
            evaluated_at=measurement.evaluated_at,
            feed_age_seconds=measurement.feed_age_seconds,
            measurement_states_json=measurement.measurement_states,
            policy_version=POLICY_VERSION,
        )
    )
    await session.flush()
    return True
