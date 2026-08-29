"""API catalogue — lecture des marchands / offres Awin et déclenchement du sync.

Ces endpoints alimenteront les futures pages catalogue/marchand/produit du site.
Ils dégradent proprement si la base est absente (listes vides).
"""

from __future__ import annotations

import math
import time
from collections import Counter

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Query
from sqlalchemy import (
    Numeric,
    String,
    case,
    cast,
    delete,
    func,
    not_,
    or_,
    select,
    update,
)

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db import models
from app.db import session as db
from app.services import (
    catalog_price_truth,
    catalog_sync,
    decision,
    offer_evidence,
    search,
    taxonomy,
)
from app.services.currency import normalize_currency_code
from app.services.freshness import offer_observation_is_fresh
from app.services.verdict import compute_verdict

log = get_logger("catalog")

router = APIRouter(prefix="/catalog", tags=["catalog"])

# Une rangée en dessous de ce seuil paraît cassée plutôt que sélective.
MIN_RAIL_ITEMS = 4
# Baisse minimale pour figurer dans « les plus grosses baisses » : 5 %.
MIN_DROP_FACTOR = 1.05

# ── Plausibilité des remises ────────────────────────────────────────────────
#
# Un prix de référence tiré du simple `max()` de l'historique n'est pas une
# donnée, c'est une hypothèse. Les feeds marchands contiennent des prix par
# défaut, des erreurs de saisie et des valeurs sentinelles : une offre relevée
# une fois à 250 € puis six fois à 2,79 € produit « −99 % », et le tri par
# remise décroissante place précisément cette aberration en vitrine.
#
# Trois garde-fous, chacun visant une famille d'erreurs observée en production :

# 1. Une remise au-delà de ce seuil est un artefact de feed, pas une promotion.
#    Aucun marchand ne solde durablement à −85 % ; au-delà, on a affaire à un
#    changement de conditionnement (lot → pièce), une erreur de devise, ou un
#    prix sentinelle. Les soldes réelles les plus agressives plafonnent à −80 %.
MAX_PLAUSIBLE_DROP_PCT = 85.0

# 2. Le prix haut doit avoir été observé plusieurs fois. Un pic isolé sur un
#    seul relevé est un accident de collecte : le LEGO à 250 € vu une fois
#    contre six relevés à 2,79 €. Un prix réellement pratiqué laisse plusieurs
#    traces.
MIN_HIGH_OBSERVATIONS = 2

# 3. Le prix haut doit peser dans l'historique. Observé 2 fois sur 40 relevés,
#    il reste une anomalie ; 2 fois sur 5, c'est un prix qui a existé.
MIN_HIGH_SHARE = 0.15

# Marqueurs de genre présents dans les libellés produit. Les flux déclarent une
# catégorie que le marchand choisit lui-même, et certains rangent des robes sous
# « Men's Clothing » : le nom du produit est alors plus fiable que sa catégorie.
_WOMEN_MARKERS = ("women", "woman", "femme", "dames", "girl", "fille", "robe")
_MEN_MARKERS = ("men's", "mens ", " men ", "homme", "heren", "garçon", "boy")

# Ces marqueurs décrivent l'objet vendu, et non le smartphone mentionné pour
# compatibilité. Ils ont été mesurés dans le sous-rayon public Smartphones, où
# 7 955 accessoires manifestes figuraient parmi 15 082 résultats avant le
# rattrapage historique. La garde est volontairement limitée à ce sous-rayon.
_PHONE_ACCESSORY_MARKERS = (
    "coque", "phone cover", "telefoonhoes", "smartphonehoes", "backcover",
    "bookcase", "screen protector", "screenprotector", "tempered glass",
    "verre trempé", "verre trempe", "protege-ecran", "protège-écran",
)


def _smartphone_primary_product_clause():
    """Exclut des Smartphones les accessoires que leur titre/source identifie.

    Il s'agit d'un filet de visibilité temporaire et explicable. La correction
    durable reste le reclassement en ``Coques & Protections`` ; on ne cache
    aucun résultat d'un autre sous-rayon ni une référence ambiguë.
    """
    name = func.lower(func.coalesce(models.Offer.name, ""))
    source_category = func.lower(func.coalesce(models.Offer.category, ""))
    # Une compatibilité smartphone ne décrit pas forcément un mobile. Les
    # onduleurs et capteurs mesurés dans la vitrine publique sont masqués avec
    # les accessoires historiques, en attendant leur reclassement explicite.
    non_phone_markers = _PHONE_ACCESSORY_MARKERS + taxonomy.PHONE_PRIMARY_IMPOSTOR_TERMS
    accessory = or_(*[
        or_(name.contains(marker), source_category.contains(marker))
        for marker in non_phone_markers
    ])
    return not_(accessory)


def _gender_conflict_clause(category: str):
    """Écarte les produits dont le nom contredit la catégorie demandée.

    « women » contient « men » : on teste donc toujours le féminin d'abord.
    """
    low = category.lower()
    asks_women = any(m in low for m in ("women", "woman", "femme", "dames"))
    asks_men = (not asks_women) and any(m in low for m in ("men", "homme", "heren"))

    unwanted = _WOMEN_MARKERS if asks_men else _MEN_MARKERS if asks_women else ()
    if not unwanted:
        return None
    from sqlalchemy import and_, not_

    return and_(*[not_(models.Offer.name.ilike(f"%{m}%")) for m in unwanted])


@router.get("/pulse")
async def pulse(session=Depends(db.get_session)) -> dict:
    """Le battement du catalogue : ce qui a bougé, et quand.

    Un catalogue qui ne dit jamais quand il a été relevé se lit comme un
    fichier figé. Ces trois chiffres — dernier relevé, relevés du jour, baisses
    du jour — sont les seuls qui prouvent que quelque chose tourne. Ils sont
    mesurés, jamais estimés : sans base, on rend `live: false` plutôt que des
    zéros qui feraient croire à un catalogue vide.
    """
    if session is None:
        return {"live": False}

    from datetime import timedelta

    since = catalog_price_truth.utc_naive_now() - timedelta(hours=24)
    last = await session.scalar(select(func.max(models.PriceSnapshot.captured_at)))
    readings = await session.scalar(
        select(func.count())
        .select_from(models.PriceSnapshot)
        .where(models.PriceSnapshot.captured_at >= since)
    )
    # Offres dont le prix a reculé depuis leur relevé le plus ancien des 24 h.
    # Une jointure suffit : on compare le dernier prix connu au plus haut relevé
    # de la période, sans reconstituer tout l'historique.
    drops_stmt = (
        select(func.count(func.distinct(models.PriceSnapshot.offer_id)))
        .select_from(models.PriceSnapshot)
        .join(models.Offer, models.Offer.id == models.PriceSnapshot.offer_id)
        .where(
            models.PriceSnapshot.captured_at >= since,
            models.PriceSnapshot.price > 0,
            models.Offer.price.isnot(None),
            models.Offer.price > 0,
            catalog_price_truth.comparable_price_evidence_sql(
                snapshot_currency=models.PriceSnapshot.currency,
                offer_currency=models.Offer.currency,
                snapshot_in_stock=models.PriceSnapshot.in_stock,
                offer_in_stock=models.Offer.in_stock,
            ),
            models.PriceSnapshot.price > models.Offer.price,
        )
    )
    drops = await session.scalar(drops_stmt)
    sync = await catalog_sync.health(
        session,
        interval_hours=max(1, get_settings().awin_auto_sync_hours or 6),
    )

    return {
        "live": True,
        "last_reading": last.isoformat() if last else None,
        "readings_24h": int(readings or 0),
        "drops_24h": int(drops or 0),
        "drops_comparable": True,
        "sync": sync,
    }


@router.get("/stats")
async def stats(session=Depends(db.get_session)) -> dict:
    if session is None:
        return {"database": False, "merchants": 0, "offers": 0, "snapshots": 0}
    merchants = await session.scalar(select(func.count()).select_from(models.Merchant))
    offers = await session.scalar(select(func.count()).select_from(models.Offer))
    snapshots = await session.scalar(select(func.count()).select_from(models.PriceSnapshot))
    out = {
        "database": True,
        "merchants": int(merchants or 0),
        "offers": int(offers or 0),
        "snapshots": int(snapshots or 0),
    }
    try:
        from app.services import catalog_grouping

        out.update(await catalog_grouping.product_stats(session))
    except Exception:  # pragma: no cover - table absente avant la 1re migration
        pass
    return out


@router.get("/merchants")
async def merchants(
    region: str | None = Query(default=None, description="Filtre pays (BE, FR, …)"),
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
    session=Depends(db.get_session),
) -> dict:
    if session is None:
        return {"total": 0, "items": []}
    stmt = select(models.Merchant).order_by(models.Merchant.name)
    if region:
        stmt = stmt.where(models.Merchant.region == region.upper())
    total = await session.scalar(
        select(func.count()).select_from(stmt.subquery())
    )
    rows = (await session.execute(stmt.limit(limit).offset(offset))).scalars().all()
    return {
        "total": int(total or 0),
        "items": [
            {
                "mid": m.awin_mid,
                "name": m.name,
                "slug": m.slug,
                "domain": m.domain,
                "region": m.region,
                "sector": m.sector,
                "logo": m.logo_url,
            }
            for m in rows
        ],
    }


_SORTS = {
    "relevance": None,
    "price_asc": (models.Offer.price.asc().nullslast(), models.Offer.id.asc()),
    "price_desc": (models.Offer.price.desc().nullslast(), models.Offer.id.asc()),
    "name": (models.Offer.name.asc(),),
}


