"""Preuves exécutables de la baseline, du stamp et du rollback Alembic."""

from __future__ import annotations

import asyncio
import json
import logging
import sqlite3
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import Settings
from app.db import models as core_models  # noqa: F401
from app.db import session as db_session
from app.db.base import Base
from app.intelligence import models as intelligence_models  # noqa: F401
from app.observations import models as observation_models  # noqa: F401
from app.product_graph import models as product_graph_models  # noqa: F401
from app.offer_graph import models as offer_graph_models  # noqa: F401


BACKEND_ROOT = Path(__file__).resolve().parents[1]
APPLICATION_TABLES = set(Base.metadata.tables)
SHADOW_TABLES = {"raw_source_records", "observations", "quarantine_records"}
GRAPH_SHADOW_TABLES = {
    "graph_brands",
    "graph_brand_aliases",
    "graph_product_families",
    "graph_product_models",
    "graph_variants",
    "graph_identifiers",
    "graph_identifier_evidence",
    "graph_offer_variant_links",
}
OFFER_GRAPH_TABLES = {"graph_offer_observations"}
BASELINE_REVISION = "b9db07b15986"
SHADOW_REVISION = "d75faf1f6a94"
CURRENCY_REVISION = "3a7f9c2e5b61"
OFFER_FLAGS_REVISION = "f4c81a9d2e70"
PRODUCT_GRAPH_REVISION = "8b2f4c7d9a10"
HEAD_REVISION = "c6a1d4e8f2b3"


@pytest.fixture(autouse=True)
def _restore_application_loggers_after_alembic():
    """Alembic ne doit pas contaminer les tests applicatifs suivants."""
    manager = logging.Logger.manager.loggerDict
    initial_disabled = {
        name: logger.disabled
        for name, logger in manager.items()
        if isinstance(logger, logging.Logger)
        and (name == "filon" or name.startswith("filon."))
    }
    yield
    for name, logger in manager.items():
        if isinstance(logger, logging.Logger) and (
            name == "filon" or name.startswith("filon.")
        ):
            logger.disabled = initial_disabled.get(name, False)


def _config(database_path: Path, monkeypatch) -> Config:
    monkeypatch.setenv(
        "ALEMBIC_DATABASE_URL",
        f"sqlite+aiosqlite:///{database_path}",
    )
    return Config(str(BACKEND_ROOT / "alembic.ini"))


def _sync_url(database_path: Path) -> str:
    return f"sqlite:///{database_path}"


def _insert_catalog_sentinel(connection, *, with_currency: bool) -> None:
    connection.execute(
        text(
            "INSERT INTO merchants (id, awin_mid, name, slug, joined) "
            "VALUES (1, 1001, 'Migration Merchant', 'migration-merchant', 1)"
        )
    )
    connection.execute(
        text(
            "INSERT INTO offers "
            "(id, merchant_id, awin_product_id, name, is_canonical, is_adult) "
            "VALUES (1, 1, 'migration-offer', 'Migration Offer', 1, 0)"
        )
    )
    if with_currency:
        connection.execute(
            text(
                "INSERT INTO price_snapshots "
                "(id, offer_id, price, currency, in_stock) "
                "VALUES (1, 1, 42.5, 'EUR', 1)"
            )
        )
    else:
        connection.execute(
            text(
                "INSERT INTO price_snapshots (id, offer_id, price, in_stock) "
                "VALUES (1, 1, 42.5, 1)"
            )
        )


def test_runtime_revision_matches_single_alembic_head(tmp_path, monkeypatch):
    config = _config(tmp_path / "head.sqlite", monkeypatch)
    scripts = ScriptDirectory.from_config(config)
    head = scripts.get_current_head()

    assert head == HEAD_REVISION
    assert head == db_session.CURRENT_SCHEMA_REVISION
    assert scripts.get_revision(HEAD_REVISION).down_revision == PRODUCT_GRAPH_REVISION


def test_default_runtime_mode_only_validates_alembic(monkeypatch):
    calls: list[str] = []

    async def validate():
        calls.append("validate")

    async def legacy_ddl():
        calls.append("legacy")

    monkeypatch.setattr(db_session, "get_settings", lambda: Settings())
    monkeypatch.setattr(db_session, "assert_schema_current", validate)
    monkeypatch.setattr(db_session, "create_all", legacy_ddl)

    asyncio.run(db_session.prepare_schema())

    assert calls == ["validate"]


def test_legacy_runtime_mode_is_explicit(monkeypatch):
    calls: list[str] = []

    async def validate():
        calls.append("validate")

    async def legacy_ddl():
        calls.append("legacy")

    monkeypatch.setattr(
        db_session,
        "get_settings",
        lambda: Settings(database_schema_mode="legacy"),
    )
    monkeypatch.setattr(db_session, "assert_schema_current", validate)
    monkeypatch.setattr(db_session, "create_all", legacy_ddl)

    asyncio.run(db_session.prepare_schema())

    assert calls == ["legacy"]


