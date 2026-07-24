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


@lru_cache
def get_settings() -> Settings:
    return Settings()