@router.get("/offers")
async def offers(
    q: str | None = Query(default=None, description="Recherche dans le nom"),
    merchant: str | None = Query(default=None, description="Slug marchand"),
    department: str | None = Query(
        default=None, description="Département FILON (nom ou slug) — filtre tous ses rayons"
    ),
    category: str | None = None,
    subcategory: str | None = None,
    brand: str | None = None,
    price_min: float | None = Query(default=None, ge=0),
    price_max: float | None = Query(default=None, ge=0),
    sort: str = Query(default="relevance", description="relevance|price_asc|price_desc|name"),
    duplicates: bool = Query(default=False, description="Inclure les doublons"),
    limit: int = Query(default=48, le=200),
    offset: int = Query(default=0, ge=0),
    session=Depends(db.get_session),
) -> dict:
    if session is None:
        return {"total": 0, "items": []}
    stmt = select(models.Offer, models.Merchant).join(
        models.Merchant, models.Offer.merchant_id == models.Merchant.id
    )
    blocked = _visible_merchant_clause()
    if blocked is not None:
        stmt = stmt.where(blocked)
    # Une carte sans visuel n'est pas présentable : les rangées l'imposaient
    # déjà, la grille principale les laissait passer.
    stmt = stmt.where(models.Offer.image_url.isnot(None), models.Offer.image_url != "")
    # Un article, une carte. Les déclinaisons de taille et les relistages
    # remplissaient des pages entières du même produit.
    if not duplicates:
        stmt = stmt.where(models.Offer.is_canonical.is_(True))
    if q:
        # Chaque terme cherché séparément : la requête entière en sous-chaîne
        # exigeait que les mots se suivent, et ne renvoyait rien dès deux mots.
        clause = search.search_clause(q)
        if clause is not None:
            stmt = stmt.where(clause)
        primary_filter = search.primary_product_filter(q)
        if primary_filter is not None:
            excluded, minimum_price = primary_filter
            lowered_name = func.lower(models.Offer.name)
            stmt = stmt.where(
                not_(or_(*[lowered_name.contains(term) for term in excluded])),
                models.Offer.price >= minimum_price,
            )
    if merchant:
        stmt = stmt.where(models.Merchant.slug == merchant)
    if department:
        # Un département n'est pas une colonne : c'est un groupe de rayons. Sans
        # ce filtre, choisir « Beauté & Santé » ne restreignait rien du tout et
        # la page affichait le catalogue entier — des pneus compris.
        names = taxonomy.categories_of_department(department)
        if names:
            stmt = stmt.where(models.Offer.filon_category.in_(names))
        else:
            # Département inconnu : on ne renvoie rien plutôt que tout, sans
            # quoi une URL erronée ressemble à un filtre qui ne marche pas.
            stmt = stmt.where(models.Offer.id < 0)
        # Le premier aperçu d'un univers doit aider à choisir, non recycler les
        # accessoires des feeds. Dès que l'utilisateur sélectionne un rayon ou
        # formule une recherche, la navigation redevient exhaustive.
        if not q and not category and not subcategory:
            excluded = search.department_browse_exclusions(department)
            if excluded:
                lowered_name = func.lower(models.Offer.name)
                lowered_category = func.lower(func.coalesce(models.Offer.category, ""))
                stmt = stmt.where(
                    not_(or_(*[
                        or_(lowered_name.contains(term), lowered_category.contains(term))
                        for term in excluded
                    ]))
                )
    resolved_category: str | None = None
    if category:
        # `category` est un contrat public FILON. Un repli silencieux vers la
        # catégorie libre du marchand rendait les filtres imprévisibles, surtout
        # lorsque cette donnée brute était absente. Les noms et slugs FILON sont
        # les seules valeurs acceptées ici.
        wanted = category.strip().casefold()
        resolved_category = next(
            (
                name for name in taxonomy.ALL_CATEGORIES
                if wanted in (name.casefold(), taxonomy.slug_of(name))
            ),
            None,
        )
        if resolved_category:
            stmt = stmt.where(models.Offer.filon_category == resolved_category)
            # Le contrôle était auparavant réservé au repli de catégorie brute.
            # Il doit aussi protéger les vrais rayons FILON Mode homme/femme.
            conflict = _gender_conflict_clause(resolved_category)
            if conflict is not None:
                stmt = stmt.where(conflict)
        else:
            # Une URL invalide doit retourner zéro, jamais déclencher un filtre
            # opaque sur des catégories source hétérogènes.
            stmt = stmt.where(models.Offer.id < 0)
    if subcategory:
        stmt = stmt.where(models.Offer.filon_subcategory == subcategory)
        # Une sous-catégorie est toujours interprétée à l'intérieur du rayon
        # demandé : cela bloque les couples historiques incohérents.
        if resolved_category:
            stmt = stmt.where(models.Offer.filon_category == resolved_category)
        if resolved_category == taxonomy.TELEPHONIE and subcategory == "Smartphones":
            stmt = stmt.where(_smartphone_primary_product_clause())
    if brand:
        stmt = stmt.where(models.Offer.brand.ilike(f"%{brand}%"))
    if price_min is not None:
        stmt = stmt.where(models.Offer.price >= price_min)
    if price_max is not None:
        stmt = stmt.where(models.Offer.price <= price_max)
    total = await session.scalar(select(func.count()).select_from(stmt.subquery()))
    order = _SORTS.get(sort)
    if order:
        stmt = stmt.order_by(*order)
    elif q:
        # « Pertinence » n'avait aucun sens jusqu'ici : l'ordre était celui de
        # la base. Les résultats les plus probables passent devant.
        relevance = search.relevance_order(q)
        if relevance is not None:
            stmt = stmt.order_by(relevance, models.Offer.price.asc().nullslast())
    rows = (await session.execute(stmt.limit(limit).offset(offset))).all()
    evidence_by_offer = await offer_evidence.load_offer_evidence(
        session,
        [offer for offer, _merchant in rows],
        current_only=True,
    )
    items = []
    for offer, merchant_row in rows:
        evidence = _fresh_current_offer_evidence(
            offer,
            evidence_by_offer.get(offer.id),
        )
        observed_at = evidence.current_observed_at if evidence is not None else None
        evidence_current = evidence is not None
        items.append(
            {
                "id": offer.id,
                "name": offer.name,
                "brand": offer.brand,
                # La catégorie publique est FILON. La valeur du marchand reste
                # disponible séparément pour l’audit, sans piloter la navigation.
                "category": offer.filon_category,
                "subcategory": offer.filon_subcategory,
                "source_category": offer.category,
                "offer_kind": offer.offer_kind,
                "price": offer.price if evidence_current else None,
                "currency": evidence.currency if evidence_current else None,
                "in_stock": True if evidence_current else None,
                "observed_at": observed_at.isoformat() if observed_at else None,
                "evidence_current": evidence_current,
                "image": offer.image_url,
                "link": offer.deep_link,
                "merchant": {"name": merchant_row.name, "slug": merchant_row.slug},
            }
        )
    return {
        "total": int(total or 0),
        "items": items,
    }


@router.get("/categories")
async def categories(session=Depends(db.get_session)) -> dict:
    """Rayons FILON et leur volume, pour la navigation."""
    if session is None:
        return {"items": []}
    stmt = (
        select(models.Offer.filon_category, func.count().label("n"))
        .join(models.Merchant, models.Offer.merchant_id == models.Merchant.id)
        .where(
            models.Offer.filon_category.isnot(None),
            models.Offer.image_url.isnot(None),
        )
        .group_by(models.Offer.filon_category)
        .order_by(func.count().desc())
    )
    blocked = _visible_merchant_clause()
    if blocked is not None:
        stmt = stmt.where(blocked)
    rows = (await session.execute(stmt)).all()
    counts = {c: int(n) for (c, n) in rows if c}

    sub_stmt = (
        select(
            models.Offer.filon_category,
            models.Offer.filon_subcategory,
            func.count().label("n"),
        )
        .join(models.Merchant, models.Offer.merchant_id == models.Merchant.id)
        .where(
            models.Offer.filon_subcategory.isnot(None),
            models.Offer.image_url.isnot(None),
        )
        .group_by(models.Offer.filon_category, models.Offer.filon_subcategory)
    )
    if blocked is not None:
        sub_stmt = sub_stmt.where(blocked)
    sub_counts: dict[str, dict[str, int]] = {}
    for (cat, sub, n) in (await session.execute(sub_stmt)).all():
        if cat and sub:
            sub_counts.setdefault(cat, {})[sub] = int(n)
    items = [
        {"name": c, "slug": taxonomy.slug_of(c), "count": n}
        for c, n in counts.items()
    ]

    # Regroupement en départements : un menu à deux niveaux se parcourt, une
    # liste de vingt-six rayons non. Les rayons vides ne sont pas proposés.
    departments = []
    for label, category_names in taxonomy.DEPARTMENTS:
        children = [
            {
                "name": c,
                "slug": taxonomy.slug_of(c),
                "count": counts[c],
                # Sous-rayons dans l'ordre du menu, et seulement ceux qui ont
                # des produits : un menu vers une page vide est pire que rien.
                "subcategories": [
                    {"name": s_, "count": sub_counts.get(c, {})[s_]}
                    for s_ in taxonomy.subcategories_of(c)
                    if sub_counts.get(c, {}).get(s_)
                ],
            }
            for c in category_names
            if counts.get(c)
        ]
        if children:
            departments.append(
                {
                    "name": label,
                    "slug": taxonomy.slug_of(label),
                    "count": sum(c["count"] for c in children),
                    "categories": children,
                }
            )
    return {"items": items, "departments": departments}


# NOTE — `GET /catalog/featured` a été retiré le 04/08/2026.
#
# Il interrogeait `models.Offer.drop_pct`, une colonne qui n'existe pas dans
# `models.py` : l'endpoint répondait donc 500 sur *toutes* les requêtes, en
# production comme ailleurs. Aucune page du front ne l'appelait, ce qui explique
# qu'il soit passé inaperçu.
#
# Un 5xx permanent n'est pas inoffensif : il pollue les logs et rend inutilisable
# toute alerte fondée sur le taux d'erreurs. Les rails de la home sont servis par
# `/catalog/highlights`, qui calcule les baisses depuis `price_snapshots` avec
# contrôle de vraisemblance ; c'est la seule source à utiliser.


@router.get("/admin/unclassified")
async def unclassified(
    limit: int = Query(default=30, le=100),
    x_admin_token: str | None = Header(default=None),
    session=Depends(db.get_session),
) -> dict:
    """Ce que les règles ne reconnaissent pas encore.

    Sert à enrichir la taxonomie à partir des libellés réellement présents dans
    les flux, plutôt qu'au jugé : sans ce diagnostic, on ajoute des motifs au
    hasard et on ne sait pas ce qu'ils rattrapent.
    """
    _require_admin(x_admin_token)
    if session is None:
        raise HTTPException(status_code=503, detail="base de données absente")

    missing = models.Offer.filon_category.is_(None)
    total = await session.scalar(
        select(func.count()).select_from(models.Offer).where(missing)
    )
    cats = (
        await session.execute(
            select(models.Offer.category, func.count().label("n"))
            .where(missing, models.Offer.category.isnot(None))
            .group_by(models.Offer.category)
            .order_by(func.count().desc())
            .limit(limit)
        )
    ).all()
    samples = (
        await session.execute(
            select(models.Offer.name).where(missing).limit(limit)
        )
    ).scalars().all()
    return {
        "unclassified_total": int(total or 0),
        "top_merchant_categories": [
            {"category": c, "count": int(n)} for (c, n) in cats
        ],
        "sample_names": list(samples),
    }


@router.get("/admin/taxonomy-quality")
async def taxonomy_quality(
    limit: int = Query(default=50, ge=1, le=200),
    scan: int = Query(default=2000, ge=1, le=5000),
    x_admin_token: str | None = Header(default=None),
    session=Depends(db.get_session),
) -> dict:
    """Contradictions de taxonomie connues, en lecture seule.

    Le scan est borné et ordonné sur les offres récemment mises à jour : il sert
    de radar de régression après ingestion, pas de remplacement à une campagne
    d'audit SQL complète. Les signaux sont volontairement conservateurs.
    """
    _require_admin(x_admin_token)
    if session is None:
        raise HTTPException(status_code=503, detail="base de données absente")

    rows = (
        await session.execute(
            select(models.Offer, models.Merchant)
            .join(models.Merchant, models.Offer.merchant_id == models.Merchant.id)
            .order_by(models.Offer.updated_at.desc().nullslast(), models.Offer.id.desc())
            .limit(scan)
        )
    ).all()

    counts: Counter[str] = Counter()
    items: list[dict] = []
    for offer, merchant in rows:
        signals = taxonomy.quality_signals(
            offer.filon_category,
            offer.filon_subcategory,
            offer.offer_kind,
            offer.name,
        )
        if not signals:
            continue
        counts.update(signals)
        if len(items) < limit:
            items.append(
                {
                    "id": offer.id,
                    "name": offer.name,
                    "brand": offer.brand,
                    "merchant": merchant.name,
                    "category": offer.filon_category,
                    "subcategory": offer.filon_subcategory,
                    "offer_kind": offer.offer_kind,
                    "signals": signals,
                }
            )

    return {
        "scanned": len(rows),
        "flagged": sum(counts.values()),
        "by_signal": [
            {"signal": signal, "count": count}
            for signal, count in counts.most_common()
        ],
        "items": items,
    }


