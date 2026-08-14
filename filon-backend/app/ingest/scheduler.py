"""Planification résiliente de la synchronisation Awin.

Le planificateur reste volontairement dans l'unique processus web Railway, mais
ne suppose plus qu'un conteneur survivra six heures. À chaque démarrage et à
chaque intervalle, il consulte le journal persistant puis ne déclenche une
synchronisation que lorsque les données sont réellement devenues périmées.
"""

from __future__ import annotations

import asyncio

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db import session as db
from app.services import catalog_sync

log = get_logger("scheduler")


async def _run_if_due(hours: int) -> None:
    async with db.session_scope() as session:
        if session is None:
            log.warning("Auto-sync ignoré : base de données indisponible")
            return
        state = await catalog_sync.health(session, interval_hours=hours)
        if state["status"] in {"fresh", "syncing"}:
            log.info("Auto-sync non nécessaire : état=%s âge=%s h", state["status"], state.get("age_hours"))
            return
        try:
            result = await catalog_sync.run_catalog_sync(session, trigger="scheduler")
            log.info("Auto-sync terminé : %s", result)
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # pragma: no cover - réseau ou compte réel
            # Le détail reste dans les logs internes ; le journal garde un code
            # neutre, sans risque de persister un secret Awin.
            log.warning("Auto-sync échoué (%s)", type(exc).__name__)


async def _loop(hours: int) -> None:
    interval = hours * 3600
    while True:
        await _run_if_due(hours)
        await asyncio.sleep(interval)


def maybe_start() -> asyncio.Task | None:
    """Démarre la surveillance si Awin, la base et l’intervalle sont configurés."""
    s = get_settings()
    if s.awin_auto_sync_hours and s.awin_auto_sync_hours > 0 and s.awin_feed_api_key and db.is_enabled():
        log.info("Surveillance catalogue activée : vérification toutes les %d h", s.awin_auto_sync_hours)
        return asyncio.create_task(_loop(s.awin_auto_sync_hours))
    return None
