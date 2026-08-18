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
            # Produits informatiques réels : l’iPhone est une compatibilité, pas l’objet vendu.
            ("Ordinateurs tablettes & accessoires", "MINIX C1 Clé USB-C vers HDMI sans fil compatible avec iPhone 15", t.INFORMATIQUE),
            ("Ordinateurs tablettes & accessoires", "ZIKE Z806 Rallonge USB-C pour iPhone 16", t.INFORMATIQUE),
            ("Ordinateurs tablettes & accessoires", "ZIKE Z850 SSD NVMe M2 2230 magnétique USB-C pour iPhone 16", t.INFORMATIQUE),
            # Cas public : « LIP » n’est pas du maquillage lorsque la source est Watch.
            ("Watch", "LIP Himalaya Horloge", t.BIJOUX),
            # Cas public : un ventilateur de boîtier ne relève pas de la climatisation.
            ("Ventilateur de Boîtier", "Ventilateur boitier 1stPlayer FS7 RGB - 12cm", t.INFORMATIQUE),
            ("", "Ventilateur de salon silencieux 45W", t.ELECTROMENAGER),
            # Cas public : une poignée de porte de garde-robe est de la quincaillerie, pas une robe.
            ("", "VEVOR Poignée de Porte pour Meuble Placard Garde-Robe", t.JARDIN),
            ("", "Robe femme longue plissée", t.MODE_FEMME),
            # Cas public : la jupe amovible d’un comptoir de stand est du mobilier.
            ("", "VEVOR Comptoir de Stand Table de Bar avec Jupe Amovible", t.MAISON),
            ("", "Jupe femme longue en lin", t.MODE_FEMME),
        ],
    )
    def test_classifies_from_the_product_name(self, category, name, expected):
        assert t.classify(category, name) == expected


class TestVevorLoadBinders:
    """Un classeur d’arrimage n’est pas un classeur de bureau."""

    def test_explicit_load_binder_is_vehicle_tie_down_equipment(self):
        name = (
            "VEVOR Classeurs à cliquet 10-13 mm charge de travail sécurisée 4,18 t "
            "crochets G70 pour chaînes, arrimage de charge transport remorquage"
        )
        assert t.classify(None, name, "Vevor") == t.AUTO
        assert t.classify_subcategory(t.AUTO, name) == "Arrimage & Hydraulique"

    def test_chain_load_binder_with_transport_proof_is_vehicle_equipment(self):
        name = (
            "VEVOR Chaîne d'Arrimage à Tendeur Lot de 2 Classeur à Chaîne G80 à Cliquet "
            "Capacité de Charge 5443 kg pour Transport Remorque Camion à Plateau"
        )
        assert t.classify(None, name, "Vevor") == t.AUTO
        assert t.classify_subcategory(t.AUTO, name) == "Arrimage & Hydraulique"

    def test_office_binder_is_never_sent_to_auto(self):
        assert t.classify(None, "Classeur à anneaux A4 pour documents de bureau") != t.AUTO


class TestYesStyleVerifiedSourceRoutes:
    """Les routes source YesStyle restent scellées au marchand audité."""

    def test_homogeneous_beauty_sources_are_classified_for_yesstyle_only(self):
        assert t.classify("Bath & Shower", "Produit opaque", "SOFNON", "YesStyle") == t.BEAUTE
        assert t.classify("Eyes", "Produit opaque", "MEKO", "YesStyle") == t.BEAUTE
        assert t.classify("Bath & Shower", "Produit opaque", "SOFNON", "Autre marchand") is None

    def test_toothpaste_is_health_and_lifestyle_stays_unclassified(self):
        assert t.classify("Toothpaste", "Produit opaque", "ECORO", "YesStyle") == t.SANTE
        assert t.classify("Lifestyle", "Re-Stay Re-spenser 350ml", "innisfree", "YesStyle") is None


class Test1FoTeamVerifiedSourceRoutes:
    """Les routes 1FoTeam restent attachées aux catégories source auditées."""

    def test_homogeneous_routes_reach_their_verified_aisles(self):
        assert t.classify("Famille Modélisme GamersGrass", "Produit opaque", "Gamers Grass", "1FoTeam") == t.LOISIRS
        assert t.classify("Autres Eléments de Refroidissement", "Produit opaque", "Noctua", "1FoTeam") == t.INFORMATIQUE
        assert t.classify("Jeux d'Ambiance", "Produit opaque", "Ravensburger", "1FoTeam") == t.JOUETS
        assert t.classify("Casque", "Produit opaque", "Logitech", "1FoTeam") == t.TV_SON

    def test_routes_do_not_escape_the_audited_merchant_or_mixed_sources(self):
        assert t.classify("Serveur NAS", "Produit opaque", "Synology", "Autre marchand") is None
        assert t.classify("Câbles", "Produit opaque", "générique", "1FoTeam") is None


