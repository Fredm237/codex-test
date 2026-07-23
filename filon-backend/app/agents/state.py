"""État partagé qui circule entre les agents de l'orchestrateur."""

from __future__ import annotations

from typing import Any, TypedDict

from app.schemas.advise import Criteria


class AdviseState(TypedDict, total=False):
    # Entrée
    query: str
    budget: float | None
    locale: str

    # Produit de chaque agent
    criteria: Criteria
    candidates: list[dict[str, Any]]          # produits filtrés (bruts catalogue)
    enriched: dict[str, dict[str, Any]]        # product_id -> {offers, cashback, promo, history, reviews}
    analyses: list[dict[str, Any]]             # ProductAnalysis (dict) triés
    recommendation: dict[str, Any] | None

    # Observabilité
    trace: list[str]
