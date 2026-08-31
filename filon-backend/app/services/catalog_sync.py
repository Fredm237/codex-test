"""Orchestration durable des synchronisations catalogue.

Le collecteur Awin reste responsable du téléchargement et de l'upsert. Ce module
encadre chaque exécution avec un journal persistant : le produit peut donc dire
si le catalogue est frais, en cours de synchronisation ou dégradé, sans déduire
cet état depuis les seuls logs d'un conteneur éphémère.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, inspect, select, update
from sqlalchemy.exc import IntegrityError

from app.core.logging import get_logger
from app.db import models
from app.services import awin_catalog, catalog_grouping
from app.services.freshness import format_utc_timestamp

log = get_logger("catalog_sync")

# Une ingestion complète peut dépasser quatre heures. La preuve de vie est donc
# renouvelée pendant les écritures et le regroupement ; seul un heartbeat absent
# depuis cette durée autorise la récupération d'un cycle `running`.
_HEARTBEAT_TIMEOUT = timedelta(minutes=15)


def _now() -> datetime:
    """Les dates historiques FILON sont UTC naïves ; conserve ce contrat."""
    return datetime.now(UTC).replace(tzinfo=None)


def _summary(run: models.CatalogSyncRun) -> dict[str, Any]:
    return {
        "id": run.id,
        "resumed_from_run_id": run.resumed_from_run_id,
        "trigger": run.trigger,
        "status": run.status,
        "started_at": format_utc_timestamp(run.started_at),
        "heartbeat_at": format_utc_timestamp(run.heartbeat_at),
        "finished_at": format_utc_timestamp(run.finished_at),
        "merchants": run.merchants_count or 0,
        "feeds": run.feeds_count or 0,
        "offers": run.offers_count or 0,
        "skipped_feeds": run.skipped_feeds or 0,
        # Le motif est un code neutre : aucune URL Awin, exception ou secret n'est
        # conservé dans la base ni renvoyé à un client.
        "failure_reason": run.failure_reason,
    }


async def _latest(session, *, status: str | None = None) -> models.CatalogSyncRun | None:
    stmt = select(models.CatalogSyncRun).order_by(models.CatalogSyncRun.started_at.desc())
    if status:
        stmt = stmt.where(models.CatalogSyncRun.status == status)
    return (await session.execute(stmt.limit(1))).scalar_one_or_none()


async def start_run(session, *, trigger: str) -> models.CatalogSyncRun | None:
    """Crée un cycle ou un successeur reprenable d'un cycle abandonné.

    Un index partiel unique protège aussi le cas où deux processus tenteraient de
    démarrer simultanément. Un cycle dont la preuve de vie a expiré devient
    terminal ``interrupted`` ; son successeur conserve explicitement sa filiation
    et reprend les checkpoints sans faire passer l'ancien cycle pour réussi.
    """
    now = _now()
    interrupted = await session.execute(
        update(models.CatalogSyncRun)
        .where(
            models.CatalogSyncRun.status == "running",
            func.coalesce(
                models.CatalogSyncRun.heartbeat_at,
                models.CatalogSyncRun.started_at,
            )
            < now - _HEARTBEAT_TIMEOUT,
        )
        .values(
            status="interrupted",
            heartbeat_at=now,
            finished_at=now,
            failure_reason="interrupted",
        )
        .returning(models.CatalogSyncRun.id)
    )
    interrupted_id = interrupted.scalar_one_or_none()

    run = models.CatalogSyncRun(
        resumed_from_run_id=interrupted_id,
        trigger=trigger,
        status="running",
        started_at=now,
        heartbeat_at=now,
    )
    session.add(run)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        log.info("Synchronisation catalogue déjà active : nouvelle demande ignorée")
        return None
    await session.refresh(run)
    if interrupted_id is not None:
        log.warning(
            "Synchronisation catalogue reprise (run_id=%s resumed_from=%s)",
            run.id,
            interrupted_id,
        )
    return run


async def touch_run(session, run_id: int) -> datetime:
    """Renouvelle la preuve de vie, sans committer la transaction appelante.

    Une mise à jour absente signifie que le processus a perdu la propriété du
    cycle. Continuer écrirait alors hors du journal mono-exécution : l'appelant
    doit échouer fermé.
    """

    now = _now()
    result = await session.execute(
        update(models.CatalogSyncRun)
        .where(
            models.CatalogSyncRun.id == run_id,
            models.CatalogSyncRun.status == "running",
        )
        .values(heartbeat_at=now)
    )
    if result.rowcount != 1:
        raise RuntimeError("catalog sync run lost ownership")
    return now


async def finish_run(
    session,
    run: models.CatalogSyncRun,
    *,
    status: str,
    merchants: int = 0,
    feeds: int = 0,
    offers: int = 0,
    skipped_feeds: int = 0,
    failure_reason: str | None = None,
) -> dict[str, Any]:
    now = _now()
    run_id = inspect(run).identity[0]
    result = await session.execute(
        update(models.CatalogSyncRun)
        .where(
            models.CatalogSyncRun.id == run_id,
            models.CatalogSyncRun.status == "running",
        )
        .values(
            status=status,
            heartbeat_at=now,
            finished_at=now,
            merchants_count=merchants,
            feeds_count=feeds,
            offers_count=offers,
            skipped_feeds=skipped_feeds,
            failure_reason=failure_reason,
        )
    )
    if result.rowcount != 1:
        await session.rollback()
        raise RuntimeError("catalog sync run lost ownership")
    await session.commit()
    await session.refresh(run)
    return _summary(run)


def _degraded_reason(merchants: int, ingest: dict[str, Any]) -> str | None:
    """Retourne un code neutre lorsqu'un cycle n'a pas rafraîchi tout son scope."""

    feeds = int(ingest.get("feeds") or 0)
    offers = int(ingest.get("offers") or 0)
    skipped = int(ingest.get("skipped") or 0)
    shadow_failures = int((ingest.get("shadow") or {}).get("failures") or 0)
    if merchants <= 0:
        return "no_merchants"
    if feeds <= 0:
        return "no_feeds"
    if skipped >= feeds:
        return "all_feeds_skipped"
    if offers <= 0:
        return "no_offers"
    if skipped > 0:
        return "feeds_skipped"
    if shadow_failures > 0:
        return "shadow_failures"
    return None


async def run_catalog_sync(
    session,
    *,
    trigger: str,
    limit_override: int | None = None,
) -> dict[str, Any]:
    """Synchronise marchands, feeds et regroupements dans un cycle journalisé."""
    if session is None:
        return {"started": False, "status": "unavailable"}

    run = await start_run(session, trigger=trigger)
    if run is None:
        return {"started": False, "status": "already_running"}
    run_id = inspect(run).identity[0]

    async def progress() -> None:
        await touch_run(session, run_id)

    try:
        merchants = await awin_catalog.sync_merchants(session)
        await progress()
        await session.commit()
        ingest = await awin_catalog.ingest_feeds(
            session,
            limit_override=limit_override,
            sync_run_id=run_id,
            resume_from_run_id=run.resumed_from_run_id,
            progress=progress,
        )
        await progress()
        await session.commit()
        grouping = await catalog_grouping.rebuild_products(
            session,
            progress=progress,
        )
        degraded_reason = _degraded_reason(merchants, ingest)
        completed = await finish_run(
            session,
            run,
            status="degraded" if degraded_reason else "succeeded",
            merchants=merchants,
            feeds=int(ingest.get("feeds") or 0),
            offers=int(ingest.get("offers") or 0),
            skipped_feeds=int(ingest.get("skipped") or 0),
            failure_reason=degraded_reason,
        )
        completed["grouping"] = grouping
        if degraded_reason:
            log.warning(
                "Synchronisation catalogue dégradée (reason=%s) : %s",
                degraded_reason,
                completed,
            )
        else:
            log.info("Synchronisation catalogue réussie : %s", completed)
        return {"started": True, "run": completed}
    except Exception as exc:  # pragma: no cover - réseau, compte ou base réelle
        await session.rollback()
        failed = await finish_run(session, run, status="failed", failure_reason="sync_failed")
        log.warning("Synchronisation catalogue échouée (%s) : %s", type(exc).__name__, failed)
        raise


async def health(session, *, interval_hours: int) -> dict[str, Any]:
    """Retourne l'état de fraîcheur à partir des cycles réellement terminés."""
    if session is None:
        return {"status": "unavailable", "last_success": None, "age_hours": None}

    now = _now()
    active = await _latest(session, status="running")
    success = await _latest(session, status="succeeded")
    latest = await _latest(session)
    freshness_limit = max(1, interval_hours) * 2

    if active is not None:
        active_age_hours = max(0, int((now - active.started_at).total_seconds() // 3600))
        heartbeat_at = active.heartbeat_at or active.started_at
        heartbeat_age_seconds = max(0, int((now - heartbeat_at).total_seconds()))
        # La durée totale n'est pas un signal d'abandon : les catalogues réels
        # dépassent parfois quatre heures. Seule une preuve de vie expirée rend
        # le verrou récupérable.
        if now - heartbeat_at >= _HEARTBEAT_TIMEOUT:
            return {
                "status": "interrupted",
                "last_success": _summary(success) if success else None,
                "active_run": _summary(active),
                "age_hours": active_age_hours,
                "heartbeat_age_seconds": heartbeat_age_seconds,
                "recovery_required": True,
            }
        return {
            "status": "syncing",
            "last_success": _summary(success) if success else None,
            "active_run": _summary(active),
            "age_hours": active_age_hours,
            "heartbeat_age_seconds": heartbeat_age_seconds,
        }
    if success is None:
        # Au déploiement de cette table, les cycles passés n'ont pas de journal.
        # Les relevés de prix existants évitent donc de déclencher une ingestion
        # complète simplement parce que l'observabilité vient d'être ajoutée.
        last_reading = await session.scalar(select(func.max(models.PriceSnapshot.captured_at)))
        if last_reading is not None:
            age_hours = max(0, int((now - last_reading).total_seconds() // 3600))
            return {
                "status": "fresh" if age_hours <= freshness_limit else "stale",
                "last_success": None,
                "last_reading": format_utc_timestamp(last_reading),
                "age_hours": age_hours,
                "freshness_limit_hours": freshness_limit,
                "source": "price_readings",
            }
        return {
            "status": (
                "degraded"
                if latest and latest.status in {"failed", "degraded"}
                else "unknown"
            ),
            "last_success": None,
            "age_hours": None,
        }

    age_hours = max(0, int((now - (success.finished_at or success.started_at)).total_seconds() // 3600))
    state = "fresh" if age_hours <= freshness_limit else "stale"
    if (
        latest
        and latest.status in {"failed", "degraded"}
        and latest.started_at > success.started_at
    ):
        state = "degraded"
    return {
        "status": state,
        "last_success": _summary(success),
        "age_hours": age_hours,
        "freshness_limit_hours": freshness_limit,
    }
