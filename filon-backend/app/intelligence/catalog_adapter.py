"""Adaptateur lecture seule entre le catalogue FILON Core et les experts.

Aucune écriture, aucun appel affilié et aucun enrichissement marchand ne se fait
ici. Le retrieval Fashion utilise les sous-rayons FILON indexés : il évite une
recherche textuelle et un tri global sur tout le catalogue Mode.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import models
from app.intelligence.contracts import CoreOfferSnapshot
from app.services import taxonomy


FASHION_CATEGORIES = frozenset(taxonomy.categories_of_department("Mode & Accessoires"))

# Les seuls mots qui déclenchent une recherche sont des pièces explicites. Les
# contextes comme « mariage », « minimal » ou « travail » ne sont jamais traités
# à tort comme un nom de produit marchand.
_PRODUCT_WORDS = frozenset({
    "robe", "dresses", "dress", "jurk", "jurken",
    "veste", "vestes", "blazer", "blazers", "jacket", "jas", "manteau", "coat",
    "jupe", "jupes", "skirt", "rok",
    "pantalon", "pantalons", "jean", "jeans", "broek", "pants",
    "chemise", "chemises", "shirt", "hemd", "tshirt", "t-shirt", "top",
    "chaussure", "chaussures", "shoe", "shoes", "schoen", "schoenen", "sneaker", "sneakers", "basket",
    "sac", "bag", "tas",
})


def _availability(in_stock: bool | None) -> str:
    if in_stock is True:
        return "in_stock"
    if in_stock is False:
        return "out_of_stock"
    return "unknown"


def _search_terms(query: str | None) -> set[str]:
    words = re.findall(r"[\wÀ-ÿ'-]+", (query or "").lower())
    return {word for word in words if word in _PRODUCT_WORDS}


def _fashion_scopes(query: str | None) -> list[dict[str, tuple[str, ...]]]:
    """Scopes Core indexables pour la pièce demandée et ses compléments.

    Chaque scope est un sous-rayon ou un rayon FILON explicitement associé à une
    pièce. Si aucune pièce n’est nommée, le moteur s’abstient plutôt que de
    proposer des produits arbitraires dans un département large.
    """
    terms = _search_terms(query)
    if not terms:
        return []

    scopes: list[dict[str, tuple[str, ...]]] = []
    if terms & {"robe", "dresses", "dress", "jurk", "jurken"}:
        scopes.append({"subcategories": ("Robes",)})
    if terms & {"veste", "vestes", "blazer", "blazers", "jacket", "jas", "manteau", "coat"}:
        scopes.append({"subcategories": ("Manteaux & Vestes",)})
    if terms & {"jupe", "jupes", "skirt", "rok"}:
        scopes.append({"subcategories": ("Jupes",)})
    if terms & {"pantalon", "pantalons", "jean", "jeans", "broek", "pants"}:
        scopes.append({"subcategories": ("Pantalons & Jeans",)})
    if terms & {"chemise", "chemises", "shirt", "hemd", "tshirt", "t-shirt", "top"}:
        scopes.append({"subcategories": ("Hauts & T-shirts",)})

    # Chaussures et accessoires sont récupérés comme compléments vérifiables
    # d’une pièce principale. Ils ne deviennent jamais une « pièce principale »
    # dans le Fashion Expert.
    wants_complements = bool(scopes) or bool(
        terms & {"chaussure", "chaussures", "shoe", "shoes", "schoen", "schoenen", "sneaker", "sneakers", "basket", "sac", "bag", "tas"}
    )
    if wants_complements:
        scopes.append({"categories": (taxonomy.CHAUSSURES,)})
        scopes.append({"categories": (taxonomy.ACCESSOIRES, taxonomy.BAGAGERIE)})
    return scopes


def _scope_clause(scope: dict[str, tuple[str, ...]]):
    if "subcategories" in scope:
        return models.Offer.filon_subcategory.in_(scope["subcategories"])
    return models.Offer.filon_category.in_(scope["categories"])


def _base_statement():
    return (
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


def _snapshot(offer: models.Offer, merchant: models.Merchant) -> CoreOfferSnapshot:
    return CoreOfferSnapshot(
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


async def retrieve_fashion_offers(
    session: AsyncSession,
    *,
    query: str | None = None,
    limit: int = 120,
) -> list[CoreOfferSnapshot]:
    """Retourne des offres Fashion admissibles sans modifier le Core.

    Le contrat M1 est volontairement strict : offre physique, publique,
    canonique, non adulte, avec image et prix. Les scopes étroits permettent une
    réponse réactive sans prétendre couvrir l’intégralité du département ni
    trouver le prix mondial le plus bas.
    """
    scopes = _fashion_scopes(query)
    if not scopes:
        return []

    safe_limit = max(1, min(limit, 180))
    limit_by_scope = max(12, safe_limit // len(scopes))
    seen: set[int] = set()
    snapshots: list[CoreOfferSnapshot] = []
    for scope in scopes:
        stmt = _base_statement().where(_scope_clause(scope)).order_by(models.Offer.id.desc()).limit(limit_by_scope)
        rows = (await session.execute(stmt)).all()
        for offer, merchant in rows:
            if offer.id in seen:
                continue
            seen.add(offer.id)
            snapshots.append(_snapshot(offer, merchant))
    return snapshots
