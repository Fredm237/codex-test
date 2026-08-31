from __future__ import annotations

import ast
import asyncio
import gc
import json
import logging
import threading
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI

from app.api.middleware import RequestLoggingMiddleware
from app.api.routes import health as health_module
from app.core.config import Settings
from app.main import create_app
from app.core.observability import (
    ProductIntelligenceMetricsRegistry,
    RequestMetricsRegistry,
    normalize_request_id,
    product_intelligence_metrics,
    request_id_context,
    request_metrics,
    traced_pipeline_stage,
)
from app.services import awin_catalog, recommend


_APP_ROOT = Path(__file__).resolve().parents[1] / "app"


def test_request_id_externe_est_toujours_remplace_par_un_identifiant_opaque():
    first = normalize_request_id("client.trace-42")
    second = normalize_request_id("client.trace-42")
    assert first != "client.trace-42"
    assert first != second
    assert len(first) == 32
    assert first.isalnum()


def test_percentiles_et_statuts_sont_mesures_sans_parametre_de_route():
    registry = RequestMetricsRegistry()
    for status, elapsed in ((200, 10), (200, 20), (404, 30), (500, 100)):
        registry.record(
            method="GET",
            route="/products/{product_id}",
            status_code=status,
            elapsed_ms=elapsed,
        )

    snapshot = registry.snapshot()
    assert snapshot["overall"]["requests"] == 4
    assert snapshot["overall"]["status_groups"] == {
        "2xx": 2,
        "4xx": 1,
        "5xx": 1,
    }
    assert snapshot["overall"]["latency_ms"]["p50"] == 20
    assert snapshot["overall"]["latency_ms"]["p95"] == 100
    assert list(snapshot["routes"]) == ["GET /products/{product_id}"]


@pytest.mark.parametrize("invalid", [float("nan"), float("inf"), -1, True, "bad"])
def test_latence_http_invalide_est_rejetee_sans_mutation_partielle(invalid):
    registry = RequestMetricsRegistry()
    before = registry.snapshot()
    alert_before = registry.alert_snapshot()

    with pytest.raises(ValueError, match="elapsed_ms_must_be_finite_nonnegative"):
        registry.record(
            method="GET",
            route="/fixed-template",
            status_code=200,
            elapsed_ms=invalid,
        )

    after = registry.snapshot()
    assert after["overall"] == before["overall"]
    assert after["routes"] == before["routes"]
    assert registry.alert_snapshot() == alert_before


def test_statut_http_reentrant_ne_peut_pas_rappeler_le_registre_sous_verrou():
    registry = RequestMetricsRegistry()
    completed: list[bool] = []
    failures: list[BaseException] = []

    class ReentrantStatus(int):
        def __ge__(self, other):
            registry.reset()
            return super().__ge__(other)

    def run() -> None:
        try:
            registry.record(
                method="GET",
                route="/fixed-template",
                status_code=ReentrantStatus(200),
                elapsed_ms=1,
            )
            completed.append(True)
        except BaseException as exc:  # pragma: no cover - assertion relay
            failures.append(exc)

    worker = threading.Thread(target=run, daemon=True)
    worker.start()
    worker.join(timeout=2)

    assert not worker.is_alive(), "custom HTTP status ran under registry lock"
    assert completed == [True]
    assert not failures
    assert registry.snapshot()["overall"]["status_groups"] == {"OTHER_STATUS": 1}
    assert registry.alert_snapshot()["status_groups"] == {"OTHER_STATUS": 1}


def test_cardinalite_des_routes_reste_bornee_avec_un_seau_other():
    registry = RequestMetricsRegistry()
    for index in range(140):
        registry.record(
            method="GET",
            route=f"/internal-route-{index}",
            status_code=200,
            elapsed_ms=1,
        )

    snapshot = registry.snapshot()
    assert len(snapshot["routes"]) == snapshot["retention"]["route_cardinality"]
    assert snapshot["routes"]["OTHER"]["requests"] == 41


