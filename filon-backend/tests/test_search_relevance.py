"""Le cas « iphone 16 » — non-régression du départage de pertinence.

Mesuré en production sur `/catalog/offers?q=iphone+16` : les quatre premiers
résultats étaient des protections d'écran à 0,49 €, et aucun téléphone
n'apparaissait avant la dixième position. La cause n'était ni le filtre, ni les
paliers de pertinence — les deux fonctionnaient. C'était le *départage* à
l'intérieur d'un palier, qui se faisait par prix croissant.

Un accessoire porte le nom du produit qu'il accessoirise : « Coque iPhone 16 »
contient « iphone 16 » aussi littéralement que le téléphone. Les deux tombent
donc au même palier, et le moins cher gagne — c'est-à-dire l'accessoire, dans
toutes les catégories où il en existe. Trier la pertinence par le prix revient à
garantir ce résultat.

Ces tests reconstituent la situation exacte et vérifient la propriété qui
compte : le produit cherché sort avant ses accessoires, sans que les accessoires
disparaissent pour autant.
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.routes.catalog import offers as offers_endpoint
from app.db import models
from app.db.base import Base
from app.services.catalog_grouping import rebuild_products
from app.services.search import accessory_penalty, order_columns, query_wants_accessories
from tests.endpoint_call import call

# EAN valides (chiffre de contrôle correct) — le regroupement les vérifie.
EAN_PHONE = "4006381333931"
EAN_CASE = "5901234123457"


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as s:
        a = models.Merchant(awin_mid=1, name="Boutique A", slug="a")
        b = models.Merchant(awin_mid=2, name="Boutique B", slug="b")
        s.add_all([a, b])
        await s.flush()

        def offer(m, pid, name, price, *, brand=None, ean=None):
            return models.Offer(
                merchant_id=m.id,
                awin_product_id=pid,
                name=name,
                brand=brand,
                price=price,
                currency="EUR",
                ean=ean,
                image_url="https://example.test/i.jpg",
                deep_link="https://example.test/go",
                is_canonical=True,
            )

        # Le téléphone, chez deux marchands sous le même EAN : un produit réel.
        s.add(offer(a, "p1", "Apple iPhone 16 128 Go Noir", 969.0,
                    brand="Apple", ean=EAN_PHONE))
        s.add(offer(b, "p2", "Apple iPhone 16 128 Go Noir", 949.0,
                    brand="Apple", ean=EAN_PHONE))
        # Les accessoires : moins chers, un seul marchand, libellés plus longs.
        s.add(offer(a, "a1", "Protection écran verre trempé pour iPhone 16", 0.49))
        s.add(offer(a, "a2", "Coque silicone iPhone 16 transparente antichoc", 0.99))
        s.add(offer(b, "a3", "Étui portefeuille iPhone 16 cuir synthétique", 2.49))
        s.add(offer(b, "a4", "Câble USB-C compatible avec iPhone 16", 1.99,
                    ean=EAN_CASE))
        await s.commit()
        await rebuild_products(s)
        yield s
    await engine.dispose()


async def _search(session, q, **kw):
    return await call(offers_endpoint, q=q, session=session, **kw)


class TestLeProduitPasseAvantSesAccessoires:
    async def test_le_telephone_sort_en_premier(self, session):
        """Le cas exact mesuré en production."""
        res = await _search(session, "iphone 16")
        premier = res["items"][0]["name"].lower()
        assert "iphone 16" in premier
        assert "coque" not in premier and "protection" not in premier

    async def test_les_deux_offres_du_telephone_precedent_les_accessoires(self, session):
        res = await _search(session, "iphone 16")
        noms = [i["name"].lower() for i in res["items"]]
        derniere_offre_telephone = max(
            i for i, n in enumerate(noms) if n.startswith("apple iphone")
        )
        premier_accessoire = min(
            i for i, n in enumerate(noms)
            if any(m in n for m in ("coque", "protection", "etui", "étui", "cable", "câble"))
        )
        assert derniere_offre_telephone < premier_accessoire

    async def test_le_prix_le_plus_bas_ne_gagne_plus(self, session):
        """La protection à 0,49 € était première ; elle ne doit plus l'être."""
        res = await _search(session, "iphone 16")
        assert res["items"][0]["price"] != 0.49

    async def test_les_accessoires_restent_dans_les_resultats(self, session):
        """Reléguer n'est pas exclure : l'utilisateur doit pouvoir les trouver."""
        res = await _search(session, "iphone 16")
        assert res["total"] == 6
        noms = " ".join(i["name"].lower() for i in res["items"])
        assert "coque" in noms and "protection" in noms


