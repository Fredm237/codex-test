"""Front door : exemptions bornées, anti-spoofing et mémoire bornée."""

from __future__ import annotations

import asyncio
import json
import logging
import threading
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI, Request
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app import __main__ as app_entrypoint
from app import main as app_main
from app.api.middleware import RateLimitMiddleware, RequestLoggingMiddleware
from app.core.config import Settings
from app.core.distributed_rate_limit import (
    DistributedRateLimitUnavailable,
    RedisSlidingWindowRateLimiter,
    _ATOMIC_SLIDING_WINDOW_SCRIPT,
)
from app.core.logging import configure_logging
from app.core.observability import request_metrics


class _Clock:
    def __init__(self, value: float = 0.0):
        self.value = value

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


class _RedisDecisionClient:
    def __init__(self, decision: object = 0, error: Exception | None = None):
        self.decision = decision
        self.error = error
        self.calls: list[tuple[object, ...]] = []

    async def eval(self, *args: object) -> object:
        self.calls.append(args)
        if self.error is not None:
            raise self.error
        return self.decision


class _AtomicQuotaClient:
    def __init__(self, limit: int):
        self.limit = limit
        self.count = 0
        self.lock = asyncio.Lock()

    async def eval(self, *_args: object) -> int:
        async with self.lock:
            if self.count >= self.limit:
                return 1
            self.count += 1
            return 0


class _CloseableRedisClient(_RedisDecisionClient):
    def __init__(self):
        super().__init__()
        self.closed = False

    async def aclose(self) -> None:
        self.closed = True


def _limiter(**kwargs) -> RateLimitMiddleware:
    # L'app n'est pas sollicitée : on teste la mécanique de comptage.
    return RateLimitMiddleware(app=None, **kwargs)


class TestExemptions:
    @pytest.mark.parametrize(
        ("method", "path"),
        [
            ("GET", "/health/live"),
            ("HEAD", "/health/live"),
        ],
    )
    def test_seules_les_lectures_de_sante_sont_exemptees(self, method, path):
        assert RateLimitMiddleware._is_exempt(method, path) is True

    @pytest.mark.parametrize(
        ("method", "path"),
        [
            ("POST", "/api/catalog"),
            ("GET", "/api/catalog"),
            ("GET", "/api/catalog/offers"),
            ("HEAD", "/api/catalog/product/123"),
            ("POST", "/api/catalog/admin/rebuild-products"),
            ("GET", "/api/catalog/admin/unclassified"),
            ("HEAD", "/api/catalog/admin/unclassified"),
            ("GET", "/api/catalog/debug/feeds"),
            ("HEAD", "/api/catalog/debug/feeds"),
            ("POST", "/api/catalog/sync/feeds"),
            ("HEAD", "/api/catalog/sync/feeds"),
            ("GET", "/api/catalogue"),
            ("GET", "/healthcheck"),
            ("GET", "/health"),
            ("GET", "/health/ready"),
            ("GET", "/health/metrics"),
            ("GET", "/health/live/extra"),
            ("GET", "/api/advise/stream"),
        ],
    )
    def test_les_routes_sensibles_et_les_lookalikes_restent_limites(
        self,
        method,
        path,
    ):
        assert RateLimitMiddleware._is_exempt(method, path) is False

    @pytest.mark.parametrize(
        "path",
        [
            "/api/advise",
            "/api/advise/stream",
            "/api/chat",
            "/api/intelligence/outfit/analyse",
            "/api/intelligence/outfit/feedback",
            "/api/catalog/admin/rebuild-products",
            "/api/catalog/categories",
            "/api/catalog/debug/feeds",
            "/api/catalog/facets",
            "/api/catalog/highlights",
            "/api/catalog/pulse",
            "/api/catalog/relief",
            "/api/catalog/sitemap/products",
            "/api/catalog/stats",
            "/api/catalog/sync/feeds",
            "/health",
            "/health/ready",
            "/health/metrics",
        ],
    )
    def test_les_routes_couteuses_ont_la_classe_stricte(self, path):
        assert RateLimitMiddleware._policy_class(path) == "expensive"

    @pytest.mark.parametrize(
        "path",
        [
            "/api/catalog/offers",
            "/api/catalog/products",
            "/api/intelligence/status",
            "/api/intelligence/outfitter",
            "/api/adviser",
        ],
    )
    def test_les_routes_ordinaires_et_lookalikes_restent_generales(self, path):
        assert RateLimitMiddleware._policy_class(path) == "general"


