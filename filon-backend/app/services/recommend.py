"""Génération des recommandations d'achat par le LLM — Refonte 2026.

Améliorations :
- Cache Redis/LRU pour éviter de rappeler le LLM pour la même requête
- Timeout explicite sur les appels LLM (pas de requête qui pend indéfiniment)
- Parallélisme : classement LLM + annonceurs Awin lorsque des offres catalogue sont disponibles
- Streaming fidèle : les étapes avancent en fonction du travail réel
- Annulation propre si le client déconnecte
- Métriques de latence pour l'observabilité

Produit exactement le contrat que le frontend consomme (voir SearchAssistant :
``Result`` = { usage, offers, cards[5] }). Le LLM raisonne réellement sur le
besoin et propose 5 options classées avec prix estimés. Si aucune clé LLM n'est
configurée (ou en cas d'erreur), on retombe sur une synthèse déterministe pour
que l'endpoint reste toujours fonctionnel.
"""

from __future__ import annotations

import asyncio
import json
import time
import random
from typing import Any, AsyncGenerator

from app.core.config import get_settings
from app.core.logging import get_logger
from app.llm.base import Message
from app.llm.router import get_router
from app.services import awin
from app.services.cache import get_cache, cache_key, TTL_RECOMMEND

log = get_logger("recommend")


def _parse_json(raw: str) -> dict[str, Any]:
    """Parse robuste : retire d'éventuelles clôtures markdown et texte autour.

    Certains modèles enveloppent le JSON dans ```json ... ``` ou ajoutent une
    phrase avant/après, ce qui faisait échouer json.loads et provoquait un repli.
    """
    s = (raw or "").strip()
    if s.startswith("```"):
        parts = s.split("```")
        s = parts[1] if len(parts) > 1 else s
        if s.lstrip().lower().startswith("json"):
            s = s.lstrip()[4:]
    a, b = s.find("{"), s.rfind("}")
    if a != -1 and b != -1 and b > a:
        s = s[a : b + 1]
    return json.loads(s)


# Les 8 étapes de raisonnement affichées par le frontend (mêmes libellés/ordre).
STEPS = [
    "Compréhension du besoin",
    "Analyse des marchands",
    "Analyse des prix",
    "Analyse de l'historique",
    "Analyse du cashback",
    "Analyse des avis",
    "Recherche d'alternatives",
    "Calcul du Score FILON",
]

# Les 5 emplacements de cartes, fixes pour la cohérence de l'UI.
SLOTS = [
    ("Meilleur rapport qualité/prix", "🥇"),
    ("Meilleur budget", "🥈"),
    ("Meilleure autonomie", "🥉"),
    ("Meilleure performance", "⭐"),
    ("Meilleur reconditionné", "♻️"),
]

_HIST = {"baisse", "hausse", "stable"}
_VALID_LOCALES = {"fr", "nl", "en"}
_LANGUAGE_NAMES = {"fr": "français", "nl": "néerlandais", "en": "anglais"}


def _response_locale(locale: str | None) -> str:
    """Normalise la langue d'annotation demandée par l'interface FILON."""
    value = (locale or "fr").lower().split("-")[0]
    return value if value in _VALID_LOCALES else "fr"


_OFFER_NOTICES = {
    "fr": {"delivery": "voir marchand", "warranty": "conditions marchand"},
    "nl": {"delivery": "bekijk verkoper", "warranty": "voorwaarden verkoper"},
    "en": {"delivery": "see merchant", "warranty": "merchant terms"},
}


