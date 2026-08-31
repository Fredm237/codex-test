"""Classement prudent d'offres indexées pour l'assistant FILON.

Améliorations :
- Cache Redis/LRU pour éviter de rappeler le LLM pour la même requête
- Timeout explicite sur les appels LLM (pas de requête qui pend indéfiniment)
- Parallélisme : classement LLM + annonceurs Awin lorsque des offres catalogue sont disponibles
- Streaming fidèle : les étapes avancent en fonction du travail réel
- Annulation propre si le client déconnecte
- Métriques de latence pour l'observabilité

Le service ne laisse le modèle choisir que les indices d'offres déjà présentes
dans le catalogue. Les textes publics restent déterministes. En l'absence
d'offre éligible, il renvoie une abstention structurée : aucun prix, marchand,
score, avantage ou produit n'est synthétisé.
"""

from __future__ import annotations

import asyncio
import json
import math
import random
import time
from collections.abc import Mapping
from typing import Any, AsyncGenerator

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.observability import (
    decision_trace_event,
    product_intelligence_metrics,
    traced_pipeline_stage,
)
from app.llm.base import Message
from app.llm.router import get_router
from app.services import awin, relevance
from app.services.cache import get_cache, cache_key, TTL_RECOMMEND
from app.services.currency import normalize_currency_code
from app.services.freshness import (
    OFFER_RECOMMENDATION_MAX_AGE_HOURS,
    offer_observation_is_fresh,
)

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


# Ces libellés décrivent uniquement les opérations réellement exécutées.
STEPS = [
    "Compréhension du besoin",
    "Recherche dans le catalogue indexé",
    "Filtrage des offres éligibles",
    "Comparaison des prix observés",
    "Lecture de l'historique disponible",
    "Vérification du stock et de la fraîcheur",
    "Classement des candidats documentés",
    "Préparation des preuves et inconnues",
]

# Les 5 emplacements de cartes, fixes pour la cohérence de l'UI.
SLOTS = [
    ("Offre indexée", "🥇"),
    ("Alternative indexée", "🥈"),
    ("Autre offre indexée", "🥉"),
    ("Option à vérifier", "⭐"),
    ("Autre option", "♻️"),
]

# Le catalogue entier est évalué avant cette étape. Cette borne concerne
# uniquement le contexte envoyé au modèle de langage, jamais la récupération ou
# le classement FILON : le modèle n’a pas besoin de relire des milliers de
# doublons pour choisir parmi les meilleurs candidats déjà comparés.
MAX_LLM_RANKING_CANDIDATES = 80

# Lorsque le classement LLM n’est pas disponible, FILON ne peut pas déduire
# autonomie, performance ou état reconditionné depuis un titre marchand. Les
# cartes de repli restent donc descriptives, localisées et strictement factuelles.
_VERIFIED_RANKS = {
    "fr": ("Offre indexée", "Alternative indexée", "Autre offre indexée", "Option à vérifier", "Autre option"),
    "nl": ("Geïndexeerd aanbod", "Geïndexeerd alternatief", "Ander geïndexeerd aanbod", "Te controleren optie", "Andere optie"),
    "en": ("Indexed offer", "Indexed alternative", "Another indexed offer", "Offer to verify", "Another option"),
}

_VALID_LOCALES = {"fr", "nl", "en"}
# Chaque évolution du moteur de preuve doit séparer son cache des décisions
# précédentes : une réponse devenue invalide ne peut pas survivre à un déploiement.
RECOMMENDATION_ENGINE_VERSION = (
    "assistant-catalog-policy-current-evidence-v4-"
    f"{relevance.CATALOG_RELEVANCE_POLICY_VERSION}"
)


def _recommend_cache_key(query: str, budget: float | None, country: str | None, locale: str) -> str:
    """Construit une clé liée à la version du moteur de décision."""
    return cache_key(
        "recommend",
        RECOMMENDATION_ENGINE_VERSION,
        query.strip().lower(),
        str(budget),
        str(country),
        locale,
    )


def _response_locale(locale: str | None) -> str:
    """Normalise la langue d'annotation demandée par l'interface FILON."""
    value = (locale or "fr").lower().split("-")[0]
    return value if value in _VALID_LOCALES else "fr"


_OFFER_NOTICES = {
    "fr": {"delivery": "voir marchand", "warranty": "conditions marchand"},
    "nl": {"delivery": "bekijk verkoper", "warranty": "voorwaarden verkoper"},
    "en": {"delivery": "see merchant", "warranty": "merchant terms"},
}


