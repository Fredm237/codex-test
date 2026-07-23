"""Interface commune à tous les fournisseurs LLM.

La couche d'abstraction permet de changer de modèle (DeepSeek, Kimi, GLM…)
sans toucher au code des agents.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass


@dataclass
class Message:
    role: str  # "system" | "user" | "assistant"
    content: str


class LLMProvider(abc.ABC):
    """Un fournisseur LLM interchangeable."""

    name: str = "base"

    @abc.abstractmethod
    async def complete(
        self, messages: list[Message], *, temperature: float = 0.2
    ) -> str:
        """Retourne la complétion textuelle du modèle."""

    async def complete_json(
        self, messages: list[Message], *, temperature: float = 0.0
    ) -> str:
        """Complétion destinée à produire du JSON. Par défaut identique."""
        return await self.complete(messages, temperature=temperature)
