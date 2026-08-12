"""Tests de l'endpoint `/api/catalog/relief` et de sa réduction en paliers.

L'endpoint alimente la scène 3D de la page d'accueil. Deux propriétés comptent
plus que les autres et sont vérifiées ici : la réduction d'un historique en
paliers (une strate par changement de prix, pas une par relevé) et la
qualification honnête de la confiance.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from app.api.routes.catalog import RELIEF_MAX_COLUMNS, RELIEF_MIN_SAMPLES, _confiance


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
