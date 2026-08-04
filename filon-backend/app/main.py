"""Point d'entrée FastAPI de FILON AI."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.api.routes import advise, catalog, chat, health, stream
from app.api.middleware import RequestLoggingMiddleware, RateLimitMiddleware

log = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.debug)
    log.info("Démarrage %s v%s (env=%s)", settings.app_name, __version__, settings.env)

    # Crée les tables si une base est configurée (MVP : create_all).
    from app.db import session as db

    if db.is_enabled():
        try:
            await db.create_all()
            log.info("Schéma base de données prêt")
        except Exception as exc:  # pragma: no cover
            log.warning("Init base ignorée (%s)", exc)

    # Cron interne : rafraîchit le catalogue toutes les N heures (si activé).
    from app.ingest import scheduler

    sync_task = scheduler.maybe_start()

    yield

    if sync_task is not None:
        sync_task.cancel()
    log.info("Arrêt de %s", settings.app_name)


def create_app() -> FastAPI:
    settings = get_settings()

    # Schéma OpenAPI fermé hors développement. Il énumérait publiquement les onze
    # routes d'administration (`purge-offers`, `reset-price-history`, `rebuild-*`)
    # ainsi que `debug/feeds`. Chacune exige bien `ADMIN_SYNC_TOKEN` et répond 403
    # sans lui — vérifié en production — mais publier la carte des opérations
    # destructrices, leurs paramètres et le nom de l'en-tête attendu offre
    # gratuitement à un attaquant tout ce qu'il lui faut pour cibler ses essais.
    docs_publics = not settings.is_production
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description="Agent IA d'achat : comprendre le besoin, comparer, décider.",
        lifespan=lifespan,
        docs_url="/docs" if docs_publics else None,
        redoc_url="/redoc" if docs_publics else None,
        openapi_url="/openapi.json" if docs_publics else None,
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
        # Ne pas annoncer une documentation qui n'est pas servie.
        corps = {"service": settings.app_name, "version": __version__}
        if docs_publics:
            corps["docs"] = "/docs"
        return corps

    return app


app = create_app()
