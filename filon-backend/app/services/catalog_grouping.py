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

import asyncio
import re
from collections import Counter, defaultdict

from sqlalchemy import bindparam, func, select, update

from app.core.logging import get_logger
from app.db import models

log = get_logger("grouping")

# Un seul regroupement à la fois, quel que soit l'appelant. Le cron appelle
# rebuild_products directement : un verrou posé sur l'endpoint seul laissait
# passer les exécutions concurrentes, d'où les interblocages et l'épuisement du
# pool de connexions observés en production.
_lock = asyncio.Lock()


def is_rebuilding() -> bool:
    return _lock.locked()


def _insert_ignoring_duplicates(session, table):
    """INSERT qui ignore les EAN déjà présents.

    Deux exécutions qui se chevauchent peuvent voir le même EAN comme absent et
    l'insérer toutes les deux : sans cette clause, la seconde violait la
    contrainte d'unicité et faisait échouer tout le regroupement.
    """
    name = session.bind.dialect.name if session.bind is not None else ""
    if name == "postgresql":
        from sqlalchemy.dialects.postgresql import insert as _insert
    elif name == "sqlite":
        from sqlalchemy.dialects.sqlite import insert as _insert
    else:
        return table.insert()
    return _insert(table).on_conflict_do_nothing(index_elements=["ean"])

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


def _consensus(counts: Counter) -> str | None:
    """Valeur la plus fréquente parmi les marchands (départage : la plus courte).

    Les marchands enjolivent les libellés (« - Livraison gratuite ! »). Le
    consensus est plus fiable que le premier venu.
    """
    if not counts:
        return None
    best = max(counts.values())
    return min((v for v, n in counts.items() if n == best), key=len)


class _Aggregate:
    """Agrégat compact d'un produit, alimenté au fil de la lecture.

    On ne conserve jamais les lignes elles-mêmes : à 800 000 offres, les
    matérialiser saturait la mémoire du conteneur et le processus était tué en
    plein rattachement. Seuls quelques compteurs bornés survivent à la lecture.
    """

    __slots__ = ("names", "brands", "categories", "currencies", "image",
                 "price_min", "price_max", "merchants", "count")

    # Le consensus n'a pas besoin de tout voir : quelques variantes suffisent.
    MAX_VARIANTS = 5

    def __init__(self) -> None:
        self.names: Counter = Counter()
        self.brands: Counter = Counter()
        self.categories: Counter = Counter()
        self.currencies: Counter = Counter()
        self.image: str | None = None
        self.price_min: float | None = None
        self.price_max: float | None = None
        self.merchants: set[int] = set()
        self.count = 0

    @staticmethod
    def _bump(counter: Counter, value: str | None) -> None:
        if not value:
            return
        value = value.strip()
        if value and (value in counter or len(counter) < _Aggregate.MAX_VARIANTS):
            counter[value] += 1

    def add(self, row) -> None:
        self.count += 1
        self._bump(self.names, row.name)
        self._bump(self.brands, row.brand)
        self._bump(self.categories, row.category)
        self._bump(self.currencies, row.currency)
        if self.image is None and row.image_url:
            self.image = row.image_url
        if row.price is not None and row.price > 0:
            self.price_min = row.price if self.price_min is None else min(self.price_min, row.price)
            self.price_max = row.price if self.price_max is None else max(self.price_max, row.price)
        self.merchants.add(row.merchant_id)

    def values(self, ean: str) -> dict:
        return {
            "ean": ean,
            "name": (_consensus(self.names) or "")[:512],
            "brand": _consensus(self.brands),
            "category": _consensus(self.categories),
            "image_url": self.image,
            "offers_count": self.count,
            "merchants_count": len(self.merchants),
            "price_min": self.price_min,
            "price_max": self.price_max,
            "currency": _consensus(self.currencies),
        }


async def _iter_offer_pages(session, columns, *, page: int):
    """Parcourt les offres par pages ordonnées par id (curseur, pas OFFSET).

    OFFSET se dégrade linéairement sur des centaines de milliers de lignes ;
    le curseur sur la clé primaire reste constant.
    """
    last_id = 0
    while True:
        rows = (
            await session.execute(
                select(*columns)
                .where(models.Offer.id > last_id)
                .order_by(models.Offer.id)
                .limit(page)
            )
        ).all()
        if not rows:
            return
        yield rows
        last_id = rows[-1].id


