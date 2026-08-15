from app.services import taxonomy as t


MERCHANT = "Bollywolly"


def assert_case(name: str, subcategory: str) -> None:
    assert t.classify(None, name, merchant_name=MERCHANT) == t.MODE_FEMME
    assert t.classify_subcategory(t.MODE_FEMME, name, merchant_name=MERCHANT) == subcategory


def test_dutch_dress_is_womens_dress_in_bollywolly_context():
    assert_case("Alcidia da Veiga • donkerblauwe zijden midi jurk • 36", "Robes")


def test_dutch_skirt_is_womens_skirt_in_bollywolly_context():
    assert_case("Bernice • groene mini rok • 34", "Jupes")


def test_dutch_tunic_is_womens_top_in_bollywolly_context():
    assert_case("Backstage • blauwe linnen tuniek Elise • M", "Hauts & T-shirts")


def test_corset_is_womens_top_in_bollywolly_context():
    assert_case("3x1 • zwart denim corset • L", "Hauts & T-shirts")


def test_model_only_stays_unclassified_even_in_bollywolly_context():
    assert t.classify(None, "7 for all Mankind • Scout blue dasher • 31", merchant_name=MERCHANT) is None


def test_generic_merchant_dutch_dress_is_not_inferred_as_womens_mode():
    assert t.classify(None, "donkerblauwe zijden midi jurk • 36", merchant_name="Generic") is None
