from app.services import taxonomy as t


def test_explicit_mini_shoulder_bag_is_handbag():
    name = "Mini sac bandoulière en cuir brillant rouge acide"
    assert t.classify("6551", name, "BIMBA Y LOLA") == t.BAGAGERIE
    assert t.classify_subcategory(t.BAGAGERIE, name, "6551") == "Sacs à main"


def test_explicit_shopping_bag_is_handbag():
    name = "Grand sac shopping en cuir tressé noir"
    assert t.classify("6551", name, "BIMBA Y LOLA") == t.BAGAGERIE
    assert t.classify_subcategory(t.BAGAGERIE, name, "6551") == "Sacs à main"


def test_french_curly_apostrophe_earrings_are_jewelry():
    name = "Boucles d’oreilles anneau format mini, cristaux cœur argenté"
    assert t.classify("166", name, "BIMBA Y LOLA") == t.BIJOUX
    assert t.classify_subcategory(t.BIJOUX, name, "166") == "Boucles d'oreilles"


def test_foulard_is_accessory():
    name = "Foulard fleurs dessin pastel bleu"
    assert t.classify("166", name, "BIMBA Y LOLA") == t.ACCESSOIRES
    assert t.classify_subcategory(t.ACCESSOIRES, name, "166") == "Écharpes & Foulards"


def test_sleeping_bag_is_not_handbag_from_mini_bag_rule():
    assert t.classify("6551", "Mini sac de couchage randonnée", None) != t.BAGAGERIE