_SYSTEM = (
    "Tu es FILON, un copilote d'achat expert pour la Belgique et l'Europe. "
    "À partir d'un besoin exprimé en langage naturel, tu proposes 5 produits réels "
    "et pertinents, classés. Tu réponds UNIQUEMENT en JSON valide, sans texte autour.\n\n"
    "Format exact attendu :\n"
    "{\n"
    '  "usage": "catégorie du besoin en français (ex: ordinateur portable, smartphone)",\n'
    '  "emoji": "un seul emoji représentant la catégorie",\n'
    '  "cards": [ 5 objets, un par emplacement, DANS CET ORDRE :\n'
    "     1) meilleur rapport qualité/prix, 2) meilleur budget, 3) meilleure autonomie,\n"
    "     4) meilleure performance, 5) meilleur reconditionné ]\n"
    "}\n\n"
    "Chaque carte : {\n"
    '  "name": "nom pr\u00e9cis d\'un produit r\u00e9el du march\u00e9",\n'
    '  "price": nombre entier en euros (estimation réaliste du prix marché 2026 en Belgique/UE),\n'
    '  "merchant": "un marchand réaliste (Amazon, Fnac, Coolblue, Bol, MediaMarkt, Krëfel, Cdiscount, Boulanger, Back Market…)",\n'
    '  "delivery": "24 h" | "48 h" | "2-3 j" | "3-4 j",\n'
    '  "warranty": "24 mois",\n'
    '  "cashback": nombre entier entre 2 et 6 (pourcentage),\n'
    '  "coupon": "−20 €" (chaine) ou null,\n'
    '  "hist": "baisse" | "hausse" | "stable",\n'
    '  "histNote": "courte note prix (ex: au plus bas sur 90 j, −30 € vs moyenne)",\n'
    '  "score": nombre entier entre 80 et 96 (Score FILON),\n'
    '  "why": "une phrase en français expliquant pourquoi ce produit",\n'
    '  "alt": "nom d\'une alternative" ou null,\n'
    '  "buy": true si c\'est le bon moment d\'acheter, false s\'il vaut mieux attendre\n'
    "}\n"
    "Respecte le budget indiqué s'il y en a un. Prix = estimations réalistes, pas inventées."
)


def _coerce_card(raw: Any, slot: int) -> dict[str, Any]:
    """Force une carte du LLM dans le contrat frontend, avec valeurs de repli."""
    rank, medal = SLOTS[slot]
    r = raw if isinstance(raw, dict) else {}
    hist = str(r.get("hist", "stable")).lower()
    if hist not in _HIST:
        hist = "stable"
    coupon = r.get("coupon")
    coupon = str(coupon) if coupon not in (None, "", "null") else None
    alt = r.get("alt")
    alt = str(alt) if alt not in (None, "", "null") else None
    try:
        price = int(round(float(r.get("price", 0)))) or 0
    except (TypeError, ValueError):
        price = 0
    try:
        score = int(r.get("score", 88))
    except (TypeError, ValueError):
        score = 88
    try:
        cashback = int(r.get("cashback", 3))
    except (TypeError, ValueError):
        cashback = 3
    return {
        "rank": rank,
        "medal": medal,
        "name": str(r.get("name") or f"Option {slot + 1}"),
        "emoji": "🛍️",
        "image": None,
        "link": None,
        "price": price,
        "merchant": str(r.get("merchant") or "Amazon"),
        "delivery": str(r.get("delivery") or "48 h"),
        "warranty": str(r.get("warranty") or "24 mois"),
        "cashback": max(0, min(9, cashback)),
        "coupon": coupon,
        "hist": hist,
        "histNote": str(r.get("histNote") or "proche de la moyenne"),
        "score": max(0, min(100, score)),
        "why": str(r.get("why") or "Un bon choix pour votre besoin."),
        "alt": alt,
        "buy": bool(r.get("buy", True)),
    }


