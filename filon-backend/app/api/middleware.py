"""Middlewares FastAPI — Refonte 2026.

Middlewares :
- RequestLogging : log structuré de chaque requête (méthode, path, status, latence)
- RateLimiter : protection basique contre les abus (par IP, en mémoire)
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import threading
import time
from array import array
from collections import OrderedDict
from dataclasses import dataclass
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger
from app.core.observability import (
    bind_request_id_context,
    normalize_request_id,
    request_id_context,
    request_metrics,
)

log = get_logger("http")


@dataclass(slots=True)
class _RateWindow:
    timestamps: array
    start: int
    size: int
    last_seen: float


@dataclass(slots=True)
class _RateLimitLogWindow:
    last_log: float
    suppressed: int = 0


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log structuré de chaque requête HTTP.

    Format : METHOD /path → STATUS (latence_ms)
    Les health checks sont exclus pour éviter le bruit.
    """

    _RATE_LIMIT_LOG_INTERVAL_SECONDS = 60.0
    _MAX_RATE_LIMIT_LOG_ROUTES = 100
    _MAX_SUPPRESSED_LOGS = 2_147_483_647

    def __init__(self, app):
        super().__init__(app)
        self._rate_limit_log_windows: dict[str, _RateLimitLogWindow] = {}
        self._rate_limit_log_lock = threading.Lock()

    def _rate_limit_log_decision(
        self,
        route: str,
        *,
        now: float,
    ) -> tuple[bool, int]:
        """Échantillonne les 429 : au plus un log par route et par minute."""
        with self._rate_limit_log_lock:
            key = route
            if (
                key not in self._rate_limit_log_windows
                and len(self._rate_limit_log_windows)
                >= self._MAX_RATE_LIMIT_LOG_ROUTES - 1
            ):
                key = "OTHER"

            current = self._rate_limit_log_windows.get(key)
            if current is None:
                self._rate_limit_log_windows[key] = _RateLimitLogWindow(
                    last_log=now,
                )
                return True, 0

            elapsed = now - current.last_log
            if elapsed < 0 or elapsed >= self._RATE_LIMIT_LOG_INTERVAL_SECONDS:
                suppressed = current.suppressed
                current.last_log = now
                current.suppressed = 0
                return True, suppressed

            current.suppressed = min(
                current.suppressed + 1,
                self._MAX_SUPPRESSED_LOGS,
            )
            return False, current.suppressed

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = normalize_request_id(request.headers.get("x-request-id"))
        token = bind_request_id_context(request_id)
        request.scope["filon.request_id"] = request_id
        start = time.monotonic()
        method = request.method
        path = request.url.path
        error_type: str | None = None
        try:
            response = await call_next(request)
        except Exception as exc:
            error_type = type(exc).__name__
            # Ne pas relancer jusqu'au serveur ASGI : son traceback inclurait
            # le message de l'exception. La réponse reste générique, corrélée
            # et observable par le type d'erreur uniquement.
            response = Response(
                content='{"error":"internal_error"}',
                status_code=500,
                media_type="application/json",
            )
        finally:
            request_id_context.reset(token)

        elapsed = (time.monotonic() - start) * 1000
        status = response.status_code
        route_object = request.scope.get("route")
        route = str(
            getattr(
                route_object,
                "path",
                request.scope.get("filon.rate_limit_bucket", "<unmatched>"),
            )
        )

        is_quiet_liveness = (
            method.upper() in {"GET", "HEAD"}
            and path == "/health/live"
        )
        if not is_quiet_liveness:
            request_metrics.record(
                method=method,
                route=route,
                status_code=status,
                elapsed_ms=elapsed,
            )
            args = (request_id, method, route, status, elapsed)
            if status >= 500:
                if error_type is None:
                    log.error("request_id=%s %s %s → %d (%.0fms)", *args)
                else:
                    log.error(
                        "request_id=%s %s %s → %d (%.0fms) error_type=%s",
                        *args,
                        error_type,
                    )
            elif status == 429:
                should_log, suppressed = self._rate_limit_log_decision(
                    route,
                    now=time.monotonic(),
                )
                if should_log:
                    log.warning(
                        "request_id=%s %s %s → %d (%.0fms) "
                        "rate_limit suppressed_since_last=%d",
                        *args,
                        suppressed,
                    )
            elif status >= 400:
                log.warning("request_id=%s %s %s → %d (%.0fms)", *args)
            elif elapsed > 5000:
                log.warning(
                    "request_id=%s %s %s → %d (%.0fms) SLOW",
                    *args,
                )
            else:
                log.info("request_id=%s %s %s → %d (%.0fms)", *args)

        response.headers["X-Response-Time"] = f"{elapsed:.0f}ms"
        response.headers["X-Request-Id"] = request_id
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting local par identité réseau pseudonymisée.

    Protège les endpoints coûteux (LLM, streaming, agrégats) contre les abus.
    Limites : 30 requêtes/minute pour la classe coûteuse, 240/min pour le reste.

    L'adresse provient exclusivement du scope ASGI. Le serveur peut la
    reconstruire depuis des en-têtes proxy uniquement si le pair est dans sa
    propre allowlist ; ce middleware ne lit jamais ``X-Forwarded-For``.
    """

    # Le rendu serveur de Vercel peut partager une même adresse entre plusieurs
    # visites. Le quota général reste donc plus large que celui des traitements
    # coûteux, mais aucune lecture catalogue n'est illimitée : certaines
    # agrégations balayent des millions de lignes quand leur cache est froid.
    _READ_METHODS = frozenset({"GET", "HEAD"})
    _LIVENESS_PATH = "/health/live"
    _EXPENSIVE_PREFIXES = (
        "/health",
        "/api/advise",
        "/api/chat",
        "/api/intelligence/outfit",
        "/api/catalog/admin",
        "/api/catalog/categories",
        "/api/catalog/debug",
        "/api/catalog/facets",
        "/api/catalog/highlights",
        "/api/catalog/pulse",
        "/api/catalog/relief",
        "/api/catalog/sitemap/products",
        "/api/catalog/stats",
        "/api/catalog/sync",
    )
    _POLICY_CLASSES = frozenset({"expensive", "general"})
    _WINDOW_SECONDS = 60.0

    # Nombre de couples pseudonyme/classe suivis simultanément. Sans plafond,
    # le dictionnaire gardait une entrée par adresse vue depuis le démarrage :
    # une fuite lente, sur un service dont la mémoire a déjà saturé une fois.
    _MAX_TRACKED_IDENTITIES = 10_000

    def __init__(
        self,
        app,
        expensive_limit: int = 30,
        general_limit: int = 240,
        *,
        max_tracked_identities: int = _MAX_TRACKED_IDENTITIES,
        clock: Callable[[], float] | None = None,
    ):
        super().__init__(app)
        if expensive_limit < 1 or general_limit < 1:
            raise ValueError("Les limites doivent être strictement positives")
        if max_tracked_identities < 1:
            raise ValueError(
                "Le plafond d'identités doit être strictement positif"
            )
        self._expensive_limit = expensive_limit
        self._general_limit = general_limit
        self._max_tracked_identities = max_tracked_identities
        self._clock = clock or time.monotonic
        self._identity_secret = secrets.token_bytes(32)
        self._windows: OrderedDict[str, _RateWindow] = OrderedDict()
        self._lock = threading.Lock()

    @staticmethod
    def _path_is_under(path: str, prefix: str) -> bool:
        return path == prefix or path.startswith(f"{prefix}/")

    @classmethod
    def _is_exempt(cls, method: str, path: str) -> bool:
        """Exempte seulement les sondes de santé en lecture."""
        if method.upper() not in cls._READ_METHODS:
            return False
        return path == cls._LIVENESS_PATH

    @classmethod
    def _policy_class(cls, path: str) -> str:
        is_expensive = any(
            cls._path_is_under(path, prefix)
            for prefix in cls._EXPENSIVE_PREFIXES
        )
        return (
            "expensive"
            if is_expensive
            else "general"
        )

    @classmethod
    def _policy_bucket(cls, path: str) -> str:
        """Retourne un label fermé quand le routeur n'a pas encore tourné."""
        for prefix in cls._EXPENSIVE_PREFIXES:
            if cls._path_is_under(path, prefix):
                return f"<rate-limit:{prefix}>"
        return "<rate-limit:general>"

    @staticmethod
    def _get_client_address(request: Request) -> str:
        """Lit seulement l'adresse déjà validée dans le scope ASGI."""
        return request.client.host if request.client else "unknown"

    def _identity_key(self, client_address: str, policy_class: str) -> str:
        digest = hmac.new(
            self._identity_secret,
            client_address.encode("utf-8", errors="replace"),
            hashlib.sha256,
        ).hexdigest()
        return f"{policy_class}:{digest}"

    def _purge_inactive_locked(self, now: float) -> None:
        while self._windows:
            _key, oldest = next(iter(self._windows.items()))
            if now < oldest.last_seen:
                # ``monotonic`` ne recule pas ; une horloge injectée qui le fait
                # invalide toutes les fenêtres plutôt que de les conserver.
                self._windows.clear()
                return
            if now - oldest.last_seen < self._WINDOW_SECONDS:
                return
            self._windows.popitem(last=False)

    @classmethod
    def _consume_window(
        cls,
        current: _RateWindow,
        *,
        now: float,
        limit: int,
    ) -> bool:
        if now < current.last_seen:
            current.start = 0
            current.size = 0

        while current.size:
            oldest = current.timestamps[current.start]
            if now - oldest < cls._WINDOW_SECONDS:
                break
            current.start = (current.start + 1) % limit
            current.size -= 1

        current.last_seen = now
        if current.size >= limit:
            return True

        insertion = (current.start + current.size) % limit
        current.timestamps[insertion] = now
        current.size += 1
        return False

    def _is_rate_limited(
        self,
        client_address: str,
        *,
        policy_class: str = "general",
    ) -> bool:
        """Compte sans conserver l'adresse brute et sans dépasser le plafond."""
        if policy_class not in self._POLICY_CLASSES:
            raise ValueError("Classe de rate limit inconnue")

        limit = (
            self._expensive_limit
            if policy_class == "expensive"
            else self._general_limit
        )
        identity_key = self._identity_key(client_address, policy_class)
        with self._lock:
            # Le temps doit être lu sous le même verrou que la mutation. Sinon,
            # deux threads peuvent obtenir t2 puis t3 et entrer dans l'ordre
            # inverse ; le plus ancien ressemble alors à un recul d'horloge et
            # viderait à tort toutes les fenêtres.
            now = self._clock()
            self._purge_inactive_locked(now)

            current = self._windows.get(identity_key)
            if current is None and len(self._windows) >= self._max_tracked_identities:
                # Fail-closed : aucune nouvelle identité n'alloue de mémoire et
                # aucune fenêtre partagée ne lui accorde un quota supplémentaire.
                return True

            if current is None:
                current = _RateWindow(
                    timestamps=array("d", [0.0]) * limit,
                    start=0,
                    size=0,
                    last_seen=now,
                )
                self._windows[identity_key] = current

            limited = self._consume_window(current, now=now, limit=limit)
            self._windows.move_to_end(identity_key)
            return limited

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path
        if self._is_exempt(request.method, path):
            return await call_next(request)

        client_address = self._get_client_address(request)

        # Limite plus stricte pour les endpoints coûteux
        policy_class = self._policy_class(path)
        is_expensive = policy_class == "expensive"
        limit = self._expensive_limit if is_expensive else self._general_limit

        if self._is_rate_limited(
            client_address,
            policy_class=policy_class,
        ):
            request.scope["filon.rate_limit_bucket"] = self._policy_bucket(path)
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
