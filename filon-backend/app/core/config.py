"""Configuration centrale, lue depuis l'environnement (.env)."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Literal, Self
from urllib.parse import urlsplit
from uuid import UUID

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
        errors: list[str] = []
        if self.product_graph_shadow_enabled and not self.observation_shadow_enabled:
            errors.append(
                "PRODUCT_GRAPH_SHADOW_ENABLED requires OBSERVATION_SHADOW_ENABLED"
            )
        if self.entity_resolution_shadow_enabled and not (
            self.observation_shadow_enabled and self.product_graph_shadow_enabled
        ):
            errors.append(
                "ENTITY_RESOLUTION_SHADOW_ENABLED requires Observation and Product Graph shadows"
            )
        if self.offer_graph_shadow_enabled and not self.observation_shadow_enabled:
            errors.append(
                "OFFER_GRAPH_SHADOW_ENABLED requires OBSERVATION_SHADOW_ENABLED"
            )
        if self.offer_truth_shadow_enabled and not (
            self.observation_shadow_enabled
            and self.product_graph_shadow_enabled
            and self.entity_resolution_shadow_enabled
            and self.offer_graph_shadow_enabled
        ):
            errors.append(
                "OFFER_TRUTH_SHADOW_ENABLED requires Observation, Product Graph, "
                "Entity Resolution and Offer Graph shadows"
            )
        if self.product_ontology_shadow_enabled and not (
            self.observation_shadow_enabled
            and self.product_graph_shadow_enabled
            and self.entity_resolution_shadow_enabled
        ):
            errors.append(
                "PRODUCT_ONTOLOGY_SHADOW_ENABLED requires Observation, Product Graph "
                "and Entity Resolution shadows"
            )
        if self.hybrid_retrieval_shadow_enabled and not (
            self.observation_shadow_enabled
            and self.product_graph_shadow_enabled
            and self.entity_resolution_shadow_enabled
            and self.product_ontology_shadow_enabled
        ):
            errors.append(
                "HYBRID_RETRIEVAL_SHADOW_ENABLED requires Observation, Product Graph, "
                "Entity Resolution and Product Ontology shadows"
            )
        if self.constraint_engine_shadow_enabled and not self.hybrid_retrieval_shadow_enabled:
            errors.append(
                "CONSTRAINT_ENGINE_SHADOW_ENABLED requires HYBRID_RETRIEVAL_SHADOW_ENABLED"
            )
        if self.merchant_intelligence_shadow_enabled and not (
            self.observation_shadow_enabled
            and self.product_graph_shadow_enabled
            and self.offer_graph_shadow_enabled
        ):
            errors.append(
                "MERCHANT_INTELLIGENCE_SHADOW_ENABLED requires all Graph shadows"
            )
        if self.evidence_engine_shadow_enabled and not (
            self.observation_shadow_enabled
            and self.product_graph_shadow_enabled
            and self.offer_graph_shadow_enabled
            and self.merchant_intelligence_shadow_enabled
        ):
            errors.append(
                "EVIDENCE_ENGINE_SHADOW_ENABLED requires all prior shadows"
            )
        if self.rate_limit_backend == "redis":
            redis_url = (self.redis_url or "").strip()
            if not redis_url:
                errors.append("REDIS_URL is required for distributed rate limiting")
            else:
                parsed_redis_url = urlsplit(redis_url)
                if (
                    parsed_redis_url.scheme not in {"redis", "rediss"}
                    or not parsed_redis_url.hostname
                ):
                    errors.append("REDIS_URL must use Redis")
            if self.rate_limit_identity_secret is None:
                errors.append(
                    "RATE_LIMIT_IDENTITY_SECRET is required for distributed rate limiting"
                )
            if self.is_production and self.rate_limit_identity_source != "railway":
                errors.append(
                    "RATE_LIMIT_IDENTITY_SOURCE must be railway for distributed "
                    "rate limiting in production"
                )

        trace_endpoint = (self.otlp_traces_endpoint or "").strip()
        trace_token = self.otlp_trace_export_token
        if self.trace_export_backend == "disabled":
            if trace_endpoint or trace_token is not None:
                errors.append(
                    "OTLP trace settings require TRACE_EXPORT_BACKEND=otlp_http"
                )
        else:
            if not trace_endpoint:
                errors.append("OTLP_TRACES_ENDPOINT is required for trace export")
            else:
                parsed_trace_endpoint = urlsplit(trace_endpoint)
                local_http = (
                    not self.is_production
                    and parsed_trace_endpoint.scheme == "http"
                    and parsed_trace_endpoint.hostname in {"localhost", "127.0.0.1", "::1"}
                )
                if (
                    (parsed_trace_endpoint.scheme != "https" and not local_http)
                    or not parsed_trace_endpoint.hostname
                    or parsed_trace_endpoint.username is not None
                    or parsed_trace_endpoint.password is not None
                    or parsed_trace_endpoint.query
                    or parsed_trace_endpoint.fragment
                    or not parsed_trace_endpoint.path.endswith("/v1/traces")
                ):
                    errors.append(
                        "OTLP_TRACES_ENDPOINT must be a safe OTLP/HTTP traces endpoint"
                    )
            if trace_token is None:
                errors.append("OTLP_TRACE_EXPORT_TOKEN is required for trace export")

        if self.rate_limit_identity_source == "railway":
            if not self.is_production:
                errors.append(
                    "Railway rate limit identity is only valid in a deployed environment"
                )
            for name, value in (
                ("RAILWAY_ENVIRONMENT_ID", self.railway_environment_id),
                ("RAILWAY_SERVICE_ID", self.railway_service_id),
            ):
                try:
                    parsed_identifier = UUID(value or "")
                except ValueError:
                    errors.append(f"{name} must be a canonical UUID")
                    continue
                if str(parsed_identifier) != value:
                    errors.append(f"{name} must be a canonical UUID")

        if not self.is_production:
            if errors:
                raise ValueError("unsafe configuration: " + "; ".join(errors))
            return self

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
    # Le compteur local préserve la compatibilité. Le mode Redis doit être un
    # opt-in complet : URL, secret partagé et aucune dégradation locale.
    rate_limit_backend: Literal["local", "redis"] = Field(default="local")
    rate_limit_identity_source: Literal["asgi", "railway"] = Field(
        default="asgi"
    )
    rate_limit_identity_secret: str | None = Field(default=None)
    rate_limit_redis_timeout_seconds: float = Field(
        default=0.25,
        ge=0.05,
        le=2.0,
    )
    # Variables injectées par Railway. Elles ne sont jamais renvoyées ni
    # journalisées ; leur présence borne l'usage de X-Real-IP à la plateforme.
    railway_environment_id: str | None = Field(default=None)
    railway_service_id: str | None = Field(default=None)
    # Secret dédié au scrape OpenMetrics. Sans valeur, l'export standard est
    # désactivé et répond 503 ; le snapshot JSON historique reste inchangé.
    metrics_export_token: str | None = Field(default=None)
    # Export de traces strictement opt-in vers un collecteur OTLP/HTTP. Les
    # noms et attributs exportés restent fermés dans ``app.core.tracing``.
    trace_export_backend: Literal["disabled", "otlp_http"] = Field(
        default="disabled"
    )
    otlp_traces_endpoint: str | None = Field(default=None, max_length=2048)
    otlp_trace_export_token: str | None = Field(default=None)
    trace_export_sample_ratio: float = Field(default=0.1, gt=0.0, le=1.0)
    trace_export_timeout_seconds: float = Field(default=2.0, ge=0.1, le=5.0)

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

    @field_validator("otlp_trace_export_token")
    @classmethod
    def validate_otlp_trace_export_token(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return None
        if (
            value != value.strip()
            or not 32 <= len(value) <= 512
            or not value.isascii()
            or any(character.isspace() or not character.isprintable() for character in value)
        ):
            raise ValueError(
                "OTLP_TRACE_EXPORT_TOKEN must be 32-512 printable non-whitespace ASCII characters"
            )
        return value

    @field_validator("rate_limit_identity_secret")
    @classmethod
    def validate_rate_limit_identity_secret(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None or value == "":
            return None
        if (
            value != value.strip()
            or not 32 <= len(value) <= 256
            or not value.isascii()
            or any(
                character.isspace() or not character.isprintable()
                for character in value
            )
        ):
            raise ValueError(
                "RATE_LIMIT_IDENTITY_SECRET must be 32-256 printable "
                "non-whitespace ASCII characters"
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
    # Projection Product/Variant Graph strictement shadow. Elle exige la preuve
    # RawSource/Observation et ne change jamais les lectures catalogue v1.
    product_graph_shadow_enabled: bool = Field(default=False)
    # Persistance des profils et décisions Entity Resolution Phase 2. Le flag
    # ne promeut aucun lecteur et exige les preuves Observation/Product Graph.
    entity_resolution_shadow_enabled: bool = Field(default=False)
    # Projection append-only des preuves offre. Elle accepte une identité
    # produit non résolue, mais ne la rend jamais éligible.
    offer_graph_shadow_enabled: bool = Field(default=False)
    # Snapshot Offer Truth temporel append-only. Le flag ne démarre aucun
    # replay et exige toutes les preuves Graph nécessaires à une Variant.
    offer_truth_shadow_enabled: bool = Field(default=False)
    # Assertions ontologiques append-only. Aucun lecteur public n'en dépend et
    # le replay reste sec sans opt-in explicite du processus de maintenance.
    product_ontology_shadow_enabled: bool = Field(default=False)
    # Runs et candidats Hybrid Retrieval append-only. Aucun texte de requête
    # brut ni lecteur public ; le writer de maintenance reste OFF par défaut.
    hybrid_retrieval_shadow_enabled: bool = Field(default=False)
    # Évaluations de contraintes append-only, sans contexte brut, scoring ni
    # lecteur public. Le writer de maintenance reste OFF par défaut.
    constraint_engine_shadow_enabled: bool = Field(default=False)
    # Mesures agrégées append-only, sans score ni confiance synthétique.
    merchant_intelligence_shadow_enabled: bool = Field(default=False)
    # Claims sourcés et décision strictement shadow ; aucune lecture publique.
    evidence_engine_shadow_enabled: bool = Field(default=False)

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
