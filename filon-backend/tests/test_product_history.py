"""La fiche d'un produit regroupé doit disposer de son historique.

`product_detail` appelait `compute_verdict(history=[])`. Or `compute_verdict`
exige `MIN_SAMPLES` relevés et `MIN_TRACKED_DAYS` jours de suivi avant de se
prononcer : avec une liste vide, la fiche répondait **toujours** « historique
trop récent pour se prononcer », y compris après un an de collecte.

Le Score FILON est la promesse centrale du produit — « est-ce le bon moment
d'acheter » plutôt que « voici une liste de prix ». Il était structurellement
incapable de répondre sur les fiches produit, les plus exposées puisque ce sont
elles qui portent la comparaison entre marchands.

L'historique retenu est le **meilleur prix par jour**, toutes offres confondues.
Concaténer les relevés bruts de plusieurs marchands ferait alterner la courbe
entre le plus cher et le moins cher, fabriquant une volatilité qui n'a jamais
existé : le verdict y lirait une forte amplitude et conseillerait d'attendre sur
un produit parfaitement stable.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.routes.catalog import _grouped_price_history
from app.db import models
from app.db.base import Base
from app.services.verdict import MIN_SAMPLES, MIN_TRACKED_DAYS, compute_verdict

PG_URL = os.getenv(
    "TEST_DATABASE_URL", "postgresql+asyncpg://filon:filon@localhost:5432/filontest"
)


async def _pg_available() -> bool:
    try:
        engine = create_async_engine(PG_URL)
        async with engine.begin():
            pass
        await engine.dispose()
        return True
    except Exception:
        return False


@pytest.fixture
async def base():
    """Un produit regroupé vendu par deux marchands, sans aucun relevé."""
    if not await _pg_available():
        pytest.skip("PostgreSQL indisponible")
    engine = create_async_engine(PG_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as s:
        produit = models.CatalogProduct(
            ean="4006381333931",
            name="Cafetière Expresso",
            price_min=79.0,
            price_max=99.0,
            currency="EUR",
            offers_count=2,
            merchants_count=2,
        )
        s.add(produit)
        await s.flush()

        offres = []
        for i, (nom, prix) in enumerate((("Cher", 99.0), ("BonMarche", 79.0)), start=1):
            m = models.Merchant(awin_mid=i, name=nom, slug=nom.lower())
            s.add(m)
            await s.flush()
            o = models.Offer(
                merchant_id=m.id,
                awin_product_id=f"p{i}",
                name="Cafetière Expresso",
                price=prix,
                currency="EUR",
                product_id=produit.id,
            )
            s.add(o)
            await s.flush()
            offres.append(o)

        await s.commit()
        s.info["produit_id"] = produit.id
        s.info["offres"] = [o.id for o in offres]
        yield s
    await engine.dispose()


async def _releve(session, offer_id: int, prix: float, jours_avant: int):
    """Écrit un relevé daté, en contournant le défaut `captured_at`."""
    await session.execute(
        insert(models.PriceSnapshot).values(
            offer_id=offer_id,
            price=prix,
            captured_at=datetime.now(timezone.utc).replace(tzinfo=None)
            - timedelta(days=jours_avant),
        )
    )
    await session.commit()


class TestLHistoriqueDunProduitRegroupe:
    async def test_sans_releve_lhistorique_est_vide(self, base):
        assert await _grouped_price_history(base, base.info["produit_id"]) == []

    async def test_les_releves_sont_rendus_par_ordre_chronologique(self, base):
        """Le graphique de la fiche et le calcul de durée l'exigent tous deux."""
        offre = base.info["offres"][0]
        for jours, prix in ((10, 95.0), (5, 92.0), (1, 88.0)):
            await _releve(base, offre, prix, jours)
        points = await _grouped_price_history(base, base.info["produit_id"])
        assert [p for p, _ in points] == [95.0, 92.0, 88.0]
        horodatages = [t for _, t in points]
        assert horodatages == sorted(horodatages)

    async def test_un_seul_point_par_jour(self, base):
        """Plusieurs relevés le même jour ne doivent pas gonfler le décompte.

        Sans regroupement, un produit vendu par cinq marchands paraîtrait suivi
        cinq fois plus longtemps qu'en réalité et franchirait `MIN_SAMPLES` sans
        avoir la profondeur correspondante.
        """
        a, b = base.info["offres"]
        await _releve(base, a, 99.0, 3)
        await _releve(base, b, 79.0, 3)
        points = await _grouped_price_history(base, base.info["produit_id"])
        assert len(points) == 1

    async def test_le_meilleur_prix_du_jour_est_retenu(self, base):
        """C'est le prix que la fiche affiche : `price_min`."""
        a, b = base.info["offres"]
        await _releve(base, a, 99.0, 3)
        await _releve(base, b, 79.0, 3)
        points = await _grouped_price_history(base, base.info["produit_id"])
        assert points[0][0] == 79.0

    async def test_l_alternance_entre_marchands_ne_cree_pas_de_fausse_volatilite(
        self, base
    ):
        """Le cas qui motive l'agrégation.

        Deux marchands, l'un à 99 € l'autre à 79 €, tous deux parfaitement
        stables sur dix jours. Les relevés bruts donneraient une courbe oscillant
        de 79 à 99 € — soit 25 % d'amplitude imaginaire. Le meilleur prix
        quotidien rend une ligne plate, ce qu'elle est.
        """
        a, b = base.info["offres"]
        for jour in range(10, 0, -1):
            await _releve(base, a, 99.0, jour)
            await _releve(base, b, 79.0, jour)
        prix = [p for p, _ in await _grouped_price_history(base, base.info["produit_id"])]
        assert set(prix) == {79.0}

    async def test_les_prix_nuls_ou_negatifs_sont_ecartes(self, base):
        """Un feed défectueux ne doit pas fabriquer un « prix au plus bas »."""
        offre = base.info["offres"][0]
        await _releve(base, offre, 0.0, 5)
        await _releve(base, offre, 89.0, 4)
        prix = [p for p, _ in await _grouped_price_history(base, base.info["produit_id"])]
        assert prix == [89.0]

    async def test_le_nombre_de_points_est_borne(self, base):
        """Un produit suivi longtemps ne doit pas renvoyer une charge illimitée."""
        offre = base.info["offres"][0]
        for jour in range(12, 0, -1):
            await _releve(base, offre, 80.0 + jour, jour)
        points = await _grouped_price_history(base, base.info["produit_id"], max_points=5)
        assert len(points) == 5
        # Les points conservés sont les plus récents, et restent chronologiques.
        horodatages = [t for _, t in points]
        assert horodatages == sorted(horodatages)


