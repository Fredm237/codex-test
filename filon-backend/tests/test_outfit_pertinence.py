"""Régressions Outfit Studio : pertinence stricte, confiance non simulée.

Constaté en production le 19/08/2026 sur `POST /api/intelligence/outfit/analyse` :
à « une tenue pour un mariage en été », le studio composait une tenue notée
`confidence_score: 100`, `confidence_band: "high"`, dont la chaussure était
« Siso Régulateur de hauteur de panneau SHOES en plastique » à 0,70 € et
l'accessoire un sac à 0,00 €.

La confiance ne mesurait que la complétude documentaire — un prix, un marchand,
une disponibilité, au moins deux pièces. Une pièce parfaitement hors sujet la
laissait donc à 100. Sans vérité terrain humaine, FILON n'expose désormais
aucune probabilité ni bande de confiance artificielle.
"""

from __future__ import annotations

import math
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from app.intelligence import fashion
from app.intelligence.contracts import CoreOfferSnapshot
from app.services import relevance, taxonomy


def _snapshot(
    offer_id: int, name: str, category: str, subcategory: str, *, price: float = 20.0
) -> CoreOfferSnapshot:
    return CoreOfferSnapshot(
        offer_id=offer_id,
        catalog_product_id=None,
        name=name,
        brand=None,
        filon_category=category,
        filon_subcategory=subcategory,
        offer_kind="physical_product",
        price=price,
        currency="EUR",
        availability="in_stock",
        image_url="https://images.example/item.jpg",
        deep_link="https://merchant.example/item",
        merchant_id=1,
        merchant_name="Marchand test",
        merchant_region="BE",
        observed_at=datetime.now(UTC),
    )


def test_une_piece_hors_sujet_reste_sous_le_seuil_de_pertinence():
    termes = relevance.mots("une tenue pour un mariage en été")

    assert relevance.score(
        termes,
        "Siso Régulateur de hauteur de panneau SHOES en plastique",
        offer_kind="physical_product",
    ) < relevance.SEUIL


def test_des_pieces_explicitement_demandees_restent_pertinentes():
    termes = relevance.mots("des chaussures de running homme")

    for nom in (
        "Chaussures de running homme Asics Gel-Contend",
        "Chaussures de running homme Nike Revolution",
    ):
        assert relevance.score(
            termes,
            nom,
            offer_kind="physical_product",
        ) >= relevance.SEUIL


def test_composition_mariage_ecarte_les_pieces_techniques_et_le_sac_non_demande():
    intent = fashion.parse_fashion_intent("Une tenue pour un mariage en été")
    robe = _snapshot(
        1,
        "Women's lace white long evening wedding dress",
        taxonomy.MODE_FEMME,
        "Robes",
    )
    faux_chaussure = _snapshot(
        2,
        "Siso Régulateur de hauteur de panneau SHOES en plastique",
        taxonomy.CHAUSSURES,
        "Bottes",
    )
    sac_non_demande = _snapshot(
        3,
        "Washable Kraft Paper Toiletry Bag Silver",
        taxonomy.ACCESSOIRES,
        "Sacs",
    )
    chaussure_non_demandee = _snapshot(
        4,
        "BlackFox | Comfortabele Schoenen / Instappers maat 36 Kleur geel",
        taxonomy.CHAUSSURES,
        "Chaussures basses",
    )

    solution = fashion.compose_outfit(
        intent,
        [robe, faux_chaussure, sac_non_demande, chaussure_non_demandee],
    )

    assert solution["decision"] == "recommend"
    assert [item["name"] for item in solution["items"]] == [robe.name]
    assert solution["style_score"] is None
    assert solution["confidence_score"] is None
    assert solution["confidence_band"] == "not_calibrated"
    assert "confidence_not_calibrated" in solution["unknowns"]


def test_abstention_mode_ne_simule_pas_une_confiance_faible():
    intent = fashion.parse_fashion_intent("Un blazer noir pour le travail sous 150 euros")
    hors_sujet = _snapshot(
        9,
        "Veste Sportstyle Pqe Camo Tk Jt - Noir / S",
        taxonomy.MODE_FEMME,
        "Manteaux & Vestes",
    )

    solution = fashion.compose_outfit(intent, [hors_sujet])

    assert solution["decision"] == "abstain"
    assert solution["rejection_reason"] == "no_verified_base"
    assert solution["style_score"] is None
    assert solution["confidence_score"] is None
    assert solution["confidence_band"] == "not_calibrated"
    assert "confidence_not_calibrated" in solution["unknowns"]