def test_upgrade_has_no_model_drift_and_snapshot_restores_without_downgrade(
    tmp_path, monkeypatch
):
    database_path = tmp_path / "migration.sqlite"
    backup_path = tmp_path / "migration.backup.sqlite"
    restored_path = tmp_path / "migration.restored.sqlite"
    config = _config(database_path, monkeypatch)

    command.upgrade(config, "head")
    # ``alembic check`` lève une exception à la moindre différence entre la
    # migration appliquée et les modèles courants.
    command.check(config)

    async_engine = create_async_engine(f"sqlite+aiosqlite:///{database_path}")
    monkeypatch.setattr(db_session, "_engine", async_engine)
    asyncio.run(db_session.assert_schema_current())
    asyncio.run(async_engine.dispose())

    engine = create_engine(_sync_url(database_path))
    assert APPLICATION_TABLES <= set(inspect(engine).get_table_names())
    currency_column = next(
        column
        for column in inspect(engine).get_columns("price_snapshots")
        if column["name"] == "currency"
    )
    assert currency_column["nullable"] is True
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO users (email, hashed_password) "
                "VALUES ('migration@filon.test', 'hash')"
            )
        )
        _insert_catalog_sentinel(connection, with_currency=True)
    engine.dispose()

    with sqlite3.connect(database_path) as source, sqlite3.connect(
        backup_path
    ) as target:
        source.backup(target)

    # L'exercice restaure vers une base distincte. Un rollback applicatif ne
    # valide jamais un downgrade destructif comme procédure normale.
    with sqlite3.connect(backup_path) as source, sqlite3.connect(
        restored_path
    ) as target:
        source.backup(target)

    engine = create_engine(_sync_url(restored_path))
    with engine.connect() as connection:
        assert (
            connection.scalar(text("SELECT version_num FROM alembic_version"))
            == HEAD_REVISION
        )
        assert (
            connection.scalar(text("SELECT email FROM users"))
            == "migration@filon.test"
        )
        assert connection.scalar(text("SELECT currency FROM price_snapshots")) == "EUR"
    engine.dispose()


def test_stamp_adopts_existing_schema_without_touching_data(tmp_path, monkeypatch):
    database_path = tmp_path / "existing.sqlite"
    config = _config(database_path, monkeypatch)
    engine = create_engine(_sync_url(database_path))
    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO users (email, hashed_password) "
                "VALUES ('existing@filon.test', 'hash')"
            )
        )
    engine.dispose()

    command.stamp(config, "head")
    command.check(config)

    engine = create_engine(_sync_url(database_path))
    with engine.connect() as connection:
        assert (
            connection.scalar(text("SELECT email FROM users"))
            == "existing@filon.test"
        )
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == (
            db_session.CURRENT_SCHEMA_REVISION
        )
    engine.dispose()


def test_existing_baseline_is_stamped_then_expanded_without_data_loss(
    tmp_path, monkeypatch
):
    database_path = tmp_path / "baseline-adoption.sqlite"
    config = _config(database_path, monkeypatch)
    command.upgrade(config, BASELINE_REVISION)
    engine = create_engine(_sync_url(database_path))
    assert "currency" not in {
        column["name"] for column in inspect(engine).get_columns("price_snapshots")
    }
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO users (email, hashed_password) "
                "VALUES ('baseline@filon.test', 'hash')"
            )
        )
        _insert_catalog_sentinel(connection, with_currency=False)
    engine.dispose()

    # Simule une base historique conforme mais sans marqueur Alembic.
    command.stamp(config, "base")
    command.stamp(config, BASELINE_REVISION)
    command.upgrade(config, "head")
    command.check(config)

    engine = create_engine(_sync_url(database_path))
    assert SHADOW_TABLES | GRAPH_SHADOW_TABLES | OFFER_GRAPH_TABLES <= set(
        inspect(engine).get_table_names()
    )
    assert "currency" in {
        column["name"] for column in inspect(engine).get_columns("price_snapshots")
    }
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT email FROM users")) == (
            "baseline@filon.test"
        )
        assert connection.scalar(text("SELECT currency FROM price_snapshots")) is None
        assert (
            connection.scalar(text("SELECT version_num FROM alembic_version"))
            == HEAD_REVISION
        )
    engine.dispose()


