"""Agent 2 — Recherche produit.

Interroge le catalogue réel de FILON (offres Awin ingérées, regroupées par EAN).
Il lisait auparavant un fichier de démonstration de quatre ordinateurs portables
chez des marchands sans partenariat : le copilote répondait à côté de sa propre
base. Le catalogue de démonstration ne sert plus que de secours hors production,
quand aucune base n'est configurée.
"""

from __future__ import annotations

from app.agents.state import AdviseState
from app.core.logging import get_logger
from app.data.catalog import all_products
from app.db import session as db
from app.services.catalog_source import search_products

log = get_logger("product_search")


def _score(product: dict, criteria) -> float:
    score = 0.0
    tags = set(product.get("tags", []))
    for u in criteria.usage:
        if u in tags:
            score += 1.0
    for m in criteria.must_have:
        if m in tags:
            score += 1.5
    if criteria.category and product.get("category") == criteria.category:
        score += 3.0
    for k in criteria.keywords:
        if k in tags:
            score += 0.3
    return score


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

    # Aucun résultat dans le catalogue réel.
    #
    # Le repli de démonstration ne doit JAMAIS servir en production. Il contient
    # des produits chez des marchands avec lesquels nous n'avons aucun accord —
    # recommander leurs marques revient à envoyer nos utilisateurs chez des
    # enseignes qui ne sont pas nos partenaires, et à afficher des prix que nous
    # n'avons jamais relevés. Constaté en ligne.
    #
    # Une réponse vide est un résultat honnête : l'étape suivante dira que nous
    # n'avons rien trouvé chez nos partenaires. C'est préférable à une
    # recommandation inventée.
    if db.is_enabled():
        state["candidates"] = []
        state.setdefault("trace", []).append(
            "product_search: aucun produit correspondant chez nos partenaires"
        )
        return state

    # Base absente : développement local uniquement. Jamais en production, où
    # DATABASE_URL est toujours défini.
    log.info("Aucune base configurée — jeu de démonstration (développement local)")
    products = all_products()

    if criteria.category:
        products = [p for p in products if p.get("category") == criteria.category]

    # Filtre budget : on garde ceux dont la meilleure offre tient dans le budget.
    if criteria.budget_max:
        products = [
            p
            for p in products
            if min(o["price"] for o in p["offers"]) <= criteria.budget_max * 1.05
        ]

    ranked = sorted(products, key=lambda p: _score(p, criteria), reverse=True)
    state["candidates"] = ranked[:5]
    state.setdefault("trace", []).append(
        f"product_search: {len(ranked)} produits (démonstration)"
    )
    return state
