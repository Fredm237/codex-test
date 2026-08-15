from app.services import taxonomy as t


def assert_destination(name: str, category: str, subcategory: str) -> None:
    assert t.classify(None, name, "Vevor") == category
    assert t.classify_subcategory(category, name, None) == subcategory


def test_vevor_e_track_with_trailer_context_is_auto_tiedown():
    assert_destination(
        "VEVOR E-Track Kit d'Arrimage avec Rails pour Camions Remorques",
        t.AUTO,
        "Arrimage & Hydraulique",
    )


def test_vevor_diesel_heater_with_vehicle_context_is_auto():
    assert_destination(
        "VEVOR Chauffage Diesel 12 V Réchauffeur d'Air pour Camion Bateau",
        t.AUTO,
        "Chauffage véhicule",
    )


def test_vevor_hydraulic_pump_with_dumper_context_is_auto():
    assert_destination(
        "VEVOR Pompe Hydraulique DC 12 V pour Camion à Benne Basculante Remorque",
        t.AUTO,
        "Arrimage & Hydraulique",
    )


def test_vevor_mulch_fabric_is_gardening():
    assert_destination(
        "VEVOR Toile de Paillage Anti-Mauvaises Herbes pour Aménagement Paysager",
        t.JARDIN,
        "Jardinage & Apiculture",
    )


def test_vevor_drywall_stilts_are_tooling():
    assert_destination(
        "VEVOR Échasses Plaquiste pour Cloison Sèche Travaux Peinture",
        t.JARDIN,
        "Outillage",
    )


def test_vevor_key_cabinet_is_home_security():
    assert_destination(
        "VEVOR Armoire à Clés Murale Rangement Sécurisé des Clefs",
        t.MAISON,
        "Sécurité & Quincaillerie",
    )


def test_vevor_door_awning_is_home_exterior_fitting():
    assert_destination(
        "VEVOR Auvent de Porte Extérieure Protection Contre la Pluie",
        t.MAISON,
        "Auvents & Rampes",
    )


def test_vevor_pyrography_is_creative_wood_work():
    assert_destination(
        "VEVOR Kit de Pyrogravure sur Bois Pyrograveur Professionnel",
        t.LOISIRS,
        "Pyrogravure & Travail du bois",
    )


def test_diesel_heater_without_vehicle_context_stays_unclassified():
    assert t.classify(None, "Chauffage diesel de démonstration", "Vevor") is None


def test_hydraulic_pump_without_vehicle_context_stays_unclassified():
    assert t.classify(None, "Pompe hydraulique industrielle", "Vevor") is None


def test_generic_safe_word_does_not_classify():
    assert t.classify(None, "Dépôt sûr et robuste", "Vevor") is None
