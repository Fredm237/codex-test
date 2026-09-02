from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config import Settings, V2_SHADOW_WRITER_FIELDS


def _production(**overrides) -> Settings:
    values = {
        "env": "production",
        "debug": False,
        "cors_origins": '["https://filon.be","https://www.filon.be"]',
        "database_url": "postgresql+asyncpg://filon:secret@database:5432/filon",
        "database_schema_mode": "alembic",
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def test_defaults_are_closed_without_explicit_local_configuration() -> None:
    settings = Settings(_env_file=None)

    assert settings.debug is False
    assert settings.cors_origins_list == []
    assert settings.is_production is False


def test_environment_is_required_and_unknown_values_are_rejected(monkeypatch) -> None:
    monkeypatch.delenv("ENV", raising=False)

    with pytest.raises(ValidationError, match="env"):
        Settings(_env_file=None)
    with pytest.raises(ValidationError, match="env"):
        Settings(_env_file=None, env="preview")


def test_staging_uses_the_same_fail_closed_boundary_as_production() -> None:
    with pytest.raises(ValidationError, match="CORS_ORIGINS must be explicit"):
        Settings(_env_file=None, env="staging")

    settings = _production(env="staging")
    assert settings.is_production is True


def test_development_accepts_an_explicit_wildcard_but_never_infers_it() -> None:
    settings = Settings(_env_file=None, env="dev", cors_origins="*")

    assert settings.cors_origins_list == ["*"]


def test_production_accepts_only_an_explicit_safe_database_contract() -> None:
    settings = _production()

    assert settings.is_production is True
    assert settings.cors_origins_list == [
        "https://filon.be",
        "https://www.filon.be",
    ]


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"debug": True}, "DEBUG must be false"),
        ({"cors_origins": ""}, "CORS_ORIGINS must be explicit"),
        ({"cors_origins": "*"}, "wildcard is forbidden"),
        ({"cors_origins": "http://filon.be"}, "invalid production CORS origin"),
        ({"cors_origins": "https://filon.be/path"}, "invalid production CORS origin"),
        ({"database_url": None}, "DATABASE_URL is required"),
        ({"database_url": "sqlite:///filon.db"}, "must use PostgreSQL"),
        ({"database_schema_mode": "legacy"}, "must be alembic"),
    ],
)
def test_production_rejects_every_unsafe_boundary(overrides, message) -> None:
    with pytest.raises(ValidationError, match=message):
        _production(**overrides)


@pytest.mark.parametrize(
    "cors_origins",
    [
        "[",
        "[]",
        '["https://filon.be", 42]',
        '["https://filon.be", ""]',
        '["https://filon.be", "https://filon.be"]',
    ],
)
def test_cors_parser_rejects_malformed_or_ambiguous_configuration(
    cors_origins: str,
) -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, env="dev", cors_origins=cors_origins)


