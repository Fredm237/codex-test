"""Tests des helpers de parsing de l'ingestion Awin (sans réseau ni base)."""

from __future__ import annotations

import gzip
from types import SimpleNamespace

import pytest

from app.services import awin_catalog as a


def _stream_settings(*, compressed: int, decompressed: int):
    return SimpleNamespace(
        awin_feed_base="https://feeds.example",
        awin_feed_api_key="private-feed-key",
        awin_max_download_bytes=compressed,
        awin_max_decompressed_bytes=decompressed,
    )


def _install_stream(monkeypatch, chunks: list[bytes]) -> None:
    class _Response:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args) -> None:
            return None

        def raise_for_status(self) -> None:
            return None

        async def aiter_bytes(self):
            for chunk in chunks:
                yield chunk

    class _Client:
        def __init__(self, **_kwargs) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args) -> None:
            return None

        def stream(self, _method: str, _url: str, *, headers: dict[str, str]):
            assert set(headers) <= {"traceparent", "x-request-id"}
            return _Response()

    monkeypatch.setattr(a.httpx, "AsyncClient", _Client)


def test_to_float_formats():
    assert a._to_float("1.299,00") == 1299.0   # format FR (point = milliers)
    assert a._to_float("1,299.00") == 1299.0   # format EN (virgule = milliers)
    assert a._to_float("799.90") == 799.9
    assert a._to_float("899") == 899.0
    assert a._to_float("") is None
    assert a._to_float(None) is None


def test_to_float_thousands_without_decimals():
    """Non-régression : « 1.299 » vaut 1299, pas 1,30.

    Lus comme des décimales, ces prix rangeaient des produits à 1 299 € parmi
    les articles à moins de 100 € et faussaient tout l'historique.
    """
    assert a._to_float("1.299") == 1299.0
    assert a._to_float("1,299") == 1299.0
    assert a._to_float("19.990") == 19990.0
    assert a._to_float("2.500") == 2500.0
    assert a._to_float("1.234.567") == 1234567.0


def test_to_float_keeps_real_decimals():
    assert a._to_float("24,99") == 24.99
    assert a._to_float("12,5") == 12.5
    assert a._to_float("0,50") == 0.5
    assert a._to_float("0.500") == 0.5   # « 0.xxx » reste un décimal
    assert a._to_float("-12,50") == -12.5


def test_to_float_strips_currency_noise():
    assert a._to_float("EUR 49.95") == 49.95
    assert a._to_float("49,95 €") == 49.95
    assert a._to_float("abc") is None


def test_to_bool():
    assert a._to_bool("1") is True
    assert a._to_bool("in stock") is True
    assert a._to_bool("0") is False
    assert a._to_bool("out of stock") is False
    assert a._to_bool("perhaps") is None
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


@pytest.mark.asyncio
async def test_download_feed_stream_gzip_respecte_le_plafond_dur_de_lignes(
    monkeypatch,
):
    payload = gzip.compress(
        b"aw_product_id,product_name\n1,One\n2,Two\n3,Three\n"
    )
    _install_stream(monkeypatch, [payload[:7], payload[7:]])
    monkeypatch.setattr(
        a,
        "get_settings",
        lambda: _stream_settings(compressed=1024, decompressed=1024),
    )
    monkeypatch.setattr(a, "_HARD_MAX_ROWS_PER_FEED", 2)

    rows = await a._download_feed_rows(["feed-1"], max_rows=0)

    assert [row["aw_product_id"] for row in rows] == ["1", "2"]


@pytest.mark.asyncio
async def test_download_feed_accepte_csv_non_compresse(monkeypatch):
    _install_stream(
        monkeypatch,
        [b"aw_product_id,product_name\n1,One\n", b"2,Two\n"],
    )
    monkeypatch.setattr(
        a,
        "get_settings",
        lambda: _stream_settings(compressed=1024, decompressed=1024),
    )

    rows = await a._download_feed_rows(["feed-1"], max_rows=1)

    assert rows == [{"aw_product_id": "1", "product_name": "One"}]


@pytest.mark.asyncio
async def test_download_feed_refuse_corps_compresse_trop_grand(monkeypatch):
    _install_stream(monkeypatch, [b"1234", b"56"])
    monkeypatch.setattr(
        a,
        "get_settings",
        lambda: _stream_settings(compressed=5, decompressed=1024),
    )

    with pytest.raises(a.AwinFeedCompressedLimitError):
        await a._download_feed_rows(["feed-1"])


@pytest.mark.asyncio
async def test_download_feed_refuse_bombe_gzip(monkeypatch):
    payload = gzip.compress(
        b"aw_product_id,product_name\n1," + (b"A" * 512) + b"\n"
    )
    _install_stream(monkeypatch, [payload])
    monkeypatch.setattr(
        a,
        "get_settings",
        lambda: _stream_settings(compressed=1024, decompressed=64),
    )

    with pytest.raises(a.AwinFeedDecompressedLimitError):
        await a._download_feed_rows(["feed-1"])


def test_snapshot_cache_keeps_one_identical_observation_per_cycle():
    cache: set[tuple[int, str, float, str | None, bool | None]] = set()

    assert a._should_record_snapshot(cache, 42, "same-product", 29.99, "EUR", True) is True
    assert a._should_record_snapshot(cache, 42, "same-product", 29.99, "EUR", True) is False
    assert len(cache) == 1


def test_snapshot_cache_keeps_real_price_or_stock_changes():
    cache: set[tuple[int, str, float, str | None, bool | None]] = set()

    assert a._should_record_snapshot(cache, 42, "same-product", 29.99, "EUR", True) is True
    assert a._should_record_snapshot(cache, 42, "same-product", 27.99, "EUR", True) is True
    assert a._should_record_snapshot(cache, 42, "same-product", 27.99, "GBP", True) is True
    assert a._should_record_snapshot(cache, 42, "same-product", 27.99, "GBP", False) is True
    assert a._should_record_snapshot(cache, 43, "same-product", 27.99, "GBP", False) is True
    assert len(cache) == 5


def test_snapshot_without_cycle_cache_still_records_normally():
    assert a._should_record_snapshot(None, 42, "product", 29.99, "EUR", True) is True
    assert a._should_record_snapshot(None, 42, "product", 29.99, "EUR", True) is True
