from app.services import taxonomy as t


def test_english_hoodie_without_gender_is_generic_mode():
    assert t.classify(None, "Classic Logo Hoodie", "Polo Ralph Lauren", "bstn-fr") == t.MODE


def test_crewneck_without_gender_is_generic_mode():
    assert t.classify(None, "Basic Crewneck", "Beastin", "bstn-fr") == t.MODE


def test_longsleeve_without_gender_is_generic_mode():
    assert t.classify(None, "Chase Longsleeve", "Carhartt WIP", "bstn-fr") == t.MODE


def test_snapback_is_accessory_with_public_subcategory():
    name = "MLB New York Yankees MVP SNAPBACK"
    assert t.classify(None, name, "47", "bstn-fr") == t.ACCESSOIRES
    assert t.classify_subcategory(t.ACCESSOIRES, name, None) == "Chapeaux & Casquettes"


def test_singular_glove_is_accessory_with_public_subcategory():
    name = "Omni-Heat Touch Glove Liner"
    assert t.classify(None, name, "Columbia", "bstn-fr") == t.ACCESSOIRES
    assert t.classify_subcategory(t.ACCESSOIRES, name, None) == "Gants"


def test_hood_model_without_a_garment_term_stays_unclassified():
    assert t.classify(None, "SHOX TL", "Nike", "bstn-fr") is None
