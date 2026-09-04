"""Commande privée de qualification et persistance des promotions V2."""

from __future__ import annotations

import json
from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from jsonschema import Draft202012Validator

from app.v2_chain import promote
from app.v2_chain.promotion_receipt import (
    PUBLIC_PROOF_KEYS,
    SHADOW_PROOF_KEYS,
    V2PromotionPersistenceReport,
)
from quality_lab.v2_canary import V2CanaryGateReport
from quality_lab.v2_public import V2PublicGateReport


CONTRACT_ROOT = (
    Path(__file__).resolve().parents[2] / "contracts" / "v2-chain" / "v1"
)


def _digest(character: str) -> str:
    return "sha256:" + character * 64


def _proof_args(names: frozenset[str]) -> list[tuple[str, str]]:
    return [(name, _digest("a")) for name in sorted(names)]


def _session_scope(session):
    @asynccontextmanager
    async def scope():
        yield session

    return scope


def _settings(*, stage: str, receipt: str | None = None):
    return SimpleNamespace(
        database_schema_mode="alembic",
        database_url="sqlite+aiosqlite:///:memory:",
        v2_chain_mode="dark" if stage == "canary" else "canary",
        v2_chain_campaign_id=_digest("f"),
        v2_canary_reader_enabled=stage == "public",
        v2_public_reader_enabled=False,
        v2_promotion_receipt_evaluation_id=receipt,
        debug=False,
    )


def _configure(monkeypatch, *, settings, session) -> None:
    monkeypatch.setattr(promote, "get_settings", lambda: settings)
    monkeypatch.setattr(promote.db, "is_enabled", lambda: True)
    monkeypatch.setattr(promote.db, "prepare_schema", AsyncMock())
    monkeypatch.setattr(promote.db, "session_scope", _session_scope(session))


@pytest.mark.asyncio
async def test_canary_command_builds_dry_run_from_the_exact_proof_set(
    monkeypatch,
) -> None:
    session = SimpleNamespace(commit=AsyncMock())
    settings = _settings(stage="canary")
    _configure(monkeypatch, settings=settings, session=session)
    gate = V2CanaryGateReport(
        schema_version="v2-shadow-to-canary-gate/v1",
        status="CANARY_AUTHORIZED",
        gates={"all": True},
        blocked_response_types=("BUY_NOW", "WAIT"),
        blocker_codes=("RESPONSE_TYPE_OFF:BUY_NOW", "RESPONSE_TYPE_OFF:WAIT"),
        evaluation_id=_digest("b"),
    )
    report = SimpleNamespace(gate=gate)
    evaluate = AsyncMock(return_value=report)
    monkeypatch.setattr(promote, "evaluate_persisted_shadow_to_canary", evaluate)
    record = AsyncMock(
        return_value=V2PromotionPersistenceReport(
            "v2-promotion-persistence/v1",
            "dry_run",
            "shadow_to_canary",
            _digest("c"),
            None,
        )
    )
    monkeypatch.setattr(promote, "record_promotion_receipt", record)
    args = SimpleNamespace(
        stage="canary",
        evaluated_at=promote._parse_evaluated_at("2026-09-04T01:00:00Z"),
        proof=_proof_args(SHADOW_PROOF_KEYS),
        maximum_p95_window_ms=500,
        apply=False,
    )

    receipt = await promote._run(args)

    assert receipt.qualification_status == "CANARY_AUTHORIZED"
    assert receipt.persistence_status == "dry_run"
    assert receipt.authorized_response_types == ("ABSTAIN",)
    assert receipt.blocked_response_types == ("BUY_NOW", "WAIT")
    assert receipt.raw_payload_retained is False
    evaluate.assert_awaited_once()
    record.assert_awaited_once_with(session, report=report, apply=False)
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_public_command_uses_active_canary_receipt_and_commits_apply(
    monkeypatch,
) -> None:
    shadow_receipt = _digest("c")
    session = SimpleNamespace(commit=AsyncMock())
    settings = _settings(stage="public", receipt=shadow_receipt)
    _configure(monkeypatch, settings=settings, session=session)
    shadow_gate = V2CanaryGateReport(
        schema_version="v2-shadow-to-canary-gate/v1",
        status="CANARY_AUTHORIZED",
        gates={"all": True},
        blocked_response_types=("BUY_NOW", "WAIT"),
        blocker_codes=("RESPONSE_TYPE_OFF:BUY_NOW", "RESPONSE_TYPE_OFF:WAIT"),
        evaluation_id=_digest("b"),
    )
    load = AsyncMock(return_value=shadow_gate)
    monkeypatch.setattr(promote, "load_authorized_canary_gate", load)
    public_gate = V2PublicGateReport(
        schema_version="v2-canary-to-public-gate/v1",
        status="PUBLIC_AUTHORIZED",
        gates={"all": True},
        authorized_response_types=("ABSTAIN",),
        blocked_response_types=("BUY_NOW", "WAIT"),
        blocker_codes=("RESPONSE_TYPE_OFF:BUY_NOW", "RESPONSE_TYPE_OFF:WAIT"),
        evaluation_id=_digest("d"),
    )
    report = SimpleNamespace(gate=public_gate)
    evaluate = AsyncMock(return_value=report)
    monkeypatch.setattr(promote, "evaluate_persisted_canary_to_public", evaluate)
    record = AsyncMock(
        return_value=V2PromotionPersistenceReport(
            "v2-promotion-persistence/v1",
            "created",
            "canary_to_public",
            _digest("e"),
            12,
        )
    )
    monkeypatch.setattr(promote, "record_promotion_receipt", record)
    args = SimpleNamespace(
        stage="public",
        evaluated_at=promote._parse_evaluated_at("2026-09-04T02:00:00Z"),
        proof=_proof_args(PUBLIC_PROOF_KEYS - {"shadow_gate_ref"}),
        shadow_receipt_evaluation_id=shadow_receipt,
        minimum_paired_observations=30,
        minimum_observations_per_response_type=30,
        response_type=["ABSTAIN"],
        apply=True,
    )

    receipt = await promote._run(args)

    assert receipt.qualification_status == "PUBLIC_AUTHORIZED"
    assert receipt.persistence_status == "created"
    assert receipt.receipt_id == 12
    load.assert_awaited_once_with(
        session,
        receipt_evaluation_id=shadow_receipt,
    )
    record.assert_awaited_once_with(session, report=report, apply=True)
    session.commit.assert_awaited_once()


