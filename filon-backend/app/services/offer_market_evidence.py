"""Preuves du marché de publication d'une offre.

Une région marchand décrit le marchand. Seule l'observation issue du feed
permet d'affirmer qu'une offre a été publiée pour un marché. Cette preuve ne
garantit ni livraison, ni frais, ni délai à une adresse particulière.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import select

from app.observations.models import Observation
from app.services.freshness import parse_observed_at


@dataclass(frozen=True)
class OfferMarketEvidence:
    country_code: str
    observed_at: datetime
    evidence_ref: str


async def load_offer_listing_markets(
    session: Any,
    offer_ids: list[int],
) -> dict[int, tuple[OfferMarketEvidence, ...]]:
    """Charge les dernières preuves vérifiées par offre et par marché."""

    bounded_ids = tuple(sorted({value for value in offer_ids if value > 0}))
    if not bounded_ids:
        return {}
    rows = await session.execute(
        select(
            Observation.id,
            Observation.offer_id,
            Observation.value_json,
            Observation.observed_at,
        )
        .where(
            Observation.offer_id.in_(bounded_ids),
            Observation.field == "listing_market",
            Observation.status == "verified",
            Observation.confidence == 1.0,
        )
        .order_by(
            Observation.offer_id,
            Observation.observed_at.desc(),
            Observation.id.desc(),
        )
    )
    latest: dict[tuple[int, str], OfferMarketEvidence] = {}
    for observation_id, offer_id, value, observed_at in rows.all():
        country = value.strip().upper() if isinstance(value, str) else ""
        timestamp = parse_observed_at(observed_at)
        if (
            not isinstance(offer_id, int)
            or not re.fullmatch(r"[A-Z]{2}", country)
            or timestamp is None
        ):
            continue
        key = (offer_id, country)
        latest.setdefault(
            key,
            OfferMarketEvidence(
                country_code=country,
                observed_at=timestamp,
                evidence_ref=f"observation:{observation_id}:listing_market",
            ),
        )
    grouped: dict[int, list[OfferMarketEvidence]] = {}
    for (offer_id, _country), evidence in sorted(latest.items()):
        grouped.setdefault(offer_id, []).append(evidence)
    return {offer_id: tuple(values) for offer_id, values in grouped.items()}