def test_cors_parser_accepts_trimmed_csv_without_changing_order() -> None:
    settings = Settings(
        _env_file=None,
        env="dev",
        cors_origins=" http://localhost:3000, http://127.0.0.1:3000 ",
    )

    assert settings.cors_origins_list == [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


def test_validation_errors_never_render_database_credentials() -> None:
    with pytest.raises(ValidationError) as captured:
        _production(
            debug=True,
            database_url="postgresql://filon:do-not-render@database/filon",
        )

    assert "do-not-render" not in str(captured.value)


@pytest.mark.parametrize(
    "token",
    [
        "short",
        " leading-token-that-is-long-enough-to-be-invalid",
        "trailing-token-that-is-long-enough-to-be-invalid ",
        "token-with-a-newline-that-is-long\nenough-to-be-invalid",
        "jeton-métriques-non-ascii-mais-assez-long-pour-être-refusé",
    ],
)
def test_metrics_export_token_rejects_weak_or_ambiguous_values(token: str) -> None:
    with pytest.raises(ValidationError, match="METRICS_EXPORT_TOKEN"):
        Settings(_env_file=None, env="test", metrics_export_token=token)


def test_otlp_trace_export_is_disabled_without_dangling_configuration() -> None:
    settings = Settings(_env_file=None, env="test")

    assert settings.trace_export_backend == "disabled"
    assert settings.otlp_traces_endpoint is None

    with pytest.raises(ValidationError, match="TRACE_EXPORT_BACKEND=otlp_http"):
        Settings(
            _env_file=None,
            env="test",
            otlp_traces_endpoint="http://localhost:4318/v1/traces",
        )


def test_production_otlp_trace_export_requires_https_token_and_exact_path() -> None:
    token = "t" * 32
    settings = _production(
        trace_export_backend="otlp_http",
        otlp_traces_endpoint="https://otel.example.com/v1/traces",
        otlp_trace_export_token=token,
    )

    assert settings.trace_export_sample_ratio == 0.1

    for endpoint in (
        "http://otel.example.com/v1/traces",
        "https://user:password@otel.example.com/v1/traces",
        "https://otel.example.com/v1/metrics",
        "https://otel.example.com/v1/traces?secret=value",
    ):
        with pytest.raises(ValidationError, match="safe OTLP/HTTP"):
            _production(
                trace_export_backend="otlp_http",
                otlp_traces_endpoint=endpoint,
                otlp_trace_export_token=token,
            )

    with pytest.raises(ValidationError, match="OTLP_TRACE_EXPORT_TOKEN"):
        _production(
            trace_export_backend="otlp_http",
            otlp_traces_endpoint="https://otel.example.com/v1/traces",
        )


def test_metrics_export_token_accepts_an_explicit_strong_value() -> None:
    token = "metrics-export-token-32-characters-minimum"

    settings = Settings(
        _env_file=None,
        env="test",
        metrics_export_token=token,
    )

    assert settings.metrics_export_token == token


def test_empty_metrics_export_token_keeps_the_export_disabled() -> None:
    settings = Settings(
        _env_file=None,
        env="test",
        metrics_export_token="",
    )

    assert settings.metrics_export_token is None


def test_rate_limit_remains_local_without_an_explicit_opt_in() -> None:
    settings = Settings(_env_file=None, env="test")

    assert settings.rate_limit_backend == "local"
    assert settings.rate_limit_identity_secret is None


def test_product_graph_shadow_is_off_and_depends_on_observation_provenance() -> None:
    settings = Settings(_env_file=None, env="test")
    assert settings.v2_chain_mode == "off"
    assert settings.v2_canary_reader_enabled is False
    assert settings.v2_public_reader_enabled is False
    assert settings.observation_shadow_enabled is False
    assert settings.product_graph_shadow_enabled is False
    assert settings.entity_resolution_shadow_enabled is False
    assert settings.offer_graph_shadow_enabled is False
    assert settings.offer_truth_shadow_enabled is False
    assert settings.product_ontology_shadow_enabled is False
    assert settings.hybrid_retrieval_shadow_enabled is False
    assert settings.constraint_engine_shadow_enabled is False
    assert settings.product_ranking_shadow_enabled is False
    assert settings.offer_optimization_shadow_enabled is False
    assert settings.confidence_shadow_enabled is False
    assert settings.buy_wait_shadow_enabled is False
    assert settings.personal_commerce_shadow_enabled is False
    assert settings.personal_commerce_subject_secret is None
    assert settings.merchant_intelligence_shadow_enabled is False
    assert settings.evidence_engine_shadow_enabled is False

    with pytest.raises(
        ValidationError,
        match="PRODUCT_GRAPH_SHADOW_ENABLED requires OBSERVATION_SHADOW_ENABLED",
    ):
        Settings(
            _env_file=None,
            env="test",
            product_graph_shadow_enabled=True,
        )

    enabled = Settings(
        _env_file=None,
        env="test",
        observation_shadow_enabled=True,
        product_graph_shadow_enabled=True,
    )
    assert enabled.product_graph_shadow_enabled is True

    with pytest.raises(
        ValidationError,
        match="ENTITY_RESOLUTION_SHADOW_ENABLED requires Observation and Product Graph shadows",
    ):
        Settings(
            _env_file=None,
            env="test",
            entity_resolution_shadow_enabled=True,
        )

    entity_enabled = Settings(
        _env_file=None,
        env="test",
        observation_shadow_enabled=True,
        product_graph_shadow_enabled=True,
        entity_resolution_shadow_enabled=True,
    )
    assert entity_enabled.entity_resolution_shadow_enabled is True

    with pytest.raises(
        ValidationError,
        match="OFFER_GRAPH_SHADOW_ENABLED requires OBSERVATION_SHADOW_ENABLED",
    ):
        Settings(
            _env_file=None,
            env="test",
            offer_graph_shadow_enabled=True,
        )

    offer_enabled = Settings(
        _env_file=None,
        env="test",
        observation_shadow_enabled=True,
        offer_graph_shadow_enabled=True,
    )
    assert offer_enabled.offer_graph_shadow_enabled is True

    with pytest.raises(
        ValidationError,
        match="OFFER_TRUTH_SHADOW_ENABLED requires Observation, Product Graph",
    ):
        Settings(
            _env_file=None,
            env="test",
            observation_shadow_enabled=True,
            product_graph_shadow_enabled=True,
            offer_graph_shadow_enabled=True,
            offer_truth_shadow_enabled=True,
        )

    offer_truth_enabled = Settings(
        _env_file=None,
        env="test",
        observation_shadow_enabled=True,
        product_graph_shadow_enabled=True,
        entity_resolution_shadow_enabled=True,
        offer_graph_shadow_enabled=True,
        offer_truth_shadow_enabled=True,
    )
    assert offer_truth_enabled.offer_truth_shadow_enabled is True

    with pytest.raises(
        ValidationError,
        match="PRODUCT_ONTOLOGY_SHADOW_ENABLED requires Observation, Product Graph",
    ):
        Settings(
            _env_file=None,
            env="test",
            observation_shadow_enabled=True,
            product_graph_shadow_enabled=True,
            product_ontology_shadow_enabled=True,
        )

    ontology_enabled = Settings(
        _env_file=None,
        env="test",
        observation_shadow_enabled=True,
        product_graph_shadow_enabled=True,
        entity_resolution_shadow_enabled=True,
        product_ontology_shadow_enabled=True,
    )
    assert ontology_enabled.product_ontology_shadow_enabled is True

    with pytest.raises(
        ValidationError,
        match="HYBRID_RETRIEVAL_SHADOW_ENABLED requires Observation, Product Graph",
    ):
        Settings(
            _env_file=None,
            env="test",
            observation_shadow_enabled=True,
            product_graph_shadow_enabled=True,
            entity_resolution_shadow_enabled=True,
            hybrid_retrieval_shadow_enabled=True,
        )

    retrieval_enabled = Settings(
        _env_file=None,
        env="test",
        observation_shadow_enabled=True,
        product_graph_shadow_enabled=True,
        entity_resolution_shadow_enabled=True,
        product_ontology_shadow_enabled=True,
        hybrid_retrieval_shadow_enabled=True,
    )
    assert retrieval_enabled.hybrid_retrieval_shadow_enabled is True

    with pytest.raises(
        ValidationError,
        match="CONSTRAINT_ENGINE_SHADOW_ENABLED requires HYBRID_RETRIEVAL_SHADOW_ENABLED",
    ):
        Settings(
            _env_file=None,
            env="test",
            constraint_engine_shadow_enabled=True,
        )

    constraint_enabled = Settings(
        _env_file=None,
        env="test",
        observation_shadow_enabled=True,
        product_graph_shadow_enabled=True,
        entity_resolution_shadow_enabled=True,
        product_ontology_shadow_enabled=True,
        hybrid_retrieval_shadow_enabled=True,
        constraint_engine_shadow_enabled=True,
    )
    assert constraint_enabled.constraint_engine_shadow_enabled is True

    with pytest.raises(
        ValidationError,
        match="PRODUCT_RANKING_SHADOW_ENABLED requires CONSTRAINT_ENGINE_SHADOW_ENABLED",
    ):
        Settings(
            _env_file=None,
            env="test",
            product_ranking_shadow_enabled=True,
        )

    ranking_enabled = Settings(
        _env_file=None,
        env="test",
        observation_shadow_enabled=True,
        product_graph_shadow_enabled=True,
        entity_resolution_shadow_enabled=True,
        product_ontology_shadow_enabled=True,
        hybrid_retrieval_shadow_enabled=True,
        constraint_engine_shadow_enabled=True,
        product_ranking_shadow_enabled=True,
    )
    assert ranking_enabled.product_ranking_shadow_enabled is True

    with pytest.raises(
        ValidationError,
        match="OFFER_OPTIMIZATION_SHADOW_ENABLED requires Product Ranking and Offer Truth shadows",
    ):
        Settings(
            _env_file=None,
            env="test",
            offer_optimization_shadow_enabled=True,
        )

    optimization_enabled = Settings(
        _env_file=None,
        env="test",
        observation_shadow_enabled=True,
        product_graph_shadow_enabled=True,
        entity_resolution_shadow_enabled=True,
        offer_graph_shadow_enabled=True,
        offer_truth_shadow_enabled=True,
        product_ontology_shadow_enabled=True,
        hybrid_retrieval_shadow_enabled=True,
        constraint_engine_shadow_enabled=True,
        product_ranking_shadow_enabled=True,
        offer_optimization_shadow_enabled=True,
    )
    assert optimization_enabled.offer_optimization_shadow_enabled is True

    with pytest.raises(
        ValidationError,
        match="CONFIDENCE_SHADOW_ENABLED requires OFFER_OPTIMIZATION_SHADOW_ENABLED",
    ):
        Settings(
            _env_file=None,
            env="test",
            confidence_shadow_enabled=True,
        )

    confidence_enabled = Settings(
        _env_file=None,
        env="test",
        observation_shadow_enabled=True,
        product_graph_shadow_enabled=True,
        entity_resolution_shadow_enabled=True,
        offer_graph_shadow_enabled=True,
        offer_truth_shadow_enabled=True,
        product_ontology_shadow_enabled=True,
        hybrid_retrieval_shadow_enabled=True,
        constraint_engine_shadow_enabled=True,
        product_ranking_shadow_enabled=True,
        offer_optimization_shadow_enabled=True,
        confidence_shadow_enabled=True,
    )
    assert confidence_enabled.confidence_shadow_enabled is True

    with pytest.raises(
        ValidationError,
        match="BUY_WAIT_SHADOW_ENABLED requires CONFIDENCE_SHADOW_ENABLED",
    ):
        Settings(
            _env_file=None,
            env="test",
            buy_wait_shadow_enabled=True,
        )

    buy_wait_enabled = Settings(
        _env_file=None,
        env="test",
        observation_shadow_enabled=True,
        product_graph_shadow_enabled=True,
        entity_resolution_shadow_enabled=True,
        offer_graph_shadow_enabled=True,
        offer_truth_shadow_enabled=True,
        product_ontology_shadow_enabled=True,
        hybrid_retrieval_shadow_enabled=True,
        constraint_engine_shadow_enabled=True,
        product_ranking_shadow_enabled=True,
        offer_optimization_shadow_enabled=True,
        confidence_shadow_enabled=True,
        buy_wait_shadow_enabled=True,
    )
    assert buy_wait_enabled.buy_wait_shadow_enabled is True

    with pytest.raises(
        ValidationError,
        match="PERSONAL_COMMERCE_SHADOW_ENABLED requires BUY_WAIT_SHADOW_ENABLED",
    ):
        Settings(
            _env_file=None,
            env="test",
            personal_commerce_shadow_enabled=True,
            personal_commerce_subject_secret="p" * 32,
        )

    with pytest.raises(
        ValidationError,
        match="PERSONAL_COMMERCE_SUBJECT_SECRET is required",
    ):
        Settings(
            _env_file=None,
            env="test",
            observation_shadow_enabled=True,
            product_graph_shadow_enabled=True,
            entity_resolution_shadow_enabled=True,
            offer_graph_shadow_enabled=True,
            offer_truth_shadow_enabled=True,
            product_ontology_shadow_enabled=True,
            hybrid_retrieval_shadow_enabled=True,
            constraint_engine_shadow_enabled=True,
            product_ranking_shadow_enabled=True,
            offer_optimization_shadow_enabled=True,
            confidence_shadow_enabled=True,
            buy_wait_shadow_enabled=True,
            personal_commerce_shadow_enabled=True,
        )

    personal_commerce_enabled = Settings(
        _env_file=None,
        env="test",
        observation_shadow_enabled=True,
        product_graph_shadow_enabled=True,
        entity_resolution_shadow_enabled=True,
        offer_graph_shadow_enabled=True,
        offer_truth_shadow_enabled=True,
        product_ontology_shadow_enabled=True,
        hybrid_retrieval_shadow_enabled=True,
        constraint_engine_shadow_enabled=True,
        product_ranking_shadow_enabled=True,
        offer_optimization_shadow_enabled=True,
        confidence_shadow_enabled=True,
        buy_wait_shadow_enabled=True,
        personal_commerce_shadow_enabled=True,
        personal_commerce_subject_secret="p" * 32,
    )
    assert personal_commerce_enabled.personal_commerce_shadow_enabled is True

    with pytest.raises(
        ValidationError,
        match="PERSONAL_COMMERCE_SUBJECT_SECRET must be 32-256",
    ):
        Settings(
            _env_file=None,
            env="test",
            personal_commerce_subject_secret="too-short",
        )

    with pytest.raises(
        ValidationError,
        match="MERCHANT_INTELLIGENCE_SHADOW_ENABLED requires all Graph shadows",
    ):
        Settings(
            _env_file=None,
            env="test",
            observation_shadow_enabled=True,
            merchant_intelligence_shadow_enabled=True,
        )

    merchant_enabled = Settings(
        _env_file=None,
        env="test",
        observation_shadow_enabled=True,
        product_graph_shadow_enabled=True,
        offer_graph_shadow_enabled=True,
        merchant_intelligence_shadow_enabled=True,
    )
    assert merchant_enabled.merchant_intelligence_shadow_enabled is True

    with pytest.raises(
        ValidationError,
        match="EVIDENCE_ENGINE_SHADOW_ENABLED requires all prior shadows",
    ):
        Settings(
            _env_file=None,
            env="test",
            observation_shadow_enabled=True,
            product_graph_shadow_enabled=True,
            offer_graph_shadow_enabled=True,
            evidence_engine_shadow_enabled=True,
        )

    evidence_enabled = Settings(
        _env_file=None,
        env="test",
        observation_shadow_enabled=True,
        product_graph_shadow_enabled=True,
        offer_graph_shadow_enabled=True,
        merchant_intelligence_shadow_enabled=True,
        evidence_engine_shadow_enabled=True,
    )
    assert evidence_enabled.evidence_engine_shadow_enabled is True


def test_atomic_v2_shadow_mode_enables_every_writer_and_no_reader() -> None:
    settings = Settings(_env_file=None, env="test", v2_chain_mode="shadow")

    assert settings.v2_chain_mode == "shadow"
    assert all(getattr(settings, field) for field in V2_SHADOW_WRITER_FIELDS)
    assert settings.v2_canary_reader_enabled is False
    assert settings.v2_public_reader_enabled is False
    assert settings.personal_commerce_shadow_enabled is False


def test_atomic_v2_shadow_mode_expands_from_the_environment(monkeypatch) -> None:
    monkeypatch.setenv("V2_CHAIN_MODE", "shadow")

    settings = Settings(_env_file=None, env="test")

    assert settings.v2_chain_mode == "shadow"
    assert all(getattr(settings, field) for field in V2_SHADOW_WRITER_FIELDS)


@pytest.mark.parametrize(
    "reader",
    ["v2_canary_reader_enabled", "v2_public_reader_enabled"],
)
def test_atomic_v2_shadow_mode_rejects_public_readers(reader: str) -> None:
    with pytest.raises(
        ValidationError,
        match="V2_CHAIN_MODE=shadow forbids every V2 public reader",
    ):
        Settings(
            _env_file=None,
            env="test",
            v2_chain_mode="shadow",
            **{reader: True},
        )


def test_atomic_v2_shadow_mode_rejects_an_explicitly_disabled_writer() -> None:
    with pytest.raises(
        ValidationError,
        match="V2_CHAIN_MODE=shadow cannot disable required writers",
    ):
        Settings(
            _env_file=None,
            env="test",
            v2_chain_mode="shadow",
            product_ranking_shadow_enabled=False,
        )


@pytest.mark.parametrize("mode", ["canary", "public"])
def test_unqualified_v2_reader_modes_fail_closed(mode: str) -> None:
    with pytest.raises(
        ValidationError,
        match=rf"V2_CHAIN_MODE={mode} is not qualified",
    ):
        Settings(_env_file=None, env="test", v2_chain_mode=mode)


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        (
            {"rate_limit_backend": "redis"},
            "REDIS_URL is required",
        ),
        (
            {
                "rate_limit_backend": "redis",
                "redis_url": "redis://redis:6379/0",
            },
            "RATE_LIMIT_IDENTITY_SECRET is required",
        ),
        (
            {
                "rate_limit_backend": "redis",
                "redis_url": "https://redis.invalid",
                "rate_limit_identity_secret": "r" * 32,
            },
            "REDIS_URL must use Redis",
        ),
    ],
)
def test_distributed_rate_limit_requires_its_complete_contract(
    overrides,
    message,
) -> None:
    with pytest.raises(ValidationError, match=message):
        Settings(_env_file=None, env="test", **overrides)


