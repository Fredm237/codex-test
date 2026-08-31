"""Les callers Assistant historiques ne doivent jamais inventer une devise."""

from __future__ import annotations

import json
import math
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import models
from app.db import session as db
from app.db.base import Base
from app.intelligence.contracts import CoreOfferSnapshot
from app.intelligence.intent_resolution import GeneralIntent, IntentScope
from app.services import catalog_search, recommend, taxonomy
from app.services.currency import (
    SUPPORTED_CURRENCY_CODES,
    SUPPORTED_CURRENCY_ROSTER_VERSION,
    normalize_currency_code,
)
from app.services.decision import compute_decision


LEGACY_REFERENCE = datetime(2026, 8, 29, 12, 0, tzinfo=UTC)


def _current_decision(price: float) -> dict:
    observed_at = datetime.now(UTC)
    return compute_decision(
        price=price,
        currency="EUR",
        history=[(price, observed_at)],
        history_currency="EUR",
        cheapest_elsewhere=price,
        comparison_currency="EUR",
        merchants_count=2,
        offers_count=2,
        in_stock=True,
        now=observed_at,
    )


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (None, None),
        ("", None),
        ("   ", None),
        ("unknown", None),
        ("ABC", None),
        ("UNK", None),
        ("NAN", None),
        ("XXX", None),
        ("XTS", None),
        ("€", None),
        (" eur ", "EUR"),
        ("gbp", "GBP"),
    ],
)
def test_currency_normalization_never_turns_an_unknown_value_into_eur(raw, expected):
    assert normalize_currency_code(raw) == expected


def test_supported_currency_roster_is_closed_and_versioned():
    assert SUPPORTED_CURRENCY_ROSTER_VERSION == "filon-currency-roster-2026-08-29-v1"
    assert {"EUR", "CHF", "GBP", "USD", "JPY"}.issubset(SUPPORTED_CURRENCY_CODES)
    assert {"ABC", "UNK", "NAN", "XXX", "XTS"}.isdisjoint(SUPPORTED_CURRENCY_CODES)


def test_resolved_path_propagates_normalized_currency_to_the_frozen_snapshot():
    now = datetime.now(UTC)
    raw = CoreOfferSnapshot(
        offer_id=1,
        catalog_product_id=None,
        name="Casque audio documenté",
        brand="Test",
        filon_category=taxonomy.TV_SON,
        filon_subcategory="Casques audio",
        offer_kind=taxonomy.PHYSICAL_PRODUCT,
        price=90.0,
        currency=" eur ",
        availability="in_stock",
        image_url="https://example.test/casque.jpg",
        deep_link="https://example.test/casque",
        merchant_id=1,
        merchant_name="Test",
        merchant_region="BE",
        observed_at=now,
    )
    intent = GeneralIntent(
        raw_request="casque audio sous 100 euros",
        locale="fr",
        scopes=(
            IntentScope(
                taxonomy.TV_SON,
                "Casques audio",
                "casque audio",
                ("casque", "audio"),
            ),
        ),
        terms=("casque", "audio"),
        required_title_phrases=(),
        budget_eur=100.0,
    )

    normalized = catalog_search._normalize_general_snapshots([raw])

    assert raw.currency == " eur "  # Le contrat source reste immuable.
    assert normalized[0].currency == "EUR"
    assert catalog_search._planned_general_offer_ids(intent, normalized) == [1]


@pytest.mark.parametrize(
    ("price", "stock", "observed_at"),
    [
        (float("nan"), True, LEGACY_REFERENCE),
        (float("inf"), True, LEGACY_REFERENCE),
        (float("-inf"), True, LEGACY_REFERENCE),
        (0.0, True, LEGACY_REFERENCE),
        (-1.0, True, LEGACY_REFERENCE),
        (10.0, False, LEGACY_REFERENCE),
        (10.0, None, LEGACY_REFERENCE),
        (10.0, True, None),
        (10.0, True, LEGACY_REFERENCE - timedelta(hours=73)),
        (10.0, True, LEGACY_REFERENCE + timedelta(minutes=1)),
    ],
)
def test_legacy_offer_guard_rejects_non_finite_stock_unknown_and_stale_facts(
    price, stock, observed_at
):
    offer = SimpleNamespace(
        price=price,
        currency="EUR",
        in_stock=stock,
        updated_at=observed_at,
    )

    assert catalog_search._offer_is_recommendable(
        offer,
        observed_at=observed_at,
        now=LEGACY_REFERENCE,
    ) is False


