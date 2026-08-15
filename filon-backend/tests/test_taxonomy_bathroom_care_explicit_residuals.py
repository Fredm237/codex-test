from app.services import taxonomy as t


def test_dutch_baby_wipes_are_baby_toilet_care():
    name = "Pampers Sensitive babydoekjes - 52 stuks"
    assert t.classify("Badkamer & verzorging", name, "Pampers", "bazta-be") == t.BEBE
    assert t.classify_subcategory(t.BEBE, name, "Badkamer & verzorging") == "Couches & Toilette"


def test_dutch_baby_oil_is_baby_toilet_care():
    name = "Johnson's Babyolie - 200 ml"
    assert t.classify("Badkamer & verzorging", name, "Johnson's", "bazta-be") == t.BEBE
    assert t.classify_subcategory(t.BEBE, name, "Badkamer & verzorging") == "Couches & Toilette"


def test_dutch_bath_toy_is_toy_bath_game():
    name = "Tomy Toomies Schildpad Badspeeltje"
    assert t.classify("Badkamer & verzorging", name, "Tomy Toomies", "bazta-be") == t.JOUETS
    assert t.classify_subcategory(t.JOUETS, name, "Badkamer & verzorging") == "Jeux de bain"


def test_dutch_toothbrush_is_dental_health():
    name = "TePe Mini Extra Zachte Kindertandenborstel 0-3 jaar"
    assert t.classify("Badkamer & verzorging", name, "TePe", "bazta-be") == t.SANTE
    assert t.classify_subcategory(t.SANTE, name, "Badkamer & verzorging") == "Hygiène bucco-dentaire"


def test_dutch_toothbrush_heads_are_dental_health():
    name = "Lov'yc Kids opzetborstels voor elektrische tandenborstel Zacht"
    assert t.classify("Badkamer & verzorging", name, "Lovyc", "bazta-be") == t.SANTE
    assert t.classify_subcategory(t.SANTE, name, "Badkamer & verzorging") == "Hygiène bucco-dentaire"


def test_bath_soap_is_beauty_body_care():
    name = "Cussons Creations Comfort Badzeep – 500ml"
    assert t.classify("Badkamer & verzorging", name, "Cussons", "bazta-be") == t.BEAUTE
    assert t.classify_subcategory(t.BEAUTE, name, "Badkamer & verzorging") == "Bain & Corps"


def test_generic_bathroom_source_is_not_enough_to_force_a_category():
    assert t.classify("Badkamer & verzorging", "Model ZX-42", "unknown", "merchant") is None
