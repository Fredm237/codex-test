"""Recherche dans le catalogue interne FILON pour l'assistant.

Interroge la base de données (1,3M offres, 207 marchands) au lieu de Google Shopping.
Retourne des produits réels avec prix, marchand, image, lien affilié Awin.

Priorité : base interne > SerpApi (fallback).
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any

from sqlalchemy import and_, func, not_, or_, select

from app.core.logging import get_logger
from app.db.session import session_scope
from app.db.models import CatalogProduct, Merchant, Offer, PriceSnapshot
from app.services import decision
from app.services.search import search_clause, terms_of

log = get_logger("catalog_search")


# Une requête d'assistant est rarement un titre de produit : « un ordinateur
# portable étudiant sous 800 € » contient une intention, un budget et des mots
# qui ne figurent jamais dans un feed. Les ancres ci-dessous servent uniquement
# à resserrer une recherche vers le rayon demandé ; elles ne fabriquent aucun
# résultat et ne font appel à aucune source externe.
_INTENT_ANCHORS: tuple[tuple[tuple[str, ...], str, tuple[str, ...]], ...] = (
    (
        ("ordinateur", "laptop", "notebook", "macbook", "computer", "pc portable", "montage", "video editing", "videomontage"),
        "laptop",
        ("housse", "hoes", "sleeve", "pochette", "sac", "support", "stand", "chargeur", "charger", "cable", "adaptateur", "keyboard", "clavier", "souris", "mouse"),
    ),
    (
        ("smartphone", "telephone", "telefoon", "iphone", "android"),
        "smartphone",
        ("coque", "case", "cover", "hoes", "protection", "protector", "verre", "glass", "chargeur", "charger", "cable", "adaptateur", "support"),
    ),
    (
        ("casque", "headphone", "koptelefoon", "noise cancelling", "noise-cancelling"),
        "casque",
        ("housse", "hoes", "case", "cable", "adaptateur", "support", "earpad", "coussin"),
    ),
)


# Un flux peut publier un prix technique (1 €) ou une garantie sous un nom de
# produit. Ces seuils ne donnent pas une valeur de marché : ils empêchent
# seulement qu'un produit principal soit présenté à un prix invraisemblable.
_PRIMARY_MIN_PRICE = {"laptop": 200.0, "smartphone": 80.0, "casque": 25.0}


def _required_name_terms(query: str, anchor: str) -> tuple[str, ...]:
    """Contraintes explicites que le titre du produit doit confirmer.

    Une demande « réduction de bruit » ne peut pas être satisfaite par un casque
    Bluetooth ordinaire. Si le feed ne porte pas cette caractéristique, l'absence
    d'offre vérifiée est plus honnête qu'une recommandation hors besoin.
    """
    normalized = " ".join(terms_of(query))
    if anchor == "casque" and any(token in normalized for token in ("bruit", "noise", "cancellation", "cancelling", "anc")):
        return ("reduction de bruit", "noise", "anc", "cancel")
    return ()


def _catalogue_intent(query: str) -> tuple[str, tuple[str, ...]] | None:
    """Retourne une ancre catalogue et les accessoires à exclure pour un besoin courant."""
    normalized = " ".join(terms_of(query))
    for triggers, anchor, excluded in _INTENT_ANCHORS:
        if any(trigger in normalized for trigger in triggers):
            return anchor, excluded
    return None


def _primary_image_url(value: str | None) -> str | None:
    """Conserve une URL image unique quand le feed en fournit plusieurs séparées par des virgules."""
    if not value:
        return None
    for candidate in value.split(","):
        url = candidate.strip()
        if url.startswith(("https://", "http://")):
            return url
    return None


async def _decisions_for_offers(session, offers: list[Offer]) -> dict[int, dict[str, Any]]:
    """Calcule les décisions des offres assistant à partir des mêmes preuves que les fiches.

    Les historiques et produits regroupés sont lus par lots : l'assistant ne doit
    pas déclencher une requête par carte ni posséder ses propres règles de score.
    """
    offer_ids = [offer.id for offer in offers]
    if not offer_ids:
        return {}

    product_ids = {offer.product_id for offer in offers if offer.product_id is not None}
    grouped_by_id: dict[int, CatalogProduct] = {}
    if product_ids:
        grouped = (
            await session.execute(select(CatalogProduct).where(CatalogProduct.id.in_(product_ids)))
        ).scalars().all()
        grouped_by_id = {product.id: product for product in grouped}

    histories: dict[int, list[tuple[float | None, Any]]] = defaultdict(list)
    history_rows = await session.execute(
        select(PriceSnapshot.offer_id, PriceSnapshot.price, PriceSnapshot.captured_at)
        .where(PriceSnapshot.offer_id.in_(offer_ids))
        .order_by(PriceSnapshot.offer_id, PriceSnapshot.captured_at)
    )
    for offer_id, price, captured_at in history_rows.all():
        histories[offer_id].append((price, captured_at))

    decisions: dict[int, dict[str, Any]] = {}
    for offer in offers:
        grouped = grouped_by_id.get(offer.product_id)
        decisions[offer.id] = decision.compute_decision(
            price=offer.price,
            currency=offer.currency,
            history=histories[offer.id],
            cheapest_elsewhere=grouped.price_min if grouped else None,
            comparison_currency=grouped.currency if grouped else offer.currency,
            merchants_count=grouped.merchants_count if grouped else 1,
            offers_count=grouped.offers_count if grouped else 1,
            in_stock=offer.in_stock,
            updated_at=offer.updated_at,
        )
    return decisions


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

            # Une demande en langage naturel est ancrée sur son produit principal.
            # Sans cela, la conjonction « ordinateur + étudiant + 800 » ne peut
            # jamais correspondre à un titre de feed et masque les vraies offres.
            intent = _catalogue_intent(query)
            search_query = intent[0] if intent else query
            clause = search_clause(search_query)
            if clause is None:
                return []

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

            # Les feeds classent parfois housses et supports dans le même
            # sous-rayon qu'un ordinateur ou un téléphone. Pour un besoin explicite
            # de produit principal, on les exclut avant de classer les résultats.
            if intent:
                anchor, excluded = intent
                lowered_name = func.lower(Offer.name)
                stmt = stmt.where(
                    not_(or_(*[lowered_name.contains(term) for term in excluded]))
                )
                min_primary_price = _PRIMARY_MIN_PRICE.get(anchor)
                if min_primary_price is not None:
                    stmt = stmt.where(Offer.price >= min_primary_price)
                required = _required_name_terms(query, anchor)
                if required:
                    stmt = stmt.where(or_(*[lowered_name.contains(term) for term in required]))

            # Filtre budget si spécifié
            if budget:
                stmt = stmt.where(Offer.price <= budget * 1.1)

            # Limiter les résultats
            stmt = stmt.limit(limit)

            result = await session.execute(stmt)
            offers = result.scalars().all()

            decisions = await _decisions_for_offers(session, offers)
            products: list[dict[str, Any]] = []
            for offer in offers:
                products.append({
                    "offer_id": offer.id,
                    "product_ean": offer.ean,
                    "name": offer.name,
                    "price": int(round(offer.price)),
                    # La devise est celle de l'offre relevée. Le pays de contexte
                    # choisi par l’utilisateur ne permet pas d'en déduire une autre.
                    "currency": offer.currency or "EUR",
                    "merchant": offer.merchant.name if offer.merchant else "marchand",
                    "image": _primary_image_url(offer.image_url),
                    "link": offer.deep_link or offer.product_url,
                    "delivery": None,
                    "rating": None,
                    "reviews": None,
                    "decision": decisions.get(offer.id),
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