@router.get("/facets")
async def facets(
    limit: int = Query(default=40, le=200),
    session=Depends(db.get_session),
) -> dict:
    """Catégories et marques les plus fréquentes, pour les menus de filtres."""
    if session is None:
        return {"categories": [], "brands": []}
    # Catégories FILON : un vocabulaire commun aux 154 marchands, là où les
    # libellés bruts produisaient des centaines d'entrées incohérentes.
    cat_stmt = (
        select(models.Offer.filon_category, func.count().label("n"))
        .where(models.Offer.filon_category.isnot(None))
        .group_by(models.Offer.filon_category)
        .order_by(func.count().desc())
        .limit(limit)
    )
    brand_stmt = (
        select(models.Offer.brand, func.count().label("n"))
        .where(models.Offer.brand.isnot(None))
        .group_by(models.Offer.brand)
        .order_by(func.count().desc())
        .limit(limit)
    )
    cats = (await session.execute(cat_stmt)).all()
    brands = (await session.execute(brand_stmt)).all()
    return {
        "categories": [{"value": c, "count": int(n)} for (c, n) in cats if c],
        "brands": [{"value": b, "count": int(n)} for (b, n) in brands if b],
    }


def _visible_merchant_clause():
    """Ce qui n'a rien à faire sur une page publique.

    Deux garde-fous cumulés, parce qu'aucun n'est suffisant seul :

    - les marchands bannis (`BLOCKED_MERCHANTS`), exact et sans faux positif ;
    - les articles marqués adultes à l'ingestion, qui attrapent les références
      érotiques isolées dans le flux d'un marchand par ailleurs généraliste.

    Le second a été ajouté après un refus de partenariat motivé par « Contenu
    pour adultes » : le flag `adultcontent/0` du feed Awin et la liste de
    marchands avaient laissé passer.

    `is_adult IS NULL` reste visible : les lignes antérieures à la migration ne
    doivent pas disparaître du catalogue avant leur requalification.
    """
    from sqlalchemy import and_, or_

    clauses = [
        or_(models.Offer.is_adult.is_(False), models.Offer.is_adult.is_(None))
    ]
    blocked = get_settings().blocked_merchant_slugs
    if blocked:
        clauses.append(models.Merchant.slug.notin_(blocked))
    return and_(*clauses)


def _fresh_current_offer_evidence(
    offer: models.Offer,
    evidence: offer_evidence.OfferEvidence | None,
) -> offer_evidence.OfferEvidence | None:
    """Valide l'unique preuve autorisée à publier le prix d'une offre.

    ``load_offer_evidence(current_only=True)`` rapproche déjà le montant, la
    devise et le stock avec un snapshot append-only. Cette dernière barrière
    protège aussi les appels directs et impose le TTL public commun.
    """

    currency = normalize_currency_code(offer.currency)
    if (
        not isinstance(offer.price, (int, float))
        or isinstance(offer.price, bool)
        or not math.isfinite(float(offer.price))
        or float(offer.price) <= 0
        or offer.in_stock is not True
        or currency is None
        or evidence is None
        or evidence.currency != currency
        or not offer_observation_is_fresh(evidence.current_observed_at)
    ):
        return None
    return evidence


def _card(
    o: models.Offer,
    m: models.Merchant,
    *,
    evidence: offer_evidence.OfferEvidence | None,
    **extra,
) -> dict | None:
    """Charge utile compacte d'une carte produit (rails de la home catalogue)."""
    currency = normalize_currency_code(o.currency)
    evidence = _fresh_current_offer_evidence(o, evidence)
    if evidence is None or currency is None:
        return None
    observed_at = evidence.current_observed_at
    return {
        "id": o.id,
        "name": o.name,
        "brand": o.brand,
        "category": o.category,
        "price": o.price,
        "currency": currency,
        "in_stock": o.in_stock,
        "observed_at": observed_at.isoformat(),
        "evidence_current": True,
        "image": o.image_url,
        "link": o.deep_link,
        "merchant": {"name": m.name, "slug": m.slug},
        **extra,
    }


def _dedup_diversify(core, *, limit: int):
    """Déduplique un rail et le rend divers, en deux passes.

    `core` doit exposer les colonnes id, merchant_id et rail_rank (le rang
    global déjà calculé, croissant = meilleur).

    Les feeds déclinent un même article par taille ou coloris : sans traitement,
    un rail affichait cinq fois la même chemise. On garde donc un exemplaire par
    (marque, nom), puis on entrelace les marchands — meilleur produit de chaque
    boutique d'abord, puis les seconds. Aucune boutique ne monopolise la rangée,
    et le rail reste plein même quand peu de marchands sont éligibles (un simple
    plafond par marchand, lui, laissait des rangées à moitié vides).
    """
    ranked = core.subquery()
    unique = (
        select(
            ranked,
            func.row_number()
            .over(partition_by=ranked.c.dedup_key, order_by=ranked.c.rail_rank)
            .label("rn_name"),
        )
        .subquery()
    )
    kept = select(unique).where(unique.c.rn_name == 1).subquery()
    spread = (
        select(
            kept,
            func.row_number()
            .over(partition_by=kept.c.merchant_id, order_by=kept.c.rail_rank)
            .label("rn_merchant"),
        )
        .subquery()
    )
    return (
        select(spread)
        .order_by(spread.c.rn_merchant, spread.c.rail_rank)
        .limit(limit)
    )


async def _rail(session, core, *, limit: int, extra=()):
    """Exécute un rail dédupliqué puis recharge les objets pour l'affichage."""
    rows = (await session.execute(_dedup_diversify(core, limit=limit))).mappings().all()
    if not rows:
        return []
    ids = [r["id"] for r in rows]
    objects = {
        o.id: (o, m)
        for (o, m) in (
            await session.execute(
                select(models.Offer, models.Merchant)
                .join(models.Merchant, models.Offer.merchant_id == models.Merchant.id)
                .where(models.Offer.id.in_(ids))
            )
        ).all()
    }
    evidence_by_offer = await offer_evidence.load_offer_evidence(
        session,
        [offer for offer, _merchant in objects.values()],
        current_only=True,
    )
    cards = []
    for r in rows:  # l'ordre du rail fait foi
        pair = objects.get(r["id"])
        if pair:
            o, m = pair
            card = _card(
                o,
                m,
                evidence=evidence_by_offer.get(o.id),
                **{k: fn(r) for k, fn in extra},
            )
            if card is not None:
                cards.append(card)
    return cards


