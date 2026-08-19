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
from app.services import relevance


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


def test_sans_termes_le_comportement_documentaire_est_conserve():
    """La signature reste rétrocompatible : sans demande, on note la documentation."""
    tenue = _tenue("Peu importe", "Peu importe non plus")
    assert fashion._confidence(tenue) == fashion._confidence(tenue, None)
