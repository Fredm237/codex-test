"""Politique temporelle minimale des offres utilisées pour recommander."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta


# Frontière déjà utilisée par le Decision Service : au-delà, un prix ne
# renforçait plus une décision. Le comparateur et le planificateur l'appliquent
# désormais comme TTL provisoire commun au prix et au stock observés.
OFFER_RECOMMENDATION_MAX_AGE_HOURS = 72


def parse_observed_at(value: object) -> datetime | None:
    if isinstance(value, datetime):
        observed = value
    elif isinstance(value, str):
        try:
            observed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        return None
    if observed.tzinfo is None or observed.utcoffset() is None:
        return observed.replace(tzinfo=UTC)
    return observed.astimezone(UTC)


def format_utc_timestamp(value: object) -> str | None:
    """Sérialise un instant public avec un décalage UTC explicite.

    Les colonnes SQL historiques restent volontairement UTC naïves pour leur
    compatibilité avec asyncpg. Cette convention de stockage ne doit jamais
    franchir le contrat HTTP : un client ne peut pas deviner le fuseau d'une
    chaîne ISO sans offset.
    """

    observed = parse_observed_at(value)
    return observed.isoformat() if observed is not None else None


def offer_observation_is_fresh(
    observed_at: object,
    *,
    now: datetime | None = None,
) -> bool:
    """Vrai uniquement pour une observation datée, non future et sous le TTL."""

    observed = parse_observed_at(observed_at)
    if observed is None:
        return False
    reference = now or datetime.now(UTC)
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=UTC)
    else:
        reference = reference.astimezone(UTC)
    age = reference - observed
    return timedelta(0) <= age <= timedelta(
        hours=OFFER_RECOMMENDATION_MAX_AGE_HOURS
    )
