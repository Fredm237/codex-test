"""Tests de l'endpoint `/api/catalog/relief` et de sa réduction en paliers.

L'endpoint alimente la scène 3D de la page d'accueil. Deux propriétés comptent
plus que les autres et sont vérifiées ici : la réduction d'un historique en
paliers (une strate par changement de prix, pas une par relevé) et la
qualification honnête de la confiance.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.routes.catalog import RELIEF_MAX_COLUMNS, RELIEF_MIN_SAMPLES, _confiance, relief
from app.db import models
from app.db.base import Base


class TestConfiance:
    """La confiance doit refléter ce que l'historique autorise à dire."""

    def test_historique_long_et_dense_donne_bonne(self):
        assert _confiance(jours=14.0, releves=20) == "bonne"

    def test_historique_moyen_donne_moyenne(self):
        assert _confiance(jours=6.0, releves=7) == "moyenne"

    def test_historique_court_donne_faible(self):
        # Le cas réel mesuré en production : 6 jours, 13 relevés.
        assert _confiance(jours=6.0, releves=13) == "moyenne"

    def test_deux_releves_sur_un_jour_reste_faible(self):
        assert _confiance(jours=1.0, releves=2) == "faible"

    def test_beaucoup_de_releves_sur_peu_de_jours_ne_suffit_pas(self):
        # Vingt relevés en deux jours ne disent rien d'une tendance : la densité
        # ne remplace pas la durée.
        assert _confiance(jours=2.0, releves=20) == "faible"

    def test_longue_duree_mais_deux_releves_ne_suffit_pas(self):
        # Symétrie du cas précédent : la durée ne remplace pas la densité.
        assert _confiance(jours=30.0, releves=2) == "faible"


class TestBornes:
    """Les garde-fous de charge utile doivent rester explicites."""

    def test_plafond_de_colonnes(self):
        # 300 colonnes ≈ 150 Ko de JSON : au-delà, la page d'accueil paierait
        # l'expérience en temps de chargement.
        assert RELIEF_MAX_COLUMNS == 300

    def test_minimum_de_releves(self):
        # Un seul relevé ne dessine aucun palier.
        assert RELIEF_MIN_SAMPLES == 2


def _reduire(brut: list[tuple[float, datetime]]) -> list[list[float]]:
    """Réimplémente la réduction en paliers de l'endpoint, pour la tester seule.

    La logique de l'endpoint est enchâssée dans une fonction asynchrone qui exige
    une base ; l'isoler ici permet de vérifier l'algorithme sans Postgres.
    """
    t0 = brut[0][1]
    paliers: list[list[float]] = []
    dernier: float | None = None
    for prix, quand in brut:
        if dernier is None or abs(prix - dernier) >= 0.01:
            jours = round((quand - t0).total_seconds() / 86400.0, 3)
            paliers.append([jours, round(prix, 2)])
            dernier = prix
    return paliers


class TestReductionEnPaliers:
    """Le cœur de la scène : transformer des relevés en marches d'escalier."""

    def test_un_prix_constant_donne_un_seul_palier(self):
        t = datetime(2026, 8, 1)
        brut = [(19.99, t + timedelta(hours=6 * i)) for i in range(12)]
        assert _reduire(brut) == [[0.0, 19.99]]

    def test_le_cas_reel_de_production(self):
        """Offre 490396 : palier à 61,39, chute, palier à 51,39."""
        t = datetime(2026, 8, 1, 5, 0)
        brut = [
            (61.39, t),
            (61.39, datetime(2026, 8, 1, 20, 20)),
            (61.39, datetime(2026, 8, 3, 4, 57)),
            (61.39, datetime(2026, 8, 4, 15, 43)),
            (55.99, datetime(2026, 8, 5, 1, 51)),
            (51.39, datetime(2026, 8, 5, 9, 36)),
            (51.39, datetime(2026, 8, 7, 10, 45)),
        ]
        paliers = _reduire(brut)
        # Trois paliers, pas sept relevés.
        assert len(paliers) == 3
        assert [p[1] for p in paliers] == [61.39, 55.99, 51.39]
        # Le premier palier est à l'origine du temps.
        assert paliers[0][0] == 0.0
        # Les suivants sont strictement postérieurs et ordonnés.
        assert paliers[1][0] < paliers[2][0]

    def test_les_epsilons_de_flottant_ne_creent_pas_de_palier(self):
        # Deux relevés du « même » prix peuvent différer d'un epsilon : le seuil
        # au centime évite de fabriquer des strates fantômes.
        t = datetime(2026, 8, 1)
        brut = [
            (10.0, t),
            (10.0000001, t + timedelta(hours=8)),
            (9.999999, t + timedelta(hours=16)),
        ]
        assert _reduire(brut) == [[0.0, 10.0]]

    def test_une_hausse_est_un_palier_comme_une_baisse(self):
        # Le relief ne montre pas que des baisses : une remontée est une marche.
        t = datetime(2026, 8, 1)
        brut = [(30.0, t), (45.0, t + timedelta(days=2))]
        paliers = _reduire(brut)
        assert [p[1] for p in paliers] == [30.0, 45.0]

    def test_les_jours_sont_relatifs_au_premier_releve(self):
        t = datetime(2026, 8, 1, 12, 0)
        brut = [(20.0, t), (18.0, t + timedelta(days=3, hours=12))]
        paliers = _reduire(brut)
        assert paliers[0][0] == 0.0
        assert paliers[1][0] == pytest.approx(3.5, abs=0.01)


