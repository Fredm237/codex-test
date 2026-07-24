"""Génération des recommandations d'achat par le LLM.

Produit exactement le contrat que le frontend consomme (voir SearchAssistant :
``Result`` = { usage, offers, cards[5] }). Le LLM raisonne réellement sur le
besoin et propose 5 options classées avec prix estimés. Si aucune clé LLM n'est
configurée (ou en cas d'erreur), on retombe sur une synthèse déterministe pour
que l'endpoint reste toujours fonctionnel.

Les prix sont des *estimations* de marché (connaissance du modèle), pas encore
des prix live — le frontend l'indique clairement à l'utilisateur.
"""

from __future__ import annotations

import asyncio
import json
import random
from typing import Any, AsyncGenerator

from app.core.logging import get_logger
from app.llm.base import Message
from app.llm.router import get_router

log = get_logger("recommend")

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
    '  "name": "nom précis d’un produit réel du marché",\n'
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
    '  "alt": "nom d’une alternative" ou null,\n'
    '  "buy": true si c’est le bon moment d’acheter, false s’il vaut mieux attendre\n'
    "}\n"
    "Respecte le budget indiqué s’il y en a un. Prix = estimations réalistes, pas inventées."
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
        "emoji": "🛍️",  # remplacé par l'emoji de catégorie plus bas
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


# Emplacements pour le classement des produits RÉELS (SerpApi).
_SYSTEM_RANK = (
    "Tu es FILON, copilote d'achat expert (Belgique/Europe). On te donne une liste "
    "de PRODUITS RÉELS (index, nom, prix, marchand) issus de Google Shopping. "
    "Choisis les 5 meilleurs pour le besoin et classe-les. Réponds UNIQUEMENT en JSON.\n\n"
    "Format :\n"
    "{\n"
    '  "usage": "catégorie du besoin en français",\n'
    '  "emoji": "un emoji de la catégorie",\n'
    '  "picks": [ 5 objets, un par emplacement, DANS CET ORDRE :\n'
    "     1) meilleur rapport qualité/prix, 2) meilleur budget, 3) meilleure autonomie,\n"
    "     4) meilleure performance, 5) meilleur reconditionné/alternative ]\n"
    "}\n"
    "Chaque pick : {\n"
    '  "index": entier = l’index du produit choisi dans la liste,\n'
    '  "score": entier 80-96 (Score FILON),\n'
    '  "why": "une phrase en français : pourquoi ce produit pour ce besoin",\n'
    '  "verdict": "acheter" ou "attendre",\n'
    '  "alt": "nom d’une alternative" ou null\n'
    "}\n"
    "Utilise des index DIFFÉRENTS pour chaque emplacement. Ne renvoie que du JSON."
)


def _build_real_card(slot: int, prod: dict[str, Any], ann: dict[str, Any], emoji: str) -> dict[str, Any]:
    """Carte à partir d'un produit RÉEL (SerpApi) + annotation du LLM."""
    rank, medal = SLOTS[slot]
    try:
        score = max(0, min(100, int(ann.get("score", 88))))
    except (TypeError, ValueError):
        score = 88
    alt = ann.get("alt")
    alt = str(alt) if alt not in (None, "", "null") else None
    verdict = str(ann.get("verdict", "acheter")).lower()
    return {
        "rank": rank,
        "medal": medal,
        "name": prod["name"],
        "emoji": emoji,
        "image": prod.get("image"),
        "link": prod.get("link"),
        "price": int(prod["price"]),
        "merchant": prod["merchant"],
        "delivery": prod.get("delivery") or "voir marchand",
        "warranty": "24 mois",           # garantie légale UE (2 ans)
        "cashback": 0,                    # pas de donnée réelle → masqué côté UI
        "coupon": None,
        "hist": None,                     # pas d'historique réel → masqué côté UI
        "histNote": "",
        "score": score,
        "why": str(ann.get("why") or "Un bon choix pour votre besoin."),
        "alt": alt,
        "buy": verdict != "attendre",
    }


async def _rank_real_products(
    query: str, budget: float | None, products: list[dict[str, Any]]
) -> dict[str, Any]:
    """Fait classer/annoter par le LLM une liste de produits réels."""
    provider = get_router().for_task("reasoning")
    listing = [
        {"index": i, "name": p["name"], "price": p["price"], "merchant": p["merchant"]}
        for i, p in enumerate(products)
    ]
    budget_txt = f" Budget max : {int(budget)} €." if budget else ""
    messages = [
        Message(role="system", content=_SYSTEM_RANK),
        Message(
            role="user",
            content=f"Besoin : {query}.{budget_txt}\nProduits réels :\n{json.dumps(listing, ensure_ascii=False)}",
        ),
    ]
    emoji = "🛍️"
    usage = query.strip().lower() or "votre besoin"
    picks: list[dict[str, Any]] = []
    if provider.name != "mock":
        try:
            data = json.loads(await provider.complete_json(messages, temperature=0.3))
            picks = data.get("picks") or []
            emoji = str(data.get("emoji") or emoji)[:4]
            usage = str(data.get("usage") or usage)
        except Exception as exc:  # pragma: no cover
            log.warning("Classement LLM indisponible (%s) → ordre SerpApi", exc)

    cards: list[dict[str, Any]] = []
    used: set[int] = set()
    for slot in range(5):
        ann = picks[slot] if slot < len(picks) else {}
        idx = ann.get("index")
        if not (isinstance(idx, int) and 0 <= idx < len(products)) or idx in used:
            idx = next((j for j in range(len(products)) if j not in used), slot % len(products))
        used.add(idx)
        cards.append(_build_real_card(slot, products[idx], ann, emoji))
    return {"usage": usage, "emoji": emoji, "offers": len(products), "cards": cards, "real": True}


