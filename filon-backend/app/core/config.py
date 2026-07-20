"""Configuration centrale, lue depuis l'environnement (.env)."""

from __future__ import annotations

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
    cors_origins: list[str] = Field(default=["*"])

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
