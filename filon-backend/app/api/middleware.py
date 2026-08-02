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

    # Le rendu serveur de Vercel sort par quelques adresses partagées : une
    # limite par IP compte donc *toutes* les pages régénérées ensemble, pas un
    # visiteur. Une page catalogue déclenche à elle seule quatre appels ; à
    # 120/min, une trentaine de régénérations suffisaient à nous limiter
    # nous-mêmes, et le site affichait « catalogue momentanément indisponible ».
    #
    # Les lectures de catalogue sont donc exemptées : elles sont mises en cache,
    # ne coûtent rien et ne sont pas la cible d'un abus. Le garde-fou reste là
    # où il sert — les endpoints qui appellent un modèle.
    _EXEMPT_PREFIXES = ("/health", "/api/catalog")

    # Nombre d'adresses suivies simultanément. Sans plafond, le dictionnaire
    # gardait une entrée par IP vue depuis le démarrage : une fuite lente, sur
    # un service dont la mémoire a déjà saturé une fois.
    _MAX_TRACKED_IPS = 10_000

    def __init__(self, app, expensive_limit: int = 30, general_limit: int = 240):
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
        recent = [t for t in self._requests[ip] if now - t < window]

        # Purge périodique des adresses devenues inactives : c'est la seule
        # chose qui empêche le dictionnaire de croître indéfiniment.
        if len(self._requests) > self._MAX_TRACKED_IPS:
            for stale, times in list(self._requests.items()):
                if not times or now - times[-1] >= window:
                    del self._requests[stale]

        if len(recent) >= limit:
            self._requests[ip] = recent
            return True

        recent.append(now)
        self._requests[ip] = recent
        return False

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path
        if path.startswith(self._EXEMPT_PREFIXES):
            return await call_next(request)

        ip = self._get_client_ip(request)

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
