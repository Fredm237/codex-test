"""Point d'entrée FastAPI de FILON AI."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis

from app import __version__
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.api.routes import advise, catalog, chat, health, intelligence, stream
from app.api.middleware import RequestLoggingMiddleware, RateLimitMiddleware

log = get_logger("main")


async def _prepare_schema() -> None:
    """Valide le schéma sans retarder la disponibilité HTTP.

    En mode normal, aucune DDL n'est exécutée : la révision Alembic déployée est
    seulement contrôlée. Le mode historique ``legacy`` n'est pas une stratégie
    de rollback de production et reste interdit en staging/production.
    """
    from app.db import session as db

    try:
        await db.prepare_schema()
        log.info("Révision du schéma base de données validée")
    except asyncio.CancelledError:
        raise
    except Exception as exc:  # pragma: no cover - dépend de PostgreSQL
        log.error("Validation du schéma en échec (error_type=%s)", type(exc).__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.debug)
    log.info("Démarrage %s v%s (env=%s)", settings.app_name, __version__, settings.env)

    # La disponibilité du service et la validation du schéma sont distinctes.
    # Les migrations sont appliquées par une étape de déploiement explicite.
    from app.db import session as db

    schema_task = asyncio.create_task(_prepare_schema()) if db.is_enabled() else None

    try:
        yield
    finally:
        if schema_task is not None and not schema_task.done():
            schema_task.cancel()
            try:
                await schema_task
            except asyncio.CancelledError:
                pass
        rate_limit_client = getattr(
            app.state,
            "rate_limit_redis_client",
            None,
        )
        if rate_limit_client is not None:
            await rate_limit_client.aclose()
        log.info("Arrêt de %s", settings.app_name)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description="Agent IA d'achat : comprendre le besoin, comparer, décider.",
        lifespan=lifespan,
    )
    rate_limit_options: dict[str, object] = {}
    if settings.rate_limit_identity_source == "railway":
        rate_limit_options["trusted_client_header"] = "x-real-ip"
    if settings.rate_limit_backend == "redis":
        rate_limit_client = Redis.from_url(
            settings.redis_url or "",
            socket_connect_timeout=settings.rate_limit_redis_timeout_seconds,
            socket_timeout=settings.rate_limit_redis_timeout_seconds,
            retry_on_timeout=False,
        )
        app.state.rate_limit_redis_client = rate_limit_client
        rate_limit_options.update(
            {
                "distributed_client": rate_limit_client,
                "identity_secret": (
                    settings.rate_limit_identity_secret or ""
                ).encode("ascii"),
            }
        )

    # Starlette exécute le dernier middleware ajouté en premier : CORS reste
    # extérieur, puis Logging corrèle aussi les 429 produits par RateLimit.
    app.add_middleware(RateLimitMiddleware, **rate_limit_options)
    app.add_middleware(RequestLoggingMiddleware)
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
    # Couche additive : le statut Intelligence ne modifie aucun contrat Core.
    app.include_router(intelligence.router, prefix="/api")

    @app.get("/")
    async def root() -> dict:
        return {"service": settings.app_name, "version": __version__, "docs": "/docs"}

    return app


app = create_app()
