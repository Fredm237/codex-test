from app.services import taxonomy as t


def test_3d_scanner_has_dedicated_computing_subcategory():
    name = "3DMakerpro Lynx Scanner 3D Édition premium"
    assert t.classify("Électronique grand public", name, None) == t.INFORMATIQUE
    assert t.classify_subcategory(t.INFORMATIQUE, name, "Électronique grand public") == "Impression 3D & Scan"


def test_3d_printing_filament_has_dedicated_computing_subcategory():
    name = "ERYONE Filament TPU Haute Vitesse 1kg Rouge Transparent"
    assert t.classify("Électronique grand public", name, None) == t.INFORMATIQUE
    assert t.classify_subcategory(t.INFORMATIQUE, name, "Électronique grand public") == "Impression 3D & Scan"


def test_laser_engraver_is_creative_fabrication():
    name = "LONGER RAY5 Graveur laser 10W"
    assert t.classify("Électronique grand public", name, None) == t.LOISIRS
    assert t.classify_subcategory(t.LOISIRS, name, "Électronique grand public") == "Gravure & Sublimation"


def test_sublimation_press_is_creative_fabrication():
    name = "SHUOHAO Presse à chaud 8 en 1 pour tasses et t-shirts"
    assert t.classify("Électronique grand public", name, None) == t.LOISIRS
    assert t.classify_subcategory(t.LOISIRS, name, "Électronique grand public") == "Gravure & Sublimation"


def test_laser_rangefinder_is_not_misclassified_as_laser_engraving():
    assert t.classify("Électronique grand public", "CIGMAN Télémètre Laser Double Face", None) is None