def test_metriques_intelligence_sont_bornees_et_ne_conservent_aucun_identifiant():
    registry = ProductIntelligenceMetricsRegistry()
    registry.record_decision(
        {
            "recommendation_scope": "scope-secret-produit-123",
            "confidence": "niveau-libre",
            "offer_kind": "kind-libre",
            "missing": ["dimension-secrete-123"],
            "signals": [{"key": "freshness", "status": "libre", "age_hours": 96}],
            "evidence": [{"state": "etat-libre", "offer_id": "offre-secrete-123"}],
            "facts": {"item_price": 42, "product_id": "produit-secret-123"},
        }
    )
    registry.record_recommendation(
        {
            "real": True,
            "cards": [
                {
                    "buy": True,
                    "name": "requete-secrete-123",
                    "offer_id": "offre-secrete-123",
                }
            ],
        },
        delivery="source-libre",
    )

    snapshot = registry.snapshot()
    serialized = json.dumps(snapshot)
    assert snapshot["decision_evaluations"]["scopes"] == {"OTHER": 1}
    assert snapshot["decision_evaluations"]["missing_dimensions"] == {"OTHER": 1}
    assert snapshot["decision_evaluations"]["freshness_age_buckets"] == {"73_168h": 1}
    assert snapshot["recommendation_responses"]["outcomes"] == {"documented": 1}
    assert snapshot["recommendation_responses"]["delivery"] == {"OTHER": 1}
    for secret in ("secret", "requete", "offre-secrete", "produit-secret"):
        assert secret not in serialized


def test_libelles_metier_reentrants_sont_normalises_avant_le_verrou():
    decision_registry = ProductIntelligenceMetricsRegistry()
    recommendation_registry = ProductIntelligenceMetricsRegistry()
    completed: list[bool] = []
    failures: list[BaseException] = []

    class ReentrantLabel:
        def __init__(self, registry: ProductIntelligenceMetricsRegistry) -> None:
            self.registry = registry

        def __str__(self) -> str:
            self.registry.reset()
            return "generated"

    decision_label = ReentrantLabel(decision_registry)
    recommendation_label = ReentrantLabel(recommendation_registry)

    def run() -> None:
        try:
            decision_registry.record_decision(
                {
                    "recommendation_scope": "a_verifier",
                    "confidence": "faible",
                    "offer_kind": "unknown",
                    "missing": [decision_label],
                    "signals": [],
                    "evidence": [],
                }
            )
            recommendation_registry.record_recommendation(
                {"real": False, "cards": []},
                delivery=recommendation_label,  # type: ignore[arg-type]
            )
            completed.append(True)
        except BaseException as exc:  # pragma: no cover - assertion relay
            failures.append(exc)

    worker = threading.Thread(target=run, daemon=True)
    worker.start()
    worker.join(timeout=2)

    assert not worker.is_alive(), "custom business label ran under registry lock"
    assert completed == [True]
    assert not failures
    decision_snapshot = decision_registry.snapshot()
    recommendation_snapshot = recommendation_registry.snapshot()
    assert decision_snapshot["decision_evaluations"]["total"] == 1
    assert decision_snapshot["decision_evaluations"]["missing_dimensions"] == {
        "OTHER": 1
    }
    assert recommendation_snapshot["recommendation_responses"]["delivery"] == {
        "generated": 1
    }


def test_retention_des_latences_et_cardinalite_des_etapes_sont_bornees():
    registry = ProductIntelligenceMetricsRegistry()
    for index in range(700):
        registry.record_stage(
            stage=f"etape-libre-{index}",
            outcome=f"sortie-libre-{index}",
            elapsed_ms=float(index),
        )

    stages = registry.snapshot()["pipeline_stages"]
    assert list(stages) == ["OTHER"]
    assert stages["OTHER"]["executions"] == 700
    assert stages["OTHER"]["outcomes"] == {"OTHER": 700}
    assert stages["OTHER"]["latency_ms"]["sample_size"] == 512


