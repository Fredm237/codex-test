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


def _init() -> None:
    global _engine, _sessionmaker
    if _engine is not None:
        return
    url = get_settings().database_url
    if not url:
        log.info("DATABASE_URL absent → persistance désactivée")
        return
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

    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncIterator:
    _init()
    if _sessionmaker is None:
        yield None
        return
    async with _sessionmaker() as session:
        yield session
