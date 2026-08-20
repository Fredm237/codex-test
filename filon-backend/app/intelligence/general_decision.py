"""Décision générale partagée par les parcours Assistant et planification de besoins."""
from __future__ import annotations

from app.intelligence.contracts import CoreOfferSnapshot
from app.intelligence.intent_resolution import GeneralIntent, IntentScope
from app.services import relevance, taxonomy


def _display_role(offer: CoreOfferSnapshot) -> str:
    if offer.filon_category == taxonomy.CHAUSSURES:
        return "footwear"
    if offer.filon_category in {taxonomy.ACCESSOIRES, taxonomy.BAGAGERIE, taxonomy.BIJOUX}:
        return "accessory"
    return "base"


def _match_proof(
    scope: IntentScope,
    offer: CoreOfferSnapshot,
    *,
    request_terms: tuple[str, ...],
) -> float:
    """Conserve séparément la preuve de scope et celle d’un qualificatif.

    Les synonymes proposés pour un scope constituent des alternatives. Les
    fusionner avec « connectée » ou « réduction de bruit » dilue cette exigence
    explicite ; chaque source de preuve est donc notée indépendamment.
    """
    scope_match = relevance.score(list(scope.query_terms), offer.name or "", offer_kind=offer.offer_kind)
    qualifier_match = (
        relevance.score(list(request_terms), offer.name or "", offer_kind=offer.offer_kind)
        if request_terms
        else 0.0
    )
    return max(scope_match, qualifier_match)


def _rank(
    scope: IntentScope,
    offer: CoreOfferSnapshot,
    *,
    request_terms: tuple[str, ...],
) -> tuple[float, float, int]:
    match = _match_proof(scope, offer, request_terms=request_terms)
    price = offer.price if offer.price is not None else float("inf")
    return (-round(match, 3), price, offer.offer_id)


def _scope_candidates(
    scope: IntentScope,
    offers: list[CoreOfferSnapshot],
    *,
    budget: float | None,
    request_terms: tuple[str, ...],
) -> list[CoreOfferSnapshot]:
    scoped = [
        offer for offer in offers
        if offer.filon_category == scope.category
        and (scope.subcategory is None or offer.filon_subcategory == scope.subcategory)
    ]
    # Le scope prouve l’univers de recherche, non la nature de chaque objet.
    # Une demande qui ne désigne pas explicitement un public enfant ne doit pas
    # faire inférer ce public depuis une offre moins chère.
    age_compatible = [
        offer for offer in scoped
        if relevance.age_compatible(scope.source_text, offer.name or "")
    ]
    if age_compatible:
        scoped = age_compatible
    elif not relevance.targets_children(scope.source_text):
        return []
    # Si la demande formule explicitement « vêtements », chaque résultat doit
    # aussi le prouver dans son titre. Cette règle générique bloque ainsi les
    # balles, filets, jeux ou bijoux qui portent seulement le nom d’un sport.
    if relevance.request_requires_clothing(scope.source_text):
        scoped = [
            offer for offer in scoped
            if relevance.has_clothing_proof(offer.name or "")
            and relevance.gender_compatible(scope.source_text, offer.name or "")
        ]
    if relevance.request_requires_footwear(scope.source_text):
        scoped = [
            offer for offer in scoped
            if relevance.has_footwear_proof(offer.name or "")
            and relevance.gender_compatible(scope.source_text, offer.name or "")
        ]
    if relevance.request_requires_headphones(scope.source_text):
        scoped = [
            offer for offer in scoped
            if relevance.has_headphone_proof(offer.name or "")
        ]
    feature_proven = [
        offer for offer in scoped
        if relevance.proves_required_features(scope.source_text, offer.name or "")
    ]
    # Si aucun titre ne prouve l’attribut demandé, conserver le scope permet
    # l’abstention contrôlée en aval plutôt qu’une recommandation inventée.
    if feature_proven:
        scoped = feature_proven
    elif relevance.request_has_required_features(scope.source_text):
        return []
    # Les satellites sont légitimes seulement quand les mots de besoin les
    # demandent. Ce filtre intervient après la lecture exhaustive du scope : il
    # ne masque jamais une offre sans avoir vérifié qu’un produit principal est
    # disponible dans ce même univers taxonomique.
    primary = [
        offer for offer in scoped
        if not relevance.is_unrequested_satellite(
            list(request_terms), offer.name or ""
        )
    ]
    if primary:
        scoped = primary
    if relevance.request_describes_collection(scope.source_text):
        # Un kit ne doit pas se réduire à une vis, un piquet ou un adaptateur
        # lorsque le même scope propose un article autonome. La préférence de
        # prix reste disponible si le budget ne permet réellement rien d’autre.
        non_components = [
            offer for offer in scoped
            if not relevance.is_unrequested_component(scope.source_text, offer.name or "")
        ]
        if non_components:
            scoped = non_components
        substantial = [
            offer for offer in scoped
            if offer.price is not None
            and offer.price >= 10.0
            and (budget is None or offer.price <= budget)
        ]
        if substantial:
            scoped = substantial
    strict = [
        offer for offer in scoped
        if _match_proof(scope, offer, request_terms=request_terms) >= relevance.SEUIL
    ]
    # Un sous-rayon taxonomique précis constitue une preuve de nature qui peut
    # suppléer un titre marchand pauvre. Un rayon large ne le permet pas : sans
    # preuve textuelle, recommander un frigo pour « machine à laver » serait une
    # substitution inventée. Dans ce cas, l’abstention est la réponse honnête.
    if not strict and scope.subcategory is None:
        return []
    return sorted(
        strict or scoped,
        key=lambda offer: _rank(scope, offer, request_terms=request_terms),
    )


