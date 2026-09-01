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
BASELINE_REVISION = "b9db07b15986"
EVIDENCE_ENGINE_REVISION = "e8c3f6a0b5d2"
HEAD_REVISION = "d1a9c3e5f7b0"
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


async def test_postgresql_adopts_known_offer_flag_drift_fail_closed() -> None:
    url = _test_database_url()
    await _reset_public_schema(url)

    baseline = await asyncio.to_thread(_run_alembic, url, "upgrade", BASELINE_REVISION)
    assert baseline.returncode == 0, "La baseline PostgreSQL n'a pas pu être créée"

    engine = create_async_engine(url)
    try:
        async with engine.begin() as connection:
            for statement in (
                "ALTER TABLE offers ALTER COLUMN is_canonical DROP NOT NULL",
                "ALTER TABLE offers ALTER COLUMN is_canonical SET DEFAULT TRUE",
                "ALTER TABLE offers ALTER COLUMN is_adult DROP NOT NULL",
                "ALTER TABLE offers ALTER COLUMN is_adult SET DEFAULT FALSE",
            ):
                await connection.execute(text(statement))

        adopted = await asyncio.to_thread(_run_alembic, url, "upgrade", "head")
        assert adopted.returncode == 0, "L'adoption du drift historique a échoué"

        async with engine.connect() as connection:
            states = {
                row.column_name: (row.is_nullable, row.column_default)
                for row in (
                    await connection.execute(
                        text(
                            "SELECT column_name, is_nullable, column_default "
                            "FROM information_schema.columns "
                            "WHERE table_schema = 'public' AND table_name = 'offers' "
                            "AND column_name IN ('is_canonical', 'is_adult')"
                        )
                    )
                )
            }
            revision = await connection.scalar(
                text("SELECT version_num FROM alembic_version")
            )

        assert states == {
            "is_canonical": ("NO", None),
            "is_adult": ("NO", None),
        }
        assert revision == HEAD_REVISION
        drift = await asyncio.to_thread(_run_alembic, url, "check")
        assert drift.returncode == 0, "Le schéma adopté conserve un drift"
    finally:
        await engine.dispose()

    await _reset_public_schema(url)
    baseline = await asyncio.to_thread(_run_alembic, url, "upgrade", BASELINE_REVISION)
    assert baseline.returncode == 0
    engine = create_async_engine(url)
    try:
        async with engine.begin() as connection:
            for statement in (
                "ALTER TABLE offers ALTER COLUMN is_canonical DROP NOT NULL",
                "ALTER TABLE offers ALTER COLUMN is_canonical SET DEFAULT TRUE",
                "ALTER TABLE offers ALTER COLUMN is_adult DROP NOT NULL",
                "ALTER TABLE offers ALTER COLUMN is_adult SET DEFAULT FALSE",
            ):
                await connection.execute(text(statement))
            await connection.execute(
                text(
                    "INSERT INTO merchants (id, awin_mid, name, slug, joined) "
                    "VALUES (1, 1001, 'Migration Merchant', 'migration-merchant', TRUE)"
                )
            )
            await connection.execute(
                text(
                    "INSERT INTO offers "
                    "(id, merchant_id, awin_product_id, name, is_canonical, is_adult) "
                    "VALUES (1, 1, 'migration-offer', 'Migration Offer', NULL, NULL)"
                )
            )

        rejected = await asyncio.to_thread(_run_alembic, url, "upgrade", "head")
        combined_output = f"{rejected.stdout}\n{rejected.stderr}"
        assert rejected.returncode != 0
        assert "Adoption refusée" in combined_output
        assert "valeur(s) NULL" in combined_output
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
            graph_tables = {
                row.name
                for row in (
                    await connection.execute(
                        text(
                            "SELECT table_name AS name FROM information_schema.tables "
                            "WHERE table_schema = 'public' "
                            "AND (table_name LIKE 'graph_%' "
                            "OR table_name IN ('merchant_quality_snapshots', "
                            "'evidence_claim_records', "
                            "'decision_eligibility_records', "
                            "'offer_truth_snapshots', "
                            "'product_ontology_snapshots', "
                            "'hybrid_retrieval_runs', "
                            "'hybrid_retrieval_candidates', "
                            "'constraint_evaluation_runs', "
                            "'constraint_candidate_evaluations', "
                            "'product_ranking_runs', "
                            "'product_ranking_candidates', "
                            "'offer_optimization_runs', "
                            "'offer_optimization_candidates'))"
                        )
                    )
                )
            }

        assert revision == HEAD_REVISION
        assert extension == "pg_trgm"
        assert currency_nullable == "YES"
        assert set(indexes) == {"ix_offers_name_trgm", "ix_offers_brand_trgm"}
        assert all("USING gin" in definition for definition in indexes.values())
        assert graph_tables == {
            "graph_brands",
            "graph_brand_aliases",
            "graph_product_families",
            "graph_product_models",
            "graph_variants",
            "graph_identifiers",
            "graph_identifier_evidence",
            "graph_offer_variant_links",
            "graph_identity_assertions",
            "graph_offer_observations",
            "graph_entity_signal_projections",
            "graph_entity_resolution_decisions",
            "offer_truth_snapshots",
            "product_ontology_snapshots",
            "hybrid_retrieval_runs",
            "hybrid_retrieval_candidates",
            "constraint_evaluation_runs",
            "constraint_candidate_evaluations",
            "product_ranking_runs",
            "product_ranking_candidates",
            "offer_optimization_runs",
            "offer_optimization_candidates",
            "merchant_quality_snapshots",
            "evidence_claim_records",
            "decision_eligibility_records",
        }

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


