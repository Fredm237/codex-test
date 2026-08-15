from app.services import taxonomy as t


def test_english_video_projector_is_classified():
    name = "Thundeal HY300 Android Wifi Smart Portable Projector 1280 720P Full HD Home Theater"
    assert t.classify("Consumer Electronics", name, "voghion") == t.TV_SON
    assert t.classify_subcategory(t.TV_SON, name, "Consumer Electronics") == "Vidéoprojecteurs"


def test_micro_sd_memory_card_is_storage():
    name = "Real Memory 128 GB TF Flash Memory Card Class 10 Micro SD Card Adapter"
    assert t.classify("Consumer Electronics", name, "voghion") == t.INFORMATIQUE
    assert t.classify_subcategory(t.INFORMATIQUE, name, "Consumer Electronics") == "Stockage"


def test_airbuds_with_spaced_earphones_are_earphones():
    name = "Mini Airdots TWS wireless Bluetooth stereo ear phones with noise cancellation"
    assert t.classify("Consumer Electronics", name, "voghion") == t.TELEPHONIE
    assert t.classify_subcategory(t.TELEPHONIE, name, "Consumer Electronics") == "Écouteurs"


def test_selfie_stick_tripod_is_photo():
    assert t.classify("Consumer Electronics", "A selfie stick with phone tripod and fill lights", "voghion") == t.PHOTO


def test_humidifier_is_climate_appliance():
    name = "Air Humidifier 2L Large Capacity with LCD Humidity Display"
    assert t.classify("Consumer Electronics", name, "voghion") == t.ELECTROMENAGER
    assert t.classify_subcategory(t.ELECTROMENAGER, name, "Consumer Electronics") == "Climatisation & Chauffage"


def test_milk_frother_is_small_appliance():
    name = "Milk frother, coffee frother, household electric milk mixer"
    assert t.classify("Consumer Electronics", name, "voghion") == t.ELECTROMENAGER
    assert t.classify_subcategory(t.ELECTROMENAGER, name, "Consumer Electronics") == "Petit électroménager"


def test_cabinet_light_is_luminaire():
    name = "LED Under Cabinet Light Night Light Wireless Remote Control Dimmable Wardrobe Lamp"
    assert t.classify("Consumer Electronics", name, "voghion") == t.MAISON
    assert t.classify_subcategory(t.MAISON, name, "Consumer Electronics") == "Luminaires"


def test_construction_projector_without_video_context_is_not_video_projector():
    assert t.classify("Consumer Electronics", "Laser projector for construction site", None) != t.TV_SON
