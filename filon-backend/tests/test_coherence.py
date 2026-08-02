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


class TestPasDeProtectionAutomatique:
    """Deux tentatives de garde-fou automatique ont échoué sur les vrais
    chiffres, et ces tests fixent la conclusion.

    L'idée était qu'une minorité concentrée — dans un rayon, puis dans un
    département — signale une seconde activité plutôt que du bruit. Elle est
    fausse : une erreur de mots-clés systématique est concentrée elle aussi.

    Mesuré sur YesStyle, marchand de cosmétiques coréens : 2 113 offres en
    Informatique (4,9 %), département High-Tech à 5,0 % — juste assez pour
    déclencher la protection. Ce bloc n'est pas une activité, c'est exactement
    la pollution du rayon Informatique qu'on veut retirer. Sa vraie mode tient
    en 103 offres, soit 0,2 %.

    La distinction relève de la connaissance du marchand. Elle est donc portée
    par `exclude`, explicitement.
    """

    async def test_un_bloc_concentre_est_realigne_comme_le_reste(self, session):
        """Le cas YesStyle, aux proportions réelles."""
        m = await _merchant(session, "yesstyle", 14)
        await _peupler(session, m, {
            "Beauté & Parfum": 38838,
            "Informatique": 2113,          # concentré, et pourtant erroné
            "Alimentation & Boissons": 1198,
            "Mode femme": 103,             # la vraie seconde activité : 0,2 %
        })
        await session.commit()

        res = await coherence.realign(session)
        assert res["offres_realignees"] == 2113 + 1198 + 103

    async def test_exclure_un_marchand_le_laisse_intact(self, session):
        m = await _merchant(session, "yesstyle", 15)
        await _peupler(session, m, {"Beauté & Parfum": 900, "Informatique": 100})
        await session.commit()

        res = await coherence.realign(session, exclude={"yesstyle"})
        assert res["offres_realignees"] == 0
        assert res["merchants_specialises"] == 0

    async def test_l_exclusion_marche_aussi_par_nom(self, session):
        m = await _merchant(session, "yesstyle", 16)
        await _peupler(session, m, {"Beauté & Parfum": 900, "Informatique": 100})
        await session.commit()

        # `_merchant` donne le slug comme nom : on vise l'autre champ.
        res = await coherence.realign(session, exclude={"YESSTYLE"})
        assert res["offres_realignees"] == 0

    async def test_exclure_un_marchand_nen_ecarte_pas_un_autre(self, session):
        a = await _merchant(session, "yesstyle", 17)
        b = await _merchant(session, "tissus", 18)
        await _peupler(session, a, {"Beauté & Parfum": 900, "Informatique": 100})
        await _peupler(session, b, {"Loisirs créatifs": 900, "Informatique": 100})
        await session.commit()

        res = await coherence.realign(session, exclude={"yesstyle"})
        assert res["offres_realignees"] == 100
        assert [d["merchant"] for d in res["detail"]] == ["tissus"]


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
