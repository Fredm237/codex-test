"""Point d'entrée FastAPI de FILON AI."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.api.routes import advise, catalog, chat, health, stream
from app.api.middleware import RequestLoggingMiddleware, RateLimitMiddleware

log = get_logger("main")


async def _prepare_schema() -> None:
    """Prépare le schéma sans retarder la disponibilité HTTP.

    Sur une base déjà existante, ``create_all`` vérifie plusieurs métadonnées et
    migrations idempotentes. Cette étape peut attendre un verrou PostgreSQL sous
    forte charge ; elle ne doit jamais empêcher Railway de joindre ``/health``
    pendant la fenêtre de démarrage de la nouvelle réplique.
    """
    from app.db import session as db

    try:
        await db.create_all()
        log.info("Schéma base de données prêt")
    except asyncio.CancelledError:
        raise
    except Exception as exc:  # pragma: no cover - dépend de PostgreSQL
        log.warning("Init schéma ignorée (%s)", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.debug)
    log.info("Démarrage %s v%s (env=%s)", settings.app_name, __version__, settings.env)

    # La disponibilité du service et l'initialisation du schéma sont distinctes.
    # Le schéma est déjà présent en production ; le travail idempotent continue en
    # arrière-plan pour les environnements neufs sans bloquer le healthcheck.
    from app.db import session as db

    schema_task = asyncio.create_task(_prepare_schema()) if db.is_enabled() else None

    # Cron interne : rafraîchit le catalogue toutes les N heures (si activé).
    from app.ingest import scheduler

    sync_task = scheduler.maybe_start()

    yield

    if sync_task is not None:
        sync_task.cancel()
    if schema_task is not None and not schema_task.done():
        schema_task.cancel()
        try:
            await schema_task
        except asyncio.CancelledError:
            pass
    log.info("Arrêt de %s", settings.app_name)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description="Agent IA d'achat : comprendre le besoin, comparer, décider.",
        lifespan=lifespan,
    )
    # Middlewares — ordre d'exécution : RateLimit → Logging → CORS → Route
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(chat.router, prefix="/api")
    app.include_router(advise.router, prefix="/api")
    app.include_router(stream.router, prefix="/api")
    app.include_router(catalog.router, prefix="/api")

    @app.get("/")
    async def root() -> dict:
        return {"service": settings.app_name, "version": __version__, "docs": "/docs"}

    return app


app = create_app()
