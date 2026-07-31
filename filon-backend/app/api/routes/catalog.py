"""API catalogue — lecture des marchands / offres Awin et déclenchement du sync.

Ces endpoints alimenteront les futures pages catalogue/marchand/produit du site.
Ils dégradent proprement si la base est absente (listes vides).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy import func, select

from app.core.config import get_settings
from app.db import models
from app.db import session as db

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


@router.get("/offers")
async def offers(
    q: str | None = Query(default=None, description="Recherche dans le nom"),
    merchant: str | None = Query(default=None, description="Slug marchand"),
    category: str | None = None,
    brand: str | None = None,
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
    total = await session.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = (await session.execute(stmt.limit(limit).offset(offset))).all()
    return {
        "total": int(total or 0),
        "items": [
            {
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
