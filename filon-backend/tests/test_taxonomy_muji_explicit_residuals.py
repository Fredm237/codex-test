from app.services import taxonomy as t


def test_muji_ballpoint_pen_is_stationery():
    name = "MUJI Stylo à bille gel 0,5 mm noir"
    assert t.classify(None, name, merchant_name="MUJI France") == t.CULTURE
    assert t.classify_subcategory(t.CULTURE, name) == "Papeterie & Bureau"


def test_muji_storage_box_is_household_storage():
    name = "MUJI Boîte de rangement transparente 25 L"
    assert t.classify(None, name, merchant_name="MUJI France") == t.MAISON
    assert t.classify_subcategory(t.MAISON, name) == "Rangement & Boîtes aux lettres"


def test_muji_stoneware_cup_is_kitchenware():
    name = "MUJI Tasse en grès blanc 300 ml"
    assert t.classify(None, name, merchant_name="MUJI France") == t.MAISON
    assert t.classify_subcategory(t.MAISON, name) == "Vaisselle & Cuisine"


def test_muji_pine_shelf_is_furniture():
    name = "MUJI Étagère en pin 5 niveaux"
    assert t.classify(None, name, merchant_name="MUJI France") == t.MAISON
    assert t.classify_subcategory(t.MAISON, name) == "Meubles"


def test_muji_sensitive_skin_toner_is_face_care():
    name = "MUJI Eau tonique pour peaux sensibles 300 ml"
    assert t.classify(None, name, merchant_name="MUJI France") == t.BEAUTE
    assert t.classify_subcategory(t.BEAUTE, name) == "Soins visage"


def test_muji_women_socks_are_womens_fashion():
    name = "MUJI Socquettes pour femme noir 23-25 cm"
    assert t.classify(None, name, merchant_name="MUJI France") == t.MODE_FEMME


def test_generic_fountain_pen_remains_unclassified():
    assert t.classify(None, "Stylo plume Studio noir") is None


def test_unqualified_lotion_remains_unclassified():
    assert t.classify(None, "Lotion de riz fermentée") is None
