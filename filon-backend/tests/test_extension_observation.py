from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import models as core_models  # noqa: F401
from app.db.base import Base
from app.extension_observation.projection import (
    ExtensionObservationError,
    persist_page_observation,
    project_page_observation,
)
from app.observations import models


ROOT = Path(__file__).parents[2] / "contracts" / "extension-observation" / "v1"
REQUEST_SCHEMA = json.loads((ROOT / "page-product-observation.schema.json").read_text())
RESPONSE_SCHEMA = json.loads((ROOT / "page-product-observation-result.schema.json").read_text())


def _payload() -> dict:
    return json.loads((ROOT / "examples" / "exact-product.json").read_text())


def test_contract_and_examples_are_valid() -> None:
    Draft202012Validator.check_schema(REQUEST_SCHEMA)
    Draft202012Validator.check_schema(RESPONSE_SCHEMA)
    validator = Draft202012Validator(REQUEST_SCHEMA, format_checker=FormatChecker())
    for example in sorted((ROOT / "examples").glob("*.json")):
        validator.validate(json.loads(example.read_text()))


def test_projection_is_deterministic_and_strips_nothing_by_guess() -> None:
    payload = _payload()
    received_at = datetime(2026, 9, 2, 8, 1, tzinfo=UTC)
    first = project_page_observation(payload, received_at=received_at)
    second = project_page_observation(payload, received_at=received_at)
    assert first == second
    assert first.payload == payload
    assert first.source_ref == "extension:merchant.example"
    assert len(first.payload_checksum) == 64
    assert len(first.replay_key) == 64
    by_field = {item.field: item for item in first.observations}
    assert by_field["gtin"].value == "4006381333931"
    assert by_field["price"].value == {"amount": "449.00", "currency": "EUR"}


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda value: value["page"].update(url="https://merchant.example/p?q=private"), "HTTPS origin and path"),
        (lambda value: value["page"].update(merchant="other.example"), "must match"),
        (lambda value: value["page"].update(gtin="4006381333932"), "checksum"),
        (lambda value: value.update(capture_mode="background"), "explicit_user_action"),
        (lambda value: value.update(observed_at="2026-09-02T08:10:01Z"), "future"),
        (lambda value: value["page"].update(extra="forbidden"), "fields"),
        (lambda value: value["page"]["json_ld"]["source_fields"].append("customer.email"), "source_fields"),
    ],
)
def test_projection_fails_closed(mutate, message: str) -> None:
    payload = _payload()
    mutate(payload)
    with pytest.raises(ExtensionObservationError, match=message):
        project_page_observation(
            payload,
            received_at=datetime(2026, 9, 2, 8, 0, tzinfo=UTC),
        )


def test_unknown_price_and_availability_stay_unknown() -> None:
    payload = json.loads((ROOT / "examples" / "partial-product.json").read_text())
    projection = project_page_observation(
        payload,
        received_at=datetime(2026, 9, 2, 8, 0, tzinfo=UTC),
    )
    by_field = {item.field: item for item in projection.observations}
    assert by_field["price"].status == "unknown"
    assert by_field["price"].value is None
    assert by_field["availability"].status == "unknown"
    assert by_field["availability"].value is None


@pytest.mark.asyncio
async def test_persistence_is_append_only_and_idempotent() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    try:
        async with maker() as session:
            projection = project_page_observation(
                _payload(),
                received_at=datetime(2026, 9, 2, 8, 1, tzinfo=UTC),
            )
            first = await persist_page_observation(session, projection)
            second = await persist_page_observation(session, projection)
            await session.commit()
            assert first.raw_created is True
            assert second.raw_created is False
            assert second.raw_source_record_id == first.raw_source_record_id
            assert first.observations_created == 12
            assert second.observations_created == 0
            assert await session.scalar(select(func.count()).select_from(models.RawSourceRecord)) == 1
            assert await session.scalar(select(func.count()).select_from(models.Observation)) == 12
    finally:
        await engine.dispose()


def test_timestamp_accepts_past_replay_but_not_future_evidence() -> None:
    payload = _payload()
    payload["observed_at"] = "2025-01-01T00:00:00Z"
    projection = project_page_observation(payload, received_at=datetime.now(UTC))
    assert projection.observed_at < datetime.now(UTC).replace(tzinfo=None) - timedelta(days=1)
