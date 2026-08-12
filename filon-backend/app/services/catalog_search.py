"""Recherche dans le catalogue interne FILON pour l'assistant.

Interroge la base de données (1,3M offres, 207 marchands) au lieu de Google Shopping.
Retourne des produits réels avec prix, marchand, image, lien affilié Awin.

Priorité : base interne > SerpApi (fallback).
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import and_

from app.core.logging import get_logger
from app.db.session import session_scope
from app.db.models import Merchant, Offer
from app.services.search import search_clause, terms_of

log = get_logger("catalog_search")


async def search_internal_products(
    query: str, budget: float | None, *, limit: int = 20, country: str | None = None
) -> list[dict[str, Any]]:
    """Recherche dans le catalogue interne FILON.

    Retourne une liste de produits normalisés (même format que serpapi_shopping)
    pour être directement utilisable par recommend.py.
    """
    terms = terms_of(query)
    if not terms:
        return []

    try:
        async with session_scope() as session:
            if session is None:
                log.warning("Base de données non disponible")
                return []

            # Construire la clause de recherche
            clause = search_clause(query)
            if clause is None:
                return []

            from sqlalchemy import select
            from sqlalchemy.orm import joinedload as jl

            # Requête : offres canoniques (dédupliquées), pas adultes, avec prix
            stmt = (
                select(Offer)
                .join(Merchant, Offer.merchant_id == Merchant.id)
                .where(
                    and_(
                        clause,
                        Offer.is_canonical == True,
                        Offer.is_adult == False,
                        Offer.price.isnot(None),
                        Offer.price > 0,
                    )
                )
                .options(jl(Offer.merchant))
                .order_by(Offer.price.asc())
            )

            # Filtre budget si spécifié
            if budget:
                stmt = stmt.where(Offer.price <= budget * 1.1)

            # Limiter les résultats
            stmt = stmt.limit(limit)

            result = await session.execute(stmt)
            offers = result.scalars().all()

            products: list[dict[str, Any]] = []
            for offer in offers:
                products.append({
                    "name": offer.name,
                    "price": int(round(offer.price)),
                    "merchant": offer.merchant.name if offer.merchant else "marchand",
                    "image": offer.image_url,
                    "link": offer.deep_link or offer.product_url,
                    "delivery": "voir marchand",
                    "rating": None,
                    "reviews": None,
                    "source": "filon_catalog",
                })

            log.info(
                "Catalogue interne : %d produits pour '%s' (budget=%s)",
                len(products), query[:40], budget
            )
            return products

    except Exception as exc:
        log.warning("Erreur recherche catalogue interne (%s) → fallback SerpApi", exc)
        return []