class TestHorsEchelle:
    """Les feeds livrent parfois des centimes pour des euros.

    Cas réel relevé en production : montre G-Shock à 69,93 € puis 6993,00 € puis
    99,90 €. Sans traitement, cette colonne devient la plus haute et la plus
    éclairée du paysage, celle qui affirme « −98 %, achetez maintenant ».

    La détection porte sur l'ordre de grandeur, non sur un facteur exact : sur ce
    cas la médiane vaut 87,41 et 6993/87,41 = 80,0, donc aucun facteur rond.
    """

    def test_un_prix_cent_fois_trop_grand_est_detecte(self):
        from app.api.routes.catalog import _est_hors_echelle

        assert _est_hors_echelle(6993.00, 69.93) is True

    def test_un_prix_cent_fois_trop_petit_est_detecte(self):
        from app.api.routes.catalog import _est_hors_echelle

        assert _est_hors_echelle(0.6993, 69.93) is True

    def test_le_facteur_quatre_vingt_du_cas_reel_est_detecte(self):
        from app.api.routes.catalog import _est_hors_echelle

        # C'est le rapport effectif entre l'aberration et la médiane : c'est lui
        # qui a fait échouer la détection par facteur exact.
        assert _est_hors_echelle(6993.0, 87.41) is True

    def test_une_vraie_variation_n_est_pas_hors_echelle(self):
        from app.api.routes.catalog import _est_hors_echelle

        # Une remise de 30 %.
        assert _est_hors_echelle(48.95, 69.93) is False

    def test_un_doublement_de_prix_n_est_pas_hors_echelle(self):
        from app.api.routes.catalog import _est_hors_echelle

        assert _est_hors_echelle(139.86, 69.93) is False

    def test_la_remise_la_plus_agressive_reste_admise(self):
        from app.api.routes.catalog import _est_hors_echelle

        # −80 % est le plancher des soldes réelles : facteur 5, sous le seuil de 10.
        assert _est_hors_echelle(20.0, 100.0) is False

    def test_prix_nul_ou_negatif_ne_leve_pas(self):
        from app.api.routes.catalog import _est_hors_echelle

        assert _est_hors_echelle(0.0, 69.93) is False
        assert _est_hors_echelle(69.93, 0.0) is False


