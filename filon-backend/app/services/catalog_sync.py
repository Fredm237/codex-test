"""Orchestration durable des synchronisations catalogue.

Le collecteur Awin reste responsable du téléchargement et de l'upsert. Ce module
encadre chaque exécution avec un journal persistant : le produit peut donc dire
si le catalogue est frais, en cours de synchronisation ou dégradé, sans déduire
cet état depuis les seuls logs d'un conteneur éphémère.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError

from app.core.logging import get_logger
from app.db import models
from app.services import awin_catalog, catalog_grouping

log = get_logger("catalog_sync")

# Une ingestion complète prend du temps. Au-delà de cette durée, un état
# `running` sans processus vivant provient d'un redéploiement ou d'une panne et
# doit cesser de bloquer les cycles suivants.
_INTERRUPTED_AFTER = timedelta(hours=4)


def _now() -> datetime:
    """Les dates historiques FILON sont UTC naïves ; conserve ce contrat."""
    return datetime.now(UTC).replace(tzinfo=None)


def _summary(run: models.CatalogSyncRun) -> dict[str, Any]:
    return {
        "id": run.id,
        "trigger": run.trigger,
        "status": run.status,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
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
    """Crée un cycle, ou retourne ``None`` lorsqu'un cycle sain est déjà actif.

    Un index partiel unique protège aussi le cas où deux processus tenteraient de
    démarrer simultanément. Les cycles abandonnés sont explicitement marqués avant
    de laisser une nouvelle tentative repartir.
    """
    now = _now()
    await session.execute(
        update(models.CatalogSyncRun)
        .where(
            models.CatalogSyncRun.status == "running",
            models.CatalogSyncRun.started_at < now - _INTERRUPTED_AFTER,
        )
        .values(status="interrupted", finished_at=now, failure_reason="interrupted")
    )
    await session.commit()

    run = models.CatalogSyncRun(trigger=trigger, status="running", started_at=now)
    session.add(run)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        log.info("Synchronisation catalogue déjà active : nouvelle demande ignorée")
        return None
    await session.refresh(run)
    return run


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
    run.status = status
    run.finished_at = _now()
    run.merchants_count = merchants
    run.feeds_count = feeds
    run.offers_count = offers
    run.skipped_feeds = skipped_feeds
    run.failure_reason = failure_reason
    await session.commit()
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

    try:
        merchants = await awin_catalog.sync_merchants(session)
        ingest = await awin_catalog.ingest_feeds(
            session,
            limit_override=limit_override,
            sync_run_id=run.id,
        )
        grouping = await catalog_grouping.rebuild_products(session)
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
        # Un cycle réellement actif reste visible comme tel. Au-delà de quatre
        # heures, un verrou `running` est traité comme interrompu : le prochain
        # passage du planificateur appelle `start_run()`, qui le marque alors
        # durablement avant de lancer une tentative neuve.
        if now - active.started_at >= _INTERRUPTED_AFTER:
            return {
                "status": "interrupted",
                "last_success": _summary(success) if success else None,
                "active_run": _summary(active),
                "age_hours": active_age_hours,
                "recovery_required": True,
            }
        return {
            "status": "syncing",
            "last_success": _summary(success) if success else None,
            "active_run": _summary(active),
            "age_hours": active_age_hours,
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
                "last_reading": last_reading.isoformat(),
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
