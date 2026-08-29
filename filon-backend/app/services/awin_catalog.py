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
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime

import httpx
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.observability import (
    outbound_trace_headers,
    traced_dependency,
    traced_pipeline_stage,
)
from app.db import models
from app.services import taxonomy
from app.services import safety
from app.services.currency import normalize_currency_code
from app.services.dedup import dedup_key
from app.services.source_normalization import parse_price, parse_tristate_bool

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
_HARD_MAX_ROWS_PER_FEED = 250_000
_SPOOL_MEMORY_BYTES = 8 * 1024 * 1024


class AwinFeedCompressedLimitError(RuntimeError):
    """Le corps Awin reçu dépasse la limite compressée configurée."""


class AwinFeedDecompressedLimitError(RuntimeError):
    """Le contenu Awin décompressé dépasse la limite configurée."""


class _BoundedBinaryReader(io.RawIOBase):
    """Adapte un flux binaire en interrompant toute décompression excessive."""

    def __init__(self, source, *, limit: int) -> None:
        super().__init__()
        self._source = source
        self._limit = limit
        self._read = 0

    def readable(self) -> bool:
        return True

    def readinto(self, buffer) -> int:
        remaining = self._limit - self._read
        chunk = self._source.read(min(len(buffer), max(0, remaining) + 1))
        if len(chunk) > remaining:
            raise AwinFeedDecompressedLimitError
        if not chunk:
            return 0
        buffer[: len(chunk)] = chunk
        self._read += len(chunk)
        return len(chunk)

    def close(self) -> None:
        try:
            self._source.close()
        finally:
            super().close()


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
    return parse_price(value)


