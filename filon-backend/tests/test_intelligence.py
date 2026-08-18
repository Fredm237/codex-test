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
from app.intelligence.contracts import CoreOfferSnapshot
from app.intelligence.fashion import compose_outfit, parse_fashion_intent, retrieval_query_for_intent
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
            # Une offre antérieure au marquage adulte doit rester visible,
            # exactement comme dans le catalogue public.
            is_adult=None,
            price=89.0,
            currency="EUR",
            in_stock=True,
            image_url="https://example.test/veste.jpg",
            deep_link="https://example.test/veste",
        )
        false_positive = models.Offer(
            merchant_id=merchant.id,
            awin_product_id="ko-wardrobe-accessory",
            name="Accessoire de garde-robe mural",
            filon_category=taxonomy.MODE_FEMME,
            filon_subcategory="Robes",
            offer_kind=taxonomy.PHYSICAL_PRODUCT,
            is_canonical=True,
            is_adult=False,
            price=4.3,
            currency="EUR",
            in_stock=True,
            image_url="https://example.test/garde-robe.jpg",
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
        intelligence_session.add_all([eligible, false_positive, service, unavailable])
        await intelligence_session.commit()

        snapshots = await retrieve_fashion_offers(intelligence_session, query="veste")

        assert [item.offer_id for item in snapshots] == [eligible.id]
        assert snapshots[0].price_evidence.status == "verified"
        assert snapshots[0].availability_evidence.status == "verified"
        assert snapshots[0].as_dict()["merchant"]["name"] == "Marchand test"

    async def test_exige_une_preuve_lexicale_de_piece_dans_le_sous_rayon(self, intelligence_session):
        merchant = models.Merchant(awin_mid=903, name="Marchand robes", slug="marchand-robes")
        intelligence_session.add(merchant)
        await intelligence_session.flush()
        dress = models.Offer(
            merchant_id=merchant.id,
            awin_product_id="dress-1",
            name="Robe de soirée portefeuille",
            filon_category=taxonomy.MODE_FEMME,
            filon_subcategory="Robes",
            offer_kind=taxonomy.PHYSICAL_PRODUCT,
            is_canonical=True,
            is_adult=False,
            price=95.0,
            currency="EUR",
            in_stock=True,
            image_url="https://example.test/robe.jpg",
        )
        wardrobe_accessory = models.Offer(
            merchant_id=merchant.id,
            awin_product_id="wardrobe-1",
            name="Accessoire de garde-robe mural",
            filon_category=taxonomy.MODE_FEMME,
            filon_subcategory="Robes",
            offer_kind=taxonomy.PHYSICAL_PRODUCT,
            is_canonical=True,
            is_adult=False,
            price=4.3,
            currency="EUR",
            in_stock=True,
            image_url="https://example.test/accessoire.jpg",
        )
        intelligence_session.add_all([dress, wardrobe_accessory])
        await intelligence_session.commit()

        snapshots = await retrieve_fashion_offers(intelligence_session, query="robe")

        assert [item.offer_id for item in snapshots] == [dress.id]

    async def test_filtre_le_mariage_seulement_lorsqu_il_est_explicitement_prouve(self, intelligence_session):
        merchant = models.Merchant(awin_mid=904, name="Marchand cérémonie", slug="marchand-ceremonie")
        intelligence_session.add(merchant)
        await intelligence_session.flush()
        wedding_dress = models.Offer(
            merchant_id=merchant.id,
            awin_product_id="wedding-dress-1",
            name="Wedding Dress White Bridal Ceremony",
            filon_category=taxonomy.MODE_FEMME,
            filon_subcategory="Robes",
            offer_kind=taxonomy.PHYSICAL_PRODUCT,
            is_canonical=True,
            is_adult=False,
            price=140.0,
            currency="EUR",
            in_stock=True,
            image_url="https://example.test/wedding-dress.jpg",
        )
        wedding_jewellery = models.Offer(
            merchant_id=merchant.id,
            awin_product_id="wedding-jewellery-not-dress",
            name="Bridal Wedding Jewellery Set Pearl Necklace Earrings Costume Dress Prom",
            filon_category=taxonomy.MODE_FEMME,
            filon_subcategory="Robes",
            offer_kind=taxonomy.PHYSICAL_PRODUCT,
            is_canonical=True,
            is_adult=False,
            price=5.14,
            currency="EUR",
            in_stock=True,
            image_url="https://example.test/wedding-jewellery.jpg",
        )
        wedding_underwear = models.Offer(
            merchant_id=merchant.id,
            awin_product_id="wedding-underwear-not-dress",
            name="Thin Breathable Invisible Bra Ladies Push-Up Underwear Strapless Wedding Dress Bra",
            filon_category=taxonomy.MODE_FEMME,
            filon_subcategory="Robes",
            offer_kind=taxonomy.PHYSICAL_PRODUCT,
            is_canonical=True,
            is_adult=False,
            price=10.15,
            currency="EUR",
            in_stock=True,
            image_url="https://example.test/wedding-underwear.jpg",
        )
        wedding_shapewear = models.Offer(
            merchant_id=merchant.id,
            awin_product_id="wedding-shapewear-not-dress",
            name="Women's clothing zipper body shaper tummy control corset bridal dress palace waist wedding dress corset",
            filon_category=taxonomy.MODE_FEMME,
            filon_subcategory="Robes",
            offer_kind=taxonomy.PHYSICAL_PRODUCT,
            is_canonical=True,
            is_adult=False,
            price=11.92,
            currency="EUR",
            in_stock=True,
            image_url="https://example.test/wedding-shapewear.jpg",
        )
        ordinary_dress = models.Offer(
            merchant_id=merchant.id,
            awin_product_id="ordinary-dress-1",
            name="Robe camisole femme",
            filon_category=taxonomy.MODE_FEMME,
            filon_subcategory="Robes",
            offer_kind=taxonomy.PHYSICAL_PRODUCT,
            is_canonical=True,
            is_adult=False,
            price=30.0,
            currency="EUR",
            in_stock=True,
            image_url="https://example.test/ordinary-dress.jpg",
        )
        intelligence_session.add_all([
            wedding_dress, wedding_jewellery, wedding_underwear, wedding_shapewear, ordinary_dress
        ])
        await intelligence_session.commit()

        snapshots = await retrieve_fashion_offers(intelligence_session, query="robe", occasion="wedding")

        assert [item.offer_id for item in snapshots] == [wedding_dress.id]

    async def test_mariage_sans_piece_explicite_retrouve_une_robe_prouvee(self, intelligence_session):
        merchant = models.Merchant(awin_mid=905, name="Marchand mariage", slug="marchand-mariage")
        intelligence_session.add(merchant)
        await intelligence_session.flush()
        wedding_dress = models.Offer(
            merchant_id=merchant.id,
            awin_product_id="wedding-dress-fallback",
            name="Robe de mariage bridal ivoire",
            filon_category=taxonomy.MODE_FEMME,
            filon_subcategory="Robes",
            offer_kind=taxonomy.PHYSICAL_PRODUCT,
            is_canonical=True,
            is_adult=False,
            price=150.0,
            currency="EUR",
            in_stock=True,
            image_url="https://example.test/wedding-fallback.jpg",
        )
        ordinary_dress = models.Offer(
            merchant_id=merchant.id,
            awin_product_id="ordinary-dress-fallback",
            name="Robe estivale femme",
            filon_category=taxonomy.MODE_FEMME,
            filon_subcategory="Robes",
            offer_kind=taxonomy.PHYSICAL_PRODUCT,
            is_canonical=True,
            is_adult=False,
            price=35.0,
            currency="EUR",
            in_stock=True,
            image_url="https://example.test/ordinary-fallback.jpg",
        )
        intelligence_session.add_all([wedding_dress, ordinary_dress])
        await intelligence_session.commit()

        snapshots = await retrieve_fashion_offers(intelligence_session, query=None, occasion="wedding")

        assert [item.offer_id for item in snapshots] == [wedding_dress.id]

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


class TestFashionExpert:
    @staticmethod
    def _offer(
        offer_id: int,
        name: str,
        category: str,
        price: float,
        *,
        stock: str = "in_stock",
    ) -> CoreOfferSnapshot:
        return CoreOfferSnapshot(
            offer_id=offer_id,
            catalog_product_id=None,
            name=name,
            brand="Test",
            filon_category=category,
            filon_subcategory=None,
            offer_kind=taxonomy.PHYSICAL_PRODUCT,
            price=price,
            currency="EUR",
            availability=stock,  # type: ignore[arg-type]
            image_url=f"https://example.test/{offer_id}.jpg",
            deep_link=f"https://example.test/{offer_id}",
            merchant_id=1,
            merchant_name="Marchand test",
            merchant_region="BE",
            observed_at=None,
        )

    def test_compose_une_solution_sous_budget_avec_offres_reelles(self):
        intent = parse_fashion_intent("Un look de mariage sous 200 €", "create")
        result = compose_outfit(
            intent,
            [
                self._offer(1, "Robe de cérémonie", taxonomy.MODE_FEMME, 120.0),
                self._offer(2, "Chaussures de cérémonie", taxonomy.CHAUSSURES, 60.0),
                self._offer(3, "Sac soirée", taxonomy.ACCESSOIRES, 40.0),
            ],
        )

        assert result["decision"] == "recommend"
        assert result["total_known_price"] == {"amount": 180.0, "currency": "EUR", "scope": "items_only"}
        assert [item["role"] for item in result["items"]] == ["base", "footwear"]
        assert "delivery_unknown" in result["unknowns"]
        assert "within_known_budget" in result["rationale_keys"]

    def test_ne_combine_pas_un_complement_de_genre_explicitement_incompatible(self):
        intent = parse_fashion_intent("Une robe de mariage sous 200 € avec chaussures", "create")
        result = compose_outfit(
            intent,
            [
                self._offer(1, "Robe femme de cérémonie", taxonomy.MODE_FEMME, 120.0),
                self._offer(2, "Chaussures homme de running", taxonomy.CHAUSSURES, 20.0),
                self._offer(4, "Chaussures basket-ball femme", taxonomy.CHAUSSURES, 25.0),
                self._offer(3, "Chaussures femme de cérémonie", taxonomy.CHAUSSURES, 60.0),
            ],
        )

        assert result["decision"] == "recommend"
        assert [item["offer_id"] for item in result["items"]] == [1, 3]
        assert "style_compatibility_not_verified" in result["unknowns"]
        assert "occasion_not_verified" in result["unknowns"]

    def test_s_abstient_lorsqu_aucune_base_verifiee_n_est_disponible(self):
        intent = parse_fashion_intent("Une tenue de travail", "create")
        result = compose_outfit(intent, [self._offer(2, "Chaussures", taxonomy.CHAUSSURES, 60.0)])

        assert result["decision"] == "abstain"
        assert result["rejection_reason"] == "no_verified_base"

    def test_ne_transmet_pas_une_occasion_au_retrieval_comme_nom_produit(self):
        assert retrieval_query_for_intent("Un look de mariage sous 200 €") is None
        assert retrieval_query_for_intent("Une robe de mariage sous 200 €") == "robe"
