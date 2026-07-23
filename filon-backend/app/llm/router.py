"""Routeur LLM : choisit le fournisseur selon la tâche.

  - default   : conversations, orchestration (DeepSeek recommandé)
  - reasoning : décision, recommandations argumentées
  - long      : analyses longues / recherches complexes (Kimi recommandé)

Si la clé d'un fournisseur configuré est absente, on retombe proprement sur
le fournisseur ``mock`` afin que le système reste fonctionnel sans budget.
"""

from __future__ import annotations

from functools import lru_cache

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.llm.base import LLMProvider, Message
from app.llm.providers.mock import MockProvider
from app.llm.providers.openai_compatible import OpenAICompatibleProvider

log = get_logger("llm.router")


class LLMRouter:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._mock = MockProvider()
        self._cache: dict[str, LLMProvider] = {}

    def _build(self, provider_key: str) -> LLMProvider:
        s = self._settings
        if provider_key == "deepseek" and s.deepseek_api_key:
            return OpenAICompatibleProvider(
                name="deepseek",
                base_url=s.deepseek_base_url,
                api_key=s.deepseek_api_key,
                model=s.deepseek_model,
                timeout=s.llm_timeout_seconds,
            )
        if provider_key == "kimi" and s.kimi_api_key:
            return OpenAICompatibleProvider(
                name="kimi",
                base_url=s.kimi_base_url,
                api_key=s.kimi_api_key,
                model=s.kimi_model,
                timeout=s.llm_timeout_seconds,
            )
        if provider_key == "glm" and s.glm_api_key:
            return OpenAICompatibleProvider(
                name="glm",
                base_url=s.glm_base_url,
                api_key=s.glm_api_key,
                model=s.glm_model,
                timeout=s.llm_timeout_seconds,
            )
        if provider_key != "mock":
            log.warning("Fournisseur '%s' indisponible (clé absente) → mock", provider_key)
        return self._mock

    def for_task(self, task: str) -> LLMProvider:
        mapping = {
            "default": self._settings.llm_provider_default,
            "reasoning": self._settings.llm_provider_reasoning,
            "long": self._settings.llm_provider_long,
        }
        key = mapping.get(task, self._settings.llm_provider_default)
        if key not in self._cache:
            self._cache[key] = self._build(key)
        return self._cache[key]


@lru_cache
def get_router() -> LLMRouter:
    return LLMRouter(get_settings())


__all__ = ["LLMRouter", "get_router", "Message"]