class TestComptage:
    def test_bloque_apres_la_limite(self):
        limiter = _limiter(general_limit=3)
        for _ in range(3):
            assert limiter._is_rate_limited("1.2.3.4") is False
        assert limiter._is_rate_limited("1.2.3.4") is True

    def test_les_adresses_sont_comptees_separement_sans_etre_stockees(self):
        limiter = _limiter(general_limit=1)
        first = "203.0.113.10"
        second = "203.0.113.11"

        assert limiter._is_rate_limited(first) is False
        assert limiter._is_rate_limited(second) is False
        assert limiter._is_rate_limited(first) is True

        serialized_state = repr(limiter._windows)
        assert first not in serialized_state
        assert second not in serialized_state

    def test_les_fenetres_expirent_avec_une_horloge_monotone(self):
        clock = _Clock()
        limiter = _limiter(clock=clock, general_limit=1)
        assert limiter._is_rate_limited("9.9.9.9") is False

    def test_la_fenetre_glissante_ne_double_pas_le_quota_a_la_frontiere(self):
        clock = _Clock()
        limiter = _limiter(clock=clock, general_limit=3)
        assert limiter._is_rate_limited("9.9.9.9") is False

        clock.advance(59.9)
        assert limiter._is_rate_limited("9.9.9.9") is False
        assert limiter._is_rate_limited("9.9.9.9") is False
        clock.advance(0.2)

        # Seule la requête de t=0 a expiré ; les deux de t=59.9 comptent.
        assert limiter._is_rate_limited("9.9.9.9") is False
        assert limiter._is_rate_limited("9.9.9.9") is True
        assert limiter._is_rate_limited("9.9.9.9") is True

        clock.advance(61)

        assert limiter._is_rate_limited("9.9.9.9") is False

    def test_les_classes_generale_et_couteuse_ont_des_budgets_separes(self):
        limiter = _limiter(general_limit=1, expensive_limit=1)
        address = "198.51.100.7"
        assert limiter._is_rate_limited(
            address,
            policy_class="general",
        ) is False
        assert limiter._is_rate_limited(
            address,
            policy_class="expensive",
        ) is False


class TestComptageDistribue:
    def test_le_script_est_atomique_borne_et_utilise_l_horloge_redis(self):
        commands = {
            "TIME",
            "ZREMRANGEBYSCORE",
            "ZSCORE",
            "ZCARD",
            "ZADD",
            "PEXPIRE",
        }

        assert all(
            f'redis.call("{command}"' in _ATOMIC_SLIDING_WINDOW_SCRIPT
            for command in commands
        )
        assert "max_identities" in _ATOMIC_SLIDING_WINDOW_SCRIPT

    @pytest.mark.asyncio
    async def test_l_identite_redis_est_stable_sans_conserver_l_adresse(self):
        client = _RedisDecisionClient()
        limiter = RedisSlidingWindowRateLimiter(
            client,
            identity_secret=b"s" * 32,
            window_seconds=60,
            max_tracked_identities=10_000,
        )

        assert await limiter.is_rate_limited(
            "203.0.113.44",
            policy_class="general",
            limit=240,
        ) is False
        assert await limiter.is_rate_limited(
            "203.0.113.44",
            policy_class="general",
            limit=240,
        ) is False

        first = client.calls[0]
        second = client.calls[1]
        assert first[2] == second[2]
        assert first[7] == second[7]
        assert first[6] != second[6]
        assert "203.0.113.44" not in repr(client.calls)
        assert first[1] == 2
        assert first[3].endswith(":registry")

    @pytest.mark.asyncio
    @pytest.mark.parametrize("decision", [1, 2])
    async def test_quota_et_plafond_global_refusent_sans_allocation_locale(
        self,
        decision,
    ):
        client = _RedisDecisionClient(decision=decision)
        limiter = RedisSlidingWindowRateLimiter(
            client,
            identity_secret=b"s" * 32,
            window_seconds=60,
            max_tracked_identities=10_000,
        )

        assert await limiter.is_rate_limited(
            "198.51.100.8",
            policy_class="expensive",
            limit=30,
        ) is True

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "client",
        [
            _RedisDecisionClient(decision=9),
            _RedisDecisionClient(error=ConnectionError("redis secret endpoint")),
        ],
    )
    async def test_une_decision_absente_ou_invalide_echoue_fermee(self, client):
        limiter = RedisSlidingWindowRateLimiter(
            client,
            identity_secret=b"s" * 32,
            window_seconds=60,
            max_tracked_identities=10_000,
        )

        with pytest.raises(DistributedRateLimitUnavailable):
            await limiter.is_rate_limited(
                "198.51.100.9",
                policy_class="general",
                limit=240,
            )