_SYSTEM_RANK = (
    "Tu es FILON, copilote d'achat (Belgique/Europe). On te donne une liste "
    "d'OFFRES INDEXÉES (index, nom, prix, devise, marchand) issues du catalogue FILON. "
    "Sélectionne jusqu'à 5 indices par pertinence pour le besoin. "
    "Réponds UNIQUEMENT en JSON.\n\n"
    "Règles STRICTES :\n"
    "- Ne garde que des produits VRAIMENT pertinents pour le besoin et cohérents "
    "entre eux (même type de produit). Écarte tout le reste.\n"
    "- Ne déduis aucune qualité, autonomie, performance, garantie, disponibilité, "
    "promotion ou état qui n'est pas explicitement fourni.\n"
    "- Ne compare jamais deux montants de devises différentes et ne déduis "
    "aucun avantage de prix sans une devise identique.\n"
    "- Si moins de 5 offres sont documentées et pertinentes, renvoie-en moins. Pas de doublon.\n\n"
    "Format :\n"
    "{\n"
    '  "picks": [{"index": entier}, ...]\n'
    "}\n"
    "Ne renvoie que du JSON."
)


def _verified_rank_label(slot: int, locale: str | None) -> str:
    """Libellé de repli qui ne promet pas une qualité produit non observée."""
    ranks = _VERIFIED_RANKS[_response_locale(locale)]
    return ranks[min(max(slot, 0), len(ranks) - 1)]


def _finite_nonnegative_age(value: object) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(value)
        and 0 <= value <= OFFER_RECOMMENDATION_MAX_AGE_HOURS
    )


def _decision_stock_is_confirmed(decision_data: Mapping[str, Any]) -> bool:
    """Exige au moins une preuve de stock positive et aucune contradiction."""

    fact_assertions: list[bool] = []
    facts = decision_data.get("facts")
    if isinstance(facts, Mapping) and "in_stock" in facts:
        fact_assertions.append(facts.get("in_stock") is True)

    signal_assertions: list[bool] = []
    signals = decision_data.get("signals")
    if isinstance(signals, list):
        for signal in signals:
            if isinstance(signal, Mapping) and signal.get("key") == "availability":
                signal_assertions.append(
                    signal.get("status") == "positive"
                    and signal.get("in_stock") is True
                )

    evidence_assertions: list[bool] = []
    evidence = decision_data.get("evidence")
    if isinstance(evidence, list):
        for item in evidence:
            if not isinstance(item, Mapping) or item.get("key") != "availability":
                continue
            value = item.get("value")
            evidence_assertions.append(
                item.get("state") == "observed"
                and isinstance(value, Mapping)
                and value.get("in_stock") is True
            )

    return (
        bool(signal_assertions)
        and all(signal_assertions)
        and bool(evidence_assertions)
        and all(evidence_assertions)
        and all(fact_assertions)
    )


def _decision_freshness_is_confirmed(
    decision_data: Mapping[str, Any],
    product: Mapping[str, Any],
) -> bool:
    """Valide toute preuve temporelle présente et refuse les contradictions."""

    fact_assertions: list[bool] = []
    facts = decision_data.get("facts")
    if isinstance(facts, Mapping):
        for key in ("freshness_hours", "age_hours"):
            if key in facts:
                fact_assertions.append(_finite_nonnegative_age(facts.get(key)))
        for key in ("last_observed_at", "observed_at"):
            if key in facts:
                fact_assertions.append(offer_observation_is_fresh(facts.get(key)))

    signal_assertions: list[bool] = []
    signals = decision_data.get("signals")
    if isinstance(signals, list):
        for signal in signals:
            if isinstance(signal, Mapping) and signal.get("key") == "freshness":
                signal_assertions.append(
                    signal.get("status") == "positive"
                    and _finite_nonnegative_age(signal.get("age_hours"))
                )

    evidence_assertions: list[bool] = []
    evidence = decision_data.get("evidence")
    if isinstance(evidence, list):
        for item in evidence:
            if not isinstance(item, Mapping) or item.get("key") != "freshness":
                continue
            value = item.get("value")
            evidence_assertions.append(
                item.get("state") == "observed"
                and isinstance(value, Mapping)
                and value.get("status") in {"positive", "fresh"}
                and _finite_nonnegative_age(value.get("age_hours"))
                and offer_observation_is_fresh(item.get("observed_at"))
            )

    if "observed_at" in product:
        fact_assertions.append(offer_observation_is_fresh(product.get("observed_at")))

    return (
        bool(fact_assertions)
        and all(fact_assertions)
        and bool(signal_assertions)
        and all(signal_assertions)
        and bool(evidence_assertions)
        and all(evidence_assertions)
    )


