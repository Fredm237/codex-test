from app.services import taxonomy as t


def assert_case(name: str) -> None:
    assert t.classify(None, name, "Techsuit") == t.TELEPHONIE
    assert t.classify_subcategory(t.TELEPHONIE, name, None) == "Coques & Protections"


def test_phone_case_for_xiaomi_is_telephony_protection():
    assert_case("Étui pour Xiaomi Redmi Note 15 Pro 5G, Techsuit, eFold, Rouge")


def test_magsafe_case_for_pixel_is_telephony_protection():
    assert_case("Étui MagSafe pour Google Pixel 10a, Techsuit, HaloFrost II, Noir")


def test_tablet_case_is_telephony_protection_not_smartphone():
    assert_case("Étui pour Apple iPad Pro 11 (2024), Spigen, Liquid Air Folio, Noir")


def test_glasses_case_is_not_assumed_to_be_telephony():
    assert t.classify(None, "Étui pour lunettes de soleil en cuir", "Generic") != t.TELEPHONIE


def test_instrument_case_is_not_assumed_to_be_telephony():
    assert t.classify(None, "Étui pour guitare acoustique", "Generic") != t.TELEPHONIE