@pytest.mark.parametrize(
    "changes",
    [
        {"price": None},
        {"price": 0.0},
        {"price": -1.0},
        {"price": math.nan},
        {"price": math.inf},
        {"price": -math.inf},
        {"currency": None},
        {"currency": ""},
        {"currency": "unknown"},
        {"currency": "XXX"},
        {"availability": "unknown"},
        {"availability": "out_of_stock"},
        {"observed_at": None},
        {"observed_at": datetime.now(UTC) - timedelta(hours=73)},
        {"observed_at": datetime.now(UTC) + timedelta(hours=1)},
    ],
)
def test_composition_refuse_les_faits_invalides_inconnus_ou_perimes(changes):
    intent = fashion.parse_fashion_intent(
        "Une robe noire pour une soirée sous 150 euros"
    )
    candidate = replace(
        _snapshot(
            90,
            "Robe noire de soirée",
            taxonomy.MODE_FEMME,
            "Robes",
            price=120.0,
        ),
        **changes,
    )

    solution = fashion.compose_outfit(intent, [candidate])

    assert solution["decision"] == "abstain"
    assert solution["rejection_reason"] == "no_verified_base"
    assert solution["total_known_price"] is None
    assert solution["items"] == []


def test_composition_normalise_la_devise_prouvee_avant_de_l_exposer():
    intent = fashion.parse_fashion_intent(
        "Une robe noire pour une soirée sous 150 euros"
    )
    candidate = replace(
        _snapshot(
            91,
            "Robe noire de soirée",
            taxonomy.MODE_FEMME,
            "Robes",
            price=120.0,
        ),
        currency=" eur ",
    )

    solution = fashion.compose_outfit(intent, [candidate])

    assert solution["decision"] == "recommend"
    assert solution["total_known_price"]["currency"] == "EUR"
    assert solution["items"][0]["currency"] == "EUR"
    assert solution["items"][0]["evidence"][0]["value"] == "120.00 EUR"
    assert all(
        evidence["confidence"] is None
        for evidence in solution["items"][0]["evidence"]
    )


def test_composition_s_abstient_si_la_somme_des_prix_deborde():
    intent = fashion.parse_fashion_intent(
        "Une robe avec chaussures et sac pour un mariage"
    )
    robe = _snapshot(
        101,
        "Robe de mariage",
        taxonomy.MODE_FEMME,
        "Robes",
        price=1e308,
    )
    chaussures = _snapshot(
        102,
        "Chaussures de mariage",
        taxonomy.CHAUSSURES,
        "Chaussures basses",
        price=1e308,
    )
    sac = _snapshot(
        103,
        "Sac de mariage",
        taxonomy.ACCESSOIRES,
        "Sacs",
        price=1e308,
    )

    solution = fashion.compose_outfit(intent, [robe, chaussures, sac])

    assert solution["decision"] == "abstain"
    assert solution["rejection_reason"] == "non_finite_total"
    assert solution["total_known_price"] is None


def test_blazer_de_travail_exige_une_preuve_de_piece_principale():
    intent = fashion.parse_fashion_intent("Un blazer noir pour le travail sous 150 euros")
    blouson_sport = _snapshot(
        10,
        "Veste Sportstyle Pqe Camo Tk Jt - Noir / S",
        taxonomy.MODE_FEMME,
        "Manteaux & Vestes",
    )
    vrai_blazer = _snapshot(
        11,
        "Blazer noir femme pour le travail",
        taxonomy.MODE_FEMME,
        "Manteaux & Vestes",
    )

    assert fashion.compose_outfit(intent, [blouson_sport])["decision"] == "abstain"
    solution = fashion.compose_outfit(intent, [blouson_sport, vrai_blazer])
    assert solution["decision"] == "recommend"
    assert solution["items"][0]["name"] == vrai_blazer.name