def _decision_price_is_confirmed(
    decision_data: Mapping[str, Any],
    product: Mapping[str, Any],
    currency: str,
) -> bool:
    facts = decision_data.get("facts")
    if not isinstance(facts, Mapping):
        return False
    product_price = product.get("price")
    decision_price = facts.get("item_price")
    if (
        isinstance(product_price, bool)
        or not isinstance(product_price, (int, float))
        or not math.isfinite(product_price)
        or product_price <= 0
        or isinstance(decision_price, bool)
        or not isinstance(decision_price, (int, float))
        or not math.isfinite(decision_price)
        or decision_price <= 0
        or not math.isclose(float(product_price), float(decision_price), abs_tol=0.005)
        or normalize_currency_code(facts.get("currency")) != currency
        or not offer_observation_is_fresh(facts.get("last_observed_at"))
    ):
        return False

    assertions: list[bool] = []
    evidence = decision_data.get("evidence")
    if isinstance(evidence, list):
        for item in evidence:
            if not isinstance(item, Mapping) or item.get("key") != "price":
                continue
            value = item.get("value")
            amount = value.get("amount") if isinstance(value, Mapping) else None
            assertions.append(
                item.get("state") == "observed"
                and offer_observation_is_fresh(item.get("observed_at"))
                and isinstance(value, Mapping)
                and normalize_currency_code(value.get("currency")) == currency
                and not isinstance(amount, bool)
                and isinstance(amount, (int, float))
                and math.isfinite(amount)
                and math.isclose(float(amount), float(product_price), abs_tol=0.005)
            )
    return bool(assertions) and all(assertions)


def _current_card_evidence_is_proven(
    product: Mapping[str, Any],
    decision_data: Mapping[str, Any] | None,
    currency: str | None,
) -> bool:
    return bool(
        decision_data is not None
        and currency is not None
        and product.get("in_stock") is True
        and offer_observation_is_fresh(product.get("observed_at"))
        and decision_data.get("version") == 3
        and _decision_price_is_confirmed(decision_data, product, currency)
        and _decision_stock_is_confirmed(decision_data)
        and _decision_freshness_is_confirmed(decision_data, product)
    )


def _verified_card_snapshot(
    product: Mapping[str, Any],
) -> tuple[dict[str, Any], Mapping[str, Any] | None, str | None]:
    """Rapproche les faits canoniques avant toute décision de publication."""

    decision_data = (
        product.get("decision")
        if isinstance(product.get("decision"), Mapping)
        else None
    )
    decision_facts = (
        decision_data.get("facts")
        if decision_data is not None
        and isinstance(decision_data.get("facts"), Mapping)
        else {}
    )
    observed_at = product.get("observed_at")
    if "observed_at" not in product:
        observed_at = decision_facts.get("last_observed_at")
    in_stock = product.get("in_stock") is True
    if "in_stock" not in product and decision_data is not None:
        # Compatibilité d'entrée : seule une preuve canonique complète peut
        # alimenter le champ, jamais l'absence de valeur ni le rang de la carte.
        in_stock = _decision_stock_is_confirmed(decision_data)

    currency = normalize_currency_code(product.get("currency"))
    verified_product = dict(product)
    verified_product["currency"] = currency
    verified_product["in_stock"] = in_stock
    verified_product["observed_at"] = observed_at
    return verified_product, decision_data, currency


def _buy_claim_is_proven(
    product: Mapping[str, Any],
    decision_data: Mapping[str, Any] | None,
    currency: str | None,
) -> bool:
    if not _current_card_evidence_is_proven(product, decision_data, currency):
        return False
    assert decision_data is not None
    verdict = decision_data.get("price_verdict")
    if not isinstance(verdict, Mapping):
        return False
    return (
        decision_data.get("recommendation_scope") == "meilleur_prix_observe"
        and verdict.get("level") in {"excellent", "bon"}
        and verdict.get("basis") == "price_history"
    )


