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

from collections import Counter, defaultdict
from dataclasses import dataclass

from sqlalchemy import func, select, update

from app.core.logging import get_logger
from app.db import models
from app.services import taxonomy

log = get_logger("coherence")

# Part du catalogue qu'un rayon doit couvrir pour être tenu pour la spécialité
# du marchand. À 70 %, un vendeur mono-rayon est reconnu et un généraliste ne
# l'est jamais — vérifié sur les deux cas limites en test.
DOMINANCE = 0.70

# En dessous, la mesure ne veut rien dire : un marchand de douze articles peut
# être « à 75 % en informatique » avec neuf produits.
MIN_OFFERS = 50

# Un rayon dont la règle se déclenche sur un mot générique n'est pas une
# spécialité : c'est un fourre-tout. « Accessoires » attrape le mot
# « accessoire » lui-même, si bien qu'un vendeur de déshumidificateurs dont les
# libellés disent « accessoire pour… » y tombe à 90 % — mesuré sur Trotec.
#
# Y ramener ses offres minoritaires prendrait les seules qui sont correctement
# classées pour les enterrer dans un rayon qui ne veut rien dire. La dominance
# est réelle ; ce qu'elle mesure ne l'est pas. Ces rayons peuvent rester le
# rayon d'une offre, ils ne peuvent pas devenir une destination.
RAYONS_NON_DESTINATION = frozenset({"Accessoires"})

# Part à partir de laquelle un rayon minoritaire cesse d'être du bruit.
#
# Toute la règle repose sur une hypothèse : la minorité est faite d'erreurs de
# mots-clés. Or une erreur de mot-clé est *dispersée* — chez TISSUS DE REVE,
# les égarées se comptent par unités dans chaque rayon. Une minorité
# *concentrée* dans un seul rayon n'est pas du bruit : c'est une seconde
# activité. YesStyle vend de la beauté à 90 %, et le reste est de la mode
# coréenne — un vrai rayon, pas des faux positifs.
#
# Un rayon secondaire qui tient un vingtième du catalogue est donc protégé :
# ses offres ne bougent pas, seules les dispersées sont ramenées. Le marchand
# reste traité, mais sa seconde activité survit.
#
# Le seuil se mesure aussi par *département*, et c'est indispensable. Mesuré
# sur YesStyle : 90,6 % en beauté, et pas un seul rayon secondaire au-dessus du
# seuil — parce que sa mode coréenne est éclatée entre Mode femme, Mode homme,
# Chaussures, Bijoux et Bagagerie, chacun sous la barre. Prise rayon par rayon,
# une seconde activité bien réelle passait pour du bruit. Prise par
# département, elle se voit : ces rayons sont tous « Mode & Accessoires ».
SECONDAIRE_REEL = 0.05


@dataclass(frozen=True)
class Profil:
    """Ce qu'on sait d'un marchand spécialisé."""

    rayon: str
    part: float
    total: int
    # Rayons secondaires assez fournis pour être une vraie activité, et non des
    # faux positifs. Leurs offres sont laissées où elles sont.
    proteges: frozenset[str]


