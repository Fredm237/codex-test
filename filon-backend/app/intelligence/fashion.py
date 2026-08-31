"""Premier expert de domaine : Fashion Expert pour Outfit Studio.

Le jalon initial est volontairement déterministe. Il ne prétend pas connaître une
matière, une taille ou une silhouette en l’absence de donnée du Core. Il compose
à partir des rôles prouvés par les rayons FILON et explique toute incertitude.
"""

from __future__ import annotations

import math
import re
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from typing import Literal

from app.intelligence.contracts import CoreOfferSnapshot
from app.services import relevance, taxonomy
from app.services.currency import normalize_currency_code
from app.services.freshness import offer_observation_is_fresh

OutfitMode = Literal["create", "complete", "recreate", "optimize", "compare", "discover"]
OutfitRole = Literal["base", "footwear", "accessory"]

_ALLOWED_MODES = frozenset({"create", "complete", "recreate", "optimize", "compare", "discover"})
_BUDGET_PATTERN = re.compile(r"(?:sous|under|budget(?: de)?|moins de|maximum|max)?\s*(\d{2,4})(?:[\s,.]\d{1,2})?\s*(?:€|eur|euro)", re.IGNORECASE)
# Termes produits suffisamment précis pour interroger le catalogue sans confondre
# une intention (« mariage », « minimal ») et un nom d’article marchand.
_ATHLETIC_FOOTWEAR_TERMS = frozenset({
    "running", "run", "basket-ball", "basketball", "football", "futsal", "trail", "cycling", "cyclisme", "vélo", "velo", "ski", "tennis",
})
_CHILD_FOOTWEAR_TERMS = frozenset({
    "enfant", "enfants", "kid", "kids", "child", "children", "junior", "baby", "bebe", "bébé", "kind", "kinder",
})
# La compatibilité professionnelle n’est jamais déduite d’une simple couleur ou
# d’un prix. Les titres doivent porter une preuve utilisable : usage, forme
# formelle, matière de ville ou chaussure de sécurité explicitement annoncée.
_WORK_FOOTWEAR_EVIDENCE = frozenset({
    "travail", "work", "bureau", "office", "business", "professionnel", "professional",
    "formel", "formal", "formeel", "ville", "oxford", "derby", "mocassin", "loafer",
    "escarpin", "pump", "pumps", "cuir", "leather", "leder", "securite", "sécurité", "safety",
})
# Ces marqueurs décrivent un costume ou une tenue à thème, pas une robe de
# soirée ordinaire. Ils restent autorisés uniquement si l’utilisateur les cite.
_THEMED_COSTUME_TERMS = frozenset({
    "costume", "déguisement", "deguisement", "cosplay", "tueur", "killer", "halloween", "carnaval", "carnival",
})
# Une marque peut nommer un gel douche « La Petite Robe Noire ». Ces produits
# d’hygiène ne sont jamais un vêtement, même lorsqu’un mot de mode apparaît.
_NON_WEARABLE_BODYCARE_TERMS = frozenset({
    "shower", "gel", "bodywash", "bath", "bain", "parfum", "perfume", "eau", "shampoo", "shampoing",
    "conditioner", "lotion", "creme", "crème", "serum", "sérum", "deodorant", "déodorant", "soap", "savon",
})

# Les occasions guident le filtre de retrieval mais ne sont pas des pièces :
# leur absence dans un titre ne doit ni pénaliser un blazer réel ni permettre à
# une veste sportive de satisfaire le mot « travail » par défaut.
_OUTFIT_CONTEXT_WORDS = frozenset({
    "mariage", "wedding", "bruiloft", "travail", "work", "bureau", "kantoor",
    "soiree", "soirée", "evening", "avond", "vacances", "holiday", "vakantie",
})

_FOOTWEAR_REQUEST_TERMS = frozenset({
    "schoenen", "chaussure", "chaussures", "shoe", "shoes", "schoen", "sneaker", "sneakers", "basket", "baskets", "boot", "boots", "botte", "bottes",
})
_ACCESSORY_REQUEST_TERMS = frozenset({
    "sac", "sacs", "bag", "bags", "tas", "tassen", "handbag", "handtas", "pochette", "clutch",
})

