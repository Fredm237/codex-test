"""Endpoints isolés de la FILON Intelligence Layer.

Le routeur ne remplace aucun endpoint catalogue. Son premier contrat est l’état
explicite des modules : le frontend peut masquer une expérience expérimentale
sans interroger ou fragiliser le Core.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(tags=["intelligence"])


def intelligence_capabilities() -> dict[str, bool]:
    """État évalué à la requête pour respecter les flags d’environnement."""
    settings = get_settings()
    intelligence = bool(settings.filon_intelligence_enabled)
    fashion = intelligence and bool(settings.fashion_expert_enabled)
    outfit = fashion and bool(settings.outfit_studio_enabled)
    return {
        "intelligence": intelligence,
        "fashion_expert": fashion,
        "outfit_studio": outfit,
    }


@router.get("/intelligence/status")
async def intelligence_status() -> dict:
    """Expose uniquement l’état des modules, jamais les données privées ou Core."""
    modules = intelligence_capabilities()
    return {
        "enabled": modules["intelligence"],
        "modules": modules,
        "version": "v1",
    }
