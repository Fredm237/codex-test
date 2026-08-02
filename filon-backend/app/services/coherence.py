"""Cohérence par marchand — le signal le plus fort, et le seul inexploité.

Le classement par mots-clés ne peut pas être juste à cette échelle : les règles
comptent plus de quatre cents tokens courts, et chacun est une porte d'entrée
pour un faux positif. Corriger token par token n'a pas de fin. « Souris » n'en
était qu'un.

Il existe pourtant un signal bien plus fiable que le libellé, et qu'on
n'utilisait pas : **le marchand**. TISSUS DE REVE ne vend que du tissu. Acer ne
vend que de l'informatique. Woodstore24 ne vend que des matériaux. Quand 95 %
du catalogue d'un marchand tombe dans un rayon, une offre isolée classée
ailleurs est presque toujours une erreur de mot-clé — pas une nouveauté.

On calcule donc, pour chaque marchand, la répartition de ses offres par rayon.
Si un rayon domine largement, il devient la référence du marchand, et les
offres marginales y sont ramenées.

Deux garde-fous, sans lesquels la règle ferait plus de mal que de bien :

- Un généraliste n'a pas de rayon dominant. Amazon vend de tout : aucun rayon
  n'atteindra le seuil, et rien ne bouge. Le seuil fait ce tri tout seul.
- Un marchand mono-rayon reste rarement pur à 100 %. Le seuil est donc haut
  mais pas absolu, et seules les offres *minoritaires* sont déplacées — jamais
  celles du rayon dominant lui-même.
"""

from __future__ import annotations

from collections import defaultdict

from sqlalchemy import func, select, update

from app.core.logging import get_logger
from app.db import models

log = get_logger("coherence")

# Part du catalogue qu'un rayon doit couvrir pour être tenu pour la spécialité
# du marchand. À 70 %, un vendeur mono-rayon est reconnu et un généraliste ne
# l'est jamais — vérifié sur les deux cas limites en test.
DOMINANCE = 0.70

# En dessous, la mesure ne veut rien dire : un marchand de douze articles peut
# être « à 75 % en informatique » avec neuf produits.
MIN_OFFERS = 50


async def merchant_profiles(session) -> dict[int, tuple[str, float, int]]:
    """Rayon dominant de chaque marchand : {merchant_id: (rayon, part, total)}.

    Seuls les marchands dont un rayon dépasse le seuil sont rendus.
    """
    rows = (
        await session.execute(
            select(
                models.Offer.merchant_id,
                models.Offer.filon_category,
                func.count().label("n"),
            )
            .where(models.Offer.filon_category.isnot(None))
            .group_by(models.Offer.merchant_id, models.Offer.filon_category)
        )
    ).all()

    par_marchand: dict[int, dict[str, int]] = defaultdict(dict)
    for merchant_id, category, n in rows:
        par_marchand[merchant_id][category] = int(n)

    profils: dict[int, tuple[str, float, int]] = {}
    for merchant_id, repartition in par_marchand.items():
        total = sum(repartition.values())
        if total < MIN_OFFERS:
            continue
        rayon, n = max(repartition.items(), key=lambda kv: kv[1])
        part = n / total
        if part >= DOMINANCE:
            profils[merchant_id] = (rayon, part, total)
    return profils


async def realign(session, *, batch: int = 2000, dry_run: bool = False) -> dict:
    """Ramène les offres marginales au rayon dominant de leur marchand.

    `dry_run` mesure sans écrire — indispensable pour vérifier l'ampleur avant
    de toucher à 795 000 lignes.
    """
    profils = await merchant_profiles(session)
    if not profils:
        return {"merchants_specialises": 0, "offres_realignees": 0, "dry_run": dry_run}

    realignees = 0
    last_id = 0
    while True:
        rows = (
            await session.execute(
                select(
                    models.Offer.id,
                    models.Offer.merchant_id,
                    models.Offer.filon_category,
                )
                .where(models.Offer.id > last_id)
                .order_by(models.Offer.id)
                .limit(batch)
            )
        ).all()
        if not rows:
            break

        payload = []
        for row in rows:
            profil = profils.get(row.merchant_id)
            if not profil:
                continue
            dominant = profil[0]
            # Seules les minoritaires bougent. Une offre déjà dans le rayon
            # dominant, ou pas encore classée, est laissée telle quelle : une
            # offre non classée relève du classement, pas de la cohérence.
            if row.filon_category and row.filon_category != dominant:
                payload.append(
                    {"id": row.id, "filon_category": dominant, "filon_subcategory": None}
                )

        if payload and not dry_run:
            # Forme ORM, pas `__table__.update()` : sur la table Core, `id`
            # serait écrit comme une colonne au lieu de filtrer la ligne, et
            # SQLAlchemy lève une violation d'unicité.
            await session.execute(update(models.Offer), payload)
            await session.commit()
        realignees += len(payload)
        last_id = rows[-1].id

    log.info(
        "Cohérence marchand : %d spécialistes, %d offres réalignées%s",
        len(profils), realignees, " (simulation)" if dry_run else "",
    )
    return {
        "merchants_specialises": len(profils),
        "offres_realignees": realignees,
        "dry_run": dry_run,
    }
