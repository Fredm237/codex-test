from app.services import taxonomy as t


def test_platform_bed_is_furniture():
    name = "Lit plateforme double en chêne"
    assert t.classify("Meilleures ventes", name, None) == t.MAISON
    assert t.classify_subcategory(t.MAISON, name, "Meilleures ventes") == "Meubles"


def test_storage_drawer_is_furniture():
    name = "Tiroir de rangement empilable - Hauteur 24 cm"
    assert t.classify("Meilleures ventes", name, None) == t.MAISON
    assert t.classify_subcategory(t.MAISON, name, "Meilleures ventes") == "Meubles"


def test_aroma_diffuser_is_decoration():
    name = "Aroma diffuseur grand modèle"
    assert t.classify("Meilleures ventes", name, None) == t.MAISON
    assert t.classify_subcategory(t.MAISON, name, "Meilleures ventes") == "Décoration"


def test_explicit_snack_is_food():
    assert t.classify("Meilleures ventes", "Croustilles de pommes de terre soufflées", None) == t.ALIMENTATION


def test_shower_flower_is_bath_and_body():
    name = "Fleur de douche blanche"
    assert t.classify("Meilleures ventes", name, None) == t.BEAUTE
    assert t.classify_subcategory(t.BEAUTE, name, "Meilleures ventes") == "Bain & Corps"


def test_rice_cooker_is_small_appliance():
    name = "Cuiseur à riz multifonction"
    assert t.classify("Meilleures ventes", name, None) == t.ELECTROMENAGER
    assert t.classify_subcategory(t.ELECTROMENAGER, name, "Meilleures ventes") == "Petit électroménager"


def test_boston_bag_is_handbag():
    name = "Sac Boston pliable et déperlant"
    assert t.classify("Meilleures ventes", name, None) == t.BAGAGERIE
    assert t.classify_subcategory(t.BAGAGERIE, name, "Meilleures ventes") == "Sacs à main"


def test_bare_word_diffuser_is_not_classified_as_aroma_diffuser():
    assert t.classify("Meilleures ventes", "Diffuseur de documents", None) is None