def _validated_pick_indices(value: object, *, candidate_count: int) -> list[int]:
    """Ne conserve que cinq indices entiers uniques issus d'une liste JSON."""

    if not isinstance(value, list):
        return []
    selected: list[int] = []
    for item in value[:MAX_LLM_RANKING_CANDIDATES]:
        if not isinstance(item, Mapping):
            continue
        index = item.get("index")
        if (
            isinstance(index, bool)
            or not isinstance(index, int)
            or not 0 <= index < candidate_count
            or index in selected
        ):
            continue
        selected.append(index)
        if len(selected) == 5:
            break
    return selected


def _unique_card_currency(cards: object) -> str | None:
    """Devise globale seulement si chaque carte prouve la même devise réelle."""

    if not isinstance(cards, list) or not cards:
        return None
    currencies: set[str] = set()
    for card in cards:
        if not isinstance(card, Mapping):
            return None
        currency = normalize_currency_code(card.get("currency"))
        if currency is None:
            return None
        currencies.add(currency)
    return next(iter(currencies)) if len(currencies) == 1 else None


def _revalidate_cached_cards(cached: dict[str, Any]) -> bool:
    """Valide une réponse cache et retire tout claim devenu périmé."""

    cards = cached.get("cards")
    if not isinstance(cards, list):
        return False
    if cached.get("real") is False:
        cached["currency"] = None
        return cards == [] and cached.get("offers") == 0
    if cached.get("real") is not True or not cards:
        return False
    for card in cards:
        if not isinstance(card, dict):
            return False
        price = card.get("price")
        offer_id = card.get("offer_id")
        if (
            isinstance(offer_id, bool)
            or not isinstance(offer_id, int)
            or offer_id <= 0
            or not isinstance(card.get("name"), str)
            or not card["name"].strip()
            or not isinstance(card.get("merchant"), str)
            or not card["merchant"].strip()
            or isinstance(price, bool)
            or not isinstance(price, (int, float))
            or not math.isfinite(price)
            or price <= 0
        ):
            return False
        currency = normalize_currency_code(card.get("currency"))
        if currency is None:
            return False
        card["currency"] = currency
        decision_data = card.get("decision")
        current_evidence = _current_card_evidence_is_proven(
            card,
            decision_data if isinstance(decision_data, Mapping) else None,
            currency,
        )
        if current_evidence is not True or card.get("evidence_current") is not True:
            return False
        card["evidence_current"] = True
        card["buy"] = _buy_claim_is_proven(
            card,
            decision_data if isinstance(decision_data, Mapping) else None,
            currency,
        )
    currency = _unique_card_currency(cards)
    offers = cached.get("offers")
    if (
        currency is None
        or isinstance(offers, bool)
        or not isinstance(offers, int)
        or offers < len(cards)
    ):
        return False
    cached["currency"] = currency
    return True


def _build_real_card(
    slot: int,
    prod: dict[str, Any],
    ann: Mapping[str, Any],
    emoji: str,
    locale: str | None = None,
) -> dict[str, Any]:
    """Carte déterministe à partir d'une offre indexée.

    ``ann`` est conservé pour compatibilité d'appel, mais son texte n'est jamais
    publié : le modèle peut uniquement choisir un indice en amont.
    """
    _, medal = SLOTS[slot]
    del ann
    rank = _verified_rank_label(slot, locale)
    verified_product, decision_data, currency = _verified_card_snapshot(prod)
    observed_at = verified_product.get("observed_at")
    in_stock = verified_product.get("in_stock") is True
    # « Bon moment » demande à la fois le meilleur prix observé et un historique
    # favorable. Tout autre cas reste une offre à vérifier, jamais un achat
    # recommandé par le seul classement conversationnel.
    evidence_current = _current_card_evidence_is_proven(
        verified_product,
        decision_data,
        currency,
    )
    buy = _buy_claim_is_proven(verified_product, decision_data, currency)
    notices = _OFFER_NOTICES[_response_locale(locale)]
    fallback_why = {
        "fr": "Offre issue du catalogue indexé ; vérifiez les conditions chez le marchand.",
        "nl": "Aanbod uit de geïndexeerde catalogus; controleer de voorwaarden bij de verkoper.",
        "en": "Offer from the indexed catalogue; verify the terms with the merchant.",
    }[_response_locale(locale)]
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
        "price": round(float(prod["price"]), 2),
        # Une devise absente reste inconnue. Le pays de navigation ne constitue
        # jamais une preuve suffisante pour remplacer cette valeur par EUR.
        "currency": currency,
        "merchant": prod["merchant"],
        "in_stock": in_stock,
        "observed_at": observed_at if offer_observation_is_fresh(observed_at) else None,
        "evidence_current": evidence_current,
        "delivery": prod.get("delivery") or notices["delivery"],
        # Les feeds ne portent pas une garantie comparable : on renvoie vers les
        # conditions du marchand au lieu d'afficher une durée universelle.
        "warranty": notices["warranty"],
        # Le feed de cette route ne prouve aucun cashback. `None` conserve
        # l'inconnue, contrairement à zéro qui affirmerait son absence.
        "cashback": None,
        "coupon": None,
        "hist": None,
        "histNote": "",
        "decision": decision_data,
        "why": fallback_why,
        # Le modèle n'est pas autorisé à proposer un nom absent des offres
        # indexées. Une future alternative devra référencer un offer_id réel.
        "alt": None,
        "buy": buy,
    }


