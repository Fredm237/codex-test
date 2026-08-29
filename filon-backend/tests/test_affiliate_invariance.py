"""La rémunération ne doit modifier ni la sélection ni le classement Assistant."""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest

from app.intelligence.contracts import CoreOfferSnapshot
from app.intelligence.general_decision import _rank
from app.intelligence.intent_resolution import IntentScope
from app.services import recommend, taxonomy
from app.services.decision import compute_decision


_CURRENT_EVIDENCE_AT = datetime.now(UTC)


class _DeterministicRankingProvider:
    """Capture le contexte classé avant que les liens affiliés soient construits."""

    name = "affiliate-invariance-probe"

    def __init__(self) -> None:
        self.messages: list[tuple[tuple[str, str], ...]] = []
        self.reranking_payloads: list[list[dict[str, Any]]] = []
        self.completed_runs = 0

    async def complete_json(self, messages, *, temperature: float = 0.0) -> str:
        self.messages.append(tuple((message.role, message.content) for message in messages))
        user_message = next(message.content for message in messages if message.role == "user")
        listing = json.loads(user_message.split("Produits réels :\n", maxsplit=1)[1])
        self.reranking_payloads.append(listing)
        self.completed_runs += 1
        return json.dumps(
            {
                "usage": "casque documenté",
                "emoji": "🎧",
                "picks": [
                    {"index": 1, "label": "Premier", "why": "Seconde offre rerankée."},
                    {"index": 0, "label": "Second", "why": "Première offre rerankée."},
                ],
            }
        )


class _DeterministicRouter:
    def __init__(self, provider: _DeterministicRankingProvider) -> None:
        self.provider = provider

    def for_task(self, task: str) -> _DeterministicRankingProvider:
        assert task == "reasoning"
        return self.provider


def _current_decision(price: float) -> dict[str, Any]:
    return compute_decision(
        price=price,
        currency="EUR",
        history=[(price, _CURRENT_EVIDENCE_AT)],
        history_currency="EUR",
        cheapest_elsewhere=price,
        comparison_currency="EUR",
        merchants_count=2,
        offers_count=2,
        in_stock=True,
        now=_CURRENT_EVIDENCE_AT,
    )


def _offers_with_commissions(schedule: dict[str, int]) -> list[dict[str, Any]]:
    """Ajoute une perturbation commerciale contrôlée à des offres inchangées."""

    offers = [
        {
            "offer_id": 101,
            "product_ean": "1111111111111",
            "offer_kind": "physical_product",
            "name": "Casque Bluetooth à réduction de bruit active",
            "price": 119,
            "currency": "EUR",
            "merchant": "Alpha",
            "link": "https://direct.invalid/offer-101",
        },
        {
            "offer_id": 202,
            "product_ean": "2222222222222",
            "offer_kind": "physical_product",
            "name": "Casque Bluetooth sans fil",
            "price": 149,
            "currency": "EUR",
            "merchant": "Beta",
            "link": "https://direct.invalid/offer-202",
        },
    ]
    return [
        {
            **offer,
            "decision": _current_decision(offer["price"]),
            "publisher_commission_bps": schedule[offer["merchant"]],
        }
        for offer in offers
    ]


def _core_offer(offer_id: int, name: str, price: float, link: str) -> CoreOfferSnapshot:
    return CoreOfferSnapshot(
        offer_id=offer_id,
        catalog_product_id=None,
        name=name,
        brand=None,
        filon_category=taxonomy.TV_SON,
        filon_subcategory="Casques audio",
        offer_kind=taxonomy.PHYSICAL_PRODUCT,
        price=price,
        currency="EUR",
        availability="in_stock",
        image_url=None,
        deep_link=link,
        merchant_id=offer_id,
        merchant_name=f"Marchand {offer_id}",
        merchant_region="BE",
        observed_at=None,
    )


def test_core_ranking_contract_excludes_commercial_rates_and_link_variants():
    """Le Core ne reçoit aucun taux et sa clé de rang ignore le lien projeté."""

    commercial_fields = {
        "publisher_commission_bps",
        "commission_bps",
        "affiliate_rate",
        "payout",
        "revenue",
    }
    assert commercial_fields.isdisjoint(CoreOfferSnapshot.__dataclass_fields__)

    scope = IntentScope(
        taxonomy.TV_SON,
        "Casques audio",
        "casque audio",
        ("casque audio",),
    )
    direct = [
        _core_offer(101, "Casque audio Alpha", 119.0, "https://direct.invalid/offer-101"),
        _core_offer(202, "Casque audio Beta", 149.0, "https://direct.invalid/offer-202"),
    ]
    commercially_projected = [
        replace(
            direct[0],
            deep_link="https://affiliate.invalid/alpha?publisher_commission_bps=900",
        ),
        replace(
            direct[1],
            deep_link="https://affiliate.invalid/beta?publisher_commission_bps=1200",
        ),
    ]

    direct_keys = {
        offer.offer_id: _rank(scope, offer, request_terms=())
        for offer in direct
    }
    projected_keys = {
        offer.offer_id: _rank(scope, offer, request_terms=())
        for offer in commercially_projected
    }
    assert direct_keys == projected_keys
    assert sorted(direct_keys, key=direct_keys.get) == sorted(
        projected_keys,
        key=projected_keys.get,
    ) == [101, 202]


