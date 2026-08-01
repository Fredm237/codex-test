"""Déduplication du catalogue — un article, une carte.

Les flux relistent le même article par taille, coloris ou lot, et plusieurs
marchands revendent le même produit. Affichés tels quels, ces doublons
remplissaient une page entière de la même chemise.

La clé de regroupement est calculée à l'ingestion et stockée : dédupliquer
795 000 lignes par fenêtrage à chaque affichage coûtait trop cher. Un booléen
indexé (`is_canonical`) rend ensuite le filtrage immédiat.
"""

from __future__ import annotations

import re

from sqlalchemy import select, update

from app.core.logging import get_logger
from app.db import models

log = get_logger("dedup")

# Suffixes de déclinaison à retirer avant comparaison : ils distinguent des
# variantes, pas des produits. « … - Size M », « … 42 », « (lot de 3) ».
# Deux familles, aux exigences différentes.
#
# La mention explicite d'une taille se reconnaît seule. Une pointure nue, elle,
# exige un séparateur devant : sans cette contrainte, « Article numéro 12345 »
# perdait ses deux derniers chiffres et fusionnait avec « Article numéro 123 ».
# Fusionner deux produits distincts est bien pire qu'afficher un doublon.
_VARIANT_SUFFIX = re.compile(
    r"\s*[-–—|,(]?\s*("
    r"(size|taille|maat)\s*[:\s]?\s*[\w./]+"
    r"|lot de \d+|pack of \d+|\d+\s?(pcs|pieces?|stuks)"
    r")\s*\)?\s*$",
    re.IGNORECASE,
)
# Pointure ou taille nue : séparateur obligatoire, deux à trois chiffres.
_VARIANT_NUMBER = re.compile(r"\s[-–—|,]\s*\d{2,3}([./-]\d{2,3})?\s*$")


def dedup_key(*, product_id: int | None, brand: str | None, name: str | None) -> str | None:
    """Clé de regroupement d'une offre.

    Le produit regroupé par EAN prime : c'est le seul signal qu'un suffixe de
    taille ne peut pas tromper. À défaut, on normalise marque et libellé.
    """
    if product_id is not None:
        return f"p:{product_id}"
    label = (name or "").strip()
    if not label:
        return None
    # Deux passes : « Chemise - Size M » puis « Chemise - 42 ».
    for _ in range(2):
        stripped = _VARIANT_NUMBER.sub("", _VARIANT_SUFFIX.sub("", label))
        stripped = stripped.strip(" -–—|,")
        if stripped == label:
            break
        label = stripped
    label = re.sub(r"\s+", " ", label).lower()
    if not label:
        return None
    return f"n:{(brand or '').strip().lower()}|{label}"[:191]


async def rebuild_canonical(session, *, batch: int = 2000, page: int = 5000) -> dict:
    """Recalcule les clés et désigne un représentant par clé : le moins cher.

    Procède en flux, par curseur sur la clé primaire, pour que la mémoire reste
    bornée quelle que soit la taille du catalogue.
    """
    # ── Passe 1 : calcul des clés, et meilleur candidat par clé ──────────────
    best: dict[str, tuple[float, int]] = {}
    keys: list[tuple[int, str | None]] = []
    last_id = 0
    total = 0

    while True:
        rows = (
            await session.execute(
                select(
                    models.Offer.id, models.Offer.product_id, models.Offer.brand,
                    models.Offer.name, models.Offer.price,
                )
                .where(models.Offer.id > last_id)
                .order_by(models.Offer.id)
                .limit(page)
            )
        ).all()
        if not rows:
            break
        total += len(rows)
        for r in rows:
            key = dedup_key(product_id=r.product_id, brand=r.brand, name=r.name)
            keys.append((r.id, key))
            if key is None:
                continue
            # Le moins cher représente le groupe ; à prix égal, le plus ancien.
            price = r.price if r.price is not None else float("inf")
            current = best.get(key)
            if current is None or (price, r.id) < current:
                best[key] = (price, r.id)
        last_id = rows[-1].id

    canonical_ids = {oid for (_, oid) in best.values()}

    # ── Passe 2 : écriture groupée ───────────────────────────────────────────
    written = 0
    for start in range(0, len(keys), batch):
        chunk = keys[start : start + batch]
        await session.execute(
            update(models.Offer),
            [
                {
                    "id": oid,
                    "dedup_key": key,
                    # Une offre sans clé exploitable reste visible : mieux vaut
                    # un doublon qu'un produit qui disparaît du catalogue.
                    "is_canonical": key is None or oid in canonical_ids,
                }
                for (oid, key) in chunk
            ],
        )
        await session.commit()
        written += len(chunk)

    summary = {
        "offers_processed": total,
        "distinct_products": len(best),
        "duplicates_hidden": total - len(canonical_ids) - (total - written),
        "canonical_offers": len(canonical_ids),
    }
    log.info("Déduplication terminée : %s", summary)
    return summary