@pytest.mark.parametrize(
    "secret",
    [
        "short",
        " leading-secret-that-is-long-enough",
        "trailing-secret-that-is-long-enough ",
        "secret-with-a-newline-that-is-long\nenough",
        "secret-non-ascii-qui-est-assez-long-éééééééé",
    ],
)
def test_rate_limit_identity_secret_rejects_ambiguous_values(secret) -> None:
    with pytest.raises(ValidationError, match="RATE_LIMIT_IDENTITY_SECRET"):
        Settings(
            _env_file=None,
            env="test",
            rate_limit_identity_secret=secret,
        )


def test_distributed_rate_limit_accepts_a_bounded_redis_configuration() -> None:
    secret = "rate-limit-shared-secret-with-32-characters"
    settings = Settings(
        _env_file=None,
        env="test",
        rate_limit_backend="redis",
        redis_url="rediss://redis.internal:6380/0",
        rate_limit_identity_secret=secret,
        rate_limit_redis_timeout_seconds=0.2,
    )

    assert settings.rate_limit_backend == "redis"
    assert settings.rate_limit_identity_secret == secret
    assert settings.rate_limit_redis_timeout_seconds == 0.2


def test_production_redis_requires_the_railway_identity_source() -> None:
    with pytest.raises(
        ValidationError,
        match="RATE_LIMIT_IDENTITY_SOURCE must be railway",
    ):
        _production(
            rate_limit_backend="redis",
            redis_url="redis://redis.internal:6379/0",
            rate_limit_identity_secret="s" * 32,
        )


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        (
            {"env": "test"},
            "only valid in a deployed environment",
        ),
        (
            {"railway_environment_id": None},
            "RAILWAY_ENVIRONMENT_ID must be a canonical UUID",
        ),
        (
            {"railway_service_id": "NOT-A-UUID"},
            "RAILWAY_SERVICE_ID must be a canonical UUID",
        ),
    ],
)
def test_railway_identity_source_rejects_an_unbound_platform(
    overrides,
    message,
) -> None:
    values = {
        "rate_limit_identity_source": "railway",
        "railway_environment_id": "b843980b-13e3-414b-8568-890a953310ed",
        "railway_service_id": "d68db2c1-3ff8-45ca-a329-c89b4e81fab9",
    }
    values.update(overrides)

    with pytest.raises(ValidationError, match=message):
        _production(**values)


