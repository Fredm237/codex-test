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
        assert profils[m.id][0] == "Loisirs créatifs"

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
        await _peupler(session, m, {"Informatique": 90, "Maison & Déco": 10})
        await session.commit()

        avant = await coherence.realign(session, dry_run=True)
        assert avant["offres_realignees"] == 10

        profils = await coherence.merchant_profiles(session)
        assert profils[m.id][0] == "Informatique"


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
