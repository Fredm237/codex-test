"""L'agent ne recommande que des marchands partenaires.

Constaté en ligne : l'assistant conseillait des marques et des enseignes avec
lesquelles FILON n'a aucun accord, à des prix jamais relevés. La cause était un
jeu de démonstration servant de repli quand le catalogue réel ne renvoyait
rien — c'est-à-dire souvent.

Recommander un marchand non partenaire n'est pas un défaut d'affichage : c'est
envoyer un utilisateur chez quelqu'un que nous ne connaissons pas, en affirmant
un prix que nous n'avons pas mesuré.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.agents import product_search
from app.agents.state import AdviseState


class _Criteria:
    usage: list[str] = []
    must_have: list[str] = []
    keywords: list[str] = []
    category = None
    budget_max = None


def _state(query: str = "ordinateur portable") -> AdviseState:
    return {"query": query, "criteria": _Criteria()}  # type: ignore[typeddict-item]


@pytest.mark.anyio
async def test_sans_resultat_reel_on_ne_propose_rien(monkeypatch):
    """Une réponse vide est honnête ; une recommandation inventée ne l'est pas."""
    async def _rien(*a, **kw):
        return []

    monkeypatch.setattr(product_search, "search_products", _rien)
    with patch.object(product_search.db, "is_enabled", return_value=True):
        out = await product_search.run(_state())

    assert out["candidates"] == []
    assert any("partenaires" in line for line in out["trace"])


@pytest.mark.anyio
async def test_le_catalogue_reel_est_toujours_prefere(monkeypatch):
    reel = [{"name": "Chemise Carhartt", "offers": [{"price": 62.9}]}]

    async def _reel(*a, **kw):
        return reel

    monkeypatch.setattr(product_search, "search_products", _reel)
    with patch.object(product_search.db, "is_enabled", return_value=True):
        out = await product_search.run(_state())

    assert out["candidates"] == reel


@pytest.mark.anyio
async def test_la_demonstration_ne_sert_que_sans_base(monkeypatch):
    """Le jeu de démonstration reste utile en développement local — et
    seulement là, où DATABASE_URL n'est pas défini."""
    async def _rien(*a, **kw):
        return []

    monkeypatch.setattr(product_search, "search_products", _rien)
    with patch.object(product_search.db, "is_enabled", return_value=False):
        out = await product_search.run(_state())

    assert any("démonstration" in line for line in out["trace"])