@router.get("/highlights")
async def highlights(
    limit: int = Query(default=12, le=24, description="Produits par section"),
    session=Depends(db.get_session),
) -> dict:
    """Sections vivantes de la home catalogue.

    Tout est calculé à partir des données réelles : les baisses et les plus bas
    historiques viennent des `price_snapshots`. Les sections sans données sont
    renvoyées vides — le front les masque plutôt que d'inventer du contenu.
    """
    if session is None:
        return {"sections": []}

    # ── Agrégat d'historique, avec prix de référence validé ────────────────
    #
    # `max()` seul n'est pas un prix de référence : c'est le pire relevé, erreurs
    # de feed incluses. On calcule donc aussi combien de fois ce maximum a été
    # observé et sur combien de relevés, pour pouvoir écarter les pics isolés.
    #
    # `count(*) FILTER (WHERE price = max)` n'est pas exprimable en une passe :
    # on agrège d'abord, puis on rejoint pour compter les occurrences du haut.
    snapshot_currency = catalog_price_truth.normalized_currency_sql(
        models.PriceSnapshot.currency
    )
    agg = (
        select(
            models.PriceSnapshot.offer_id.label("offer_id"),
            snapshot_currency.label("currency"),
            func.max(models.PriceSnapshot.price).label("high"),
            func.min(models.PriceSnapshot.price).label("low"),
            func.count().label("samples"),
        )
        .join(models.Offer, models.Offer.id == models.PriceSnapshot.offer_id)
        .where(
            models.PriceSnapshot.price > 0,
            models.Offer.price.isnot(None),
            models.Offer.price > 0,
            catalog_price_truth.comparable_price_evidence_sql(
                snapshot_currency=models.PriceSnapshot.currency,
                offer_currency=models.Offer.currency,
                snapshot_in_stock=models.PriceSnapshot.in_stock,
                offer_in_stock=models.Offer.in_stock,
            ),
        )
        .group_by(models.PriceSnapshot.offer_id, snapshot_currency)
        .having(func.count() > 1)
        .subquery()
    )

    # Occurrences du prix haut. Comparaison à l'arrondi au centime : deux
    # relevés du « même » prix peuvent différer d'un epsilon en flottant.
    high_hits = (
        select(
            agg.c.offer_id.label("offer_id"),
            func.count().label("high_count"),
        )
        .select_from(
            agg.join(
                models.PriceSnapshot,
                (models.PriceSnapshot.offer_id == agg.c.offer_id)
                & (
                    catalog_price_truth.normalized_currency_sql(
                        models.PriceSnapshot.currency
                    )
                    == agg.c.currency
                )
                & models.PriceSnapshot.in_stock.is_(True)
                & (
                    func.round(cast(models.PriceSnapshot.price, Numeric(12, 2)), 2)
                    == func.round(cast(agg.c.high, Numeric(12, 2)), 2)
                ),
            )
        )
        .group_by(agg.c.offer_id)
        .subquery()
    )

    snap = (
        select(
            agg.c.offer_id.label("offer_id"),
            agg.c.currency.label("currency"),
            agg.c.high.label("high"),
            agg.c.low.label("low"),
            agg.c.samples.label("samples"),
            func.coalesce(high_hits.c.high_count, 1).label("high_count"),
        )
        .select_from(agg.join(high_hits, high_hits.c.offer_id == agg.c.offer_id))
        .subquery()
    )

    # Un prix de référence crédible : observé plusieurs fois, et assez souvent
    # pour ne pas être un accident.
    trusted_high = (
        snap.c.high_count >= MIN_HIGH_OBSERVATIONS,
        snap.c.high_count >= snap.c.samples * MIN_HIGH_SHARE,
    )

    # Clé de déduplication : le produit regroupé par EAN quand il existe, sinon
    # (marque, nom). Le repli sur le nom est fragile — les feeds suffixent les
    # déclinaisons (« … - Size M »), et l'affichage tronque le titre à deux
    # lignes : deux cartes visuellement identiques peuvent porter des noms
    # différents. L'EAN, lui, ne se laisse pas tromper.
    # `concat` ignorant les NULL sous PostgreSQL, on branche explicitement.
    dedup_key = case(
        (
            models.Offer.product_id.isnot(None),
            func.concat("p:", cast(models.Offer.product_id, String)),
        ),
        else_=func.lower(
            func.concat(func.coalesce(models.Offer.brand, ""), " ", models.Offer.name)
        ),
    )

    def core(order_by, *extra_cols):
        """Colonnes communes à tous les rails + rang global."""
        return select(
            models.Offer.id.label("id"),
            models.Offer.merchant_id.label("merchant_id"),
            dedup_key.label("dedup_key"),
            func.row_number().over(order_by=order_by).label("rail_rank"),
            *extra_cols,
        ).join(models.Merchant, models.Offer.merchant_id == models.Merchant.id)

    visible = [
        models.Offer.price.isnot(None),
        models.Offer.price > 0,
        models.Offer.in_stock.is_(True),
        catalog_price_truth.normalized_currency_sql(models.Offer.currency).in_(
            tuple(sorted(catalog_price_truth.SUPPORTED_CURRENCY_CODES))
        ),
        models.Offer.image_url.isnot(None),
        # Les anciennes lignes NULL restent visibles pendant le rattrapage ; dès
        # que leur nature est connue, un séjour/service/numérique sort des rails
        # promotionnels conçus exclusivement pour des biens comparables.
        or_(
            models.Offer.offer_kind.is_(None),
            models.Offer.offer_kind.in_([taxonomy.PHYSICAL_PRODUCT, taxonomy.TECH_ACCESSORY]),
        ),
    ]
    blocked = _visible_merchant_clause()
    if blocked is not None:
        visible.append(blocked)
    visible = tuple(visible)

    # 📉 Les plus grosses baisses de prix (prix actuel < plus haut relevé).
    #
    # Le tri par remise décroissante est un amplificateur d'erreurs : sans
    # plafond, il met en tête les feeds les plus abîmés. On borne donc la remise
    # par le haut *et* on exige un prix de référence observé plusieurs fois.
    drop_pct = ((snap.c.high - models.Offer.price) / snap.c.high * 100.0)
    drops_core = (
        core(drop_pct.desc(), snap.c.high.label("high"), snap.c.low.label("low"),
             drop_pct.label("drop_pct"))
        .join(
            snap,
            (snap.c.offer_id == models.Offer.id)
            & catalog_price_truth.same_supported_currency_sql(
                snap.c.currency, models.Offer.currency
            ),
        )
        # Une baisse d'un pour cent n'est pas une bonne affaire, c'est du bruit :
        # afficher « -1 % » décrédibilise la rangée entière.
        .where(
            *visible,
            *trusted_high,
            snap.c.high > models.Offer.price * MIN_DROP_FACTOR,
            drop_pct <= MAX_PLAUSIBLE_DROP_PCT,
        )
    )
    drops = await _rail(
        session, drops_core, limit=limit,
        extra=(
            ("price_high", lambda r: r["high"]),
            ("price_low", lambda r: r["low"]),
            ("drop_pct", lambda r: round(float(r["drop_pct"]), 1)),
        ),
    )

    # 🏅 Au plus bas historique (et le prix a réellement varié).
    #
    # Trié par profondeur `(high - low) / high`, ce rail renvoyait exactement les
    # mêmes produits que « baisses », dans le même ordre : les deux mesures sont
    # colinéaires quand le prix courant est au plus bas. Deux rangées identiques
    # sur la même page donnent l'impression d'un catalogue vide.
    #
    # La question propre à ce rail est « depuis combien de temps ce prix est-il
    # au plancher ? ». On trie donc par richesse d'historique : un plus-bas
    # confirmé sur trente relevés vaut mieux qu'un plus-bas de deux jours.
    lowest_core = (
        core(
            snap.c.samples.desc(),
            snap.c.high.label("high"),
            snap.c.low.label("low"),
        )
        .join(
            snap,
            (snap.c.offer_id == models.Offer.id)
            & catalog_price_truth.same_supported_currency_sql(
                snap.c.currency, models.Offer.currency
            ),
        )
        .where(
            *visible,
            *trusted_high,
            snap.c.high > snap.c.low,
            models.Offer.price <= snap.c.low,
            # Même exigence de vraisemblance : un « plus bas » adossé à un haut
            # aberrant raconte la même contre-vérité.
            ((snap.c.high - snap.c.low) / snap.c.high * 100.0)
            <= MAX_PLAUSIBLE_DROP_PCT,
        )
    )
    lowest = await _rail(
        session, lowest_core, limit=limit,
        extra=(
            ("price_high", lambda r: r["high"]),
            ("price_low", lambda r: r["low"]),
            ("is_lowest", lambda r: True),
        ),
    )

    # 🆕 Derniers produits entrés au catalogue.
    fresh_core = core(models.Offer.created_at.desc()).where(*visible)
    fresh = await _rail(session, fresh_core, limit=limit)

    # 💶 Moins de 100 € — strictement en euros : 95 £ n'est pas « moins de 100 € ».
    # Dispersion déterministe plutôt qu'un tri par prix : trié par prix, le rail
    # ne montrait que des articles collés au plafond, tous à 100,00 €.
    budget_core = core((models.Offer.id % 997).asc()).where(
        *visible,
        models.Offer.price >= 10,
        models.Offer.price <= 100,
        models.Offer.currency == "EUR",
    )
    budget = await _rail(session, budget_core, limit=limit)

    sections = [
        {"key": "drops", "items": drops},
        {"key": "lowest", "items": lowest},
        {"key": "budget", "items": budget},
        {"key": "fresh", "items": fresh},
    ]
    # Une rangée d'une seule carte fait cassé : mieux vaut ne pas l'afficher
    # tant que les données ne la remplissent pas.
    return {"sections": [s for s in sections if len(s["items"]) >= MIN_RAIL_ITEMS]}


@router.get("/offer/{offer_id}")
async def offer_detail(offer_id: int, session=Depends(db.get_session)) -> dict:
    """Détail d'une offre + son historique de prix (pour la fiche produit)."""
    if session is None:
        raise HTTPException(status_code=503, detail="base de données absente")
    row = (
        await session.execute(
            select(models.Offer, models.Merchant).join(
                models.Merchant, models.Offer.merchant_id == models.Merchant.id
            ).where(models.Offer.id == offer_id)
        )
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="offre introuvable")
    o, m = row
    # Les offres antérieures à la migration sont classées à la lecture jusqu’au
    # rattrapage. Ainsi, un séjour ne peut pas recevoir un verdict produit entre
    # le déploiement du schéma et son reclassement par lots.
    offer_kind = o.offer_kind or taxonomy.classify_offer_kind(o.category, o.name, o.brand)
    evidence = (
        await offer_evidence.load_offer_evidence(session, [o])
    ).get(o.id)
    current_evidence = _fresh_current_offer_evidence(o, evidence)
    current_price = o.price if current_evidence is not None else None
    current_currency = current_evidence.currency if current_evidence is not None else None
    current_stock = True if current_evidence is not None else None
    observed_at = (
        current_evidence.current_observed_at
        if current_evidence is not None
        else None
    )
    hist = list(evidence.history) if evidence is not None else []
    history_currency = evidence.currency if evidence is not None else None
    prices = [price for price, _captured_at in hist]
    grouped = (
        await _grouped_product_summary(session, o.product_id)
        if taxonomy.is_ean_comparable(offer_kind)
        else None
    )
    return {
        "id": o.id,
        "name": o.name,
        "brand": o.brand,
        # Contrat identique à /offers : la navigation consomme la taxonomie
        # FILON, jamais une catégorie marchande éventuellement absente.
        "category": o.filon_category,
        "subcategory": o.filon_subcategory,
        "source_category": o.category,
        "offer_kind": offer_kind,
        "ean": o.ean,
        "price": current_price,
        "currency": current_currency,
        "in_stock": current_stock,
        "observed_at": observed_at.isoformat() if observed_at else None,
        "evidence_current": current_evidence is not None,
        "image": o.image_url,
        "link": o.deep_link,
        "merchant": {"name": m.name, "slug": m.slug, "domain": m.domain, "region": m.region},
        "history": [
            {
                "price": price,
                "currency": history_currency,
                "at": captured_at.isoformat(),
                "in_stock": True,
            }
            for price, captured_at in hist
        ],
        "price_min": min(prices) if prices else None,
        "price_max": max(prices) if prices else None,
        # Le produit regroupé, s'il est vendu ailleurs : c'est ce qui permet à la
        # fiche d'une offre de renvoyer vers la comparaison multi-marchands.
        "product": grouped,
        "verdict": (
            compute_verdict(
                price=current_price,
                currency=current_currency,
                history=hist,
                cheapest_elsewhere=grouped["price_min"] if grouped else None,
                comparison_currency=grouped["currency"] if grouped else None,
                history_currency=history_currency,
                merchants_count=grouped["merchants_count"] if grouped else 1,
                in_stock=current_stock,
            )
            if taxonomy.is_ean_comparable(offer_kind)
            else None
        ),
        "decision": decision.compute_decision(
            price=current_price,
            currency=current_currency,
            history=hist,
            cheapest_elsewhere=grouped["price_min"] if grouped else None,
            comparison_currency=grouped["currency"] if grouped else None,
            history_currency=history_currency,
            merchants_count=grouped["merchants_count"] if grouped else 1,
            offers_count=grouped["offers_count"] if grouped else 1,
            in_stock=current_stock,
            updated_at=observed_at,
            offer_kind=offer_kind,
        ),
    }


async def _current_product_price_scopes(
    session,
    product_ids: list[int],
) -> dict[int, dict]:
    """Prix courants comparables, groupés sans jamais traverser une devise."""

    if not product_ids:
        return {}
    offers = (
        await session.execute(
            select(models.Offer).where(models.Offer.product_id.in_(product_ids))
        )
    ).scalars().all()
    evidence_by_offer = await offer_evidence.load_offer_evidence(
        session,
        list(offers),
        current_only=True,
    )
    grouped: dict[int, list[tuple[models.Offer, offer_evidence.OfferEvidence]]] = {}
    for offer in offers:
        evidence = _fresh_current_offer_evidence(
            offer,
            evidence_by_offer.get(offer.id),
        )
        if evidence is None or offer.product_id is None:
            continue
        grouped.setdefault(offer.product_id, []).append((offer, evidence))

    scopes: dict[int, dict] = {}
    for product_id in product_ids:
        current = grouped.get(product_id, [])
        currencies = {evidence.currency for _offer, evidence in current}
        if len(currencies) != 1:
            scopes[product_id] = {
                "price_min": None,
                "price_max": None,
                "currency": None,
                "offers_count": 0,
                "merchants_count": 0,
            }
            continue
        prices = [float(offer.price) for offer, _evidence in current]
        scopes[product_id] = {
            "price_min": min(prices),
            "price_max": max(prices),
            "currency": next(iter(currencies)),
            "offers_count": len(current),
            "merchants_count": len({offer.merchant_id for offer, _evidence in current}),
        }
    return scopes


