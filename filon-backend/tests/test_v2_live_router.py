"""Raccordement public V2 : autorisation exacte, bloc atomique et repli V1."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.v2_chain import live_router
from app.v2_chain.canary import V2CanaryPayload
from app.v2_chain.promotion_guard import V2RuntimeAuthorization
from quality_lab.v2_canary import V2CanaryGateReport


SUBJECT = "sha256:" + "e" * 64
CAMPAIGN = "sha256:" + "f" * 64
RECEIPT = "sha256:" + "a" * 64
GATE_ID = "sha256:" + "b" * 64


class _Scope:
    def __init__(self, session) -> None:
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, *_exc) -> None:
        return None


def _settings(mode: str):
    return SimpleNamespace(
        v2_chain_mode=mode,
        v2_chain_campaign_id=CAMPAIGN,
        v2_canary_subject_digests_list=[SUBJECT] if mode == "canary" else [],
        v2_supported_verticals_list=["smartphones"],
        v2_supported_locales_list=["fr"],
        v2_supported_decision_types_list=["purchase_advice"],
        v2_max_data_age_seconds=300,
    )


def _authorization(mode: str) -> V2RuntimeAuthorization:
    return V2RuntimeAuthorization(
        schema_version="v2-runtime-authorization/v1",
        mode=mode,
        promotion_stage=(
            "shadow_to_canary" if mode == "canary" else "canary_to_public"
        ),
        receipt_evaluation_id=RECEIPT,
        gate_evaluation_id=GATE_ID,
        authorized_response_types=("ABSTAIN",),
        canary_subjects=1 if mode == "canary" else 0,
    )


def _gate() -> V2CanaryGateReport:
    return V2CanaryGateReport(
        schema_version="v2-shadow-to-canary-gate/v1",
        status="CANARY_AUTHORIZED",
        gates={},
        blocked_response_types=("BUY_NOW", "WAIT"),
        blocker_codes=("RESPONSE_TYPE_OFF:BUY_NOW", "RESPONSE_TYPE_OFF:WAIT"),
        evaluation_id=GATE_ID,
    )


def _payload() -> V2CanaryPayload:
    return V2CanaryPayload(
        response={"outcome": "ABSTAIN", "items": []},
        chain_complete=True,
        safety_state="ABSTAIN",
        provenance_complete=True,
        response_type="ABSTAIN",
    )


def _install_promoted_runtime(monkeypatch, *, mode: str):
    session = SimpleNamespace(commit=AsyncMock())
    monkeypatch.setattr(live_router, "get_settings", lambda: _settings(mode))
    monkeypatch.setattr(live_router.db, "session_scope", lambda: _Scope(session))
    monkeypatch.setattr(
        live_router,
        "authorize_v2_runtime",
        AsyncMock(return_value=_authorization(mode)),
    )
    monkeypatch.setattr(
        live_router,
        "load_authorized_canary_gate",
        AsyncMock(return_value=_gate()),
    )
    inspection = SimpleNamespace(
        data_age_seconds=15,
        dependencies_admissible=True,
    )
    inspector = AsyncMock(return_value=inspection)
    monkeypatch.setattr(live_router, "inspect_v2_online", inspector)
    reader = AsyncMock(return_value=_payload())
    recorder = AsyncMock()
    monkeypatch.setattr(live_router, "read_v2_online", reader)
    monkeypatch.setattr(live_router, "record_canary_read", recorder)
    return session, reader, recorder, inspector


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ("off", "shadow", "dark"))
async def test_non_promoted_modes_preserve_the_exact_core_block(
    monkeypatch,
    mode: str,
) -> None:
    core = {"real": True, "cards": [{"offer_id": 7}]}
    monkeypatch.setattr(live_router, "get_settings", lambda: _settings(mode))

    result = await live_router.route_promoted_response(
        core_response=core,
        core_latency_us=1_000,
        query="un smartphone",
        budget=500,
        country="be",
        locale="fr",
        surface="advise_stream",
        subject_digest=SUBJECT,
    )

    assert result.response is core
    assert result.source == "core_v1"
    assert result.reason_code == "reader_off"


@pytest.mark.asyncio
async def test_closed_canary_serves_only_the_authorized_abstention_and_records_it(
    monkeypatch,
) -> None:
    session, reader, recorder, inspector = _install_promoted_runtime(
        monkeypatch,
        mode="canary",
    )
    core = {"real": False, "offers": 0, "cards": []}

    result = await live_router.route_promoted_response(
        core_response=core,
        core_latency_us=8_000,
        query="un smartphone",
        budget=500,
        country="be",
        locale="fr",
        surface="advise_stream",
        subject_digest=SUBJECT,
    )

    assert result.source == "v2"
    assert result.reason_code == "v2_authorized"
    assert result.response == {
        "usage": "un smartphone",
        "offers": 0,
        "cards": [],
        "real": False,
        "currency": None,
        "country": "be",
    }
    reader.assert_awaited_once()
    inspector.assert_awaited_once()
    assert reader.await_args.kwargs["inspection"] is inspector.return_value
    recorder.assert_awaited_once()
    receipt = recorder.await_args.kwargs["receipt"]
    assert receipt.source == "v2"
    assert receipt.response_type == "ABSTAIN"
    assert receipt.core_latency_us == 8_000
    assert receipt.raw_query_retained is False
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_canary_abstention_never_erases_a_real_core_result(monkeypatch) -> None:
    session, reader, recorder, inspector = _install_promoted_runtime(
        monkeypatch,
        mode="canary",
    )
    core = {"real": True, "offers": 1, "cards": [{"offer_id": 7}]}

    result = await live_router.route_promoted_response(
        core_response=core,
        core_latency_us=2_000,
        query="un smartphone",
        budget=None,
        country="be",
        locale="fr",
        surface="advise_stream",
        subject_digest=SUBJECT,
    )

    assert result.response is core
    assert result.source == "core_v1"
    assert result.reason_code == "critical_unknown"
    inspector.assert_awaited_once()
    reader.assert_not_awaited()
    recorder.assert_awaited_once()
    assert recorder.await_args.kwargs["receipt"].source == "core_v1"
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_canary_subject_outside_the_closed_cohort_keeps_core(monkeypatch) -> None:
    session, reader, recorder, inspector = _install_promoted_runtime(
        monkeypatch,
        mode="canary",
    )
    core = {"real": True, "cards": []}

    result = await live_router.route_promoted_response(
        core_response=core,
        core_latency_us=4_000,
        query="un smartphone",
        budget=None,
        country="be",
        locale="fr",
        surface="advise_stream",
        subject_digest="sha256:" + "1" * 64,
    )

    assert result.response is core
    assert result.source == "core_v1"
    assert result.reason_code == "outside_closed_cohort"
    reader.assert_not_awaited()
    inspector.assert_not_awaited()
    recorder.assert_not_awaited()
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_canary_telemetry_failure_falls_back_to_the_whole_core_block(
    monkeypatch,
) -> None:
    _session, _reader, recorder, _inspector = _install_promoted_runtime(
        monkeypatch,
        mode="canary",
    )
    recorder.side_effect = RuntimeError("database write failed")
    core = {"real": True, "cards": [{"offer_id": 9}]}

    result = await live_router.route_promoted_response(
        core_response=core,
        core_latency_us=4_000,
        query="un smartphone",
        budget=None,
        country="be",
        locale="fr",
        surface="advise_stream",
        subject_digest=SUBJECT,
    )

    assert result.response is core
    assert result.source == "core_v1"
    assert result.reason_code == "runtime_hold"


@pytest.mark.asyncio
async def test_unadapted_actionable_response_can_never_cross_the_public_contract(
    monkeypatch,
) -> None:
    _session, reader, recorder, _inspector = _install_promoted_runtime(
        monkeypatch,
        mode="canary",
    )
    reader.return_value = V2CanaryPayload(
        response={"outcome": "BUY_NOW", "items": [{"offer": 7}]},
        chain_complete=True,
        safety_state="SAFE",
        provenance_complete=True,
        response_type="BUY_NOW",
    )
    core = {"real": False, "offers": 0, "cards": []}

    result = await live_router.route_promoted_response(
        core_response=core,
        core_latency_us=4_000,
        query="un smartphone",
        budget=None,
        country="be",
        locale="fr",
        surface="advise_stream",
        subject_digest=SUBJECT,
    )

    assert result.response is core
    assert result.source == "core_v1"
    assert result.reason_code == "v2_reader_error"
    receipt = recorder.await_args.kwargs["receipt"]
    assert receipt.response_type == "CORE"
    assert receipt.fallback_reason == "v2_reader_error"


@pytest.mark.asyncio
async def test_public_mode_uses_exact_authorization_without_canary_identity(
    monkeypatch,
) -> None:
    session, reader, recorder, _inspector = _install_promoted_runtime(
        monkeypatch,
        mode="public",
    )

    result = await live_router.route_promoted_response(
        core_response={
            "query": "un smartphone",
            "criteria": {},
            "recommendation": None,
            "alternatives": [],
            "trace": [],
        },
        core_latency_us=12_000,
        query="un smartphone",
        budget=None,
        country=None,
        locale="fr",
        surface="advise",
        subject_digest=None,
    )

    assert result.source == "v2"
    assert result.response["query"] == "un smartphone"
    assert result.response["recommendation"] is None
    assert result.response["alternatives"] == []
    reader.assert_awaited_once()
    recorder.assert_awaited_once()
    public_receipt = recorder.await_args.kwargs["receipt"]
    assert public_receipt.gate_evaluation_id == GATE_ID
    assert public_receipt.assignment_reason == "public_authorized"
    assert public_receipt.source == "v2"
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_public_abstention_never_erases_a_core_recommendation(monkeypatch) -> None:
    session, reader, recorder, inspector = _install_promoted_runtime(
        monkeypatch,
        mode="public",
    )
    core = {
        "query": "un smartphone",
        "criteria": {},
        "recommendation": {"product": "core-result"},
        "alternatives": [],
        "trace": [],
    }

    result = await live_router.route_promoted_response(
        core_response=core,
        core_latency_us=5_000,
        query="un smartphone",
        budget=None,
        country=None,
        locale="fr",
        surface="advise",
        subject_digest=None,
    )

    assert result.response is core
    assert result.source == "core_v1"
    assert result.reason_code == "critical_unknown"
    inspector.assert_awaited_once()
    reader.assert_not_awaited()
    recorder.assert_awaited_once()
    assert recorder.await_args.kwargs["receipt"].source == "core_v1"
    assert recorder.await_args.kwargs["receipt"].fallback_reason == "critical_unknown"
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_public_telemetry_failure_returns_the_whole_core_block(monkeypatch) -> None:
    _session, _reader, recorder, _inspector = _install_promoted_runtime(
        monkeypatch,
        mode="public",
    )
    recorder.side_effect = RuntimeError("database write failed")
    core = {
        "query": "un smartphone",
        "criteria": {},
        "recommendation": None,
        "alternatives": [],
        "trace": [],
    }

    result = await live_router.route_promoted_response(
        core_response=core,
        core_latency_us=5_000,
        query="un smartphone",
        budget=None,
        country=None,
        locale="fr",
        surface="advise",
        subject_digest=None,
    )

    assert result.response is core
    assert result.source == "core_v1"
    assert result.reason_code == "runtime_hold"


@pytest.mark.asyncio
async def test_missing_runtime_receipt_fails_closed_without_exposing_details(
    monkeypatch,
) -> None:
    _session, reader, recorder, _inspector = _install_promoted_runtime(
        monkeypatch,
        mode="canary",
    )
    live_router.authorize_v2_runtime.side_effect = RuntimeError("receipt absent")
    core = {"real": True, "cards": []}

    result = await live_router.route_promoted_response(
        core_response=core,
        core_latency_us=1,
        query="un smartphone",
        budget=None,
        country="be",
        locale="fr",
        surface="advise_stream",
        subject_digest=SUBJECT,
    )

    assert result.response is core
    assert result.reason_code == "runtime_hold"
    reader.assert_not_awaited()
    recorder.assert_not_awaited()
