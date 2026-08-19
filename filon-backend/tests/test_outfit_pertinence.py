"""Régression Outfit Studio : la confiance doit suivre la correspondance.

Constaté en production le 19/08/2026 sur `POST /api/intelligence/outfit/analyse` :
à « une tenue pour un mariage en été », le studio composait une tenue notée
`confidence_score: 100`, `confidence_band: "high"`, dont la chaussure était
« Siso Régulateur de hauteur de panneau SHOES en plastique » à 0,70 € et
l'accessoire un sac à 0,00 €.

La confiance ne mesurait que la complétude documentaire — un prix, un marchand,
une disponibilité, au moins deux pièces. Une pièce parfaitement hors sujet la
laissait donc à 100.
"""

from __future__ import annotations

from app.intelligence import fashion
from app.intelligence.contracts import CoreOfferSnapshot
from app.services import relevance, taxonomy


class _Offre:
    """Instantané minimal, au contrat de CoreOfferSnapshot utilisé par _confidence."""

    def __init__(self, name: str, availability: str = "in_stock", kind: str = "physical_product"):
        self.name = name
        self.availability = availability
        self.offer_kind = kind
        self.price = 10.0
        self.offer_id = 1
        self.id = 1


def _tenue(*noms: str) -> list[fashion.OutfitItem]:
    roles = ["base", "footwear", "accessory"]
    return [fashion.OutfitItem(offer=_Offre(n), role=r) for n, r in zip(noms, roles)]


def _snapshot(offer_id: int, name: str, category: str, subcategory: str) -> CoreOfferSnapshot:
    return CoreOfferSnapshot(
        offer_id=offer_id,
        catalog_product_id=None,
        name=name,
        brand=None,
        filon_category=category,
        filon_subcategory=subcategory,
        offer_kind="physical_product",
        price=20.0,
        currency="EUR",
        availability="in_stock",
        image_url="https://images.example/item.jpg",
        deep_link="https://merchant.example/item",
        merchant_id=1,
        merchant_name="Marchand test",
        merchant_region="BE",
        observed_at=None,
    )


def test_une_piece_hors_sujet_fait_chuter_la_confiance():
    termes = relevance.mots("une tenue pour un mariage en été")
    tenue = _tenue(
        "Robe de soirée longue en dentelle pour mariage",
        "Siso Régulateur de hauteur de panneau SHOES en plastique",
    )
    assert fashion._confidence(tenue, termes) < 80, (
        "Une chaussure qui n'en est pas une doit interdire la confiance élevée"
    )


def test_la_confiance_reste_haute_quand_tout_correspond():
    termes = relevance.mots("des chaussures de running homme")
    tenue = _tenue(
        "Chaussures de running homme Asics Gel-Contend",
        "Chaussures de running homme Nike Revolution",
    )
    assert fashion._confidence(tenue, termes) >= 80


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
    assert solution["confidence_score"] >= 55


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


def test_sans_termes_le_comportement_documentaire_est_conserve():
    """La signature reste rétrocompatible : sans demande, on note la documentation."""
    tenue = _tenue("Peu importe", "Peu importe non plus")
    assert fashion._confidence(tenue) == fashion._confidence(tenue, None)