async def test_postgresql_heartbeat_upgrade_and_downgrade_preserve_active_run() -> None:
    url = _test_database_url()
    await _reset_public_schema(url)

    before = await asyncio.to_thread(
        _run_alembic,
        url,
        "upgrade",
        EVIDENCE_ENGINE_REVISION,
    )
    assert before.returncode == 0

    engine = create_async_engine(url)
    try:
        async with engine.begin() as connection:
            await connection.execute(
                text(
                    "INSERT INTO catalog_sync_runs "
                    "(id, trigger, status, started_at, merchants_count, "
                    "feeds_count, offers_count, skipped_feeds) "
                    "VALUES (17, 'scheduler', 'running', "
                    "TIMESTAMP '2026-08-31 02:34:19', 0, 0, 0, 0)"
                )
            )
    finally:
        await engine.dispose()

    upgraded = await asyncio.to_thread(_run_alembic, url, "upgrade", "head")
    assert upgraded.returncode == 0
    engine = create_async_engine(url)
    try:
        async with engine.begin() as connection:
            heartbeat = await connection.scalar(
                text("SELECT heartbeat_at FROM catalog_sync_runs WHERE id = 17")
            )
            nullable = await connection.scalar(
                text(
                    "SELECT is_nullable FROM information_schema.columns "
                    "WHERE table_schema = 'public' "
                    "AND table_name = 'catalog_sync_runs' "
                    "AND column_name = 'heartbeat_at'"
                )
            )
            checkpoint_table = await connection.scalar(
                text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'public' "
                    "AND table_name = 'catalog_sync_feed_checkpoints'"
                )
            )
            resume_index = await connection.scalar(
                text(
                    "SELECT indexname FROM pg_indexes "
                    "WHERE schemaname = 'public' "
                    "AND tablename = 'raw_source_records' "
                    "AND indexname = 'ix_raw_source_sync_feed_record'"
                )
            )
            lineage_column = await connection.scalar(
                text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_schema = 'public' "
                    "AND table_name = 'catalog_sync_runs' "
                    "AND column_name = 'resumed_from_run_id'"
                )
            )
            lineage_index = await connection.scalar(
                text(
                    "SELECT indexname FROM pg_indexes "
                    "WHERE schemaname = 'public' "
                    "AND tablename = 'catalog_sync_runs' "
                    "AND indexname = 'ix_catalog_sync_runs_resumed_from_run_id'"
                )
            )
            await connection.execute(
                text(
                    "INSERT INTO catalog_sync_feed_checkpoints "
                    "(sync_run_id, feed_id, status, rows_count) "
                    "VALUES (17, '42', 'running', 1200)"
                )
            )
        assert heartbeat is not None
        assert nullable == "NO"
        assert checkpoint_table == "catalog_sync_feed_checkpoints"
        assert resume_index == "ix_raw_source_sync_feed_record"
        assert lineage_column == "resumed_from_run_id"
        assert lineage_index == "ix_catalog_sync_runs_resumed_from_run_id"
    finally:
        await engine.dispose()

    downgraded = await asyncio.to_thread(
        _run_alembic,
        url,
        "downgrade",
        EVIDENCE_ENGINE_REVISION,
    )
    assert downgraded.returncode == 0
    engine = create_async_engine(url)
    try:
        async with engine.connect() as connection:
            status = await connection.scalar(
                text("SELECT status FROM catalog_sync_runs WHERE id = 17")
            )
            heartbeat_column = await connection.scalar(
                text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_schema = 'public' "
                    "AND table_name = 'catalog_sync_runs' "
                    "AND column_name = 'heartbeat_at'"
                )
            )
            lineage_column = await connection.scalar(
                text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_schema = 'public' "
                    "AND table_name = 'catalog_sync_runs' "
                    "AND column_name = 'resumed_from_run_id'"
                )
            )
        assert status == "running"
        assert heartbeat_column is None
        assert lineage_column is None
    finally:
        await engine.dispose()
