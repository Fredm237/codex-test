"""Middlewares FastAPI — Refonte 2026.

Middlewares :
- RequestLogging : log structuré de chaque requête (méthode, path, status, latence)
- RateLimiter : protection basique contre les abus (par IP, en mémoire)
"""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger

log = get_logger("http")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log structuré de chaque requête HTTP.

    Format : METHOD /path → STATUS (latence_ms)
    Les health checks sont exclus pour éviter le bruit.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Exclure les health checks du logging
        if request.url.path.startswith("/health"):
            return await call_next(request)

        start = time.time()
        response = await call_next(request)
        elapsed = (time.time() - start) * 1000

        # Log avec niveau adapté au status code
        status = response.status_code
        method = request.method
        path = request.url.path

        if status >= 500:
            log.error("%s %s → %d (%.0fms)", method, path, status, elapsed)
        elif status >= 400:
            log.warning("%s %s → %d (%.0fms)", method, path, status, elapsed)
        elif elapsed > 5000:
            log.warning("%s %s → %d (%.0fms) SLOW", method, path, status, elapsed)
        else:
            log.info("%s %s → %d (%.0fms)", method, path, status, elapsed)

        # Headers de performance pour le frontend
        response.headers["X-Response-Time"] = f"{elapsed:.0f}ms"
        response.headers["X-Request-Id"] = str(id(request))

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting basique par IP (en mémoire).

    Protège les endpoints coûteux (LLM, streaming) contre les abus.
    Limites : 30 requêtes/minute pour /api/advise, 60/min pour le reste.
    """

    def __init__(self, app, expensive_limit: int = 30, general_limit: int = 120):
        super().__init__(app)
        self._expensive_limit = expensive_limit
        self._general_limit = general_limit
        self._requests: dict[str, list[float]] = defaultdict(list)

    def _get_client_ip(self, request: Request) -> str:
        """Récupère l'IP du client (supporte les proxies)."""
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _is_rate_limited(self, ip: str, limit: int) -> bool:
        """Vérifie si l'IP a dépassé la limite sur la dernière minute."""
        now = time.time()
        window = 60.0  # 1 minute

        # Nettoyage des entrées expirées
        self._requests[ip] = [t for t in self._requests[ip] if now - t < window]

        if len(self._requests[ip]) >= limit:
            return True

        self._requests[ip].append(now)
        return False

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Pas de rate limiting sur les health checks
        if request.url.path.startswith("/health"):
            return await call_next(request)

        ip = self._get_client_ip(request)
        path = request.url.path

        # Limite plus stricte pour les endpoints coûteux
        is_expensive = "/advise" in path or "/chat" in path
        limit = self._expensive_limit if is_expensive else self._general_limit

        if self._is_rate_limited(ip, limit):
            log.warning("Rate limit atteint pour %s sur %s", ip, path)
            return Response(
                content='{"error": "Too many requests. Please wait a moment."}',
                status_code=429,
                media_type="application/json",
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(limit),
                },
            )

        return await call_next(request)