class TestJournal429:
    def test_un_seul_log_par_route_et_par_minute(self):
        middleware = RequestLoggingMiddleware(app=None)

        assert middleware._rate_limit_log_decision(
            "/api/advise",
            now=0.0,
        ) == (True, 0)
        assert middleware._rate_limit_log_decision(
            "/api/advise",
            now=1.0,
        )[0] is False
        assert middleware._rate_limit_log_decision(
            "/api/advise",
            now=59.9,
        )[0] is False
        assert middleware._rate_limit_log_decision(
            "/api/advise",
            now=60.0,
        ) == (True, 2)

    def test_les_decisions_de_log_concurrentes_sont_atomiques(self):
        middleware = RequestLoggingMiddleware(app=None)
        decisions: list[bool] = []

        def decide() -> None:
            decisions.append(
                middleware._rate_limit_log_decision(
                    "/api/advise",
                    now=1.0,
                )[0]
            )

        threads = [threading.Thread(target=decide) for _ in range(50)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=2)

        assert not any(thread.is_alive() for thread in threads)
        assert decisions.count(True) == 1
        assert decisions.count(False) == 49

    def test_la_cardinalite_des_routes_de_log_est_strictement_bornee(self):
        middleware = RequestLoggingMiddleware(app=None)

        for index in range(250):
            middleware._rate_limit_log_decision(
                f"/route/{index}",
                now=1.0,
            )

        assert len(middleware._rate_limit_log_windows) == 100
        assert "OTHER" in middleware._rate_limit_log_windows


class TestMemoire:
    def test_purge_periodique_des_pseudonymes_inactifs_sous_le_cap(self):
        clock = _Clock()
        limiter = _limiter(
            clock=clock,
            max_tracked_identities=10,
            general_limit=10,
        )
        limiter._is_rate_limited("192.0.2.1")
        assert len(limiter._windows) == 1

        clock.advance(61)
        limiter._is_rate_limited("192.0.2.2")

        assert len(limiter._windows) == 1

    def test_le_plafond_est_strict_et_le_debordement_est_bloque(self):
        limiter = _limiter(max_tracked_identities=2, general_limit=10)
        assert limiter._is_rate_limited("192.0.2.1") is False
        assert limiter._is_rate_limited("192.0.2.2") is False

        assert limiter._is_rate_limited("192.0.2.3") is True
        assert limiter._is_rate_limited("192.0.2.4") is True
        assert len(limiter._windows) == 2

    def test_une_fenetre_active_survit_a_la_purge(self):
        clock = _Clock()
        limiter = _limiter(
            clock=clock,
            max_tracked_identities=10,
            general_limit=2,
        )
        limiter._is_rate_limited("192.0.2.1")
        clock.advance(30)
        limiter._is_rate_limited("192.0.2.2")
        clock.advance(31)
        limiter._is_rate_limited("192.0.2.3")

        # .1 est expirée ; .2 existe encore et sa seconde requête est admise.
        assert len(limiter._windows) == 2
        assert limiter._is_rate_limited("192.0.2.2") is False
        assert limiter._is_rate_limited("192.0.2.2") is True

    def test_un_slot_est_libere_des_que_la_derniere_identite_expire(self):
        clock = _Clock()
        limiter = _limiter(
            clock=clock,
            max_tracked_identities=2,
            general_limit=10,
        )
        clock.advance(60)
        assert limiter._is_rate_limited("192.0.2.1") is False
        clock.advance(0.1)
        assert limiter._is_rate_limited("192.0.2.2") is False

        clock.advance(59.9)
        assert limiter._is_rate_limited("192.0.2.3") is False
        clock.advance(0.2)

        assert limiter._is_rate_limited("192.0.2.4") is False
        assert len(limiter._windows) == 2

    def test_la_lecture_du_temps_est_serialisee_avec_les_mutations(self):
        class ProbeClock:
            def __init__(self):
                self.barrier = threading.Barrier(2)
                self.overlap = False

            def __call__(self) -> float:
                try:
                    self.barrier.wait(timeout=0.2)
                    self.overlap = True
                except threading.BrokenBarrierError:
                    pass
                return 1.0

        clock = ProbeClock()
        limiter = _limiter(clock=clock, general_limit=10)
        threads = [
            threading.Thread(
                target=limiter._is_rate_limited,
                args=(f"192.0.2.{index}",),
            )
            for index in (1, 2)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=2)

        assert not any(thread.is_alive() for thread in threads)
        assert clock.overlap is False