@pytest.mark.parametrize("invalid", [float("nan"), float("inf"), -1, True, "bad"])
def test_latence_etape_invalide_est_rejetee_sans_mutation_partielle(invalid):
    registry = ProductIntelligenceMetricsRegistry()
    before = registry.snapshot()
    alert_before = registry.alert_snapshot()

    with pytest.raises(ValueError, match="elapsed_ms_must_be_finite_nonnegative"):
        registry.record_stage(
            stage="retrieval",
            outcome="ok",
            elapsed_ms=invalid,
        )

    assert registry.snapshot() == before
    assert registry.alert_snapshot() == alert_before


@pytest.mark.asyncio
async def test_ingestion_distingue_toutes_les_sorties_degradees_du_succes():
    assert awin_catalog._ingestion_stage_outcome({"feeds": 2, "skipped": 1}) == "degraded"
    assert awin_catalog._ingestion_stage_outcome(
        {"feeds": 2, "skipped": 0, "shadow": {"failures": 1}}
    ) == "degraded"
    assert awin_catalog._ingestion_stage_outcome({"feeds": 0, "skipped": 0}) == "degraded"
    assert awin_catalog._ingestion_stage_outcome(
        {"feeds": 2, "skipped": 0, "shadow": {"failures": 0}}
    ) == "ok"

    product_intelligence_metrics.reset()
    assert await awin_catalog.ingest_feeds(None) == {"feeds": 0, "offers": 0, "skipped": 0}
    stages = product_intelligence_metrics.snapshot()["pipeline_stages"]
    assert stages["ingestion"]["outcomes"] == {"degraded": 1}


@pytest.mark.asyncio
async def test_cache_sse_traverse_aussi_etape_catalogue(monkeypatch):
    cached = {
        "real": False,
        "offers": 0,
        "cards": [],
        "currency": None,
        "message": "Aucune offre indexée.",
    }

    class _Cache:
        async def get_json(self, _key: str) -> dict:
            return cached

    async def no_sleep(_delay: float) -> None:
        return None

    monkeypatch.setattr(recommend, "get_cache", lambda: _Cache())
    monkeypatch.setattr(recommend.asyncio, "sleep", no_sleep)
    product_intelligence_metrics.reset()

    events = [
        event
        async for event in recommend.stream_events(
            "requête-secrète",
            100,
            "be",
            "fr",
        )
    ]

    assert events[-1] == {"type": "results", "data": cached}
    metrics = product_intelligence_metrics.snapshot()
    assert metrics["pipeline_stages"]["catalogue"]["outcomes"] == {"ok": 1}
    assert metrics["recommendation_responses"]["delivery"] == {"cache": 1}


@pytest.mark.asyncio
async def test_fermeture_sse_annule_et_consomme_toute_tache(monkeypatch):
    started = asyncio.Event()
    cancelled = asyncio.Event()

    async def pending_result(*_args, **_kwargs) -> dict:
        started.set()
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            cancelled.set()
            raise

    monkeypatch.setattr(recommend, "generate_result", pending_result)
    pending_stream = recommend.stream_events("secret-pending-query", None, "be", "fr")
    assert await pending_stream.__anext__() == {"type": "step", "i": 0}
    await started.wait()
    await pending_stream.aclose()
    assert cancelled.is_set()

    contexts: list[dict] = []
    loop = asyncio.get_running_loop()
    previous_handler = loop.get_exception_handler()
    loop.set_exception_handler(lambda _loop, context: contexts.append(context))

    async def failing_result(*_args, **_kwargs) -> dict:
        raise RuntimeError("signed-url-secret-token")

    monkeypatch.setattr(recommend, "generate_result", failing_result)
    failing_stream = recommend.stream_events("secret-failing-query", None, "be", "fr")
    try:
        assert await failing_stream.__anext__() == {"type": "step", "i": 0}
        await asyncio.sleep(0)
        await failing_stream.aclose()
        del failing_stream
        gc.collect()
        await asyncio.sleep(0)
    finally:
        loop.set_exception_handler(previous_handler)

    assert "signed-url-secret-token" not in repr(contexts)
    assert all(context.get("message") != "Task exception was never retrieved" for context in contexts)


