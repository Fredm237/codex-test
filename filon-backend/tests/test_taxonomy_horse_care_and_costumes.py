from app.services import taxonomy as t


def test_horse_coat_conditioner_is_animal_care_not_womenswear():
    assert t.classify(
        "Animal Cheval > Nettoyant robe cheval > Adulte > Mixte",
        "Crème conditionneur coat shine HORKA",
        "HORKA",
        "Sport Is Good FR",
    ) == t.ANIMALERIE


def test_human_conditioner_without_equine_source_remains_beauty():
    assert t.classify(
        "Haircare",
        "Conditionneur hydratant pour cheveux",
    ) == t.BEAUTE


def test_halloween_dress_is_exposed_in_costumes_not_dresses():
    assert t.classify_subcategory(
        t.MODE_FEMME,
        "TecTake Halloween Danseres Kostuum Dames - Jurk avec Skeletprint",
    ) == "Déguisements & Costumes"


def test_ordinary_dress_remains_in_dresses():
    assert t.classify_subcategory(
        t.MODE_FEMME,
        "Robe femme Deeluxe Sacha",
    ) == "Robes"


def test_carnival_costume_is_exposed_in_costumes_not_dresses():
    assert t.classify_subcategory(
        t.MODE_FEMME,
        "Vrouwenkostuum Sexy Zombie Halloween Carnaval Verkleedkleding",
    ) == "Déguisements & Costumes"