_PRODUCT_WORDS = frozenset({
    "robe", "dress", "jurk", "veste", "blazer", "jacket", "jas", "manteau",
    "coat", "broek", "pantalon", "pants", "jean", "shirt", "chemise", "hemd",
    "tshirt", "t-shirt", "top", "schoenen", "chaussures", "shoe", "sneaker",
    "basket", "sac", "bag", "tas", "jupe", "skirt", "rok",
})
_BASE_REQUEST_TERMS = _PRODUCT_WORDS - _FOOTWEAR_REQUEST_TERMS - _ACCESSORY_REQUEST_TERMS


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


def _words(value: str | None) -> set[str]:
    """Découpe un texte de demande sans déduire de propriété non présente."""
    return set(re.findall(r"[\wÀ-ÿ'-]+", (value or "").lower()))


def _primary_role_for_intent(intent: FashionIntent) -> OutfitRole:
    """La pièce explicitement demandée devient la base de la recommandation."""
    words = _words(intent.raw_request)
    # Lorsqu’une tenue cite plusieurs pièces, le vêtement principal reste la
    # base. Chaussures et sac ne deviennent principaux que s’ils sont demandés
    # seuls, par exemple « des chaussures noires ».
    if words & _BASE_REQUEST_TERMS:
        return "base"
    if words & _FOOTWEAR_REQUEST_TERMS:
        return "footwear"
    if words & _ACCESSORY_REQUEST_TERMS:
        return "accessory"
    return "base"


def role_of(offer: CoreOfferSnapshot) -> OutfitRole:
    """Rôle fondé sur la taxonomie FILON; pas sur une description imaginée."""
    category = offer.filon_category
    if category == taxonomy.CHAUSSURES:
        return "footwear"
    if category in {taxonomy.ACCESSOIRES, taxonomy.BIJOUX, taxonomy.BAGAGERIE}:
        return "accessory"
    return "base"


def _gender_signal(text: str | None) -> str | None:
    """Signal lexical minimal ; l'absence de signal reste inconnue, jamais déduite."""
    words = set(re.findall(r"[\wÀ-ÿ'-]+", (text or "").lower()))
    feminine = {"femme", "femmes", "woman", "women", "ladies", "dames", "dame"}
    masculine = {"homme", "hommes", "man", "men", "mens", "male", "masculin"}
    if words & feminine:
        return "feminine"
    if words & masculine:
        return "masculine"
    return None


def _is_athletic_footwear(text: str | None) -> bool:
    return bool(_words(text) & _ATHLETIC_FOOTWEAR_TERMS)


def _is_child_footwear(text: str | None) -> bool:
    return bool(_words(text) & _CHILD_FOOTWEAR_TERMS)


def _has_work_footwear_evidence(text: str | None) -> bool:
    return bool(_words(text) & _WORK_FOOTWEAR_EVIDENCE)


def _is_unrequested_themed_costume(request: str, offer_name: str | None) -> bool:
    request_words = _words(request)
    return bool(_words(offer_name) & _THEMED_COSTUME_TERMS) and not bool(request_words & _THEMED_COSTUME_TERMS)


def _is_non_wearable_bodycare(offer_name: str | None) -> bool:
    return bool(_words(offer_name) & _NON_WEARABLE_BODYCARE_TERMS)


def _sports_requested(text: str) -> bool:
    return _is_athletic_footwear(text)


def _is_dress(offer: CoreOfferSnapshot) -> bool:
    return offer.filon_subcategory == "Robes" or bool(
        set(re.findall(r"[\wÀ-ÿ'-]+", (offer.name or "").lower())) & {"robe", "robes", "dress", "dresses", "jurk", "jurken"}
    )


def _compatible_currency(items: list[OutfitItem]) -> str | None:
    currencies = {item.offer.currency for item in items if item.offer.currency}
    return next(iter(currencies)) if len(currencies) == 1 else None


def _normalized_eligible_offer(
    offer: CoreOfferSnapshot,
    *,
    now: datetime | None = None,
) -> CoreOfferSnapshot | None:
    """Ferme la composition aux faits invalides, inconnus ou périmés."""

    price = offer.price
    currency = normalize_currency_code(offer.currency)
    if not (
        price is not None
        and not isinstance(price, bool)
        and math.isfinite(price)
        and price > 0
        and currency is not None
        and offer.availability == "in_stock"
        and offer_observation_is_fresh(offer.observed_at, now=now)
    ):
        return None
    return replace(offer, currency=currency)