@pytest.mark.asyncio
async def test_x_forwarded_for_forge_ne_permet_pas_de_tourner_le_quota(caplog):
    app = FastAPI()
    app.add_middleware(
        RateLimitMiddleware,
        expensive_limit=3,
        general_limit=10,
    )
    app.add_middleware(RequestLoggingMiddleware)

    @app.get("/api/advise/not-a-route")
    async def expensive() -> dict:
        return {"ok": True}

    transport = httpx.ASGITransport(
        app=app,
        client=("198.51.100.50", 12345),
    )
    with caplog.at_level(logging.WARNING, logger="filon.http"):
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            responses = [
                await client.get(
                    "/api/advise/not-a-route",
                    headers={"x-forwarded-for": f"203.0.113.{index}"},
                )
                for index in range(10)
            ]

    assert [response.status_code for response in responses] == [
        200,
        200,
        200,
        429,
        429,
        429,
        429,
        429,
        429,
        429,
    ]
    rate_records = [
        record
        for record in caplog.records
        if record.name == "filon.http"
    ]
    assert len(rate_records) == 1
    assert "suppressed_since_last=0" in rate_records[0].getMessage()
    assert "<rate-limit:/api/advise>" in rate_records[0].getMessage()
    serialized_records = repr(
        [(record.msg, record.args, record.__dict__) for record in rate_records]
    )
    assert "198.51.100.50" not in serialized_records
    assert "203.0.113." not in serialized_records


@pytest.mark.asyncio
async def test_un_lookalike_health_reste_observe(caplog):
    app = FastAPI()
    app.add_middleware(RequestLoggingMiddleware)

    @app.get("/health/live")
    async def live() -> dict:
        return {"ok": True}

    @app.get("/health")
    async def health() -> dict:
        return {"ok": True}

    @app.get("/healthcheck")
    async def health_lookalike() -> dict:
        return {"ok": True}

    transport = httpx.ASGITransport(app=app)
    with caplog.at_level(logging.INFO, logger="filon.http"):
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            live_response = await client.get("/health/live")
            health_response = await client.get("/health")
            response = await client.get("/healthcheck")

    assert live_response.status_code == 200
    assert health_response.status_code == 200
    assert response.status_code == 200
    messages = [
        record.getMessage()
        for record in caplog.records
        if record.name == "filon.http"
    ]
    assert any("/healthcheck" in message for message in messages)
    assert any("/health →" in message for message in messages)
    assert not any("/health/live" in message for message in messages)


@pytest.mark.asyncio
async def test_les_429_sont_agreges_par_bucket_canonique(caplog):
    request_metrics.reset()
    app = FastAPI()
    app.add_middleware(
        RateLimitMiddleware,
        expensive_limit=1,
        general_limit=1,
    )
    app.add_middleware(RequestLoggingMiddleware)

    @app.get("/api/advise/a")
    async def advise() -> dict:
        return {"ok": True}

    @app.get("/ordinary")
    async def ordinary() -> dict:
        return {"ok": True}

    transport = httpx.ASGITransport(
        app=app,
        client=("198.51.100.55", 12345),
    )
    with caplog.at_level(logging.WARNING, logger="filon.http"):
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            await client.get("/api/advise/a")
            await client.get("/ordinary")
            advise_blocked = await client.get("/api/advise/a")
            ordinary_blocked = await client.get("/ordinary")

    assert advise_blocked.status_code == 429
    assert ordinary_blocked.status_code == 429
    messages = [
        record.getMessage()
        for record in caplog.records
        if record.name == "filon.http"
    ]
    assert len(messages) == 2
    assert any("<rate-limit:/api/advise>" in message for message in messages)
    assert any("<rate-limit:general>" in message for message in messages)
    routes = request_metrics.snapshot()["routes"]
    assert routes["GET <rate-limit:/api/advise>"]["requests"] == 1
    assert routes["GET <rate-limit:general>"]["requests"] == 1
    request_metrics.reset()


