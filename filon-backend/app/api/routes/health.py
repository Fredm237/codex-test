"""Endpoint de santé + état des dépendances optionnelles — Refonte 2026.

Améliorations :
- Vérification active de la connexion DB (pas juste "est-elle configurée ?")
- Métriques de cache (hit rate, hits, misses)
- Latence de réponse du health check lui-même
- Uptime du service
- Version Python et infos système
"""

from __future__ import annotations

import asyncio
import platform
import secrets
import sys
import time
from typing import Annotated

from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse, Response
from sqlalchemy import text

from app import __version__
from app.core.config import get_settings
from app.core.metrics_export import (
    OPENMETRICS_CONTENT_TYPE,
    MetricsExportError,
    render_openmetrics,
)
from app.core.observability import product_intelligence_metrics, request_metrics
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
    except Exception:
        return {
            "status": "error",
            "error_code": "database_probe_failed",
            "latency_ms": 0,
        }


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
    except Exception:
        return {
            "status": "error",
            "error_code": "redis_probe_failed",
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

    # Statut global : "ok" seulement si les dépendances critiques répondent.
    #
    # « slow » comptait auparavant comme sain, et c'est ce qui a rendu la sonde
    # inutile : une base qui ne répond pas à `SELECT 1` en deux secondes ne sert
    # plus une seule requête — tous les endpoints du catalogue rendaient 500
    # pendant que /health affichait « ok ». Une sonde qui ne bouge pas quand le
    # service est à terre ne surveille rien.
    #
    # « slow » reste distinct d'« error » dans le détail des dépendances : c'est
    # ce qui permet à l'hébergeur de ne pas redémarrer un service dont la base
    # répond, en retard. Mais le statut global, lui, doit le dire.
    overall = "ok"
    if db_status["status"] in ("error", "slow"):
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
async def readiness() -> JSONResponse:
    """Refuse le trafic si la base ou sa révision ne sont pas prêtes."""
    settings = get_settings()
    database = await _check_db()
    schema: dict[str, object]

    if database["status"] == "disabled":
        schema = {"status": "disabled"}
        ready = settings.env.lower() in {"dev", "development", "local", "test"}
    elif database["status"] != "ok":
        schema = {"status": "not_checked"}
        ready = False
    else:
        try:
            await asyncio.wait_for(
                db.assert_schema_current(),
                timeout=_DB_CHECK_TIMEOUT,
            )
            schema = {"status": "ok", "revision": db.CURRENT_SCHEMA_REVISION}
            ready = True
        except asyncio.TimeoutError:
            schema = {"status": "slow"}
            ready = False
        except Exception:
            schema = {"status": "error", "error_code": "schema_revision_invalid"}
            ready = False

    payload = {
        "ready": ready,
        "version": __version__,
        "database": database,
        "schema": schema,
    }
    return JSONResponse(status_code=200 if ready else 503, content=payload)


@router.get("/health/live")
async def liveness() -> dict:
    """Liveness probe pour Kubernetes/Railway.

    Retourne 200 tant que le processus est vivant.
    """
    return {"alive": True, "uptime_seconds": round(time.time() - _START_TIME)}


@router.get("/health/metrics")
async def metrics() -> dict:
    """Métriques agrégées sans requête, payload, IP ni identifiant produit."""
    snapshot = request_metrics.snapshot()
    snapshot["product_intelligence"] = product_intelligence_metrics.snapshot()
    return snapshot


@router.get("/health/metrics/openmetrics", include_in_schema=False)
async def openmetrics(
    authorization: Annotated[str | None, Header()] = None,
) -> Response:
    """Export OpenMetrics authentifié ; désactivé sans secret explicite."""
    token = get_settings().metrics_export_token
    if token is None:
        return JSONResponse(
            status_code=503,
            content={"error": "metrics_export_disabled"},
            headers={"Cache-Control": "no-store"},
        )

    expected = f"Bearer {token}"
    if authorization is None or not secrets.compare_digest(authorization, expected):
        return JSONResponse(
            status_code=401,
            content={"error": "unauthorized"},
            headers={
                "Cache-Control": "no-store",
                "WWW-Authenticate": "Bearer",
            },
        )

    try:
        payload = render_openmetrics(
            request_metrics.snapshot(),
            product_intelligence_metrics.snapshot(),
        )
    except MetricsExportError:
        return JSONResponse(
            status_code=503,
            content={"error": "metrics_export_invalid"},
            headers={"Cache-Control": "no-store"},
        )

    return Response(
        content=payload,
        headers={
            "Cache-Control": "no-store",
            "Content-Type": OPENMETRICS_CONTENT_TYPE,
        },
    )
