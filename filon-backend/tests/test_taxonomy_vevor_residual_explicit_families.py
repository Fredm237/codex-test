from app.services import taxonomy as t


def assert_destination(name: str, category: str, subcategory: str) -> None:
    assert t.classify(None, name, "Vevor", "vevor-fr") == category
    assert t.classify_subcategory(category, name, None) == subcategory


def test_vevor_tow_hitch_is_auto_towing_and_bodywork():
    assert_destination(
        "VEVOR Attelage de Distribution de Poids Remorque 4500 kg Kit de Système d'Attelage",
        t.AUTO,
        "Remorquage & Carrosserie",
    )


def test_vevor_paintless_dent_repair_is_auto_bodywork():
    assert_destination(
        "VEVOR Outils de Débosselage sans Peinture Kit Débosselage Carrosserie",
        t.AUTO,
        "Remorquage & Carrosserie",
    )


def test_vevor_greenhouse_film_is_gardening():
    assert_destination(
        "VEVOR Film à Effet de Serre Film Polyéthylène pour Serre Agriculture",
        t.JARDIN,
        "Jardinage & Apiculture",
    )


def test_vevor_welder_is_workshop_tooling():
    assert_destination(
        "VEVOR Poste à Souder MIG-200 Poste de Soudage Portable",
        t.JARDIN,
        "Outillage",
    )


def test_vevor_tile_cutter_is_workshop_tooling():
    assert_destination(
        "VEVOR Coupe-Carreaux 1200 mm Coupe Carrelage Manuel",
        t.JARDIN,
        "Outillage",
    )


def test_vevor_food_dehydrator_is_small_appliance():
    assert_destination(
        "VEVOR Déshydrateur Alimentaire Électrique 10 Plateaux Inox",
        t.ELECTROMENAGER,
        "Petit électroménager",
    )


def test_vevor_cotton_candy_machine_is_small_appliance():
    assert_destination(
        "VEVOR Machine à Barbe à Papa Professionnelle 1000 W",
        t.ELECTROMENAGER,
        "Petit électroménager",
    )


def test_generic_machine_stays_unclassified():
    assert t.classify(None, "Machine de collection édition limitée", "Vevor", "vevor-fr") is None


def test_truck_word_alone_does_not_classify_as_auto():
    assert t.classify(None, "Support universel pour camion", "Vevor", "vevor-fr") is None