@pytest.mark.asyncio
async def test_etapes_imbriquees_partagent_correlation_sans_fuite_exception():
    product_intelligence_metrics.reset()
    records: list[logging.LogRecord] = []

    class _ListHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    handler = _ListHandler()
    loggers = [
        logging.getLogger(logger_name)
        for logger_name in (
        "filon.stage.retrieval",
        "filon.stage.decision",
        "filon.stage.ingestion",
        )
    ]
    previous_disable = logging.root.manager.disable
    previous_states = [(logger.level, logger.disabled) for logger in loggers]
    logging.disable(logging.NOTSET)
    for logger in loggers:
        logger.disabled = False
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)

    try:
        @traced_pipeline_stage("decision")
        async def decision_stage() -> None:
            return None

        @traced_pipeline_stage("retrieval")
        async def retrieval_stage() -> None:
            await decision_stage()

        await retrieval_stage()
        messages = [record.getMessage() for record in records if "request_id=" in record.getMessage()]
        request_ids = {
            message.split("request_id=", 1)[1].split(" ", 1)[0]
            for message in messages
        }
        assert len(request_ids) == 1
        assert request_id_context.get() is None
        stages = product_intelligence_metrics.snapshot()["pipeline_stages"]
        assert stages["retrieval"]["outcomes"] == {"ok": 1}
        assert stages["decision"]["outcomes"] == {"ok": 1}

        records.clear()

        @traced_pipeline_stage("ingestion")
        async def failing_stage() -> None:
            raise RuntimeError("signed-url-secret-token")

        with pytest.raises(RuntimeError, match="signed-url-secret-token"):
            await failing_stage()

        assert "signed-url-secret-token" not in "\n".join(
            record.getMessage() for record in records
        )
        stages = product_intelligence_metrics.snapshot()["pipeline_stages"]
        assert stages["ingestion"]["outcomes"] == {"error": 1}
    finally:
        for logger, (level, disabled) in zip(loggers, previous_states, strict=True):
            logger.removeHandler(handler)
            logger.setLevel(level)
            logger.disabled = disabled
        logging.disable(previous_disable)


@pytest.mark.asyncio
async def test_decorateur_remplace_contexte_non_fiable_et_ignore_entrees_sorties():
    records: list[logging.LogRecord] = []

    class _ListHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    handler = _ListHandler()
    logger = logging.getLogger("filon.stage.catalogue")
    previous_disable = logging.root.manager.disable
    previous_state = (logger.level, logger.disabled)
    logging.disable(logging.NOTSET)
    logger.disabled = False
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    outer_token = request_id_context.set("private-context-123")  # type: ignore[arg-type]

    @traced_pipeline_stage("catalogue")
    async def echo_secret(_secret_input: str) -> str:
        return "private-return-456"

    try:
        assert await echo_secret("private-argument-789") == "private-return-456"
        assert request_id_context.get() == "private-context-123"
    finally:
        request_id_context.reset(outer_token)
        logger.removeHandler(handler)
        logger.setLevel(previous_state[0])
        logger.disabled = previous_state[1]
        logging.disable(previous_disable)

    serialized_records = repr(
        [(record.msg, record.args, record.exc_info, record.__dict__) for record in records]
    )
    for secret in ("private-context-123", "private-argument-789", "private-return-456"):
        assert secret not in serialized_records
    request_ids = {
        record.getMessage().split("request_id=", 1)[1].split(" ", 1)[0]
        for record in records
    }
    assert len(request_ids) == 1
    assert len(request_ids.pop()) == 32


