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
            ("Heimwerker-Zubehör", "Patte de fixation pour étagère", t.JARDIN),
            ("Cartouches d'encre", "Cartouche d'encre noire Canon", t.INFORMATIQUE),
            ("Color Lenses", "Color Lenses Ocean Blue", t.BEAUTE),
            ("Mobilier > Armoires et étagères > Rayonnage", "Bibliothèque Mini 1004 Anthracite", t.MAISON),
            ("Déco > Textiles > Tapis", "Varjo Tapis 170x240 Bleu", t.MAISON),
            ("", "Timb Eetkamerstoel Gestoffeerd Bruin/Hallingdal 368", t.MAISON),
            ("", "Epic Ronde Salontafel Ø60 cm Wit Travertijn", t.MAISON),
            ("", "Houkime Tapijt 170x240 Middernacht", t.MAISON),
            ("", "FABRIC Nagel Glazen Lampenvoet Vierkant 27x27", t.MAISON),
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

    @pytest.mark.parametrize("name", ["3 STRIPE FLEECE HOODY", "ADIBREAK CLASSIC TRACKPANT", "ACG Dri-FIT Tee"])
    def test_short_apparel_forms_land_in_generic_fashion(self, name):
        assert t.classify("", name) == t.MODE

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
            (t.TELEPHONIE, "iPhone 15 Pro 128 Go", "Smartphones"),
            (t.TELEPHONIE, "Burga Tough Backcover MagSafe pour Apple iPhone 15 Pro", "Coques & Protections"),
            (t.TELEPHONIE, "Phone Case for iPhone 15", "Coques & Protections"),
            (t.TELEPHONIE, "Screen Protector for iPhone 15", "Coques & Protections"),
            (t.TELEPHONIE, "Écran tactile Samsung Galaxy S23+ avec cadre", "Pièces détachées"),
            (t.TELEPHONIE, "Support PCB Oppo Reno16 F", "Pièces détachées"),
            (t.TELEPHONIE, "Batterie Xiaomi Redmi Note 11 Pro", "Chargeurs & Batteries"),
            (t.TELEPHONIE, "Chargeur rapide USB-C pour iPhone 15", "Chargeurs & Batteries"),
            (t.AUTO, "Pneu Michelin 205/55 R16", "Pneus"),
            (t.BEAUTE, "Rasasi Fattan Eau De Parfum", "Parfums"),
            (t.ELECTROMENAGER, "Aspirateur balai sans fil", "Aspirateurs"),
            (t.INFORMATIQUE, "Cartouche d'encre noire Canon", "Imprimantes & Consommables"),
            (t.BEAUTE, "Color Lenses Ocean Blue", "Lentilles & Regard"),
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