async def _rank_real_products(
    query: str, budget: float | None, products: list[dict[str, Any]], locale: str | None = None
) -> dict[str, Any]:
    """Fait sélectionner au LLM des indices parmi des produits réels comparables.

    Améliorations :
    - Awin advertisers chargés en parallèle avec l'appel LLM
    - Timeout explicite sur l'appel LLM
    """
    decision_trace_event(
        "candidate_count",
        counts={"candidate_count": len(products)},
    )
    # Défense en profondeur pour les anciens appelants : même si la recherche
    # catalogue régresse, une offre sans devise ne doit atteindre ni le budget,
    # ni le contexte du reranker, ni une carte portant un claim favorable.
    comparable_products: list[dict[str, Any]] = []
    for product in products:
        currency = normalize_currency_code(product.get("currency"))
        price = product.get("price")
        if (
            currency is None
            or isinstance(price, bool)
            or not isinstance(price, (int, float))
            or not math.isfinite(price)
            or price <= 0
        ):
            continue
        # Le budget de ce contrat historique est exprimé en euros. Sans taux
        # de change et frais observés, aucune autre devise n'est comparable.
        if budget is not None and (currency != "EUR" or price > budget):
            continue
        comparable_products.append({**product, "currency": currency})

    decision_trace_event(
        "filtering",
        counts={
            "input_count": len(products),
            "eligible_count": len(comparable_products),
            "rejected_count": max(0, len(products) - len(comparable_products)),
        },
    )

    if not comparable_products:
        decision_trace_event(
            "product_ranking",
            counts={"candidate_count": 0, "ranked_count": 0},
            flags={"model_used": False},
        )
        decision_trace_event("offer_selection", counts={"selected_count": 0})
        decision_trace_event(
            "evidence",
            counts={"evidenced_count": 0, "unknown_count": len(products)},
        )
        decision_trace_event(
            "decision",
            outcome="abstain",
            reason="no_comparable_offer",
        )
        return _synth(query, budget)

    currencies = {product["currency"] for product in comparable_products}
    # Sans FX et frais observés, même des codes valides ne deviennent pas
    # comparables. L'abstention précède tout appel au modèle et tout fallback.
    if len(currencies) != 1:
        decision_trace_event(
            "product_ranking",
            counts={
                "candidate_count": len(comparable_products),
                "ranked_count": 0,
            },
            flags={"model_used": False},
        )
        decision_trace_event("offer_selection", counts={"selected_count": 0})
        decision_trace_event(
            "evidence",
            counts={"evidenced_count": 0, "unknown_count": len(comparable_products)},
        )
        decision_trace_event(
            "decision",
            outcome="abstain",
            reason="currency_not_comparable",
        )
        return _synth(query, budget)

    # Le reranker et le fallback ne voient que des snapshots dont toutes les
    # dimensions publiques ont été rapprochées. Un prix techniquement valide
    # sans preuve canonique n'est pas une carte Assistant publiable.
    evidenced_products: list[dict[str, Any]] = []
    for product in comparable_products:
        verified_product, decision_data, currency = _verified_card_snapshot(product)
        if _current_card_evidence_is_proven(
            verified_product,
            decision_data,
            currency,
        ) is True:
            evidenced_products.append(product)

    decision_trace_event(
        "evidence",
        counts={
            "evidenced_count": len(evidenced_products),
            "unknown_count": max(
                0,
                len(comparable_products) - len(evidenced_products),
            ),
        },
    )

    if not evidenced_products:
        decision_trace_event(
            "product_ranking",
            counts={
                "candidate_count": len(comparable_products),
                "ranked_count": 0,
            },
            flags={"model_used": False},
        )
        decision_trace_event("offer_selection", counts={"selected_count": 0})
        decision_trace_event(
            "decision",
            outcome="abstain",
            reason="no_current_evidence",
        )
        return _synth(query, budget)

    settings = get_settings()
    timeout = settings.llm_timeout_seconds

    provider = get_router().for_task("reasoning")
    # `products` contient toutes les offres éligibles, déjà comparées par le
    # Score FILON. Seul le contexte du modèle est compacté après ce classement
    # global afin de respecter sa fenêtre de contexte sans tronquer la recherche.
    ranking_candidates = evidenced_products[:MAX_LLM_RANKING_CANDIDATES]
    listing = [
        {
            "index": i,
            "name": p["name"],
            "price": p["price"],
            "currency": p["currency"],
            "merchant": p["merchant"],
            "offer_kind": p.get("offer_kind", "physical_product"),
        }
        for i, p in enumerate(ranking_candidates)
    ]
    budget_txt = f" Budget max : {int(budget)} €." if budget else ""
    response_locale = _response_locale(locale)
    messages = [
        Message(role="system", content=_SYSTEM_RANK),
        Message(
            role="user",
            content=(
                f"Besoin : {query}.{budget_txt}\nProduits réels :\n{json.dumps(listing, ensure_ascii=False)}"
            ),
        ),
    ]
    emoji = "🛍️"
    usage = query.strip().lower() or "votre besoin"
    selected_indices: list[int] = []
    model_used = False

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
            model_used = True
            selected_indices = _validated_pick_indices(
                data.get("picks") if isinstance(data, Mapping) else None,
                candidate_count=len(ranking_candidates),
            )
        except asyncio.TimeoutError:
            log.warning("Classement LLM timeout (%ss) → ordre catalogue", timeout)
        except Exception as exc:
            log.warning(
                "Classement LLM indisponible (error_type=%s) → ordre catalogue",
                type(exc).__name__,
            )
    else:
        # En mode mock, on charge quand même les advertisers pour les liens
        await awin.ensure_advertisers()

    cards: list[dict[str, Any]] = []
    for idx in selected_indices:
        card = _build_real_card(
            len(cards), ranking_candidates[idx], {}, emoji, response_locale
        )
        if card.get("evidence_current") is True:
            cards.append(card)

    if not cards:
        for slot in range(min(5, len(ranking_candidates))):
            card = _build_real_card(
                len(cards), ranking_candidates[slot], {}, emoji, response_locale
            )
            if card.get("evidence_current") is True:
                cards.append(card)

    decision_trace_event(
        "product_ranking",
        counts={
            "candidate_count": len(evidenced_products),
            "ranked_count": len(ranking_candidates),
        },
        flags={"model_used": model_used},
    )
    decision_trace_event(
        "offer_selection",
        counts={"selected_count": len(cards)},
    )

    if not cards:
        decision_trace_event(
            "decision",
            outcome="abstain",
            reason="ranking_unavailable",
        )
        return _synth(query, budget)

    decision_trace_event(
        "decision",
        outcome="recommend",
        reason="none" if selected_indices else "ranking_unavailable",
    )
    return {
        "usage": usage,
        "emoji": emoji,
        "offers": len(evidenced_products),
        "cards": cards,
        "real": True,
        "currency": _unique_card_currency(cards),
    }