@pytest.mark.anyio
async def test_affiliate_invariance_when_commissions_are_inverted(monkeypatch):
    """Inverser les commissions change les liens, jamais le ranking produit."""

    provider = _DeterministicRankingProvider()
    monkeypatch.setattr(
        recommend,
        "get_settings",
        lambda: SimpleNamespace(llm_timeout_seconds=1),
    )
    monkeypatch.setattr(recommend, "get_router", lambda: _DeterministicRouter(provider))

    async def no_advertiser_refresh() -> None:
        return None

    monkeypatch.setattr(recommend.awin, "ensure_advertisers", no_advertiser_refresh)

    current: dict[str, Any] = {"run": 0, "schedule": {}}

    def commercial_link(url: str | None, merchant: str | None = None) -> str | None:
        # La pose commerciale doit intervenir seulement après la complétion du
        # reranking du passage courant.
        assert provider.completed_runs == current["run"]
        if url is None or merchant is None or current["schedule"][merchant] == 0:
            return url
        return (
            f"https://affiliate.invalid/{merchant.lower()}"
            f"?publisher_commission_bps={current['schedule'][merchant]}"
        )

    monkeypatch.setattr(recommend.awin, "affiliate_link", commercial_link)

    async def execute(schedule: dict[str, int]):
        current["run"] += 1
        current["schedule"] = schedule
        products = _offers_with_commissions(schedule)
        result = await recommend._rank_real_products(
            "casque à réduction de bruit",
            200,
            products,
            "fr",
        )
        return result, products

    # Le reranker place Beta en tête alors qu'elle n'est pas rémunérée ; Alpha,
    # moins bien classée, porte la commission la plus forte du premier passage.
    first_schedule = {"Alpha": 900, "Beta": 0}
    first, first_products = await execute(first_schedule)
    second_schedule = {"Alpha": 0, "Beta": 1_200}
    second, second_products = await execute(second_schedule)
    assert {
        product["offer_id"]: product["publisher_commission_bps"]
        for product in first_products
    } == {101: 900, 202: 0}
    assert {
        product["offer_id"]: product["publisher_commission_bps"]
        for product in second_products
    } == {101: 0, 202: 1_200}

    first_ids = [card["offer_id"] for card in first["cards"]]
    second_ids = [card["offer_id"] for card in second["cards"]]
    assert first_ids == second_ids == [202, 101]

    # Le changement commercial est réel, appliqué par offre après le ranking.
    first_links = {card["offer_id"]: card["link"] for card in first["cards"]}
    second_links = {card["offer_id"]: card["link"] for card in second["cards"]}
    assert first_links == {
        202: "https://direct.invalid/offer-202",
        101: "https://affiliate.invalid/alpha?publisher_commission_bps=900",
    }
    assert second_links == {
        202: "https://affiliate.invalid/beta?publisher_commission_bps=1200",
        101: "https://direct.invalid/offer-101",
    }
    assert first_links != second_links

    first_without_links = {
        **first,
        "cards": [
            {key: value for key, value in card.items() if key != "link"}
            for card in first["cards"]
        ],
    }
    second_without_links = {
        **second,
        "cards": [
            {key: value for key, value in card.items() if key != "link"}
            for card in second["cards"]
        ],
    }
    assert first_without_links == second_without_links

    # Les taux contrôlés ont bien été inversés dans les entrées, mais ils sont
    # absents du contexte du reranker et n'en modifient aucune autre donnée.
    assert [
        {key: value for key, value in product.items() if key != "publisher_commission_bps"}
        for product in first_products
    ] == [
        {key: value for key, value in product.items() if key != "publisher_commission_bps"}
        for product in second_products
    ]
    assert first_schedule != second_schedule
    assert provider.messages[0] == provider.messages[1]
    assert provider.reranking_payloads[0] == provider.reranking_payloads[1]
    reranking_context = repr(provider.messages[0]).lower()
    assert "commission" not in reranking_context
    assert "affiliate" not in reranking_context
    assert "payout" not in reranking_context
    assert "revenue" not in reranking_context
