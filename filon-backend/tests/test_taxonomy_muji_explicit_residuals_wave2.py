from app.services import taxonomy as t


def test_muji_women_dotted_socks_are_womens_fashion():
    name = "Soquettes à pois et à bordures confortables pour femme"
    assert t.classify("Meilleures ventes", name, merchant_name="MUJI France") == t.MODE_FEMME


def test_muji_cereal_mug_is_kitchenware():
    name = "Tasse à céréales en grès - Gris Beige, Ø 11.5 cm"
    assert t.classify("Nouveautés", name, merchant_name="MUJI France") == t.MAISON
    assert t.classify_subcategory(t.MAISON, name) == "Vaisselle & Cuisine"


def test_muji_insulated_mug_is_kitchenware():
    name = "Tasse isotherme avec couvercle - 400 ml"
    assert t.classify("Nouveautés", name, merchant_name="MUJI France") == t.MAISON
    assert t.classify_subcategory(t.MAISON, name) == "Vaisselle & Cuisine"


def test_muji_stackable_storage_box_is_household_storage():
    name = "Boîte de rangement empilable en acrylique à 3 tiroirs"
    assert t.classify("Rangements", name, merchant_name="MUJI France") == t.MAISON
    assert t.classify_subcategory(t.MAISON, name) == "Rangement & Boîtes aux lettres"


def test_muji_rattan_storage_basket_is_household_storage():
    name = "Panier de rangement ouvert en rotin - 26 x 36 x 12 cm"
    assert t.classify("Rangements", name, merchant_name="MUJI France") == t.MAISON
    assert t.classify_subcategory(t.MAISON, name) == "Rangement & Boîtes aux lettres"


def test_muji_wooden_hanger_is_household_storage():
    name = "Cintre en hêtre"
    assert t.classify("Utilitaire", name, merchant_name="MUJI France") == t.MAISON
    assert t.classify_subcategory(t.MAISON, name) == "Rangement & Boîtes aux lettres"


def test_muji_bamboo_corner_shelf_is_furniture():
    name = "Étagère d'angle en bambou à 3 niveaux"
    assert t.classify("Conçus pour organiser", name, merchant_name="MUJI France") == t.MAISON
    assert t.classify_subcategory(t.MAISON, name) == "Meubles"


def test_muji_narrow_walnut_shelf_is_furniture():
    name = "Étagère étroite en noyer - 3 niveaux"
    assert t.classify("Étagères", name, merchant_name="MUJI France") == t.MAISON
    assert t.classify_subcategory(t.MAISON, name) == "Meubles"


def test_muji_fountain_pen_refill_uses_explicit_stationery_source():
    name = "Recharge pour stylo-plume - encre noire, lot de 5"
    assert t.classify("Stylos et crayons", name, merchant_name="MUJI France") == t.CULTURE
    assert t.classify_subcategory(t.CULTURE, name, "Stylos et crayons") == "Papeterie & Bureau"


def test_muji_calligraphy_pen_uses_explicit_stationery_source():
    name = "Stylo calligraphie"
    assert t.classify("Mix & Match - Papeterie", name, merchant_name="MUJI France") == t.CULTURE
    assert t.classify_subcategory(t.CULTURE, name, "Mix & Match - Papeterie") == "Papeterie & Bureau"


def test_unqualified_fountain_pen_still_remains_unclassified():
    assert t.classify(None, "Stylo plume Studio noir") is None