def test_legacy_offer_guard_never_uses_the_mutable_updated_at_as_observation():
    offer = SimpleNamespace(
        price=10.0,
        currency="EUR",
        in_stock=True,
        updated_at=LEGACY_REFERENCE,
    )

    assert catalog_search._offer_is_recommendable(
        offer, now=LEGACY_REFERENCE
    ) is False
    assert catalog_search._offer_is_recommendable(
        offer,
        observed_at=LEGACY_REFERENCE,
        now=LEGACY_REFERENCE,
    ) is True


@pytest.mark.anyio
async def test_reranker_abstains_before_any_model_call_when_currency_is_missing(monkeypatch):
    def forbidden_settings():
        raise AssertionError("Une offre sans devise ne doit pas atteindre le reranker")

    monkeypatch.setattr(recommend, "get_settings", forbidden_settings)

    result = await recommend._rank_real_products(
        "casque audio",
        200,
        [
            {
                "offer_id": 1,
                "name": "Casque au prix techniquement le plus bas",
                "price": 1,
                "currency": None,
                "merchant": "Sans devise",
            }
        ],
        "fr",
    )

    assert result == {
        "usage": "casque audio",
        "emoji": "\U0001F6CD\uFE0F",
        "offers": 0,
        "cards": [],
        "real": False,
        "currency": None,
    }


@pytest.mark.anyio
async def test_reranker_abstains_on_mixed_currencies_without_budget_before_model(monkeypatch):
    def forbidden_settings():
        raise AssertionError("Des devises mixtes ne doivent pas atteindre le reranker")

    monkeypatch.setattr(recommend, "get_settings", forbidden_settings)

    result = await recommend._rank_real_products(
        "casque audio",
        None,
        [
            {
                "offer_id": 1,
                "name": "Casque EUR",
                "price": 90,
                "currency": "EUR",
                "merchant": "Euro",
            },
            {
                "offer_id": 2,
                "name": "Casque GBP",
                "price": 80,
                "currency": "GBP",
                "merchant": "Livre",
            },
        ],
        "fr",
    )

    assert result["real"] is False
    assert result["cards"] == []
    assert result["currency"] is None


@pytest.mark.anyio
async def test_euro_budget_excludes_unknown_and_foreign_currencies_before_ranking(monkeypatch):
    class MockProvider:
        name = "mock"

    class MockRouter:
        def for_task(self, task):
            assert task == "reasoning"
            return MockProvider()

    monkeypatch.setattr(
        recommend,
        "get_settings",
        lambda: SimpleNamespace(llm_timeout_seconds=1),
    )
    monkeypatch.setattr(recommend, "get_router", lambda: MockRouter())

    async def no_advertiser_refresh():
        return None

    monkeypatch.setattr(recommend.awin, "ensure_advertisers", no_advertiser_refresh)

    result = await recommend._rank_real_products(
        "casque audio sous 100 euros",
        100,
        [
            {
                "offer_id": 1,
                "name": "Casque sans devise",
                "price": 1,
                "currency": "unknown",
                "merchant": "Inconnu",
            },
            {
                "offer_id": 2,
                "name": "Casque en livres",
                "price": 2,
                "currency": "GBP",
                "merchant": "Etranger",
            },
            {
                "offer_id": 3,
                "name": "Casque en euros",
                "price": 90,
                "currency": " eur ",
                "merchant": "Comparable",
                "decision": _current_decision(90),
            },
        ],
        "fr",
    )

    assert result["real"] is True
    assert result["offers"] == 1
    assert [card["offer_id"] for card in result["cards"]] == [3]
    assert result["cards"][0]["currency"] == "EUR"
    assert result["currency"] == "EUR"


