"""Ingestion du catalogue Awin → base de données FILON.

Deux étages, indépendants et sans plantage fatal (dégradation propre) :

1. `sync_merchants()` — appelle l'API Publisher Awin (programmes « joined ») et
   met à jour la table `merchants`. Ne nécessite que `AWIN_API_TOKEN`. C'est le
   socle : la liste de tes marchands inscrits.

2. `ingest_feeds()` — télécharge les feeds produits Awin (Create-a-Feed), n'en
   garde que ceux des marchands inscrits dans les régions ciblées, et remplit
   `offers` + `price_snapshots`. Nécessite `AWIN_FEED_API_KEY`.

Aucun secret n'est codé en dur : tout vient de la configuration (variables
d'environnement). Ces fonctions sont conçues pour tourner sur Railway (accès
Internet), pas dans le bac à sable de développement.
"""

from __future__ import annotations

import csv
import gzip
import io
import re
from dataclasses import dataclass

import httpx
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db import models

log = get_logger("awin_catalog")

# Colonnes demandées explicitement au feed → parsing déterministe.
_FEED_COLUMNS = [
    "aw_product_id",
    "product_name",
    "aw_deep_link",
    "merchant_image_url",
    "search_price",
    "currency",
    "merchant_category",
    "brand_name",
    "ean",
    "in_stock",
]


