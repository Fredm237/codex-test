from app.services import taxonomy as t


def test_wardrobe_shelf_is_home_not_womens_dress():
    assert t.classify(
        None,
        "VEVOR Étagères, 2 pièces, étagères d'armoire en bois découpées sur mesure "
        "pour systèmes de placard, panneau de garde-robe à usage polyvalent",
        None,
        "Vevor FR",
    ) == t.MAISON


def test_ordinary_womens_dress_remains_womenswear():
    assert t.classify(
        "Mode femme > Robes",
        "Robe femme portefeuille en jersey",
    ) == t.MODE_FEMME


def test_eyeshadow_palette_named_red_robe_is_beauty_not_dress():
    assert t.classify(
        "Makeup",
        "UCANBE - Red Robe 15-Color Eyeshadow Palette 10.8g",
        None,
        "YesStyle FR",
    ) == t.BEAUTE


def test_red_robe_with_explicit_dress_context_remains_womenswear():
    assert t.classify(
        "Mode femme > Robes",
        "Robe rouge Red Robe satinée femme",
    ) == t.MODE_FEMME


def test_space_lady_collection_uses_explicit_mens_source():
    assert t.classify(
        "Lifestyle > T-shirt > Adulte > Homme",
        "T-shirt Grimey Space Lady Heavy Weight",
        None,
        "Sport Is Good FR",
    ) == t.MODE_HOMME


def test_explicit_women_marker_still_beats_mens_source():
    assert t.classify(
        "Men's Clothing",
        "Designer Skull Hoodies Women 240131",
        None,
        "Voghion Global",
    ) == t.MODE_FEMME