class TestOfferKinds:
    @pytest.mark.parametrize(
        "merchant_category,name,expected",
        [
            ("Appartement de vacances", "Appartement de vacances à Lac Balaton à partir de 154€ par nuit", t.ACCOMMODATION),
            ("Vakantieparken", "HH Hertenkamp Mobile Home", t.ACCOMMODATION),
            ("Hôtel", "Chambre d'hôtel à Bruges", t.ACCOMMODATION),
            ("Wonen & Koken > Wonen > Beddengoed", "Hotel Kussen en microvezel", t.PHYSICAL_PRODUCT),
            ("Heimwerker-Zubehör", "Coffre-fort pour hôtel Häfele", t.PHYSICAL_PRODUCT),
            ("", "Bidon ELITE Fly Teams Arkéa B&B Hotels", t.PHYSICAL_PRODUCT),
            ("", "Code Steam Game Key EU", t.DIGITAL_CONTENT),
            ("Services", "Installation de borne électrique à domicile", t.SERVICE),
            ("", "Service de montage professionnel", t.SERVICE),
            ("Heimwerker-Zubehör", "Häfele Glissière à extension partielle Acier Montage latéral, 600 mm", t.PHYSICAL_PRODUCT),
            ("Sports & Outdoor", "Palestine Flag Fine Workmanship Simple Installation Canvas Header", t.PHYSICAL_PRODUCT),
            ("Telefoon accessoires", "Coque iPhone 15 Pro MagSafe", t.TECH_ACCESSORY),
            ("", "iPhone 15 smartphone 128 Go", t.PHYSICAL_PRODUCT),
        ],
    )
    def test_detects_transactional_kind(self, merchant_category, name, expected):
        assert t.classify_offer_kind(merchant_category, name) == expected

    def test_stays_override_ambiguous_physical_words(self):
        assert t.classify("Vakantieparken", "HH Hertenkamp Mobile Home") == t.VOYAGES
        assert t.classify_subcategory(t.VOYAGES, "HH Hertenkamp Mobile Home") == "Campings & Parcs"

    @pytest.mark.parametrize(
        "merchant_category,expected_subcategory",
        [
            ("Appartements", "Villas & Appartements"),
            ("Appartementen", "Villas & Appartements"),
            ("Villas", "Villas & Appartements"),
            ("Villen", "Villas & Appartements"),
            ("Studios", "Villas & Appartements"),
            ("Parcs de vacances", "Campings & Parcs"),
            ("Ferienparks", "Campings & Parcs"),
        ],
    )
    def test_bungalow_net_contextualizes_ambiguous_accommodation_categories(
        self, merchant_category, expected_subcategory
    ):
        assert t.classify_offer_kind(merchant_category, "Ref. 123", merchant_name="Bungalow.net NL BE") == t.ACCOMMODATION
        assert t.classify(merchant_category, "Ref. 123", merchant_name="Bungalow.net NL BE") == t.VOYAGES
        assert t.classify_subcategory(t.VOYAGES, "Ref. 123", merchant_category) == expected_subcategory

    def test_an_ambiguous_studio_without_booking_context_stays_unclassified(self):
        assert t.classify_offer_kind("Studios", "Ref. 123", merchant_name="Atelier photo") == t.PHYSICAL_PRODUCT
        assert t.classify("Studios", "Ref. 123", merchant_name="Atelier photo") is None

    def test_verified_gites_merchant_keeps_short_booking_titles_as_accommodation(self):
        assert t.classify_offer_kind("", "Ref. séjour 123", merchant_name="Gites FR") == t.ACCOMMODATION

    @pytest.mark.parametrize("reference", ["PKW", "MO", "OFF", "LLKW"])
    def test_tyre_specialist_context_classifies_minimal_vehicle_codes(self, reference):
        merchant = "autobandenmarkt / 123pneus BE"
        assert t.classify("250", reference, "MICHELIN", merchant) == t.AUTO
        assert t.classify_subcategory(t.AUTO, reference, "250", merchant) == "Pneus"

    def test_vehicle_code_without_tyre_specialist_context_stays_unclassified(self):
        assert t.classify("250", "PKW", "MICHELIN", "Marchand généraliste") is None

    @pytest.mark.parametrize("name", ["Paletti Sofa Middenmodule Mist", "Componibili 3-delige Kast Bio Groen"])
    def test_andlight_context_classifies_collection_names_as_home(self, name):
        assert t.classify("", name, merchant_name="Andlight BE") == t.MAISON

    def test_collection_name_without_andlight_context_stays_unclassified(self):
        assert t.classify("", "Paletti Sofa Middenmodule Mist", merchant_name="Marchand généraliste") is None

    @pytest.mark.parametrize(
        "brand,name",
        [
            ("Adidas", "SAMBA OG"),
            ("ASICS", "GEL-1130"),
            ("New Balance", "1000"),
            ("Vans", "Authentic Reissue 44"),
            ("Nike", "ACG AIR EXPLORAID"),
        ],
    )
    def test_verified_brand_models_classify_as_shoes(self, brand, name):
        assert t.classify("", name, brand) == t.CHAUSSURES

    def test_brand_model_does_not_override_an_explicit_garment(self):
        assert t.classify("", "Nike Air Max T-shirt", "Nike") == t.MODE

    def test_model_without_verified_brand_stays_unclassified(self):
        assert t.classify("", "SAMBA OG", "Marchand généraliste") is None

    @pytest.mark.parametrize(
        "merchant,name,expected",
        [
            ("ISOTIGER (FR)", "Joint de portes pour Renault Scenic", t.AUTO),
            ("GSMnet FR", "Support PCB Oppo Reno16 F", t.TELEPHONIE),
            ("Overhemden - NL", "John Miller Tailored Fit", t.MODE_HOMME),
            ("Milk Bar Babystore", "Référence bébé 123", t.BEBE),
            ("Bobshop FR", "Référence vélo 123", t.SPORT),
            ("tapis.fr", "Référence tapis 123", t.MAISON),
            ("Didrikson FR", "Tiril", t.MODE),
            ("TISSUS DE REVE FR", "Réf. 3812", t.LOISIRS),
            ("Smartphonehoesjes NL - BE", "Réf. 3812", t.TELEPHONIE),
            ("PrintAbout FR", "Réf. 3812", t.INFORMATIQUE),
            ("Horloge NL-BE", "Réf. 3812", t.BIJOUX),
            ("Maxi Zoo BE", "Réf. 3812", t.ANIMALERIE),
            ("Foot Store FR", "Réf. 3812", t.CHAUSSURES),
        ],
    )
    def test_verified_specialist_contexts_classify_minimal_references(self, merchant, name, expected):
        assert t.classify("", name, merchant_name=merchant) == expected

    def test_specialist_reference_without_context_stays_unclassified(self):
        assert t.classify("", "Référence modèle 123", merchant_name="Marchand généraliste") is None
        assert t.classify("", "Tiril", merchant_name="Marchand généraliste") is None
        assert t.classify("", "Réf. 3812", merchant_name="Marchand généraliste") is None

    def test_tyre_dimension_overrides_camping_model_name(self):
        category = "Les pneus industriels, pneus camion et les pneus utilitaire"
        name = "Michelin CrossClimate Camping ( 195/75 R16CP 107/105R 8PR EV Suitable )"
        assert t.classify_offer_kind(category, name, "MICHELIN") == t.PHYSICAL_PRODUCT
        assert t.classify(category, name, "MICHELIN") == t.AUTO
        assert t.classify_subcategory(t.AUTO, name, category) == "Pneus"

    def test_travel_subcategories_are_multilingual(self):
        assert t.classify("Appartement de vacances", "Appartement de vacances à Hévíz") == t.VOYAGES
        assert t.classify_subcategory(t.VOYAGES, "Appartement de vacances à Hévíz") == "Locations de vacances"
        assert t.classify_subcategory(t.VOYAGES, "Hotel kamers in Gent") == "Hôtels"

    def test_only_physical_kinds_are_ean_comparable(self):
        assert t.is_ean_comparable(t.PHYSICAL_PRODUCT) is True
        assert t.is_ean_comparable(t.TECH_ACCESSORY) is True
        assert t.is_ean_comparable(t.ACCOMMODATION) is False
        assert t.is_ean_comparable(t.SERVICE) is False
        assert t.is_ean_comparable(t.DIGITAL_CONTENT) is False