def test_pick_validation_requires_a_list_of_mappings_and_ignores_bad_members():
    assert recommend._validated_pick_indices(None, candidate_count=2) == []
    assert recommend._validated_pick_indices({"index": 0}, candidate_count=2) == []
    assert recommend._validated_pick_indices("0", candidate_count=2) == []
    assert recommend._validated_pick_indices(
        [
            None,
            "bad",
            17,
            {"index": True},
            {"index": "0"},
            {"index": 9},
            {"index": 1},
            {"index": 1},
        ],
        candidate_count=2,
    ) == [1]


def test_global_currency_requires_every_card_to_share_one_real_currency():
    assert recommend._unique_card_currency([]) is None
    assert recommend._unique_card_currency([{"currency": None}]) is None
    assert recommend._unique_card_currency(
        [{"currency": "EUR"}, {"currency": "GBP"}]
    ) is None
    assert recommend._unique_card_currency(
        [{"currency": " eur "}, {"currency": "EUR"}]
    ) == "EUR"


@pytest.mark.anyio
async def test_llm_can_only_choose_indices_and_cannot_publish_claims(monkeypatch):
    class AdversarialProvider:
        name = "adversarial"

        async def complete_json(self, messages, *, temperature=0.0):
            return json.dumps(
                {
                    "usage": "ACHAT GARANTI",
                    "emoji": "💰",
                    "picks": [
                        None,
                        "bad",
                        {"index": True},
                        {"index": 99},
                        {
                            "index": 0,
                            "label": "Meilleur garanti",
                            "why": "Stock et livraison garantis par le modèle.",
                        },
                    ],
                }
            )

    class AdversarialRouter:
        def for_task(self, task):
            assert task == "reasoning"
            return AdversarialProvider()

    monkeypatch.setattr(
        recommend,
        "get_settings",
        lambda: SimpleNamespace(llm_timeout_seconds=1),
    )
    monkeypatch.setattr(recommend, "get_router", lambda: AdversarialRouter())

    async def no_advertiser_refresh():
        return None

    monkeypatch.setattr(recommend.awin, "ensure_advertisers", no_advertiser_refresh)

    result = await recommend._rank_real_products(
        "casque audio",
        None,
        [
            {
                "offer_id": 7,
                "name": "Casque documenté",
                "price": 90,
                "currency": "EUR",
                "merchant": "Marchand",
                "decision": _current_decision(90),
            }
        ],
        "fr",
    )

    assert result["usage"] == "casque audio"
    assert result["emoji"] == "\U0001F6CD\uFE0F"
    assert result["currency"] == "EUR"
    assert [card["offer_id"] for card in result["cards"]] == [7]
    assert result["cards"][0]["rank"] == "Offre indexée"
    assert result["cards"][0]["why"] == (
        "Offre issue du catalogue indexé ; vérifiez les conditions chez le marchand."
    )
    assert result["cards"][0]["buy"] is False
    assert result["cards"][0]["evidence_current"] is True
    assert "garanti" not in repr(result).lower()


