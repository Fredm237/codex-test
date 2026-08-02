"""Cohérence par marchand.

Le classement par mots-clés compte plus de quatre cents tokens courts, chacun
étant une porte d'entrée pour un faux positif. Les corriger un par un n'a pas
de fin — « souris » n'en était qu'un.

Le marchand est un signal bien plus fiable, et il n'était pas utilisé : quand
95 % du catalogue d'un vendeur tombe dans un rayon, une offre isolée classée
ailleurs est presque toujours une erreur de mot-clé.

Ces tests vérifient les deux cas limites : le spécialiste doit être reconnu,
le généraliste ne doit jamais l'être.
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import models
from app.db.base import Base
from app.services import coherence


async def _peupler(session, marchand: models.Merchant, repartition: dict[str, int]):
    n = 0
    for categorie, combien in repartition.items():
        for _ in range(combien):
            n += 1
            session.add(
                models.Offer(
                    merchant_id=marchand.id,
                    awin_product_id=f"{marchand.slug}-{n}",
                    name=f"Article {n}",
                    price=10.0,
                    currency="EUR",
                    image_url="https://e.test/i.jpg",
                    filon_category=categorie,
                )
            )


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as s:
        yield s
    await engine.dispose()


async def _merchant(session, slug: str, mid: int) -> models.Merchant:
    m = models.Merchant(awin_mid=mid, name=slug, slug=slug)
    session.add(m)
    await session.flush()
    return m


class TestSpecialiste:
    async def test_le_rayon_dominant_est_reconnu(self, session):
        """TISSUS DE REVE : 95 mercerie, 5 égarées par des mots-clés."""
        m = await _merchant(session, "tissus-de-reve", 1)
        await _peupler(session, m, {
            "Loisirs créatifs": 95,
            "Informatique": 2,      # « gris souris »
            "Auto & Moto": 2,       # « motif voitures »
            "Animalerie": 1,        # « chiens et chats »
        })
        await session.commit()

        profils = await coherence.merchant_profiles(session)
        assert profils[m.id].rayon == "Loisirs créatifs"

    async def test_les_egarees_sont_ramenees(self, session):
        m = await _merchant(session, "tissus-de-reve", 1)
        await _peupler(session, m, {
            "Loisirs créatifs": 95, "Informatique": 2,
            "Auto & Moto": 2, "Animalerie": 1,
        })
        await session.commit()

        res = await coherence.realign(session)
        assert res["offres_realignees"] == 5
        assert res["merchants_specialises"] == 1

    async def test_la_simulation_ne_touche_a_rien(self, session):
        """Indispensable avant de modifier 795 000 lignes."""
        m = await _merchant(session, "acer", 2)
        await _peupler(session, m, {
            "Informatique": 90, "Maison & Déco": 4, "Animalerie": 3, "Mode femme": 3,
        })
        await session.commit()

        avant = await coherence.realign(session, dry_run=True)
        assert avant["offres_realignees"] == 10

        profils = await coherence.merchant_profiles(session)
        assert profils[m.id].rayon == "Informatique"

    async def test_la_simulation_dit_d_ou_viennent_les_offres(self, session):
        """« 24 369 offres » est invérifiable sans savoir chez qui."""
        m = await _merchant(session, "tissus-de-reve", 3)
        await _peupler(session, m, {
            "Loisirs créatifs": 95, "Informatique": 2, "Auto & Moto": 2, "Animalerie": 1,
        })
        await session.commit()

        res = await coherence.realign(session, dry_run=True)
        assert res["detail"] == [
            {
                "merchant": "tissus-de-reve",
                "vers": "Loisirs créatifs",
                "offres": 5,
                "sur": 100,
                "rayons_proteges": [],
            }
        ]


class TestGeneraliste:
    async def test_un_generaliste_nest_jamais_realigne(self, session):
        """Le garde-fou essentiel : sans lui, Amazon verrait tout son catalogue
        écrasé dans son rayon le plus fourni."""
        m = await _merchant(session, "amazon", 3)
        await _peupler(session, m, {
            "Informatique": 30, "Mode femme": 25, "Maison & Déco": 20,
            "Jeux & Jouets": 15, "Animalerie": 10,
        })
        await session.commit()

        assert await coherence.merchant_profiles(session) == {}
        res = await coherence.realign(session)
        assert res["offres_realignees"] == 0


class TestSecondeActivite:
    """Toute la règle suppose que la minorité est faite d'erreurs de mots-clés.

    Or une erreur de mot-clé est *dispersée*. Une minorité concentrée dans un
    seul rayon est une seconde activité : YesStyle vend de la beauté à 90 %, et
    le reste est de la mode coréenne — 4 000 articles réels, qu'un réalignement
    aveugle enterrerait en parfumerie.
    """

    async def test_un_rayon_secondaire_fourni_est_protege(self, session):
        m = await _merchant(session, "yesstyle", 10)
        await _peupler(session, m, {
            "Beauté & Parfum": 906,   # l'activité principale
            "Mode femme": 84,          # la seconde, bien réelle
            "Informatique": 5,         # dispersé : du bruit
            "Animalerie": 5,
        })
        await session.commit()

        profils = await coherence.merchant_profiles(session)
        assert profils[m.id].proteges == frozenset({"Mode femme"})

        res = await coherence.realign(session)
        # Les 84 de mode restent ; seules les dix dispersées sont ramenées.
        assert res["offres_realignees"] == 10

    async def test_une_minorite_dispersee_bouge_toujours(self, session):
        """Le garde-fou ne doit pas neutraliser la règle elle-même."""
        m = await _merchant(session, "tissus", 11)
        await _peupler(session, m, {
            "Loisirs créatifs": 950,
            "Informatique": 20, "Auto & Moto": 20, "Animalerie": 10,
        })
        await session.commit()
        assert (await coherence.realign(session))["offres_realignees"] == 50


class TestRayonFourreTout:
    """« Accessoires » se déclenche sur le mot « accessoire » lui-même.

    Un vendeur de déshumidificateurs dont les libellés disent « accessoire
    pour… » y tombe à 90 % — mesuré sur Trotec. La dominance est réelle ; ce
    qu'elle mesure ne l'est pas, et y ramener le reste enterrerait les seules
    offres correctement classées.
    """

    async def test_accessoires_ne_peut_pas_etre_une_destination(self, session):
        m = await _merchant(session, "trotec", 12)
        await _peupler(session, m, {"Accessoires": 90, "Maison & Déco": 10})
        await session.commit()

        assert await coherence.merchant_profiles(session) == {}
        assert (await coherence.realign(session))["offres_realignees"] == 0

    async def test_mais_reste_un_rayon_valable_pour_une_offre(self, session):
        """Interdire la destination n'interdit pas le rayon."""
        m = await _merchant(session, "mode", 13)
        await _peupler(session, m, {"Mode femme": 90, "Accessoires": 10})
        await session.commit()
        assert (await coherence.merchant_profiles(session))[m.id].rayon == "Mode femme"


class TestGardeFous:
    async def test_un_petit_marchand_est_ignore(self, session):
        """Douze articles ne suffisent pas à établir une spécialité."""
        m = await _merchant(session, "petit", 4)
        await _peupler(session, m, {"Informatique": 10, "Maison & Déco": 2})
        await session.commit()
        assert await coherence.merchant_profiles(session) == {}

    async def test_les_offres_non_classees_restent_libres(self, session):
        """Une offre sans rayon relève du classement, pas de la cohérence."""
        m = await _merchant(session, "acer", 5)
        await _peupler(session, m, {"Informatique": 80})
        for i in range(20):
            session.add(models.Offer(
                merchant_id=m.id, awin_product_id=f"nc-{i}", name="Inconnu",
                price=1.0, currency="EUR", image_url="https://e.test/i.jpg",
                filon_category=None,
            ))
        await session.commit()

        res = await coherence.realign(session)
        assert res["offres_realignees"] == 0