class TestSneakidsVerifiedSourceRoutes:
    """Les routes Sneakids ne couvrent que les chemins relus intégralement."""

    def test_audited_footwear_and_baggage_routes_reach_their_verified_aisles(self):
        assert t.classify(
            "Lifestyle > Ballerines > Junior > Femme", "Produit opaque", "Gioseppo", "Sneakids FR"
        ) == t.CHAUSSURES
        assert t.classify(
            "Lifestyle > Bottines > Junior > Homme", "Produit opaque", "Birkenstock", "Sneakids FR"
        ) == t.CHAUSSURES
        assert t.classify(
            "Lifestyle > Sac de voyage > Adulte > Mixte", "Produit opaque", "Eastpak", "Sneakids FR"
        ) == t.BAGAGERIE
        assert t.classify(
            "Lifestyle > Trousse > Junior > Mixte", "Produit opaque", "Alpino", "Sneakids FR"
        ) == t.BAGAGERIE

    def test_routes_remain_scoped_and_neighbouring_sources_still_abstain(self):
        assert t.classify(
            "Lifestyle > Claquettes > Junior > Mixte", "Produit opaque", "Fila", "Autre marchand"
        ) is None
        assert t.classify(
            "Lifestyle > Blouson > Junior > Mixte", "Produit opaque", "Schott", "Sneakids FR"
        ) is None


class TestOnFightVerifiedPhysicalSportRoutes:
    """Les équipements On Fight restent physiques malgré la racine Training."""

    def test_audited_roots_are_physical_and_reach_sport(self):
        training_source = "Training > Corde à sauter > Adulte > Mixte"
        kick_boxing_source = "Kick-Boxing > Protège-tibias Kick-Boxing > Adulte > Mixte"
        assert t.classify_offer_kind(training_source, "Produit opaque", "Sveltus", "On Fight FR") == t.PHYSICAL_PRODUCT
        assert t.classify(training_source, "Produit opaque", "Sveltus", "On Fight FR") == t.SPORT
        assert t.classify_offer_kind(kick_boxing_source, "Produit opaque", "Montana", "On Fight FR") == t.PHYSICAL_PRODUCT
        assert t.classify(kick_boxing_source, "Produit opaque", "Montana", "On Fight FR") == t.SPORT

    def test_service_titles_and_other_merchants_keep_the_generic_service_rule(self):
        source = "Training > Corde à sauter > Adulte > Mixte"
        assert t.classify_offer_kind(source, "Cours de training individuel", "", "On Fight FR") == t.SERVICE
        assert t.classify_offer_kind(source, "Produit opaque", "", "Autre marchand") == t.SERVICE
        assert t.classify("Ju-Jitsu > Porte-clé > Adulte > Mixte", "Produit opaque", "Danrho", "On Fight FR") is None


class TestSportIsGoodVerifiedSportRoots:
    """Les racines Sport Is Good auditées restent des équipements physiques de Sport."""

    def test_audited_roots_are_physical_and_reach_sport(self):
        training = "Training > Corde à sauter > Adulte > Mixte"
        equestrian = "Équipement du cavalier > Chaps > Adulte > Mixte"
        assert t.classify_offer_kind(training, "Corde à sauter Sporti", "Sporti", "Sport Is Good FR") == t.PHYSICAL_PRODUCT
        assert t.classify(training, "Corde à sauter Sporti", "Sporti", "Sport Is Good FR") == t.SPORT
        assert t.classify_offer_kind(equestrian, "Chaps en cuir HORKA", "HORKA", "Sport Is Good FR") == t.PHYSICAL_PRODUCT
        assert t.classify(equestrian, "Chaps en cuir HORKA", "HORKA", "Sport Is Good FR") == t.SPORT

    def test_service_title_and_other_merchants_remain_outside_the_route(self):
        source = "Training > Corde à sauter > Adulte > Mixte"
        assert t.classify_offer_kind(source, "Formation training individuel", "", "Sport Is Good FR") == t.SERVICE
        assert t.classify_offer_kind(source, "Produit opaque", "", "Autre marchand") == t.SERVICE
        assert t.classify("Lifestyle > Trousse > Adulte > Mixte", "Produit opaque", "Eastpak", "Sport Is Good FR") is None


class TestSportIsGoodVerifiedLifestyleRoutes:
    """Les chemins Lifestyle exigent une preuve source et un objet nommé."""

    def test_audited_lifestyle_objects_reach_their_verified_aisles(self):
        assert t.classify("Lifestyle > Tongs > Adulte > Homme", "Tongs Fila Troy", "Fila", "Sport Is Good FR") == t.CHAUSSURES
        assert t.classify("Lifestyle > Trousse > Adulte > Mixte", "Trousse Eastpak Oval", "Eastpak", "Sport Is Good FR") == t.BAGAGERIE
        assert t.classify("Lifestyle > Lacets > Adulte > Mixte", "Lacets Urban Classic flat", "Urban Classic", "Sport Is Good FR") == t.ACCESSOIRES
        assert t.classify("Lifestyle > Boucles d'oreilles > Adulte > Femme", "Boucles d'oreilles femme Pieces Bree", "Pieces", "Sport Is Good FR") == t.BIJOUX
        assert t.classify("Lifestyle > Bomber > Adulte > Homme", "Bomber Alpha Industries MA-1", "Alpha Industries", "Sport Is Good FR") == t.MODE_HOMME
        assert t.classify("Lifestyle > Chemisier > Adulte > Femme", "Chemiser femme La Petite Étoile Saddie", "La Petite Étoile", "Sport Is Good FR") == t.MODE_FEMME
        assert t.classify("Lifestyle > Blouson > Junior > Femme", "Blouson fille Name it", "Name it", "Sport Is Good FR") == t.MODE_ENFANT

    def test_lifestyle_routes_stay_scoped_and_require_the_named_object(self):
        source = "Lifestyle > Tongs > Adulte > Homme"
        assert t.classify(source, "Produit opaque", "", "Sport Is Good FR") is None
        assert t.classify(source, "Tongs Fila Troy", "Fila", "Autre marchand") is None
        assert t.classify("Lifestyle > Gourde > Junior > Mixte", "Gourde acier enfant", "Rex London", "Sport Is Good FR") is None


