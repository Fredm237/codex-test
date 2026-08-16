from app.services import taxonomy as t

MERCHANT = "2dekansje NL-BE"


def test_2dekansje_small_kitchen_appliance_requires_explicit_object():
    source = "Wonen & Koken > Koken & tafelen > Kleine keukenapparaten"
    name = "Bestron Poffertjesmaker - 800W"
    assert t.classify(source, name, merchant_name=MERCHANT) == t.ELECTROMENAGER
    assert t.classify_subcategory(t.ELECTROMENAGER, name, source) == "Petit électroménager"


def test_2dekansje_cleaning_appliance_requires_explicit_object():
    source = "Wonen & Koken > Schoonmaken & opruimen > Stofzuigen & schoonmaken"
    name = "Ecovacs Robotstofzuiger met Dweilfunctie"
    assert t.classify(source, name, merchant_name=MERCHANT) == t.ELECTROMENAGER
    assert t.classify_subcategory(t.ELECTROMENAGER, name, source) == "Aspirateurs"


def test_2dekansje_coffee_appliance_requires_explicit_object():
    source = "Wonen & Koken > Koken & tafelen > Thee & koffie"
    name = "KitchenBrothers Elektrische Melkopschuimer - 4-in-1"
    assert t.classify(source, name, merchant_name=MERCHANT) == t.ELECTROMENAGER
    assert t.classify_subcategory(t.ELECTROMENAGER, name, source) == "Petit électroménager"


def test_2dekansje_coffee_tableware_requires_explicit_object():
    source = "Wonen & Koken > Koken & tafelen > Thee & koffie"
    name = "Monzana Glazen Theepot met RVS-Filter"
    assert t.classify(source, name, merchant_name=MERCHANT) == t.MAISON
    assert t.classify_subcategory(t.MAISON, name, source) == "Vaisselle & Cuisine"


def test_2dekansje_massage_health_requires_explicit_object():
    source = "Mooi & Gezond > Massageapparaten"
    name = "Auronic Shiatsu Massagekussen met Warmtefunctie"
    assert t.classify(source, name, merchant_name=MERCHANT) == t.SANTE
    assert t.classify_subcategory(t.SANTE, name, source) == "Massage & Bien-être"


def test_2dekansje_fan_requires_explicit_object():
    source = "Wonen & Koken > Klimaatbeheersing > Ventilatoren"
    name = "Auronic Torenventilator - 76 cm"
    assert t.classify(source, name, merchant_name=MERCHANT) == t.ELECTROMENAGER
    assert t.classify_subcategory(t.ELECTROMENAGER, name, source) == "Climatisation & Chauffage"


def test_2dekansje_blender_accessory_is_not_promoted_by_object_rule():
    assert t.classify(
        "Wonen & Koken > Koken & tafelen > Kleine keukenapparaten",
        "MOA Extra Glazen Kan voor Blender",
        merchant_name=MERCHANT,
    ) is None


def test_2dekansje_fan_source_without_fan_object_remains_unclassified():
    assert t.classify(
        "Wonen & Koken > Klimaatbeheersing > Ventilatoren",
        "Coast Boksbal Met Standaard",
        merchant_name=MERCHANT,
    ) is None


def test_2dekansje_object_route_does_not_apply_to_another_merchant():
    assert t.classify(
        "Wonen & Koken > Koken & tafelen > Kleine keukenapparaten",
        "Bestron Poffertjesmaker - 800W",
        merchant_name="Autre marchand",
    ) is None