class TestTaxonomyQualitySignals:
    @pytest.mark.parametrize(
        "category,subcategory,kind,name,expected",
        [
            (t.MODE_FEMME, "Robes", t.PHYSICAL_PRODUCT, "Patron KnowMe Robe", t.QUALITY_SEWING_SUPPORT_IN_FASHION),
            (t.TELEPHONIE, "Smartphones", t.PHYSICAL_PRODUCT, "Écran OLED Samsung Galaxy", t.QUALITY_PHONE_PART_AS_SMARTPHONE),
            (t.VOYAGES, "Hôtels", t.ACCOMMODATION, "Coussin Hotel en microfibre", t.QUALITY_PHYSICAL_ITEM_AS_ACCOMMODATION),
            (t.JARDIN, "Quincaillerie", t.SERVICE, "Glissière à montage latéral", t.QUALITY_PHYSICAL_ITEM_AS_SERVICE),
        ],
    )
    def test_detects_known_high_certainty_contradictions(self, category, subcategory, kind, name, expected):
        assert t.quality_signals(category, subcategory, kind, name) == [expected]

    def test_does_not_flag_a_valid_phone_or_stay(self):
        assert t.quality_signals(t.TELEPHONIE, "Smartphones", t.PHYSICAL_PRODUCT, "iPhone 15 128 Go") == []
        assert t.quality_signals(t.VOYAGES, "Hôtels", t.ACCOMMODATION, "Chambre d'hôtel à Bruges") == []


