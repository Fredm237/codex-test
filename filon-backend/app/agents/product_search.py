"""Agent 2 — Recherche produit.

Interroge le catalogue réel de FILON (offres Awin ingérées, regroupées par EAN).
Il lisait auparavant un fichier de démonstration de quatre ordinateurs portables
chez des marchands sans partenariat. Ce repli est désormais interdit dans tous
les environnements : aucune base ou aucune correspondance produit une abstention.
"""

from __future__ import annotations

from app.agents.state import AdviseState
from app.services.catalog_source import search_products


async def run(state: AdviseState) -> AdviseState:
    criteria = state["criteria"]

    # Catalogue réel d'abord : c'est lui qui porte les vrais prix et les vrais
    # marchands partenaires.
    real = await search_products(
        state.get("query", ""),
        budget_max=criteria.budget_max,
        limit=5,
    )
    if real:
        state["candidates"] = real
        state.setdefault("trace", []).append(
            f"product_search: {len(real)} produits du catalogue FILON"
        )
        return state

    # Aucune base ou aucune correspondance réelle : abstention. Un environnement
    # de développement n'autorise pas l'API publique à retourner des produits,
    # marchands ou prix de démonstration comme s'ils avaient été observés.
    state["candidates"] = []
    state.setdefault("trace", []).append(
        "product_search: aucun produit correspondant chez nos partenaires"
    )
    return state
