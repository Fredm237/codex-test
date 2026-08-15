from app.services import taxonomy as t


def test_cleansing_oil_is_face_care():
    name = "Fancl - Mild Cleansing Oil Black & Smooth Refill 115ml"
    assert t.classify("-", name, "Fancl") == t.BEAUTE
    assert t.classify_subcategory(t.BEAUTE, name, "-") == "Soins visage"


def test_acne_patch_is_face_care():
    name = "CCCDRLEE - Butterfly Acne Patch - 12pcs"
    assert t.classify("-", name, "CCCDRLEE") == t.BEAUTE
    assert t.classify_subcategory(t.BEAUTE, name, "-") == "Soins visage"


def test_hair_ampoule_is_hair_care():
    name = "Pretty skin - NMN Biotox Spicule Shot Hair Ampoule 15ml"
    assert t.classify("-", name, "Pretty skin") == t.BEAUTE
    assert t.classify_subcategory(t.BEAUTE, name, "-") == "Cheveux"


def test_scalp_therapy_is_hair_care():
    name = "COSNORI - 8 Grow Pro-Vit B5 Scalp Therapy Ampoule 60ml"
    assert t.classify("-", name, "COSNORI") == t.BEAUTE
    assert t.classify_subcategory(t.BEAUTE, name, "-") == "Cheveux"


def test_cuticle_oil_is_nail_care():
    name = "Homei - Cuticle Oil 7ml"
    assert t.classify("-", name, "Homei") == t.BEAUTE
    assert t.classify_subcategory(t.BEAUTE, name, "-") == "Ongles"


def test_generic_treatment_alone_remains_unclassified():
    assert t.classify("-", "Treatment 200ml", None) is None
