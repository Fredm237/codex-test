from app.services import taxonomy as t

MERCHANT = "2dekansje NL-BE"


def test_2dekansje_bathroom_furniture_source_is_home():
    source = "Wonen & Koken > Badkamer & sanitair > Badkamermeubels"
    name = "Yaheetech Badkamerkast met 3 Laden"
    assert t.classify(source, name, merchant_name=MERCHANT) == t.MAISON


def test_2dekansje_kitchen_utensils_source_is_home():
    source = "Wonen & Koken > Koken & tafelen > Keukengerei"
    name = "Castagnola Keukenschort - Waterafstotend Kookschort"
    assert t.classify(source, name, merchant_name=MERCHANT) == t.MAISON


def test_2dekansje_trash_bin_source_is_home():
    source = "Wonen & Koken > Schoonmaken & opruimen > Prullenbakken & vuilnisbakken"
    name = "Hailo Inbouwprullenbak - RVS"
    assert t.classify(source, name, merchant_name=MERCHANT) == t.MAISON


def test_2dekansje_home_routes_do_not_apply_to_another_merchant():
    assert t.classify(
        "Wonen & Koken > Badkamer & sanitair > Badkamermeubels",
        "Référence opaque",
        merchant_name="Autre marchand",
    ) is None


def test_2dekansje_unrelated_route_remains_unclassified_when_opaque():
    assert t.classify("Vertaald > Frans", "Référence opaque", merchant_name=MERCHANT) is None