class TestSportIsGoodFinalExplicitRoutes:
    """Les derniers objets admis conservent une preuve source et titre complète."""

    def test_final_audited_objects_reach_their_verified_aisles(self):
        assert t.classify("Santé et bien-être > Electrolytes > Adulte > Mixte", "Electrolytes Science in Sport Go Hydro Citron 4 g", "Science in Sport", "Sport Is Good FR") == t.SANTE
        assert t.classify("Santé et bien-être > Protéine > Adulte > Mixte", "Doypack Apurna Whey Fraise 750gr", "Apurna", "Sport Is Good FR") == t.SANTE
        assert t.classify("Lifestyle > Prothèse mammaire > Adulte > Femme", "Prothèse mammaire légère symétrique double gel", "Anita", "Sport Is Good FR") == t.SANTE
        assert t.classify("Automobile > Baume soin cuir > Adulte > Mixte", "Baume soin du cuir Dr Wack S100", "Dr Wack", "Sport Is Good FR") == t.AUTO
        assert t.classify("Mobilité urbaine > Kit de protection mobilité urbaine > Adulte > Mixte", "Kit de protection biomécanique comfort Hudora", "Hudora", "Sport Is Good FR") == t.SPORT

    def test_final_routes_remain_scoped_and_uncertain_objects_abstain(self):
        assert t.classify("Santé et bien-être > Electrolytes > Adulte > Mixte", "Electrolytes Science in Sport Go Hydro", "Science in Sport", "Autre marchand") is None
        assert t.classify("Lifestyle > Gourde > Junior > Mixte", "Gourde enfant Rex London", "Rex London", "Sport Is Good FR") is None
        assert t.classify("Culture et Nature > Glacière > Adulte > Mixte", "Glacière Rex London Best In Show", "Rex London", "Sport Is Good FR") is None


class Test2DekansjeVerifiedSourceRoutes:
    """Les chemins néerlandais 2dekansje restent limités aux familles relues."""

    def test_audited_sources_reach_their_verified_aisles(self):
        assert t.classify("Wonen & Koken > Koken & tafelen > Keukenmachines", "Produit opaque", "VAIVE", "2dekansje NL-BE") == t.ELECTROMENAGER
        assert t.classify("Mooi & Gezond > Gezondheid > Personenweegschalen", "e.volve Weegschaal Personenweegschaal Digitaal", "e.volve", "2dekansje NL-BE") == t.SANTE
        assert t.classify("Elektronica > Beeld & geluid > Hoofdtelefoons & oordopjes", "SoundFront Pro Draadloze Oordopjes", "SoundFront", "2dekansje NL-BE") == t.TV_SON
        assert t.classify("Hobby & Sport > Sport > Sup Board", "LifeGoods SUP Board", "LifeGoods", "2dekansje NL-BE") == t.SPORT
        assert t.classify("Hobby & Sport > Reizen & vrije tijd > Reistassen", "Eagle Creek No Matter What Duffel 60L", "Eagle Creek", "2dekansje NL-BE") == t.BAGAGERIE

    def test_routes_stay_scoped_and_reject_broad_sources(self):
        source = "Wonen & Koken > Koken & tafelen > Kleine keukenapparaten"
        assert t.classify(source, "Produit opaque", "KitchenBrothers", "Autre marchand") is None
        assert t.classify("Wonen & Koken", "Produit opaque", "", "2dekansje NL-BE") is None


class Test2DekansjeSmallKitchenObjectRoutes:
    """Le chemin hétérogène des petits appareils exige toujours un objet explicite."""

    def test_named_small_kitchen_objects_reach_their_verified_aisles(self):
        source = "Wonen & Koken > Koken & tafelen > Kleine keukenapparaten"
        assert t.classify(source, "KitchenBrothers Airfryer XXL Dual Zone - 9L", "KitchenBrothers", "2dekansje NL-BE") == t.ELECTROMENAGER
        assert t.classify(source, "Solis Vac Pro 569 Vacumeermachine", "Solis", "2dekansje NL-BE") == t.ELECTROMENAGER
        assert t.classify(source, "Digitale Personenweegschaal Gewicht & BMI", "e.volve", "2dekansje NL-BE") == t.SANTE
        assert t.classify(source, "KitchenBrothers Messenset - Messenblok", "KitchenBrothers", "2dekansje NL-BE") == t.MAISON

    def test_small_kitchen_accessories_and_consumables_remain_unclassified(self):
        source = "Wonen & Koken > Koken & tafelen > Kleine keukenapparaten"
        assert t.classify(source, "MOA Extra Glazen Kan voor Blender", "MOA", "2dekansje NL-BE") is None
        assert t.classify(source, "Solis Vacuumzakken Voedsel 20 x 30 cm", "Solis", "2dekansje NL-BE") is None
        assert t.classify(source, "Produit opaque", "", "2dekansje NL-BE") is None
        assert t.classify(source, "KitchenBrothers Airfryer XXL Dual Zone - 9L", "KitchenBrothers", "Autre marchand") is None


