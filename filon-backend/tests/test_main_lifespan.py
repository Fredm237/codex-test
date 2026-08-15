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

    monkeypatch.setattr(main.db if hasattr(main, "db") else __import__("app.db.session", fromlist=["session"]), "is_enabled", lambda: True)
    monkeypatch.setattr(main, "_prepare_schema", slow_schema)

    from app.ingest import scheduler

    monkeypatch.setattr(scheduler, "maybe_start", lambda: None)

    async with main.lifespan(FastAPI()):
        await asyncio.wait_for(started.wait(), timeout=0.2)
        assert not release.is_set()

    release.set()