class TestProvenResidualFamilies:
    """Familles mesurées dans les reliquats de production avant correction."""

    @pytest.mark.parametrize(
        "merchant_category,name,expected",
        [
            ("VTT > Manivelle > Adulte > Mixte", "Manivelle type 2 en alliage Praxis", t.SPORT),
            ("BMX > Casque BMX > Junior > Mixte", "Casque enfant Fly Racing Rayce Repeat", t.SPORT),
            ("Warhammer 40.000", "Warhammer 40k - Kill Team : Exodites", t.JOUETS),
            ("Crayon sourcils", "Anastasia Beverly Hills - Brow Definer Brow Pen", t.BEAUTE),
            ("Styling", "Color Wow - One Minute Transformation Crème Coiffante", t.BEAUTE),
            ("Multisports > Boxer > Adulte > Homme", "Boxers Erima (x2)", t.SPORT),
            ("Athlétisme > Cuissard > Adulte > Femme", "Cuissard femme Erima Racing", t.SPORT),
        ],
    )
    def test_classifies_measured_residual_families(self, merchant_category, name, expected):
        assert t.classify(merchant_category, name) == expected

    @pytest.mark.parametrize(
        "category,name,merchant_category,expected",
        [
            (t.SPORT, "Manivelle type 2 en alliage Praxis", "VTT > Manivelle > Adulte > Mixte", "Cyclisme"),
            (t.BEAUTE, "Anastasia Beverly Hills - Brow Definer Brow Pen", "Crayon sourcils", "Maquillage"),
            (t.BEAUTE, "Color Wow - One Minute Transformation Crème Coiffante", "Styling", "Cheveux"),
        ],
    )
    def test_assigns_measured_residual_subcategories(self, category, name, merchant_category, expected):
        assert t.classify_subcategory(category, name, merchant_category) == expected

    def test_generic_merchandise_is_not_promoted_from_a_brand_alone(self):
        assert t.classify("", "Fusion 2.0", brand="Karhu") is None
        assert t.classify("", "ROCC Duftkerze Flint", brand="Alessi") == t.MAISON


class TestPostCampaignDepthRules:
    """Cas observés après la première campagne de reliquats."""

    @pytest.mark.parametrize(
        "merchant_category,name,brand,merchant_name,expected",
        [
            (None, "Elina Parka", "Didriksons", "Didrikson FR", t.MODE),
            ("Coffrets", "Sisley - Rose Noire Kit", "Sisley", "ICI PARIS XL BE", t.BEAUTE),
            ("Bâtonnets parfumés", "SCENTO - Diffuseur D'ambiance Vanille", "SCENTO", "ICI PARIS XL BE", t.MAISON),
            ("Produits Wi-Fi", "Point d'Accès Répéteur WiFi Mercusys ME30", "Mercusys", "1FoTeam FR", t.INFORMATIQUE),
            ("Carte Mère", "Carte Mère Gigabyte B760 DS3H Gen5", "Gigabyte", "1FoTeam FR", t.INFORMATIQUE),
            ("Watercooling", "Kit Watercooling AIO Lian Li HydroShift II", "Lian-Li", "1FoTeam FR", t.INFORMATIQUE),
            ("Librairie", "Magazine - White Dwarf n°524", "Games Workshop", "1FoTeam FR", t.CULTURE),
            ("Nettoyant", "CHANEL - La Mousse Crème Nettoyante Au Camélia", "Chanel", "ICI PARIS XL BE", t.BEAUTE),
        ],
    )
    def test_classifies_post_campaign_residuals(self, merchant_category, name, brand, merchant_name, expected):
        assert t.classify(merchant_category, name, brand, merchant_name) == expected

    def test_keeps_beauty_context_as_a_last_resort(self):
        assert t.classify("", "Collection Ambre Noire", "Maison X", "ICI PARIS XL BE") == t.BEAUTE
        assert t.classify("", "Collection Ambre Noire", "Maison X", "Marchand généraliste") is None

    def test_assigns_subcategories_for_explicit_post_campaign_terms(self):
        assert t.classify_subcategory(t.BEAUTE, "CHANEL Brow Definer", "Crayon sourcils") == "Maquillage"
        assert t.classify_subcategory(t.BEAUTE, "Color Wow crème coiffante", "Styling") == "Cheveux"
