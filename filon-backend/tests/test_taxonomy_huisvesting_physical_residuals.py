from app.services import taxonomy as t


def test_dutch_toaster_is_small_appliance_not_housing():
    name = "Tristar BR1013 Broodrooster incl. standaard"
    assert t.classify("Huisvesting", name, "Tristar") == t.ELECTROMENAGER
    assert t.classify_subcategory(t.ELECTROMENAGER, name, "Huisvesting") == "Petit électroménager"
    assert t.classify_offer_kind("Huisvesting", name, "Tristar", "bazta-be") == t.PHYSICAL_PRODUCT


def test_dutch_scented_candle_is_home_decoration_not_housing():
    name = "Jelly Belly Bosbessen geurkaars"
    assert t.classify("Huisvesting", name, "Jelly Belly") == t.MAISON
    assert t.classify_subcategory(t.MAISON, name, "Huisvesting") == "Décoration"


def test_dutch_tealight_is_home_decoration():
    name = "Dag LED theelichtjes - 5 stuks"
    assert t.classify("Huisvesting", name, "Day") == t.MAISON
    assert t.classify_subcategory(t.MAISON, name, "Huisvesting") == "Décoration"


def test_kitchen_utensil_is_home_kitchen():
    name = "Masterpro kurkentrekker - Roestvrij staal"
    assert t.classify("Huisvesting", name, "Masterpro") == t.MAISON
    assert t.classify_subcategory(t.MAISON, name, "Huisvesting") == "Vaisselle & Cuisine"


def test_portable_hand_sewing_machine_is_creative_hobby():
    name = "Kiwi draagbare handnaaimachine"
    assert t.classify("Huisvesting", name, "Kiwi") == t.LOISIRS
    assert t.classify_subcategory(t.LOISIRS, name, "Huisvesting") == "Tissus & Mercerie"


def test_huisvesting_label_alone_never_means_accommodation():
    assert t.classify_offer_kind("Huisvesting", "Tristar BR1013 Broodrooster", "Tristar", "bazta-be") == t.PHYSICAL_PRODUCT
