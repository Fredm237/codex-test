from app.services import taxonomy as t


def test_watercolor_painting_brush_is_creative_hobby():
    name = "Cross-border Nylon Wool Board Brush Watercolor Oil Painting Acrylic Painting Brush"
    assert t.classify("Education & Office Supplies", name, "voghion") == t.LOISIRS
    assert t.classify_subcategory(t.LOISIRS, name, "Education & Office Supplies") == "Dessin & Peinture"


def test_art_brush_is_creative_hobby():
    name = "Round front watercolor brush art painting brush"
    assert t.classify("Education & Office Supplies", name, "voghion") == t.LOISIRS
    assert t.classify_subcategory(t.LOISIRS, name, "Education & Office Supplies") == "Dessin & Peinture"


def test_oil_painting_crayon_is_creative_hobby():
    name = "Creative block coloring crayon oil painting stick"
    assert t.classify("Education & Office Supplies", name, "voghion") == t.LOISIRS
    assert t.classify_subcategory(t.LOISIRS, name, "Education & Office Supplies") == "Dessin & Peinture"


def test_generic_office_pen_is_not_forced_into_creative_hobbies():
    assert t.classify("Education & Office Supplies", "Student gel pen blue black", None) is None
