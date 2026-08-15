from app.services import taxonomy as t


def test_wireless_headset_is_telephony_earphones():
    name = "Wireless Bluetooth headset sports waterproof Bluetooth 5.1 headset stereo headset with microphone"
    assert t.classify("Consumer Electronics", name, "voghion", "voghion-global") == t.TELEPHONIE
    assert t.classify_subcategory(t.TELEPHONIE, name, "Consumer Electronics") == "Écouteurs"


def test_tws_earbuds_are_telephony_earphones():
    name = "TWS Bluetooth-compatible 5.0 Wireless Solid Color Smart Touch Earphones Stereo Earbuds"
    assert t.classify("Consumer Electronics", name, "voghion", "voghion-global") == t.TELEPHONIE
    assert t.classify_subcategory(t.TELEPHONIE, name, "Consumer Electronics") == "Écouteurs"


def test_smartwatch_is_telephony_connected_watch():
    name = "New F8 smartwatch AI voice assistant heart rate oxygen monitoring"
    assert t.classify("Consumer Electronics", name, "voghion", "voghion-global") == t.TELEPHONIE
    assert t.classify_subcategory(t.TELEPHONIE, name, "Consumer Electronics") == "Montres connectées"


def test_english_loudspeaker_is_tv_sound_speaker():
    name = "T&G TG337 New Portable Speaker Wireless Bluetooth 3D Stereo Surround Subwoofer"
    assert t.classify("Consumer Electronics", name, "voghion", "voghion-global") == t.TV_SON
    assert t.classify_subcategory(t.TV_SON, name, "Consumer Electronics") == "Enceintes"


def test_dutch_luidspreker_is_tv_sound_speaker():
    name = "Philips BT55W draadloze Bluetooth-luidspreker"
    assert t.classify("Electronica", name, "Philips", "bazta-be") == t.TV_SON
    assert t.classify_subcategory(t.TV_SON, name, "Electronica") == "Enceintes"


def test_generic_consumer_electronics_source_is_not_enough_on_its_own():
    assert t.classify("Consumer Electronics", "Model ZX-42", "unknown", "merchant") is None
