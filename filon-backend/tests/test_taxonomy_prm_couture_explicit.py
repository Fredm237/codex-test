from app.services import taxonomy as t


def assert_mercerie(name: str, brand: str) -> None:
    assert t.classify(None, name, brand) == t.LOISIRS
    assert t.classify_subcategory(t.LOISIRS, name, None) == "Tissus & Mercerie"


def test_prm_flannel_is_raw_fabric_not_a_garment():
    assert_mercerie("Flanelle de laine – Carreaux vert canard et gris", "Coupons Couture")


def test_prm_twill_viscose_is_raw_fabric_not_a_garment():
    assert_mercerie("Twill 100% viscose – Motif paisley bleu marine", "Coupons Couture")


def test_prm_double_gauze_is_raw_fabric_not_a_garment():
    assert_mercerie("Double gaze 100% coton bio – Vert d’eau", "Coupons Couture")


def test_gutermann_sewing_thread_is_mercerie():
    assert_mercerie("Fil pour tout coudre 100m – Coloris 000", "Gütermann")


def test_bohin_bobbin_is_mercerie():
    assert_mercerie("Canettes universelles en plastique Bohin", "Bohin")


def test_bohin_sewing_tool_is_mercerie():
    assert_mercerie("Pied-de-biche universel pour machine à coudre", "Bohin")


def test_finished_tweed_dress_is_not_absorbed_by_mercerie():
    category = t.classify(None, "Robe en tweed noir", "Coupons Couture")
    assert category != t.LOISIRS


def test_food_crepe_without_couture_brand_is_not_mercerie():
    assert t.classify(None, "Crêpe au sucre et citron", "Restaurant") != t.LOISIRS


def test_generic_plastic_bobbin_without_couture_brand_is_not_mercerie():
    assert t.classify(None, "Canette en plastique pour boisson", "Generic") != t.LOISIRS
