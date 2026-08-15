from app.services import taxonomy as t


def assert_destination(name: str, category: str, subcategory: str | None) -> None:
    assert t.classify(None, name, "Kastner & Öhler", "kastner-hler-fr") == category
    assert t.classify_subcategory(category, name, None) == subcategory


def test_kastner_aftershave_is_face_care():
    assert_destination(
        "DIOR Fahrenheit Lotion Après-Rasage (Flacon) 100ml",
        t.BEAUTE,
        "Soins visage",
    )


def test_kastner_body_butter_is_bath_and_body():
    assert_destination(
        "CLINIQUE Beurre Corporel Deep Comfort 200 ml",
        t.BEAUTE,
        "Bain & Corps",
    )


def test_kastner_body_balm_is_bath_and_body():
    assert_destination(
        "BIOTHERM Oil Therapie - Baume Corps 400ml",
        t.BEAUTE,
        "Bain & Corps",
    )


def test_kastner_blush_is_makeup_not_colour_word():
    assert_destination(
        "CLINIQUE Rouge - Blushing Blush Powder Blush 6mg",
        t.BEAUTE,
        "Maquillage",
    )


def test_kastner_cookware_is_kitchenware():
    assert_destination(
        "WMF Marmite à pâtes avec couvercle 24 cm argent",
        t.MAISON,
        "Vaisselle & Cuisine",
    )


def test_kastner_carafe_is_kitchenware():
    assert_destination(
        "RIEDEL Carafe à décanter Ultra",
        t.MAISON,
        "Vaisselle & Cuisine",
    )


def test_kastner_long_johns_are_mens_underwear():
    assert_destination(
        "HUBER Caleçon long avec ouverture Comfort bleu | M",
        t.MODE_HOMME,
        "Sous-vêtements",
    )


def test_generic_lotion_stays_unclassified():
    assert t.classify(None, "Lotion de collection édition limitée", "Kastner & Öhler", "kastner-hler-fr") is None


def test_balm_without_body_context_stays_unclassified():
    assert t.classify(None, "Baume de collection édition limitée", "Kastner & Öhler", "kastner-hler-fr") is None


def test_matte_sneaker_is_not_makeup():
    assert t.classify(None, "Sneakers Stay Matte édition noire", "Kastner & Öhler", "kastner-hler-fr") == t.CHAUSSURES
