"""Premier expert de domaine : Fashion Expert pour Outfit Studio.

Le jalon initial est volontairement déterministe. Il ne prétend pas connaître une
matière, une taille ou une silhouette en l’absence de donnée du Core. Il compose
à partir des rôles prouvés par les rayons FILON et explique toute incertitude.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Literal

from app.intelligence.contracts import CoreOfferSnapshot
from app.services import taxonomy

OutfitMode = Literal["create", "complete", "recreate", "optimize", "compare", "discover"]
OutfitRole = Literal["base", "footwear", "accessory"]

_ALLOWED_MODES = frozenset({"create", "complete", "recreate", "optimize", "compare", "discover"})
_BUDGET_PATTERN = re.compile(r"(?:sous|under|budget(?: de)?|moins de|maximum|max)?\s*(\d{2,4})(?:[\s,.]\d{1,2})?\s*(?:€|eur|euro)", re.IGNORECASE)
# Termes produits suffisamment précis pour interroger le catalogue sans confondre
# une intention (« mariage », « minimal ») et un nom d’article marchand.
_PRODUCT_WORDS = frozenset({
    "robe", "dress", "jurk", "veste", "blazer", "jacket", "jas", "manteau",
    "coat", "broek", "pantalon", "pants", "jean", "shirt", "chemise", "hemd",
    "tshirt", "t-shirt", "top", "schoenen", "chaussures", "shoe", "sneaker",
    "basket", "sac", "bag", "tas", "jupe", "skirt", "rok",
})


@dataclass(frozen=True)
class FashionIntent:
    mode: OutfitMode
    raw_request: str
    budget_eur: float | None
    occasion: str | None
    style_hints: tuple[str, ...]
    color_hints: tuple[str, ...]
    missing_inputs: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class OutfitItem:
    offer: CoreOfferSnapshot
    role: OutfitRole

    def as_dict(self) -> dict[str, object]:
        payload = self.offer.as_dict()
        payload["role"] = self.role
        return payload


def retrieval_query_for_intent(raw_request: str) -> str | None:
    """Ne transmet au catalogue que les mots décrivant explicitement une pièce."""
    words = re.findall(r"[\wÀ-ÿ'-]+", (raw_request or "").lower())
    selected = [word for word in words if word in _PRODUCT_WORDS]
    return " ".join(selected) or None


def parse_fashion_intent(raw_request: str, requested_mode: str | None = None) -> FashionIntent:
    """Extrait seulement les contraintes lexicalement explicites.

    Tout élément non reconnu reste du texte de demande. Cette prudence évite de
    présenter une interprétation LLM ou stylistique comme une donnée utilisateur.
    """
    text = " ".join((raw_request or "").strip().split())
    folded = text.lower()
    mode = requested_mode if requested_mode in _ALLOWED_MODES else "create"
    if any(word in folded for word in ("compléter", "complete", "aanvullen")):
        mode = "complete"
    elif any(word in folded for word in ("recréer", "recreate", "nabootsen")):
        mode = "recreate"
    elif any(word in folded for word in ("optimiser", "optimize", "optimaliseer")):
        mode = "optimize"
    elif any(word in folded for word in ("comparer", "compare", "vergelijk")):
        mode = "compare"
    elif any(word in folded for word in ("inspir", "discover", "ontdek")):
        mode = "discover"

    budget_match = _BUDGET_PATTERN.search(folded)
    budget = float(budget_match.group(1)) if budget_match else None

    occasion = next(
        (
            value
            for value, terms in {
                "wedding": ("mariage", "wedding", "bruiloft"),
                "work": ("travail", "work", "bureau", "kantoor"),
                "evening": ("soirée", "soiree", "evening", "avond"),
                "holiday": ("vacances", "holiday", "vakantie"),
            }.items()
            if any(term in folded for term in terms)
        ),
        None,
    )
    styles = tuple(
        value
        for value, terms in {
            "minimal": ("minimal", "minimaal"),
            "casual": ("casual",),
            "formal": ("formel", "formal", "formeel", "chic"),
            "street": ("street", "streetwear"),
        }.items()
        if any(term in folded for term in terms)
    )
    colors = tuple(
        color
        for color in ("black", "white", "blue", "green", "red", "brown", "beige", "grey")
        if any(term in folded for term in _color_terms(color))
    )
    missing = tuple(
        field
        for field, provided in (("budget", budget is not None), ("occasion", occasion is not None))
        if not provided
    )
    return FashionIntent(
        mode=mode,  # type: ignore[arg-type]
        raw_request=text,
        budget_eur=budget,
        occasion=occasion,
        style_hints=styles,
        color_hints=colors,
        missing_inputs=missing,
    )


def _color_terms(color: str) -> tuple[str, ...]:
    return {
        "black": ("noir", "black", "zwart"),
        "white": ("blanc", "white", "wit"),
        "blue": ("bleu", "blue", "blauw"),
        "green": ("vert", "green", "groen"),
        "red": ("rouge", "red", "rood"),
        "brown": ("marron", "brun", "brown", "bruin"),
        "beige": ("beige",),
        "grey": ("gris", "grey", "gray", "grijs"),
    }[color]


def role_of(offer: CoreOfferSnapshot) -> OutfitRole:
    """Rôle fondé sur la taxonomie FILON; pas sur une description imaginée."""
    category = offer.filon_category
    if category == taxonomy.CHAUSSURES:
        return "footwear"
    if category in {taxonomy.ACCESSOIRES, taxonomy.BIJOUX, taxonomy.BAGAGERIE}:
        return "accessory"
    return "base"


def _compatible_currency(items: list[OutfitItem]) -> str | None:
    currencies = {item.offer.currency for item in items if item.offer.currency}
    return next(iter(currencies)) if len(currencies) == 1 else None


def compose_outfit(intent: FashionIntent, offers: list[CoreOfferSnapshot]) -> dict[str, object]:
    """Produit une solution minimale achetable ou une abstention explicable."""
    by_role: dict[OutfitRole, list[CoreOfferSnapshot]] = {"base": [], "footwear": [], "accessory": []}
    for offer in offers:
        by_role[role_of(offer)].append(offer)
    for candidates in by_role.values():
        candidates.sort(key=lambda offer: (offer.price if offer.price is not None else float("inf"), offer.id if hasattr(offer, "id") else offer.offer_id))

    selected: list[OutfitItem] = []
    base = by_role["base"][0] if by_role["base"] else None
    if base is None:
        return _abstention(intent, "no_verified_base", offers)
    selected.append(OutfitItem(offer=base, role="base"))

    currency = base.currency
    budget = intent.budget_eur
    running_total = base.price or 0.0
    if budget is not None and (currency != "EUR" or running_total > budget):
        return _abstention(intent, "budget_unreachable", offers)

    # La chaussure complète le look uniquement lorsqu’elle est réellement dans
    # le catalogue, dans la même devise et sous le budget explicite.
    footwear = next(
        (
            offer
            for offer in by_role["footwear"]
            if offer.currency == currency
            and (budget is None or (offer.price or 0.0) + running_total <= budget)
        ),
        None,
    )
    if footwear is not None:
        selected.append(OutfitItem(offer=footwear, role="footwear"))
        running_total += footwear.price or 0.0

    accessory = next(
        (
            offer
            for offer in by_role["accessory"]
            if offer.currency == currency
            and (budget is None or (offer.price or 0.0) + running_total <= budget)
        ),
        None,
    )
    if accessory is not None:
        selected.append(OutfitItem(offer=accessory, role="accessory"))
        running_total += accessory.price or 0.0

    confidence = _confidence(selected)
    style = _style_score(selected, intent, budget, running_total)
    unknowns = ["delivery_unknown"]
    if any(item.offer.availability == "unknown" for item in selected):
        unknowns.append("availability_to_verify")
    if intent.occasion is None:
        unknowns.append("occasion_not_specified")

    return {
        "decision": "recommend",
        "style_score": style,
        "confidence_score": confidence,
        "confidence_band": "high" if confidence >= 80 else "medium" if confidence >= 55 else "low",
        "total_known_price": {"amount": round(running_total, 2), "currency": currency, "scope": "items_only"},
        "delivery": "unknown",
        "items": [item.as_dict() for item in selected],
        "rationale_keys": _rationale(selected, intent, budget, running_total),
        "unknowns": unknowns,
        "rejection_reason": None,
    }


def _abstention(intent: FashionIntent, reason: str, offers: list[CoreOfferSnapshot]) -> dict[str, object]:
    return {
        "decision": "abstain",
        "style_score": None,
        "confidence_score": 0,
        "confidence_band": "low",
        "total_known_price": None,
        "delivery": "unknown",
        "items": [],
        "rationale_keys": ["abstention", reason],
        "unknowns": ["delivery_unknown", *intent.missing_inputs],
        "rejection_reason": reason,
        "candidates_considered": len(offers),
    }


def _confidence(items: list[OutfitItem]) -> int:
    if not items:
        return 0
    score = 45  # prix, marchand et catégorie Core de toutes les pièces.
    score += 20  # toutes les pièces ont un prix et une devise par contrat.
    if all(item.offer.availability == "in_stock" for item in items):
        score += 20
    elif any(item.offer.availability == "unknown" for item in items):
        score += 5
    if len(items) >= 2:
        score += 15
    return min(score, 100)


def _style_score(items: list[OutfitItem], intent: FashionIntent, budget: float | None, total: float) -> int:
    roles = {item.role for item in items}
    score = 35  # base présente
    if "footwear" in roles:
        score += 25
    if "accessory" in roles:
        score += 10
    if budget is not None and total <= budget:
        score += 20
    if intent.occasion is not None:
        score += 10
    return min(score, 100)


def _rationale(items: list[OutfitItem], intent: FashionIntent, budget: float | None, total: float) -> list[str]:
    rationale = ["verified_catalog_items", "roles_covered"]
    if budget is not None and total <= budget:
        rationale.append("within_known_budget")
    if intent.occasion is not None:
        rationale.append("occasion_explicitly_considered")
    if any(item.offer.availability == "unknown" for item in items):
        rationale.append("availability_partially_unknown")
    return rationale
