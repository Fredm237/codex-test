"""Frontière temporelle partagée par les moteurs de recommandation."""

from datetime import UTC, datetime, timedelta

import pytest

from app.services.freshness import (
    OFFER_RECOMMENDATION_MAX_AGE_HOURS,
    offer_observation_is_fresh,
)


NOW = datetime(2026, 8, 29, 12, 0, tzinfo=UTC)


@pytest.mark.parametrize("value", [None, "", "not-a-date", True])
def test_fraicheur_refuse_une_observation_absente_ou_invalide(value):
    assert offer_observation_is_fresh(value, now=NOW) is False


def test_fraicheur_accepte_exactement_la_frontiere_provisoire():
    observed = NOW - timedelta(hours=OFFER_RECOMMENDATION_MAX_AGE_HOURS)

    assert offer_observation_is_fresh(observed, now=NOW) is True
    assert offer_observation_is_fresh(observed.isoformat(), now=NOW) is True


def test_fraicheur_refuse_expiration_et_date_future():
    expired = NOW - timedelta(
        hours=OFFER_RECOMMENDATION_MAX_AGE_HOURS,
        seconds=1,
    )

    assert offer_observation_is_fresh(expired, now=NOW) is False
    assert offer_observation_is_fresh(NOW + timedelta(seconds=1), now=NOW) is False