async def _grouped_product_summary(session, product_id: int | None) -> dict | None:
    """Résumé du produit regroupé — uniquement s'il apporte quelque chose.

    Renvoie None quand le produit n'a qu'un seul marchand : annoncer
    « disponible chez 1 marchand » n'aide personne.
    """
    if product_id is None:
        return None
    p = (
        await session.execute(
            select(models.CatalogProduct).where(models.CatalogProduct.id == product_id)
        )
    ).scalar_one_or_none()
    if p is None or (p.merchants_count or 0) < 2:
        return None
    scope = (await _current_product_price_scopes(session, [p.id])).get(p.id)
    if scope is None or scope["merchants_count"] < 2:
        return None
    return {
        "ean": p.ean,
        **scope,
    }


@router.get("/products")
async def products(
    q: str | None = Query(default=None, description="Recherche dans le nom"),
    brand: str | None = None,
    multi_merchant: bool = Query(default=False, description="Vendus par 2+ marchands"),
    limit: int = Query(default=48, le=200),
    offset: int = Query(default=0, ge=0),
    session=Depends(db.get_session),
) -> dict:
    """Produits regroupés par EAN — l'unité réelle, pas la ligne de feed."""
    if session is None:
        return {"total": 0, "items": []}
    stmt = select(models.CatalogProduct)
    if q:
        stmt = stmt.where(models.CatalogProduct.name.ilike(f"%{q}%"))
    if brand:
        stmt = stmt.where(models.CatalogProduct.brand.ilike(f"%{brand}%"))
    if multi_merchant:
        stmt = stmt.where(models.CatalogProduct.merchants_count > 1)
    total = await session.scalar(select(func.count()).select_from(stmt.subquery()))
    stmt = stmt.order_by(
        models.CatalogProduct.merchants_count.desc(), models.CatalogProduct.id.asc()
    )
    rows = (await session.execute(stmt.limit(limit).offset(offset))).scalars().all()
    scopes = await _current_product_price_scopes(
        session,
        [product.id for product in rows],
    )
    return {
        "total": int(total or 0),
        "items": [
            {
                "ean": p.ean,
                "name": p.name,
                "brand": p.brand,
                "category": p.category,
                "image": p.image_url,
                "price_min": scopes.get(p.id, {}).get("price_min"),
                "price_max": scopes.get(p.id, {}).get("price_max"),
                "currency": scopes.get(p.id, {}).get("currency"),
                "offers_count": p.offers_count,
                "merchants_count": p.merchants_count,
                "compared_offers_count": scopes.get(p.id, {}).get("offers_count", 0),
                "compared_merchants_count": scopes.get(p.id, {}).get("merchants_count", 0),
            }
            for p in rows
        ],
    }


@router.get("/sitemap/products")
async def sitemap_products(
    limit: int = Query(default=5000, le=50000),
    offset: int = Query(default=0, ge=0),
    min_merchants: int = Query(default=2, ge=1, description="Marchands minimum"),
    session=Depends(db.get_session),
) -> dict:
    """EAN et date de mise à jour, pour la génération du sitemap.

    Charge utile volontairement minimale : un sitemap n'a besoin de rien d'autre,
    et il s'agit de parcourir des dizaines de milliers de lignes.

    `min_merchants=2` par défaut : une fiche regroupée n'apporte de contenu
    propre qu'à partir de deux marchands. En dessous, elle redirait ce que dit
    déjà la fiche de l'offre — soumettre ces pages à l'indexation reviendrait à
    proposer des milliers de pages sans valeur ajoutée.
    """
    if session is None:
        return {"total": 0, "items": []}
    stmt = select(models.CatalogProduct).where(
        models.CatalogProduct.merchants_count >= min_merchants
    )
    total = await session.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = (
        await session.execute(
            select(models.CatalogProduct.ean, models.CatalogProduct.updated_at)
            .where(models.CatalogProduct.merchants_count >= min_merchants)
            .order_by(models.CatalogProduct.id)
            .limit(limit)
            .offset(offset)
        )
    ).all()
    return {
        "total": int(total or 0),
        "items": [
            {"ean": ean, "updated": updated.isoformat() if updated else None}
            for (ean, updated) in rows
        ],
    }


@router.get("/product/{ean}")
async def product_detail(ean: str, session=Depends(db.get_session)) -> dict:
    """Fiche d'un produit regroupé : toutes les offres, du moins cher au plus cher."""
    if session is None:
        raise HTTPException(status_code=503, detail="base de données absente")
    product = (
        await session.execute(
            select(models.CatalogProduct).where(models.CatalogProduct.ean == ean)
        )
    ).scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail="produit introuvable")

    rows = (
        await session.execute(
            select(models.Offer, models.Merchant)
            .join(models.Merchant, models.Offer.merchant_id == models.Merchant.id)
            .where(models.Offer.product_id == product.id)
            .order_by(models.Offer.price.asc().nullslast())
        )
    ).all()
    evidence_by_offer = await offer_evidence.load_offer_evidence(
        session,
        [offer for offer, _merchant in rows],
        current_only=True,
    )
    current_rows = []
    for offer, merchant in rows:
        evidence = _fresh_current_offer_evidence(
            offer,
            evidence_by_offer.get(offer.id),
        )
        if evidence is not None:
            current_rows.append((offer, merchant, evidence))
    currencies = {evidence.currency for _offer, _merchant, evidence in current_rows}
    comparison_currency = next(iter(currencies)) if len(currencies) == 1 else None
    comparable_rows = (
        sorted(current_rows, key=lambda row: (float(row[0].price), row[0].id))
        if comparison_currency is not None
        else []
    )
    best_offer = comparable_rows[0][0] if comparable_rows else None
    best_evidence = None
    if best_offer is not None:
        best_evidence = (
            await offer_evidence.load_offer_evidence(session, [best_offer])
        ).get(best_offer.id)
    best_history = list(best_evidence.history) if best_evidence is not None else []
    history_currency = best_evidence.currency if best_evidence is not None else None
    verified_by_id = {
        offer.id: evidence for offer, _merchant, evidence in current_rows
    }
    compared_merchants = len({offer.merchant_id for offer, _merchant, _evidence in comparable_rows})
    compared_offers = len(comparable_rows)
    compared_prices = [float(offer.price) for offer, _merchant, _evidence in comparable_rows]
    ordered_rows = (
        [(offer, merchant) for offer, merchant, _evidence in comparable_rows]
        + sorted(
            [(offer, merchant) for offer, merchant in rows if offer.id not in verified_by_id],
            key=lambda row: row[0].id,
        )
        + (
            sorted(
                [(offer, merchant) for offer, merchant, _evidence in current_rows],
                key=lambda row: row[0].id,
            )
            if comparison_currency is None
            else []
        )
    )

    return {
        "ean": product.ean,
        "name": product.name,
        "brand": product.brand,
        "category": product.category,
        "image": product.image_url,
        "price_min": min(compared_prices) if compared_prices else None,
        "price_max": max(compared_prices) if compared_prices else None,
        "currency": comparison_currency,
        "offers_count": product.offers_count,
        "merchants_count": product.merchants_count,
        "offers": [
            {
                "id": o.id,
                "price": o.price if o.id in verified_by_id else None,
                "currency": verified_by_id[o.id].currency if o.id in verified_by_id else None,
                "in_stock": True if o.id in verified_by_id else None,
                "observed_at": (
                    verified_by_id[o.id].current_observed_at.isoformat()
                    if o.id in verified_by_id
                    else None
                ),
                "evidence_current": o.id in verified_by_id,
                "link": o.deep_link,
                "merchant": {"name": m.name, "slug": m.slug, "region": m.region},
            }
            for (o, m) in ordered_rows
        ],
        # Verdict porté par le meilleur prix du produit : c'est celui que
        # l'utilisateur retiendra, et l'écart entre marchands le nourrit sans
        # dépendre de l'historique.
        "verdict": compute_verdict(
            price=best_offer.price if best_offer is not None else None,
            currency=comparison_currency,
            history=best_history,
            cheapest_elsewhere=None,
            comparison_currency=comparison_currency,
            history_currency=history_currency,
            merchants_count=compared_merchants or 1,
            in_stock=True if best_offer is not None else None,
        ),
        "decision": decision.compute_decision(
            price=best_offer.price if best_offer is not None else None,
            currency=comparison_currency,
            history=best_history,
            cheapest_elsewhere=min(compared_prices) if compared_prices else None,
            comparison_currency=comparison_currency,
            history_currency=history_currency,
            merchants_count=compared_merchants or 1,
            offers_count=compared_offers or 1,
            in_stock=True if best_offer is not None else None,
            updated_at=(
                best_evidence.current_observed_at
                if best_evidence is not None
                else None
            ),
        ),
    }


def _require_admin(x_admin_token: str | None) -> None:
    s = get_settings()
    if not s.admin_sync_token or x_admin_token != s.admin_sync_token:
        raise HTTPException(status_code=403, detail="admin token requis")


async def _run_rebuild_products() -> None:
    """Reconstruction des produits en tâche de fond (session dédiée).

    Le verrou vit dans le service, pas ici : le cron appelle rebuild_products
    directement et doit être couvert par la même garde.
    """
    from app.services import catalog_grouping

    async with db.session_scope() as session:
        if session is None:
            log.warning("Regroupement EAN : base absente")
            return
        try:
            summary = await catalog_grouping.rebuild_products(session)
            log.info("Regroupement EAN terminé : %s", summary)
        except Exception as exc:  # pragma: no cover - dépend des données réelles
            log.warning("Regroupement EAN échoué : %s", exc)


@router.post("/admin/rebuild-products")
async def rebuild_products_endpoint(
    background: BackgroundTasks,
    wait: bool = Query(default=False, description="Attendre la fin et renvoyer le bilan"),
    x_admin_token: str | None = Header(default=None),
    session=Depends(db.get_session),
) -> dict:
    """Regroupe les offres en produits, par EAN (protégé par ADMIN_SYNC_TOKEN).

    `wait=true` renvoie le bilan chiffré — dont le taux d'EAN exploitables, qui
    détermine ce qu'on pourra bâtir dessus. Sinon la reconstruction part en
    arrière-plan et l'avancée se suit via /api/catalog/products.
    """
    _require_admin(x_admin_token)
    if session is None:
        raise HTTPException(status_code=503, detail="base de données absente")
    from app.services import catalog_grouping

    if catalog_grouping.is_rebuilding():
        raise HTTPException(
            status_code=409,
            detail="un regroupement est déjà en cours — suivre /api/catalog/stats",
        )
    if wait:
        return await catalog_grouping.rebuild_products(session)
    background.add_task(_run_rebuild_products)
    return {"started": True, "note": "suivre /api/catalog/stats"}


