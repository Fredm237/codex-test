from app.services import taxonomy as t


def test_womens_gilet_from_nouveautes_is_mode_femme():
    name = "Gilet en mélange de lyocell côtelé pour femme"
    assert t.classify("Nouveautés", name, None, "muji-france") == t.MODE_FEMME
    assert t.classify_subcategory(t.MODE_FEMME, name, "Nouveautés") == "Pulls & Sweats"


def test_womens_cardigan_from_nouveautes_is_mode_femme():
    name = "Cardigan à col ras du cou et maille ajourée en mélange de Lyocell pour femme"
    assert t.classify("Nouveautés", name, None, "muji-france") == t.MODE_FEMME
    assert t.classify_subcategory(t.MODE_FEMME, name, "Nouveautés") == "Pulls & Sweats"


def test_womens_chemiser_from_nouveautes_is_mode_femme():
    name = "Chemisier semi-transparent à mancherons en coton biologique à haute torsion pour femme"
    assert t.classify("Nouveautés", name, None, "muji-france") == t.MODE_FEMME
    assert t.classify_subcategory(t.MODE_FEMME, name, "Nouveautés") == "Hauts & T-shirts"


def test_mens_gilet_remains_mode_homme():
    name = "Gilet en laine pour homme"
    assert t.classify("Nouveautés", name, None, "muji-france") == t.MODE_HOMME
    assert t.classify_subcategory(t.MODE_HOMME, name, "Nouveautés") == "Pulls & Sweats"


def test_generic_nouveautes_source_remains_unclassified():
    assert t.classify("Nouveautés", "Model ZX-42", None, "muji-france") is None