class Test2DekansjeCleaningObjectRoutes:
    """Le rayon ménage hétérogène exige un objet complet et explicitement nommé."""

    def test_named_cleaning_devices_and_tools_reach_verified_aisles(self):
        source = "Wonen & Koken > Schoonmaken & opruimen > Stofzuigen & schoonmaken"
        assert t.classify(source, "Auronic Steelstofzuiger Draadloos - 220 watt", "Auronic", "2dekansje NL-BE") == t.ELECTROMENAGER
        assert t.classify(source, "Perel Ultrasone Reiniger 6 L - 310 W", "Perel", "2dekansje NL-BE") == t.ELECTROMENAGER
        assert t.classify(source, "SolidStock Luxe Vloertrekker RVS - Vloerwisser", "SolidStock", "2dekansje NL-BE") == t.MAISON
        assert t.classify(source, "Ultra Clean 3-in-1 Spinning Mopset", "Ultra Clean", "2dekansje NL-BE") == t.MAISON

    def test_cleaning_consumables_and_mop_attachment_remain_unclassified(self):
        source = "Wonen & Koken > Schoonmaken & opruimen > Stofzuigen & schoonmaken"
        assert t.classify(source, "Monzana Stofzuigerzakken - 5 Laags", "Monzana", "2dekansje NL-BE") is None
        assert t.classify(source, "Livington MultiScrubber Pads - 3-delig", "Livington", "2dekansje NL-BE") is None
        assert t.classify(source, "Heldenwerk Elektrische vloerwisser - dweil opzetstuk", "Heldenwerk", "2dekansje NL-BE") is None
        assert t.classify(source, "Auronic Steelstofzuiger Draadloos - 220 watt", "Auronic", "Autre marchand") is None


class Test2DekansjeStorageObjectRoutes:
    """Le chemin Rangement reste limité aux objets domestiques ou de voyage nommés."""

    def test_named_storage_objects_reach_verified_aisles(self):
        source = "Wonen & Koken > Schoonmaken & opruimen > Opbergen"
        assert t.classify(source, "TRVLMORE Handbagage Koffer met Wielen", "TRVLMORE", "2dekansje NL-BE") == t.BAGAGERIE
        assert t.classify(source, "Mica Decorations Opbergmand met Deksel", "Mica Decorations", "2dekansje NL-BE") == t.MAISON
        assert t.classify(source, "SoBuy Smalle Schoenenkast met 2 Kleppen", "SoBuy", "2dekansje NL-BE") == t.MAISON
        assert t.classify(source, "O'DADDY Wasmand 3 Vakken - Wassorteerder", "O'DADDY", "2dekansje NL-BE") == t.MAISON

    def test_storage_leisure_objects_and_other_merchants_remain_unclassified(self):
        source = "Wonen & Koken > Schoonmaken & opruimen > Opbergen"
        assert t.classify(source, "Redcliffs Tentorganizer - Hangorganizer 7 Vaks", "Redcliffs", "2dekansje NL-BE") is None
        assert t.classify(source, "Coast Buiten fietsenstalling - Draagbare garage", "Coast", "2dekansje NL-BE") is None
        assert t.classify(source, "Mica Decorations Opbergmand met Deksel", "Mica Decorations", "Autre marchand") is None


class Test2DekansjeLaundryObjectRoutes:
    """Le chemin Lavage n’accepte que les appareils ou supports explicitement nommés."""

    def test_named_laundry_objects_reach_verified_aisles(self):
        source = "Wonen & Koken > Schoonmaken & opruimen > Wassen, drogen & strijken"
        assert t.classify(source, "VAIVE SteamMaster 2600 Strijkijzer - Stoomstrijkijzer", "VAIVE", "2dekansje NL-BE") == t.ELECTROMENAGER
        assert t.classify(source, "Vlectro Elektrisch droogrek - Opvouwbaar & Verwarmd", "Vlectro", "2dekansje NL-BE") == t.ELECTROMENAGER
        assert t.classify(source, "BRASQ Droogtoren 4 Lagen - Droogrek", "BRASQ", "2dekansje NL-BE") == t.MAISON
        assert t.classify(source, "Yaheetech Wasmand met Deksel 96L", "Yaheetech", "2dekansje NL-BE") == t.MAISON

    def test_laundry_consumables_and_intruders_remain_unclassified(self):
        source = "Wonen & Koken > Schoonmaken & opruimen > Wassen, drogen & strijken"
        assert t.classify(source, "Lenor Wasverzachter Fresh Air Morning Fresh", "Lenor", "2dekansje NL-BE") is None
        assert t.classify(source, "Scanpart wasdrogerballen van wol", "Scanpart", "2dekansje NL-BE") is None
        assert t.classify(source, "AyeSense 8 in 1 Air Duster Pro", "AyeSense", "2dekansje NL-BE") is None
        assert t.classify(source, "BRASQ Droogtoren 4 Lagen - Droogrek", "BRASQ", "Autre marchand") is None


class Test2DekansjeHobbySportObjectRoutes:
    """Le chemin Hobby & Sport accepte seulement les équipements sportifs nommés."""

    def test_named_sport_objects_reach_sport(self):
        source = "Hobby & Sport"
        assert t.classify(source, "Dartset Winmau pro kabinet, bord en pijlen", "Winmau", "2dekansje NL-BE") == t.SPORT
        assert t.classify(source, "LifeGoods SUP Board Allround Compact", "LifeGoods", "2dekansje NL-BE") == t.SPORT
        assert t.classify(source, "Coast Mini Trampoline Opvouwbare Fitnesstrampoline", "Coast", "2dekansje NL-BE") == t.SPORT
        assert t.classify(source, "Julbo Fast Lane Rennfietshelm", "Julbo", "2dekansje NL-BE") == t.SPORT

    def test_creative_and_ambiguous_hobby_objects_remain_unclassified(self):
        source = "Hobby & Sport"
        assert t.classify(source, "Rubye Diamond Painting Volwassenen", "Rubye", "2dekansje NL-BE") is None
        assert t.classify(source, "EarthVision Metaaldetector TerraWave", "EarthVision", "2dekansje NL-BE") is None
        assert t.classify(source, "Dartset Winmau pro kabinet, bord en pijlen", "Winmau", "Autre marchand") is None


