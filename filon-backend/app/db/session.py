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

# Doit avancer avec la tête Alembic. Un test empêche qu'une nouvelle révision
# soit ajoutée sans mettre à jour le garde-fou runtime.
CURRENT_SCHEMA_REVISION = "c0f8b2d4e6a9"


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

    # Pool élargi : le regroupement du catalogue mobilise une connexion longtemps
    # et la valeur par défaut (5 + 10) a déjà été saturée en production, faisant
    # expirer les requêtes ordinaires et échouer le healthcheck du déploiement.
    _engine = create_async_engine(
        url, pool_pre_ping=True, pool_size=10, max_overflow=20, pool_timeout=30
    )
    _sessionmaker = async_sessionmaker(_engine, expire_on_commit=False)


def is_enabled() -> bool:
    _init()
    return _sessionmaker is not None


async def _legacy_migrate() -> None:
    """Ancien rattrapage idempotent, réservé aux diagnostics locaux.

    `create_all` crée les tables manquantes mais ne modifie jamais une table
    existante : une colonne ajoutée à un modèle déjà déployé doit donc l'être
    explicitement. Sans Postgres (tests SQLite), `create_all` produit déjà la
    définition complète — il n'y a rien à rattraper.

    Chaque instruction s'exécute dans sa *propre* connexion en autocommit. Sous
    PostgreSQL, une instruction qui échoue avorte toute la transaction : les
    suivantes échouent en cascade et le commit final lève à son tour. Attraper
    l'exception ne suffit donc pas — il faut l'isoler, sans quoi une migration
    bénigne empêche l'application de démarrer.
    """
    if _engine is None or _engine.dialect.name != "postgresql":
        return
    from sqlalchemy import text

    statements = (
        "ALTER TABLE offers ADD COLUMN IF NOT EXISTS product_id INTEGER "
        "REFERENCES catalog_products(id)",
        "CREATE INDEX IF NOT EXISTS ix_offers_product_id ON offers (product_id)",
        "ALTER TABLE offers ADD COLUMN IF NOT EXISTS filon_category VARCHAR(64)",
        "CREATE INDEX IF NOT EXISTS ix_offers_filon_category ON offers (filon_category)",
        "ALTER TABLE offers ADD COLUMN IF NOT EXISTS filon_subcategory VARCHAR(64)",
        "CREATE INDEX IF NOT EXISTS ix_offers_filon_subcategory ON offers (filon_subcategory)",
        "ALTER TABLE offers ADD COLUMN IF NOT EXISTS offer_kind VARCHAR(32)",
        "CREATE INDEX IF NOT EXISTS ix_offers_offer_kind ON offers (offer_kind)",
        "ALTER TABLE offers ADD COLUMN IF NOT EXISTS dedup_key VARCHAR(191)",
        "CREATE INDEX IF NOT EXISTS ix_offers_dedup_key ON offers (dedup_key)",
        "ALTER TABLE offers ADD COLUMN IF NOT EXISTS is_canonical BOOLEAN DEFAULT TRUE",
        "CREATE INDEX IF NOT EXISTS ix_offers_is_canonical ON offers (is_canonical)",
        "ALTER TABLE offers ADD COLUMN IF NOT EXISTS is_adult BOOLEAN DEFAULT FALSE",
        "CREATE INDEX IF NOT EXISTS ix_offers_is_adult ON offers (is_adult)",
        "ALTER TABLE price_snapshots ADD COLUMN IF NOT EXISTS currency VARCHAR(8)",
        # Index trigramme : sans lui, une recherche par sous-chaîne impose un
        # parcours complet des 795 000 lignes. L'extension peut être refusée
        # selon les droits — la migration le tolère et trace un avertissement.
        "CREATE EXTENSION IF NOT EXISTS pg_trgm",
        "CREATE INDEX IF NOT EXISTS ix_offers_name_trgm ON offers "
        "USING gin (name gin_trgm_ops)",
        "CREATE INDEX IF NOT EXISTS ix_offers_brand_trgm ON offers "
        "USING gin (brand gin_trgm_ops)",
    )
    for sql in statements:
        try:
            async with _engine.connect() as conn:
                await conn.execution_options(isolation_level="AUTOCOMMIT")
                await conn.execute(text(sql))
        except Exception as exc:  # pragma: no cover - dépend de l'état réel
            # Une migration qui échoue ne doit jamais empêcher le démarrage.
            log.warning(
                "Migration legacy ignorée (error_type=%s)",
                type(exc).__name__,
            )


async def create_all() -> None:
    """Crée/rattrape l'ancien schéma lorsque le mode ``legacy`` est explicite."""
    _init()
    if _engine is None:
        return
    from app.db.base import Base

    # Importe les modèles pour qu'ils soient enregistrés dans Base.metadata
    # avant create_all (sinon aucune table n'est créée). Les modèles Intelligence
    # sont parallèles : leur présence n'altère aucune table du Core.
    from app.db import models  # noqa: F401
    from app.intelligence import models as intelligence_models  # noqa: F401
    from app.observations import models as observation_models  # noqa: F401
    from app.product_graph import models as product_graph_models  # noqa: F401
    from app.offer_graph import models as offer_graph_models  # noqa: F401
    from app.offer_truth import models as offer_truth_models  # noqa: F401
    from app.product_ontology import models as product_ontology_models  # noqa: F401
    from app.hybrid_retrieval import models as hybrid_retrieval_models  # noqa: F401
    from app.constraint_engine import models as constraint_engine_models  # noqa: F401
    from app.product_ranking import models as product_ranking_models  # noqa: F401
    from app.offer_optimization import models as offer_optimization_models  # noqa: F401
    from app.merchant_intelligence import models as merchant_models  # noqa: F401
    from app.evidence_engine import models as evidence_models  # noqa: F401

    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Hors de la transaction précédente : voir _legacy_migrate.
    await _legacy_migrate()


async def assert_schema_current() -> None:
    """Refuse une base non versionnée ou en retard en mode Alembic."""
    _init()
    if _engine is None:
        return

    from sqlalchemy import text

    try:
        async with _engine.connect() as conn:
            result = await conn.execute(text("SELECT version_num FROM alembic_version"))
            revisions = {row[0] for row in result}
    except Exception as exc:
        raise RuntimeError(
            "Schéma non versionné : exécutez le runbook Alembic avant le service."
        ) from exc

    if revisions != {CURRENT_SCHEMA_REVISION}:
        actual = ", ".join(sorted(revisions)) or "aucune"
        raise RuntimeError(
            "Révision Alembic inattendue "
            f"({actual}) ; attendue : {CURRENT_SCHEMA_REVISION}."
        )


async def prepare_schema() -> None:
    """Valide le schéma, sans DDL implicite sauf diagnostic ``legacy`` local."""
    mode = get_settings().database_schema_mode
    if mode == "legacy":
        log.warning(
            "DATABASE_SCHEMA_MODE=legacy : DDL historique local actif ; "
            "ce mode est interdit en staging/production."
        )
        await create_all()
        return
    await assert_schema_current()


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