def compose_general_plan(intent: GeneralIntent, offers: list[CoreOfferSnapshot], *, max_items: int = 3) -> dict[str, object]:
    """Sélectionne des offres prouvées après lecture exhaustive des scopes.

    La fonction ne transforme pas un regroupement d’articles en promesse de style,
    de compatibilité ou de disponibilité future. Elle expose seulement les
    catégories et contraintes que les données observées permettent de vérifier.
    """
    if not intent.resolved:
        return _abstention(intent, "intent_not_resolved", offers)

    selected: list[dict[str, object]] = []
    selected_ids: set[int] = set()
    currency: str | None = None
    total = 0.0
    budget = intent.budget_eur

    ranking_qualifiers = relevance.explicit_qualifier_terms(intent.terms)
    for scope in intent.scopes:
        candidates = _scope_candidates(
            scope,
            offers,
            budget=budget,
            request_terms=ranking_qualifiers,
        )
        if not candidates:
            return _abstention(intent, "no_verified_scope", offers, missing_scope=scope)
        # Une demande multi-produits exige un représentant par scope. Une demande
        # à scope unique peut présenter plusieurs sous-rayons distincts, mais pas
        # plusieurs fois le même article sous prétexte de remplir un kit.
        target = 1 if len(intent.scopes) > 1 else max_items
        represented_subcategories: set[str | None] = set()
        for offer in candidates:
            if len(selected) >= max_items or sum(
                1 for item in selected if item["plan_scope"]["category"] == scope.category
            ) >= target:
                break
            if offer.offer_id in selected_ids:
                continue
            if len(intent.scopes) == 1 and offer.filon_subcategory in represented_subcategories:
                continue
            if currency is not None and offer.currency != currency:
                continue
            if budget is not None and (offer.currency != "EUR" or (offer.price or 0.0) + total > budget):
                continue
            item = offer.as_dict()
            item["role"] = _display_role(offer)
            item["plan_scope"] = {"category": scope.category, "subcategory": scope.subcategory}
            selected.append(item)
            selected_ids.add(offer.offer_id)
            represented_subcategories.add(offer.filon_subcategory)
            currency = offer.currency
            total += offer.price or 0.0
            if len(intent.scopes) > 1:
                break
        if not any(item["plan_scope"]["category"] == scope.category for item in selected):
            return _abstention(intent, "budget_unreachable", offers, missing_scope=scope)

    confidence = 55
    if all(item["availability"] == "in_stock" for item in selected):
        confidence += 20
    if budget is not None and total <= budget:
        confidence += 15
    if len(selected) > 1:
        confidence += 10
    return {
        "decision": "recommend",
        "style_score": None,
        "confidence_score": min(confidence, 100),
        "confidence_band": "high" if confidence >= 80 else "medium",
        "total_known_price": {"amount": round(total, 2), "currency": currency, "scope": "items_only"},
        "delivery": "unknown",
        "items": selected,
        "rationale_keys": ["taxonomy_resolved", "verified_catalog_items", "constraints_checked", *( ["within_known_budget"] if budget is not None and total <= budget else [])],
        "unknowns": ["delivery_unknown", "cross_item_compatibility_not_verified"],
        "rejection_reason": None,
    }


def _abstention(
    intent: GeneralIntent,
    reason: str,
    offers: list[CoreOfferSnapshot],
    *,
    missing_scope: IntentScope | None = None,
) -> dict[str, object]:
    return {
        "decision": "abstain",
        "style_score": None,
        "confidence_score": 0,
        "confidence_band": "low",
        "total_known_price": None,
        "delivery": "unknown",
        "items": [],
        "rationale_keys": ["abstention", reason],
        "unknowns": ["delivery_unknown"],
        "rejection_reason": reason,
        "candidates_considered": len(offers),
        "missing_scope": (
            {"category": missing_scope.category, "subcategory": missing_scope.subcategory}
            if missing_scope is not None
            else None
        ),
    }
