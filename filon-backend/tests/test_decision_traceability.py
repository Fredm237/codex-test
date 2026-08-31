from __future__ import annotations

import asyncio
import gzip
import logging
import re
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from app.core.observability import (
    bind_request_id_context,
    current_request_id,
    decision_trace_event,
    outbound_trace_headers,
    request_id_context,
    traced_dependency,
)
from app.intelligence.contracts import CoreOfferSnapshot
from app.intelligence.general_decision import compose_general_plan
from app.intelligence.intent_resolution import resolve_intent_with_fallback
from app.llm.base import Message
from app.llm.providers import openai_compatible
from app.llm.providers.openai_compatible import OpenAICompatibleProvider
from app.services import awin_catalog, taxonomy


_TRACEPARENT = re.compile(r"^00-([0-9a-f]{32})-([0-9a-f]{16})-01$")


def test_en_tetes_sortants_utilisent_seulement_la_correlation_filon():
    assert outbound_trace_headers() == {}
    token = bind_request_id_context("customer-email-private")
    try:
        request_id = current_request_id()
        headers = outbound_trace_headers()
    finally:
        request_id_context.reset(token)

    assert request_id is not None
    assert request_id != "customer-email-private"
    assert headers["x-request-id"] == request_id
    match = _TRACEPARENT.fullmatch(headers["traceparent"])
    assert match is not None
    assert match.group(1) == request_id

    zero_token = bind_request_id_context("0" * 32)
    try:
        assert current_request_id() != "0" * 32
        assert "-00000000000000000000000000000000-" not in outbound_trace_headers()[
            "traceparent"
        ]
    finally:
        request_id_context.reset(zero_token)


def test_jalon_decisionnel_refuse_entrees_libres_et_comptes_invalides(caplog):
    token = bind_request_id_context("private-client-id")
    try:
        with caplog.at_level(logging.INFO, logger="filon.decision_trace"):
            assert decision_trace_event(
                "filtering",
                outcome="private-outcome",
                reason="private-reason",
                counts={
                    "input_count": 7,
                    "eligible_count": 2,
                    "unknown-field": "private-product-name",
                    "rejected_count": -4,
                },
                flags={"model_used": True, "private-flag": True},
            )
            assert not decision_trace_event("private-stage")
    finally:
        request_id_context.reset(token)

    serialized = repr(
        [(record.msg, record.args, record.__dict__) for record in caplog.records]
    )
    assert "event=filtering" in caplog.text
    assert "outcome=OTHER" in caplog.text
    assert "reason=OTHER" in caplog.text
    assert "input_count=7" in caplog.text
    assert "eligible_count=2" in caplog.text
    assert "model_used=true" in caplog.text
    for secret in (
        "private-client-id",
        "private-product-name",
        "private-stage",
        "private-flag",
    ):
        assert secret not in serialized
    assert "rejected_count" not in serialized


@pytest.mark.asyncio
async def test_span_dependance_propage_le_meme_span_et_masque_exception(caplog):
    token = bind_request_id_context("external-value")
    captured_headers: dict[str, str] = {}
    try:
        with caplog.at_level(logging.INFO, logger="filon.dependency.llm"):
            with pytest.raises(RuntimeError, match="signed-url-private-token"):
                async with traced_dependency("llm", "complete_json"):
                    captured_headers.update(outbound_trace_headers())
                    raise RuntimeError("signed-url-private-token")
    finally:
        request_id_context.reset(token)

    match = _TRACEPARENT.fullmatch(captured_headers["traceparent"])
    assert match is not None
    assert f"span_id={match.group(2)}" in caplog.text
    assert "dependency=llm operation=complete_json" in caplog.text
    assert "outcome=error error_type=RuntimeError" in caplog.text
    serialized = repr(
        [(record.msg, record.args, record.exc_info, record.__dict__) for record in caplog.records]
    )
    assert "signed-url-private-token" not in serialized
    assert "external-value" not in serialized


