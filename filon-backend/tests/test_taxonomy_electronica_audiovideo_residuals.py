from app.services import taxonomy as t


def test_dutch_aux_audio_cable_is_audio_video_cable():
    name = "Goobay AUX-adapter Audiokabel - 3 m"
    assert t.classify("Electronica", name, "Goobay") == t.TV_SON
    assert t.classify_subcategory(t.TV_SON, name, "Electronica") == "Câbles audio & vidéo"


def test_toslink_audio_cable_is_audio_video_cable():
    name = "Nedis Optische TosLink Mannelijke Audiokabel - 5 meter"
    assert t.classify("Electronica", name, "Nedis") == t.TV_SON
    assert t.classify_subcategory(t.TV_SON, name, "Electronica") == "Câbles audio & vidéo"


def test_hdmi_cable_is_audio_video_cable():
    name = "Goobay HDMI Hoge Snelheidskabel w. Ethernet - 5 meter"
    assert t.classify("Electronica", name, "Goobay") == t.TV_SON
    assert t.classify_subcategory(t.TV_SON, name, "Electronica") == "Câbles audio & vidéo"


def test_universal_remote_is_tv_sound_remote():
    name = "Nedis Voorgeprogrammeerde Universele Afstandsbediening"
    assert t.classify("Electronica", name, "Nedis") == t.TV_SON
    assert t.classify_subcategory(t.TV_SON, name, "Electronica") == "Télécommandes"


def test_generic_technical_cable_is_not_captured_by_audio_video_rule():
    assert t.classify("Informatique", "Câble USB-C de données", None) != t.TV_SON