def test_chaussures_explicitement_demandees_deviennent_piece_principale():
    intent = fashion.parse_fashion_intent("Des chaussures noires pour le travail sous 120 euros")
    chaussures = _snapshot(
        12,
        "Chaussures noires femme pour le travail",
        taxonomy.CHAUSSURES,
        "Chaussures basses",
    )

    solution = fashion.compose_outfit(intent, [chaussures])

    assert solution["decision"] == "recommend"
    assert solution["items"][0]["name"] == chaussures.name
    assert solution["items"][0]["role"] == "footwear"


def test_robe_sous_budget_est_retenue_apres_une_robe_plus_pertinente_mais_trop_chere():
    intent = fashion.parse_fashion_intent("Une robe noire pour une soirée sous 150 euros")
    robe_hors_budget = _snapshot(
        10,
        "Robe noire de soirée premium",
        taxonomy.MODE_FEMME,
        "Robes",
        price=190.0,
    )
    robe_achetable = _snapshot(
        11,
        "Robe noire de soirée",
        taxonomy.MODE_FEMME,
        "Robes",
        price=120.0,
    )

    solution = fashion.compose_outfit(intent, [robe_hors_budget, robe_achetable])
    assert solution["decision"] == "recommend"
    assert solution["items"][0]["name"] == robe_achetable.name
    assert solution["total_known_price"]["amount"] == 120.0


def test_robe_ecarte_un_gel_douche_qui_cite_une_robe_dans_son_nom():
    intent = fashion.parse_fashion_intent("Une robe noire pour une soirée sous 150 euros")
    gel_douche = _snapshot(
        11,
        "Guerlain - La Petite Robe Noire Shower Gel - 200 ML",
        taxonomy.MODE_FEMME,
        "Robes",
    )
    robe_soiree = _snapshot(
        12,
        "Robe noire de soirée",
        taxonomy.MODE_FEMME,
        "Robes",
    )

    assert fashion.compose_outfit(intent, [gel_douche])["decision"] == "abstain"
    solution = fashion.compose_outfit(intent, [gel_douche, robe_soiree])
    assert solution["decision"] == "recommend"
    assert solution["items"][0]["name"] == robe_soiree.name


def test_robe_de_soiree_ecarte_un_costume_a_theme_non_demande():
    intent = fashion.parse_fashion_intent("Une robe noire pour une soirée sous 150 euros")
    costume_tueur = _snapshot(
        12,
        "Une robe noire pour un tueur",
        taxonomy.MODE_FEMME,
        "Robes",
    )
    robe_soiree = _snapshot(
        13,
        "Robe noire de soirée",
        taxonomy.MODE_FEMME,
        "Robes",
    )

    assert fashion.compose_outfit(intent, [costume_tueur])["decision"] == "abstain"
    solution = fashion.compose_outfit(intent, [costume_tueur, robe_soiree])
    assert solution["decision"] == "recommend"
    assert solution["items"][0]["name"] == robe_soiree.name


def test_chaussures_de_travail_ecartent_futsal_et_enfant_explicitement_nomme():
    intent = fashion.parse_fashion_intent("Des chaussures noires pour le travail sous 120 euros")
    futsal_enfant = _snapshot(
        13,
        "Chaussures Futsal Enfant Munich Arenga Kid 306, noires",
        taxonomy.CHAUSSURES,
        "Chaussures basses",
    )
    sneaker_generique = _snapshot(
        14,
        "Chaussures adidas Vs Pace 2.0 Homme blanches et noires",
        taxonomy.CHAUSSURES,
        "Chaussures basses",
    )
    chaussures_adultes = _snapshot(
        15,
        "Chaussures noires adultes en cuir pour le travail",
        taxonomy.CHAUSSURES,
        "Chaussures basses",
    )

    assert fashion.compose_outfit(intent, [futsal_enfant])["decision"] == "abstain"
    assert fashion.compose_outfit(intent, [sneaker_generique])["decision"] == "abstain"
    solution = fashion.compose_outfit(intent, [futsal_enfant, sneaker_generique, chaussures_adultes])
    assert solution["decision"] == "recommend"
    assert solution["items"][0]["name"] == chaussures_adultes.name