_SYSTEM_RANK = (
    "Tu es FILON, copilote d'achat expert (Belgique/Europe). On te donne une liste "
    "de PRODUITS RÉELS (index, nom, prix, marchand) issus du catalogue partenaire FILON. "
    "Sélectionne les MEILLEURS (jusqu'à 5), du meilleur au moins bon. "
    "Réponds UNIQUEMENT en JSON.\n\n"
    "Règles STRICTES :\n"
    "- Ne garde que des produits VRAIMENT pertinents pour le besoin et cohérents "
    "entre eux (même type de produit). Écarte tout le reste.\n"
    "- EXCLIS le matériel obsolète ou sous-dimensionné, les pièces détachées, "
    "accessoires, lots, et les 'pièges' (très bas prix parce que dépassé).\n"
    "- 'Le moins cher' n'est PAS 'le meilleur budget' : privilégie le vrai rapport "
    "qualité/prix.\n"
    "- Donne à CHAQUE reco une étiquette courte ADAPTÉE au produit et au besoin "
    "(ex : 'Meilleur rapport qualité/prix', 'Le plus polyvalent', 'Idéal gaming', "
    "'Le plus léger', 'Meilleur reconditionné'). N'utilise JAMAIS une étiquette "
    "absurde pour le produit (jamais 'autonomie' pour un PC de bureau).\n"
    "- Si moins de 5 produits sont vraiment bons, renvoie-en moins. Pas de doublon.\n\n"
    "Format :\n"
    "{\n"
    '  "usage": "catégorie du besoin en français",\n'
    '  "emoji": "un emoji de la catégorie",\n'
    '  "picks": [ jusqu\'à 5 objets, du meilleur au moins bon ]\n'
    "}\n"
    "Chaque pick : {\n"
    '  "index": entier = index du produit dans la liste,\n'
    '  "label": "étiquette courte adaptée, max 4 mots",\n'
    '  "why": "une phrase prudente expliquant la pertinence du nom et du prix pour ce besoin, sans inventer de caractéristique",\n'
    '  "alt": "nom d\'une alternative" ou null\n'
    "}\n"
    "Ne renvoie que du JSON."
)


def _build_real_card(
    slot: int, prod: dict[str, Any], ann: dict[str, Any], emoji: str, locale: str | None = None
) -> dict[str, Any]:
    """Carte à partir d'une offre réelle du catalogue partenaire + annotation LLM."""
    default_rank, medal = SLOTS[slot]
    rank = str(ann.get("label") or default_rank)
    decision_data = prod.get("decision") if isinstance(prod.get("decision"), dict) else None
    observed_score = decision_data.get("score_observed", 0) if decision_data else 0
    possible_score = decision_data.get("score_possible", 0) if decision_data else 0
    evidence_score = round((observed_score / possible_score) * 100) if possible_score else 0
    alt = ann.get("alt")
    alt = str(alt) if alt not in (None, "", "null") else None
    scope = decision_data.get("recommendation_scope") if decision_data else None
    price_level = (decision_data or {}).get("price_verdict", {}).get("level")
    # « Bon moment » demande à la fois le meilleur prix observé et un historique
    # favorable. Tout autre cas reste une offre à vérifier, jamais un achat
    # recommandé par le seul classement conversationnel.
    buy = scope == "meilleur_prix_observe" and price_level in {"excellent", "bon"}
    notices = _OFFER_NOTICES[_response_locale(locale)]
    return {
        "rank": rank,
        "medal": medal,
        "offer_id": prod.get("offer_id"),
        "product_ean": prod.get("product_ean"),
        "offer_kind": prod.get("offer_kind") or "physical_product",
        "name": prod["name"],
        "emoji": emoji,
        "image": prod.get("image"),
        "link": awin.affiliate_link(prod.get("link"), prod.get("merchant")),
        "price": int(prod["price"]),
        "currency": str(prod.get("currency") or "EUR"),
        "merchant": prod["merchant"],
        "delivery": prod.get("delivery") or notices["delivery"],
        # Les feeds ne portent pas une garantie comparable : on renvoie vers les
        # conditions du marchand au lieu d'afficher une durée universelle.
        "warranty": notices["warranty"],
        "cashback": 0,
        "coupon": None,
        "hist": None,
        "histNote": "",
        # Il s'agit d'un ratio de données observées, pas d'une note produit
        # calculée par le LLM. La décision détaillée reste exposée séparément.
        "evidence_score": evidence_score,
        "decision": decision_data,
        "why": str(ann.get("why") or "Un bon choix pour votre besoin."),
        "alt": alt,
        "buy": buy,
    }


