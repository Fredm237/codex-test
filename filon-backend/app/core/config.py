"""Configuration centrale, lue depuis l'environnement (.env)."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Literal, Self
from urllib.parse import urlsplit

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        hide_input_in_errors=True,
    )

    # Application
    app_name: str = "FILON AI"
    # Obligatoire : une valeur absente ou inconnue ne doit jamais transformer
    # silencieusement un déploiement en environnement local permissif.
    env: Literal[
        "local",
        "dev",
        "development",
        "test",
        "staging",
        "prod",
        "production",
    ]
    debug: bool = Field(default=False)
    # Accepte une liste JSON ou séparée par des virgules. L'absence d'une valeur
    # n'ouvre aucune origine par défaut ; la production refuse aussi le wildcard.
    cors_origins: str = Field(default="")

    @property
    def is_production(self) -> bool:
        return self.env in {"staging", "prod", "production"}

    @property
    def cors_origins_list(self) -> list[str]:
        raw = (self.cors_origins or "").strip()
        if not raw:
            return []
        if raw == "*":
            return ["*"]
        if raw.startswith("["):
            try:
                parsed = json.loads(raw)
            except (json.JSONDecodeError, TypeError) as exc:
                raise ValueError("CORS_ORIGINS must be valid JSON or CSV") from exc
            if not isinstance(parsed, list) or not parsed:
                raise ValueError("CORS_ORIGINS JSON must be a non-empty list")
            origins = [origin.strip() for origin in parsed if isinstance(origin, str)]
            if len(origins) != len(parsed) or any(not origin for origin in origins):
                raise ValueError("CORS_ORIGINS entries must be non-empty strings")
        else:
            origins = [origin.strip() for origin in raw.split(",") if origin.strip()]
        if not origins:
            raise ValueError("CORS_ORIGINS must contain at least one origin")
        if len(origins) != len(set(origins)):
            raise ValueError("CORS_ORIGINS must not contain duplicates")
        return origins

    @model_validator(mode="after")
    def reject_unsafe_production_configuration(self) -> Self:
        origins = self.cors_origins_list
        if not self.is_production:
            return self

        errors: list[str] = []
        if self.debug:
            errors.append("DEBUG must be false")
        if not origins:
            errors.append("CORS_ORIGINS must be explicit")
        elif "*" in origins:
            errors.append("CORS_ORIGINS wildcard is forbidden")
        for origin in origins:
            if origin == "*":
                continue
            parsed = urlsplit(origin)
            if (
                parsed.scheme != "https"
                or not parsed.netloc
                or parsed.username is not None
                or parsed.password is not None
                or parsed.path
                or parsed.query
                or parsed.fragment
            ):
                errors.append(f"invalid production CORS origin: {origin!r}")
        database_url = (self.database_url or "").strip()
        if not database_url:
            errors.append("DATABASE_URL is required")
        elif urlsplit(database_url).scheme not in {
            "postgres",
            "postgresql",
            "postgresql+asyncpg",
        }:
            errors.append("DATABASE_URL must use PostgreSQL")
        if self.database_schema_mode != "alembic":
            errors.append("DATABASE_SCHEMA_MODE must be alembic")
        if errors:
            raise ValueError(
                "unsafe production configuration: " + "; ".join(errors)
            )
        return self

    # Infrastructure (optionnelle au runtime : dégradation propre si absente)
    database_url: str | None = Field(default=None)
    # ``alembic`` interdit toute mutation DDL implicite au démarrage. Le mode
    # historique ``legacy`` est réservé aux diagnostics locaux ; il est refusé
    # dans tout environnement déployé.
    database_schema_mode: Literal["alembic", "legacy"] = Field(default="alembic")
    redis_url: str | None = Field(default=None)
    qdrant_url: str | None = Field(default=None)
    # Secret dédié au scrape OpenMetrics. Sans valeur, l'export standard est
    # désactivé et répond 503 ; le snapshot JSON historique reste inchangé.
    metrics_export_token: str | None = Field(default=None)

    @field_validator("metrics_export_token")
    @classmethod
    def validate_metrics_export_token(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return None
        if (
            value != value.strip()
            or not 32 <= len(value) <= 256
            or not value.isascii()
            or any(character.isspace() or not character.isprintable() for character in value)
        ):
            raise ValueError(
                "METRICS_EXPORT_TOKEN must be 32-256 printable non-whitespace ASCII characters"
            )
        return value

    # LLM — couche d'abstraction multi-fournisseurs
    # Fournisseur par tâche : "mock" fonctionne sans aucune clé.
    llm_provider_default: str = Field(default="mock")
    llm_provider_reasoning: str = Field(default="mock")
    llm_provider_long: str = Field(default="mock")

    deepseek_api_key: str | None = Field(default=None)
    deepseek_base_url: str = Field(default="https://api.deepseek.com/v1")
    deepseek_model: str = Field(default="deepseek-chat")

    kimi_api_key: str | None = Field(default=None)
    kimi_base_url: str = Field(default="https://api.moonshot.cn/v1")
    kimi_model: str = Field(default="moonshot-v1-128k")

    glm_api_key: str | None = Field(default=None)
    glm_base_url: str = Field(default="https://open.bigmodel.cn/api/paas/v4")
    glm_model: str = Field(default="glm-4")

    llm_timeout_seconds: float = Field(default=30.0)

    # FILON Intelligence Layer — opt-in explicite. Les trois flags sont séparés
    # pour qu'un module expérimental n'affecte jamais le catalogue ou l'assistant
    # existants tant qu'il n'a pas été activé et validé.
    filon_intelligence_enabled: bool = Field(default=False)
    fashion_expert_enabled: bool = Field(default=False)
    outfit_studio_enabled: bool = Field(default=False)
    # Double écriture append-only de l'ingestion vers RawSource/Observation.
    # Désactivée tant que P0.e n'a pas été validé sur un lot réel borné.
    observation_shadow_enabled: bool = Field(default=False)

    # Données produits réelles (Google Shopping via SerpApi)
    serpapi_api_key: str | None = Field(default=None)
    serpapi_base_url: str = Field(default="https://serpapi.com/search.json")
    serpapi_gl: str = Field(default="be")   # pays : Belgique
    serpapi_hl: str = Field(default="fr")   # langue : français

    # Affiliation Awin — l'ID éditeur n'est pas secret (il figure dans les liens).
    # Le token API, lui, est un SECRET : à définir en variable d'environnement,
    # jamais dans le code (AWIN_API_TOKEN).
    awin_publisher_id: str = Field(default="3005443")
    awin_api_token: str | None = Field(default=None)
    awin_api_base: str = Field(default="https://api.awin.com")
    awin_clickref: str = Field(default="filon")

    # Ingestion des feeds produits Awin (Create-a-Feed / datafeed).
    # La clé de feed peut différer du token API : elle se trouve dans l'URL
    # générée par l'UI Awin (Toolbox → Create-a-Feed). SECRET → env AWIN_FEED_API_KEY.
    awin_feed_api_key: str | None = Field(default=None)
    awin_feed_base: str = Field(default="https://productdata.awin.com")
    # Régions ciblées pour le catalogue (codes pays), séparées par des virgules.
    awin_regions: str = Field(default="BE,FR,LU,NL")
    # Nombre max de feeds à ingérer par run (garde-fou coût/temps ; 0 = tous).
    awin_feed_limit: int = Field(default=0)
    # Nombre max de lignes ingérées par feed. ``0`` conserve la compatibilité
    # de configuration mais active tout de même le plafond dur de 250 000.
    awin_max_rows_per_feed: int = Field(default=100_000, ge=0, le=250_000)
    # Le flux est spoulé sur disque après 8 MiB, mais les deux volumes restent
    # fail-closed pour résister aux réponses géantes et aux bombes gzip.
    awin_max_download_bytes: int = Field(
        default=256 * 1024 * 1024,
        ge=1024,
        le=1024 * 1024 * 1024,
    )
    awin_max_decompressed_bytes: int = Field(
        default=512 * 1024 * 1024,
        ge=1024,
        le=2 * 1024 * 1024 * 1024,
    )
    # Fenêtre de fraîcheur du job catalogue autonome (0 = job désactivé).
    # Un Railway Cron peut exécuter ``python -m app.ingest.scheduler`` ; le
    # processus web ne démarre jamais de boucle de synchronisation.
    awin_auto_sync_hours: int = Field(default=0, ge=0)

    @property
    def awin_regions_list(self) -> list[str]:
        return [r.strip().upper() for r in (self.awin_regions or "").split(",") if r.strip()]

    # Jeton protégeant les endpoints d'administration (déclenchement d'un sync).
    # SECRET → env ADMIN_SYNC_TOKEN. Sans valeur, les endpoints admin sont fermés.
    admin_sync_token: str | None = Field(default=None)

    # Marchands exclus de tout affichage public (slugs, séparés par des virgules).
    # Le flag adultcontent d'Awin ne suffit pas : des articles pour adultes
    # remontaient encore en page d'accueil. Filtrer par marchand est exact, sans
    # les faux positifs qu'entraînerait une liste de mots-clés.
    blocked_merchants: str = Field(default="montamour")

    @property
    def blocked_merchant_slugs(self) -> list[str]:
        return [s.strip().lower() for s in (self.blocked_merchants or "").split(",") if s.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