@router.post("/admin/reclassify")
async def reclassify_offers(
    batch: int = Query(default=2000, le=10000),
    after_id: int = Query(default=0, ge=0),
    max_offers: int = Query(default=0, ge=0),
    max_seconds: float = Query(default=120.0, gt=0, le=600),
    filon_category: str | None = Query(
        default=None, max_length=64,
        description="Limiter le rattrapage à un rayon FILON existant.",
    ),
    only_unclassified: bool = Query(
        default=False,
        description="Ne parcourir que les offres encore sans rayon FILON.",
    ),
    merchant_category: str | None = Query(
        default=None, max_length=255,
        description="Limiter le rattrapage à une catégorie déclarée par le marchand.",
    ),
    merchant_id: int | None = Query(
        default=None, gt=0,
        description="Limiter le rattrapage à un marchand précis.",
    ),
    offer_ids: str | None = Query(
        default=None, max_length=25_000,
        description="Liste CSV d’identifiants d’offres à reclasser explicitement (5 000 maximum).",
    ),
    x_admin_token: str | None = Header(default=None),
) -> dict:
    """Recalcule la catégorie FILON des offres déjà en base.

    Le classement se fait à l'ingestion ; les offres antérieures doivent être
    rattrapées. Procède en flux, par curseur sur la clé primaire, pour que la
    mémoire reste bornée quelle que soit la taille du catalogue.

    Reprenable et borné par construction. Traiter le million d'offres en une
    seule requête a fait tomber la production : le proxy coupe la connexion bien
    avant la fin, et surtout le volume d'écritures accumulé a saturé le disque
    de la base (`No space left on device` sur `pg_wal`). Trois garde-fous en
    découlent :

    - `max_seconds` arrête la passe avant que la requête n'expire ;
    - `max_offers` plafonne le nombre d'offres touchées par appel ;
    - `after_id` reprend là où la passe précédente s'est arrêtée.

    `filon_category` limite optionnellement la passe aux offres actuellement
    rangées dans un rayon précis. `only_unclassified` traite au contraire les
    lignes encore sans rayon ; `merchant_category` cible une famille brute du
    flux (par exemple « Appartement de vacances ») et `merchant_id` une source
    précise. `offer_ids` accepte enfin une liste CSV bornée d’offres nommément
    auditées. Ces filtres permettent un rattrapage sûr sans réécrire les
    catégories déjà vérifiées.

    La réponse renvoie `next_after_id` et `done` : l'appelant boucle jusqu'à
    `done`, ce qui laisse Postgres recycler son journal entre deux passes.
    Chaque lot est validé séparément, donc une interruption ne perd que le lot
    en cours.
    """
    _require_admin(x_admin_token)
    # En appel HTTP, FastAPI résout Query en booléen. En appel direct de test ou
    # d’outil interne, la valeur par défaut reste un objet Query : il ne doit pas
    # activer accidentellement le filtre des offres non classées.
    only_unclassified = only_unclassified is True
    merchant_category = merchant_category if isinstance(merchant_category, str) else None
    merchant_id = merchant_id if isinstance(merchant_id, int) and not isinstance(merchant_id, bool) else None
    offer_ids = offer_ids if isinstance(offer_ids, str) else None
    target_offer_ids: list[int] | None = None
    if offer_ids:
        try:
            target_offer_ids = sorted({int(value.strip()) for value in offer_ids.split(",") if value.strip()})
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="offer_ids doit être une liste CSV d’entiers positifs") from exc
        if not target_offer_ids or any(value <= 0 for value in target_offer_ids):
            raise HTTPException(status_code=422, detail="offer_ids doit contenir au moins un entier positif")
        if len(target_offer_ids) > 5_000:
            raise HTTPException(status_code=422, detail="offer_ids est limité à 5 000 offres")
    if not db.is_enabled():
        raise HTTPException(status_code=503, detail="base de données absente")

    started = time.monotonic()
    updated = 0
    classified = 0
    kind_counts: dict[str, int] = {}
    last_id = after_id
    done = False
    async with db.session_scope() as session:
        if session is None:
            raise HTTPException(status_code=503, detail="base de données absente")
        while True:
            remaining = batch
            if max_offers:
                remaining = min(remaining, max_offers - updated)
                if remaining <= 0:
                    break
            stmt = select(
                models.Offer.id, models.Offer.category,
                models.Offer.name, models.Offer.brand,
                models.Merchant.name.label("merchant_name"),
            ).join(
                models.Merchant, models.Merchant.id == models.Offer.merchant_id
            ).where(models.Offer.id > last_id)
            if filon_category:
                stmt = stmt.where(models.Offer.filon_category == filon_category)
            if only_unclassified:
                stmt = stmt.where(models.Offer.filon_category.is_(None))
            if merchant_category:
                stmt = stmt.where(models.Offer.category == merchant_category)
            if merchant_id:
                stmt = stmt.where(models.Offer.merchant_id == merchant_id)
            if target_offer_ids:
                stmt = stmt.where(models.Offer.id.in_(target_offer_ids))
            rows = (
                await session.execute(
                    stmt.order_by(models.Offer.id).limit(remaining)
                )
            ).all()
            if not rows:
                done = True
                break
            payload = []
            for r in rows:
                kind = taxonomy.classify_offer_kind(
                    r.category, r.name, r.brand, r.merchant_name
                )
                value = taxonomy.classify(
                    r.category, r.name, r.brand, r.merchant_name
                )
                payload.append({
                    "id": r.id,
                    "filon_category": value,
                    "filon_subcategory": taxonomy.classify_subcategory(
                        value, r.name, r.category, r.merchant_name
                    ),
                    "offer_kind": kind,
                })
                kind_counts[kind] = kind_counts.get(kind, 0) + 1
                if value:
                    classified += 1
            await session.execute(update(models.Offer), payload)
            await session.commit()
            updated += len(payload)
            last_id = rows[-1].id
            if time.monotonic() - started >= max_seconds:
                break

    return {
        "offers_processed": updated,
        "offers_classified": classified,
        "coverage_pct": round(classified / updated * 100, 1) if updated else 0.0,
        "next_after_id": last_id,
        "done": done,
        "elapsed_seconds": round(time.monotonic() - started, 1),
        "filon_category": filon_category,
        "only_unclassified": only_unclassified,
        "merchant_category": merchant_category,
        "merchant_id": merchant_id,
        "offer_ids_count": len(target_offer_ids) if target_offer_ids else 0,
        "offer_kinds": kind_counts,
    }


@router.post("/admin/flag-adult")
async def flag_adult_offers(
    batch: int = Query(default=2000, le=10000),
    x_admin_token: str | None = Header(default=None),
) -> dict:
    """Requalifie le rayon adulte des offres déjà en base.

    Le drapeau est posé à l'ingestion ; les 795 000 offres antérieures ne l'ont
    pas et restent visibles tant qu'elles n'ont pas été relues (voir
    `_visible_merchant_clause`). Ce rattrapage les parcourt en flux, par curseur
    sur la clé primaire, pour que la mémoire reste bornée.

    Idempotent : relancer ne fait que réécrire les mêmes valeurs.
    """
    _require_admin(x_admin_token)
    if not db.is_enabled():
        raise HTTPException(status_code=503, detail="base de données absente")

    from app.services import safety

    processed = 0
    flagged = 0
    async with db.session_scope() as session:
        if session is None:
            raise HTTPException(status_code=503, detail="base de données absente")
        last_id = 0
        while True:
            rows = (
                await session.execute(
                    select(
                        models.Offer.id, models.Offer.name,
                        models.Offer.category, models.Offer.brand,
                    )
                    .where(models.Offer.id > last_id)
                    .order_by(models.Offer.id)
                    .limit(batch)
                )
            ).all()
            if not rows:
                break
            payload = []
            for r in rows:
                value = safety.is_adult(name=r.name, category=r.category, brand=r.brand)
                payload.append({"id": r.id, "is_adult": value})
                if value:
                    flagged += 1
            await session.execute(update(models.Offer), payload)
            await session.commit()
            processed += len(payload)
            last_id = rows[-1].id

    return {
        "offers_processed": processed,
        "offers_flagged_adult": flagged,
        "flagged_pct": round(flagged / processed * 100, 3) if processed else 0.0,
    }


@router.get("/admin/merchant-profiles")
async def merchant_profiles_endpoint(
    x_admin_token: str | None = Header(default=None),
) -> dict:
    """Rayon dominant de chaque marchand — à lire avant tout réalignement."""
    _require_admin(x_admin_token)
    if not db.is_enabled():
        raise HTTPException(status_code=503, detail="base de données absente")

    from app.services import coherence

    async with db.session_scope() as session:
        if session is None:
            raise HTTPException(status_code=503, detail="base de données absente")
        profils = await coherence.merchant_profiles(session)
        noms = dict(
            (await session.execute(select(models.Merchant.id, models.Merchant.name))).all()
        )

    items = [
        {
            "merchant": noms.get(mid, str(mid)),
            "rayon": p.rayon,
            "part_pct": round(p.part * 100, 1),
            "offres": p.total,
        }
        for mid, p in profils.items()
    ]
    items.sort(key=lambda x: x["offres"], reverse=True)
    return {"specialistes": len(items), "items": items}


@router.get("/admin/merchant-breakdown")
async def merchant_breakdown_endpoint(
    merchant: str = Query(description="Nom ou slug du marchand"),
    x_admin_token: str | None = Header(default=None),
) -> dict:
    """Répartition complète d'un marchand, rayon par rayon et par département.

    Un cas limite du réalignement — un marchand dont la seconde activité est
    éclatée entre plusieurs rayons — ne se tranche pas sur une intuition. Ceci
    donne les chiffres qui permettent de le trancher.
    """
    _require_admin(x_admin_token)
    if not db.is_enabled():
        raise HTTPException(status_code=503, detail="base de données absente")

    from app.services import coherence

    async with db.session_scope() as session:
        if session is None:
            raise HTTPException(status_code=503, detail="base de données absente")
        row = (
            await session.execute(
                select(models.Merchant.id, models.Merchant.name).where(
                    or_(
                        models.Merchant.name.ilike(f"%{merchant}%"),
                        models.Merchant.slug == merchant,
                    )
                ).limit(1)
            )
        ).first()
        if row is None:
            raise HTTPException(status_code=404, detail=f"marchand introuvable : {merchant}")
        detail = await coherence.repartition_marchand(session, row.id)

    return {"merchant": row.name, **detail}


@router.post("/admin/realign")
async def realign_endpoint(
    dry_run: bool = Query(
        default=True,
        description="Simulation par défaut : mesurer avant d'écrire sur 795 000 lignes",
    ),
    exclude: str | None = Query(
        default=None,
        description="Marchands à laisser intacts, séparés par des virgules (nom ou slug)",
    ),
    batch: int = Query(default=2000, le=10000),
    x_admin_token: str | None = Header(default=None),
) -> dict:
    """Ramène les offres marginales au rayon dominant de leur marchand.

    Simulation par défaut, à dessein. Cette opération peut déplacer des dizaines
    de milliers d'offres : on mesure l'ampleur avant de la subir. Passer
    `dry_run=false` pour écrire.
    """
    _require_admin(x_admin_token)
    if not db.is_enabled():
        raise HTTPException(status_code=503, detail="base de données absente")

    from app.services import coherence

    async with db.session_scope() as session:
        if session is None:
            raise HTTPException(status_code=503, detail="base de données absente")
        return await coherence.realign(
            session,
            batch=batch,
            dry_run=dry_run,
            exclude=set(exclude.split(",")) if exclude else None,
        )