async def merchant_profiles(session) -> dict[int, Profil]:
    """Rayon dominant de chaque marchand.

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

    profils: dict[int, Profil] = {}
    for merchant_id, repartition in par_marchand.items():
        total = sum(repartition.values())
        if total < MIN_OFFERS:
            continue
        rayon, n = max(repartition.items(), key=lambda kv: kv[1])
        if rayon in RAYONS_NON_DESTINATION:
            continue
        part = n / total
        if part < DOMINANCE:
            continue
        profils[merchant_id] = Profil(rayon, part, total, _proteges(rayon, repartition))
    return profils


def _proteges(dominant: str, repartition: dict[str, int]) -> frozenset[str]:
    """Rayons relevant d'une seconde activité, à ne pas déplacer.

    Deux mesures, parce qu'une seule ne suffit pas : un rayon peut être fourni
    à lui seul, ou n'exister que dispersé entre plusieurs rayons d'un même
    département. Le second cas est celui de YesStyle, et il est invisible rayon
    par rayon.

    Le département du rayon dominant est exclu du calcul : à l'intérieur d'un
    même département, une offre mal placée est précisément l'erreur de mot-clé
    que le réalignement doit corriger.
    """
    total = sum(repartition.values())
    if not total:
        return frozenset()

    proteges = {
        autre
        for autre, combien in repartition.items()
        if autre != dominant and combien / total >= SECONDAIRE_REEL
    }

    dept_dominant = taxonomy.department_of(dominant)
    par_departement: dict[str, int] = defaultdict(int)
    for autre, combien in repartition.items():
        dept = taxonomy.department_of(autre)
        if dept and dept != dept_dominant:
            par_departement[dept] += combien

    for dept, combien in par_departement.items():
        if combien / total >= SECONDAIRE_REEL:
            proteges.update(
                autre
                for autre in repartition
                if taxonomy.department_of(autre) == dept
            )

    return frozenset(proteges)


async def repartition_marchand(session, merchant_id: int) -> dict:
    """Répartition complète d'un marchand, rayon par rayon et département par
    département — pour arbitrer un cas limite sur des chiffres plutôt que sur
    une intuition.
    """
    rows = (
        await session.execute(
            select(models.Offer.filon_category, func.count().label("n"))
            .where(models.Offer.merchant_id == merchant_id)
            .where(models.Offer.filon_category.isnot(None))
            .group_by(models.Offer.filon_category)
        )
    ).all()
    repartition = {c: int(n) for c, n in rows}
    total = sum(repartition.values())
    if not total:
        return {"total": 0, "rayons": [], "departements": []}

    dominant = max(repartition.items(), key=lambda kv: kv[1])[0]
    proteges = _proteges(dominant, repartition)

    par_departement: dict[str, int] = defaultdict(int)
    for rayon, n in repartition.items():
        par_departement[taxonomy.department_of(rayon) or "—"] += n

    return {
        "total": total,
        "dominant": dominant,
        "rayons": [
            {
                "rayon": rayon,
                "offres": n,
                "part_pct": round(n / total * 100, 1),
                "protege": rayon in proteges,
            }
            for rayon, n in sorted(repartition.items(), key=lambda kv: -kv[1])
        ],
        "departements": [
            {"departement": d, "offres": n, "part_pct": round(n / total * 100, 1)}
            for d, n in sorted(par_departement.items(), key=lambda kv: -kv[1])
        ],
    }


async def realign(session, *, batch: int = 2000, dry_run: bool = False) -> dict:
    """Ramène les offres marginales au rayon dominant de leur marchand.

    `dry_run` mesure sans écrire — indispensable pour vérifier l'ampleur avant
    de toucher à 795 000 lignes.
    """
    profils = await merchant_profiles(session)
    if not profils:
        return {"merchants_specialises": 0, "offres_realignees": 0, "dry_run": dry_run}

    realignees = 0
    # Répartition par marchand : sans elle, « 24 369 offres » est un nombre
    # qu'on ne peut ni vérifier ni contester avant d'écrire.
    par_marchand: Counter[int] = Counter()
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
            # Seules les minoritaires *dispersées* bougent. Une offre déjà dans
            # le rayon dominant est à sa place ; une offre non classée relève du
            # classement, pas de la cohérence ; et une offre appartenant à une
            # seconde activité du marchand n'est pas une erreur de mot-clé.
            if not row.filon_category:
                continue
            if row.filon_category == profil.rayon:
                continue
            if row.filon_category in profil.proteges:
                continue
            payload.append(
                {"id": row.id, "filon_category": profil.rayon, "filon_subcategory": None}
            )
            par_marchand[row.merchant_id] += 1

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
    noms = dict(
        (
            await session.execute(
                select(models.Merchant.id, models.Merchant.name).where(
                    models.Merchant.id.in_(par_marchand.keys())
                )
            )
        ).all()
    ) if par_marchand else {}

    return {
        "merchants_specialises": len(profils),
        "offres_realignees": realignees,
        "dry_run": dry_run,
        "detail": [
            {
                "merchant": noms.get(mid, str(mid)),
                "vers": profils[mid].rayon,
                "offres": n,
                "sur": profils[mid].total,
                "rayons_proteges": sorted(profils[mid].proteges),
            }
            for mid, n in par_marchand.most_common()
        ],
    }
