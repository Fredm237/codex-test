"""Lecture groupée des relevés qui prouvent une offre courante.

`Offer.updated_at` est un horodatage technique mutable. Il ne prouve ni le
prix, ni sa devise, ni le stock. Cette passerelle ne reconnaît donc que les
snapshots append-only qui portent explicitement ces trois faits.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import func, or_, select

from app.db.models import Offer, PriceSnapshot
from app.services.currency import normalize_currency_code
from app.services.freshness import parse_observed_at


@dataclass(frozen=True)
class OfferEvidence:
    currency: str | None
    history: tuple[tuple[float, datetime], ...]
    current_observed_at: datetime | None


# Le catalogue peut remettre plusieurs milliers d'offres aux retrievers. Le lot
# reste volontairement sous les limites de paramètres des moteurs SQL supportés
# et borne aussi la taille d'une page d'historique complet.
OFFER_EVIDENCE_BATCH_SIZE = 500


def _identity(offer: object) -> int | None:
    value = getattr(offer, "offer_id", None)
    if value is None:
        value = getattr(offer, "id", None)
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _valid_price(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value > 0
    )


def _confirmed_stock(offer: object) -> bool:
    if hasattr(offer, "in_stock"):
        return getattr(offer, "in_stock") is True
    return getattr(offer, "availability", None) == "in_stock"


def _same_current_offer_state(
    offer: object,
    *,
    price: object,
    currency: object,
    in_stock: object,
) -> bool:
    """Refuse une preuve si la ligne Offre a changé depuis son hydratation.

    Le chemin ``current_only`` joint la table des offres pour laisser SQL
    agréger au plus un horodatage par identifiant. Cette revalidation empêche
    qu'une mutation concurrente rattache cette preuve à l'ancien snapshot Python.
    """

    offer_price = getattr(offer, "price", None)
    offer_currency = normalize_currency_code(getattr(offer, "currency", None))
    return (
        _confirmed_stock(offer)
        and in_stock is True
        and _valid_price(offer_price)
        and _valid_price(price)
        # Une différence, même minime, peut signaler une mutation concurrente.
        # La tolérance ne vaut que pour snapshot source ↔ ligne DB, pas pour
        # ligne DB ↔ objet déjà hydraté.
        and float(price) == float(offer_price)
        and offer_currency is not None
        and normalize_currency_code(currency) == offer_currency
    )


def _batches(values: tuple[int, ...]):
    for start in range(0, len(values), OFFER_EVIDENCE_BATCH_SIZE):
        yield values[start : start + OFFER_EVIDENCE_BATCH_SIZE]


def _current_observations_statement(offer_ids: tuple[int, ...]):
    """Agrège la dernière preuve du prix+devise+stock actuellement exposé.

    La comparaison approximative reproduit ``math.isclose`` (tolérance absolue
    0,005 et relative 1e-9). Les contrôles Python restent autoritaires : le SQL
    réduit le volume, il ne rend jamais une devise ou un nombre valide.
    """

    price_delta = func.abs(PriceSnapshot.price - Offer.price)
    price_matches = or_(
        price_delta <= 0.005,
        price_delta <= func.abs(PriceSnapshot.price) * 1e-9,
        price_delta <= func.abs(Offer.price) * 1e-9,
    )
    return (
        select(
            PriceSnapshot.offer_id,
            Offer.price,
            Offer.currency,
            Offer.in_stock,
            func.max(PriceSnapshot.captured_at),
        )
        .join(Offer, Offer.id == PriceSnapshot.offer_id)
        .where(
            PriceSnapshot.offer_id.in_(offer_ids),
            PriceSnapshot.in_stock.is_(True),
            Offer.in_stock.is_(True),
            PriceSnapshot.price > 0,
            Offer.price > 0,
            func.upper(func.trim(PriceSnapshot.currency))
            == func.upper(func.trim(Offer.currency)),
            price_matches,
        )
        .group_by(
            PriceSnapshot.offer_id,
            Offer.price,
            Offer.currency,
            Offer.in_stock,
        )
    )


async def load_offer_evidence(
    session: Any,
    offers: list[object],
    *,
    current_only: bool = False,
) -> dict[int, OfferEvidence]:
    """Charge par lots les preuves comparables de chaque offre.

    Les anciens snapshots sans devise restent exclus. Les montants hors stock
    ne deviennent pas des prix achetables. Un horodatage futur est conservé
    dans l'historique afin que la couche de décision puisse invalider la preuve
    au lieu de le masquer. ``current_only`` ne matérialise aucun historique :
    SQL renvoie au plus le dernier relevé courant de chaque offre du lot.
    """

    indexed: dict[int, object] = {}
    for offer in offers:
        offer_id = _identity(offer)
        if offer_id is not None:
            indexed[offer_id] = offer
    if not indexed:
        return {}

    histories: dict[int, list[tuple[float, datetime]]] = {
        offer_id: [] for offer_id in indexed
    }
    current_observations: dict[int, list[datetime]] = {
        offer_id: [] for offer_id in indexed
    }
    for offer_ids in _batches(tuple(indexed)):
        if current_only:
            rows = await session.execute(_current_observations_statement(offer_ids))
            for offer_id, price, currency, in_stock, captured_at in rows.all():
                offer = indexed.get(offer_id)
                observed_at = parse_observed_at(captured_at)
                if (
                    offer is None
                    or observed_at is None
                    or not _same_current_offer_state(
                        offer,
                        price=price,
                        currency=currency,
                        in_stock=in_stock,
                    )
                ):
                    continue
                current_observations[offer_id].append(observed_at)
            continue

        rows = await session.execute(
            select(
                PriceSnapshot.offer_id,
                PriceSnapshot.price,
                PriceSnapshot.currency,
                PriceSnapshot.in_stock,
                PriceSnapshot.captured_at,
            )
            .where(PriceSnapshot.offer_id.in_(offer_ids))
            .order_by(PriceSnapshot.offer_id, PriceSnapshot.captured_at)
        )
        for offer_id, price, currency, in_stock, captured_at in rows.all():
            offer = indexed.get(offer_id)
            if offer is None:
                continue
            normalized_currency = normalize_currency_code(currency)
            offer_currency = normalize_currency_code(getattr(offer, "currency", None))
            observed_at = parse_observed_at(captured_at)
            if (
                normalized_currency is None
                or normalized_currency != offer_currency
                or not _valid_price(price)
                or in_stock is not True
                or observed_at is None
            ):
                continue
            histories[offer_id].append((float(price), observed_at))
            offer_price = getattr(offer, "price", None)
            if (
                _confirmed_stock(offer)
                and _valid_price(offer_price)
                and math.isclose(float(price), float(offer_price), abs_tol=0.005)
            ):
                current_observations[offer_id].append(observed_at)

    return {
        offer_id: OfferEvidence(
            currency=normalize_currency_code(getattr(offer, "currency", None)),
            history=tuple(histories[offer_id]),
            current_observed_at=max(current_observations[offer_id], default=None),
        )
        for offer_id, offer in indexed.items()
    }