@router.post("/admin/rebuild-canonical")
async def rebuild_canonical_endpoint(
    x_admin_token: str | None = Header(default=None),
) -> dict:
    """Recalcule les clés de doublon et désigne un représentant par article.

    À relancer après un regroupement par EAN : c'est lui qui fournit le signal
    le plus fiable, qu'un suffixe de taille ne peut pas tromper.
    """
    _require_admin(x_admin_token)
    if not db.is_enabled():
        raise HTTPException(status_code=503, detail="base de données absente")
    from app.services import dedup

    async with db.session_scope() as session:
        if session is None:
            raise HTTPException(status_code=503, detail="base de données absente")
        return await dedup.rebuild_canonical(session)


@router.post("/admin/purge-offers")
async def purge_offers(
    merchant: str | None = Query(default=None, description="Slug marchand"),
    brand: str | None = Query(default=None, description="Marque (correspondance partielle)"),
    q: str | None = Query(default=None, description="Texte dans le nom du produit"),
    confirm: bool = Query(default=False, description="Doit valoir true pour exécuter"),
    dry_run: bool = Query(default=True, description="Ne compte que, sans supprimer"),
    x_admin_token: str | None = Header(default=None),
    session=Depends(db.get_session),
) -> dict:
    """Supprime des offres (et leurs relevés), par marchand, marque ou mot-clé.

    Sert à retirer ce qu'un feed n'aurait jamais dû apporter — le contenu adulte
    notamment : couper le flag à l'ingestion empêche les prochains imports, mais
    ne retire pas les lignes déjà en base, qui continuent d'être indexées.

    `dry_run=true` par défaut : on compte d'abord, on supprime ensuite.
    """
    _require_admin(x_admin_token)
    if session is None:
        raise HTTPException(status_code=503, detail="base de données absente")
    if not (merchant or brand or q):
        raise HTTPException(status_code=400, detail="préciser merchant, brand ou q")

    stmt = select(models.Offer.id)
    if merchant:
        stmt = stmt.where(
            models.Offer.merchant_id.in_(
                select(models.Merchant.id).where(models.Merchant.slug == merchant)
            )
        )
    if brand:
        stmt = stmt.where(models.Offer.brand.ilike(f"%{brand}%"))
    if q:
        stmt = stmt.where(models.Offer.name.ilike(f"%{q}%"))

    ids = [i for (i,) in (await session.execute(stmt)).all()]
    if dry_run or not confirm:
        return {
            "matched_offers": len(ids),
            "deleted": False,
            "note": "ajouter ?confirm=true&dry_run=false pour supprimer",
        }

    # Les relevés d'abord : ils référencent les offres.
    await session.execute(
        delete(models.PriceSnapshot).where(models.PriceSnapshot.offer_id.in_(ids))
    )
    await session.execute(delete(models.Offer).where(models.Offer.id.in_(ids)))
    await session.commit()
    log.warning("Offres purgées : %s (merchant=%s brand=%s q=%s)", len(ids), merchant, brand, q)
    return {"matched_offers": len(ids), "deleted": True}


@router.post("/sync/merchants")
async def sync_merchants_endpoint(
    x_admin_token: str | None = Header(default=None),
    session=Depends(db.get_session),
) -> dict:
    """Déclenche la synchro des marchands (protégé par ADMIN_SYNC_TOKEN)."""
    _require_admin(x_admin_token)
    if session is None:
        raise HTTPException(status_code=503, detail="base de données absente")
    from app.services import awin_catalog

    count = await awin_catalog.sync_merchants(session)
    return {"synced_merchants": count}


async def _run_feed_ingest(limit: int | None) -> None:
    """Synchronisation complète en arrière-plan, journalisée comme le cron."""
    async with db.session_scope() as session:
        if session is None:
            log.warning("Ingestion feeds : base absente")
            return
        try:
            summary = await catalog_sync.run_catalog_sync(
                session,
                trigger="manual",
                limit_override=limit,
            )
            log.info("Ingestion feeds terminée : %s", summary)
        except Exception as exc:  # pragma: no cover - réseau/compte
            log.warning("Ingestion feeds échouée (%s)", type(exc).__name__)


@router.get("/debug/feeds")
async def debug_feeds(
    x_admin_token: str | None = Header(default=None),
    session=Depends(db.get_session),
) -> dict:
    """Diagnostic : montre la réponse brute d'Awin (liste des feeds) pour caler
    le parseur sur le format réel. Protégé par ADMIN_SYNC_TOKEN. Masque la clé.
    """
    _require_admin(x_admin_token)
    import httpx

    from app.services import awin_catalog

    s = get_settings()
    out: dict = {
        "feed_key_present": bool(s.awin_feed_api_key),
        "feed_base": s.awin_feed_base,
        "regions": s.awin_regions_list,
    }
    if not s.awin_feed_api_key:
        out["error"] = "AWIN_FEED_API_KEY absent"
        return out

    list_url = f"{s.awin_feed_base}/datafeed/list/apikey/{s.awin_feed_api_key}/"
    out["list_url"] = list_url.replace(s.awin_feed_api_key, "***")
    try:
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            resp = await client.get(list_url)
        out["list_http_status"] = resp.status_code
        out["list_body_head"] = resp.text[:1200]
    except Exception as exc:
        out["list_fetch_error"] = str(exc)

    try:
        feeds = await awin_catalog.list_feeds()
        out["parsed_feeds_count"] = len(feeds)
        out["sample_feeds"] = [
            {
                "feed_id": f.feed_id,
                "advertiser_id": f.advertiser_id,
                "advertiser_name": f.advertiser_name,
                "region": f.region,
                "products": f.products,
            }
            for f in feeds[:5]
        ]
        if session is not None:
            rows = (await session.execute(select(models.Merchant.awin_mid))).all()
            joined = {mid for (mid,) in rows}
            matched = [f for f in feeds if f.advertiser_id in joined]
            out["feeds_matching_joined_merchants"] = len(matched)
            if matched:
                out["sample_download_url"] = awin_catalog._download_url([matched[0].feed_id]).replace(
                    s.awin_feed_api_key, "***"
                )
    except Exception as exc:
        out["parse_error"] = str(exc)

    return out


@router.post("/sync/feeds")
async def sync_feeds_endpoint(
    background: BackgroundTasks,
    limit: int | None = Query(default=None, description="Nb max de feeds pour ce run"),
    x_admin_token: str | None = Header(default=None),
) -> dict:
    """Lance l'ingestion des feeds en arrière-plan (protégé par ADMIN_SYNC_TOKEN).

    Longue par nature : renvoie immédiatement. Suivre l'avancée via /catalog/stats.
    Utiliser ?limit=3 pour un premier test, avant un run complet (cron).
    """
    _require_admin(x_admin_token)
    if not db.is_enabled():
        raise HTTPException(status_code=503, detail="base de données absente")
    if not get_settings().awin_feed_api_key:
        raise HTTPException(status_code=400, detail="AWIN_FEED_API_KEY absent")
    background.add_task(_run_feed_ingest, limit)
    return {"started": True, "limit": limit, "note": "suivre /api/catalog/stats"}


@router.post("/admin/reset-price-history")
async def reset_price_history(
    confirm: bool = Query(default=False, description="Doit valoir true pour exécuter"),
    x_admin_token: str | None = Header(default=None),
    session=Depends(db.get_session),
) -> dict:
    """Purge les relevés de prix (protégé par ADMIN_SYNC_TOKEN).

    À n'utiliser qu'après une correction du parsing : les relevés produits avec
    un prix mal lu faussent durablement « plus bas » et « plus haut ». L'action
    est irréversible — l'historique ne se rattrape pas — mais mieux vaut repartir
    de zéro que bâtir sur des valeurs fausses.
    """
    _require_admin(x_admin_token)
    if session is None:
        raise HTTPException(status_code=503, detail="base de données absente")
    if not confirm:
        raise HTTPException(status_code=400, detail="ajouter ?confirm=true pour exécuter")
    before = await session.scalar(select(func.count()).select_from(models.PriceSnapshot))
    await session.execute(delete(models.PriceSnapshot))
    await session.commit()
    log.warning("Historique de prix purgé : %s relevés supprimés", before)
    return {"deleted_snapshots": int(before or 0)}


# ── Relief de prix : la matière de la scène 3D ───────────────────────────────
#
# La page d'accueil rend un paysage où chaque offre est une colonne dont la
# hauteur est son prix et dont les strates sont ses paliers successifs. Un
# endpoint dédié est nécessaire : `offer/{id}` ne donne l'historique que d'une
# offre, et il en faut plusieurs centaines en une requête pour remplir un
# `InstancedMesh` sans multiplier les allers-retours.

# Au-delà, le JSON dépasse le budget de charge utile de la page d'accueil.
RELIEF_MAX_COLUMNS = 300
# En dessous de deux relevés, il n'y a pas de palier : rien à dessiner.
RELIEF_MIN_SAMPLES = 2
# Une heure : la collecte de prix tourne au mieux quelques fois par jour, donc un
# TTL court ne ferait que repayer 20 s de calcul sans rien rafraîchir.
TTL_RELIEF = 3600

# Erreurs d'échelle des feeds : un marchand qui envoie les centimes au lieu des
# euros produit un palier hors de proportion (G-Shock relevée à 69,93 puis
# 6993,00 puis 99,90). Un simple plafond de remise ne suffit pas : le palier
# aberrant doit être retiré de la colonne, sans quoi la scène rendrait une
# flèche de cathédrale au milieu d'un paysage de plain-pied.
#
# Chercher un facteur exact (×100, ×1000) échoue en pratique : la référence
# calculée sur une colonne déjà polluée n'est pas le prix que le feed a
# multiplié. Sur le cas G-Shock, la médiane vaut 87,41 et 6993/87,41 = 80,0 :
# aucun facteur rond. Le critère robuste est l'ordre de grandeur.
_ECART_ORDRE_GRANDEUR = 10.0


def _est_hors_echelle(prix: float, reference: float) -> bool:
    """Vrai si `prix` s'écarte de `reference` de plus d'un ordre de grandeur.

    Test symétrique : le feed peut gonfler le prix (centimes lus comme euros) ou
    l'écraser (l'inverse). Un facteur 10 est déjà hors de portée d'une promotion :
    la remise la plus agressive observée plafonne à −80 %, soit un facteur 5.
    """
    if prix <= 0 or reference <= 0:
        return False
    return prix >= reference * _ECART_ORDRE_GRANDEUR or prix <= reference / _ECART_ORDRE_GRANDEUR


def _paliers_plausibles(paliers: list[list[float]], prix_courant: float) -> list[list[float]]:
    """Retire les paliers hors d'échelle par rapport au reste de la colonne.

    La référence est la médiane des *autres* paliers, recalculée pour chacun :
    inclure le palier testé dans sa propre référence l'aiderait à se justifier,
    et sur une colonne de deux points la médiane serait tirée à mi-chemin de
    l'aberration.
    """
    if len(paliers) < 3:
        # À deux points, aucun des deux n'est plus légitime que l'autre : les
        # écarter reviendrait à choisir au hasard. Le filtre SQL de plausibilité
        # (MAX_PLAUSIBLE_DROP_PCT) a déjà écarté les cas les plus grossiers.
        return paliers
    import statistics

    gardes = []
    for i, p in enumerate(paliers):
        autres = [q[1] for j, q in enumerate(paliers) if j != i]
        if not _est_hors_echelle(p[1], statistics.median(autres)):
            gardes.append(p)

    # Ne jamais rendre une colonne indessinable : s'il reste moins de deux
    # paliers, c'est la colonne entière qui est douteuse, et on préfère le brut
    # — le filtre SQL amont l'aura déjà bornée.
    if len(gardes) < 2:
        return paliers
    # Le premier palier doit rester à l'origine du temps, sinon la colonne
    # flotterait après le début de la fenêtre.
    if gardes[0][0] != 0.0:
        gardes = [[0.0, gardes[0][1]]] + gardes[1:]
    return gardes


