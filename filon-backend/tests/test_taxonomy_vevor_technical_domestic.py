from app.services import taxonomy as t


def assert_destination(name: str, category: str, subcategory: str) -> None:
    assert t.classify(None, name, "Vevor", "vevor-fr") == category
    assert t.classify_subcategory(category, name, None) == subcategory


def test_vevor_hydraulic_workshop_press_is_tooling():
    assert_destination(
        "VEVOR Presse Hydraulique d'Atelier 12 T avec Vérin Cadre en H",
        t.JARDIN,
        "Outillage",
    )


def test_vevor_electrical_distribution_box_is_tooling():
    assert_destination(
        "VEVOR Boîte de Distribution Électrique Coffret Électrique Étanche Extérieur",
        t.JARDIN,
        "Outillage",
    )


def test_vevor_refrigerant_recharge_kit_is_tooling():
    assert_destination(
        "VEVOR Kit de Recharge de Réfrigérant Manomètre à 4 Voies",
        t.JARDIN,
        "Outillage",
    )


def test_vevor_parcel_box_is_home_storage():
    assert_destination(
        "VEVOR Boîte à Colis Boîte aux Lettres Acier Galvanisé Verrouillable",
        t.MAISON,
        "Rangement & Boîtes aux lettres",
    )


def test_vevor_badge_kit_is_creative_badge_making():
    assert_destination(
        "VEVOR Badge Personnalisé Kits de Consommables pour Fabrication de Badge Rond",
        t.LOISIRS,
        "Création de badges",
    )


def test_generic_badge_stays_unclassified():
    assert t.classify(None, "Badge de collection édition limitée", "Vevor", "vevor-fr") is None


def test_generic_box_stays_unclassified():
    assert t.classify(None, "Boîte de rangement universelle", "Vevor", "vevor-fr") is None