class TestLeVerdictSePrononceDesormais:
    async def test_un_historique_suffisant_permet_de_conclure(self, base):
        """Le cœur du correctif.

        Avec `history=[]`, ce scénario rendait « insuffisant » quelle que soit la
        profondeur accumulée.
        """
        offre = base.info["offres"][1]
        for jour in range(30, 0, -2):  # 15 relevés sur 30 jours
            await _releve(base, offre, 90.0, jour)
        points = await _grouped_price_history(base, base.info["produit_id"])
        assert len(points) >= MIN_SAMPLES

        verdict = compute_verdict(
            price=79.0, currency="EUR", history=points, merchants_count=2
        )
        assert verdict["level"] != "insuffisant"
        assert verdict["samples"] >= MIN_SAMPLES
        assert verdict["tracked_days"] >= MIN_TRACKED_DAYS

    async def test_un_prix_au_plus_bas_est_reconnu(self, base):
        offre = base.info["offres"][1]
        for jour in range(30, 0, -2):
            await _releve(base, offre, 95.0, jour)
        points = await _grouped_price_history(base, base.info["produit_id"])
        verdict = compute_verdict(
            price=79.0, currency="EUR", history=points, merchants_count=2
        )
        assert verdict["level"] == "excellent"

    async def test_un_historique_trop_court_reste_prudent(self, base):
        """La règle cardinale du module ne doit pas céder.

        Brancher l'historique ne signifie pas se prononcer plus tôt : deux jours
        de suivi ne permettent aucune conclusion, et le dire est la seule réponse
        honnête.
        """
        offre = base.info["offres"][1]
        await _releve(base, offre, 95.0, 2)
        await _releve(base, offre, 94.0, 1)
        points = await _grouped_price_history(base, base.info["produit_id"])
        verdict = compute_verdict(
            price=79.0, currency="EUR", history=points, merchants_count=1
        )
        assert verdict["level"] == "insuffisant"
        assert verdict["confidence"] == "faible"


class TestLaFicheNePasseePlusUnHistoriqueVide:
    def test_product_detail_transmet_un_historique(self):
        """Garde-fou textuel : `history=[]` ne doit pas revenir dans la fiche.

        Le défaut était discret — un argument vide au milieu d'un appel correct —
        et neutralisait silencieusement la principale promesse du produit.
        """
        from pathlib import Path

        import app.api.routes.catalog as module

        source = Path(module.__file__).read_text(encoding="utf-8")
        assert "history=[]" not in source
        assert "_grouped_price_history" in source