class Test2DekansjeHealthObjectRoutes:
    """Le chemin Santé reste borné aux dispositifs de santé explicitement cités."""

    def test_named_health_objects_reach_health(self):
        source = "Mooi & Gezond > Gezondheid"
        assert t.classify(source, "ACON Flowflex Zelftest Corona, Covid 19", "ACON Flowflex", "2dekansje NL-BE") == t.SANTE
        assert t.classify(source, "Gandria Pillendoos 7 Dagen - Medicijndoos", "Gandria", "2dekansje NL-BE") == t.SANTE
        assert t.classify(source, "Medzone Rollator Lichtgewicht en Opvouwbaar", "Medzone", "2dekansje NL-BE") == t.SANTE
        assert t.classify(source, "Panacea LED Rood & Nabij-Infrarood Lamp - Lichttherapie", "Panacea", "2dekansje NL-BE") == t.SANTE

    def test_health_intruders_and_other_merchants_remain_unclassified(self):
        source = "Mooi & Gezond > Gezondheid"
        assert t.classify(source, "Monzana Digitale watertester met LCD-display", "Monzana", "2dekansje NL-BE") is None
        assert t.classify(source, "Faas Wiebeloogjes - Zelfklevende Hobby Oogjes", "Faas", "2dekansje NL-BE") is None
        assert t.classify(source, "Gandria Pillendoos 7 Dagen - Medicijndoos", "Gandria", "Autre marchand") is None


class Test2DekansjeTranslatedObjectRoutes:
    """Le marqueur Vertaald est un confinement de flux, jamais une destination."""

    def test_explicit_translated_objects_reach_verified_aisles(self):
        assert t.classify("Vertaald > Frans", "Yolora Oorbellen - Rond - Zilver", "Yolora", "2dekansje NL-BE") == t.BIJOUX
        assert t.classify("Vertaald", "Umbro Voetbaldoel - Metaal", "Umbro", "2dekansje NL-BE") == t.SPORT
        assert t.classify("Vertaald > Frans", "Lifeproducts Elektrisch Warmtekussen", "Lifeproducts", "2dekansje NL-BE") == t.SANTE
        assert t.classify("Vertaald", "alpina Contactgrill - Tosti Apparaat", "alpina", "2dekansje NL-BE") == t.ELECTROMENAGER

    def test_translation_marker_never_creates_a_broad_route(self):
        assert t.classify("Vertaald > Frans", "Coast Schilderezel met Lade - Beukenhout", "Coast", "2dekansje NL-BE") is None
        assert t.classify("Vertaald", "Coast Artificial Fig Tree Art Plant Decoratie", "Coast", "2dekansje NL-BE") is None
        assert t.classify("Vertaald > Frans", "Umbro Voetbaldoel - Metaal", "Umbro", "Autre marchand") is None


class Test2DekansjeSecondBatchSourceRoutes:
    """Les familles résiduelles validées restent bornées à leurs chemins exacts."""

    def test_second_batch_reaches_the_verified_aisles(self):
        assert t.classify("Hobby & Sport > Sport > Vechtsport", "Joya Fightgear scheenbeschermers", "Joya", "2dekansje NL-BE") == t.SPORT
        assert t.classify("Hobby & Sport > Reizen & vrije tijd > Tenten", "SoBuy Campingtent 1-Persoons", "SoBuy", "2dekansje NL-BE") == t.SPORT
        assert t.classify("Mooi & Gezond > Gezondheid > Thermometers", "Bintoi Digitale Thermometer", "Bintoi", "2dekansje NL-BE") == t.SANTE
        assert t.classify("Elektronica > Mobiele telefoons > Opladers, batterijen & autoladers", "Philips Draadloze Oplader 10W", "Philips", "2dekansje NL-BE") == t.TELEPHONIE
        assert t.classify("Elektronica > Huistelefoons", "Philips DECT Huistelefoon", "Philips", "2dekansje NL-BE") == t.TELEPHONIE
        assert t.classify("Elektronica > Beeld & geluid > Beamers", "Spoused Beamer Full-HD", "Spoused", "2dekansje NL-BE") == t.TV_SON
        assert t.classify("Hobby & Sport > Boeken", "Grow, Cook & Eat It", "", "2dekansje NL-BE") == t.CULTURE

    def test_second_batch_stays_scoped_and_does_not_promote_parent_sources(self):
        assert t.classify("Elektronica > Huistelefoons", "Philips DECT Huistelefoon", "Philips", "Autre marchand") is None
        assert t.classify("Hobby & Sport > Reizen & vrije tijd", "Produit opaque", "", "2dekansje NL-BE") is None
        assert t.classify("Elektronica", "Produit opaque", "", "2dekansje NL-BE") is None

    def test_sport_equipment_with_training_in_its_name_is_physical(self):
        source = "Hobby & Sport > Sport > Overige (Sport)"
        goal = "Dunlop Voetbaldoel Set - Voetbal Training Goals voor Kinderen"
        assert t.classify_offer_kind(source, goal, "Dunlop", "2dekansje NL-BE") == t.PHYSICAL_PRODUCT
        assert t.classify_offer_kind(source, "Formation training football", "", "2dekansje NL-BE") == t.SERVICE
        assert t.classify_offer_kind(source, goal, "Dunlop", "Autre marchand") == t.SERVICE


