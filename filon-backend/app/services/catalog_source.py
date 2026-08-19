"""Passerelle entre le catalogue réel et les agents.

Les agents lisaient `app/data/catalog.py` — quatre ordinateurs portables codés
en dur, chez des marchands avec lesquels FILON n'a aucun partenariat. Le
copilote répondait donc à côté de sa propre base : 795 000 offres ingérées, et
aucune servie.

Ce module interroge la base et rend des produits au format que les agents
attendent déjà, pour que le branchement ne réécrive pas toute la chaîne.
"""

from __future__ import annotations

import re

from sqlalchemy import or_, select

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db import models
from app.db import session as db
from app.services import relevance

log = get_logger("catalog_source")

# Mots vides : les retirer évite de chercher « pour » ou « avec » dans les noms.
_STOPWORDS = {
    "un", "une", "des", "le", "la", "les", "de", "du", "pour", "avec", "sans",
    "et", "ou", "en", "au", "aux", "dans", "sur", "je", "veux", "cherche",
    "besoin", "bon", "bonne", "meilleur", "meilleure", "euros", "eur", "moins",
    "plus", "qui", "que", "quoi", "mon", "ma", "mes", "ce", "cette", "est",
}


def keywords(text: str) -> list[str]:
    """Termes de recherche exploitables, extraits d'une question en langage naturel."""
    words = re.findall(r"[\w'-]{3,}", (text or "").lower())
    return [w for w in words if w not in _STOPWORDS][:6]


def _shape(
    *,
    product_id: str,
    name: str,
    brand: str | None,
    category: str | None,
    image: str | None,
    offers: list[tuple],
    relevance_score: float = 0.0,
) -> dict:
    """Format attendu par les agents en aval (product_search, price_compare…)."""
    return {
        "product_id": product_id,
        "name": name,
        "brand": brand,
        "category": category,
        # Score de correspondance à la demande : c'est lui qui classe en aval,
        # devant le prix. Sans lui, le moins cher gagnait toujours.
        "relevance": relevance_score,
        "tags": keywords(name),
        "specs": {},
        "rating": None,
        "reviews_count": 0,
        "image": image,
        "offers": [
            {
                "merchant": m.name,
                "merchant_slug": m.slug,
                "price": o.price,
                "currency": o.currency,
                "url": o.deep_link,
                "in_stock": o.in_stock,
                # Attendus par les agents, absents des flux Awin : rester à None
                # plutôt que d'inventer un délai de livraison ou une garantie.
                "delivery_days": None,
                "warranty_months": None,
                "affiliate_network": "Awin",
            }
            for (o, m) in offers
            if o.price is not None
        ],
    }


async def search_products(
    query: str,
    *,
    budget_max: float | None = None,
    limit: int = 5,
) -> list[dict]:
    """Cherche dans le catalogue réel et rend au plus `limit` produits.

    Les offres partageant un même produit regroupé (même EAN chez plusieurs
    marchands) sont réunies : c'est exactement ce dont le comparateur a besoin.
    Rend une liste vide si la base est absente — l'appelant décide alors quoi
    faire, plutôt que de recevoir des données inventées.
    """
    terms = keywords(query)
    if not terms:
        return []

    async with db.session_scope() as session:
        if session is None:
            return []

        # Les termes les plus discriminants doivent TOUS être présents.
        #
        # Le filtre unissait auparavant les termes par OU : un seul mot commun
        # suffisait, et « machine à café » remontait « Crazy Machines ». On exige
        # désormais les deux termes les plus spécifiques, ce qui écarte la
        # correspondance accidentelle sans imposer la phrase entière — un nom
        # d'offre ne reprend jamais toute une demande.
        exigés = relevance.termes_significatifs(terms)[:2] or terms[:1]

        stmt = (
            select(models.Offer, models.Merchant)
            .join(models.Merchant, models.Offer.merchant_id == models.Merchant.id)
            .where(
                models.Offer.price.isnot(None),
                models.Offer.price > 0,
                models.Offer.image_url.isnot(None),
                *[models.Offer.name.ilike(f"%{t}%") for t in exigés],
            )
        )
        blocked = get_settings().blocked_merchant_slugs
        if blocked:
            stmt = stmt.where(models.Merchant.slug.notin_(blocked))
        if budget_max:
            # Marge de 5 % : une offre à peine au-dessus du budget reste utile.
            stmt = stmt.where(models.Offer.price <= budget_max * 1.05)

        # On récupère large, puis on regroupe et on classe en mémoire.
        #
        # Le tri par prix croissant se faisait AVANT la limite : on ne chargeait
        # donc que les cent articles les moins chers contenant un mot, et les
        # vrais candidats n'étaient jamais lus — aucun classement en mémoire ne
        # pouvait les rattraper. On charge maintenant un échantillon plus large,
        # sans le biaiser par le prix, et c'est la pertinence qui tranche.
        rows = (await session.execute(stmt.limit(400))).all()
        if not rows:
            return []

        # Les offres qui ne répondent pas à la demande sont écartées ici, pas
        # rangées derrière : mieux vaut ne rien proposer qu'un article à côté.
        pertinentes = [
            pair for pair in rows
            if relevance.score(
                terms, pair[0].name or "",
                offer_kind=getattr(pair[0], "offer_kind", None),
            ) >= relevance.SEUIL
        ]
        if not pertinentes:
            log.info("catalog_search_sans_correspondance", extra={"query": query[:80]})
            return []
        rows = pertinentes

        grouped: dict[object, list[tuple]] = {}
        for pair in rows:
            offer = pair[0]
            key = offer.product_id if offer.product_id is not None else ("offer", offer.id)
            grouped.setdefault(key, []).append(pair)

        # Un seul aller-retour pour les libellés canoniques des produits groupés.
        product_ids = [k for k in grouped if not isinstance(k, tuple)]
        canonical: dict[int, models.CatalogProduct] = {}
        if product_ids:
            canonical = {
                p.id: p
                for p in (
                    await session.execute(
                        select(models.CatalogProduct).where(
                            models.CatalogProduct.id.in_(product_ids)
                        )
                    )
                ).scalars()
            }

        products: list[dict] = []
        for key, offers in grouped.items():
            offers.sort(key=lambda pair: pair[0].price)
            first = offers[0][0]
            product = canonical.get(key) if not isinstance(key, tuple) else None
            products.append(
                _shape(
                    product_id=(product.ean if product else f"offer-{first.id}"),
                    name=(product.name if product else first.name),
                    brand=(product.brand if product else first.brand),
                    category=(product.category if product else first.category),
                    image=(product.image_url if product else first.image_url),
                    offers=offers,
                    # Le nom présenté au visiteur est celui du produit regroupé
                    # quand il existe : c'est donc lui qu'on note, pas l'offre.
                    relevance_score=relevance.score(
                        terms,
                        (product.name if product else first.name) or "",
                        offer_kind=getattr(first, "offer_kind", None),
                    ),
                )
            )

        products = [p for p in products if p["offers"]]
        # Le classement final : correspondance d'abord, prix ensuite. Trier sur
        # le seul prix faisait remonter l'article le moins cher du lot, pas le
        # plus proche de la demande.
        products.sort(
            key=lambda p: (-round(p.get("relevance") or 0.0, 1),
                           min(o["price"] for o in p["offers"]))
        )
        log.info("Catalogue réel : %d produits pour « %s »", len(products), query)
        return products[:limit]