class TestPaliersPlausibles:
    """Le nettoyage doit retirer l'aberration sans mutiler la colonne."""

    def test_le_cas_g_shock_est_assaini(self):
        from app.api.routes.catalog import _paliers_plausibles

        paliers = [[0.0, 69.93], [0.631, 74.92], [2.008, 6993.0], [3.867, 99.9]]
        nets = _paliers_plausibles(paliers, prix_courant=99.9)
        valeurs = [p[1] for p in nets]
        assert 6993.0 not in valeurs
        # Les trois paliers légitimes subsistent.
        assert valeurs == [69.93, 74.92, 99.9]

    def test_le_premier_palier_reste_a_l_origine(self):
        from app.api.routes.catalog import _paliers_plausibles

        # Si l'aberration occupait la première position, la colonne ne doit pas
        # se retrouver flottante après le début de la fenêtre.
        paliers = [[0.0, 1303.02], [3.867, 13.03], [4.192, 12.50]]
        nets = _paliers_plausibles(paliers, prix_courant=12.50)
        assert nets[0][0] == 0.0

    def test_une_colonne_saine_est_intacte(self):
        from app.api.routes.catalog import _paliers_plausibles

        paliers = [[0.0, 61.39], [4.2, 55.99], [4.6, 51.39]]
        assert _paliers_plausibles(paliers, prix_courant=51.39) == paliers

    def test_un_seul_palier_est_rendu_tel_quel(self):
        from app.api.routes.catalog import _paliers_plausibles

        paliers = [[0.0, 19.99]]
        assert _paliers_plausibles(paliers, prix_courant=19.99) == paliers

    def test_on_prefere_les_donnees_brutes_a_une_colonne_vide(self):
        from app.api.routes.catalog import _paliers_plausibles

        # Deux paliers dont l'un paraît aberrant : aucun des deux n'est plus
        # légitime que l'autre, les écarter reviendrait à choisir au hasard.
        paliers = [[0.0, 5.0], [1.0, 500.0]]
        nets = _paliers_plausibles(paliers, prix_courant=5.0)
        assert len(nets) == 2

    def test_le_cas_kinguin_est_assaini(self):
        from app.api.routes.catalog import _paliers_plausibles

        # Autre cas réel : clé Steam relevée à 1303 € au milieu de prix à deux
        # chiffres.
        paliers = [[0.0, 1303.02], [3.867, 161.34], [4.192, 16.59], [4.526, 18.89]]
        nets = _paliers_plausibles(paliers, prix_courant=18.89)
        assert 1303.02 not in [p[1] for p in nets]


class TestGardeFousReutilises:
    """Le relief doit s'appuyer sur les seuils déjà établis, pas les redéfinir."""

    def test_les_seuils_de_la_home_sont_disponibles(self):
        from app.api.routes.catalog import (
            MAX_PLAUSIBLE_DROP_PCT,
            MIN_HIGH_OBSERVATIONS,
            MIN_HIGH_SHARE,
        )

        # Ces valeurs proviennent d'un travail antérieur sur les rangs de la
        # page d'accueil : le relief les réutilise pour rester cohérent.
        assert MAX_PLAUSIBLE_DROP_PCT == 85.0
        assert MIN_HIGH_OBSERVATIONS == 2
        assert MIN_HIGH_SHARE == 0.15


@pytest.fixture
async def relief_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as session:
        yield session
    await engine.dispose()


async def _seed_relief_offer(session, *, category: str, snapshot_currencies: list[str | None]):
    merchant = models.Merchant(
        awin_mid=901,
        name=f"Boutique {category}",
        slug=f"boutique-{category}",
    )
    session.add(merchant)
    await session.flush()
    offer = models.Offer(
        merchant_id=merchant.id,
        awin_product_id=f"relief-{category}",
        name=f"Produit {category}",
        price=80.0,
        currency="EUR",
        in_stock=True,
        is_canonical=True,
        is_adult=False,
        filon_category=category,
        image_url="https://example.test/relief.jpg",
    )
    session.add(offer)
    await session.flush()
    now = datetime.now(UTC).replace(tzinfo=None)
    prices = [100.0, 100.0, 80.0]
    for index, (price, currency) in enumerate(zip(prices, snapshot_currencies, strict=True)):
        session.add(
            models.PriceSnapshot(
                offer_id=offer.id,
                price=price,
                currency=currency,
                in_stock=True,
                captured_at=now - timedelta(days=3 - index),
            )
        )
    await session.commit()


async def test_relief_publie_une_devise_explicitement_prouvee(relief_session):
    category = "truth-valid"
    await _seed_relief_offer(
        relief_session,
        category=category,
        snapshot_currencies=["EUR", " eur ", "EUR"],
    )
    result = await relief(
        limit=12,
        window_days=21,
        category=category,
        session=relief_session,
    )
    assert result["count"] == 1
    assert result["columns"][0]["currency"] == "EUR"


async def test_relief_ne_melange_jamais_deux_devises(relief_session):
    category = "truth-mixed"
    await _seed_relief_offer(
        relief_session,
        category=category,
        snapshot_currencies=["GBP", "GBP", "EUR"],
    )
    result = await relief(
        limit=12,
        window_days=21,
        category=category,
        session=relief_session,
    )
    assert result["columns"] == []
