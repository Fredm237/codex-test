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


class TestEnrichedFromRealFeedLabels:
    """Libellés relevés dans les 243 212 offres que rien ne reconnaissait."""

    @pytest.mark.parametrize(
        "label,expected",
        [
            ("Jewelry & Accessories", t.BIJOUX),
            ("Apparel Accessories", t.ACCESSOIRES),
            ("Men's Tops", t.MODE_HOMME),
            ("Men's Socks", t.MODE_HOMME),
            ("Men's Trousers", t.MODE_HOMME),
            ("Shoes", t.CHAUSSURES),
            ("Wheels", t.AUTO),
            ("Equipamiento deportivo", t.SPORT),      # espagnol
            ("Luggage & Bags", t.BAGAGERIE),
            ("Beauty & Health", t.BEAUTE),
            ("Software > Video Game Software", t.GAMING),
            ("Haircare", t.BEAUTE),
            ("Schoonmaak", t.MAISON),                 # néerlandais
            ("Verzorgingsproducten", t.BEAUTE),
            ("Gezicht- & huidverzorging", t.BEAUTE),
            ("Wassen, strijken & drogen", t.ELECTROMENAGER),
            ("Tuingereedschap & -apparatuur", t.JARDIN),
            ("Mother & Kids", t.BEBE),
            ("Make up", t.BEAUTE),
            ("Shampoo & conditioner", t.BEAUTE),
            ("Fragrance", t.BEAUTE),
            ("Cellphones & Telecommunications", t.TELEPHONIE),
            ("Home Appliances", t.ELECTROMENAGER),
            ("Nails", t.BEAUTE),
            ("Patrons", t.LOISIRS),
            ("Hygiëne", t.SANTE),                     # tréma, pas accent grave
        ],
    )
    def test_top_unclassified_labels_are_now_recognised(self, label, expected):
        assert t.classify(label, "") == expected

    def test_genderless_clothing_lands_in_the_generic_aisle(self):
        """Plutôt qu'un rayon genré au hasard, ou nulle part."""
        assert t.classify("Underwear & Sleepwears", "") == t.MODE
        assert t.classify("", "Pyjama flanelle sans couture") == t.MODE

    def test_the_generic_aisle_never_overrides_an_identified_audience(self):
        assert t.classify("Underwear & Sleepwears", "Pyjama pour femme") == t.MODE_FEMME
        assert t.classify("Men's Tops", "Polo ERREA Team") == t.MODE_HOMME


class TestSubcategories:
    """Troisième niveau : le rayon est connu, les motifs sont donc plus sûrs."""

    @pytest.mark.parametrize(
        "category,name,expected",
        [
            (t.CHAUSSURES, "Nike Air Max sneakers homme", "Baskets & Sneakers"),
            (t.CHAUSSURES, "Bottines femme cuir noir", "Bottes & Bottines"),
            (t.CHAUSSURES, "Closed Toe Platform Mules Chunky Heels", "Escarpins & Talons"),
            (t.MODE_HOMME, "Stenströms Regular Fit Chemise bleu", "Chemises"),
            (t.MODE_HOMME, "Polo ERREA Team", "T-shirts & Polos"),
            (t.MODE_FEMME, "Robe de soirée longue", "Robes"),
            (t.BIJOUX, "Hip Hop Diamond Necklace Pendant", "Colliers & Pendentifs"),
            (t.BAGAGERIE, "Sac à dos randonnée 30L", "Sacs à dos"),
            (t.INFORMATIQUE, "MacBook Air M2 ordinateur portable", "Ordinateurs portables"),
            (t.AUTO, "Pneu Michelin 205/55 R16", "Pneus"),
            (t.BEAUTE, "Rasasi Fattan Eau De Parfum", "Parfums"),
            (t.ELECTROMENAGER, "Aspirateur balai sans fil", "Aspirateurs"),
        ],
    )
    def test_classifies_within_its_aisle(self, category, name, expected):
        assert t.classify_subcategory(category, name) == expected

    def test_returns_none_outside_a_mapped_aisle(self):
        assert t.classify_subcategory(t.ALIMENTATION, "Café en grains") is None
        assert t.classify_subcategory(None, "Peu importe") is None

    def test_returns_none_when_nothing_matches(self):
        assert t.classify_subcategory(t.CHAUSSURES, "Article 12345") is None

    def test_every_subcategory_belongs_to_its_declared_aisle(self):
        for category, rules in t.SUBCATEGORIES.items():
            assert category in t.ALL_CATEGORIES
            labels = [label for label, _ in rules]
            assert len(labels) == len(set(labels)), f"doublon dans {category}"
            assert t.subcategories_of(category) == labels


class TestDepartements:
    """Un département n'existe pas en base : il doit s'étendre à ses rayons.

    Sans cette extension, sélectionner « Beauté & Santé » dans le catalogue
    n'appliquait aucun filtre et la page renvoyait le catalogue entier.
    """

    def test_par_nom_et_par_slug(self):
        from app.services.taxonomy import categories_of_department, slug_of

        par_nom = categories_of_department("Beauté & Santé")
        par_slug = categories_of_department(slug_of("Beauté & Santé"))
        assert par_nom == par_slug
        assert par_nom, "le département doit rendre au moins un rayon"

    def test_casse_et_espaces_ignorés(self):
        from app.services.taxonomy import categories_of_department

        assert categories_of_department("  high-tech  ") == categories_of_department("High-Tech")

    def test_departement_inconnu_ne_rend_rien(self):
        from app.services.taxonomy import categories_of_department

        assert categories_of_department("Rayon Inexistant") == []
        assert categories_of_department("") == []

    def test_tous_les_departements_sont_atteignables_par_slug(self):
        from app.services.taxonomy import DEPARTMENTS, categories_of_department, slug_of

        for label, categories in DEPARTMENTS:
            assert categories_of_department(slug_of(label)) == list(categories)