def _slugify(text: str) -> str:
    text = (text or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "marchand"


def _to_float(value: str | None) -> float | None:
    if not value:
        return None
    v = value.strip().replace(" ", "").replace(" ", "")
    # Le *dernier* séparateur est le décimal ; les autres sont des milliers.
    # Gère « 1.299,00 » → 1299.00, « 1,299.00 » → 1299.00, « 799.90 » → 799.90.
    if "," in v and "." in v:
        dec = "," if v.rfind(",") > v.rfind(".") else "."
        thou = "." if dec == "," else ","
        v = v.replace(thou, "").replace(dec, ".")
    elif "," in v:
        v = v.replace(",", ".")
    try:
        return round(float(re.sub(r"[^0-9.\-]", "", v)), 2)
    except ValueError:
        return None


def _to_bool(value: str | None) -> bool | None:
    if value is None or value == "":
        return None
    return value.strip().lower() in {"1", "true", "yes", "y", "in stock", "instock"}


# ─────────────────────────────────────────────────────────────────────────────
# 1) Synchronisation des marchands inscrits (API Publisher)
# ─────────────────────────────────────────────────────────────────────────────


async def fetch_joined_programmes() -> list[dict]:
    """Récupère les programmes « joined » depuis l'API Publisher Awin."""
    s = get_settings()
    if not s.awin_api_token or not s.awin_publisher_id:
        log.warning("AWIN_API_TOKEN/publisher_id absent → aucun marchand à synchroniser")
        return []
    url = f"{s.awin_api_base}/publishers/{s.awin_publisher_id}/programmes"
    headers = {"Authorization": f"Bearer {s.awin_api_token}"}
    params = {"relationship": "joined"}
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.get(url, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()
    return data if isinstance(data, list) else data.get("programmes", [])


def _programme_to_values(p: dict) -> dict | None:
    mid = p.get("id")
    if not isinstance(mid, int):
        return None
    name = str(p.get("name") or "").strip() or f"Marchand {mid}"
    region = p.get("primaryRegion") or {}
    region_code = (region.get("countryCode") if isinstance(region, dict) else None) or None
    domain = None
    disp = p.get("displayUrl") or p.get("clickThroughUrl")
    if disp:
        domain = re.sub(r"^https?://(www\.)?", "", str(disp)).split("/")[0] or None
    sector = p.get("primarySector") or (p.get("sector") if isinstance(p.get("sector"), str) else None)
    return {
        "awin_mid": mid,
        "name": name,
        "slug": _slugify(name),
        "domain": domain,
        "region": (region_code or "").upper() or None,
        "currency": p.get("currencyCode"),
        "sector": sector,
        "logo_url": p.get("logoUrl"),
        "joined": True,
    }


async def sync_merchants(session) -> int:
    """Upsert des marchands inscrits. Retourne le nombre synchronisé."""
    if session is None:
        log.warning("Pas de base de données → sync marchands ignorée")
        return 0
    programmes = await fetch_joined_programmes()
    count = 0
    for p in programmes:
        values = _programme_to_values(p)
        if not values:
            continue
        stmt = (
            pg_insert(models.Merchant)
            .values(**values)
            .on_conflict_do_update(
                index_elements=["awin_mid"],
                set_={
                    "name": values["name"],
                    "slug": values["slug"],
                    "domain": values["domain"],
                    "region": values["region"],
                    "currency": values["currency"],
                    "sector": values["sector"],
                    "logo_url": values["logo_url"],
                    "joined": True,
                },
            )
        )
        await session.execute(stmt)
        count += 1
    await session.commit()
    log.info("Marchands Awin synchronisés : %d", count)
    return count


# ─────────────────────────────────────────────────────────────────────────────
# 2) Ingestion des feeds produits (Create-a-Feed)
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class FeedInfo:
    feed_id: str
    advertiser_id: int
    advertiser_name: str
    region: str
    products: int


async def list_feeds() -> list[FeedInfo]:
    """Liste les feeds disponibles pour l'éditeur (endpoint datafeed/list)."""
    s = get_settings()
    if not s.awin_feed_api_key:
        log.warning("AWIN_FEED_API_KEY absent → ingestion des feeds désactivée")
        return []
    url = f"{s.awin_feed_base}/datafeed/list/apikey/{s.awin_feed_api_key}/"
    async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        text = resp.text
    feeds: list[FeedInfo] = []
    reader = csv.DictReader(io.StringIO(text))
    for row in reader:
        # noms de colonnes tolérants (l'entête Awin varie légèrement)
        low = {k.strip().lower(): (v or "").strip() for k, v in row.items() if k}
        fid = low.get("feed id") or low.get("feed_id")
        adv = low.get("advertiser id") or low.get("advertiser_id")
        if not fid or not adv:
            continue
        try:
            advertiser_id = int(adv)
        except ValueError:
            continue
        try:
            products = int(re.sub(r"[^0-9]", "", low.get("no of products", "0") or "0") or 0)
        except ValueError:
            products = 0
        feeds.append(
            FeedInfo(
                feed_id=fid,
                advertiser_id=advertiser_id,
                advertiser_name=low.get("advertiser name", ""),
                region=(low.get("primary region") or low.get("region") or "").upper(),
                products=products,
            )
        )
    log.info("Feeds Awin listés : %d", len(feeds))
    return feeds


def _download_url(feed_ids: list[str]) -> str:
    s = get_settings()
    cols = ",".join(_FEED_COLUMNS)
    fid = ",".join(feed_ids)
    return (
        f"{s.awin_feed_base}/datafeed/download/apikey/{s.awin_feed_api_key}/"
        f"language/any/fid/{fid}/columns/{cols}/format/csv/delimiter/%2C/"
        f"compression/gzip/adultcontent/1/"
    )


async def _download_feed_rows(feed_ids: list[str]) -> list[dict]:
    """Télécharge et décompresse un lot de feeds (CSV gzip) → lignes dict."""
    url = _download_url(feed_ids)
    async with httpx.AsyncClient(timeout=300.0, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        raw = resp.content
    try:
        data = gzip.decompress(raw)
    except (OSError, EOFError):
        data = raw  # au cas où la réponse ne serait pas gzip
    text = data.decode("utf-8", errors="replace")
    return list(csv.DictReader(io.StringIO(text)))


async def _upsert_offer(session, merchant_id: int, row: dict) -> None:
    pid = (row.get("aw_product_id") or "").strip()
    name = (row.get("product_name") or "").strip()
    if not pid or not name:
        return
    price = _to_float(row.get("search_price"))
    in_stock = _to_bool(row.get("in_stock"))
    values = {
        "merchant_id": merchant_id,
        "awin_product_id": pid[:191],
        "ean": (row.get("ean") or "").strip()[:64] or None,
        "name": name[:512],
        "brand": (row.get("brand_name") or "").strip()[:191] or None,
        "category": (row.get("merchant_category") or "").strip()[:255] or None,
        "price": price,
        "currency": (row.get("currency") or "").strip()[:8] or None,
        "in_stock": in_stock,
        "image_url": (row.get("merchant_image_url") or "").strip() or None,
        "deep_link": (row.get("aw_deep_link") or "").strip() or None,
    }
    stmt = (
        pg_insert(models.Offer)
        .values(**values)
        .on_conflict_do_update(
            constraint="uq_offer_merchant_product",
            set_={k: values[k] for k in ("name", "brand", "category", "price", "currency", "in_stock", "image_url", "deep_link", "ean")},
        )
        .returning(models.Offer.id)
    )
    result = await session.execute(stmt)
    offer_id = result.scalar_one_or_none()
    if offer_id is not None and price is not None:
        session.add(models.PriceSnapshot(offer_id=offer_id, price=price, in_stock=in_stock))


async def ingest_feeds(session, *, batch: int = 10) -> dict:
    """Ingestion des feeds des marchands inscrits, régions ciblées.

    Retourne un petit récapitulatif {feeds, offers}.
    """
    if session is None:
        log.warning("Pas de base de données → ingestion feeds ignorée")
        return {"feeds": 0, "offers": 0}
    s = get_settings()
    regions = set(s.awin_regions_list)

    # Marchands inscrits connus en base : awin_mid -> merchant_id
    rows = (await session.execute(select(models.Merchant.id, models.Merchant.awin_mid))).all()
    mid_to_id = {mid: pk for (pk, mid) in rows}
    if not mid_to_id:
        log.warning("Aucun marchand en base → lancer sync_merchants d'abord")
        return {"feeds": 0, "offers": 0}

    feeds = await list_feeds()
    # ne garder que les feeds des marchands inscrits, dans les régions voulues
    selected = [
        f for f in feeds
        if f.advertiser_id in mid_to_id and (not regions or not f.region or f.region in regions)
    ]
    if s.awin_feed_limit > 0:
        selected = selected[: s.awin_feed_limit]
    log.info("Feeds retenus pour ingestion : %d / %d", len(selected), len(feeds))

    total_offers = 0
    for i in range(0, len(selected), batch):
        chunk = selected[i : i + batch]
        fid_to_merchant = {f.feed_id: mid_to_id[f.advertiser_id] for f in chunk}
        try:
            rows = await _download_feed_rows(list(fid_to_merchant.keys()))
        except Exception as exc:  # pragma: no cover - réseau/compte
            log.warning("Feed lot %s indisponible (%s)", list(fid_to_merchant.keys()), exc)
            continue
        # Un lot mélange plusieurs feeds ; on rattache par advertiser via aw_deep_link
        # n'étant pas fiable, on ingère par feed unitaire quand le lot > 1.
        if len(chunk) == 1:
            merchant_id = next(iter(fid_to_merchant.values()))
            for row in rows:
                await _upsert_offer(session, merchant_id, row)
                total_offers += 1
            await session.commit()
        else:
            # Retéléchargement feed par feed pour un rattachement marchand fiable.
            for f in chunk:
                try:
                    frows = await _download_feed_rows([f.feed_id])
                except Exception as exc:  # pragma: no cover
                    log.warning("Feed %s indisponible (%s)", f.feed_id, exc)
                    continue
                merchant_id = mid_to_id[f.advertiser_id]
                for row in frows:
                    await _upsert_offer(session, merchant_id, row)
                    total_offers += 1
                await session.commit()

    log.info("Ingestion terminée : %d feeds, %d offres", len(selected), total_offers)
    return {"feeds": len(selected), "offers": total_offers}