@pytest.fixture
async def legacy_catalogue(monkeypatch):
    """Catalogue minimal forçant la voie SQL historique non résolue."""

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    previous = (db._engine, db._sessionmaker)
    db._engine = engine
    db._sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

    async with db._sessionmaker() as session:
        merchant = models.Merchant(
            awin_mid=9001,
            name="Marchand devises",
            slug="marchand-devises",
        )
        session.add(merchant)
        await session.flush()

        now = datetime.now(UTC).replace(tzinfo=None)

        def offer(
            product_id: str,
            price: float,
            currency: str | None,
            *,
            in_stock: bool | None = True,
            updated_at: datetime = now,
        ):
            return models.Offer(
                merchant_id=merchant.id,
                awin_product_id=product_id,
                name=f"Casque audio documenté {product_id}",
                brand="Test",
                category="Headphones",
                filon_category=taxonomy.TV_SON,
                filon_subcategory="Casques audio",
                offer_kind=taxonomy.PHYSICAL_PRODUCT,
                price=price,
                currency=currency,
                in_stock=in_stock,
                image_url="https://example.test/casque.jpg",
                deep_link=f"https://example.test/{product_id}",
                is_canonical=True,
                is_adult=False,
                updated_at=updated_at,
            )

        created_offers = [
                offer("missing", 30.0, None),
                offer("blank", 31.0, "   "),
                offer("placeholder", 32.0, "unknown"),
                offer("no-currency-code", 33.0, "XXX"),
                offer("gbp", 40.0, "GBP"),
                offer("eur", 90.0, "EUR"),
                offer("eur-normalized", 95.0, " eur "),
                offer("infinite", float("inf"), "EUR"),
                offer("nan", float("nan"), "EUR"),
                offer("zero", 0.0, "EUR"),
                offer("negative", -1.0, "EUR"),
                offer("out-of-stock", 80.0, "EUR", in_stock=False),
                offer("stock-unknown", 80.0, "EUR", in_stock=None),
                offer("stale", 80.0, "EUR", updated_at=now - timedelta(hours=73)),
            ]
        session.add_all(created_offers)
        await session.flush()
        for created in created_offers:
            currency = normalize_currency_code(created.currency)
            if (
                created.price is not None
                and math.isfinite(created.price)
                and created.price > 0
            ):
                session.add(
                    models.PriceSnapshot(
                        offer_id=created.id,
                        price=created.price,
                        currency=currency,
                        in_stock=created.in_stock,
                        captured_at=created.updated_at,
                    )
                )
        await session.commit()

    async def unresolved_intent(query):
        return GeneralIntent(
            raw_request=query,
            locale="fr",
            scopes=(),
            terms=("casque",),
            required_title_phrases=(),
            budget_eur=None,
        )

    monkeypatch.setattr(catalog_search, "resolve_intent_with_fallback", unresolved_intent)

    yield

    db._engine, db._sessionmaker = previous
    await engine.dispose()


@pytest.mark.anyio
async def test_legacy_catalogue_excludes_absent_and_placeholder_currencies(legacy_catalogue):
    products = await catalog_search.search_internal_products("casque audio", None)

    assert {product["offer_id"] for product in products}  # IDs réels, non synthétiques.
    assert {product["currency"] for product in products} == {"EUR", "GBP"}
    assert {product["name"].rsplit(" ", 1)[-1] for product in products} == {
        "eur",
        "eur-normalized",
        "gbp",
    }


@pytest.mark.anyio
async def test_legacy_catalogue_applies_euro_budget_only_to_euro_offers(legacy_catalogue):
    too_small = await catalog_search.search_internal_products("casque audio", 50)
    sufficient = await catalog_search.search_internal_products("casque audio", 100)

    # L'offre GBP à 40 et les offres sans devise ne passent jamais pour des
    # montants EUR sous le budget.
    assert too_small == []
    assert {product["currency"] for product in sufficient} == {"EUR"}
    assert {product["price"] for product in sufficient} == {90, 95}


