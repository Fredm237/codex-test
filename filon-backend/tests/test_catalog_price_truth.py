"""Contrat commun des agrégats prix/devise/stock du catalogue."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine, literal, select

from app.services.catalog_price_truth import (
    PRICE_TRUTH_CACHE_VERSION,
    comparable_price_evidence_sql,
    same_supported_currency_sql,
    utc_naive_now,
)


@pytest.fixture(scope="module")
def connection():
    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        yield conn
    engine.dispose()


def _same_currency(connection, left, right) -> bool:
    value = connection.scalar(
        select(same_supported_currency_sql(literal(left), literal(right)))
    )
    return value is True


def _comparable(connection, snapshot_currency, offer_currency, snapshot_stock, offer_stock) -> bool:
    value = connection.scalar(
        select(
            comparable_price_evidence_sql(
                snapshot_currency=literal(snapshot_currency),
                offer_currency=literal(offer_currency),
                snapshot_in_stock=literal(snapshot_stock),
                offer_in_stock=literal(offer_stock),
            )
        )
    )
    return value is True


def test_devise_identique_est_normalisee_sans_invention(connection):
    assert _same_currency(connection, " eur ", "EUR")


@pytest.mark.parametrize(
    ("left", "right"),
    [
        (None, "EUR"),
        ("EUR", None),
        ("", "EUR"),
        ("XXX", "XXX"),
        ("EUR", "GBP"),
    ],
)
def test_devise_absente_invalide_ou_differente_echoue_ferme(connection, left, right):
    assert not _same_currency(connection, left, right)


@pytest.mark.parametrize(
    ("snapshot_stock", "offer_stock"),
    [(None, True), (False, True), (True, None), (True, False)],
)
def test_stock_doit_etre_confirme_des_deux_cotes(connection, snapshot_stock, offer_stock):
    assert not _comparable(connection, "EUR", "EUR", snapshot_stock, offer_stock)


def test_preuve_prix_complete_est_comparable(connection):
    assert _comparable(connection, " eur ", "EUR", True, True)


def test_seuil_utc_reste_naif_pour_les_colonnes_sql():
    before = datetime.now(UTC).replace(tzinfo=None)
    current = utc_naive_now()
    after = datetime.now(UTC).replace(tzinfo=None)
    assert current.tzinfo is None
    assert before <= current <= after


def test_version_de_cache_est_explicite():
    assert PRICE_TRUTH_CACHE_VERSION == "catalog-price-truth-v1"
