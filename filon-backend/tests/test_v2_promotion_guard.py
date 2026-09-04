"""Garde runtime des modes V2 CANARY/PUBLIC."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import Settings
from app.db import models as core_models  # noqa: F401
from app.db.base import Base
from app.v2_chain.models import V2PromotionReceipt
from app.v2_chain.proof_registry import record_promotion_proof
from app.v2_chain.promotion_guard import (
    CANARY_GATES,
    PUBLIC_GATES,
    V2PromotionGuardError,
    authorize_v2_runtime,
    load_authorized_canary_gate,
)
from app.v2_chain.promotion_receipt import PUBLIC_PROOF_KEYS, SHADOW_PROOF_KEYS


CONTRACT_ROOT = (
    Path(__file__).resolve().parents[2] / "contracts" / "v2-chain" / "v1"
)


def _digest(character: str) -> str:
    return "sha256:" + character * 64


def _proofs(names: frozenset[str]) -> dict[str, str]:
    return {
        name: _digest(format(index + 1, "x")[-1])
        for index, name in enumerate(sorted(names))
    }


def _shadow_receipt(**overrides) -> V2PromotionReceipt:
    values = {
        "evaluation_id": _digest("a"),
        "gate_evaluation_id": _digest("b"),
        "source_gate_evaluation_id": None,
        "promotion_stage": "shadow_to_canary",
        "status": "CANARY_AUTHORIZED",
        "authorized_response_types_json": ["ABSTAIN"],
        "blocked_response_types_json": ["BUY_NOW", "WAIT"],
        "gates_json": {name: True for name in CANARY_GATES},
        "metrics_json": {"valid_terminal_windows": 30},
        "proof_refs_json": _proofs(SHADOW_PROOF_KEYS),
        "policy_json": {
            "campaign_id": _digest("f"),
            "maximum_p95_window_ms": 500,
        },
        "raw_payload_retained": False,
        "evaluated_at": datetime(2026, 9, 4, 12, 0, 0),
    }
    values.update(overrides)
    return V2PromotionReceipt(**values)


def _public_receipt(**overrides) -> V2PromotionReceipt:
    source_gate = _digest("b")
    proofs = _proofs(PUBLIC_PROOF_KEYS)
    proofs["shadow_gate_ref"] = source_gate
    values = {
        "evaluation_id": _digest("c"),
        "gate_evaluation_id": _digest("d"),
        "source_gate_evaluation_id": source_gate,
        "promotion_stage": "canary_to_public",
        "status": "PUBLIC_AUTHORIZED",
        "authorized_response_types_json": ["ABSTAIN"],
        "blocked_response_types_json": ["BUY_NOW", "WAIT"],
        "gates_json": {name: True for name in PUBLIC_GATES},
        "metrics_json": {"paired_observations": 30},
        "proof_refs_json": proofs,
        "policy_json": {"requested_response_types": ["ABSTAIN"]},
        "raw_payload_retained": False,
        "evaluated_at": datetime(2026, 9, 4, 13, 0, 0),
    }
    values.update(overrides)
    return V2PromotionReceipt(**values)


def _settings(mode: str) -> Settings:
    common = {
        "_env_file": None,
        "env": "test",
        "v2_chain_mode": mode,
        "v2_chain_campaign_id": _digest("f"),
        "v2_promotion_receipt_evaluation_id": (
            _digest("a") if mode == "canary" else _digest("c")
        ),
        "v2_supported_verticals": "smartphones",
        "v2_supported_locales": "fr-BE",
        "v2_supported_decision_types": "purchase_advice",
        "v2_max_data_age_seconds": 300,
    }
    if mode == "canary":
        common.update(
            v2_canary_reader_enabled=True,
            v2_canary_subject_digests=_digest("e"),
        )
    else:
        common.update(v2_public_reader_enabled=True)
    return Settings(**common)


async def _database():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    return engine, async_sessionmaker(engine, expire_on_commit=False)


async def _register_receipt_proofs(session, receipt: V2PromotionReceipt) -> None:
    scope_ref = (
        receipt.policy_json["campaign_id"]
        if receipt.promotion_stage == "shadow_to_canary"
        else receipt.source_gate_evaluation_id
    )
    refs: dict[str, str] = {}
    for index, proof_kind in enumerate(sorted(receipt.proof_refs_json)):
        if proof_kind == "shadow_gate_ref":
            refs[proof_kind] = receipt.source_gate_evaluation_id
            continue
        persisted = await record_promotion_proof(
            session,
            scope_ref=scope_ref,
            proof_kind=proof_kind,
            artifact_ref=f"test:guard/{proof_kind}",
            artifact_digest="sha256:" + f"{index + 40:064x}",
            verifier_version="pytest-v1",
            verification_status="VERIFIED",
            verified_at=datetime(2026, 9, 4, 11, 0, 0, tzinfo=timezone.utc),
            apply=True,
        )
        refs[proof_kind] = persisted.proof_ref
    receipt.proof_refs_json = refs


@pytest.mark.asyncio
async def test_canary_requires_and_returns_the_exact_authorized_receipt() -> None:
    engine, sessions = await _database()
    try:
        async with sessions() as session:
            receipt = _shadow_receipt()
            await _register_receipt_proofs(session, receipt)
            session.add(receipt)
            await session.flush()

            authorization = await authorize_v2_runtime(
                session,
                settings=_settings("canary"),
            )

            assert authorization.mode == "canary"
            assert authorization.promotion_stage == "shadow_to_canary"
            assert authorization.receipt_evaluation_id == _digest("a")
            assert authorization.authorized_response_types == ("ABSTAIN",)
            assert authorization.canary_subjects == 1
            assert authorization.raw_payload_retained is False

            gate = await load_authorized_canary_gate(
                session,
                receipt_evaluation_id=_digest("a"),
            )
            assert gate.status == "CANARY_AUTHORIZED"
            assert gate.evaluation_id == _digest("b")
            assert gate.blocked_response_types == ("BUY_NOW", "WAIT")
            assert gate.blocker_codes == (
                "RESPONSE_TYPE_OFF:BUY_NOW",
                "RESPONSE_TYPE_OFF:WAIT",
            )
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_canary_fails_closed_for_absent_hold_or_drifted_receipt() -> None:
    engine, sessions = await _database()
    try:
        async with sessions() as session:
            with pytest.raises(V2PromotionGuardError, match="is absent"):
                await authorize_v2_runtime(session, settings=_settings("canary"))

            session.add(_shadow_receipt(status="CANARY_HOLD"))
            await session.flush()
            with pytest.raises(V2PromotionGuardError, match="not authorized"):
                await authorize_v2_runtime(session, settings=_settings("canary"))
            await session.rollback()

            session.add(
                _shadow_receipt(
                    authorized_response_types_json=["ABSTAIN", "WAIT"],
                    blocked_response_types_json=["WAIT", "BUY_NOW"],
                )
            )
            await session.flush()
            with pytest.raises(V2PromotionGuardError, match="partition"):
                await authorize_v2_runtime(session, settings=_settings("canary"))
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_public_requires_the_exact_authorized_canary_lineage() -> None:
    engine, sessions = await _database()
    try:
        async with sessions() as session:
            shadow = _shadow_receipt()
            public = _public_receipt()
            await _register_receipt_proofs(session, shadow)
            await _register_receipt_proofs(session, public)
            session.add_all([shadow, public])
            await session.flush()

            authorization = await authorize_v2_runtime(
                session,
                settings=_settings("public"),
            )

            assert authorization.mode == "public"
            assert authorization.promotion_stage == "canary_to_public"
            assert authorization.receipt_evaluation_id == _digest("c")
            assert authorization.authorized_response_types == ("ABSTAIN",)
            assert authorization.canary_subjects == 0
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_public_fails_closed_when_canary_lineage_is_missing() -> None:
    engine, sessions = await _database()
    try:
        async with sessions() as session:
            session.add(_public_receipt())
            await session.flush()

            with pytest.raises(V2PromotionGuardError, match="lineage is absent"):
                await authorize_v2_runtime(session, settings=_settings("public"))
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_public_fails_closed_when_lineage_reference_drifted() -> None:
    engine, sessions = await _database()
    try:
        async with sessions() as session:
            public = _public_receipt()
            public.proof_refs_json["shadow_gate_ref"] = _digest("f")
            session.add_all([_shadow_receipt(), public])
            await session.flush()

            with pytest.raises(V2PromotionGuardError, match="lineage drifted"):
                await authorize_v2_runtime(session, settings=_settings("public"))
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_public_cannot_expand_beyond_canary_authorized_response_types() -> None:
    engine, sessions = await _database()
    try:
        async with sessions() as session:
            shadow = _shadow_receipt()
            public = _public_receipt(
                authorized_response_types_json=["ABSTAIN", "WAIT"],
                blocked_response_types_json=["BUY_NOW"],
            )
            await _register_receipt_proofs(session, shadow)
            await _register_receipt_proofs(session, public)
            session.add_all([shadow, public])
            await session.flush()

            with pytest.raises(V2PromotionGuardError, match="exceed"):
                await authorize_v2_runtime(session, settings=_settings("public"))
    finally:
        await engine.dispose()


def test_runtime_authorization_contract_and_example_are_valid() -> None:
    schema = json.loads(
        (CONTRACT_ROOT / "runtime-authorization.schema.json").read_text()
    )
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    manifest = json.loads((CONTRACT_ROOT / "manifest.json").read_text())
    examples = manifest["runtime_authorization_examples"]
    assert examples == [
        "examples/runtime-authorization-canary.json",
        "examples/runtime-authorization-public.json",
    ]
    for relative_path in examples:
        validator.validate(json.loads((CONTRACT_ROOT / relative_path).read_text()))