@pytest.mark.asyncio
async def test_contextes_concurrents_ne_se_melangent_pas(caplog):
    barrier = asyncio.Event()

    async def worker() -> tuple[str, str]:
        token = bind_request_id_context("same-external-value")
        try:
            request_id = current_request_id()
            assert request_id is not None
            async with traced_dependency("redis", "read"):
                barrier.set()
                await asyncio.sleep(0)
                traceparent = outbound_trace_headers()["traceparent"]
            return request_id, traceparent
        finally:
            request_id_context.reset(token)

    with caplog.at_level(logging.INFO, logger="filon.dependency.redis"):
        first, second = await asyncio.gather(worker(), worker())
        await barrier.wait()

    assert first[0] != second[0]
    assert first[0] in first[1]
    assert second[0] in second[1]
    assert request_id_context.get() is None


@pytest.mark.asyncio
async def test_span_autonome_restaure_un_contexte_vide():
    assert request_id_context.get() is None


@pytest.mark.asyncio
async def test_parcours_decisionnel_recommande_est_correle_et_sans_produit(caplog):
    token = bind_request_id_context("customer-private-value")
    try:
        with caplog.at_level(logging.INFO, logger="filon.decision_trace"):
            intent = await resolve_intent_with_fallback(
                "ordinateur portable sous 500 euros",
                "fr",
            )
            result = compose_general_plan(
                intent,
                [
                    CoreOfferSnapshot(
                        offer_id=918273645,
                        catalog_product_id=None,
                        name="ordinateur portable private-product-sentinel",
                        brand="private-brand-sentinel",
                        filon_category=taxonomy.INFORMATIQUE,
                        filon_subcategory="Ordinateurs portables",
                        offer_kind=taxonomy.PHYSICAL_PRODUCT,
                        price=400.0,
                        currency="EUR",
                        availability="in_stock",
                        image_url="https://private.example/image",
                        deep_link="https://private.example/item",
                        merchant_id=123456789,
                        merchant_name="private-merchant-sentinel",
                        merchant_region="BE",
                        observed_at=datetime.now(UTC),
                    )
                ],
            )
    finally:
        request_id_context.reset(token)

    assert result["decision"] == "recommend"
    messages = [record.getMessage() for record in caplog.records]
    events = [message.split("event=", 1)[1].split(" ", 1)[0] for message in messages]
    assert events == [
        "intent",
        "candidate_count",
        "filtering",
        "product_ranking",
        "offer_selection",
        "evidence",
        "decision",
    ]
    request_ids = {
        message.split("request_id=", 1)[1].split(" ", 1)[0]
        for message in messages
    }
    assert len(request_ids) == 1
    serialized = repr(
        [(record.msg, record.args, record.__dict__) for record in caplog.records]
    )
    for secret in (
        "customer-private-value",
        "private-product-sentinel",
        "private-brand-sentinel",
        "private-merchant-sentinel",
        "private.example",
        "918273645",
        "123456789",
    ):
        assert secret not in serialized


@pytest.mark.asyncio
async def test_fournisseur_llm_propage_traceparent_sans_mettre_secret_dans_url(
    monkeypatch,
):
    captured: dict[str, object] = {}

    class _Response:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {"choices": [{"message": {"content": "{}"}}]}

    class _Client:
        def __init__(self, **_kwargs) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args) -> None:
            return None

        async def post(self, url: str, *, json: object, headers: dict[str, str]):
            captured.update(url=url, json=json, headers=headers)
            return _Response()

    monkeypatch.setattr(openai_compatible.httpx, "AsyncClient", _Client)
    provider = OpenAICompatibleProvider(
        name="private-provider-name",
        base_url="https://llm.example/v1",
        api_key="private-api-key",
        model="private-model",
    )
    token = bind_request_id_context("client-private-id")
    try:
        request_id = current_request_id()
        assert await provider.complete_json([Message(role="user", content="private-prompt")]) == "{}"
    finally:
        request_id_context.reset(token)

    assert request_id is not None
    headers = captured["headers"]
    assert isinstance(headers, dict)
    assert headers["Authorization"] == "Bearer private-api-key"
    assert headers["x-request-id"] == request_id
    assert _TRACEPARENT.fullmatch(headers["traceparent"])
    assert "private-api-key" not in str(captured["url"])
    assert "private-prompt" not in str(captured["url"])


