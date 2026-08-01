"""Tests de la taxonomie FILON.

Le cas fondateur est celui constaté en production : une robe rangée par le
marchand sous « Men's Clothing ».
"""

from __future__ import annotations

import pytest

from app.services import taxonomy as t


class TestProductNameWinsOverMerchantCategory:
    def test_the_production_bug_a_dress_filed_under_mens_clothing(self):
        assert t.classify(
            "Men's Clothing",
            "Women's Clothing Popular Long-sleeved T-shirt",
        ) == t.MODE_FEMME

    def test_a_mens_shirt_stays_in_menswear(self):
        assert t.classify("Men's Clothing", "OLYMP Luxor Modern Fit Overhemd") == t.MODE_HOMME

    def test_children_take_precedence_over_the_declared_aisle(self):
        assert t.classify("Men's Clothing", "Neptun Kids' Jacket") == t.MODE_ENFANT

    def test_the_merchant_category_is_used_when_the_name_says_nothing(self):
        assert t.classify("Women's Clothing", "Modèle Aurora") == t.MODE_FEMME


class TestWomenContainsMen:
    """« women » contient « men » : l'ordre d'évaluation n'est pas négociable."""

    @pytest.mark.parametrize("label", ["Women's Clothing", "women's dress", "WOMEN JACKET"])
    def test_women_is_never_read_as_men(self, label):
        assert t.classify(label, "") == t.MODE_FEMME


class TestMainCategories:
    @pytest.mark.parametrize(
        "category,name,expected",
        [
            ("", "Sony WH-1000XM5 Casque audio sans fil", t.TV_SON),
            ("", "MacBook Air M2 ordinateur portable", t.INFORMATIQUE),
            ("", "iPhone 15 smartphone 128 Go", t.TELEPHONIE),
            ("", "Manette PS5 DualSense", t.GAMING),
            ("", "Pneu Michelin 205/55 R16", t.AUTO),
            ("", "EUKANUBA Droog Hondenvoer", t.ANIMALERIE),
            ("", "Rasasi Dames Fattan Eau De Parfum", t.BEAUTE),
            ("", "Lampes de chevet Finesse Marbre Laiton", t.MAISON),
            ("", "Poussette bébé 3 roues", t.BEBE),
            ("", "Nike Air Max sneakers", t.CHAUSSURES),
            ("", "Montre automatique acier", t.BIJOUX),
            ("", "Parquet en Chêne Premium Chevron", t.JARDIN),
        ],
    )
    def test_classifies_from_the_product_name(self, category, name, expected):
        assert t.classify(category, name) == expected


class TestRefusesToGuess:
    def test_unknown_returns_none_rather_than_a_wrong_aisle(self):
        assert t.classify("Divers", "Article 12345") is None
        assert t.classify(None, None) is None
        assert t.classify("", "") is None

    def test_every_result_belongs_to_the_published_taxonomy(self):
        samples = [
            ("Men's Clothing", "Women's dress"),
            ("", "Casque audio"),
            ("", "Croquettes pour chien"),
            ("Divers", "Article inconnu"),
        ]
        for category, name in samples:
            result = t.classify(category, name)
            assert result is None or result in t.ALL_CATEGORIES


class TestClothingDoesNotShortCircuitOtherRules:
    """Un libellé vestimentaire sans public identifié ne doit pas tout bloquer."""

    def test_sportswear_reaches_the_sport_aisle(self):
        assert t.classify("", "Pantalon de jogging Écosse Travel") == t.SPORT
        assert t.classify("Men's Clothing", "tight-fitting hip yoga pants") == t.SPORT

    def test_female_only_garments_need_no_explicit_marker(self):
        assert t.classify("", "Robe de soirée longue") == t.MODE_FEMME
        assert t.classify("", "Jupe plissée midi") == t.MODE_FEMME