def _synth(query: str, budget: float | None) -> dict[str, Any]:
    """Repli déterministe quand le LLM n'est pas disponible."""
    seed = abs(hash(query)) % (10**8)
    base = int(budget) if budget else 200 + seed % 700
    merchants = ["Amazon", "Fnac", "Coolblue", "Boulanger", "MediaMarkt"]
    defs = [
        (0.98, 93, True, "Le meilleur équilibre global pour votre besoin.", "−20 €", "baisse", "sous la moyenne"),
        (0.80, 86, True, "Presque aussi bon, sensiblement moins cher.", None, "stable", "prix habituel"),
        (1.05, 88, False, "L'endurance en plus, si c'est votre priorité.", None, "stable", "proche moyenne"),
        (1.18, 85, False, "Le plus puissant de la sélection.", None, "hausse", "mieux vaut attendre"),
        (0.72, 87, True, "L'équivalent reconditionné, garanti, au meilleur prix.", None, "baisse", "−28 % vs neuf"),
    ]
    delivery = ["24 h", "48 h", "2-3 j", "3-4 j"]
    cards = []
    for i, (mult, score, buy, why, coupon, hist, note) in enumerate(defs):
        rank, medal = SLOTS[i]
        cards.append({
            "rank": rank, "medal": medal, "name": f"Option {i + 1}", "emoji": "🛍️",
            "image": None, "link": None,
            "price": int(base * mult),
            "merchant": "Back Market" if i == 4 else merchants[(seed >> i) % 5],
            "delivery": delivery[i % 4], "warranty": "24 mois",
            "cashback": 3 + ((seed >> i) % 4), "coupon": coupon, "hist": hist,
            "histNote": note, "score": score, "why": why, "alt": None, "buy": buy,
        })
    usage = query.strip().lower() or "votre besoin"
    return {"usage": usage, "emoji": "🛍️", "offers": 24 + seed % 26, "cards": cards, "real": False}


async def generate_result(query: str, budget: float | None) -> dict[str, Any]:
    """Retourne le ``Result`` attendu par le frontend.

    Ordre de préférence :
      1. Produits RÉELS (SerpApi) classés/argumentés par le LLM — photos, prix,
         marchands et liens réels.
      2. LLM seul : produits plausibles, prix estimés.
      3. Synthèse déterministe (aucune clé).
    """
    from app.services.serpapi_shopping import search_products

    products = await search_products(query, budget)
    if products:
        log.info("Mode données réelles : %d produits SerpApi", len(products))
        return await _rank_real_products(query, budget, products)

    provider = get_router().for_task("reasoning")
    if provider.name == "mock":
        log.info("Pas de LLM configuré → synthèse de repli")
        return _synth(query, budget)

    budget_txt = f" Budget maximum : {int(budget)} €." if budget else ""
    messages = [
        Message(role="system", content=_SYSTEM),
        Message(role="user", content=f"Besoin : {query}.{budget_txt}"),
    ]
    try:
        raw = await provider.complete_json(messages, temperature=0.4)
        data = json.loads(raw)
        cards_raw = data.get("cards") or []
        emoji = str(data.get("emoji") or "🛍️")[:4]
        cards = [_coerce_card(cards_raw[i] if i < len(cards_raw) else {}, i) for i in range(5)]
        for c in cards:
            c["emoji"] = emoji
        return {
            "usage": str(data.get("usage") or query.strip().lower() or "votre besoin"),
            "emoji": emoji,
            "offers": 24 + abs(hash(query)) % 26,
            "cards": cards,
            "real": False,
        }
    except Exception as exc:  # pragma: no cover - dépend du réseau/modèle
        log.warning("LLM indisponible ou réponse invalide (%s) → repli", exc)
        return _synth(query, budget)


async def stream_events(
    query: str, budget: float | None
) -> AsyncGenerator[dict[str, Any], None]:
    """Suite d'événements SSE identiques à ceux du frontend (step/step-done/results)."""
    # Lance le vrai travail LLM en tâche de fond pendant que défilent les étapes.
    task = asyncio.create_task(generate_result(query, budget))
    for i in range(len(STEPS)):
        yield {"type": "step", "i": i}
        await asyncio.sleep(0.24)
        yield {"type": "step-done", "i": i}
    data = await task
    yield {"type": "results", "data": data}