@pytest.mark.asyncio
async def test_catalogue_public_et_admin_sont_tous_deux_limites():
    app = FastAPI()
    app.add_middleware(
        RateLimitMiddleware,
        expensive_limit=1,
        general_limit=1,
    )

    @app.get("/api/catalog/offers")
    async def public_catalog() -> dict:
        return {"ok": True}

    @app.get("/api/catalog/admin/unclassified")
    async def admin_catalog() -> dict:
        return {"ok": True}

    public_transport = httpx.ASGITransport(
        app=app,
        client=("198.51.100.60", 12345),
    )
    async with httpx.AsyncClient(
        transport=public_transport,
        base_url="http://test",
    ) as client:
        public_statuses = [
            (await client.get("/api/catalog/offers")).status_code
            for _ in range(3)
        ]

    admin_transport = httpx.ASGITransport(
        app=app,
        client=("198.51.100.61", 12345),
    )
    async with httpx.AsyncClient(
        transport=admin_transport,
        base_url="http://test",
    ) as client:
        admin_statuses = [
            (await client.get("/api/catalog/admin/unclassified")).status_code
            for _ in range(2)
        ]

    assert public_statuses == [200, 429, 429]
    assert admin_statuses == [200, 429]


@pytest.mark.asyncio
async def test_outfit_utilise_le_quota_couteux():
    app = FastAPI()
    app.add_middleware(
        RateLimitMiddleware,
        expensive_limit=1,
        general_limit=10,
    )

    @app.post("/api/intelligence/outfit/analyse")
    async def analyse() -> dict:
        return {"ok": True}

    transport = httpx.ASGITransport(
        app=app,
        client=("198.51.100.62", 12345),
    )
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        statuses = [
            (await client.post("/api/intelligence/outfit/analyse")).status_code
            for _ in range(2)
        ]

    assert statuses == [200, 429]


@pytest.mark.asyncio
async def test_les_requetes_concurrentes_respectent_exactement_la_limite():
    app = FastAPI()
    app.add_middleware(
        RateLimitMiddleware,
        expensive_limit=5,
        general_limit=10,
    )

    @app.get("/api/advise/concurrent")
    async def expensive() -> dict:
        await asyncio.sleep(0)
        return {"ok": True}

    transport = httpx.ASGITransport(
        app=app,
        client=("198.51.100.70", 12345),
    )
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        responses = await asyncio.gather(
            *(client.get("/api/advise/concurrent") for _ in range(20))
        )

    statuses = [response.status_code for response in responses]
    assert statuses.count(200) == 5
    assert statuses.count(429) == 15


@pytest.mark.asyncio
async def test_le_quota_distribue_serialise_les_requetes_concurrentes():
    app = FastAPI()
    client = _AtomicQuotaClient(limit=5)
    app.add_middleware(
        RateLimitMiddleware,
        expensive_limit=5,
        general_limit=10,
        distributed_client=client,
        identity_secret=b"s" * 32,
    )

    @app.get("/api/advise/concurrent")
    async def expensive() -> dict:
        await asyncio.sleep(0)
        return {"ok": True}

    transport = httpx.ASGITransport(
        app=app,
        client=("198.51.100.71", 12345),
    )
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as http_client:
        responses = await asyncio.gather(
            *(http_client.get("/api/advise/concurrent") for _ in range(20))
        )

    statuses = [response.status_code for response in responses]
    assert statuses.count(200) == 5
    assert statuses.count(429) == 15


