from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config import Settings


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