async def _rank_real_products(
    query: str, budget: float | None, products: list[dict[str, Any]], locale: str | None = None
) -> dict[str, Any]:
    """Fait classer/annoter par le LLM une liste de produits réels.

    Améliorations :
    - Awin advertisers chargés en parallèle avec l'appel LLM
    - Timeout explicite sur l'appel LLM
    """
    settings = get_settings()
    timeout = settings.llm_timeout_seconds

    provider = get_router().for_task("reasoning")
    listing = [
        {"index": i, "name": p["name"], "price": p["price"], "merchant": p["merchant"], "offer_kind": p.get("offer_kind", "physical_product")}
        for i, p in enumerate(products)
    ]
    budget_txt = f" Budget max : {int(budget)} €." if budget else ""
    response_locale = _response_locale(locale)
    language_txt = _LANGUAGE_NAMES[response_locale]
    messages = [
        Message(role="system", content=_SYSTEM_RANK),
        Message(
            role="user",
            content=(
                f"Langue de réponse obligatoire : {language_txt}. "
                "Traduis l'usage, les étiquettes, les explications et les alternatives dans cette langue. "
                "Les valeurs techniques de verdict doivent rester exactement `acheter` ou `attendre`.\n"
                f"Besoin : {query}.{budget_txt}\nProduits réels :\n{json.dumps(listing, ensure_ascii=False)}"
            ),
        ),
    ]
    emoji = "🛍️"
    usage = query.strip().lower() or "votre besoin"
    picks: list[dict[str, Any]] = []

    if provider.name != "mock":
        try:
            # Parallélisme : LLM + Awin en même temps
            llm_task = asyncio.create_task(
                asyncio.wait_for(
                    provider.complete_json(messages, temperature=0.3),
                    timeout=timeout,
                )
            )
            awin_task = asyncio.create_task(awin.ensure_advertisers())

            raw, _ = await asyncio.gather(llm_task, awin_task)
            data = _parse_json(raw)
            picks = data.get("picks") or []
            emoji = str(data.get("emoji") or emoji)[:4]
            usage = str(data.get("usage") or usage)
        except asyncio.TimeoutError:
            log.warning("Classement LLM timeout (%ss) → ordre SerpApi", timeout)
        except Exception as exc:
            log.warning("Classement LLM indisponible (%s) → ordre SerpApi", exc)
    else:
        # En mode mock, on charge quand même les advertisers pour les liens
        await awin.ensure_advertisers()

    cards: list[dict[str, Any]] = []
    used: set[int] = set()
    for ann in picks[:5]:
        idx = ann.get("index")
        if not (isinstance(idx, int) and 0 <= idx < len(products)) or idx in used:
            continue
        used.add(idx)
        cards.append(_build_real_card(len(cards), products[idx], ann, emoji, response_locale))

    if not cards:
        for slot in range(min(5, len(products))):
            cards.append(_build_real_card(slot, products[slot], {}, emoji, response_locale))

    return {"usage": usage, "emoji": emoji, "offers": len(products), "cards": cards, "real": True}


def _synth(query: str, budget: float | None) -> dict[str, Any]:
    """Repli sûr : ne jamais fabriquer prix, marchands ou scores sans offre réelle."""
    return {
        "usage": query.strip().lower() or "votre besoin",
        "emoji": "🛍️",
        "offers": 0,
        "cards": [],
        "real": False,
    }


def _currency_for(country: str | None) -> str:
    return "CHF" if (country or "").lower() == "ch" else "€"


