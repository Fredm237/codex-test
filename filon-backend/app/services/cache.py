"""Cache Redis optionnel — refonte 2026.

Améliorations :
- Sérialisation JSON structurée (pas juste des strings)
- TTL par type de donnée (recommandations, catalogue, highlights)
- Cache mémoire local (LRU) en fallback quand Redis est absent
- Métriques de hit/miss pour l'observabilité
- Invalidation par préfixe (pour les syncs catalogue)
"""

from __future__ import annotations

import hashlib
import json
import time
from functools import lru_cache
from typing import Any

from app.core.config import get_settings
from app.core.logging import get_logger

log = get_logger("cache")

# TTL par type de donnée (en secondes)
TTL_RECOMMEND = 1800       # 30 min — les recommandations LLM sont coûteuses
TTL_CATALOG = 300          # 5 min — les données catalogue changent peu
TTL_HIGHLIGHTS = 600       # 10 min — les highlights sont calculés à partir de la base
TTL_CATEGORIES = 3600      # 1h — la taxonomie est quasi-statique
TTL_DEFAULT = 600          # 10 min par défaut


class CacheMetrics:
    """Compteurs simples de hit/miss pour le health check."""

    def __init__(self) -> None:
        self.hits = 0
        self.misses = 0
        self.errors = 0

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    def to_dict(self) -> dict:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "errors": self.errors,
            "hit_rate": round(self.hit_rate, 3),
        }


class LocalLRUCache:
    """Cache mémoire LRU simple pour quand Redis est absent."""

    def __init__(self, max_size: int = 256) -> None:
        self._store: dict[str, tuple[Any, float]] = {}
        self._max_size = max_size

    def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if time.time() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl: int) -> None:
        if len(self._store) >= self._max_size:
            # Éviction de l'entrée la plus ancienne
            oldest_key = min(self._store, key=lambda k: self._store[k][1])
            del self._store[oldest_key]
        self._store[key] = (value, time.time() + ttl)

    def invalidate_prefix(self, prefix: str) -> int:
        keys = [k for k in self._store if k.startswith(prefix)]
        for k in keys:
            del self._store[k]
        return len(keys)


class Cache:
    """Cache hybride Redis + LRU local."""

    def __init__(self) -> None:
        self._client = None
        self._local = LocalLRUCache()
        self.metrics = CacheMetrics()
        url = get_settings().redis_url
        if url:
            try:
                import redis.asyncio as redis

                self._client = redis.from_url(url, decode_responses=True)
                log.info("Cache Redis connecté")
            except Exception as exc:
                log.warning("Redis indisponible (%s) → cache local LRU", exc)

    @property
    def enabled(self) -> bool:
        return True  # Toujours actif (local ou Redis)

    @property
    def redis_enabled(self) -> bool:
        return self._client is not None

    async def get_json(self, key: str) -> Any | None:
        """Récupère une valeur JSON depuis le cache."""
        # Essai Redis d'abord
        if self._client:
            try:
                raw = await self._client.get(key)
                if raw is not None:
                    self.metrics.hits += 1
                    return json.loads(raw)
            except Exception as exc:
                self.metrics.errors += 1
                log.debug("Redis get error (%s): %s", key, exc)

        # Fallback local
        value = self._local.get(key)
        if value is not None:
            self.metrics.hits += 1
            return value

        self.metrics.misses += 1
        return None

    async def set_json(self, key: str, value: Any, ttl: int = TTL_DEFAULT) -> None:
        """Stocke une valeur JSON dans le cache."""
        # Toujours stocker en local
        self._local.set(key, value, ttl)

        # Et dans Redis si disponible
        if self._client:
            try:
                await self._client.set(key, json.dumps(value, ensure_ascii=False), ex=ttl)
            except Exception as exc:
                self.metrics.errors += 1
                log.debug("Redis set error (%s): %s", key, exc)

    async def invalidate_prefix(self, prefix: str) -> int:
        """Invalide toutes les clés commençant par un préfixe."""
        count = self._local.invalidate_prefix(prefix)
        if self._client:
            try:
                cursor = 0
                while True:
                    cursor, keys = await self._client.scan(cursor, match=f"{prefix}*", count=100)
                    if keys:
                        await self._client.delete(*keys)
                        count += len(keys)
                    if cursor == 0:
                        break
            except Exception as exc:
                self.metrics.errors += 1
                log.debug("Redis invalidate error (%s): %s", prefix, exc)
        return count

    # Rétro-compatibilité avec l'ancienne API
    async def get(self, key: str) -> str | None:
        result = await self.get_json(key)
        return str(result) if result is not None else None

    async def set(self, key: str, value: str, ttl: int = TTL_DEFAULT) -> None:
        await self.set_json(key, value, ttl)


_cache: Cache | None = None


def get_cache() -> Cache:
    global _cache
    if _cache is None:
        _cache = Cache()
    return _cache


def cache_key(*parts: str) -> str:
    """Génère une clé de cache déterministe à partir de segments."""
    raw = ":".join(str(p) for p in parts)
    return f"filon:{hashlib.md5(raw.encode()).hexdigest()[:12]}:{parts[0]}"
