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


async def _migrate() -> None:
    """Migrations légères et idempotentes (le projet n'utilise pas Alembic).

    `create_all` crée les tables manquantes mais ne modifie jamais une table
    existante : une colonne ajoutée à un modèle déjà déployé doit donc l'être
    explicitement. Sans Postgres (tests SQLite), `create_all` produit déjà la
    définition complète — il n'y a rien à rattraper.

    Chaque instruction s'exécute dans sa *propre* connexion en autocommit. Sous
    PostgreSQL, une instruction qui échoue avorte toute la transaction : les
    suivantes échouent en cascade et le commit final lève à son tour. Attraper
    l'exception ne suffit donc pas — il faut l'isoler, sans quoi une migration
    bénigne empêche l'application de démarrer.

    Chaque instruction est en outre bornée par un `lock_timeout`. Une migration
    qui réclame un verrou déjà tenu doit renoncer et laisser démarrer
    l'application : ce code tourne au démarrage, et `price_snapshots` comme
    `offers` sont lues en permanence par l'ingestion. Sans cette borne, un
    redémarrage pendant un cycle d'ingestion attend le verrou indéfiniment, le
    healthcheck expire, et le déploiement échoue en boucle.
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
        "ALTER TABLE offers ADD COLUMN IF NOT EXISTS dedup_key VARCHAR(191)",
        "CREATE INDEX IF NOT EXISTS ix_offers_dedup_key ON offers (dedup_key)",
        "ALTER TABLE offers ADD COLUMN IF NOT EXISTS is_canonical BOOLEAN DEFAULT TRUE",
        "CREATE INDEX IF NOT EXISTS ix_offers_is_canonical ON offers (is_canonical)",
        "ALTER TABLE offers ADD COLUMN IF NOT EXISTS is_adult BOOLEAN DEFAULT FALSE",
        "CREATE INDEX IF NOT EXISTS ix_offers_is_adult ON offers (is_adult)",
        # Mémorise le prix qui précède chaque écriture, pour n'ajouter un relevé
        # d'historique que lorsque le prix bouge (voir awin_catalog._upsert_offer).
        "ALTER TABLE offers ADD COLUMN IF NOT EXISTS previous_price DOUBLE PRECISION",
        # Garde-fou en base. L'écriture conditionnelle vit dans l'ingestion, mais
        # un script d'appoint, un rattrapage ou un futur chemin d'écriture peuvent
        # l'ignorer — c'est ainsi que 2,4 millions de lignes quotidiennes se sont
        # accumulées sans que personne ne le remarque. Le trigger rend la règle
        # inviolable quel que soit l'appelant, et reste sans effet lorsque
        # l'application fait déjà le tri.
        """
        CREATE OR REPLACE FUNCTION filon_skip_unchanged_snapshot()
        RETURNS TRIGGER AS $$
        DECLARE
            dernier DOUBLE PRECISION;
        BEGIN
            SELECT price INTO dernier
            FROM price_snapshots
            WHERE offer_id = NEW.offer_id
            ORDER BY captured_at DESC, id DESC
            LIMIT 1;
            -- Premier relèvement de cette offre : l'historique doit avoir une
            -- origine, on laisse passer.
            IF dernier IS NULL THEN
                RETURN NEW;
            END IF;
            -- Moins d'un demi-centime d'écart : les prix sont en flottant, et ce
            -- bruit ne représente aucune variation commerciale.
            IF abs(dernier - NEW.price) < 0.005 THEN
                RETURN NULL;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
        """,
        # Création conditionnelle, sans `DROP TRIGGER` préalable. `DROP TRIGGER`
        # exige un ACCESS EXCLUSIVE sur price_snapshots, qu'une simple lecture
        # encore ouverte suffit à bloquer ; au démarrage, cela suspend
        # l'application. Mettre à jour la fonction suffit d'ailleurs à changer le
        # comportement, le trigger la désignant par son nom.
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_trigger
                WHERE tgname = 'trg_skip_unchanged_snapshot'
                  AND tgrelid = 'price_snapshots'::regclass
            ) THEN
                CREATE TRIGGER trg_skip_unchanged_snapshot
                BEFORE INSERT ON price_snapshots
                FOR EACH ROW EXECUTE FUNCTION filon_skip_unchanged_snapshot();
            END IF;
        END $$
        """,
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
                # Renoncer vite plutôt que bloquer le démarrage : la migration
                # sera retentée au redémarrage suivant.
                await conn.execute(text("SET lock_timeout = '5s'"))
                await conn.execute(text(sql))
        except Exception as exc:  # pragma: no cover - dépend de l'état réel
            # Une migration qui échoue ne doit jamais empêcher le démarrage.
            log.warning("Migration ignorée (%s…) : %s", " ".join(sql.split())[:60], exc)


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
    # Hors de la transaction précédente : voir _migrate.
    await _migrate()


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