@pytest.mark.asyncio
async def test_tous_les_appels_awin_portent_la_correlation_sans_loguer_les_cles(
    monkeypatch,
    caplog,
):
    calls: list[dict[str, object]] = []
    settings = SimpleNamespace(
        awin_api_token="private-awin-token",
        awin_publisher_id="private-publisher-id",
        awin_api_base="https://publisher.example",
        awin_feed_api_key="private-feed-key",
        awin_feed_base="https://feeds.example",
        awin_max_download_bytes=1024 * 1024,
        awin_max_decompressed_bytes=1024 * 1024,
    )

    class _Response:
        def __init__(self, url: str) -> None:
            self._url = url

        def raise_for_status(self) -> None:
            return None

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args) -> None:
            return None

        def json(self) -> list[dict[str, object]]:
            return []

        @property
        def text(self) -> str:
            return "Feed ID,Advertiser ID,Advertiser Name\nfeed-1,42,Private Merchant\n"

        async def aiter_bytes(self):
            yield gzip.compress(
                b"aw_product_id,product_name\nproduct-1,Private Product\n"
            )

    class _Client:
        def __init__(self, **_kwargs) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args) -> None:
            return None

        async def get(
            self,
            url: str,
            *,
            headers: dict[str, str],
            params: dict[str, str] | None = None,
        ) -> _Response:
            calls.append({"url": url, "headers": dict(headers), "params": params})
            return _Response(url)

        def stream(
            self,
            method: str,
            url: str,
            *,
            headers: dict[str, str],
        ) -> _Response:
            calls.append(
                {
                    "method": method,
                    "url": url,
                    "headers": dict(headers),
                    "params": None,
                }
            )
            return _Response(url)

    monkeypatch.setattr(awin_catalog, "get_settings", lambda: settings)
    monkeypatch.setattr(awin_catalog.httpx, "AsyncClient", _Client)
    token = bind_request_id_context("external-private-id")
    try:
        request_id = current_request_id()
        with caplog.at_level(logging.INFO, logger="filon.dependency.awin"):
            assert await awin_catalog.fetch_joined_programmes() == []
            assert len(await awin_catalog.list_feeds()) == 1
            rows = await awin_catalog._download_feed_rows(["feed-1"])
    finally:
        request_id_context.reset(token)

    assert request_id is not None
    assert rows[0]["aw_product_id"] == "product-1"
    assert len(calls) == 3
    traceparents: set[str] = set()
    for call in calls:
        headers = call["headers"]
        assert isinstance(headers, dict)
        assert headers["x-request-id"] == request_id
        traceparent = headers["traceparent"]
        assert _TRACEPARENT.fullmatch(traceparent)
        assert request_id in traceparent
        traceparents.add(traceparent)
    assert len(traceparents) == 3
    assert "operation=programmes" in caplog.text
    assert "operation=feed_list" in caplog.text
    assert "operation=feed_download" in caplog.text
    serialized = repr(
        [(record.msg, record.args, record.__dict__) for record in caplog.records]
    )
    for secret in (
        "private-awin-token",
        "private-feed-key",
        "private-publisher-id",
        "external-private-id",
        "Private Merchant",
        "Private Product",
    ):
        assert secret not in serialized
    async with traced_dependency("postgres", "read"):
        assert current_request_id() is not None
        assert outbound_trace_headers()
    assert request_id_context.get() is None
