"""Configuration centrale, lue depuis l'environnement (.env)."""

from __future__ import annotations

import json
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Application
    app_name: str = "FILON AI"
    env: str = Field(default="dev")
    debug: bool = Field(default=True)
    # Gardé en chaîne pour ne jamais planter au démarrage : accepte "*", une
    # liste JSON, ou une liste séparée par des virgules (voir cors_origins_list).
    cors_origins: str = Field(default="*")

    @property
    def cors_origins_list(self) -> list[str]:
        raw = (self.cors_origins or "").strip()
        if raw in ("", "*"):
            return ["*"]
        if raw.startswith("["):
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list) and parsed:
                    return [str(o).strip() for o in parsed]
            except (json.JSONDecodeError, TypeError):
                pass
        return [o.strip() for o in raw.split(",") if o.strip()] or ["*"]

    # Infrastructure (optionnelle au runtime : dégradation propre si absente)
    database_url: str | None = Field(default=None)
    redis_url: str | None = Field(default=None)
    qdrant_url: str | None = Field(default=None)

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
    # Nombre max de lignes ingérées par feed (garde-fou mémoire ; 0 = illimité).
    awin_max_rows_per_feed: int = Field(default=0)
    # Synchronisation automatique du catalogue toutes les N heures (0 = désactivé).
    # Mettre 6 sur Railway pour rafraîchir prix + alimenter l'historique sans rien
    # relancer à la main. Nécessite AWIN_FEED_API_KEY et une base de données.
    awin_auto_sync_hours: int = Field(default=0)

    @property
    def awin_regions_list(self) -> list[str]:
        return [r.strip().upper() for r in (self.awin_regions or "").split(",") if r.strip()]

    # Jeton protégeant les endpoints d'administration (déclenchement d'un sync).
    # SECRET → env ADMIN_SYNC_TOKEN. Sans valeur, les endpoints admin sont fermés.
    admin_sync_token: str | None = Field(default=None)


@lru_cache
def get_settings() -> Settings:
    return Settings()