@pytest.mark.asyncio
async def test_redis_indisponible_ferme_les_routes_mais_pas_la_liveness():
    app = FastAPI()
    client = _RedisDecisionClient(error=TimeoutError("redis endpoint"))
    protected_calls = 0
    app.add_middleware(
        RateLimitMiddleware,
        distributed_client=client,
        identity_secret=b"s" * 32,
    )

    @app.get("/health/live")
    async def live() -> dict:
        return {"ok": True}

    @app.get("/ordinary")
    async def protected() -> dict:
        nonlocal protected_calls
        protected_calls += 1
        return {"ok": True}

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as http_client:
        live_response = await http_client.get("/health/live")
        protected_response = await http_client.get("/ordinary")

    assert live_response.status_code == 200
    assert protected_response.status_code == 503
    assert protected_response.json() == {"error": "rate_limit_unavailable"}
    assert protected_response.headers["retry-after"] == "1"
    assert protected_calls == 0
    assert len(client.calls) == 1


@pytest.mark.asyncio
async def test_create_app_branche_et_ferme_le_client_redis(monkeypatch):
    redis_client = _CloseableRedisClient()
    factory_calls: list[tuple[str, dict[str, object]]] = []

    class FakeRedis:
        @staticmethod
        def from_url(url: str, **kwargs: object) -> _CloseableRedisClient:
            factory_calls.append((url, kwargs))
            return redis_client

    settings = Settings(
        _env_file=None,
        env="test",
        rate_limit_backend="redis",
        redis_url="redis://redis.internal:6379/0",
        rate_limit_identity_secret="s" * 32,
        rate_limit_redis_timeout_seconds=0.2,
    )
    monkeypatch.setattr(app_main, "get_settings", lambda: settings)
    monkeypatch.setattr(app_main, "Redis", FakeRedis)

    app = app_main.create_app()
    rate_limit_middleware = next(
        middleware
        for middleware in app.user_middleware
        if middleware.cls is RateLimitMiddleware
    )

    assert app.state.rate_limit_redis_client is redis_client
    assert rate_limit_middleware.kwargs["distributed_client"] is redis_client
    assert rate_limit_middleware.kwargs["identity_secret"] == b"s" * 32
    assert factory_calls == [
        (
            "redis://redis.internal:6379/0",
            {
                "socket_connect_timeout": 0.2,
                "socket_timeout": 0.2,
                "retry_on_timeout": False,
            },
        )
    ]

    async with app.router.lifespan_context(app):
        assert redis_client.closed is False
    assert redis_client.closed is True