def test_production_redis_accepts_canonical_railway_identity() -> None:
    settings = _production(
        rate_limit_backend="redis",
        rate_limit_identity_source="railway",
        rate_limit_identity_secret="s" * 32,
        redis_url="redis://redis.internal:6379/0",
        railway_environment_id="b843980b-13e3-414b-8568-890a953310ed",
        railway_service_id="d68db2c1-3ff8-45ca-a329-c89b4e81fab9",
    )

    assert settings.rate_limit_identity_source == "railway"


def test_awin_feed_limits_are_finite_by_default() -> None:
    settings = Settings(_env_file=None, env="test")

    assert settings.awin_max_rows_per_feed == 100_000
    assert settings.awin_max_download_bytes == 256 * 1024 * 1024
    assert settings.awin_max_decompressed_bytes == 512 * 1024 * 1024


@pytest.mark.parametrize(
    "overrides",
    [
        {"awin_max_rows_per_feed": -1},
        {"awin_max_rows_per_feed": 250_001},
        {"awin_max_download_bytes": 1023},
        {"awin_max_download_bytes": 1024 * 1024 * 1024 + 1},
        {"awin_max_decompressed_bytes": 1023},
        {"awin_max_decompressed_bytes": 2 * 1024 * 1024 * 1024 + 1},
    ],
)
def test_awin_feed_limits_reject_out_of_contract_values(overrides) -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, env="test", **overrides)