def test_proof_set_rejects_missing_duplicate_or_unknown_names() -> None:
    expected = frozenset({"a", "b"})
    with pytest.raises(ValueError, match="required set"):
        promote._proof_mapping([("a", _digest("a"))], expected=expected)
    with pytest.raises(ValueError, match="duplicate"):
        promote._proof_mapping(
            [("a", _digest("a")), ("a", _digest("b"))],
            expected=frozenset({"a"}),
        )
    with pytest.raises(ValueError, match="required set"):
        promote._proof_mapping(
            [("a", _digest("a")), ("unknown", _digest("b"))],
            expected=expected,
        )


def test_public_configuration_requires_the_active_canary_receipt(monkeypatch) -> None:
    settings = _settings(stage="public", receipt=_digest("a"))
    monkeypatch.setattr(promote, "get_settings", lambda: settings)
    monkeypatch.setattr(promote.db, "is_enabled", lambda: True)
    args = SimpleNamespace(
        stage="public",
        shadow_receipt_evaluation_id=_digest("b"),
    )

    with pytest.raises(RuntimeError, match="active canary receipt"):
        promote._validate_configuration(args)


def test_promotion_command_contract_and_examples_are_valid() -> None:
    schema = json.loads(
        (CONTRACT_ROOT / "promotion-command-receipt.schema.json").read_text()
    )
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    manifest = json.loads((CONTRACT_ROOT / "manifest.json").read_text())
    for relative_path in manifest["promotion_command_receipt_examples"]:
        validator.validate(json.loads((CONTRACT_ROOT / relative_path).read_text()))


def test_proof_subcommand_requires_a_registered_kind_and_explicit_timestamp() -> None:
    args = promote._parser().parse_args(
        [
            "proof",
            "--scope-ref",
            _digest("a"),
            "--proof-kind",
            "single_alembic_head_ref",
            "--artifact-ref",
            "test:alembic/single-head",
            "--artifact-digest",
            _digest("b"),
            "--verifier-version",
            "local-v1",
            "--verification-status",
            "VERIFIED",
            "--verified-at",
            "2026-09-04T12:00:00Z",
        ]
    )

    assert args.stage == "proof"
    assert args.verified_at.tzinfo is not None
    assert args.apply is False
