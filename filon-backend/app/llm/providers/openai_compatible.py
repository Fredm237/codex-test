"""Fournisseur générique pour toute API compatible OpenAI.

DeepSeek, Kimi (Moonshot) et GLM (Zhipu) exposent tous une API de type
``/chat/completions`` compatible OpenAI. On les couvre donc avec une seule
implémentation paramétrée par (base_url, api_key, model).
"""

from __future__ import annotations

import httpx

from app.llm.base import LLMProvider, Message


class OpenAICompatibleProvider(LLMProvider):
    def __init__(
        self,
        *,
        name: str,
        base_url: str,
        api_key: str,
        model: str,
        timeout: float = 30.0,
    ) -> None:
        self.name = name
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._timeout = timeout

    async def complete(
        self, messages: list[Message], *, temperature: float = 0.2
    ) -> str:
        payload = {
            "model": self._model,
            "temperature": temperature,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }
        headers = {"Authorization": f"Bearer {self._api_key}"}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(
                f"{self._base_url}/chat/completions", json=payload, headers=headers
            )
            resp.raise_for_status()
            data = resp.json()
        return data["choices"][0]["message"]["content"]

    async def complete_json(
        self, messages: list[Message], *, temperature: float = 0.0
    ) -> str:
        # Les trois fournisseurs acceptent response_format json_object.
        payload = {
            "model": self._model,
            "temperature": temperature,
            "response_format": {"type": "json_object"},
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }
        headers = {"Authorization": f"Bearer {self._api_key}"}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(
                f"{self._base_url}/chat/completions", json=payload, headers=headers
            )
            resp.raise_for_status()
            data = resp.json()
        return data["choices"][0]["message"]["content"]