@pytest.mark.anyio
async def test_grouped_product_aggregates_are_scoped_by_normalized_currency():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    async with sessionmaker() as session:
        merchants = [
            models.Merchant(awin_mid=9101 + index, name=f"Marchand {index}", slug=f"marchand-{index}")
            for index in range(5)
        ]
        session.add_all(merchants)
        product = models.CatalogProduct(
            ean="1234567890123",
            name="Casque groupé",
            brand="Test",
            # Ces projections sont volontairement multidevises et fausses pour
            # prouver que `_decisions_for_offers` ne les consulte plus.
            price_min=80.0,
            price_max=100.0,
            currency="GBP",
            merchants_count=3,
            offers_count=3,
        )
        session.add(product)
        await session.flush()
        now = datetime.now(UTC).replace(tzinfo=None)

        def grouped_offer(
            index: int,
            price: float,
            currency: str,
            *,
            is_canonical: bool = True,
            is_adult: bool = False,
        ):
            return models.Offer(
                merchant_id=merchants[index].id,
                product_id=product.id,
                awin_product_id=f"grouped-{index}",
                ean=product.ean,
                name="Casque audio groupé",
                brand="Test",
                category="Headphones",
                filon_category=taxonomy.TV_SON,
                filon_subcategory="Casques audio",
                offer_kind=taxonomy.PHYSICAL_PRODUCT,
                price=price,
                currency=currency,
                in_stock=True,
                image_url="https://example.test/casque.jpg",
                deep_link=f"https://example.test/{index}",
                is_canonical=is_canonical,
                is_adult=is_adult,
                updated_at=now,
            )

        eur_expensive = grouped_offer(0, 100.0, "EUR")
        eur_best = grouped_offer(1, 90.0, " eur ")
        gbp = grouped_offer(2, 80.0, "GBP")
        duplicate = grouped_offer(3, 1.0, "EUR", is_canonical=False)
        adult = grouped_offer(4, 2.0, "EUR", is_adult=True)
        grouped = (eur_expensive, eur_best, gbp, duplicate, adult)
        session.add_all(grouped)
        await session.flush()
        session.add_all(
            [
                models.PriceSnapshot(
                    offer_id=offer.id,
                    price=offer.price,
                    currency=normalize_currency_code(offer.currency),
                    in_stock=True,
                    captured_at=now,
                )
                for offer in grouped
            ]
        )
        await session.flush()

        decisions = await catalog_search._decisions_for_offers(
            session, [eur_expensive, eur_best, gbp]
        )

        expensive_facts = decisions[eur_expensive.id]["facts"]
        expensive_comparison = next(
            signal
            for signal in decisions[eur_expensive.id]["signals"]
            if signal["key"] == "comparison"
        )
        best_facts = decisions[eur_best.id]["facts"]
        gbp_comparison = next(
            signal
            for signal in decisions[gbp.id]["signals"]
            if signal["key"] == "comparison"
        )

        assert expensive_facts["currency"] == "EUR"
        assert expensive_facts["merchants_compared"] == 2
        assert expensive_facts["offers_compared"] == 2
        assert expensive_comparison["status"] == "warning"
        assert expensive_comparison["cheapest_elsewhere"] == 90.0
        assert best_facts["currency"] == "EUR"
        assert best_facts["merchants_compared"] == 2
        assert gbp_comparison == {
            "key": "comparison",
            "status": "unknown",
            "merchants_count": 1,
        }

    await engine.dispose()


@pytest.mark.anyio
async def test_currencyless_price_snapshots_never_create_a_favourable_history_verdict():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    async with sessionmaker() as session:
        merchant = models.Merchant(awin_mid=9201, name="Historique", slug="historique")
        session.add(merchant)
        await session.flush()
        now = datetime.now(UTC).replace(tzinfo=None)
        offer = models.Offer(
            merchant_id=merchant.id,
            awin_product_id="history-without-currency",
            name="Casque audio avec historique legacy",
            brand="Test",
            category="Headphones",
            filon_category=taxonomy.TV_SON,
            filon_subcategory="Casques audio",
            offer_kind=taxonomy.PHYSICAL_PRODUCT,
            price=50.0,
            currency="EUR",
            in_stock=True,
            image_url="https://example.test/casque.jpg",
            deep_link="https://example.test/history",
            is_canonical=True,
            is_adult=False,
            updated_at=now,
        )
        session.add(offer)
        await session.flush()
        session.add_all(
            [
                models.PriceSnapshot(
                    offer_id=offer.id,
                    price=100.0,
                    in_stock=True,
                    captured_at=now - timedelta(days=10 - index * 2),
                )
                for index in range(6)
            ]
        )
        await session.flush()

        result = (await catalog_search._decisions_for_offers(session, [offer]))[offer.id]

        assert result["price_verdict"]["level"] == "insuffisant"
        assert result["price_verdict"]["samples"] == 0
        history_signal = next(
            signal for signal in result["signals"] if signal["key"] == "price_moment"
        )
        assert history_signal["status"] == "unknown"
        assert history_signal["samples"] == 0

    await engine.dispose()
