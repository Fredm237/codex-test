"""Synchronisation Awin en ligne de commande — à lancer sur Railway.

Usage :
    python -m app.ingest.awin_sync              # marchands + feeds
    python -m app.ingest.awin_sync merchants    # marchands uniquement
    python -m app.ingest.awin_sync feeds        # feeds uniquement

Prérequis (variables d'environnement sur Railway) :
    DATABASE_URL        base PostgreSQL
    AWIN_API_TOKEN      token API Publisher (marchands)
    AWIN_FEED_API_KEY   clé de feed produits (feeds ; optionnelle)

Se planifie via un cron Railway (ex. toutes les 6 h). Aucune donnée n'est
inventée : sans clé/marchand, l'étape correspondante est simplement ignorée.
"""

from __future__ import annotations

import asyncio
import sys

from app.core.logging import configure_logging, get_logger
from app.db import session as db
from app.services import awin_catalog

log = get_logger("awin_sync")


async def _run(step: str) -> None:
    configure_logging(True)
    if not db.is_enabled():
        log.error("DATABASE_URL absent → impossible de synchroniser le catalogue")
        return
    await db.create_all()

    async with db.session_scope() as session:
        if session is None:
            log.error("Session base indisponible")
            return
        if step in ("all", "merchants"):
            n = await awin_catalog.sync_merchants(session)
            log.info("→ %d marchands synchronisés", n)
        if step in ("all", "feeds"):
            summary = await awin_catalog.ingest_feeds(session)
            log.info("→ feeds=%s offres=%s", summary["feeds"], summary["offers"])


def main() -> None:
    step = sys.argv[1].lower() if len(sys.argv) > 1 else "all"
    if step not in ("all", "merchants", "feeds"):
        print(__doc__)
        raise SystemExit(2)
    asyncio.run(_run(step))


if __name__ == "__main__":
    main()
