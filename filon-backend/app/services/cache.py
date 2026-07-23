"""Cache Redis optionnel.

Si REDIS_URL n'est pas configuré (ou Redis indisponible), le cache devient un
no-op : l'application continue de fonctionner, sans accélération.
"""

from __future__ import annotations

from app.core.config import get_settings
from app.core.logging import get_logger

log = get_logger("cache")


class Cache:
    def __init__(self) -> None:
        self._client = None
        url = get_settings().redis_url
        if url:
            try:
                import redis.asyncio as redis

                self._client = redis.from_url(url, decode_responses=True)
            except Exception as exc:  # pragma: no cover
                log.warning("Redis indisponible (%s) → cache désactivé", exc)

    @property
    def enabled(self) -> bool:
        return self._client is not None

    async def get(self, key: str) -> str | None:
        if not self._client:
            return None
        try:
            return await self._client.get(key)
        except Exception:  # pragma: no cover
            return None

    async def set(self, key: str, value: str, ttl: int = 3600) -> None:
        if not self._client:
            return
        try:
            await self._client.set(key, value, ex=ttl)
        except Exception:  # pragma: no cover
            pass


_cache: Cache | None = None


def get_cache() -> Cache:
    global _cache
    if _cache is None:
        _cache = Cache()
    return _cache
