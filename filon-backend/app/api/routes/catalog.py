"""API catalogue — lecture des marchands / offres Awin et déclenchement du sync.

Ces endpoints alimenteront les futures pages catalogue/marchand/produit du site.
Ils dégradent proprement si la base est absente (listes vides).
"""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Query
from sqlalchemy import String, case, cast, delete, func, select

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db import models
from app.db import session as db

log = get_logger("catalog")

router = APIRouter(prefix="/catalog", tags=["catalog"])


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
    category: str | None = None,
    brand: str | None = None,
    price_min: float | None = Query(default=None, ge=0),
    price_max: float | None = Query(default=None, ge=0),
    sort: str = Query(default="relevance", description="relevance|price_asc|price_desc|name"),
    limit: int = Query(default=48, le=200),
    offset: int = Query(default=0, ge=0),
    session=Depends(db.get_session),
) -> dict:
    if session is None:
        return {"total": 0, "items": []}
    stmt = select(models.Offer, models.Merchant).join(
        models.Merchant, models.Offer.merchant_id == models.Merchant.id
    )
    if q:
        stmt = stmt.where(models.Offer.name.ilike(f"%{q}%"))
    if merchant:
        stmt = stmt.where(models.Merchant.slug == merchant)
    if category:
        stmt = stmt.where(models.Offer.category.ilike(f"%{category}%"))
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
    rows = (await session.execute(stmt.limit(limit).offset(offset))).all()
    return {
        "total": int(total or 0),
        "items": [
            {
                "id": o.id,
                "name": o.name,
                "brand": o.brand,
                "category": o.category,
                "price": o.price,
                "currency": o.currency,
                "in_stock": o.in_stock,
                "image": o.image_url,
                "link": o.deep_link,
                "merchant": {"name": m.name, "slug": m.slug},
            }
            for (o, m) in rows
        ],
    }


@router.get("/facets")
async def facets(
    limit: int = Query(default=40, le=200),
    session=Depends(db.get_session),
) -> dict:
    """Catégories et marques les plus fréquentes, pour les menus de filtres."""
    if session is None:
        return {"categories": [], "brands": []}
    cat_stmt = (
        select(models.Offer.category, func.count().label("n"))
        .where(models.Offer.category.isnot(None))
        .group_by(models.Offer.category)
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


def _card(o: models.Offer, m: models.Merchant, **extra) -> dict:
    """Charge utile compacte d'une carte produit (rails de la home catalogue)."""
    return {
        "id": o.id,
        "name": o.name,
        "brand": o.brand,
        "category": o.category,
        "price": o.price,
        "currency": o.currency,
        "in_stock": o.in_stock,
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
    cards = []
    for r in rows:  # l'ordre du rail fait foi
        pair = objects.get(r["id"])
        if pair:
            o, m = pair
            cards.append(_card(o, m, **{k: fn(r) for k, fn in extra}))
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

    # Agrégat d'historique : uniquement les offres relevées au moins deux fois,
    # sinon « baisse » et « plus bas » n'ont aucun sens.
    snap = (
        select(
            models.PriceSnapshot.offer_id.label("offer_id"),
            func.max(models.PriceSnapshot.price).label("high"),
            func.min(models.PriceSnapshot.price).label("low"),
        )
        .group_by(models.PriceSnapshot.offer_id)
        .having(func.count() > 1)
        .subquery()
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

    visible = (
        models.Offer.price.isnot(None),
        models.Offer.price > 0,
        models.Offer.image_url.isnot(None),
    )

    # 📉 Les plus grosses baisses de prix (prix actuel < plus haut relevé).
    drop_pct = ((snap.c.high - models.Offer.price) / snap.c.high * 100.0)
    drops_core = (
        core(drop_pct.desc(), snap.c.high.label("high"), snap.c.low.label("low"),
             drop_pct.label("drop_pct"))
        .join(snap, snap.c.offer_id == models.Offer.id)
        .where(*visible, snap.c.high > models.Offer.price)
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
    depth = ((snap.c.high - snap.c.low) / snap.c.high)
    lowest_core = (
        core(depth.desc(), snap.c.high.label("high"), snap.c.low.label("low"))
        .join(snap, snap.c.offer_id == models.Offer.id)
        .where(*visible, snap.c.high > snap.c.low, models.Offer.price <= snap.c.low)
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
    return {"sections": [s for s in sections if s["items"]]}


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
    hist = (
        await session.execute(
            select(models.PriceSnapshot.price, models.PriceSnapshot.captured_at)
            .where(models.PriceSnapshot.offer_id == offer_id)
            .order_by(models.PriceSnapshot.captured_at)
        )
    ).all()
    prices = [p for (p, _) in hist if p is not None]
    return {
        "id": o.id,
        "name": o.name,
        "brand": o.brand,
        "category": o.category,
        "ean": o.ean,
        "price": o.price,
        "currency": o.currency,
        "in_stock": o.in_stock,
        "image": o.image_url,
        "link": o.deep_link,
        "merchant": {"name": m.name, "slug": m.slug, "domain": m.domain, "region": m.region},
        "history": [
            {"price": p, "at": at.isoformat() if at else None} for (p, at) in hist
        ],
        "price_min": min(prices) if prices else None,
        "price_max": max(prices) if prices else None,
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
    return {
        "total": int(total or 0),
        "items": [
            {
                "ean": p.ean,
                "name": p.name,
                "brand": p.brand,
                "category": p.category,
                "image": p.image_url,
                "price_min": p.price_min,
                "price_max": p.price_max,
                "currency": p.currency,
                "offers_count": p.offers_count,
                "merchants_count": p.merchants_count,
            }
            for p in rows
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
    return {
        "ean": product.ean,
        "name": product.name,
        "brand": product.brand,
        "category": product.category,
        "image": product.image_url,
        "price_min": product.price_min,
        "price_max": product.price_max,
        "currency": product.currency,
        "offers_count": product.offers_count,
        "merchants_count": product.merchants_count,
        "offers": [
            {
                "id": o.id,
                "price": o.price,
                "currency": o.currency,
                "in_stock": o.in_stock,
                "link": o.deep_link,
                "merchant": {"name": m.name, "slug": m.slug, "region": m.region},
            }
            for (o, m) in rows
        ],
    }


def _require_admin(x_admin_token: str | None) -> None:
    s = get_settings()
    if not s.admin_sync_token or x_admin_token != s.admin_sync_token:
        raise HTTPException(status_code=403, detail="admin token requis")


async def _run_rebuild_products() -> None:
    """Reconstruction des produits en tâche de fond (session dédiée)."""
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
    if wait:
        from app.services import catalog_grouping

        return await catalog_grouping.rebuild_products(session)
    background.add_task(_run_rebuild_products)
    return {"started": True, "note": "suivre /api/catalog/products"}


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
    """Ingestion des feeds en tâche de fond (session dédiée hors requête)."""
    from app.services import awin_catalog

    async with db.session_scope() as session:
        if session is None:
            log.warning("Ingestion feeds : base absente")
            return
        try:
            summary = await awin_catalog.ingest_feeds(session, limit_override=limit)
            log.info("Ingestion feeds terminée : %s", summary)
        except Exception as exc:  # pragma: no cover - réseau/compte
            log.warning("Ingestion feeds échouée : %s", exc)


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
