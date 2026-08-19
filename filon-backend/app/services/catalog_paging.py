"""Lecture exhaustive, par lots stables, des offres filtrées du catalogue.

Les couches Intelligence ne doivent pas décider sur un échantillon arbitraire :
elles lisent toutes les offres qui satisfont leurs critères d’éligibilité, puis
appliquent leur classement. La pagination par clé primaire évite les `OFFSET`
coûteux et garde la mémoire de la requête bornée à un lot lors de la lecture.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TypeVar

from sqlalchemy import Select

from app.db.models import Offer


RowT = TypeVar("RowT")

# Taille technique du lot : ce n’est jamais une limite métier ni une limite de
# couverture. Les pages sont toutes parcourues jusqu’à épuisement de la requête.
DEFAULT_BATCH_SIZE = 500


async def fetch_all_offer_rows(
    execute: Callable[[Select], Awaitable[object]],
    statement: Select,
    *,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> list[RowT]:
    """Retourne toutes les lignes d’une requête d’offres, sans plafond métier.

    La requête initiale peut contenir des jointures, des filtres et des options
    de chargement. Son éventuel ordre est remplacé par `Offer.id` afin que chaque
    page soit déterministe et qu’aucune ligne ne soit sautée ou lue deux fois.
    """
    if batch_size < 1:
        raise ValueError("batch_size must be positive")

    rows: list[RowT] = []
    last_offer_id = 0
    base = statement.order_by(None)

    while True:
        page_result = await execute(
            base.where(Offer.id > last_offer_id)
            .order_by(Offer.id.asc())
            .limit(batch_size)
        )
        page = page_result.all()  # type: ignore[attr-defined]
        if not page:
            break

        rows.extend(page)
        last_offer_id = page[-1][0].id
        if len(page) < batch_size:
            break

    return rows
