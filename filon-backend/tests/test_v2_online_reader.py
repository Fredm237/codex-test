"""Qualification du lecteur V2 en ligne avant tout raccordement public."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import models as core_models
from app.db.base import Base
from app.hybrid_retrieval.models import HybridRetrievalRun
from app.observations.models import Observation, RawSourceRecord
from app.product_ontology.models import ProductOntologySnapshot
from app.v2_chain.execution import run_journaled_v2_shadow_chain
from app.v2_chain.online_reader import (
    ONLINE_READER_VERSION,
    V2OnlineReadRequest,
    V2OnlineReaderError,
    read_v2_online,
)


EVALUATED_AT = datetime(2026, 9, 3, 20, tzinfo=timezone.utc)
ROUTES_ROOT = Path(__file__).resolve().parents[1] / "app" / "api" / "routes"
CONTRACT_ROOT = Path(__file__).resolve().parents[2] / "contracts" / "v2-chain" / "v1"
SCHEMA = json.loads((CONTRACT_ROOT / "online-response.schema.json").read_text())
VALIDATOR = Draft202012Validator(SCHEMA)


async def _database():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    return engine, async_sessionmaker(engine, expire_on_commit=False)


async def _seed(session) -> None:
    merchant = core_models.Merchant(
        awin_mid=1919,
        name="Online Reader Merchant",
        slug="online-reader-merchant",
        joined=True,
    )
    session.add(merchant)
    await session.flush()
    offer = core_models.Offer(
        merchant_id=merchant.id,
        awin_product_id="online-reader-1",
        name="Acme Smartphone Prime 128GB",
        brand="Acme",
        price=599,
        currency="EUR",
        in_stock=True,
        is_canonical=True,
        is_adult=False,
    )
    session.add(offer)
    await session.flush()
    session.add(
        core_models.PriceSnapshot(
            offer_id=offer.id,
            price=599,
            currency="EUR",
            in_stock=True,
            captured_at=(EVALUATED_AT - timedelta(hours=1)).replace(tzinfo=None),
        )
    )
    raw = RawSourceRecord(
        source_type="awin_feed",
        source_ref="awin-feed:1919",
        source_record_key="1919:online-reader-1",
        schema_version="awin-create-a-feed-v1",
        context_json={"merchant_id": merchant.id},
        payload_json={
            "ean": "4006381333931",
            "brand_name": "Acme",
            "product_name": offer.name,
            "name": offer.name,
            "offer_kind": "physical_product",
            "search_price": "599.00",
            "currency": "EUR",
            "in_stock": "yes",
        },
        payload_checksum="c" * 64,
        replay_key="d" * 64,
        observed_at=(EVALUATED_AT - timedelta(hours=1)).replace(tzinfo=None),
    )
    session.add(raw)
    await session.flush()
    session.add(
        Observation(
            raw_source_record_id=raw.id,
            subject_type="offer",
            subject_ref=f"offer:{offer.id}",
            offer_id=offer.id,
            field="name",
            value_json=offer.name,
            status="verified",
            source_type="awin_feed",
            source_ref=raw.source_ref,
            observed_at=raw.observed_at,
            transformation="test",
            transformation_version="v1",
            confidence=1.0,
        )
    )
    await session.commit()


@pytest.mark.asyncio
async def test_online_reader_executes_real_chain_without_writing_or_exposing_query() -> None:
    engine, sessions = await _database()
    try:
        async with sessions() as session:
            await _seed(session)
            await run_journaled_v2_shadow_chain(
                session,
                evaluated_at=EVALUATED_AT,
                vertical="smartphones",
                limit=1,
                apply=True,
            )
            runs_before = await session.scalar(
                select(func.count()).select_from(HybridRetrievalRun)
            )
            snapshots_before = await session.scalar(
                select(func.count()).select_from(ProductOntologySnapshot)
            )

            result = await read_v2_online(
                session,
                V2OnlineReadRequest(
                    query="Acme Smartphone Prime",
                    vertical="smartphones",
                    locale="fr",
                ),
                evaluated_at=EVALUATED_AT,
            )

            assert result.chain_complete is True
            assert result.safety_state == "ABSTAIN"
            assert result.provenance_complete is True
            assert result.response_type == "ABSTAIN"
            assert result.response["schema_version"] == "v2-online-response/v1"
            assert result.response["reader_version"] == ONLINE_READER_VERSION
            assert result.response["outcome"] == "ABSTAIN"
            assert result.response["items"] == []
            assert result.response["raw_query_retained"] is False
            assert result.response["query_digest"].startswith("sha256:")
            assert len(result.response["provenance"]) == 6
            assert {item["stage"] for item in result.response["provenance"]} == {
                "hybrid_retrieval",
                "constraint_engine",
                "product_ranking",
                "offer_optimization",
                "confidence",
                "buy_wait",
            }
            VALIDATOR.validate(dict(result.response))
            assert await session.scalar(
                select(func.count()).select_from(HybridRetrievalRun)
            ) == runs_before
            assert await session.scalar(
                select(func.count()).select_from(ProductOntologySnapshot)
            ) == snapshots_before
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_online_reader_empty_index_is_an_honest_abstention() -> None:
    engine, sessions = await _database()
    try:
        async with sessions() as session:
            result = await read_v2_online(
                session,
                V2OnlineReadRequest(query="unknown product", vertical="smartphones"),
                evaluated_at=EVALUATED_AT,
            )

            assert result.response_type == "ABSTAIN"
            assert result.response["items"] == []
            assert "retrieval_no_match" in result.response["reason_codes"]
    finally:
        await engine.dispose()


@pytest.mark.parametrize(
    "kwargs",
    (
        {"query": "", "vertical": "smartphones"},
        {"query": "phone", "vertical": "unknown"},
        {"query": "phone", "vertical": "smartphones", "locale": "de"},
        {"query": "phone", "vertical": "smartphones", "country_code": "be"},
        {
            "query": "phone",
            "vertical": "smartphones",
            "budget_amount_decimal": "500",
        },
        {
            "query": "phone",
            "vertical": "smartphones",
            "budget_amount_decimal": "NaN",
            "budget_currency": "EUR",
        },
        {
            "query": "phone",
            "vertical": "smartphones",
            "budget_amount_decimal": "500",
            "budget_currency": "eur",
        },
    ),
)
def test_online_reader_contract_fails_closed(kwargs) -> None:
    with pytest.raises(V2OnlineReaderError):
        V2OnlineReadRequest(**kwargs)


def test_online_reader_is_not_wired_to_public_routes() -> None:
    public_routes = "\n".join(
        path.read_text(encoding="utf-8") for path in ROUTES_ROOT.glob("*.py")
    )

    assert "v2_chain.online_reader" not in public_routes
    assert "read_v2_online" not in public_routes


def test_online_reader_contract_and_example_are_valid() -> None:
    Draft202012Validator.check_schema(SCHEMA)
    example = json.loads((CONTRACT_ROOT / "examples" / "abstain.json").read_text())

    VALIDATOR.validate(example)
    assert example["raw_query_retained"] is False
    assert example["items"] == []
