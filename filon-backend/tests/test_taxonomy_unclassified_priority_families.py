from app.services import taxonomy as t


def test_technical_rj45_cable_is_computing():
    assert t.classify(
        "Câble Réseau",
        "Câble/Cordon réseau RJ45 Catégorie 6 FTP Droit 25m",
    ) == t.INFORMATIQUE


def test_thunderbolt_cable_is_computing_when_protocol_precedes_cable():
    assert t.classify(
        "Câbles",
        "Thunderbolt 3 Cable - Câble de charge pour Apple MacBooks",
    ) == t.INFORMATIQUE


def test_generic_phone_charging_cable_is_not_captured_as_computing():
    assert t.classify(
        "Accessoires téléphone",
        "Câble de charge USB-C compatible iPhone",
    ) == t.TELEPHONIE


def test_child_bottines_are_shoes():
    assert t.classify(
        "Lifestyle > Bottines > Junior > Mixte",
        "Bottines enfant Kickers kick col",
    ) == t.CHAUSSURES


def test_womens_bottines_are_shoes():
    assert t.classify(
        "Lifestyle > Bottines > Adulte > Femme",
        "Bottines en cuir femme Blackstone - Fur",
    ) == t.CHAUSSURES


def test_cabinet_tree_is_home_furniture():
    assert t.classify(
        "Furniture > Cabinets & Storage > Storage Cabinets & Lockers",
        "Lockerkast Lyon - 10 vakken",
    ) == t.MAISON


def test_filing_cabinet_tree_is_home_furniture():
    assert t.classify(
        "Furniture > Cabinets & Storage > Filing Cabinets",
        "Bisley hangmappenkast Basic 4 laden",
    ) == t.MAISON


def test_generic_office_tree_is_not_assumed_to_be_home_furniture():
    assert t.classify(
        "Furniture > Office Furniture",
        "Pulsate",
    ) is None