def _confiance(jours: float, releves: int) -> str:
    """Qualifie ce que l'historique autorise à affirmer.

    Le front module l'opacité et le texte sur cette valeur : une colonne peu
    suivie s'affiche en retrait plutôt que d'asséner une tendance que trois
    relevés ne soutiennent pas.
    """
    if releves >= 10 and jours >= 10:
        return "bonne"
    if releves >= 5 and jours >= 4:
        return "moyenne"
    return "faible"


@router.get("/relief")
async def relief(
    limit: int = Query(default=180, le=RELIEF_MAX_COLUMNS, ge=12),
    window_days: int = Query(default=21, le=90, ge=3),
    category: str | None = Query(default=None, description="Rayon FILON à isoler"),
    session=Depends(db.get_session),
) -> dict:
    """Le relief des prix : N offres, leurs paliers, prêtes à être instanciées.

    Chaque colonne porte ses `steps` — des paires `[jours, prix]` — plutôt qu'une
    courbe lissée : sur trois semaines un prix ne décrit pas une pente mais des
    paliers, tenus puis rompus. C'est cette marche d'escalier que la scène rend,
    et c'est la forme réelle de la donnée, pas une interprétation.

    Les offres sont classées par ampleur de baisse : le premier plan du paysage
    est occupé par ce qui vient de décrocher, puisque c'est la seule information
    qui répond à « est-ce le bon moment ? ».
    """
    if session is None:
        return {"live": False, "columns": []}

    from datetime import UTC, datetime, timedelta

    from app.services.cache import cache_key, get_cache

    # La requête balaie 12,6 millions de relevés : 20 s mesurées sans cache, ce
    # qui est disqualifiant pour une page d'accueil. Le relief ne change qu'à
    # chaque collecte de prix, donc rien ne justifie de le recalculer par visite.
    cache = get_cache()
    cle = cache_key(
        "relief",
        catalog_price_truth.PRICE_TRUTH_CACHE_VERSION,
        str(limit),
        str(window_days),
        category or "tous",
    )
    en_cache = await cache.get_json(cle)
    if en_cache is not None:
        return {**en_cache, "cached": True}

    depuis = catalog_price_truth.utc_naive_now() - timedelta(days=window_days)

    # Présélection : les offres qui ont bougé dans la fenêtre. On agrège d'abord
    # pour ne rapatrier l'historique détaillé que des colonnes retenues — sortir
    # tous les relevés de 1,29 million d'offres pour n'en garder que 180 serait
    # absurde.
    snapshot_currency = catalog_price_truth.normalized_currency_sql(
        models.PriceSnapshot.currency
    )
    agg = (
        select(
            models.PriceSnapshot.offer_id.label("offer_id"),
            snapshot_currency.label("currency"),
            func.max(models.PriceSnapshot.price).label("haut"),
            func.min(models.PriceSnapshot.price).label("bas"),
            func.count().label("releves"),
            func.min(models.PriceSnapshot.captured_at).label("debut"),
        )
        .join(models.Offer, models.Offer.id == models.PriceSnapshot.offer_id)
        .where(
            models.PriceSnapshot.captured_at >= depuis,
            models.PriceSnapshot.price > 0,
            models.Offer.price.isnot(None),
            models.Offer.price > 0,
            catalog_price_truth.comparable_price_evidence_sql(
                snapshot_currency=models.PriceSnapshot.currency,
                offer_currency=models.Offer.currency,
                snapshot_in_stock=models.PriceSnapshot.in_stock,
                offer_in_stock=models.Offer.in_stock,
            ),
        )
        .group_by(models.PriceSnapshot.offer_id, snapshot_currency)
        .having(func.count() >= RELIEF_MIN_SAMPLES)
        .subquery()
    )

    # Combien de fois le prix haut a-t-il été observé ? Un pic vu une seule fois
    # est un accident de collecte, pas un prix pratiqué. Cette vérification
    # existait déjà pour les rangs de la home (cf. MIN_HIGH_OBSERVATIONS) ; la
    # scène 3D la réutilise plutôt que d'en inventer une variante.
    hauts = (
        select(
            agg.c.offer_id.label("offer_id"),
            func.count().label("occurrences_haut"),
        )
        .select_from(
            agg.join(
                models.PriceSnapshot,
                (models.PriceSnapshot.offer_id == agg.c.offer_id)
                & (
                    catalog_price_truth.normalized_currency_sql(
                        models.PriceSnapshot.currency
                    )
                    == agg.c.currency
                )
                & models.PriceSnapshot.in_stock.is_(True)
                & (
                    func.round(cast(models.PriceSnapshot.price, Numeric(12, 2)), 2)
                    == func.round(cast(agg.c.haut, Numeric(12, 2)), 2)
                ),
            )
        )
        .group_by(agg.c.offer_id)
        .subquery()
    )

    conditions = [
        models.Offer.price.isnot(None),
        models.Offer.price > 0,
        models.Offer.in_stock.is_(True),
        models.Offer.is_canonical.is_(True),
        models.Offer.is_adult.is_(False),
        models.Offer.filon_category.isnot(None),
        # Une baisse réelle : le haut de la fenêtre dépasse le prix courant.
        agg.c.haut > models.Offer.price,
        # Garde-fous de plausibilité, identiques à ceux des rangs de la home.
        # Sans eux, le premier plan du paysage — la colonne la plus éclairée,
        # celle qui affirme « achetez maintenant » — serait une erreur de feed.
        func.coalesce(hauts.c.occurrences_haut, 1) >= MIN_HIGH_OBSERVATIONS,
        func.coalesce(hauts.c.occurrences_haut, 1) >= agg.c.releves * MIN_HIGH_SHARE,
        models.Offer.price >= agg.c.haut * (1.0 - MAX_PLAUSIBLE_DROP_PCT / 100.0),
    ]
    if category:
        conditions.append(models.Offer.filon_category == category)

    # Ampleur de la baisse, en pourcentage du prix haut observé.
    ampleur = ((agg.c.haut - models.Offer.price) / agg.c.haut).label("ampleur")

    stmt = (
        select(
            models.Offer.id,
            models.Offer.name,
            models.Offer.brand,
            models.Offer.filon_category,
            models.Offer.price,
            agg.c.currency.label("currency"),
            models.Offer.image_url,
            models.Merchant.name.label("marchand"),
            agg.c.haut,
            agg.c.bas,
            agg.c.releves,
            agg.c.debut,
            ampleur,
        )
        .select_from(
            agg.join(
                models.Offer,
                (models.Offer.id == agg.c.offer_id)
                & catalog_price_truth.same_supported_currency_sql(
                    models.Offer.currency, agg.c.currency
                ),
            )
            .join(models.Merchant, models.Merchant.id == models.Offer.merchant_id)
            .outerjoin(hauts, hauts.c.offer_id == agg.c.offer_id)
        )
        .where(*conditions)
        .order_by(ampleur.desc())
        .limit(limit)
    )

    lignes = (await session.execute(stmt)).all()
    if not lignes:
        # Un relief vide n'est pas mis en cache : c'est probablement le signe que
        # la collecte est en panne, et il ne faut pas figer cet état.
        return {"live": True, "window_days": window_days, "columns": []}

    # Historique détaillé des seules colonnes retenues, en une requête.
    ids = [r.id for r in lignes]
    hist_rows = (
        await session.execute(
            select(
                models.PriceSnapshot.offer_id,
                models.PriceSnapshot.price,
                models.PriceSnapshot.captured_at,
            )
            .join(models.Offer, models.Offer.id == models.PriceSnapshot.offer_id)
            .where(
                models.PriceSnapshot.offer_id.in_(ids),
                models.PriceSnapshot.captured_at >= depuis,
                models.PriceSnapshot.price > 0,
                catalog_price_truth.comparable_price_evidence_sql(
                    snapshot_currency=models.PriceSnapshot.currency,
                    offer_currency=models.Offer.currency,
                    snapshot_in_stock=models.PriceSnapshot.in_stock,
                    offer_in_stock=models.Offer.in_stock,
                ),
            )
            .order_by(models.PriceSnapshot.offer_id, models.PriceSnapshot.captured_at)
        )
    ).all()

    par_offre: dict[int, list[tuple[float, object]]] = {}
    for oid, prix, quand in hist_rows:
        if prix is None or quand is None:
            continue
        par_offre.setdefault(oid, []).append((float(prix), quand))

    colonnes = []
    for r in lignes:
        brut = par_offre.get(r.id, [])
        if len(brut) < RELIEF_MIN_SAMPLES:
            continue

        t0 = brut[0][1]
        # Réduction aux paliers : on ne garde qu'un point quand le prix change.
        # Quinze relevés d'un prix identique décrivent un seul palier, et
        # transmettre les quinze gonflerait la charge utile sans rien ajouter.
        paliers: list[list[float]] = []
        dernier: float | None = None
        for prix, quand in brut:
            if dernier is None or abs(prix - dernier) >= 0.01:
                jours = round((quand - t0).total_seconds() / 86400.0, 3)
                paliers.append([jours, round(prix, 2)])
                dernier = prix

        paliers = _paliers_plausibles(paliers, float(r.price))
        if len(paliers) < 2:
            continue

        # Les extrêmes sont recalculés sur les paliers retenus : annoncer un haut
        # de 6993 € écarté de la scène mais conservé dans le libellé rendrait le
        # nettoyage invisible et le chiffre mensonger.
        valeurs = [p[1] for p in paliers]
        haut = max(valeurs)
        bas = min(valeurs)
        if haut <= 0:
            continue
        ampleur_reelle = (haut - float(r.price)) / haut

        duree = round((brut[-1][1] - t0).total_seconds() / 86400.0, 2)
        colonnes.append(
            {
                "id": r.id,
                "name": r.name,
                "brand": r.brand,
                "merchant": r.marchand,
                "category": r.filon_category,
                "price": round(float(r.price), 2),
                "currency": r.currency,
                "image": r.image_url,
                "high": round(haut, 2),
                "low": round(bas, 2),
                "drop_pct": round(ampleur_reelle * -100.0, 1),
                "steps": paliers,
                "tracked_days": duree,
                "samples": int(r.releves),
                "confidence": _confiance(duree, int(r.releves)),
            }
        )

    charge = {
        "live": True,
        "generated_at": datetime.now(UTC).isoformat(),
        "window_days": window_days,
        "count": len(colonnes),
        "columns": colonnes,
    }
    if colonnes:
        await cache.set_json(cle, charge, TTL_RELIEF)
    return {**charge, "cached": False}
