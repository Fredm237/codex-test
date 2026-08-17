"""Contrats de base de la FILON Intelligence Layer.

Ces tests verrouillent l’activation explicite et la lecture uniquement d’offres
Fashion admissibles, sans modifier les tables ou règles du Core.
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.routes import intelligence
from app.core.config import Settings
from app.db import models
from app.db.base import Base
from app.intelligence import models as intelligence_models  # noqa: F401
from app.intelligence.catalog_adapter import retrieve_fashion_offers
from app.services import taxonomy


class TestIntelligenceFlags:
    async def test_les_modules_sont_eteints_par_defaut(self, monkeypatch):
        monkeypatch.setattr(intelligence, "get_settings", lambda: Settings())
        payload = await intelligence.intelligence_status()
        assert payload["enabled"] is False
        assert payload["modules"] == {
            "intelligence": False,
            "fashion_expert": False,
            "outfit_studio": False,
        }

    async def test_outfit_exige_tous_les_flags(self, monkeypatch):
        monkeypatch.setattr(
            intelligence,
            "get_settings",
            lambda: Settings(
                filon_intelligence_enabled=True,
                fashion_expert_enabled=True,
                outfit_studio_enabled=True,
            ),
        )
        payload = await intelligence.intelligence_status()
        assert payload["enabled"] is True
        assert payload["modules"]["outfit_studio"] is True

        monkeypatch.setattr(
            intelligence,
            "get_settings",
            lambda: Settings(
                filon_intelligence_enabled=False,
                fashion_expert_enabled=True,
                outfit_studio_enabled=True,
            ),
        )
        payload = await intelligence.intelligence_status()
        assert payload["modules"]["fashion_expert"] is False
        assert payload["modules"]["outfit_studio"] is False


@pytest.fixture
async def intelligence_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as session:
        yield session
    await engine.dispose()


class TestFashionCatalogAdapter:
    async def test_ne_retient_que_les_offres_physiques_admissibles(self, intelligence_session):
        merchant = models.Merchant(awin_mid=901, name="Marchand test", slug="marchand-test")
        intelligence_session.add(merchant)
        await intelligence_session.flush()
        eligible = models.Offer(
            merchant_id=merchant.id,
            awin_product_id="ok-1",
            name="Veste de cérémonie bleue",
            brand="FILON Test",
            filon_category=taxonomy.MODE_FEMME,
            filon_subcategory="Manteaux & Vestes",
            offer_kind=taxonomy.PHYSICAL_PRODUCT,
            is_canonical=True,
            is_adult=False,
            price=89.0,
            currency="EUR",
            in_stock=True,
            image_url="https://example.test/veste.jpg",
            deep_link="https://example.test/veste",
        )
        service = models.Offer(
            merchant_id=merchant.id,
            awin_product_id="ko-service",
            name="Conseil vestimentaire",
            filon_category=taxonomy.MODE,
            offer_kind=taxonomy.SERVICE,
            is_canonical=True,
            is_adult=False,
            price=10.0,
            currency="EUR",
            in_stock=True,
            image_url="https://example.test/service.jpg",
        )
        unavailable = models.Offer(
            merchant_id=merchant.id,
            awin_product_id="ko-stock",
            name="Chaussures indisponibles",
            filon_category=taxonomy.CHAUSSURES,
            offer_kind=taxonomy.PHYSICAL_PRODUCT,
            is_canonical=True,
            is_adult=False,
            price=70.0,
            currency="EUR",
            in_stock=False,
            image_url="https://example.test/chaussures.jpg",
        )
        intelligence_session.add_all([eligible, service, unavailable])
        await intelligence_session.commit()

        snapshots = await retrieve_fashion_offers(intelligence_session, query="veste")

        assert [item.offer_id for item in snapshots] == [eligible.id]
        assert snapshots[0].price_evidence.status == "verified"
        assert snapshots[0].availability_evidence.status == "verified"
        assert snapshots[0].as_dict()["merchant"]["name"] == "Marchand test"

    async def test_un_stock_inconnu_reste_explicite(self, intelligence_session):
        merchant = models.Merchant(awin_mid=902, name="Marchand inconnu", slug="marchand-inconnu")
        intelligence_session.add(merchant)
        await intelligence_session.flush()
        offer = models.Offer(
            merchant_id=merchant.id,
            awin_product_id="unknown-stock",
            name="Sac en cuir",
            filon_category=taxonomy.ACCESSOIRES,
            offer_kind=taxonomy.PHYSICAL_PRODUCT,
            is_canonical=True,
            is_adult=False,
            price=55.0,
            currency="EUR",
            in_stock=None,
            image_url="https://example.test/sac.jpg",
        )
        intelligence_session.add(offer)
        await intelligence_session.commit()

        snapshots = await retrieve_fashion_offers(intelligence_session, query="sac")

        assert len(snapshots) == 1
        assert snapshots[0].availability == "unknown"
        assert snapshots[0].availability_evidence.status == "unknown"
