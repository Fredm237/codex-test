"""Preuve PostgreSQL réelle du contrat Alembic de production.

Le test est opt-in localement et obligatoire en CI via ``TEST_POSTGRES_URL``.
Il refuse toute cible distante ou dont le nom n'est pas explicitement une base
FILON jetable de test avant de réinitialiser son schéma public.
"""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


BACKEND_ROOT = Path(__file__).resolve().parents[1]
HEAD_REVISION = "3a7f9c2e5b61"
MIGRATION_LOCK_ID = 0x46494C4F4E


def _test_database_url() -> str:
    url = os.getenv("TEST_POSTGRES_URL", "").strip()
    if not url:
        pytest.skip("TEST_POSTGRES_URL absent: preuve PostgreSQL réservée à la CI")
    parsed = urlsplit(url)
    database = parsed.path.removeprefix("/")
    if parsed.scheme not in {"postgresql", "postgresql+asyncpg"}:
        pytest.fail("TEST_POSTGRES_URL doit utiliser PostgreSQL")
    if parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        pytest.fail("TEST_POSTGRES_URL doit cibler exclusivement le loopback")
    if database != "filon_test":
        pytest.fail("TEST_POSTGRES_URL doit cibler exactement la base filon_test")
    return url


def _run_alembic(url: str, *arguments: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["ALEMBIC_DATABASE_URL"] = url
    return subprocess.run(
        [sys.executable, "-m", "alembic", *arguments],
        cwd=BACKEND_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


async def _reset_public_schema(url: str) -> None:
    engine = create_async_engine(url)
    try:
        async with engine.begin() as connection:
            await connection.execute(text("DROP SCHEMA public CASCADE"))
            await connection.execute(text("CREATE SCHEMA public"))
    finally:
        await engine.dispose()


async def test_postgresql_upgrade_drift_extensions_indexes_and_lock() -> None:
    url = _test_database_url()
    await _reset_public_schema(url)

    upgrade = await asyncio.to_thread(_run_alembic, url, "upgrade", "head")
    assert upgrade.returncode == 0, "Alembic PostgreSQL upgrade head a échoué"

    engine = create_async_engine(url)
    try:
        async with engine.connect() as connection:
            revision = await connection.scalar(
                text("SELECT version_num FROM alembic_version")
            )
            extension = await connection.scalar(
                text("SELECT extname FROM pg_extension WHERE extname = 'pg_trgm'")
            )
            currency_nullable = await connection.scalar(
                text(
                    "SELECT is_nullable FROM information_schema.columns "
                    "WHERE table_schema = 'public' "
                    "AND table_name = 'price_snapshots' "
                    "AND column_name = 'currency'"
                )
            )
            indexes = {
                row.name: row.definition
                for row in (
                    await connection.execute(
                        text(
                            "SELECT indexname AS name, indexdef AS definition "
                            "FROM pg_indexes WHERE schemaname = 'public' "
                            "AND indexname IN "
                            "('ix_offers_name_trgm', 'ix_offers_brand_trgm')"
                        )
                    )
                )
            }

        assert revision == HEAD_REVISION
        assert extension == "pg_trgm"
        assert currency_nullable == "YES"
        assert set(indexes) == {"ix_offers_name_trgm", "ix_offers_brand_trgm"}
        assert all("USING gin" in definition for definition in indexes.values())

        drift = await asyncio.to_thread(_run_alembic, url, "check")
        assert drift.returncode == 0, "Alembic PostgreSQL check a détecté un drift"

        async with engine.connect() as lock_owner:
            acquired = await lock_owner.scalar(
                text("SELECT pg_try_advisory_lock(:lock_id)"),
                {"lock_id": MIGRATION_LOCK_ID},
            )
            await lock_owner.commit()
            assert acquired is True
            try:
                concurrent = await asyncio.to_thread(
                    _run_alembic,
                    url,
                    "upgrade",
                    "head",
                )
                combined_output = f"{concurrent.stdout}\n{concurrent.stderr}"
                assert concurrent.returncode != 0
                assert "Une autre release FILON" in combined_output
            finally:
                await lock_owner.execute(
                    text("SELECT pg_advisory_unlock(:lock_id)"),
                    {"lock_id": MIGRATION_LOCK_ID},
                )
                await lock_owner.commit()
    finally:
        await engine.dispose()
