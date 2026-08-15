from app.services import taxonomy as t


MERCHANT = "Bungalow.net"


def assert_booking(source: str, name: str) -> None:
    assert t.classify_offer_kind(source, name, merchant_name=MERCHANT) == t.ACCOMMODATION
    assert t.classify(source, name, merchant_name=MERCHANT) == t.VOYAGES


def test_chalet_category_is_booking_only_for_bungalow_net():
    assert_booking("Chalets", "Chalet Le Pleynet 14p")


def test_dutch_housing_category_is_booking_only_for_bungalow_net():
    assert_booking("Woningen", "Holidayhome - Margaritenweg 17-R | Niedersfeld")


def test_mobile_home_category_is_booking_only_for_bungalow_net():
    assert_booking("Stacaravans", "Mobil home La Masia Confort 6p A/C")


def test_group_accommodation_is_booking_only_for_bungalow_net():
    assert_booking("Groepsaccommodaties", "Group Villa for 24 people")


def test_physical_chalet_outside_booking_merchant_is_not_accommodation():
    assert t.classify_offer_kind("Maison", "Lampe chalet en bois", merchant_name="Maison déco") == t.PHYSICAL_PRODUCT
    assert t.classify("Maison", "Lampe chalet en bois", merchant_name="Maison déco") != t.VOYAGES
