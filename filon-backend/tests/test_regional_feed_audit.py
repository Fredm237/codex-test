"""Qualification de l'audit régional Awin sans écriture."""

from __future__ import annotations

import json
from contextlib import asynccontextmanager
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

from jsonschema import Draft202012Validator
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import models as core_models
from app.db.base import Base
from app.ingest import regional_feed_audit
from app.observations.awin import project_awin_row
from app.product_graph.identity import project_awin_identity_assertions
from app.product_graph.resolution import project_awin_variant
from app.services import awin_catalog
from app.services.catalog_grouping import extract_awin_gtin

ROOT = Path(__file__).parents[2]
CONTRACT = ROOT / "contracts" / "v2-chain" / "v1"


def test_scope_and_samples_are_strictly_bounded() -> None:
    assert regional_feed_audit._validate_scope(
        region="be",
        feed_ids=["41", "42"],
        sample_rows=500,
        max_sampled_feeds=12,
    ) == ("BE", ("41", "42"), 500, 12)

    for field, value in (("sample_rows", 2_001), ("max_sampled_feeds", 65)):
        arguments = {
            "region": "BE",
            "feed_ids": (),
            "sample_rows": 500,
            "max_sampled_feeds": 12,
        }
        arguments[field] = value
        try:
            regional_feed_audit._validate_scope(**arguments)
        except ValueError as exc:
            assert "between" in str(exc)
        else:  # pragma: no cover - garde explicite
            raise AssertionError("unsafe audit bound accepted")


def test_alternate_awin_gtin_is_validated_without_weak_identity_fallback() -> None:
    row = {
        "ean": "invalid",
        "product_GTIN": "4006381333931",
        "upc": "9780201379624",
        "aw_product_id": "merchant-sku",
        "product_name": "Smartphone Exemple 128 Go",
    }

    assert extract_awin_gtin(row) == (
        "4006381333931",
        "product_GTIN",
        "4006381333931",
    )
    resolution = project_awin_variant(row)
    assert resolution.resolution == "resolved"
    assert resolution.reason_code == "exact_gtin"
    assert resolution.gtin == "4006381333931"
    assertions = project_awin_identity_assertions(row, merchant_id=12)
    gtin = next(item for item in assertions if item.identifier_namespace == "gtin")
    assert gtin.status == "validated"
    assert gtin.identifier_scope == "global"
    assert gtin.normalized_value == "4006381333931"


def test_raw_projection_preserves_source_field_but_exposes_verified_gtin() -> None:
    row = {
        "aw_product_id": "sku-1",
        "product_name": "Smartphone Exemple",
        "product_GTIN": "4006381333931",
    }

    projection = project_awin_row(row, feed_id="42", merchant_id=12)

    assert "ean" not in projection.payload
    assert projection.payload["product_GTIN"] == "4006381333931"
    gtin = next(item for item in projection.observations if item.field == "gtin")
    assert (gtin.status, gtin.value) == ("verified", "4006381333931")
    assert not any(issue.stage == "identifier_validation" for issue in projection.issues)


def test_aggregate_counts_only_real_smartphones_with_valid_gtin() -> None:
    feed = awin_catalog.FeedInfo(
        "42",
        77,
        "Marchand belge",
        "BE",
        8_000,
        ("product_name", "merchant_category", "product_GTIN"),
    )
    rows = [
        {
            "product_name": "Smartphone Exemple 128 Go",
            "merchant_category": "Smartphones",
            "product_GTIN": "4006381333931",
        },
        {
            "product_name": "Coque pour smartphone",
            "merchant_category": "Accessoires téléphone",
            "product_GTIN": "9780201379624",
        },
        {
            "product_name": "Smartphone Exemple 256 Go",
            "merchant_category": "Smartphones",
            "product_GTIN": "invalid",
        },
    ]

    result = regional_feed_audit._aggregate_rows(feed, rows)

    assert result.sampled_rows == 3
    assert result.identifier_supplied_rows == 3
    assert result.valid_gtin_rows == 2
    assert result.smartphone_rows == 2
    assert result.smartphone_valid_gtin_rows == 1


async def test_audit_selects_only_joined_regional_feed_and_recommends_evidence(
    monkeypatch,
) -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with maker() as session:
            session.add(
                core_models.Merchant(
                    awin_mid=77,
                    name="Marchand belge",
                    slug="marchand-belge",
                    region="BE",
                    joined=True,
                )
            )
            await session.commit()

        @asynccontextmanager
        async def session_scope():
            async with maker() as session:
                yield session

        monkeypatch.setattr(regional_feed_audit.db, "session_scope", session_scope)
        monkeypatch.setattr(regional_feed_audit.db, "is_enabled", lambda: True)
        monkeypatch.setattr(
            regional_feed_audit,
            "get_settings",
            lambda: SimpleNamespace(awin_feed_api_key="configured"),
        )
        monkeypatch.setattr(
            awin_catalog,
            "list_feeds",
            AsyncMock(
                return_value=[
                    awin_catalog.FeedInfo(
                        "41", 77, "Marchand belge", "BE", 500, ("ean",)
                    ),
                    awin_catalog.FeedInfo(
                        "42",
                        77,
                        "Marchand belge",
                        "BE",
                        8_000,
                        ("product_GTIN",),
                    ),
                    awin_catalog.FeedInfo(
                        "43", 88, "Non inscrit", "BE", 9_000, ("ean",)
                    ),
                    awin_catalog.FeedInfo(
                        "44", 77, "Marchand belge", "NL", 9_000, ("ean",)
                    ),
                ]
            ),
        )

        async def download(feed_ids: list[str], *, max_rows: int):
            assert max_rows == 500
            if feed_ids == ["42"]:
                return [
                    {
                        "product_name": "Smartphone Exemple 128 Go",
                        "merchant_category": "Smartphones",
                        "product_GTIN": "4006381333931",
                    }
                ]
            return [
                {
                    "product_name": "Smartphone sans code",
                    "merchant_category": "Smartphones",
                    "ean": "",
                }
            ]

        monkeypatch.setattr(awin_catalog, "_download_feed_rows", download)
        receipt = await regional_feed_audit.audit(
            region="BE",
            sample_rows=500,
            max_sampled_feeds=12,
        )

        assert receipt.status == "qualified"
        assert receipt.eligible_feed_count == 2
        assert receipt.sampled_feed_count == 2
        assert receipt.qualified_feed_ids == ("42",)
        assert receipt.recommended_feed_id == "42"
        assert receipt.raw_payload_retained is False
        assert receipt.product_names_retained is False

        schema = json.loads(
            (CONTRACT / "regional-feed-audit.schema.json").read_text(
                encoding="utf-8"
            )
        )
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(
            json.loads(json.dumps(asdict(receipt)))
        )
    finally:
        await engine.dispose()


def test_contract_example_is_valid_and_contains_no_raw_commerce_payload() -> None:
    schema = json.loads(
        (CONTRACT / "regional-feed-audit.schema.json").read_text(encoding="utf-8")
    )
    example = json.loads(
        (CONTRACT / "examples" / "regional-feed-audit-qualified.json").read_text(
            encoding="utf-8"
        )
    )
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(example)
    for feed in example["feeds"]:
        for forbidden in (
            "product_name",
            "search_price",
            "aw_deep_link",
            "image_url",
        ):
            assert forbidden not in feed
