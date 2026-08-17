"""Adaptateur lecture seule entre le catalogue FILON Core et les experts.

Aucune écriture, aucun appel affilié et aucun enrichissement marchand ne se fait
ici. L’adaptateur réduit les offres à une vue vérifiée utilisable par l’expert.
"""

from __future__ import annotations

import re

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import models
from app.intelligence.contracts import CoreOfferSnapshot
from app.services import search, taxonomy


FASHION_CATEGORIES = frozenset(taxonomy.categories_of_department("Mode & Accessoires"))


def _availability(in_stock: bool | None) -> str:
    if in_stock is True:
        return "in_stock"
    if in_stock is False:
        return "out_of_stock"
    return "unknown"


def _search_terms(query: str | None) -> list[str]:
    if not query:
        return []
    # Les mots très courts sont trop bruyants pour une recherche sur millions
    # d’offres. Le moteur Fashion interprète le contexte ailleurs; ici, on ne
    # filtre que les mots explicitement présents dans le nom ou la marque.
    terms = re.findall(r"[\wÀ-ÿ'-]+", query.lower())
    return [term for term in terms if len(term) >= 3][:5]


async def retrieve_fashion_offers(
    session: AsyncSession,
    *,
    query: str | None = None,
    limit: int = 120,
) -> list[CoreOfferSnapshot]:
    """Retourne des offres Fashion admissibles sans modifier le Core.

    Le contrat M1 est volontairement strict : offre physique, publique,
    canonique, non adulte, avec image et prix. Le stock inconnu reste possible
    mais est porté comme incertitude; le stock explicitement absent est exclu.
    """
    safe_limit = max(1, min(limit, 200))
    stmt = (
        select(models.Offer, models.Merchant)
        .join(models.Merchant, models.Offer.merchant_id == models.Merchant.id)
        .where(
            models.Offer.filon_category.in_(FASHION_CATEGORIES),
            models.Offer.offer_kind == taxonomy.PHYSICAL_PRODUCT,
            models.Offer.is_canonical.is_(True),
            # Même règle que le catalogue public : les lignes historiques sans
            # marquage sont visibles, les offres explicitement adultes ne le sont jamais.
            or_(models.Offer.is_adult.is_(False), models.Offer.is_adult.is_(None)),
            models.Offer.price.isnot(None),
            models.Offer.currency.isnot(None),
            models.Offer.image_url.isnot(None),
            models.Offer.image_url != "",
            or_(models.Offer.in_stock.is_(True), models.Offer.in_stock.is_(None)),
        )
    )
    terms = _search_terms(query)
    for term in terms:
        needle = f"%{term}%"
        stmt = stmt.where(or_(models.Offer.name.ilike(needle), models.Offer.brand.ilike(needle)))

    # Un tri global par prix sur tout le département Fashion dépasse largement
    # le budget d’interaction. On préserve la pertinence recherchée (si la
    # personne a nommé une pièce), puis le Fashion Expert compare les prix connus
    # dans cet ensemble réel. Il ne prétend donc jamais avoir trouvé « le moins
    # cher de tout le catalogue ».
    relevance = search.relevance_order(query)
    if relevance is not None:
        stmt = stmt.order_by(relevance.asc(), models.Offer.id.asc())
    else:
        stmt = stmt.order_by(models.Offer.id.desc())
    stmt = stmt.limit(safe_limit)
    rows = (await session.execute(stmt)).all()
    return [
        CoreOfferSnapshot(
            offer_id=offer.id,
            catalog_product_id=offer.product_id,
            name=offer.name,
            brand=offer.brand,
            filon_category=offer.filon_category,
            filon_subcategory=offer.filon_subcategory,
            offer_kind=offer.offer_kind,
            price=offer.price,
            currency=offer.currency,
            availability=_availability(offer.in_stock),
            image_url=offer.image_url,
            deep_link=offer.deep_link,
            merchant_id=merchant.id,
            merchant_name=merchant.name,
            merchant_region=merchant.region,
            observed_at=offer.updated_at,
        )
        for offer, merchant in rows
    ]