def test_entrypoint_desactive_access_log_et_borne_les_proxies(monkeypatch):
    calls: list[tuple[tuple, dict]] = []
    monkeypatch.setenv("PORT", "9123")
    monkeypatch.setenv("FORWARDED_ALLOW_IPS", "127.0.0.1,10.42.0.0/24")
    monkeypatch.setattr(
        app_entrypoint.uvicorn,
        "run",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    app_entrypoint.main()

    assert calls == [
        (
            ("app.main:app",),
            {
                "host": "0.0.0.0",
                "port": 9123,
                "access_log": False,
                "proxy_headers": True,
                "forwarded_allow_ips": "127.0.0.1,10.42.0.0/24",
            },
        )
    ]


@pytest.mark.asyncio
async def test_uvicorn_applique_reellement_le_cidr_proxy(monkeypatch):
    monkeypatch.setenv("FORWARDED_ALLOW_IPS", "10.42.0.0/16")
    inner = FastAPI()

    @inner.get("/")
    async def peer(request: Request) -> dict:
        return {"host": request.client.host}

    app = ProxyHeadersMiddleware(
        inner,
        trusted_hosts=app_entrypoint._trusted_proxy_allowlist(),
    )

    trusted_transport = httpx.ASGITransport(
        app=app,
        client=("10.42.5.9", 12345),
    )
    async with httpx.AsyncClient(
        transport=trusted_transport,
        base_url="http://test",
    ) as client:
        trusted = await client.get(
            "/",
            headers=[
                ("x-forwarded-for", "198.51.100.66"),
                (
                    "x-forwarded-for",
                    "203.0.113.80:443, 10.42.9.9",
                ),
            ],
        )

    untrusted_transport = httpx.ASGITransport(
        app=app,
        client=("10.43.5.9", 12345),
    )
    async with httpx.AsyncClient(
        transport=untrusted_transport,
        base_url="http://test",
    ) as client:
        untrusted = await client.get(
            "/",
            headers={"x-forwarded-for": "203.0.113.81"},
        )

    assert trusted.json() == {"host": "203.0.113.80"}
    assert untrusted.json() == {"host": "10.43.5.9"}


def test_la_version_minimale_uvicorn_supporte_la_chaine_proxy():
    requirements = Path(__file__).resolve().parents[1] / "requirements.txt"
    assert "uvicorn[standard]>=0.49.0" in requirements.read_text().splitlines()


def test_railway_legacy_est_exact_et_le_nouveau_service_utilise_le_dashboard():
    backend_root = Path(__file__).resolve().parents[1]
    config = json.loads((backend_root / "railway.json").read_text())
    assert config["deploy"]["preDeployCommand"] == "alembic upgrade head"
    assert config["deploy"]["healthcheckPath"] == "/health/ready"
    assert config["deploy"]["healthcheckTimeout"] == 120

    env_example = (backend_root / ".env.example").read_text()
    deploy_guide = (backend_root / "DEPLOY.md").read_text()
    flattened_guide = " ".join(deploy_guide.split())
    assert "FORWARDED_ALLOW_IPS=127.0.0.1" in env_example
    assert "FORWARDED_ALLOW_IPS=<IP/CIDR" in deploy_guide
    assert "DATABASE_SCHEMA_MODE=alembic" in deploy_guide
    assert "OBSERVATION_SHADOW_ENABLED=false" in deploy_guide
    assert "DEBUG=false" in deploy_guide
    assert "/health/ready" in deploy_guide
    assert "Nouveau service : configuration Dashboard obligatoire" in deploy_guide
    assert "nouveau service ne peut plus l'activer" in deploy_guide
    assert "`railway.json` n'est pas sa source de configuration" in deploy_guide
    assert "Ne rien renseigner comme **Railway Config File**" in flattened_guide
    assert "**Pre-Deploy Command** : `alembic upgrade head`" in deploy_guide
    assert "**Start Command** : `python -m app`" in deploy_guide
    assert "**Healthcheck Timeout** : `120` secondes" in deploy_guide
    assert "Job catalogue séparé du processus web" in deploy_guide
    assert "**Start Command** : `python -m app.ingest.scheduler`" in deploy_guide
    assert "**Cron Schedule** : `0 */6 * * *` (UTC)" in deploy_guide
    assert "**Pre-Deploy Command** : aucune" in deploy_guide
    assert "service web/release reste l'unique" in deploy_guide


@pytest.mark.parametrize(
    "allowlist",
    [
        "*",
        "0.0.0.0/0",
        "::/0",
        "0.0.0.0/1,128.0.0.0/1",
        "::/1,8000::/1",
        "10.42.0.1/24",
        "not-an-ip",
    ],
)
def test_entrypoint_refuse_une_allowlist_proxy_non_bornee(
    monkeypatch,
    allowlist,
):
    monkeypatch.setenv("FORWARDED_ALLOW_IPS", allowlist)
    called = False

    def run(*_args, **_kwargs):
        nonlocal called
        called = True

    monkeypatch.setattr(app_entrypoint.uvicorn, "run", run)

    with pytest.raises(RuntimeError, match="interdit|invalide"):
        app_entrypoint.main()
    assert called is False


def test_logging_desactive_le_canal_uvicorn_qui_contient_la_query(monkeypatch):
    names = (
        "httpx",
        "httpcore",
        "hpack",
        "urllib3",
        "asyncio",
        "uvicorn.access",
    )
    loggers = [logging.getLogger(name) for name in names]
    previous = [
        (logger.level, logger.disabled, logger.propagate)
        for logger in loggers
    ]
    monkeypatch.setattr(logging, "basicConfig", lambda **_kwargs: None)
    try:
        configure_logging(debug=False)
        access_logger = logging.getLogger("uvicorn.access")
        assert access_logger.disabled is True
        assert access_logger.propagate is False
    finally:
        for logger, (level, disabled, propagate) in zip(
            loggers,
            previous,
            strict=True,
        ):
            logger.setLevel(level)
            logger.disabled = disabled
            logger.propagate = propagate