def test_shadow_rollback_flag_preserves_head_schema_and_currency(tmp_path, monkeypatch):
    database_path = tmp_path / "shadow-rollback.sqlite"
    config = _config(database_path, monkeypatch)
    command.upgrade(config, "head")
    engine = create_engine(_sync_url(database_path))
    with engine.begin() as connection:
        _insert_catalog_sentinel(connection, with_currency=True)

    rollback_settings = Settings(observation_shadow_enabled=False)
    assert rollback_settings.observation_shadow_enabled is False
    assert rollback_settings.product_graph_shadow_enabled is False
    assert rollback_settings.offer_graph_shadow_enabled is False
    tables = set(inspect(engine).get_table_names())
    assert SHADOW_TABLES | GRAPH_SHADOW_TABLES | OFFER_GRAPH_TABLES <= tables
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT currency FROM price_snapshots")) == "EUR"
        assert (
            connection.scalar(text("SELECT version_num FROM alembic_version"))
            == HEAD_REVISION
        )
    engine.dispose()


def test_graph_expand_downgrade_is_reversible_without_touching_core_data(
    tmp_path,
    monkeypatch,
):
    database_path = tmp_path / "graph-rollback.sqlite"
    config = _config(database_path, monkeypatch)
    command.upgrade(config, "head")
    engine = create_engine(_sync_url(database_path))
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO users (email, hashed_password) "
                "VALUES ('graph-rollback@filon.test', 'hash')"
            )
        )
    engine.dispose()

    command.downgrade(config, OFFER_FLAGS_REVISION)
    engine = create_engine(_sync_url(database_path))
    tables = set(inspect(engine).get_table_names())
    assert not ((GRAPH_SHADOW_TABLES | OFFER_GRAPH_TABLES) & tables)
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT email FROM users")) == (
            "graph-rollback@filon.test"
        )
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == (
            OFFER_FLAGS_REVISION
        )
    engine.dispose()

    command.upgrade(config, "head")
    command.check(config)
    engine = create_engine(_sync_url(database_path))
    assert GRAPH_SHADOW_TABLES | OFFER_GRAPH_TABLES <= set(
        inspect(engine).get_table_names()
    )
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT email FROM users")) == (
            "graph-rollback@filon.test"
        )
    engine.dispose()


def test_docker_image_contains_the_alembic_runtime_contract():
    dockerfile = (BACKEND_ROOT / "Dockerfile").read_text().splitlines()

    alembic_ini_copy = dockerfile.index(
        "COPY --chown=filon:filon alembic.ini ./alembic.ini"
    )
    alembic_tree_copy = dockerfile.index(
        "COPY --chown=filon:filon alembic ./alembic"
    )
    unprivileged_user = dockerfile.index("USER filon")
    start = dockerfile.index('CMD ["python", "-m", "app"]')

    assert alembic_ini_copy < start
    assert alembic_tree_copy < start
    assert alembic_tree_copy < unprivileged_user < start
    assert any(
        requirement.startswith("alembic>=")
        for requirement in (BACKEND_ROOT / "requirements.txt").read_text().splitlines()
    )


def test_legacy_railway_config_keeps_the_exact_safe_deployment_contract():
    railway = json.loads((BACKEND_ROOT / "railway.json").read_text())

    assert railway["$schema"] == "https://railway.com/railway.schema.json"
    assert railway["build"] == {
        "builder": "DOCKERFILE",
        "dockerfilePath": "Dockerfile",
    }
    assert railway["deploy"] == {
        "preDeployCommand": "alembic upgrade head",
        "startCommand": "python -m app",
        "healthcheckPath": "/health/ready",
        "healthcheckTimeout": 120,
        "restartPolicyType": "ON_FAILURE",
        "restartPolicyMaxRetries": 10,
    }


def test_alembic_uses_a_postgresql_advisory_lock_for_single_ownership():
    environment = (BACKEND_ROOT / "alembic" / "env.py").read_text()

    assert "pg_try_advisory_lock" in environment
    assert "pg_advisory_unlock" in environment
    assert "Une autre release FILON" in environment


def test_new_railway_service_guide_forbids_relying_on_legacy_config_as_code():
    guide = (BACKEND_ROOT / "DEPLOY.md").read_text()
    runbook = (
        BACKEND_ROOT.parent / "docs/architecture/DATABASE_MIGRATION_RUNBOOK.md"
    ).read_text()
    documentation = f"{guide}\n{runbook}"
    flattened = " ".join(documentation.split())

    assert "Nouveau service : configuration Dashboard obligatoire" in flattened
    assert "Un nouveau service ne peut plus activer Config as Code" in flattened
    assert "2026-12-01" in documentation
    assert "`railway.json` n'est pas sa source de configuration" in flattened
    assert "Pre-Deploy Command** : `alembic upgrade head`" in flattened
    assert "Start Command** : `python -m app`" in flattened
    assert "Healthcheck Path** : `/health/ready`" in flattened
    assert "Healthcheck Timeout** : `120` secondes" in flattened
    assert "auto-détecte" in documentation and "`Dockerfile`" in documentation
    assert ".railway/railway.ts" in documentation
    for command_text in (
        "railway config migrate",
        "railway config pull",
        "railway config plan",
        "railway config apply",
    ):
        assert command_text in documentation
    assert not (BACKEND_ROOT.parent / ".railway/railway.ts").exists()
