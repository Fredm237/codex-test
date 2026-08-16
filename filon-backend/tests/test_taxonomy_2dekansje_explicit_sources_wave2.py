from app.services import taxonomy as t

MERCHANT = "2dekansje NL-BE"


def test_2dekansje_christmas_decor_source_is_home_decoration():
    source = "Kerst > Kerstdecoratie"
    name = "Coast Verlichte Berkenboom Kerstdecoratie - 150 cm"
    assert t.classify(source, name, merchant_name=MERCHANT) == t.MAISON
    assert t.classify_subcategory(t.MAISON, name, source) == "Décoration"


def test_2dekansje_pots_and_pans_source_is_kitchenware():
    source = "Wonen & Koken > Koken & tafelen > Potten & pannen"
    name = "Smeg Gietijzeren Grillpan - 26 cm"
    assert t.classify(source, name, merchant_name=MERCHANT) == t.MAISON
    assert t.classify_subcategory(t.MAISON, name, source) == "Vaisselle & Cuisine"


def test_2dekansje_electric_blankets_source_is_climate_appliance():
    source = "Wonen & Koken > Klimaatbeheersing > Elektrische dekens"
    name = "Auronic Elektrische Warmtedeken - 2 Persoons"
    assert t.classify(source, name, merchant_name=MERCHANT) == t.ELECTROMENAGER
    assert t.classify_subcategory(t.ELECTROMENAGER, name, source) == "Climatisation & Chauffage"


def test_2dekansje_fondue_and_fryer_source_is_small_appliance():
    source = "Wonen & Koken > Koken & tafelen > Fonduesets & friteuses"
    name = "KitchenBrothers Airfryer XXL - 7,2L"
    assert t.classify(source, name, merchant_name=MERCHANT) == t.ELECTROMENAGER
    assert t.classify_subcategory(t.ELECTROMENAGER, name, source) == "Petit électroménager"


def test_2dekansje_glassware_source_is_kitchenware():
    source = "Wonen & Koken > Koken & tafelen > Glazen & bekers"
    name = "Gimex Royal Line Champagneglas - 250 ml"
    assert t.classify(source, name, merchant_name=MERCHANT) == t.MAISON
    assert t.classify_subcategory(t.MAISON, name, source) == "Vaisselle & Cuisine"


def test_2dekansje_plates_source_is_kitchenware():
    source = "Wonen & Koken > Koken & tafelen > Borden"
    name = "Villeroy & Boch Ontbijtbord 23 cm"
    assert t.classify(source, name, merchant_name=MERCHANT) == t.MAISON
    assert t.classify_subcategory(t.MAISON, name, source) == "Vaisselle & Cuisine"


def test_2dekansje_aircooler_source_is_climate_appliance():
    source = "Wonen & Koken > Klimaatbeheersing > Aircoolers & luchtkoelers"
    name = "Princess Smart Aircooler - 3L Waterreservoir"
    assert t.classify(source, name, merchant_name=MERCHANT) == t.ELECTROMENAGER
    assert t.classify_subcategory(t.ELECTROMENAGER, name, source) == "Climatisation & Chauffage"


def test_2dekansje_kettle_source_is_small_appliance():
    source = "Wonen & Koken > Koken & tafelen > Waterkokers"
    name = "MOA Waterkoker Retro - 1,8L"
    assert t.classify(source, name, merchant_name=MERCHANT) == t.ELECTROMENAGER
    assert t.classify_subcategory(t.ELECTROMENAGER, name, source) == "Petit électroménager"


def test_2dekansje_wave2_routes_do_not_apply_to_another_merchant():
    assert t.classify("Kerst > Kerstdecoratie", "Référence opaque", merchant_name="Autre marchand") is None


def test_2dekansje_heterogeneous_fan_source_remains_unclassified_when_opaque():
    assert t.classify(
        "Wonen & Koken > Klimaatbeheersing > Ventilatoren",
        "Référence opaque",
        merchant_name=MERCHANT,
    ) is None
