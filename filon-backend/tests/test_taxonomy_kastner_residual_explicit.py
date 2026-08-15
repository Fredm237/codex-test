from app.services import taxonomy as t


def test_kastner_double_face_powder_is_makeup():
    name = "CLINIQUE Super-Poudre - Poudre Double Face Oil-Free 10g"
    assert t.classify(None, name, merchant_name="Kastner & Öhler") == t.BEAUTE
    assert t.classify_subcategory(t.BEAUTE, name) == "Maquillage"


def test_kastner_face_cream_is_face_care():
    name = "LANCÔME Crème pour le visage - Rénergie Crème 50ml"
    assert t.classify(None, name, merchant_name="Kastner & Öhler") == t.BEAUTE
    assert t.classify_subcategory(t.BEAUTE, name) == "Soins visage"


def test_kastner_kitchen_press_is_kitchenware():
    name = "WMF Presse-purée Gourmet argent"
    assert t.classify(None, name, merchant_name="Kastner & Öhler") == t.MAISON
    assert t.classify_subcategory(t.MAISON, name) == "Vaisselle & Cuisine"


def test_kastner_espresso_maker_is_kitchenware():
    name = "ALESSI Machine à expresso / 3 tasses argent"
    assert t.classify(None, name, merchant_name="Kastner & Öhler") == t.MAISON
    assert t.classify_subcategory(t.MAISON, name) == "Vaisselle & Cuisine"


def test_kastner_bath_mat_is_household_linen():
    name = "VOSSEN Tapis de bain FEELING 60x60cm"
    assert t.classify(None, name, merchant_name="Kastner & Öhler") == t.MAISON
    assert t.classify_subcategory(t.MAISON, name) == "Linge de maison"


def test_kastner_german_hosiery_is_generic_mode_without_gender_inference():
    assert t.classify(None, "WOLFORD Strumpfhose Satin Opaque 50", merchant_name="Kastner & Öhler") == t.MODE


def test_generic_writing_tool_remains_unclassified():
    assert t.classify(None, "LAMY Stylo plume Studio 67 Noir Medium", merchant_name="Kastner & Öhler") is None