def test_logs_du_parcours_assistant_ne_referencent_aucune_entree_utilisateur():
    paths = [
        "api/middleware.py",
        "api/routes/stream.py",
        "core/observability.py",
        "db/session.py",
        "main.py",
        "observations/awin.py",
        "services/awin.py",
        "services/awin_catalog.py",
        "services/cache.py",
        "services/recommend.py",
        "services/catalog_search.py",
        "services/catalog_source.py",
        "services/serpapi_shopping.py",
        "services/vectorstore.py",
    ]
    forbidden_names = {
        "advertiser_name",
        "budget",
        "country",
        "feed_id",
        "payload",
        "prefix",
        "q",
        "query",
        "request",
        "row",
    }

    def is_safe_exception_type(node: ast.AST) -> bool:
        return (
            isinstance(node, ast.Attribute)
            and node.attr == "__name__"
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == "type"
            and len(node.value.args) == 1
            and isinstance(node.value.args[0], ast.Name)
            and node.value.args[0].id == "exc"
        )

    def contains_unsafe_exception(node: ast.AST) -> bool:
        if is_safe_exception_type(node):
            return False
        if isinstance(node, ast.Name) and node.id == "exc":
            return True
        return any(contains_unsafe_exception(child) for child in ast.iter_child_nodes(node))

    violations: list[str] = []
    for relative_path in paths:
        tree = ast.parse((_APP_ROOT / relative_path).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in {"debug", "info", "warning", "error", "exception"}
            ):
                continue
            if node.func.attr == "exception":
                violations.append(f"{relative_path}:{node.lineno}:traceback")
            referenced = {
                child.id
                for child in ast.walk(node)
                if isinstance(child, ast.Name)
            }
            leaked = sorted(referenced & forbidden_names)
            if leaked:
                violations.append(f"{relative_path}:{node.lineno}:{','.join(leaked)}")
            expressions = [*node.args, *(keyword.value for keyword in node.keywords)]
            if any(contains_unsafe_exception(expression) for expression in expressions):
                violations.append(f"{relative_path}:{node.lineno}:exception_message")

    assert violations == []


@pytest.mark.asyncio
async def test_middleware_ne_journalise_ni_id_externe_ni_message_exception():
    records: list[logging.LogRecord] = []

    class _ListHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    handler = _ListHandler()
    loggers = [logging.getLogger("filon.http")]
    previous_disable = logging.root.manager.disable
    previous_states = [(logger.level, logger.disabled) for logger in loggers]
    logging.disable(logging.NOTSET)
    for logger in loggers:
        logger.disabled = False
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)

    app = FastAPI()
    app.add_middleware(RequestLoggingMiddleware)

    @app.get("/failure")
    async def failure() -> dict:
        raise RuntimeError("signed-url-secret-token")

    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get(
                "/failure?q=private-query-sentinel",
                headers={"x-request-id": "private-customer-123"},
            )
    finally:
        for logger, (level, disabled) in zip(loggers, previous_states, strict=True):
            logger.removeHandler(handler)
            logger.setLevel(level)
            logger.disabled = disabled
        logging.disable(previous_disable)

    assert response.status_code == 500
    assert response.json() == {"error": "internal_error"}
    assert len(response.headers["x-request-id"]) == 32
    assert response.headers["x-response-time"].endswith("ms")
    serialized_records = repr(
        [(record.msg, record.args, record.exc_info, record.__dict__) for record in records]
    )
    assert "signed-url-secret-token" not in serialized_records
    assert "private-customer-123" not in serialized_records
    assert "private-query-sentinel" not in serialized_records
    assert "error_type=RuntimeError" in "\n".join(
        record.getMessage() for record in records
    )


@pytest.mark.asyncio
async def test_endpoint_metriques_expose_intelligence_sans_modifier_le_contrat_http():
    request_metrics.reset()
    product_intelligence_metrics.reset()
    request_metrics.record(method="GET", route="/catalogue", status_code=200, elapsed_ms=12)
    product_intelligence_metrics.record_recommendation(
        {"real": False, "cards": []},
        delivery="generated",
    )

    snapshot = await health_module.metrics()

    assert snapshot["overall"]["requests"] == 1
    assert snapshot["product_intelligence"]["schema_version"] == 1
    assert snapshot["product_intelligence"]["recommendation_responses"]["outcomes"] == {
        "abstained": 1
    }