class TestLaRequeteAccessoireEstRespectee:
    async def test_chercher_une_coque_rend_des_coques(self, session):
        """Le malus s'annule dès que la requête nomme l'accessoire."""
        res = await _search(session, "coque iphone 16")
        assert res["total"] >= 1
        assert "coque" in res["items"][0]["name"].lower()

    async def test_la_penalite_ne_sapplique_pas_a_ces_requetes(self):
        assert accessory_penalty("coque iphone") is None
        assert accessory_penalty("protection ecran") is None
        assert accessory_penalty("chargeurs") is None       # pluriel absorbé
        assert accessory_penalty("verre trempe iphone") is None

    async def test_elle_sapplique_aux_requetes_de_produit(self):
        assert accessory_penalty("iphone 16") is not None
        assert accessory_penalty("lave linge") is not None

    def test_detection_de_lintention_accessoire(self):
        assert query_wants_accessories("coque samsung") is True
        assert query_wants_accessories("étui cuir") is True
        assert query_wants_accessories("iphone 16") is False
        assert query_wants_accessories("") is False
        assert query_wants_accessories(None) is False


class TestLaConcurrenceMarchandeDepartage:
    async def test_le_produit_multi_marchand_passe_devant(self, session):
        """Deux libellés au même palier : celui vendu par plusieurs marchands gagne.

        C'est le signal central du correctif. Un EAN partagé par plusieurs
        marchands décrit un produit réel et comparable ; un article vendu par un
        seul marchand sous un libellé bavard est presque toujours périphérique.
        """
        res = await _search(session, "apple")
        assert res["items"][0]["name"].startswith("Apple iPhone")

    def test_le_tri_reste_utilisable_sans_jointure(self):
        """Un appelant qui ne joint pas `catalog_products` obtient un tri correct."""
        colonnes = order_columns("iphone 16")
        assert colonnes                       # non vide
        colonnes_jointes = order_columns(
            "iphone 16", merchants_count=models.CatalogProduct.merchants_count
        )
        assert len(colonnes_jointes) == len(colonnes) + 1

    def test_une_requete_vide_ne_produit_aucun_tri(self):
        assert order_columns("") == []
        assert order_columns(None) == []


class TestLibellesQuiNeDoiventPasEtrePenalises:
    """Un faux positif enterre un vrai produit : la liste doit rester étroite."""

    @pytest.mark.parametrize(
        "libelle",
        [
            "Housse de couette percale 240x220",   # linge de maison, pas accessoire
            "Soutien-gorge à armatures",           # « support » absent de la liste
            "Casserole inox 20 cm",                # ne doit pas matcher « case »
            "Machine à café Delonghi",
        ],
    )
    async def test_ces_libelles_ne_sont_pas_lus_comme_des_accessoires(
        self, session, libelle
    ):
        m = (await session.execute(
            models.Merchant.__table__.select().limit(1)
        )).first()
        session.add(
            models.Offer(
                merchant_id=m.id, awin_product_id=f"x-{libelle[:8]}", name=libelle,
                price=49.0, currency="EUR", image_url="https://example.test/i.jpg",
                is_canonical=True,
            )
        )
        await session.commit()
        # Recherché par son propre nom, l'article doit sortir premier.
        premier_mot = libelle.split()[0]
        res = await _search(session, premier_mot)
        assert res["items"][0]["name"] == libelle
