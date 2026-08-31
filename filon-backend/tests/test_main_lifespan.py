import asyncio

import pytest
from fastapi import FastAPI

from app import main


@pytest.mark.asyncio
async def test_lifespan_does_not_wait_for_schema_initialization(monkeypatch):
    started = asyncio.Event()
    release = asyncio.Event()

    async def slow_schema():
        started.set()
        await release.wait()

    session_module = __import__("app.db.session", fromlist=["session"])
    monkeypatch.setattr(session_module, "is_enabled", lambda: True)
    monkeypatch.setattr(main, "_prepare_schema", slow_schema)

    async with main.lifespan(FastAPI()):
        await asyncio.wait_for(started.wait(), timeout=0.2)
        assert not release.is_set()

    release.set()


@pytest.mark.asyncio
async def test_lifespan_never_executes_the_catalog_scheduler(monkeypatch):
    from app.ingest import scheduler

    called = False

    async def forbidden_scheduler() -> str:
        nonlocal called
        called = True
        raise AssertionError("the web process must not run the scheduler")

    session_module = __import__("app.db.session", fromlist=["session"])
    monkeypatch.setattr(session_module, "is_enabled", lambda: False)
    monkeypatch.setattr(scheduler, "run_once", forbidden_scheduler)

    async with main.lifespan(FastAPI()):
        await asyncio.sleep(0)

    assert called is False


@pytest.mark.asyncio
async def test_lifespan_configures_and_closes_trace_export(monkeypatch):
    configured = []
    closed = []
    session_module = __import__("app.db.session", fromlist=["session"])
    monkeypatch.setattr(session_module, "is_enabled", lambda: False)
    monkeypatch.setattr(
        main,
        "configure_trace_export",
        lambda settings: configured.append(settings.env) or True,
    )
    monkeypatch.setattr(
        main,
        "shutdown_trace_export",
        lambda: closed.append(True),
    )

    async with main.lifespan(FastAPI()):
        assert configured == ["test"]

    assert closed == [True]