def _shard_of(ean: str, shards: int) -> int:
    """Tranche déterministe d'un EAN (les derniers chiffres sont bien répartis)."""
    return int(ean[-4:]) % shards


async def rebuild_products(
    session, *, batch: int = 1000, page: int = 5000, shards: int = 4
) -> dict:
    """Regroupe les offres en produits. Ignore l'appel si un run est en cours."""
    if _lock.locked():
        log.warning("Regroupement EAN déjà en cours : appel ignoré")
        return {"skipped": True, "reason": "regroupement déjà en cours"}
    async with _lock:
        return await _rebuild_products(session, batch=batch, page=page, shards=shards)


async def _rebuild_products(
    session, *, batch: int, page: int, shards: int
) -> dict:
    """Reconstruit les produits à partir des offres. Idempotent.

    Procède en deux passes en flux — agrégation, puis rattachement — afin que la
    mémoire reste bornée quelle que soit la taille du catalogue. L'agrégation est
    en outre découpée en `shards` tranches d'EAN : les agrégats sont
    proportionnels au nombre de produits, et tout retenir d'un coup dépassait ce
    dont dispose le conteneur.

    Renvoie un résumé chiffré, dont le taux d'EAN exploitables : c'est lui qui
    conditionne ce qu'on peut bâtir dessus (multi-marchands, verdict).
    """
    # ── Passe 1 : agrégation par EAN, tranche par tranche ────────────────────
    columns = (
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
    existing = {
        ean: pid
        for (ean, pid) in (
            await session.execute(
                select(models.CatalogProduct.ean, models.CatalogProduct.id)
            )
        ).all()
    }

    total_offers = 0
    grouped_offers = 0
    created = updated = multi_merchant = 0

    for shard in range(shards):
        aggregates: dict[str, _Aggregate] = {}
        async for rows in _iter_offer_pages(session, columns, page=page):
            if shard == 0:
                total_offers += len(rows)
            for r in rows:
                ean = normalize_ean(r.ean)
                if not ean or _shard_of(ean, shards) != shard:
                    continue
                grouped_offers += 1
                agg = aggregates.get(ean)
                if agg is None:
                    agg = aggregates[ean] = _Aggregate()
                agg.add(r)

        to_create: list[dict] = []
        to_update: list[dict] = []
        for ean, agg in aggregates.items():
            if len(agg.merchants) > 1:
                multi_merchant += 1
            (to_update if ean in existing else to_create).append(agg.values(ean))
        aggregates.clear()

        insert_stmt = _insert_ignoring_duplicates(
            session, models.CatalogProduct.__table__
        )
        for start in range(0, len(to_create), batch):
            await session.execute(insert_stmt, to_create[start : start + batch])
        await session.commit()

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

        created += len(to_create)
        updated += len(to_update)
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

    # ── Passe 2 : rattachement, en flux également ─────────────────────────────
    linked = 0
    async for rows in _iter_offer_pages(
        session, (models.Offer.id, models.Offer.ean), page=page
    ):
        mapping = []
        for r in rows:
            ean = normalize_ean(r.ean)
            pid = existing.get(ean) if ean else None
            if pid is not None:
                mapping.append({"id": r.id, "product_id": pid})
        for start in range(0, len(mapping), batch):
            # Bulk update par clé primaire : un aller-retour par lot.
            await session.execute(update(models.Offer), mapping[start : start + batch])
        if mapping:
            await session.commit()
            linked += len(mapping)

    summary = {
        "offers_total": total_offers,
        "offers_with_valid_ean": grouped_offers,
        "ean_coverage_pct": round(grouped_offers / total_offers * 100, 1) if total_offers else 0.0,
        "products_total": len(existing),
        "products_created": created,
        "products_updated": updated,
        "products_multi_merchant": multi_merchant,
        "offers_linked": linked,
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
