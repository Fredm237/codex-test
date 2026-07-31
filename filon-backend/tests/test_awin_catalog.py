"""Tests des helpers de parsing de l'ingestion Awin (sans réseau ni base)."""

from __future__ import annotations

from app.services import awin_catalog as a


def test_to_float_formats():
    assert a._to_float("1.299,00") == 1299.0   # format FR (point = milliers)
    assert a._to_float("1,299.00") == 1299.0   # format EN (virgule = milliers)
    assert a._to_float("799.90") == 799.9
    assert a._to_float("899") == 899.0
    assert a._to_float("") is None
    assert a._to_float(None) is None


def test_to_bool():
    assert a._to_bool("1") is True
    assert a._to_bool("in stock") is True
    assert a._to_bool("0") is False
    assert a._to_bool("") is None
    assert a._to_bool(None) is None


def test_slugify():
    assert a._slugify("Coolblue BE!") == "coolblue-be"
    assert a._slugify("  ") == "marchand"


def test_programme_to_values():
    p = {
        "id": 12345,
        "name": "MediaMarkt",
        "primaryRegion": {"countryCode": "be", "name": "Belgium"},
        "displayUrl": "https://www.mediamarkt.be/",
        "currencyCode": "EUR",
    }
    v = a._programme_to_values(p)
    assert v["awin_mid"] == 12345
    assert v["slug"] == "mediamarkt"
    assert v["region"] == "BE"
    assert v["domain"] == "mediamarkt.be"
    assert v["joined"] is True

    assert a._programme_to_values({"name": "no id"}) is None


def test_download_url_has_columns_and_key():
    from app.core.config import get_settings

    get_settings.cache_clear()
    url = a._download_url(["111", "222"])
    assert "/fid/111,222/" in url
    assert "aw_deep_link" in url and "search_price" in url
    assert "compression/gzip" in url