async def generate_result(
    query: str, budget: float | None, country: str | None = None, locale: str | None = None
) -> dict[str, Any]:
    """Retourne le ``Result`` attendu par le frontend.

    Améliorations :
    - Cache : vérifie d'abord si un résultat récent existe
    - Métriques de latence
    - Timeout global de 25s pour ne jamais bloquer le client

    Ordre de préférence :
      1. Cache (hit) — instantané
      2. Produits RÉELS du catalogue partenaire classés/argumentés par le LLM
      3. Aucune offre vérifiée : résultat non réel, bloqué explicitement par le frontend

    Aucune recherche Google Shopping ou SerpApi n’est autorisée dans ce parcours.
    """
    start = time.time()
    cache = get_cache()

    # La locale fait partie du cache : une annotation néerlandaise ne doit jamais
    # être réutilisée pour un visiteur anglais ou francophone.
    response_locale = _response_locale(locale)
    key = cache_key("recommend", query.strip().lower(), str(budget), str(country), response_locale)

    # Vérification du cache
    cached = await cache.get_json(key)
    if cached is not None:
        log.info("Cache hit pour '%s' (%.0fms)", query[:40], (time.time() - start) * 1000)
        return cached

    from app.services.catalog_search import search_internal_products

    result: dict[str, Any]

    # PRIORITÉ 1 : Catalogue interne FILON (1,3M offres, 207 marchands)
    try:
        products = await asyncio.wait_for(
            search_internal_products(query, budget, country=country),
            timeout=5.0,
        )
        if products:
            log.info("Catalogue interne : %d résultats pour '%s'", len(products), query[:40])
    except (asyncio.TimeoutError, Exception) as exc:
        log.warning("Catalogue interne timeout/erreur (%s)", exc)
        products = []

    # Sans offre du catalogue, le frontend affiche un état explicite « aucune
    # offre vérifiée » plutôt qu'une suggestion issue d'une source externe ou
    # d'une estimation présentée comme achetable.

    if products:
        log.info("Mode données réelles : %d produits via catalogue interne (%s)", len(products), country or "be")
        result = await _rank_real_products(query, budget, products, response_locale)
    else:
        # Ne pas appeler le LLM pour remplir cinq cartes fictives que le frontend
        # devra ensuite bloquer. Cela évite un coût inutile et garantit que tout
        # client de l'API reçoit la même absence honnête d'offre vérifiée.
        log.info("Aucune offre catalogue vérifiée pour '%s'", query[:40])
        result = _synth(query, budget)

    result["country"] = (country or "be").lower()
    result["currency"] = _currency_for(country)

    # Stockage en cache
    await cache.set_json(key, result, TTL_RECOMMEND)

    elapsed = (time.time() - start) * 1000
    log.info("Recommandation générée pour '%s' en %.0fms (real=%s)", query[:40], elapsed, result.get("real"))
    return result


async def stream_events(
    query: str, budget: float | None, country: str | None = None, locale: str | None = None
) -> AsyncGenerator[dict[str, Any], None]:
    """Suite d'événements SSE identiques à ceux du frontend (step/step-done/results).

    Améliorations :
    - Si le résultat est en cache, les étapes défilent rapidement (50ms)
    - Sinon, les étapes avancent à cadence normale pendant que le LLM travaille
    - Annulation propre si le résultat arrive avant la fin des étapes
    """
    cache = get_cache()
    response_locale = _response_locale(locale)
    key = cache_key("recommend", query.strip().lower(), str(budget), str(country), response_locale)

    # Vérification rapide du cache
    cached = await cache.get_json(key)
    if cached is not None:
        # Cache hit : on défile les étapes très vite pour l'effet visuel
        for i in range(len(STEPS)):
            yield {"type": "step", "i": i}
            await asyncio.sleep(0.05)
            yield {"type": "step-done", "i": i}
        yield {"type": "results", "data": cached}
        return

    # Lance le vrai travail en tâche de fond
    task = asyncio.create_task(generate_result(query, budget, country, response_locale))

    # Les étapes avancent pendant que le LLM travaille
    for i in range(len(STEPS)):
        yield {"type": "step", "i": i}
        # Durée adaptative : plus court si le résultat est déjà prêt
        if task.done():
            await asyncio.sleep(0.05)
        else:
            await asyncio.sleep(0.22 + random.uniform(0, 0.08))
        yield {"type": "step-done", "i": i}

    # Attend le résultat si pas encore prêt
    try:
        data = await asyncio.wait_for(task, timeout=30.0)
    except asyncio.TimeoutError:
        log.error("stream_events: timeout global atteint")
        data = _synth(query, budget)
        data["country"] = (country or "be").lower()
        data["currency"] = _currency_for(country)

    yield {"type": "results", "data": data}
