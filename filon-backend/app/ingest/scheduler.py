"""Cron interne : rafraîchit le catalogue Awin toutes les N heures.

Activé par AWIN_AUTO_SYNC_HOURS (> 0) + AWIN_FEED_API_KEY + base de données.
Tourne dans le process web (une seule réplique), en tâche de fond asyncio.
Aucun service Railway supplémentaire à configurer : il suffit d'une variable.
"""

from __future__ import annotations

import asyncio

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db import session as db
from app.services import awin_catalog, catalog_grouping

log = get_logger("scheduler")


async def _loop(hours: int) -> None:
    interval = hours * 3600
    while True:
        # On attend d'abord l'intervalle : évite de relancer une grosse ingestion
        # à chaque redéploiement.
        await asyncio.sleep(interval)
        try:
            async with db.session_scope() as session:
                if session is None:
                    continue
                await awin_catalog.sync_merchants(session)
                summary = await awin_catalog.ingest_feeds(session)
                # Les offres viennent de changer : les produits regroupés
                # doivent suivre, sinon les fiches multi-marchands se périment.
                grouping = await catalog_grouping.rebuild_products(session)
            log.info("Auto-sync terminé : %s | regroupement : %s", summary, grouping)
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # pragma: no cover - réseau/compte
            log.warning("Auto-sync échoué (%s)", exc)


def maybe_start() -> asyncio.Task | None:
    """Démarre le cron si activé et configuré. Retourne la tâche (ou None)."""
    s = get_settings()
    if s.awin_auto_sync_hours and s.awin_auto_sync_hours > 0 and s.awin_feed_api_key and db.is_enabled():
        log.info("Cron catalogue activé : synchro toutes les %d h", s.awin_auto_sync_hours)
        return asyncio.create_task(_loop(s.awin_auto_sync_hours))
    return None