def compose_outfit(intent: FashionIntent, offers: list[CoreOfferSnapshot]) -> dict[str, object]:
    """Produit une solution minimale achetable ou une abstention explicable."""
    by_role: dict[OutfitRole, list[CoreOfferSnapshot]] = {"base": [], "footwear": [], "accessory": []}
    reference = datetime.now(UTC)
    for raw_offer in offers:
        offer = _normalized_eligible_offer(raw_offer, now=reference)
        if offer is not None:
            by_role[role_of(offer)].append(offer)
    # Correspondance d'abord, prix ensuite.
    #
    # Le tri portait sur le seul prix croissant, et remontait donc l'article le
    # moins cher du rôle : « Siso Régulateur de hauteur de panneau SHOES » à
    # 0,70 € tenait lieu de chaussure parce que son nom contient « SHOES ».
    # Un article hors sujet ne devient pas juste parce qu'il est bon marché.
    termes = [
        term for term in relevance.mots(intent.raw_request or "")
        if term not in _OUTFIT_CONTEXT_WORDS
    ]

    def _rang(offer: CoreOfferSnapshot) -> tuple:
        pertinence = relevance.score(
            termes, offer.name or "", offer_kind=getattr(offer, "offer_kind", None)
        )
        prix = offer.price if offer.price is not None else float("inf")
        return (-round(pertinence, 1), prix, getattr(offer, "id", None) or offer.offer_id)

    def _eligible(offer: CoreOfferSnapshot) -> bool:
        # Une taxonomie historique peut placer un élément de bricolage dans les
        # chaussures. Le rôle Core reste nécessaire, mais un marqueur d’article
        # satellite non demandé le disqualifie avant toute composition.
        if relevance.is_unrequested_satellite(termes, offer.name or ""):
            return False
        if _is_unrequested_themed_costume(intent.raw_request, offer.name):
            return False
        if _words(intent.raw_request) & _BASE_REQUEST_TERMS and _is_non_wearable_bodycare(offer.name):
            return False
        # « Travail » est une contrainte explicite. FILON n’infère pas qu’une
        # chaussure de futsal ou enfant est professionnelle : sans alternative
        # adulte non sportive documentée, il préfère l’abstention.
        if intent.occasion == "work" and role_of(offer) == "footwear":
            return (
                not (_is_athletic_footwear(offer.name) or _is_child_footwear(offer.name))
                and _has_work_footwear_evidence(offer.name)
            )
        return True

    def _matches_requested_piece(offer: CoreOfferSnapshot, *, fallback_base: bool = False) -> bool:
        # Sans pièce explicite, la requête SQL a déjà réduit le fallback
        # d’occasion à une base documentée. Seule cette pièce principale peut
        # être retenue sans preuve supplémentaire ; les compléments doivent
        # toujours prouver leur caractère cérémoniel dans leur propre titre.
        if not termes:
            if fallback_base:
                return True
            if intent.occasion == "wedding":
                words = set(re.findall(r"[\wÀ-ÿ'-]+", (offer.name or "").lower()))
                return bool(words & {"mariage", "wedding", "bridal", "bride", "cérémonie", "ceremonie", "soirée", "soiree", "evening", "formal", "formel"})
            return False
        # Une pièce complémentaire est optionnelle, mais elle ne doit pas être
        # ajoutée seulement parce qu’elle est classée sous Chaussures ou Accessoires.
        # Elle doit confirmer une pièce explicitement demandée, ou — pour un
        # mariage — porter un marqueur cérémoniel réel dans son propre titre.
        if relevance.score(
            termes, offer.name or "", offer_kind=getattr(offer, "offer_kind", None)
        ) >= relevance.SEUIL:
            return True
        if intent.occasion == "wedding":
            words = set(re.findall(r"[\wÀ-ÿ'-]+", (offer.name or "").lower()))
            return bool(words & {"mariage", "wedding", "bridal", "bride", "cérémonie", "ceremonie", "soirée", "soiree", "evening", "formal", "formel"})
        return False

    for candidates in by_role.values():
        candidates.sort(key=_rang)

    selected: list[OutfitItem] = []
    primary_role = _primary_role_for_intent(intent)
    budget = intent.budget_eur
    # Une catégorie Core seule ne suffit jamais pour la pièce principale : elle
    # doit aussi prouver les caractéristiques produits explicitement demandées.
    # Une chaussure ou un sac explicitement demandé peut légitimement être cette
    # pièce principale ; FILON ne force donc pas une robe ou un blazer absent.
    base = next(
        (
            offer for offer in by_role[primary_role]
            if _eligible(offer)
            and _matches_requested_piece(offer, fallback_base=True)
            # Le budget est une contrainte de sélection, pas seulement un motif
            # d’échec après avoir choisi la première pièce très pertinente. Tous
            # les candidats restent lus et classés, puis la première offre
            # réellement achetable est retenue.
            and (
                budget is None
                or (offer.currency == "EUR" and offer.price is not None and offer.price <= budget)
            )
        ),
        None,
    )
    if base is None:
        return _abstention(intent, "no_verified_base", offers)
    selected.append(OutfitItem(offer=base, role=primary_role))

    currency = base.currency
    running_total = base.price or 0.0
    if budget is not None and (currency != "EUR" or running_total > budget):
        return _abstention(intent, "budget_unreachable", offers)

    # La chaussure complète le look uniquement lorsqu’elle est réellement dans
    # le catalogue, dans la même devise et sous le budget explicite.
    base_gender = _gender_signal(base.name)
    footwear = next(
        (
            offer
            for offer in by_role["footwear"]
            if primary_role != "footwear"
            if _eligible(offer)
            and _matches_requested_piece(offer)
            and offer.currency == currency
            and (
                base_gender is None
                or _gender_signal(offer.name) is None
                or _gender_signal(offer.name) == base_gender
            )
            and (
                not _is_dress(base)
                or _sports_requested(intent.raw_request)
                or not _is_athletic_footwear(offer.name)
            )
            and (budget is None or (offer.price or 0.0) + running_total <= budget)
        ),
        None,
    )
    if footwear is not None:
        candidate_total = running_total + (footwear.price or 0.0)
        if not math.isfinite(candidate_total):
            return _abstention(intent, "non_finite_total", offers)
        selected.append(OutfitItem(offer=footwear, role="footwear"))
        running_total = candidate_total

    accessory = next(
        (
            offer
            for offer in by_role["accessory"]
            if primary_role != "accessory"
            if _eligible(offer)
            and _matches_requested_piece(offer)
            and offer.currency == currency
            and (budget is None or (offer.price or 0.0) + running_total <= budget)
        ),
        None,
    )
    if accessory is not None:
        candidate_total = running_total + (accessory.price or 0.0)
        if not math.isfinite(candidate_total):
            return _abstention(intent, "non_finite_total", offers)
        selected.append(OutfitItem(offer=accessory, role="accessory"))
        running_total = candidate_total

    # Les prix et la disponibilité peuvent être observés. La compatibilité de
    # style, de coupe et d'occasion ne l'est pas dans M1 : elle reste toujours
    # explicitement à confirmer par la personne.
    unknowns = [
        "delivery_unknown",
        "style_compatibility_not_verified",
        "confidence_not_calibrated",
    ]
    if any(item.offer.availability == "unknown" for item in selected):
        unknowns.append("availability_to_verify")
    if intent.occasion is None:
        unknowns.append("occasion_not_specified")
    else:
        unknowns.append("occasion_not_verified")

    return {
        "decision": "recommend",
        # Aucun jeu humain adjudique ne permet encore de calibrer une probabilité
        # de correction. Le précédent score de style ne mesurait que le nombre de
        # rôles couverts et le budget : il ne constituait donc pas une mesure de
        # compatibilité stylistique distincte et supportée.
        "style_score": None,
        "confidence_score": None,
        "confidence_band": "not_calibrated",
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
        "confidence_score": None,
        "confidence_band": "not_calibrated",
        "total_known_price": None,
        "delivery": "unknown",
        "items": [],
        "rationale_keys": ["abstention", reason],
        "unknowns": [
            "delivery_unknown",
            "confidence_not_calibrated",
            *intent.missing_inputs,
        ],
        "rejection_reason": reason,
        "candidates_considered": len(offers),
    }


def _rationale(items: list[OutfitItem], intent: FashionIntent, budget: float | None, total: float) -> list[str]:
    rationale = ["verified_catalog_items", "roles_covered"]
    if budget is not None and total <= budget:
        rationale.append("within_known_budget")
    if intent.occasion is not None:
        rationale.append("occasion_recorded_not_verified")
    if any(item.offer.availability == "unknown" for item in items):
        rationale.append("availability_partially_unknown")
    return rationale
