"""Régression : sérialiser une offre issue d'un flux Awin ne doit pas échouer.

Deuxième panne 500 constatée en production sur `POST /api/advise` le
04/08/2026, révélée après correction du tri de l'agent décision :

    ValidationError: 2 validation errors for ProductAnalysis
    best_offer.delivery_days   Input should be a valid integer, input=None
    best_offer.warranty_months Input should be a valid integer, input=None

Le schéma exigeait des entiers non nuls alors que `catalog_source._shape()`
pose délibérément ces champs à `None` : les flux marchands ne portent ni délai
de livraison ni durée de garantie, et le commentaire du code précise qu'il vaut
mieux `None` que d'inventer une valeur. Schéma et source se contredisaient.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.schemas.advise import Offer, ProductAnalysis
from app.services.catalog_source import _shape


class _FakeOffer:
    def __init__(self, price):
        self.price = price
        self.currency = "EUR"
        self.updated_at = datetime.now(UTC)
        self.deep_link = "https://exemple.test/produit"
        self.in_stock = True


class _FakeMerchant:
    name = "Marchand Test"
    slug = "marchand-test"


def test_offre_sans_delai_ni_garantie_est_acceptee():
    """Le cas exact de la panne."""
    offre = Offer(merchant="Zalando", price=59.9, delivery_days=None,
                  warranty_months=None)
    assert offre.delivery_days is None
    assert offre.warranty_months is None


def test_offre_avec_valeurs_reste_valide():
    """La rétrocompatibilité avec le catalogue de démonstration est préservée."""
    offre = Offer(merchant="Amazon", price=649.0, delivery_days=1,
                  warranty_months=24)
    assert offre.delivery_days == 1
    assert offre.warranty_months == 24


def test_champs_omis_valent_none():
    offre = Offer(merchant="Fnac", price=100.0)
    assert offre.delivery_days is None
    assert offre.delivery_cost is None
    assert offre.warranty_months is None
    assert offre.in_stock is None


def test_analyse_complete_avec_offre_awin_reelle():
    """La forme produite par _shape() doit traverser le schéma sans erreur."""
    produit = _shape(
        product_id="0705632189061",
        name="Baskets de running homme",
        brand="Marque",
        category="chaussures",
        image=None,
        offers=[(_FakeOffer(59.9), _FakeMerchant())],
    )
    # C'est bien la source qui pose None, pas une hypothèse du test.
    assert produit["offers"][0]["delivery_days"] is None
    assert produit["offers"][0]["delivery_cost"] is None
    assert produit["offers"][0]["currency"] == "EUR"
    assert produit["offers"][0]["observed_at"] is not None
    assert produit["offers"][0]["warranty_months"] is None
    assert produit["rating"] is None

    analyse = ProductAnalysis(
        product_id=produit["product_id"],
        name=produit["name"],
        best_offer=produit["offers"][0],
        real_price=59.9,
    )
    assert analyse.best_offer.delivery_days is None
    assert analyse.best_offer.delivery_cost is None
    assert analyse.best_offer.currency == "EUR"
    assert analyse.best_offer.observed_at is not None
    assert analyse.real_price == 59.9
    assert analyse.shipping_cost_known is False


def test_le_prix_reste_obligatoire():
    """La souplesse ajoutée ne doit pas relâcher les champs essentiels."""
    with pytest.raises(ValidationError):
        Offer(merchant="Zalando")
