"""API catalogue — lecture des marchands / offres Awin et déclenchement du sync.

Ces endpoints alimenteront les futures pages catalogue/marchand/produit du site.
Ils dégradent proprement si la base est absente (listes vides).
"""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Query
from sqlalchemy import func, select

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
    return {
        "database": True,
        "merchants": int(merchants or 0),
        "offers": int(offers or 0),
        "snapshots": int(snapshots or 0),
    }


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

    base = select(models.Offer, models.Merchant).join(
        models.Merchant, models.Offer.merchant_id == models.Merchant.id
    )
    visible = (
        models.Offer.price.isnot(None),
        models.Offer.price > 0,
        models.Offer.image_url.isnot(None),
    )

    drop_pct = ((snap.c.high - models.Offer.price) / snap.c.high * 100.0)

    # 📉 Les plus grosses baisses de prix (prix actuel < plus haut relevé).
    drops_stmt = (
        base.add_columns(snap.c.high, snap.c.low, drop_pct.label("drop_pct"))
        .join(snap, snap.c.offer_id == models.Offer.id)
        .where(*visible, snap.c.high > models.Offer.price)
        .order_by(drop_pct.desc())
        .limit(limit)
    )
    drops = [
        _card(o, m, price_high=high, price_low=low, drop_pct=round(float(pct), 1))
        for (o, m, high, low, pct) in (await session.execute(drops_stmt)).all()
    ]

    # 🏅 Au plus bas historique (et le prix a réellement varié).
    lowest_stmt = (
        base.add_columns(snap.c.high, snap.c.low)
        .join(snap, snap.c.offer_id == models.Offer.id)
        .where(
            *visible,
            snap.c.high > snap.c.low,
            models.Offer.price <= snap.c.low,
        )
        .order_by(((snap.c.high - snap.c.low) / snap.c.high).desc())
        .limit(limit)
    )
    lowest = [
        _card(o, m, price_high=high, price_low=low, is_lowest=True)
        for (o, m, high, low) in (await session.execute(lowest_stmt)).all()
    ]

    # 🆕 Derniers produits entrés au catalogue.
    fresh_stmt = (
        base.where(*visible)
        .order_by(models.Offer.created_at.desc(), models.Offer.id.desc())
        .limit(limit)
    )
    fresh = [_card(o, m) for (o, m) in (await session.execute(fresh_stmt)).all()]

    # 💶 Moins de 100 € — la porte d'entrée « petits prix ».
    budget_stmt = (
        base.where(*visible, models.Offer.price <= 100)
        .order_by(models.Offer.price.desc(), models.Offer.id.desc())
        .limit(limit)
    )
    budget = [_card(o, m) for (o, m) in (await session.execute(budget_stmt)).all()]

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


def _require_admin(x_admin_token: str | None) -> None:
    s = get_settings()
    if not s.admin_sync_token or x_admin_token != s.admin_sync_token:
        raise HTTPException(status_code=403, detail="admin token requis")


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
