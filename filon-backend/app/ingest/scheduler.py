"""Job autonome et mono-exécution de synchronisation catalogue.

Le processus web ne lance jamais ce module. Un ordonnanceur externe (par
exemple un Railway Cron) exécute ``python -m app.ingest.scheduler``. Le job
consulte le journal persistant, ne synchronise que si les données sont dues,
puis se termine avec un code observable.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Sequence
from typing import Any

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.db import session as db
from app.services import catalog_sync

log = get_logger("scheduler")

_MAX_ROWS_PER_FEED = 100_000
_MAX_DOWNLOAD_BYTES = 256 * 1024 * 1024
_MAX_DECOMPRESSED_BYTES = 512 * 1024 * 1024


def _validated_interval() -> int:
    """Valide le contrat borné du job sans exposer ses secrets."""

    settings = get_settings()
    hours = settings.awin_auto_sync_hours
    if hours <= 0:
        raise RuntimeError("catalog scheduler requires AWIN_AUTO_SYNC_HOURS > 0")
    if not settings.awin_api_token:
        raise RuntimeError("catalog scheduler requires AWIN_API_TOKEN")
    if not settings.awin_feed_api_key:
        raise RuntimeError("catalog scheduler requires AWIN_FEED_API_KEY")
    if settings.database_schema_mode != "alembic":
        raise RuntimeError("catalog scheduler requires DATABASE_SCHEMA_MODE=alembic")
    if not 0 < settings.awin_max_rows_per_feed <= _MAX_ROWS_PER_FEED:
        raise RuntimeError("catalog scheduler rows-per-feed bound is unsafe")
    if settings.awin_max_download_bytes > _MAX_DOWNLOAD_BYTES:
        raise RuntimeError("catalog scheduler download bound is unsafe")
    if settings.awin_max_decompressed_bytes > _MAX_DECOMPRESSED_BYTES:
        raise RuntimeError("catalog scheduler decompressed bound is unsafe")
    if not db.is_enabled():
        raise RuntimeError("catalog scheduler requires DATABASE_URL")
    return hours


def _is_due(state: dict[str, Any], *, hours: int) -> bool:
    age_hours = state.get("age_hours")
    return not (
        state.get("status") == "syncing"
        or (
            state.get("status") == "fresh"
            and isinstance(age_hours, (int, float))
            and age_hours < hours
        )
    )


async def preflight() -> dict[str, object]:
    """Qualifie le job et son schéma sans déclencher d'écriture."""

    hours = _validated_interval()
    await db.prepare_schema()
    async with db.session_scope() as session:
        if session is None:
            raise RuntimeError("catalog scheduler database session unavailable")
        state = await catalog_sync.health(session, interval_hours=hours)
    return {
        "catalog_state": str(state.get("status") or "unknown"),
        "due": _is_due(state, hours=hours),
        "interval_hours": hours,
        "schema_revision": db.CURRENT_SCHEMA_REVISION,
        "status": "ready",
    }


async def _run_if_due(hours: int, *, stop_after_current_feed: bool = False) -> str:
    async with db.session_scope() as session:
        if session is None:
            raise RuntimeError("catalog scheduler database session unavailable")
        state = await catalog_sync.health(session, interval_hours=hours)
        if not _is_due(state, hours=hours):
            log.info(
                "Synchronisation non nécessaire : état=%s âge=%s h",
                state["status"],
                state.get("age_hours"),
            )
            return str(state["status"])
        result = await catalog_sync.run_catalog_sync(
            session,
            trigger="scheduler",
            stop_after_current_feed=stop_after_current_feed,
        )
        log.info("Synchronisation catalogue terminée : %s", result)
        if result.get("started") is False:
            return str(result.get("status") or "not_started")
        run = result.get("run")
        if not isinstance(run, dict) or run.get("status") != "succeeded":
            raise RuntimeError("catalog scheduler received an invalid sync outcome")
        return "succeeded"


async def run_once(*, stop_after_current_feed: bool = False) -> str:
    """Valide la configuration et exécute au plus un cycle dû."""

    hours = _validated_interval()
    await db.prepare_schema()
    return await _run_if_due(
        hours,
        stop_after_current_feed=stop_after_current_feed,
    )


async def interrupt_stale_once() -> dict[str, object]:
    """Clôt au plus un cycle stale sans lancer de successeur catalogue."""

    hours = _validated_interval()
    await db.prepare_schema()
    async with db.session_scope() as session:
        if session is None:
            raise RuntimeError("catalog scheduler database session unavailable")
        interrupted = await catalog_sync.interrupt_stale_run(session)
    return {
        "status": "interrupted" if interrupted is not None else "not_stale",
        "run_id": interrupted.get("id") if interrupted is not None else None,
        "interval_hours": hours,
        "schema_revision": db.CURRENT_SCHEMA_REVISION,
        "successor_started": False,
    }


def main(argv: Sequence[str] = ()) -> int:
    arguments = tuple(argv)
    if arguments not in {
        (),
        ("--check",),
        ("--interrupt-stale",),
        ("--stop-after-current-feed",),
    }:
        log.error(
            "Usage: python -m app.ingest.scheduler "
            "[--check|--interrupt-stale|--stop-after-current-feed]"
        )
        return 2
    try:
        settings = get_settings()
        configure_logging(settings.debug)
        if arguments == ("--check",):
            receipt = asyncio.run(preflight())
            print(json.dumps(receipt, separators=(",", ":"), sort_keys=True))
            return 0
        if arguments == ("--interrupt-stale",):
            receipt = asyncio.run(interrupt_stale_once())
            print(json.dumps(receipt, separators=(",", ":"), sort_keys=True))
            return 0
        outcome = asyncio.run(
            run_once(
                stop_after_current_feed=arguments
                == ("--stop-after-current-feed",),
            )
        )
    except Exception as exc:  # pragma: no cover - dépendances réelles
        log.error("Job catalogue en échec (error_type=%s)", type(exc).__name__)
        return 1
    log.info("Job catalogue terminé : outcome=%s", outcome)
    return 0


if __name__ == "__main__":
    import sys

    raise SystemExit(main(tuple(sys.argv[1:])))
