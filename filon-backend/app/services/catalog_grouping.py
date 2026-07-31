"""Regroupement des offres en produits, par EAN.

Le catalogue stocke des *offres* : une ligne par produit et par marchand, et
souvent plusieurs lignes pour un même article (déclinaisons d'un feed). Cette
couche les regroupe en *produits* — l'unité qui intéresse l'utilisateur, et
celle qui permet de comparer plusieurs marchands sur une même fiche.

La clé de regroupement est l'EAN, validé strictement : regrouper sur un code
douteux fusionnerait des articles sans rapport, ce qui est bien pire que de ne
pas regrouper du tout. Les offres sans EAN exploitable restent autonomes.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict

from sqlalchemy import bindparam, func, select, update

from app.core.logging import get_logger
from app.db import models

log = get_logger("grouping")

# Longueurs GTIN valides : EAN-8, UPC-A, EAN-13, GTIN-14.
_VALID_LENGTHS = {8, 12, 13, 14}


def _check_digit(digits: str) -> int:
    """Chiffre de contrôle GS1, calculé sur le code privé de son dernier chiffre.

    Poids 3 et 1 alternés en partant de la droite. Vaut pour EAN-8, UPC-A,
    EAN-13 et GTIN-14.
    """
    total = 0
    for i, ch in enumerate(reversed(digits)):
        total += int(ch) * (3 if i % 2 == 0 else 1)
    return (10 - total % 10) % 10


def normalize_ean(raw: str | None) -> str | None:
    """Renvoie un EAN exploitable, ou None.

    Rejette ce que les feeds mettent régulièrement dans ce champ : texte,
    zéros de remplissage, chiffres répétés, longueurs non normalisées et codes
    dont le chiffre de contrôle est faux.
    """
    if not raw:
        return None
    digits = re.sub(r"\D", "", str(raw))
    if len(digits) not in _VALID_LENGTHS:
        return None
    if len(set(digits)) == 1:
        # « 00000000000000 », « 1111111111111 » : remplissage, pas un code.
        return None
    if _check_digit(digits[:-1]) != int(digits[-1]):
        return None
    # Un GTIN-14 ou un UPC-A ne sont qu'un EAN-13 cadré différemment : on
    # normalise sur 13 chiffres pour que les marchands se rejoignent.
    if len(digits) == 14 and digits[0] == "0":
        digits = digits[1:]
    elif len(digits) == 12:
        digits = "0" + digits
    return digits


def _canonical(values: list[str | None]) -> str | None:
    """Valeur la plus fréquente parmi les marchands (départage : la plus courte).

    Les marchands enjolivent les libellés (« - Livraison gratuite ! »). Le
    consensus est plus fiable que le premier venu.
    """
    counts = Counter(v.strip() for v in values if v and v.strip())
    if not counts:
        return None
    best = max(counts.values())
    return min((v for v, n in counts.items() if n == best), key=len)


async def rebuild_products(session, *, batch: int = 1000) -> dict:
    """Reconstruit les produits à partir des offres. Idempotent.

    Renvoie un résumé chiffré — dont le taux d'EAN exploitables, qui conditionne
    tout ce qu'on pourra bâtir dessus (multi-marchands, verdict, alternatives).
    """
    rows = (
        await session.execute(
            select(
                models.Offer.id,
                models.Offer.ean,
                models.Offer.name,
                models.Offer.brand,
                models.Offer.category,
                models.Offer.image_url,
                models.Offer.price,
                models.Offer.currency,
                models.Offer.merchant_id,
            )
        )
    ).all()

    total_offers = len(rows)
    buckets: dict[str, list] = defaultdict(list)
    for r in rows:
        ean = normalize_ean(r.ean)
        if ean:
            buckets[ean].append(r)

    grouped_offers = sum(len(v) for v in buckets.values())

    existing = {
        ean: pid
        for (ean, pid) in (
            await session.execute(
                select(models.CatalogProduct.ean, models.CatalogProduct.id)
            )
        ).all()
    }

    # Construction en mémoire, puis écritures groupées. Une requête par produit
    # ne tient pas à cette échelle : sur ~230 000 produits, cela représentait
    # autant d'allers-retours et le rattachement n'arrivait jamais à son terme.
    to_create: list[dict] = []
    to_update: list[dict] = []
    multi_merchant = 0

    for ean, items in buckets.items():
        prices = [i.price for i in items if i.price is not None and i.price > 0]
        merchants = {i.merchant_id for i in items}
        if len(merchants) > 1:
            multi_merchant += 1

        values = {
            "ean": ean,
            "name": (_canonical([i.name for i in items]) or "")[:512],
            "brand": _canonical([i.brand for i in items]),
            "category": _canonical([i.category for i in items]),
            "image_url": next((i.image_url for i in items if i.image_url), None),
            "offers_count": len(items),
            "merchants_count": len(merchants),
            "price_min": min(prices) if prices else None,
            "price_max": max(prices) if prices else None,
            "currency": _canonical([i.currency for i in items]),
        }
        (to_update if ean in existing else to_create).append(values)

    # Création groupée, puis relecture des identifiants attribués.
    for start in range(0, len(to_create), batch):
        await session.execute(
            models.CatalogProduct.__table__.insert(), to_create[start : start + batch]
        )
    await session.commit()

    if to_create:
        existing.update(
            {
                ean: pid
                for (ean, pid) in (
                    await session.execute(
                        select(models.CatalogProduct.ean, models.CatalogProduct.id)
                    )
                ).all()
            }
        )

    # Mise à jour groupée : un seul aller-retour par lot, au lieu d'un par produit.
    if to_update:
        # Table Core : la clé de mise à jour est l'EAN, pas la clé primaire —
        # la machinerie ORM de bulk-update-by-PK ne s'applique pas ici.
        t = models.CatalogProduct.__table__
        stmt = (
            t.update()
            .where(t.c.ean == bindparam("_ean"))
            .values(
                name=bindparam("_name"),
                brand=bindparam("_brand"),
                category=bindparam("_category"),
                image_url=bindparam("_image_url"),
                offers_count=bindparam("_offers_count"),
                merchants_count=bindparam("_merchants_count"),
                price_min=bindparam("_price_min"),
                price_max=bindparam("_price_max"),
                currency=bindparam("_currency"),
            )
        )
        for start in range(0, len(to_update), batch):
            await session.execute(
                stmt,
                [
                    {f"_{k}": v for k, v in row.items()}
                    for row in to_update[start : start + batch]
                ],
            )
        await session.commit()

    # Rattachement des offres, en écritures groupées elles aussi.
    assignments = [
        (item.id, existing[ean])
        for ean, items in buckets.items()
        if ean in existing
        for item in items
    ]
    # Bulk update par clé primaire : SQLAlchemy génère un WHERE id = :id et
    # regroupe les lignes en un seul aller-retour par lot.
    linked = 0
    for start in range(0, len(assignments), batch):
        chunk = assignments[start : start + batch]
        await session.execute(
            update(models.Offer),
            [{"id": oid, "product_id": pid} for oid, pid in chunk],
        )
        await session.commit()
        linked += len(chunk)

    summary = {
        "offers_total": total_offers,
        "offers_with_valid_ean": grouped_offers,
        "ean_coverage_pct": round(grouped_offers / total_offers * 100, 1) if total_offers else 0.0,
        "products_total": len(buckets),
        "products_created": len(to_create),
        "products_updated": len(to_update),
        "offers_linked": linked,
        "products_multi_merchant": multi_merchant,
    }
    log.info("Regroupement par EAN terminé : %s", summary)
    return summary


async def product_stats(session) -> dict:
    """Chiffres de couverture, sans rien reconstruire."""
    products = await session.scalar(select(func.count()).select_from(models.CatalogProduct))
    multi = await session.scalar(
        select(func.count())
        .select_from(models.CatalogProduct)
        .where(models.CatalogProduct.merchants_count > 1)
    )
    linked = await session.scalar(
        select(func.count())
        .select_from(models.Offer)
        .where(models.Offer.product_id.isnot(None))
    )
    return {
        "products": int(products or 0),
        "products_multi_merchant": int(multi or 0),
        "offers_linked": int(linked or 0),
    }