def _to_bool(value: str | None) -> bool | None:
    return parse_tristate_bool(value)


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
    async with traced_dependency("awin", "programmes"):
        headers.update(outbound_trace_headers())
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
    async with traced_dependency("postgres", "write"):
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
    async with traced_dependency("awin", "feed_list"):
        async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
            resp = await client.get(url, headers=outbound_trace_headers())
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

    Le réseau est lu par morceaux dans un spool qui quitte la mémoire après
    8 MiB. Les volumes compressé et décompressé ainsi que le nombre de lignes
    sont tous plafonnés. ``max_rows=0`` signifie le plafond dur, jamais illimité.
    """
    settings = get_settings()
    compressed_limit = settings.awin_max_download_bytes
    decompressed_limit = settings.awin_max_decompressed_bytes
    row_limit = min(
        max_rows if max_rows > 0 else _HARD_MAX_ROWS_PER_FEED,
        _HARD_MAX_ROWS_PER_FEED,
    )
    url = _download_url(feed_ids)
    with tempfile.SpooledTemporaryFile(
        max_size=min(_SPOOL_MEMORY_BYTES, compressed_limit),
        mode="w+b",
    ) as spool:
        async with traced_dependency("awin", "feed_download"):
            async with httpx.AsyncClient(
                timeout=300.0,
                follow_redirects=True,
            ) as client:
                async with client.stream(
                    "GET",
                    url,
                    headers=outbound_trace_headers(),
                ) as resp:
                    resp.raise_for_status()
                    downloaded = 0
                    async for chunk in resp.aiter_bytes():
                        downloaded += len(chunk)
                        if downloaded > compressed_limit:
                            raise AwinFeedCompressedLimitError
                        spool.write(chunk)

        spool.seek(0)
        magic = spool.read(2)
        spool.seek(0)
        source = (
            gzip.GzipFile(fileobj=spool, mode="rb")
            if magic == b"\x1f\x8b"
            else spool
        )
        bounded = _BoundedBinaryReader(source, limit=decompressed_limit)
        rows: list[dict] = []
        with io.TextIOWrapper(
            io.BufferedReader(bounded),
            encoding="utf-8",
            errors="replace",
            newline="",
        ) as text_stream:
            reader = csv.DictReader(text_stream)
            for row in reader:
                rows.append(row)
                if len(rows) >= row_limit:
                    break
        return rows


def _should_record_snapshot(
    snapshot_cache: set[tuple[int, str, float, str | None, bool | None]] | None,
    merchant_id: int,
    product_id: str,
    price: float,
    currency: str | None,
    in_stock: bool | None,
) -> bool:
    """Retourne si un relevé est inédit dans le cycle Awin courant."""
    if snapshot_cache is None:
        return True
    key = (merchant_id, product_id[:191], price, currency, in_stock)
    if key in snapshot_cache:
        return False
    snapshot_cache.add(key)
    return True


async def _upsert_offer(
    session,
    merchant_id: int,
    row: dict,
    *,
    merchant_name: str | None = None,
    snapshot_cache: set[tuple[int, str, float, str | None, bool | None]] | None = None,
) -> int | None:
    pid = (row.get("aw_product_id") or "").strip()
    name = (row.get("product_name") or "").strip()
    if not pid or not name:
        return None
    price = _to_float(row.get("search_price"))
    currency = normalize_currency_code(row.get("currency"))
    in_stock = _to_bool(row.get("in_stock"))
    offer_kind = taxonomy.classify_offer_kind(
        row.get("merchant_category"), name, row.get("brand_name"), merchant_name
    )
    values = {
        "merchant_id": merchant_id,
        "awin_product_id": pid[:191],
        "ean": (row.get("ean") or "").strip()[:64] or None,
        "name": name[:512],
        "brand": (row.get("brand_name") or "").strip()[:191] or None,
        "category": (row.get("merchant_category") or "").strip()[:255] or None,
        "filon_category": (_cat := taxonomy.classify(
            row.get("merchant_category"), name, row.get("brand_name"), merchant_name
        )),
        "filon_subcategory": taxonomy.classify_subcategory(
            _cat, name, row.get("merchant_category"), merchant_name
        ),
        "offer_kind": offer_kind,
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
        "currency": currency,
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
            set_={k: values[k] for k in (
                "name", "brand", "category", "filon_category", "filon_subcategory",
                "offer_kind", "dedup_key", "price", "currency", "in_stock", "image_url",
                "deep_link", "ean", "is_adult",
            )},
        )
        .returning(models.Offer.id)
    )
    result = await session.execute(stmt)
    offer_id = result.scalar_one_or_none()
    if offer_id is not None and price is not None:
        # Plusieurs feeds Awin d’un même marchand existent souvent pour les
        # langues FR/NL/EN. Ils peuvent porter le même article dans le même run.
        # Sans garde, chaque variante ajoutait un relevé identique et gonflait
        # artificiellement l’historique, donc la confiance du Score FILON.
        #
        # Le cache ne vit que le temps d’un cycle : un même prix est toujours
        # relevé au prochain cycle, mais jamais deux fois pour le même article,
        # prix et stock pendant ce cycle.
        if _should_record_snapshot(
            snapshot_cache, merchant_id, pid, price, currency, in_stock
        ):
            session.add(
                models.PriceSnapshot(
                    offer_id=offer_id,
                    price=price,
                    currency=currency,
                    in_stock=in_stock,
                )
            )
    return offer_id


def _ingestion_stage_outcome(result: dict) -> str:
    shadow = result.get("shadow") or {}
    if result.get("skipped") or shadow.get("failures"):
        return "degraded"
    if not result.get("feeds"):
        return "degraded"
    return "ok"


@traced_pipeline_stage("ingestion", result_outcome=_ingestion_stage_outcome)
async def ingest_feeds(
    session,
    *,
    limit_override: int | None = None,
    sync_run_id: int | None = None,
) -> dict:
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

    # Marchands inscrits connus en base : le nom est aussi un signal sémantique
    # borné, utilisé uniquement par les règles qui l’exigent explicitement.
    async with traced_dependency("postgres", "read"):
        rows = (
            await session.execute(
                select(
                    models.Merchant.id,
                    models.Merchant.awin_mid,
                    models.Merchant.name,
                )
            )
        ).all()
    mid_to_merchant = {mid: (pk, name) for (pk, mid, name) in rows}
    if not mid_to_merchant:
        log.warning("Aucun marchand en base → lancer sync_merchants d'abord")
        return {"feeds": 0, "offers": 0, "skipped": 0}

    feeds = await list_feeds()
    selected = [
        f for f in feeds
        if f.advertiser_id in mid_to_merchant and (not regions or not f.region or f.region in regions)
    ]
    limit = limit_override if limit_override is not None else s.awin_feed_limit
    if limit and limit > 0:
        selected = selected[:limit]
    log.info("Feeds retenus pour ingestion : %d / %d", len(selected), len(feeds))

    total_offers = 0
    skipped = 0
    shadow_raw = 0
    shadow_observations = 0
    shadow_quarantine = 0
    shadow_failures = 0
    # Déduplique uniquement les relevés identiques d'un même cycle. Les offres
    # elles-mêmes restent toutes lues : une variante linguistique peut enrichir
    # le libellé, mais elle ne doit pas compter comme une nouvelle observation.
    snapshot_cache: set[
        tuple[int, str, float, str | None, bool | None]
    ] = set()
    for f in selected:
        try:
            frows = await _download_feed_rows([f.feed_id], max_rows=max_rows)
        except Exception as exc:  # pragma: no cover - réseau/compte
            log.warning(
                "Feed indisponible (error_type=%s)",
                type(exc).__name__,
            )
            skipped += 1
            continue
        merchant_id, merchant_name = mid_to_merchant[f.advertiser_id]
        feed_observed_at = datetime.now(UTC).replace(tzinfo=None)
        n = 0
        # Un seul span par feed couvre les écritures en lot ; un span par ligne
        # rendrait les journaux inutilisables et augmenterait leur coût sans
        # apporter de nouvelle corrélation.
        async with traced_dependency("postgres", "write"):
            for row in frows:
                offer_id = await _upsert_offer(
                    session,
                    merchant_id,
                    row,
                    merchant_name=merchant_name,
                    snapshot_cache=snapshot_cache,
                )
                if s.observation_shadow_enabled:
                    # Le savepoint garantit qu'un défaut du shadow ne peut pas
                    # annuler l'upsert v1 ni contaminer la transaction principale.
                    try:
                        from app.observations.awin import capture_awin_row

                        async with session.begin_nested():
                            captured = await capture_awin_row(
                                session,
                                row,
                                feed_id=f.feed_id,
                                merchant_id=merchant_id,
                                merchant_name=merchant_name,
                                offer_id=offer_id,
                                sync_run_id=sync_run_id,
                                observed_at=feed_observed_at,
                            )
                        shadow_raw += int(captured.raw_created)
                        shadow_observations += captured.observations_created
                        shadow_quarantine += captured.quarantine_created
                    except Exception as exc:  # pragma: no cover - base réelle
                        shadow_failures += 1
                        log.warning(
                            "Shadow observation ignorée (error_type=%s)",
                            type(exc).__name__,
                        )
                n += 1
                if n % 200 == 0:  # commit périodique → progression visible dans /stats
                    await session.commit()
            await session.commit()
        total_offers += n
        log.info("Feed traité → %d offres", n)

    log.info("Ingestion terminée : %d feeds, %d offres, %d ignorés", len(selected), total_offers, skipped)
    return {
        "feeds": len(selected),
        "offers": total_offers,
        "skipped": skipped,
        "shadow": {
            "enabled": s.observation_shadow_enabled,
            "raw_sources": shadow_raw,
            "observations": shadow_observations,
            "quarantine": shadow_quarantine,
            "failures": shadow_failures,
        },
    }
