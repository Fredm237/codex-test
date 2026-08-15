from app.services import taxonomy as t


def test_dutch_led_light_chain_is_home_luminaire():
    name = "Premier 200 LED meerkleurige lichtketting op batterijen - 20 meter"
    assert t.classify("Kerstmis", name, "Premier") == t.MAISON
    assert t.classify_subcategory(t.MAISON, name, "Kerstmis") == "Luminaires"


def test_dutch_christmas_bauble_is_home_decoration():
    name = "Decoris Seizoen Rode Mini Kerstbal set - 24 stuks"
    assert t.classify("Kerstmis", name, "Decoris") == t.MAISON
    assert t.classify_subcategory(t.MAISON, name, "Kerstmis") == "Décoration"


def test_dutch_snow_globe_is_home_decoration():
    name = "Drie Koningen Muzikale LED Sneeuwbol Notenkraker - 10cm"
    assert t.classify("Kerstmis", name, "Three Kings") == t.MAISON
    assert t.classify_subcategory(t.MAISON, name, "Kerstmis") == "Décoration"


def test_explicit_beauty_advent_calendar_is_beauty_gift_set():
    name = "Technic Vintage Kersenbloesem Luxe Toiletartikelen Adventskalender"
    assert t.classify("Kerstmis", name, "Technic") == t.BEAUTE
    assert t.classify_subcategory(t.BEAUTE, name, "Kerstmis") == "Coffrets & Calendriers"


def test_christmas_word_alone_does_not_force_a_category():
    assert t.classify("Kerstmis", "Vrolijk Kerstmis", None) is None
