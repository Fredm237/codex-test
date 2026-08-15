from app.services import taxonomy as t

MERCHANT = "2dekansje NL-BE"


def test_2dekansje_christmas_tree_source_is_home_decoration():
    source = "Kerst > Kerstbomen"
    name = "Coast Kunstkerstboom Groen - 180 cm"
    assert t.classify(source, name, merchant_name=MERCHANT) == t.MAISON
    assert t.classify_subcategory(t.MAISON, name, source) == "Décoration"


def test_2dekansje_christmas_lights_source_is_home_lighting():
    source = "Kerst > Kerstverlichting"
    name = "Monzana Regen Lichtketting LED Kerst - Warm wit"
    assert t.classify(source, name, merchant_name=MERCHANT) == t.MAISON
    assert t.classify_subcategory(t.MAISON, name, source) == "Luminaires"


def test_2dekansje_luggage_source_is_baggage():
    source = "Hobby & Sport > Reizen & vrije tijd > Koffers & reistassen"
    name = "Monzana Kofferset - 4 stuks met wielen"
    assert t.classify(source, name, merchant_name=MERCHANT) == t.BAGAGERIE
    assert t.classify_subcategory(t.BAGAGERIE, name, source) == "Valises & Bagages"


def test_2dekansje_pet_source_is_pet_supplies():
    source = "Wonen & Koken > Alles voor huisdieren"
    name = "Yaheetech Krabpaal - Kattenboom met Kattenhuis"
    assert t.classify(source, name, merchant_name=MERCHANT) == t.ANIMALERIE
    assert t.classify_subcategory(t.ANIMALERIE, name, source) == "Chat"


def test_2dekansje_tableware_source_is_kitchenware():
    source = "Wonen & Koken > Koken & tafelen > Tafelen"
    name = "Castagnola Kunstlederen Onderzetters met houder"
    assert t.classify(source, name, merchant_name=MERCHANT) == t.MAISON
    assert t.classify_subcategory(t.MAISON, name, source) == "Vaisselle & Cuisine"


def test_2dekansje_humidifier_source_is_climate_appliance():
    source = "Wonen & Koken > Klimaatbeheersing > Luchtbevochtigers"
    name = "Auronic Luchtbevochtiger - 6L tankcapaciteit"
    assert t.classify(source, name, merchant_name=MERCHANT) == t.ELECTROMENAGER
    assert t.classify_subcategory(t.ELECTROMENAGER, name, source) == "Climatisation & Chauffage"


def test_2dekansje_source_route_does_not_apply_to_another_merchant():
    assert t.classify("Kerst > Kerstbomen", "Référence opaque", merchant_name="Autre marchand") is None


def test_2dekansje_broader_source_remains_unclassified():
    assert t.classify(
        "Wonen & Koken > Koken & tafelen > Kleine keukenapparaten",
        "Référence opaque",
        merchant_name=MERCHANT,
    ) is None
