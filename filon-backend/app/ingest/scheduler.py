"""Job autonome et mono-exécution de synchronisation catalogue.

Le processus web ne lance jamais ce module. Un ordonnanceur externe (par
exemple un Railway Cron) exécute ``python -m app.ingest.scheduler``. Le job
consulte le journal persistant, ne synchronise que si les données sont dues,
puis se termine avec un code observable.
"""

from __future__ import annotations

import asyncio

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.db import session as db
from app.services import catalog_sync

log = get_logger("scheduler")


async def _run_if_due(hours: int) -> str:
    async with db.session_scope() as session:
        if session is None:
            raise RuntimeError("catalog scheduler database session unavailable")
        state = await catalog_sync.health(session, interval_hours=hours)
        age_hours = state.get("age_hours")
        if state["status"] == "syncing" or (
            state["status"] == "fresh"
            and isinstance(age_hours, (int, float))
            and age_hours < hours
        ):
            log.info(
                "Synchronisation non nécessaire : état=%s âge=%s h",
                state["status"],
                state.get("age_hours"),
            )
            return str(state["status"])
        result = await catalog_sync.run_catalog_sync(session, trigger="scheduler")
        log.info("Synchronisation catalogue terminée : %s", result)
        if result.get("started") is False:
            return str(result.get("status") or "not_started")
        run = result.get("run")
        if not isinstance(run, dict) or run.get("status") != "succeeded":
            raise RuntimeError("catalog scheduler received an invalid sync outcome")
        return "succeeded"


async def run_once() -> str:
    """Valide la configuration et exécute au plus un cycle dû."""

    settings = get_settings()
    hours = settings.awin_auto_sync_hours
    if hours <= 0:
        raise RuntimeError("catalog scheduler requires AWIN_AUTO_SYNC_HOURS > 0")
    if not settings.awin_api_token:
        raise RuntimeError("catalog scheduler requires AWIN_API_TOKEN")
    if not settings.awin_feed_api_key:
        raise RuntimeError("catalog scheduler requires AWIN_FEED_API_KEY")
    if not db.is_enabled():
        raise RuntimeError("catalog scheduler requires DATABASE_URL")
    await db.prepare_schema()
    return await _run_if_due(hours)


def main() -> int:
    try:
        settings = get_settings()
        configure_logging(settings.debug)
        outcome = asyncio.run(run_once())
    except Exception as exc:  # pragma: no cover - dépendances réelles
        log.error("Job catalogue en échec (error_type=%s)", type(exc).__name__)
        return 1
    log.info("Job catalogue terminé : outcome=%s", outcome)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
