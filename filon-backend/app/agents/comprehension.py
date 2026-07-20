"""Agent 1 — Compréhension.

Transforme la demande en langage naturel en critères structurés, via le LLM
(tâche "default"). Robuste : si la sortie n'est pas un JSON exploitable, on
retombe sur des critères minimaux.
"""

from __future__ import annotations

import json

from app.agents.state import AdviseState
from app.llm.router import Message, get_router
from app.schemas.advise import Criteria

_SYSTEM = (
    "Tu es l'agent Compréhension de FILON. À partir du besoin d'achat de "
    "l'utilisateur, renvoie UNIQUEMENT un objet JSON avec les clés : "
    "category, budget_max, usage (liste), must_have (liste), priorities "
    "(liste), keywords (liste). Pas de texte autour."
)


async def run(state: AdviseState) -> AdviseState:
    router = get_router()
    llm = router.for_task("default")
    prompt = state["query"]
    if state.get("budget"):
        prompt += f"\nBudget maximum : {state['budget']} €"

    raw = await llm.complete_json(
        [Message("system", _SYSTEM), Message("user", prompt)]
    )
    try:
        data = json.loads(raw)
        criteria = Criteria(**data)
    except (json.JSONDecodeError, TypeError, ValueError):
        criteria = Criteria(keywords=state["query"].lower().split()[:8])

    # Le budget explicite de la requête prime sur l'inférence.
    if state.get("budget"):
        criteria.budget_max = state["budget"]

    state["criteria"] = criteria
    state.setdefault("trace", []).append(
        f"comprehension: category={criteria.category} budget_max={criteria.budget_max}"
    )
    return state
