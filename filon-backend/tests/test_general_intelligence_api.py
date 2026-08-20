from datetime import datetime, timezone

import pytest

from app.api.routes import intelligence
from app.intelligence.contracts import CoreOfferSnapshot
from app.services import taxonomy


class FakeSession:
    def __init__(self):
        self.added = []
        self.committed = False

    def add(self, value):
        self.added.append(value)

    async def commit(self):
        self.committed = True


@pytest.mark.asyncio
async def test_outfit_non_mode_utilise_le_moteur_general(monkeypatch):
    session = FakeSession()
    used = {"general": False, "fashion": False}
    offer = CoreOfferSnapshot(
        offer_id=1,
        catalog_product_id=None,
        name="Tennis shirt adulte",
        brand="Test",
        filon_category=taxonomy.SPORT,
        filon_subcategory="Vêtements de sport",
        offer_kind=taxonomy.PHYSICAL_PRODUCT,
        price=40.0,
        currency="EUR",
        availability="in_stock",
        image_url="https://example.test/item.jpg",
        deep_link="https://example.test/item",
        merchant_id=1,
        merchant_name="Test",
        merchant_region="BE",
        observed_at=datetime.now(timezone.utc),
    )

    async def general_retrieval(_session, _intent):
        used["general"] = True
        return [offer]

    async def fashion_retrieval(*_args, **_kwargs):
        used["fashion"] = True
        return []

    monkeypatch.setattr(intelligence, "retrieve_general_offers", general_retrieval)
    monkeypatch.setattr(intelligence, "retrieve_fashion_offers", fashion_retrieval)
    monkeypatch.setattr(intelligence, "intelligence_capabilities", lambda: {"intelligence": True, "fashion_expert": True, "outfit_studio": True})

    response = await intelligence.outfit_analyse(
        intelligence.OutfitAnalyseRequest(request="tenniskleding onder 100 €", locale="nl"),
        session=session,
    )

    assert used == {"general": True, "fashion": False}
    assert response["domain"] == "general"
    assert response["solution"]["decision"] == "recommend"
    assert session.committed is True


@pytest.mark.asyncio
async def test_outfit_non_vestimentaire_non_resolu_s_abstient_dans_le_moteur_general(monkeypatch):
    from app.intelligence.intent_resolution import GeneralIntent

    session = FakeSession()
    used = {"general": False, "fashion": False}

    async def unresolved_intent(_request, _locale):
        return GeneralIntent(
            raw_request="hardloophorloge onder 250 euro",
            locale="nl",
            scopes=(),
            terms=("hardloophorloge",),
            required_title_phrases=(),
            budget_eur=250.0,
        )

    async def general_retrieval(_session, _intent):
        used["general"] = True
        return []

    async def fashion_retrieval(*_args, **_kwargs):
        used["fashion"] = True
        return []

    monkeypatch.setattr(intelligence, "resolve_intent_with_fallback", unresolved_intent)
    monkeypatch.setattr(intelligence, "retrieve_general_offers", general_retrieval)
    monkeypatch.setattr(intelligence, "retrieve_fashion_offers", fashion_retrieval)
    monkeypatch.setattr(intelligence, "intelligence_capabilities", lambda: {"intelligence": True, "fashion_expert": True, "outfit_studio": True})

    response = await intelligence.outfit_analyse(
        intelligence.OutfitAnalyseRequest(request="hardloophorloge onder 250 euro", locale="nl"),
        session=session,
    )

    assert used == {"general": True, "fashion": False}
    assert response["domain"] == "general"
    assert response["solution"]["decision"] == "abstain"
