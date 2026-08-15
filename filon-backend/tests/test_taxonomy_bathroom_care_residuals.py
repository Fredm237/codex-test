from app.services import taxonomy as t


def test_baby_bath_seat_is_baby_toilette():
    name = "Angelcare Badstoel Soft Touch - Roze"
    assert t.classify("Badkamer & verzorging", name, "Angelcare") == t.BEBE
    assert t.classify_subcategory(t.BEBE, name, "Badkamer & verzorging") == "Couches & Toilette"


def test_baby_care_oil_is_baby_toilette():
    name = "HiPP Babysanft Sensitive Babyverzorgingsolie Met Biologische Amandelolie"
    assert t.classify("Badkamer & verzorging", name, "HiPP") == t.BEBE
    assert t.classify_subcategory(t.BEBE, name, "Badkamer & verzorging") == "Couches & Toilette"


def test_bath_sponge_is_bath_and_body():
    name = "Coral Badsponzen - 7 stuks"
    assert t.classify("Badkamer & verzorging", name, "Coral") == t.BEAUTE
    assert t.classify_subcategory(t.BEAUTE, name, "Badkamer & verzorging") == "Bain & Corps"


def test_nail_clipper_is_nails():
    name = "Beter Mini Cure nagelknipper"
    assert t.classify("Badkamer & verzorging", name, "Beter") == t.BEAUTE
    assert t.classify_subcategory(t.BEAUTE, name, "Badkamer & verzorging") == "Ongles"


def test_dutch_toothbrushes_are_oral_hygiene():
    name = "Knuffelvarken Tandenborstels - 2 stuks"
    assert t.classify("Badkamer & verzorging", name, "Gurli Gris") == t.SANTE
    assert t.classify_subcategory(t.SANTE, name, "Badkamer & verzorging") == "Hygiène bucco-dentaire"


def test_unspecified_pampers_wipes_remain_unclassified_without_baby_title_signal():
    assert t.classify("Badkamer & verzorging", "Pampers Sensitive vochtige doekjes", "Pampers") is None
