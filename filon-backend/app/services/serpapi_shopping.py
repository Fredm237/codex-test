"""Produits réels via Google Shopping (SerpApi).

Renvoie de vrais produits — nom, prix du jour, photo, marchand, lien cliquable —
que le LLM classera et argumentera ensuite. Sans clé SERPAPI_API_KEY, renvoie une
liste vide et le système retombe sur le mode « LLM estimé ».
"""

from __future__ import annotations

from typing import Any

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger

log = get_logger("serpapi")


def _num(v: Any) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


async def search_products(
    query: str, budget: float | None, *, limit: int = 20
) -> list[dict[str, Any]]:
    """Recherche Google Shopping. Retourne une liste de produits normalisés."""
    s = get_settings()
    if not s.serpapi_api_key:
        return []

    params = {
        "engine": "google_shopping",
        "q": query,
        "api_key": s.serpapi_api_key,
        "gl": s.serpapi_gl,
        "hl": s.serpapi_hl,
        "num": str(limit),
    }
    try:
        async with httpx.AsyncClient(timeout=s.llm_timeout_seconds) as client:
            resp = await client.get(s.serpapi_base_url, params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:  # pragma: no cover - dépend du réseau
        log.warning("SerpApi indisponible (%s) → repli", exc)
        return []

    results = data.get("shopping_results") or []
    products: list[dict[str, Any]] = []
    for r in results:
        price = _num(r.get("extracted_price"))
        if price is None:
            continue
        title = r.get("title")
        if not title:
            continue
        products.append(
            {
                "name": str(title),
                "price": int(round(price)),
                "merchant": str(r.get("source") or "marchand"),
                "image": r.get("thumbnail") or None,
                "link": r.get("product_link") or r.get("link") or None,
                "delivery": str(r.get("delivery") or "").strip() or None,
                "rating": _num(r.get("rating")),
                "reviews": r.get("reviews"),
            }
        )

    # Filtre budget avec petite marge (le classement final revient au LLM).
    if budget:
        within = [p for p in products if p["price"] <= budget * 1.1]
        products = within or products

    log.info("SerpApi : %d produits pour '%s'", len(products), query)
    return products[:limit]