def _synth(query: str, budget: float | None) -> dict[str, Any]:
    """Repli sûr : ne jamais fabriquer prix, marchands ou scores sans offre réelle."""
    return {
        "usage": query.strip().lower() or "votre besoin",
        "emoji": "🛍️",
        "offers": 0,
        "cards": [],
        "real": False,
        "currency": None,
    }


@traced_pipeline_stage("catalogue")
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
      2. Offres indexées du catalogue classées/annotées prudemment par le LLM
      3. Aucune offre indexée : abstention explicite pour le frontend

    Aucune recherche Google Shopping ou SerpApi n’est autorisée dans ce parcours.
    """
    start = time.time()
    cache = get_cache()

    # La locale fait partie du cache : une annotation néerlandaise ne doit jamais
    # être réutilisée pour un visiteur anglais ou francophone.
    response_locale = _response_locale(locale)
    key = _recommend_cache_key(query, budget, country, response_locale)

    # Vérification du cache
    cached = await cache.get_json(key)
    if isinstance(cached, dict) and _revalidate_cached_cards(cached):
        log.info("Cache recommandation hit (%.0fms)", (time.time() - start) * 1000)
        product_intelligence_metrics.record_recommendation(cached, delivery="cache")
        cards = cached.get("cards") if isinstance(cached.get("cards"), list) else []
        decision_trace_event(
            "offer_selection",
            counts={"selected_count": len(cards)},
            flags={"cache_used": True},
        )
        decision_trace_event(
            "evidence",
            counts={"evidenced_count": len(cards), "unknown_count": 0},
            flags={"cache_used": True},
        )
        decision_trace_event(
            "decision",
            outcome="recommend" if cards else "abstain",
            reason="none" if cards else "no_catalog_offer",
            flags={"cache_used": True},
        )
        return cached
    if cached is not None:
        log.warning("Cache recommandation invalide → recalcul")

    from app.services.catalog_search import search_internal_products

    result: dict[str, Any]

    # PRIORITÉ 1 : Catalogue interne FILON (1,3M offres, 207 marchands)
    try:
        # La recherche parcourt l’intégralité des offres éligibles. Aucun délai
        # arbitraire ne la transforme en échantillon incomplet ou en abstention.
        products = await search_internal_products(query, budget, country=country)
        if products:
            log.info("Catalogue interne : %d résultats", len(products))
    except Exception as exc:
        log.warning("Catalogue interne erreur (error_type=%s)", type(exc).__name__)
        products = []

    # Sans offre du catalogue, le frontend affiche un état explicite « aucune
    # offre indexée » plutôt qu'une suggestion issue d'une source externe ou
    # d'une estimation présentée comme achetable.

    if products:
        log.info("Mode données réelles : %d produits via catalogue interne", len(products))
        result = await _rank_real_products(query, budget, products, response_locale)
    else:
        # Ne pas appeler le LLM pour remplir cinq cartes fictives que le frontend
        # devra ensuite bloquer. Cela évite un coût inutile et garantit que tout
        # client de l'API reçoit la même absence honnête d'offre indexée.
        log.info("Aucune offre catalogue indexée")
        decision_trace_event("offer_selection", counts={"selected_count": 0})
        decision_trace_event(
            "evidence",
            counts={"evidenced_count": 0, "unknown_count": 0},
        )
        decision_trace_event(
            "decision",
            outcome="abstain",
            reason="no_catalog_offer",
        )
        result = _synth(query, budget)

    result["country"] = (country or "be").lower()
    result["currency"] = _unique_card_currency(result.get("cards"))

    # Stockage en cache
    await cache.set_json(key, result, TTL_RECOMMEND)

    elapsed = (time.time() - start) * 1000
    product_intelligence_metrics.record_recommendation(result, delivery="generated")
    log.info("Recommandation générée en %.0fms (real=%s)", elapsed, result.get("real"))
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
    response_locale = _response_locale(locale)

    # Le cycle unique passe toujours par ``generate_result`` : son cache garde
    # le chemin rapide et l'instrumentation catalogue couvre aussi le SSE.
    task = asyncio.create_task(generate_result(query, budget, country, response_locale))
    try:
        # Les étapes avancent pendant que le LLM travaille.
        for i in range(len(STEPS)):
            yield {"type": "step", "i": i}
            # Durée adaptative : plus court si le résultat est déjà prêt.
            if task.done():
                await asyncio.sleep(0.05)
            else:
                await asyncio.sleep(0.22 + random.uniform(0, 0.08))
            yield {"type": "step-done", "i": i}

        # Attend le résultat si pas encore prêt.
        try:
            data = await asyncio.wait_for(task, timeout=30.0)
        except asyncio.TimeoutError:
            log.error("stream_events: timeout global atteint")
            data = _synth(query, budget)
            data["country"] = (country or "be").lower()
            product_intelligence_metrics.record_recommendation(data, delivery="timeout")

        yield {"type": "results", "data": data}
    finally:
        # Une fermeture anticipée du générateur (déconnexion SSE) ne doit
        # laisser ni tâche orpheline ni exception brute au handler asyncio.
        if not task.done():
            task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        except Exception:
            # Le décorateur catalogue a déjà compté et journalisé uniquement
            # le type. Consommer ici l'exception empêche asyncio d'en publier
            # ultérieurement le message via "Task exception was never retrieved".
            pass
