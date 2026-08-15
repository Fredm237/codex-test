from app.services import taxonomy as t


def test_home_video_projector_is_tv_sound_video_projector():
    name = "Ultimea Apollo P50 Projecteur Netflix 1080P 700 ANSI Dolby Audio WiFi"
    assert t.classify("Électronique grand public", name, None, "geekbuying-fr") == t.TV_SON
    assert t.classify_subcategory(t.TV_SON, name, "Électronique grand public") == "Vidéoprojecteurs"


def test_lcd_projector_with_video_signal_is_tv_sound_video_projector():
    name = "Ultimea Apollo P40 Projecteur LCD natif 1080P 700LM"
    assert t.classify("Électronique grand public", name, None, "geekbuying-fr") == t.TV_SON
    assert t.classify_subcategory(t.TV_SON, name, "Électronique grand public") == "Vidéoprojecteurs"


def test_laser_level_is_diy_tool():
    name = "CIGMAN CM701 Niveau Laser 3x360° Autonivelant Croix Verte 30m"
    assert t.classify("Électronique grand public", name, None, "geekbuying-fr") == t.JARDIN
    assert t.classify_subcategory(t.JARDIN, name, "Électronique grand public") == "Outillage"


def test_bare_projector_word_is_not_enough_for_tv_sound():
    assert t.classify("Électronique grand public", "Projecteur de chantier modèle X", None, "merchant") is None


def test_bare_laser_word_is_not_enough_for_diy_tool():
    assert t.classify("Électronique grand public", "Laser modèle X", None, "merchant") is None
