from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import models
from app.db.base import Base
from app.extension_observation.projection import project_page_observation
from app.extension_observation.resolution import resolve_exact_comparison


ROOT = Path(__file__).parents[2] / "contracts" / "extension-observation" / "v1"
RESULT_SCHEMA = json.loads((ROOT / "page-product-observation-result.schema.json").read_text())
VALIDATOR = Draft202012Validator(RESULT_SCHEMA, format_checker=FormatChecker())
EAN = "4006381333931"


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as value:
        yield value
    await engine.dispose()


def _projection(*, gtin: str | None = EAN):
    payload = json.loads((ROOT / "examples" / "exact-product.json").read_text())
    payload["page"]["gtin"] = gtin
    return project_page_observation(
        payload,
        received_at=datetime(2026, 9, 2, 8, 1, tzinfo=UTC),
    )


async def _seed(session, *, currencies=("EUR", "EUR"), captured_at=None):
    merchants = [
        models.Merchant(awin_mid=10, name="Marchand A", slug="merchant-a"),
        models.Merchant(awin_mid=11, name="Marchand B", slug="merchant-b"),
    ]
    session.add_all(merchants)
    await session.flush()
    product = models.CatalogProduct(
        ean=EAN,
        name="Sony WH-1000XM6 Black",
        brand="Sony",
        offers_count=2,
        merchants_count=2,
        price_min=399.0,
        price_max=449.0,
        currency="EUR" if len(set(currencies)) == 1 else None,
    )
    session.add(product)
    await session.flush()
    offers = []
    for index, (merchant, currency, price) in enumerate(zip(merchants, currencies, (449.0, 399.0), strict=True)):
        offer = models.Offer(
            merchant_id=merchant.id,
            product_id=product.id,
            awin_product_id=f"xm6-{index}",
            ean=EAN,
            name="Sony WH-1000XM6 Black",
            brand="Sony",
            price=price,
            currency=currency,
            in_stock=True,
            is_adult=False,
            deep_link=f"https://merchant-{index}.example/product",
        )
        session.add(offer)
        offers.append(offer)
    await session.flush()
    when = captured_at or datetime(2026, 9, 2, 8, 0)
    session.add_all(
        [
            models.PriceSnapshot(
                offer_id=offer.id,
                price=offer.price,
                currency=offer.currency,
                in_stock=True,
                captured_at=when,
            )
            for offer in offers
        ]
    )
    await session.commit()
    return offers


@pytest.mark.asyncio
async def test_exact_gtin_compares_two_current_merchants(session) -> None:
    await _seed(session)
    result = await resolve_exact_comparison(
        session,
        _projection(),
        evaluated_at=datetime(2026, 9, 2, 8, 2, tzinfo=UTC),
    )
    contract = result.as_contract()
    VALIDATOR.validate(contract)
    assert contract["resolution"] == "exact"
    assert contract["comparison"] == {
        "state": "verified",
        "offers_compared": 2,
        "merchants_compared": 2,
        "currency": "EUR",
        "best_price": "399",
    }
    assert contract["destination_url"].startswith(f"https://filon.be/produits/{EAN}")


@pytest.mark.asyncio
async def test_comparison_abstains_across_currencies(session) -> None:
    await _seed(session, currencies=("EUR", "GBP"))
    result = await resolve_exact_comparison(
        session,
        _projection(),
        evaluated_at=datetime(2026, 9, 2, 8, 2, tzinfo=UTC),
    )
    assert result.resolution == "exact"
    assert result.comparison["state"] == "unknown"
    assert result.comparison["best_price"] is None
    assert "mixed_currency" in result.reason_codes


@pytest.mark.asyncio
async def test_comparison_abstains_on_stale_evidence(session) -> None:
    stale = datetime(2026, 8, 20, 8, 0)
    await _seed(session, captured_at=stale)
    result = await resolve_exact_comparison(
        session,
        _projection(),
        evaluated_at=datetime(2026, 9, 2, 8, 2, tzinfo=UTC),
    )
    assert result.comparison["state"] == "unknown"
    assert result.comparison["offers_compared"] == 0
    assert "no_current_offer_evidence" in result.reason_codes


@pytest.mark.asyncio
async def test_missing_gtin_never_uses_title_as_exact_identity(session) -> None:
    result = await resolve_exact_comparison(session, _projection(gtin=None))
    contract = result.as_contract()
    VALIDATOR.validate(contract)
    assert result.resolution == "ambiguous"
    assert result.comparison is None
    assert result.destination_url.startswith("https://filon.be/recherche?")


@pytest.mark.asyncio
async def test_unknown_gtin_is_not_fabricated_from_catalog(session) -> None:
    result = await resolve_exact_comparison(session, _projection())
    contract = result.as_contract()
    VALIDATOR.validate(contract)
    assert result.resolution == "not_found"
    assert result.comparison is None
    assert result.reason_codes == ("catalog_product_not_found",)
