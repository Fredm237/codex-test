"""Session SQLAlchemy async, optionnelle.

Si DATABASE_URL est absent, l'application démarre quand même (la persistance
est simplement désactivée). Permet un premier run sans Postgres.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from app.core.config import get_settings
from app.core.logging import get_logger

log = get_logger("db")

_engine = None
_sessionmaker = None


def _normalize_async_url(url: str) -> str:
    """Force le driver async asyncpg.

    Railway (et la plupart des hébergeurs) exposent DATABASE_URL au format
    `postgres://` ou `postgresql://` (driver synchrone). Le moteur async a
    besoin de `postgresql+asyncpg://` — on le convertit ici pour que la variable
    Railway fonctionne sans réglage particulier.
    """
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+asyncpg://" + url[len("postgresql://"):]
    return url


def _init() -> None:
    global _engine, _sessionmaker
    if _engine is not None:
        return
    url = get_settings().database_url
    if not url:
        log.info("DATABASE_URL absent → persistance désactivée")
        return
    url = _normalize_async_url(url)
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    _engine = create_async_engine(url, pool_pre_ping=True)
    _sessionmaker = async_sessionmaker(_engine, expire_on_commit=False)


def is_enabled() -> bool:
    _init()
    return _sessionmaker is not None


async def create_all() -> None:
    _init()
    if _engine is None:
        return
    from app.db.base import Base

    # Importe les modèles pour qu'ils soient enregistrés dans Base.metadata
    # avant create_all (sinon aucune table n'est créée).
    from app.db import models  # noqa: F401

    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncIterator:
    _init()
    if _sessionmaker is None:
        yield None
        return
    async with _sessionmaker() as session:
        yield session


class session_scope:
    """Context manager async pour obtenir une session hors requête HTTP
    (scripts d'ingestion, tâches planifiées). Rend `None` si la base est absente.
    """

    def __init__(self) -> None:
        self._cm = None

    async def __aenter__(self):
        _init()
        if _sessionmaker is None:
            return None
        self._cm = _sessionmaker()
        return await self._cm.__aenter__()

    async def __aexit__(self, *exc) -> None:
        if self._cm is not None:
            await self._cm.__aexit__(*exc)
