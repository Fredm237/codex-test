from app.services import taxonomy as t


LILOS = "Lilo's Nature"


def test_dutch_dog_leash_is_animalerie_with_dog_subcategory():
    name = "No Fuss Hondenriem Groen"
    assert t.classify(None, name, merchant_name=LILOS) == t.ANIMALERIE
    assert t.classify_subcategory(t.ANIMALERIE, name) == "Chien"


def test_dutch_cat_cave_is_animalerie_with_cat_subcategory():
    name = "Lora kattengrot"
    assert t.classify(None, name, merchant_name=LILOS) == t.ANIMALERIE
    assert t.classify_subcategory(t.ANIMALERIE, name) == "Chat"


def test_lilos_explicit_cat_supplement_uses_bounded_specialist_context():
    assert t.classify(None, "Organimal Propolis – Katten", brand=LILOS, merchant_name=LILOS) == t.ANIMALERIE


def test_animal_word_outside_lilos_context_does_not_become_animalerie_for_a_book():
    assert t.classify(None, "Livre sur katten en ville", brand="Éditeur", merchant_name="Librairie") == t.CULTURE


def test_missing_value_stays_unclassified():
    assert t.classify(None, "nan", brand=LILOS, merchant_name=LILOS) is None