@pytest.mark.asyncio
async def test_middleware_propage_request_id_et_agrege_la_route_template():
    records: list[logging.LogRecord] = []

    class _ListHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    handler = _ListHandler()
    loggers = [
        logging.getLogger("filon.http"),
        logging.getLogger("filon.stage.catalogue"),
    ]
    previous_disable = logging.root.manager.disable
    previous_states = [(logger.level, logger.disabled) for logger in loggers]
    logging.disable(logging.NOTSET)
    for logger in loggers:
        logger.disabled = False
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)

    app = FastAPI()
    app.add_middleware(RequestLoggingMiddleware)

    @traced_pipeline_stage("catalogue")
    async def catalogue_stage() -> None:
        return None

    @app.get("/products/{product_id}")
    async def product(product_id: str) -> dict:
        await catalogue_stage()
        return {"found": bool(product_id)}

    request_metrics.reset()
    product_intelligence_metrics.reset()
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get(
                "/products/private-product-123",
                headers={"x-request-id": "client-42"},
            )
    finally:
        for logger, (level, disabled) in zip(loggers, previous_states, strict=True):
            logger.removeHandler(handler)
            logger.setLevel(level)
            logger.disabled = disabled
        logging.disable(previous_disable)

    assert response.status_code == 200
    assert response.headers["x-request-id"] != "client-42"
    assert len(response.headers["x-request-id"]) == 32
    assert response.headers["x-response-time"].endswith("ms")
    snapshot = request_metrics.snapshot()
    assert "GET /products/{product_id}" in snapshot["routes"]
    assert "private-product-123" not in json.dumps(snapshot)
    serialized_records = repr(
        [(record.msg, record.args, record.exc_info, record.__dict__) for record in records]
    )
    assert "private-product-123" not in serialized_records
    assert "client-42" not in serialized_records
    messages = [record.getMessage() for record in records if "request_id=" in record.getMessage()]
    request_ids = {
        message.split("request_id=", 1)[1].split(" ", 1)[0]
        for message in messages
    }
    assert request_ids == {response.headers["x-request-id"]}
    assert any("stage=catalogue event=start" in message for message in messages)


@pytest.mark.asyncio
async def test_pile_reelle_main_correlle_aussi_la_reponse_429():
    app = create_app()
    request_metrics.reset()
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            for _ in range(31):
                response = await client.get(
                    "/api/advise/not-a-route",
                    headers={"x-forwarded-for": "203.0.113.77"},
                )

        assert response.status_code == 429
        assert len(response.headers["x-request-id"]) == 32
        assert response.headers["x-response-time"].endswith("ms")
        assert response.headers["retry-after"] == "60"
        snapshot = request_metrics.snapshot()
        assert snapshot["overall"]["requests"] == 31
        assert snapshot["overall"]["status_groups"] == {"4xx": 31}
    finally:
        request_metrics.reset()


@pytest.mark.asyncio
async def test_readiness_refuse_base_lente_et_revision_invalide(monkeypatch):
    async def slow_database():
        return {"status": "slow", "latency_ms": 2000}

    monkeypatch.setattr(health_module, "_check_db", slow_database)
    response = await health_module.readiness()
    assert response.status_code == 503

    async def healthy_database():
        return {"status": "ok", "latency_ms": 1}

    async def invalid_schema():
        raise RuntimeError("revision secrète à ne pas exposer")

    monkeypatch.setattr(health_module, "_check_db", healthy_database)
    monkeypatch.setattr(health_module.db, "assert_schema_current", invalid_schema)
    response = await health_module.readiness()
    assert response.status_code == 503
    assert b"revision secr" not in response.body
    assert b"schema_revision_invalid" in response.body


@pytest.mark.asyncio
async def test_readiness_sans_base_est_locale_seulement(monkeypatch):
    async def disabled_database():
        return {"status": "disabled", "latency_ms": 0}

    monkeypatch.setattr(health_module, "_check_db", disabled_database)
    monkeypatch.setattr(
        health_module,
        "get_settings",
        lambda: Settings(
            env="production",
            debug=False,
            cors_origins="https://filon.be",
            database_url="postgresql+asyncpg://filon:test@database/filon",
            database_schema_mode="alembic",
        ),
    )
    production = await health_module.readiness()
    assert production.status_code == 503

    monkeypatch.setattr(
        health_module,
        "get_settings",
        lambda: Settings(env="dev"),
    )
    development = await health_module.readiness()
    assert development.status_code == 200
    assert json.loads(development.body)["ready"] is True
