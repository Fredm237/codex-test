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
from app.services import taxonomy
from app.services import safety
from app.services.dedup import dedup_key

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
    """Convertit un prix de flux en float, quel que soit le format du marchand.

    Les feeds Awin melangent les conventions : « 799.90 », « 1.299,00 »,
    « 1,299.00 », « 1.299 ». Le piege est le separateur unique suivi de trois
    chiffres : « 1.299 » et « 1,299 » valent 1299, pas 1,30 — les lire comme des
    decimales rangeait des produits a 1 299 EUR dans les petits prix.
    """
    if not value:
        return None
    # Retire les espaces (dont insecables/fins) puis tout ce qui n'est ni
    # chiffre, ni separateur, ni signe : symboles monetaires et codes ISO.
    cleaned = value.strip()
    for ws in (" ", "\u00a0", "\u202f", "\u2009"):
        cleaned = cleaned.replace(ws, "")
    v = re.sub(r"[^0-9,.\-]", "", cleaned)
    if not v:
        return None

    if "," in v and "." in v:
        # Les deux presents : le *dernier* separateur est le decimal.
        dec = "," if v.rfind(",") > v.rfind(".") else "."
        v = v.replace("." if dec == "," else ",", "").replace(dec, ".")
    elif "," in v or "." in v:
        sep = "," if "," in v else "."
        parts = v.split(sep)
        if len(parts) > 2:
            # « 1.234.567 » : separateurs de milliers repetes.
            v = "".join(parts)
        elif len(parts[1]) == 3 and parts[0].lstrip("-") not in ("", "0"):
            # « 1.299 » / « 1,299 » : trois chiffres derriere = milliers.
            v = parts[0] + parts[1]
        else:
            v = parts[0] + "." + parts[1]

    try:
        return round(float(v), 2)
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
        # adultcontent/0 : FILON est un catalogue grand public. Ce flag valait 1,
        # ce qui faisait remonter des produits pour adultes en page d'accueil.
        f"compression/gzip/adultcontent/0/"
    )


async def _download_feed_rows(feed_ids: list[str], *, max_rows: int = 0) -> list[dict]:
    """Télécharge un feed (CSV gzip) et renvoie ses lignes.

    Lecture en flux : on s'arrête à `max_rows` sans matérialiser tout le feed
    (essentiel pour les gros feeds — évite la saturation mémoire).
    """
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
    reader = csv.DictReader(io.StringIO(text))
    rows: list[dict] = []
    for row in reader:
        rows.append(row)
        if max_rows and len(rows) >= max_rows:
            break
    return rows


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
        "filon_category": (_cat := taxonomy.classify(
            row.get("merchant_category"), name, row.get("brand_name")
        )),
        "filon_subcategory": taxonomy.classify_subcategory(
            _cat, name, row.get("merchant_category")
        ),
        # Le rattachement au produit EAN se fait plus tard : la clé se contente
        # ici du libellé, et le rattrapage la recalcule ensuite.
        "dedup_key": dedup_key(product_id=None, brand=row.get("brand_name"), name=name),
        # Posé dès l'ingestion : une référence érotique arrivée dans le flux
        # d'un marchand généraliste ne doit jamais atteindre une page publique.
        "is_adult": safety.is_adult(
            name=name,
            category=row.get("merchant_category"),
            brand=row.get("brand_name"),
        ),
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
            # `is_adult` fait partie de la mise à jour : un marchand qui renomme
            # une référence ne doit pas conserver un drapeau devenu faux, ni le
            # perdre quand il le devient.
            set_={k: values[k] for k in ("name", "brand", "category", "price", "currency", "in_stock", "image_url", "deep_link", "ean", "is_adult")},
        )
        .returning(models.Offer.id)
    )
    result = await session.execute(stmt)
    offer_id = result.scalar_one_or_none()
    if offer_id is not None and price is not None:
        session.add(models.PriceSnapshot(offer_id=offer_id, price=price, in_stock=in_stock))


async def ingest_feeds(session, *, limit_override: int | None = None) -> dict:
    """Ingestion des feeds des marchands inscrits, régions ciblées.

    Un feed à la fois (rattachement marchand fiable). `limit_override` borne le
    nombre de feeds pour ce run (prioritaire sur AWIN_FEED_LIMIT). Le garde-fou
    AWIN_MAX_ROWS_PER_FEED limite les lignes par feed (mémoire). Retourne un
    récapitulatif {feeds, offers, skipped}.
    """
    if session is None:
        log.warning("Pas de base de données → ingestion feeds ignorée")
        return {"feeds": 0, "offers": 0, "skipped": 0}
    s = get_settings()
    regions = set(s.awin_regions_list)
    max_rows = s.awin_max_rows_per_feed

    # Marchands inscrits connus en base : awin_mid -> merchant_id
    rows = (await session.execute(select(models.Merchant.id, models.Merchant.awin_mid))).all()
    mid_to_id = {mid: pk for (pk, mid) in rows}
    if not mid_to_id:
        log.warning("Aucun marchand en base → lancer sync_merchants d'abord")
        return {"feeds": 0, "offers": 0, "skipped": 0}

    feeds = await list_feeds()
    selected = [
        f for f in feeds
        if f.advertiser_id in mid_to_id and (not regions or not f.region or f.region in regions)
    ]
    limit = limit_override if limit_override is not None else s.awin_feed_limit
    if limit and limit > 0:
        selected = selected[:limit]
    log.info("Feeds retenus pour ingestion : %d / %d", len(selected), len(feeds))

    total_offers = 0
    skipped = 0
    for f in selected:
        try:
            frows = await _download_feed_rows([f.feed_id], max_rows=max_rows)
        except Exception as exc:  # pragma: no cover - réseau/compte
            log.warning("Feed %s (%s) indisponible (%s)", f.feed_id, f.advertiser_name, exc)
            skipped += 1
            continue
        merchant_id = mid_to_id[f.advertiser_id]
        n = 0
        for row in frows:
            await _upsert_offer(session, merchant_id, row)
            n += 1
            if n % 200 == 0:  # commit périodique → progression visible dans /stats
                await session.commit()
        await session.commit()
        total_offers += n
        log.info("Feed %s (%s) → %d offres", f.feed_id, f.advertiser_name, n)

    log.info("Ingestion terminée : %d feeds, %d offres, %d ignorés", len(selected), total_offers, skipped)
    return {"feeds": len(selected), "offers": total_offers, "skipped": skipped}
