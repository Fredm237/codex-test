"""Environnement Alembic async de FILON.

La cible est fournie par ``ALEMBIC_DATABASE_URL`` (tests et opérations
ponctuelles) ou, à défaut, par ``DATABASE_URL``. Aucune base implicite n'est
utilisée : une commande de migration ne doit jamais viser une cible par hasard.
"""

from __future__ import annotations

import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool, text
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.db.base import Base
from app.db import models as core_models  # noqa: F401
from app.intelligence import models as intelligence_models  # noqa: F401
from app.observations import models as observation_models  # noqa: F401
from app.product_graph import models as product_graph_models  # noqa: F401
from app.offer_graph import models as offer_graph_models  # noqa: F401
from app.merchant_intelligence import models as merchant_intelligence_models  # noqa: F401


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Index PostgreSQL explicitement gérés par la migration de baseline. Ils ne
# figurent pas dans les modèles afin que ``create_all`` des tests SQLite ne crée
# pas de faux index B-tree portant un nom trigramme.
MIGRATION_ONLY_INDEXES = {
    "ix_offers_brand_trgm",
    "ix_offers_name_trgm",
}

# Verrou de session PostgreSQL propre à FILON. Il rend une erreur explicite si
# deux releases tentent de migrer la même base, au lieu de laisser deux suites
# Alembic concurrentes modifier le schéma.
MIGRATION_LOCK_ID = 0x46494C4F4E


def _database_url() -> str:
    url = os.getenv("ALEMBIC_DATABASE_URL") or os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "Définissez ALEMBIC_DATABASE_URL ou DATABASE_URL avant d'exécuter Alembic."
        )
    if url.startswith("postgres://"):
        url = "postgresql://" + url.removeprefix("postgres://")
    if url.startswith("postgresql://"):
        url = "postgresql+asyncpg://" + url.removeprefix("postgresql://")
    if url.startswith("sqlite://"):
        url = "sqlite+aiosqlite://" + url.removeprefix("sqlite://")
    return url


def _configure(connection=None, *, url: str | None = None) -> None:
    def include_object(_object, name, type_, _reflected, _compare_to) -> bool:
        return not (type_ == "index" and name in MIGRATION_ONLY_INDEXES)

    context.configure(
        connection=connection,
        url=url,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        include_object=include_object,
        render_as_batch=(url or str(connection.engine.url)).startswith("sqlite"),
    )


def run_migrations_offline() -> None:
    _configure(url=_database_url())
    with context.begin_transaction():
        context.run_migrations()


def _run_migrations(connection) -> None:
    _configure(connection)
    with context.begin_transaction():
        context.run_migrations()


async def _acquire_migration_lock(connection) -> bool:
    if connection.dialect.name != "postgresql":
        return False
    acquired = await connection.scalar(
        text("SELECT pg_try_advisory_lock(:lock_id)"),
        {"lock_id": MIGRATION_LOCK_ID},
    )
    # Le verrou est de session ; clore l'autobegin permet ensuite à Alembic de
    # gérer sa propre transaction sans libérer le verrou.
    await connection.commit()
    if acquired is not True:
        raise RuntimeError(
            "Une autre release FILON détient déjà le verrou de migration."
        )
    return True


async def _release_migration_lock(connection) -> None:
    if connection.in_transaction():
        await connection.rollback()
    await connection.execute(
        text("SELECT pg_advisory_unlock(:lock_id)"),
        {"lock_id": MIGRATION_LOCK_ID},
    )
    await connection.commit()


async def _run_async_migrations() -> None:
    section = config.get_section(config.config_ini_section) or {}
    section["sqlalchemy.url"] = _database_url()
    connectable = async_engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        locked = False
        try:
            locked = await _acquire_migration_lock(connection)
            await connection.run_sync(_run_migrations)
        finally:
            if locked:
                await _release_migration_lock(connection)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(_run_async_migrations())