class TestBimbaYLolaVerifiedSourceRoutes:
    """Les codes source opaques ne valent que pour Bimba y Lola après audit complet."""

    def test_audited_numeric_codes_reach_their_verified_aisles(self):
        assert t.classify("6551", "Produit opaque", "BIMBA Y LOLA", "Bimba y Lola FR") == t.BAGAGERIE
        assert t.classify("187", "Produit opaque", "BIMBA Y LOLA", "Bimba y Lola FR") == t.CHAUSSURES
        assert t.classify("188", "Produit opaque", "BIMBA Y LOLA", "Bimba y Lola FR") == t.BIJOUX
        assert t.classify("1604", "Produit opaque", "BIMBA Y LOLA", "Bimba y Lola FR") == t.MODE_FEMME

    def test_numeric_routes_remain_scoped_and_mixed_codes_abstain(self):
        assert t.classify("187", "Produit opaque", "", "Autre marchand") is None
        assert t.classify("166", "Produit opaque", "BIMBA Y LOLA", "Bimba y Lola FR") is None
        assert t.classify("167", "Produit opaque", "BIMBA Y LOLA", "Bimba y Lola FR") is None

    def test_mixed_codes_require_audited_object_proof(self):
        assert t.classify("167", "Porte-clés cœurs doré", "BIMBA Y LOLA", "Bimba y Lola FR") == t.ACCESSOIRES
        assert t.classify("166", "Pochette moyenne en cuir citron", "BIMBA Y LOLA", "Bimba y Lola FR") == t.BAGAGERIE
        assert t.classify("166", "Trench court fluide col montant camel", "BIMBA Y LOLA", "Bimba y Lola FR") == t.MODE
        assert t.classify("166", "Body brodé moutarde", "BIMBA Y LOLA", "Bimba y Lola FR") == t.MODE
        assert t.classify("166", "Ras-de-cou métallique", "BIMBA Y LOLA", "Bimba y Lola FR") == t.BIJOUX

    def test_mixed_codes_remain_local_and_opaque_titles_still_abstain(self):
        assert t.classify("166", "Trench court fluide col montant camel", "", "Autre marchand") is None
        assert t.classify("167", "Triangle à rayures écru", "BIMBA Y LOLA", "Bimba y Lola FR") is None


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
            ("Tandheelkunde", t.SANTE),
            ("Health Products", t.SANTE),
            ("Computer & Office", t.INFORMATIQUE),
            ("Équipement > Équipement militaire > Sacs > Sacs", t.BAGAGERIE),
            ("Peintures AK Interactive - 3Gen.", t.LOISIRS),
            ("Figuren & actiehelden", t.JOUETS),
            ("Polshorloges", t.BIJOUX),
            ("Reinigingsmiddel", t.MAISON),
            ("Carrelage Mur Intérieur", t.JARDIN),
            ("Habillement > Couvre-chef > Bérets", t.MODE),
            ("Health & Wellness", t.SANTE),
            ("Mondwater & floss", t.SANTE),
            ("Hand- & voetverzorging", t.BEAUTE),
            ("Sports & Outdoor", t.SPORT),
            ("Jeux pour Famille / Amis", t.JOUETS),
            ("Eten & drinken", t.ALIMENTATION),
            ("Wonen & Koken > Wonen > Kasten", t.MAISON),
            ("Furniture > Office Furniture > Office & Desk Chairs", t.MAISON),
            ("Wonen & Koken > Klimaatbeheersing > Verwarming", t.MAISON),
            ("Animaux", t.ANIMALERIE),
            ("Peintures Citadel GW", t.LOISIRS),
            ("Creme, gel & olie", t.BEAUTE),
            ("Sonnebrandcreme & aftersun", t.BEAUTE),
            ("Carrelage Sol Intérieur", t.JARDIN),
            ("Hobby & Sport > Reizen & vrije tijd > Kampeerartikelen", t.SPORT),
            ("Lifestyle > Sabots > Junior > Mixte", t.CHAUSSURES),
            ("KoRo New > c > Petit-déj’ protéiné", t.ALIMENTATION),
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
            (t.MODE_HOMME, "OLYMP Casual Regular Fit Polo shirt Korte mouw roze", "T-shirts & Polos"),
            (t.MODE_FEMME, "Robe de soirée longue", "Robes"),
            (t.BIJOUX, "Hip Hop Diamond Necklace Pendant", "Colliers & Pendentifs"),
            (t.BAGAGERIE, "Sac à dos randonnée 30L", "Sacs à dos"),
            (t.INFORMATIQUE, "MacBook Air M2 ordinateur portable", "Ordinateurs portables"),
            (t.TELEPHONIE, "iPhone 15 Pro 128 Go", "Smartphones"),
            (t.TELEPHONIE, "Burga Tough Backcover MagSafe pour Apple iPhone 15 Pro", "Coques & Protections"),
            (t.TELEPHONIE, "Phone Case for iPhone 15", "Coques & Protections"),
            # Libellé réel du catalogue Smartphonehoesjes NL-BE : le composé
            # néerlandais ne contient pas de séparation avant « hoes ».
            (t.TELEPHONIE, "Selencia Nova Telefoonhoes met Koord voor Samsung Galaxy S24", "Coques & Protections"),
            (t.TELEPHONIE, "Screen Protector for iPhone 15", "Coques & Protections"),
            # Échantillons réellement visibles sous Smartphones avant cette vague.
            (t.TELEPHONIE, "imoshion 2 Pack Camera lens protector voor Apple iPhone 16 Pro", "Coques & Protections"),
            (t.TELEPHONIE, "Accezz Classic Tablet Case voor Samsung Galaxy Tab A11", "Coques & Protections"),
            (t.TELEPHONIE, "Support de téléphone SP Connect Universal Bike Mount", "Coques & Protections"),
            (t.TELEPHONIE, "Samsung Galaxy Watch8 44 Horloge", "Montres connectées"),
            (t.TELEPHONIE, "imoshion Oplaadkabel voor Samsung Galaxy Watch USB-C", "Chargeurs & Batteries"),
            # Seconde mesure publique post-campagne : variantes issues d'autres flux.
            (t.TELEPHONIE, "Shockproof Case voor Samsung Galaxy Tab A11", "Coques & Protections"),
            (t.TELEPHONIE, "Selencia Vivid tablethoes voor Samsung Galaxy Tab A11 Plus", "Coques & Protections"),
            (t.TELEPHONIE, "Film de protection antimicrobien 3MK Samsung Galaxy A52", "Coques & Protections"),
            (t.TELEPHONIE, "Support pour smartphone Omni Ridecase II", "Coques & Protections"),
            (t.TELEPHONIE, "Luxury Wireless Charging Phone Adapter USB-C", "Chargeurs & Batteries"),
            (t.TELEPHONIE, "No Gaps Strap for Samsung Galaxy Classic Watch", "Montres connectées"),
            # Troisième mesure publique : les derniers objets explicitement non-smartphone.
            (t.TELEPHONIE, "BeHello Hoesje iPhone 16 Soft Touch MagSafe", "Coques & Protections"),
            (t.TELEPHONIE, "Housse de protection pour smartphone universal", "Coques & Protections"),
            (t.TELEPHONIE, "Support universel pour smartphones ROKK mini", "Coques & Protections"),
            (t.TELEPHONIE, "Protection d'objectif d'appareil photo Apple iPhone 17 Pro", "Coques & Protections"),
            (t.TELEPHONIE, "Protection avant tactile OCA pour Apple iPhone 11", "Pièces détachées"),
            (t.TELEPHONIE, "Tablette Samsung Galaxy Tab A11 11 pouces", "Tablettes"),
            (t.TELEPHONIE, "Casio Edifice Bluetooth Smartphone Link Horloge", "Montres connectées"),
            # Quatrième mesure publique : les sept derniers accessoires observés.
            (t.TELEPHONIE, "Leren polsband met iPhone-oplader", "Coques & Protections"),
            (t.TELEPHONIE, "BasicPlus Schermbeschermer iPhone 11 Pro Max", "Coques & Protections"),
            (t.TELEPHONIE, "Amitec USB-oplader voor Smartphone en Tablet", "Chargeurs & Batteries"),
            (t.TELEPHONIE, "BeHello Schermprotector Glas iPhone 15 Plus", "Coques & Protections"),
            (t.TELEPHONIE, "Bicycle mobile phone bracket for Samsung iPhone", "Coques & Protections"),
            (t.TELEPHONIE, "KSIX ExtremeGlass Screen Protection iPhone 12", "Coques & Protections"),
            (t.TELEPHONIE, "Écran tactile Samsung Galaxy S23+ avec cadre", "Pièces détachées"),
            (t.TELEPHONIE, "Support PCB Oppo Reno16 F", "Pièces détachées"),
            (t.TELEPHONIE, "Batterie Xiaomi Redmi Note 11 Pro", "Chargeurs & Batteries"),
            (t.TELEPHONIE, "Chargeur rapide USB-C pour iPhone 15", "Chargeurs & Batteries"),
            # Audit global public : objets explicites encore absorbés par « iPhone ».
            (t.TELEPHONIE, "Draadloze Bluetooth Oordopjes Sport Earbuds voor Smartphone", "Écouteurs"),
            (t.TELEPHONIE, "Apple iPhone Lightning Dock - Dorée", "Chargeurs & Batteries"),
            (t.TELEPHONIE, "F9 TWS In-Ear Wireless Earbuds for iPhone Android", "Écouteurs"),
            (t.TELEPHONIE, "Kit protection de smartphone Tigra MtCase fit-clic", "Coques & Protections"),
            # Audit final public : les trois derniers accessoires résiduels.
            (t.TELEPHONIE, "Support de Travail Reballing Mijing Z20 pour Apple iPhone 16", "Pièces détachées"),
            (t.TELEPHONIE, "Samsung Galaxy Snellader met twee USB-C poorten", "Chargeurs & Batteries"),
            # Audit public suivant : ces quatre objets restaient absorbés par le
            # mot de compatibilité Smartphone/iPhone.
            (t.TELEPHONIE, "Verre de protection trempé Quad Lock iPhone 12/12 Pro", "Coques & Protections"),
            (t.TELEPHONIE, "Support de table universel Mars Gaming MA-RSS pour smartphones (Gris)", "Coques & Protections"),
            (t.TELEPHONIE, "New Wireless Headset Touch Earphones Clip-Ear Headphones Xiaomi Earphone For IPhone Earbud", "Écouteurs"),
            (t.TELEPHONIE, "Support de table universel Mars Gaming MA-RSS pour smartphones (Argent)", "Coques & Protections"),
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
            ("Telefoon accessoires", "Étui pour Samsung Galaxy S24", t.TECH_ACCESSORY),
            ("", "Étui de passeport en cuir", t.PHYSICAL_PRODUCT),
            ("", "Étui ramasse crottes", t.PHYSICAL_PRODUCT),
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
            ("ASICS", "GT-2160"),
            ("New Balance", "U2002RV1"),
            ("Salomon", "XT-QUEST"),
            ("Birkenstock", "Arizona Suede Leather"),
            ("UGG", "WMNS TASMAN II"),
            ("Jordan", "TATUM 4"),
        ],
    )
    def test_verified_brand_models_classify_as_shoes(self, brand, name):
        assert t.classify("", name, brand) == t.CHAUSSURES

    def test_brand_model_does_not_override_an_explicit_garment(self):
        assert t.classify("", "Nike Air Max T-shirt", "Nike") == t.MODE

    @pytest.mark.parametrize("name,brand", [
        ("Swoosh Series Oversize Down Vest", "Nike"),
        ("JUMPMAN AIR EMB", "Jordan"),
        ("Newel Pant", "Carhartt WIP"),
    ])
    def test_brand_model_never_turns_an_ambiguous_or_explicit_garment_into_shoes(self, name, brand):
        assert t.classify("", name, brand) != t.CHAUSSURES

    @pytest.mark.parametrize("merchant_category,name", [
        ("Taekwondo > Plastron > Adulte > Homme", "Plastron reconnu WT Kwon"),
        ("Jiu-Jitsu brésilien > Kimono", "Kimono Mizuno Gis"),
        ("Pêche du carnassier > Leurre souple", "Leurres Fox Rage Zander Pro Shad"),
        ("VTT > Cassette", "Cassette Shimano Deore CS-HG50 10V"),
    ])
    def test_observed_martial_arts_fishing_and_cycling_categories_are_sport(self, merchant_category, name):
        assert t.classify(merchant_category, name) == t.SPORT

    @pytest.mark.parametrize("name", [
        "TRIUMPH Soutien-gorge à armatures BODY MAKE-UP ILLUSION LACE",
        "CHANTELLE Culotte PLAY noir",
        "WOLFORD Collant NEON 40 lot de 2",
        "SKINY Slip lot de 2 COTTON RIB",
        "SELECTED Sakko SLHSLIM-NEIL BLZ",
        "BOSS Poloshirt Slim Fit PASSENGER",
    ])
    def test_observed_multilingual_apparel_forms_are_generic_fashion(self, name):
        assert t.classify("", name) == t.MODE

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


