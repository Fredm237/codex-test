"""Endpoint de santé + état des dépendances optionnelles."""

from __future__ import annotations

from fastapi import APIRouter

from app import __version__
from app.core.config import get_settings
from app.db import session as db
from app.services.cache import get_cache
from app.services.vectorstore import get_vectorstore

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    s = get_settings()
    return {
        "status": "ok",
        "app": s.app_name,
        "version": __version__,
        "env": s.env,
        "dependencies": {
            "database": db.is_enabled(),
            "redis": get_cache().enabled,
            "qdrant": get_vectorstore().enabled,
        },
        "llm": {
            "default": s.llm_provider_default,
            "reasoning": s.llm_provider_reasoning,
            "long": s.llm_provider_long,
        },
    }
