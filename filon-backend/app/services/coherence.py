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

# Ce qui distingue une seconde activité d'une erreur de classement, ce n'est pas
# le volume — c'est le département.
#
# Deux seuils ont été essayés avant celui-ci, et les deux ont échoué sur les
# chiffres réels : ils supposaient qu'une minorité *fournie* signale une
# activité, alors qu'une erreur de mots-clés systématique est fournie elle
# aussi. La quantité ne dit rien. La distance, si.
#
# Un spécialiste étale naturellement son catalogue sur les rayons voisins de son
# département — c'est du rangement, pas une erreur :
#
#   Overhemden vend des chemises homme (94,6 %), et 1 979 cravates et ceintures
#   en « Accessoires ». Kinguin vend des clés de jeu (87,9 %), et 1 238 recharges
#   en « Téléphonie », 840 licences logicielles en « Informatique ». Dans les
#   deux cas le département tient 98 % : une seule activité, plusieurs rayons.
#
# Un bloc tombé dans un *autre* département, en revanche, est la signature même
# de l'erreur de mots-clés :
#
#   YesStyle vend des cosmétiques coréens, et 2 113 offres partent en
#   « Informatique » — un autre département. C'est la pollution du rayon
#   Informatique, pas une activité. Sa mode réelle tient en 103 offres.
#   TISSUS DE REVE voit ses tissus filer en « Mode » parce qu'ils portent le nom
#   du vêtement auquel ils sont destinés.
#
# Le département du rayon dominant est donc protégé en entier, et tout ce qui en
# sort est ramené. Vérifié sur les cinq marchands ci-dessus.
#
# Ce que la règle ne saura jamais trancher reste porté par `realign(exclude=…)` :
# vingt spécialistes se relisent à la main.


@dataclass(frozen=True)
class Profil:
    """Ce qu'on sait d'un marchand spécialisé."""

    rayon: str
    part: float
    total: int

    @property
    def departement(self) -> str | None:
        return taxonomy.department_of(self.rayon)


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
        profils[merchant_id] = Profil(rayon, part, total)
    return profils


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
            }
            for rayon, n in sorted(repartition.items(), key=lambda kv: -kv[1])
        ],
        "departements": [
            {"departement": d, "offres": n, "part_pct": round(n / total * 100, 1)}
            for d, n in sorted(par_departement.items(), key=lambda kv: -kv[1])
        ],
    }


async def realign(
    session,
    *,
    batch: int = 2000,
    dry_run: bool = False,
    exclude: set[str] | None = None,
) -> dict:
    """Ramène les offres marginales au rayon dominant de leur marchand.

    `dry_run` mesure sans écrire — indispensable pour vérifier l'ampleur avant
    de toucher à 795 000 lignes.

    `exclude` met un marchand entièrement de côté, par nom ou par slug. C'est
    la forme que prend la seule décision qu'aucun seuil ne sait prendre : celle
    de savoir si la minorité d'un marchand donné est une seconde activité ou
    une erreur de classement. Vingt spécialistes se relisent à la main.
    """
    profils = await merchant_profiles(session)
    if exclude:
        vises = {e.strip().lower() for e in exclude if e.strip()}
        if vises:
            ecartes = {
                mid
                for mid, nom, slug in (
                    await session.execute(
                        select(models.Merchant.id, models.Merchant.name, models.Merchant.slug)
                    )
                ).all()
                if (nom or "").lower() in vises or (slug or "").lower() in vises
            }
            profils = {mid: p for mid, p in profils.items() if mid not in ecartes}
    if not profils:
        return {
            "merchants_specialises": 0,
            "offres_realignees": 0,
            "dry_run": dry_run,
            "detail": [],
        }

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
            # Une offre non classée relève du classement, pas de la cohérence.
            if not row.filon_category:
                continue
            # Tout le département du rayon dominant est à sa place : les rayons
            # voisins sont le rangement normal d'un spécialiste, pas une erreur.
            # `is not None` compte : deux rayons hors département ne sont pas
            # « du même département », ils sont seulement tous deux non rattachés.
            if (
                profil.departement is not None
                and taxonomy.department_of(row.filon_category) == profil.departement
            ):
                continue
            if row.filon_category == profil.rayon:
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
            }
            for mid, n in par_marchand.most_common()
        ],
    }
