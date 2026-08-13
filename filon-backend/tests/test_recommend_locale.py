"""Locale des annotations produites par l'assistant catalogue."""

from app.services.recommend import _response_locale


def test_supported_locales_are_preserved():
    assert _response_locale("fr") == "fr"
    assert _response_locale("nl") == "nl"
    assert _response_locale("en") == "en"


def test_locale_regions_are_normalised_for_the_stream_contract():
    assert _response_locale("fr-BE") == "fr"
    assert _response_locale("nl-BE") == "nl"
    assert _response_locale("en-GB") == "en"


def test_unknown_or_missing_locale_falls_back_to_french():
    assert _response_locale(None) == "fr"
    assert _response_locale("de") == "fr"
    assert _response_locale("") == "fr"