class TestSecondWaveFootwearModels:
    """Modèles relevés dans les reliquats BSTN, toujours croisés avec la marque."""

    @pytest.mark.parametrize(
        "brand,name",
        [
            ("Salomon", "ACS PRO LTR"),
            ("Salomon", "RX SLIDE 3.0"),
            ("Salomon", "GENESIS ADVANCED"),
            ("Hoka One One", "BONDI 9"),
            ("Hoka", "CLIFTON ONE9"),
            ("Converse", "Chuck 70 GORE-TEX"),
            ("Puma", "Deviate NITRO 4"),
            ("Puma", "Arizona Python Wns"),
            ("On", "Cloudflow 5"),
            ("Autry Action Shoes", "MEDALIST LOW WOM"),
            ("Autry", "REELWIND LOW"),
            ("Axel Arigato", "DICE T-TOE"),
            ("Birkenstock", "Naples Wrapped"),
            ("Ugg", "NEUMEL WEATHER HYBRID"),
            ("Nike", "AIR FOAMPOSITE ONE"),
        ],
    )
    def test_verified_brand_model_pairs_are_shoes(self, brand, name):
        assert t.classify(None, name, brand) == t.CHAUSSURES

    def test_a_clothing_signal_beats_a_footwear_model_pair(self):
        assert t.classify(None, "Chuck 70 T-shirt", "Converse") == t.MODE

    def test_cloud_model_does_not_classify_without_the_on_brand(self):
        assert t.classify(None, "Cloud 6", "Une autre marque") is None


class TestBoundedMerchantFallbacks:
    """Un contexte marchand ne s'applique qu'après tous les signaux produit."""

    def test_asmc_short_tactical_reference_uses_verified_outdoor_context(self):
        assert t.classify(None, "2SGL Mag Pouch BEL HK417 MKIII", "Tasmanian Tiger", "ASMC FR") == t.SPORT

    def test_maverton_short_personalised_gift_uses_verified_home_context(self):
        assert t.classify(None, "Cadeau personnalisé avec gravure", "Murrano", "Maverton FR") == t.MAISON

    def test_explicit_bag_beats_asmc_context(self):
        assert t.classify(None, "Sac à dos tactique", "Tasmanian Tiger", "ASMC FR") == t.BAGAGERIE

    def test_explicit_jewellery_beats_maverton_context(self):
        assert t.classify(None, "Bague personnalisée", "Murrano", "Maverton FR") == t.BIJOUX
