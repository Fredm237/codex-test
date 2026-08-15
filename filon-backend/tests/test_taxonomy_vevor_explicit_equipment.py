from app.services import taxonomy as t


def assert_destination(name: str, category: str, subcategory: str | None) -> None:
    assert t.classify(None, name, "Vevor", "vevor-fr") == category
    assert t.classify_subcategory(category, name, None) == subcategory


def test_vevor_demolition_hammer_is_tooling():
    assert_destination(
        "VEVOR Marteau de Démolition 2200 W Marteau-Piqueur avec Burins",
        t.JARDIN,
        "Outillage",
    )


def test_vevor_submersible_well_pump_has_precise_destination():
    assert_destination(
        "VEVOR Pompe Immergée pour Puits 6600 L/h Pompe à Eau pour Puits Profond",
        t.JARDIN,
        "Pompes & Arrosage",
    )


def test_vevor_meat_grinder_is_small_appliance():
    assert_destination(
        "VEVOR Hachoir à Viande 575 W Hachoir Électrique Multifonctionnel",
        t.ELECTROMENAGER,
        "Petit électroménager",
    )


def test_vevor_hydraulic_jack_is_auto_lifting_tool():
    assert_destination(
        "VEVOR Cric Hydraulique Rouleur Capacité de 2,5 T Cric de Plancher",
        t.AUTO,
        "Outils & Levage",
    )


def test_vevor_pottery_wheel_is_creative_ceramics():
    assert_destination(
        "VEVOR Tour de Potier 28 cm Roue de Poterie Électrique pour Argile",
        t.LOISIRS,
        "Poterie & Céramique",
    )


def test_vevor_honey_extractor_is_gardening_and_beekeeping():
    assert_destination(
        "VEVOR Extracteur de Miel Manuel Centrifugeuse pour Apiculture",
        t.JARDIN,
        "Jardinage & Apiculture",
    )


def test_a_generic_pump_stays_unclassified():
    assert t.classify(None, "Pompe universelle de rechange", "Vevor", "vevor-fr") is None


def test_generic_laser_measurement_is_not_creative_engraving():
    assert t.classify(None, "Niveau laser professionnel", "Vevor", "vevor-fr") == t.JARDIN
    assert t.classify_subcategory(t.JARDIN, "Niveau laser professionnel", None) == "Outillage"
