"""Régression : une offre sans note ne doit pas faire planter l'agent décision.

Constaté en production le 04/08/2026 sur `POST /api/advise` (HTTP 500) :

    File "app/agents/decision.py", line 42, in _rank_key
        return (a["real_price"], -rating)
    TypeError: bad operand type for unary -: 'NoneType'

Les flux marchands Awin ne fournissent aucune note : `catalog_source._shape()`
pose explicitement `rating: None`. Or `dict.get("rating", 0.0)` ne substitue la
valeur par défaut que si la **clé est absente**, pas si elle vaut `None`. Le
`None` arrivait donc intact devant l'opérateur unaire `-`.
"""

from __future__ import annotations

import pytest

from app.agents import decision, reviews
from app.agents.decision import _rank_key


def _analyse(real_price: float, rating) -> dict:
    """Analyse minimale telle que produite par _build_analysis."""
    return {
        "product_id": f"p-{real_price}-{rating}",
        "name": "article de test",
        "real_price": real_price,
        "reviews": None if rating is None else {"rating": rating, "count": 0},
    }


# La clé de tri commence désormais par la pertinence, négative pour que le
# score le plus élevé sorte en tête. Les cas ci-dessous portent sur la
# tolérance au `rating` absent, qui reste entière : c'est la forme du tuple qui
# a changé, pas le comportement qu'ils protègent.


def test_rank_key_tolere_rating_none_explicite():
    """Le cas exact de la panne : la clé existe et vaut None."""
    a = {"real_price": 10.0, "reviews": {"rating": None, "count": 0}}
    assert _rank_key(a) == (-0.0, 10.0, 0.0)


def test_rank_key_tolere_reviews_absent():
    assert _rank_key({"real_price": 10.0}) == (-0.0, 10.0, 0.0)


def test_rank_key_tolere_reviews_none():
    assert _rank_key({"real_price": 10.0, "reviews": None}) == (-0.0, 10.0, 0.0)


def test_rank_key_conserve_la_note_quand_elle_existe():
    a = {"real_price": 10.0, "reviews": {"rating": 4.5, "count": 12}}
    assert _rank_key(a) == (-0.0, 10.0, -4.5)


def test_rank_key_place_la_pertinence_avant_le_prix():
    """Un article cher mais pertinent passe devant un article hors sujet à 0,01 €.

    C'est la correction du 19/08/2026 : l'assistant répondait « Carte Cadeau
    Crypto Voucher » à qui demandait un casque, parce que le tri portait
    d'abord sur le prix.
    """
    hors_sujet = {"real_price": 0.01, "relevance": 0.1, "reviews": None}
    pertinent = {"real_price": 129.0, "relevance": 0.9, "reviews": None}
    assert sorted([hors_sujet, pertinent], key=_rank_key)[0] is pertinent


def test_tri_mixte_ne_leve_pas_et_ordonne_par_prix():
    """Un lot mêlant notes présentes et absentes doit se trier sans erreur."""
    analyses = [
        _analyse(30.0, None),
        _analyse(10.0, 4.5),
        _analyse(20.0, None),
        _analyse(10.0, None),
    ]
    analyses.sort(key=_rank_key)
    prix = [a["real_price"] for a in analyses]
    assert prix == [10.0, 10.0, 20.0, 30.0]
    # À prix égal, la note la plus élevée passe devant l'article sans note.
    assert analyses[0]["reviews"] == {"rating": 4.5, "count": 0}


@pytest.mark.asyncio
async def test_agent_decision_complet_avec_offres_sans_note():
    """L'agent décision doit produire une recommandation malgré l'absence de notes."""
    state = {
        "candidates": [
            {"product_id": "a", "name": "Article A", "rating": None},
            {"product_id": "b", "name": "Article B", "rating": None},
        ],
        "enriched": {
            "a": {
                "best_offer": {"price": 49.9, "delivery_cost": 0.0},
                "reviews": {"rating": None, "count": 0},
            },
            "b": {
                "best_offer": {"price": 39.9, "delivery_cost": 0.0},
                "reviews": {"rating": None, "count": 0},
            },
        },
    }
    out = await decision.run(state)
    assert out["recommendation"] is not None
    # Le moins cher gagne.
    assert out["recommendation"]["product"]["product_id"] == "b"


@pytest.mark.asyncio
async def test_agent_reviews_normalise_les_champs_nuls():
    """L'agent avis ne doit jamais propager de None vers le schéma ReviewSummary."""
    state = {
        "candidates": [
            {
                "product_id": "a",
                "name": "Article Awin",
                "rating": None,
                "reviews_count": None,
                "pros": None,
                "cons": None,
            }
        ],
        "enriched": {"a": {}},
    }
    out = await reviews.run(state)
    r = out["enriched"]["a"]["reviews"]
    assert r["rating"] == 0.0
    assert r["count"] == 0
    assert r["pros"] == []
    assert r["cons"] == []
