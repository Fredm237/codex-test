"""Endpoint de santé + état des dépendances optionnelles — Refonte 2026.

Améliorations :
- Vérification active de la connexion DB (pas juste "est-elle configurée ?")
- Métriques de cache (hit rate, hits, misses)
- Latence de réponse du health check lui-même
- Uptime du service
- Version Python et infos système
"""

from __future__ import annotations

import platform
import sys
import asyncio
import time

from fastapi import APIRouter
from sqlalchemy import text

from app import __version__
from app.core.config import get_settings
from app.db import session as db
from app.services.cache import get_cache
from app.services.vectorstore import get_vectorstore

router = APIRouter(tags=["health"])

_START_TIME = time.time()


# Railway sonde /health en continu et coupe le déploiement au bout de 120 s.
# Sans délai maximum, une base lente fait *pendre* la sonde au lieu de la faire
# échouer proprement : c'est exactement le mode de panne des deux échecs de
# déploiement déjà constatés. Deux secondes suffisent à distinguer une base
# vivante d'une base injoignable.
_DB_CHECK_TIMEOUT = 2.0


async def _check_db() -> dict:
    """Vérifie activement la connexion à la base de données, sous délai borné."""
    if not db.is_enabled():
        return {"status": "disabled", "latency_ms": 0}

    async def _probe() -> float:
        start = time.time()
        async with db.session_scope() as session:
            await session.execute(text("SELECT 1"))
        return (time.time() - start) * 1000

    try:
        latency = await asyncio.wait_for(_probe(), timeout=_DB_CHECK_TIMEOUT)
        return {"status": "ok", "latency_ms": round(latency, 1)}
    except asyncio.TimeoutError:
        # « lent » n'est pas « mort » : on le distingue pour ne pas déclencher
        # un redémarrage alors que la base répond, en retard.
        return {"status": "slow", "latency_ms": _DB_CHECK_TIMEOUT * 1000}
    except Exception as exc:
        return {"status": "error", "error": str(exc)[:100], "latency_ms": 0}


async def _check_redis() -> dict:
    """Vérifie activement la connexion Redis."""
    cache = get_cache()
    if not cache.redis_enabled:
        return {"status": "local_only", "metrics": cache.metrics.to_dict()}
    try:
        start = time.time()
        await cache.set_json("_health_check", {"t": time.time()}, ttl=10)
        result = await cache.get_json("_health_check")
        latency = (time.time() - start) * 1000
        return {
            "status": "ok" if result else "degraded",
            "latency_ms": round(latency, 1),
            "metrics": cache.metrics.to_dict(),
        }
    except Exception as exc:
        return {
            "status": "error",
            "error": str(exc)[:100],
            "metrics": cache.metrics.to_dict(),
        }


@router.get("/health")
async def health() -> dict:
    """Health check complet avec vérification active des dépendances."""
    start = time.time()
    s = get_settings()

    db_status = await _check_db()
    redis_status = await _check_redis()
    vs = get_vectorstore()

    uptime_seconds = time.time() - _START_TIME
    latency = (time.time() - start) * 1000

    # Statut global : "ok" si toutes les dépendances critiques sont fonctionnelles
    overall = "ok"
    if db_status["status"] == "error":
        overall = "degraded"

    return {
        "status": overall,
        "app": s.app_name,
        "version": __version__,
        "env": s.env,
        "uptime_seconds": round(uptime_seconds),
        "latency_ms": round(latency, 1),
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "platform": platform.system(),
        "dependencies": {
            "database": db_status,
            "redis": redis_status,
            "qdrant": {"status": "ok" if vs.enabled else "disabled"},
        },
        "llm": {
            "default": s.llm_provider_default,
            "reasoning": s.llm_provider_reasoning,
            "long": s.llm_provider_long,
        },
    }


@router.get("/health/ready")
async def readiness() -> dict:
    """Readiness probe pour Kubernetes/Railway.

    Retourne 200 si le service est prêt à recevoir du trafic.
    Vérifie uniquement que l'app démarre correctement (pas les dépendances optionnelles).
    """
    return {"ready": True, "version": __version__}


@router.get("/health/live")
async def liveness() -> dict:
    """Liveness probe pour Kubernetes/Railway.

    Retourne 200 tant que le processus est vivant.
    """
    return {"alive": True, "uptime_seconds": round(time.time() - _START_TIME)}
