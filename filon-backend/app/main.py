"""Point d'entrée FastAPI de FILON AI."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.api.routes import advise, chat, health, stream

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

    yield
    log.info("Arrêt de %s", settings.app_name)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description="Agent IA d'achat : comprendre le besoin, comparer, décider.",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        # Le frontend n'envoie aucun cookie/credential : on garde credentials=False,
        # ce qui rend "*" pleinement valide et évite tout blocage CORS navigateur,
        # quelle que soit la valeur de CORS_ORIGINS.
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(chat.router, prefix="/api")
    app.include_router(advise.router, prefix="/api")
    app.include_router(stream.router, prefix="/api")

    @app.get("/")
    async def root() -> dict:
        return {"service": settings.app_name, "version": __version__, "docs": "/docs"}

    return app


app = create_app()
