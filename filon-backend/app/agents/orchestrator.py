"""Orchestrateur du système d'agents.

Coordonne les agents spécialisés dans l'ordre :

  comprehension → product_search → [price_compare, cashback, promo,
  price_history, reviews] → decision

Utilise LangGraph si disponible (StateGraph). Sinon, retombe sur un runner
séquentiel équivalent, pour rester exécutable sans dépendance lourde.
"""

from __future__ import annotations

from app.agents import (
    cashback,
    comprehension,
    decision,
    price_compare,
    price_history,
    product_search,
    promo,
    reviews,
)
from app.agents.state import AdviseState
from app.core.logging import get_logger
from app.schemas.advise import (
    AdviseRequest,
    AdviseResponse,
    Criteria,
    ProductAnalysis,
    Recommendation,
)

log = get_logger("orchestrator")

# Ordre d'exécution. Les cinq agents d'enrichissement sont indépendants entre
# eux et pourraient tourner en parallèle ; on les enchaîne pour la lisibilité.
_PIPELINE = [
    comprehension.run,
    product_search.run,
    price_compare.run,
    cashback.run,
    promo.run,
    price_history.run,
    reviews.run,
    decision.run,
]


async def _run_sequential(state: AdviseState) -> AdviseState:
    for step in _PIPELINE:
        state = await step(state)
    return state


def _build_graph():
    """Construit un StateGraph LangGraph si la lib est installée."""
    try:
        from langgraph.graph import END, START, StateGraph
    except Exception:  # pragma: no cover - dépend de l'environnement
        return None

    g = StateGraph(AdviseState)
    g.add_node("comprehension", comprehension.run)
    g.add_node("product_search", product_search.run)
    g.add_node("price_compare", price_compare.run)
    g.add_node("cashback", cashback.run)
    g.add_node("promo", promo.run)
    g.add_node("price_history", price_history.run)
    g.add_node("reviews", reviews.run)
    g.add_node("decision", decision.run)

    g.add_edge(START, "comprehension")
    g.add_edge("comprehension", "product_search")
    g.add_edge("product_search", "price_compare")
    g.add_edge("price_compare", "cashback")
    g.add_edge("cashback", "promo")
    g.add_edge("promo", "price_history")
    g.add_edge("price_history", "reviews")
    g.add_edge("reviews", "decision")
    g.add_edge("decision", END)
    return g.compile()


_GRAPH = _build_graph()


async def advise(request: AdviseRequest) -> AdviseResponse:
    state: AdviseState = {
        "query": request.query,
        "budget": request.budget,
        "locale": request.locale,
        "trace": [],
    }

    if _GRAPH is not None:
        result: AdviseState = await _GRAPH.ainvoke(state)
    else:
        log.info("LangGraph absent → runner séquentiel")
        result = await _run_sequential(state)

    criteria = result.get("criteria") or Criteria()
    reco = None
    if result.get("recommendation"):
        r = result["recommendation"]
        reco = Recommendation(
            product=ProductAnalysis(**r["product"]),
            verdict=r["verdict"],
            headline=r["headline"],
            reasons=r["reasons"],
        )
    alternatives = [
        ProductAnalysis(**a) for a in result.get("analyses", [])[1:4]
    ]

    return AdviseResponse(
        query=request.query,
        criteria=criteria,
        recommendation=reco,
        alternatives=alternatives,
        trace=result.get("trace", []),
    )
