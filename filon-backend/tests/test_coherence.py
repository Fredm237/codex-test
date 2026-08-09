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


class TestCestLeDepartementQuiDecide:
    """Ce qui sépare une seconde activité d'une erreur, c'est la distance.

    Deux seuils de volume ont été essayés avant celui-ci et ont échoué sur les
    vrais chiffres : ils supposaient qu'une minorité fournie signale une
    activité, alors qu'une erreur de mots-clés systématique est fournie elle
    aussi. La quantité ne dit rien ; le département, si.

    Les quatre cas ci-dessous sont les répartitions réelles du catalogue.
    """

    async def test_les_rayons_voisins_du_departement_restent(self, session):
        """Kinguin : 87,9 % en Gaming, mais le département High-Tech fait 98 %.

        Les 1 238 recharges en Téléphonie et les 840 licences en Informatique
        sont une seule activité rangée sur trois rayons — les forcer en Gaming
        classerait une licence Windows comme un jeu.
        """
        m = await _merchant(session, "kinguin", 20)
        await _peupler(session, m, {
            "Gaming": 18180, "Téléphonie": 1238, "Informatique": 840,
            "Alimentation & Boissons": 97, "Animalerie": 96, "Auto & Moto": 83,
        })
        await session.commit()

        res = await coherence.realign(session)
        assert res["offres_realignees"] == 97 + 96 + 83

    async def test_un_bloc_d_un_autre_departement_est_ramene(self, session):
        """YesStyle : cosmétiques coréens, et 2 113 offres en Informatique.

        Même volume que Kinguin, conclusion inverse — parce qu'Informatique
        n'est pas le département de la beauté. C'est la pollution du rayon
        Informatique, et non une activité : la mode réelle tient en 103 offres.
        """
        m = await _merchant(session, "yesstyle", 21)
        await _peupler(session, m, {
            "Beauté & Parfum": 38838,
            "Informatique": 2113,
            "Alimentation & Boissons": 1198,
            "Mode femme": 103,
        })
        await session.commit()

        res = await coherence.realign(session)
        assert res["offres_realignees"] == 2113 + 1198 + 103

    async def test_les_accessoires_d_un_specialiste_de_la_mode_restent(self, session):
        """Overhemden : 94,6 % en chemises homme, 1 979 cravates et ceintures.

        « Accessoires » est du même département : c'est le rayon voisin d'un
        chemisier, pas une erreur. En revanche ses 729 offres en Loisirs
        créatifs — des chemises nommées d'après leur tissu — reviennent.
        """
        m = await _merchant(session, "overhemden", 22)
        await _peupler(session, m, {
            "Mode homme": 55846, "Accessoires": 1979, "Mode femme": 303,
            "Chaussures": 143, "Loisirs créatifs": 729, "Beauté & Parfum": 18,
        })
        await session.commit()

        res = await coherence.realign(session)
        assert res["offres_realignees"] == 729 + 18

    async def test_les_tissus_nommes_d_apres_le_vetement_reviennent(self, session):
        """TISSUS DE REVE, le cas d'origine : la mercerie n'est pas de la mode."""
        m = await _merchant(session, "tissus-de-reve", 23)
        await _peupler(session, m, {
            "Loisirs créatifs": 5938,
            "Mode femme": 548, "Informatique": 320, "Auto & Moto": 213,
        })
        await session.commit()

        res = await coherence.realign(session)
        assert res["offres_realignees"] == 548 + 320 + 213

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
