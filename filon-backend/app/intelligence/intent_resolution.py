"""Résolution générale et explicable d’intentions d’achat vers la taxonomie FILON.

Le module ne possède aucune liste de produits ou de domaines à maintenir. Il
réutilise les règles taxonomiques déjà appliquées au million d’offres pour résoudre
une demande dans les trois langues vers un ou plusieurs rayons FILON.
"""
from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass

from app.llm.base import Message
from app.llm.router import get_router
from app.services import taxonomy

_GENERIC_WORDS = frozenset({
    "un", "une", "des", "le", "la", "les", "de", "du", "pour", "avec", "sans", "et", "and", "en", "met", "with",
    "je", "veux", "cherche", "need", "want", "zoek", "ik", "een", "het", "the", "a", "an", "under", "sous", "onder",
    "budget", "euro", "euros", "eur", "pourquoi", "meilleur", "best", "bon", "bonne", "outfit", "tenue", "kit",
})

_SPLIT_SCOPES = re.compile(r"\s*(?:[,;]|\bet\b|\band\b|\ben\b|\bavec\b|\bwith\b|\bmet\b)\s*", re.IGNORECASE)
# Le néerlandais, l’anglais marchand et l’allemand concatènent souvent le type
# de produit au besoin : « tenniskleding », « campinguitrusting ». Cette étape
# est un découpage linguistique générique, non une règle propre à un rayon.
_COMPOUND_SUFFIXES = ("kleding", "kledij", "uitrusting", "equipment", "accessories", "artikelen", "schoenen", "shoes", "gear")


@dataclass(frozen=True)
class IntentScope:
    category: str
    subcategory: str | None
    source_text: str
    query_terms: tuple[str, ...]


@dataclass(frozen=True)
class GeneralIntent:
    raw_request: str
    locale: str
    scopes: tuple[IntentScope, ...]
    terms: tuple[str, ...]
    required_title_phrases: tuple[str, ...]
    budget_eur: float | None

    @property
    def resolved(self) -> bool:
        return bool(self.scopes)

    def as_dict(self) -> dict[str, object]:
        return {
            "locale": self.locale,
            "terms": list(self.terms),
            "budget_eur": self.budget_eur,
            "required_title_phrases": list(self.required_title_phrases),
            "scopes": [
                {"category": scope.category, "subcategory": scope.subcategory, "query_terms": list(scope.query_terms)}
                for scope in self.scopes
            ],
        }


def _normalize_compounds(value: str) -> str:
    normalized = value.lower()
    for suffix in _COMPOUND_SUFFIXES:
        normalized = re.sub(rf"\b([a-zà-ÿ]{{3,}})({suffix})\b", rf"\1 \2", normalized)
    return normalized


def _tokens(value: str) -> tuple[str, ...]:
    words = re.findall(r"[\wÀ-ÿ'-]{2,}", _normalize_compounds(value))
    return tuple(word for word in words if word not in _GENERIC_WORDS and not word.isdigit())


def _budget(value: str) -> float | None:
    # Les préfixes et symboles monétaires sont obligatoires : « iPhone 15 » n’est
    # jamais un budget, tandis que « sous 600 € » et « under €600 » le sont.
    patterns = (
        r"€\s*(\d{2,5})(?:[,.]\d{1,2})?",
        r"(?:sous|under|onder|budget(?:\s+de)?|maximum|max)\s*(\d{2,5})(?:[,.]\d{1,2})?\s*(?:€|eur|euro)?",
        r"\b(\d{2,5})(?:[,.]\d{1,2})?\s*(?:€|eur|euro)\b",
    )
    for pattern in patterns:
        match = re.search(pattern, value, re.IGNORECASE)
        if match:
            return float(match.group(1))
    return None


def _model_phrases(value: str) -> tuple[str, ...]:
    """Repère un identifiant explicite de forme « nom 15 » sans confondre le budget.

    Cette règle est structurelle : elle protège toutes les gammes numérotées,
    sans connaître les marques ni les familles de produits.
    """
    phrases: list[str] = []
    normalized = _normalize_compounds(value)
    for match in re.finditer(r"\b([a-zà-ÿ][a-zà-ÿ0-9-]{1,})\s+([0-9]{1,4}[a-z]?)\b", normalized):
        prefix, number = match.groups()
        trailing = normalized[match.end(): match.end() + 6]
        if prefix in _GENERIC_WORDS or re.match(r"\s*(?:€|eur|euro)", trailing):
            continue
        phrase = f"{prefix} {number}"
        if phrase not in phrases:
            phrases.append(phrase)
    return tuple(phrases)


def _scope_for(text: str) -> IntentScope | None:
    normalized = _normalize_compounds(text)
    category = taxonomy.classify(None, normalized, None)
    if category is None:
        return None
    subcategory = taxonomy.classify_subcategory(category, name=normalized)
    tokens = _tokens(normalized)
    # Les termes qui résolvent seuls vers le même rayon sont le signal le plus
    # portable entre langues. À défaut, on garde les deux premiers mots utiles
    # de la phrase, sans créer de synonymes propres à un produit.
    category_terms = tuple(
        token for token in tokens
        if taxonomy.classify(None, token, None) == category
        or taxonomy.classify_subcategory(category, name=token) == subcategory and subcategory is not None
    )
    query_terms = category_terms or tokens[:2]
    return IntentScope(
        category=category,
        subcategory=subcategory,
        source_text=text,
        query_terms=query_terms,
    )


def _allowed_scopes() -> dict[str, set[str | None]]:
    return {
        category: {None, *(label for label, _pattern in taxonomy.SUBCATEGORIES.get(category, []))}
        for category in taxonomy.ALL_CATEGORIES
    }


def _parse_semantic_payload(raw: str) -> object:
    value = (raw or "").strip()
    if value.startswith("```"):
        value = value.split("\n", 1)[1] if "\n" in value else ""
        if value.rstrip().endswith("```"):
            value = value.rstrip()[:-3]
    return json.loads(value)


def _semantic_scopes(raw: str, payload: object) -> tuple[IntentScope, ...]:
    if not isinstance(payload, dict) or not isinstance(payload.get("scopes"), list):
        return ()
    allowed = _allowed_scopes()
    scopes: list[IntentScope] = []
    for item in payload["scopes"]:
        if not isinstance(item, dict):
            continue
        category = item.get("category")
        subcategory = item.get("subcategory")
        if not isinstance(category, str) or category not in allowed:
            continue
        if subcategory is not None and (not isinstance(subcategory, str) or subcategory not in allowed[category]):
            continue
        semantic_terms = item.get("keywords")
        if isinstance(semantic_terms, list):
            terms = tuple(
                token.lower().strip() for token in semantic_terms
                if isinstance(token, str) and re.fullmatch(r"[a-zà-ÿ][a-zà-ÿ0-9 -]{1,40}", token.lower().strip())
            )[:8]
        else:
            terms = ()
        scope = IntentScope(
            category=category,
            subcategory=subcategory,
            source_text=raw,
            query_terms=terms or _tokens(raw)[:4],
        )
        if (scope.category, scope.subcategory) not in {(value.category, value.subcategory) for value in scopes}:
            scopes.append(scope)
    return tuple(scopes)


async def resolve_intent_with_fallback(raw_request: str, locale: str = "fr") -> GeneralIntent:
    """Résout d’abord sans modèle, puis utilise un choix taxonomique contraint.

    Le modèle n’invente aucun rayon : il ne peut répondre qu’avec une catégorie
    et une sous-catégorie issues de la taxonomie FILON. Si son JSON est invalide
    ou indisponible, l’abstention déterministe est conservée.
    """
    deterministic = resolve_intent(raw_request, locale)
    # Une catégorie sans sous-rayon est parfois légitime (un besoin sport large),
    # mais elle peut aussi provenir d’un mot ambigu dans une phrase naturelle.
    # Le choix sémantique reste donc contraint aux scopes FILON et peut préciser
    # ce cas ; une réponse vide laisse intacte la résolution déterministe.
    needs_semantic_check = not deterministic.resolved or all(
        scope.subcategory is None for scope in deterministic.scopes
    )
    if not needs_semantic_check:
        return deterministic
    allowed = _allowed_scopes()
    choices = [
        {"category": category, "subcategories": sorted(value for value in subcategories if value is not None)}
        for category, subcategories in allowed.items()
    ]
    messages = [
        Message(
            role="system",
            content=(
                "Classifie uniquement l’intention d’achat vers les catégories FILON fournies. "
                "Réponds en JSON strict {\\\"scopes\\\":[{\\\"category\\\":string,\\\"subcategory\\\":string|null,\\\"keywords\\\":[string]}]}. "
                "Les keywords sont au plus huit termes concrets, multilingues si nécessaire, décrivant les articles utiles au besoin ; ils servent seulement à classer les offres du scope. "
                "N’invente aucune catégorie ni sous-catégorie ; renvoie scopes vide si aucun choix n’est défendable."
            ),
        ),
        Message(role="user", content=f"Langue: {locale}. Demande: {raw_request}. Choix autorisés: {json.dumps(choices, ensure_ascii=False)}"),
    ]
    try:
        provider = get_router().for_task("default")
        if provider.name == "mock":
            return deterministic
        raw = await asyncio.wait_for(provider.complete_json(messages, temperature=0.0), timeout=8.0)
        scopes = _semantic_scopes(raw_request, _parse_semantic_payload(raw))
    except (asyncio.TimeoutError, ValueError, TypeError, json.JSONDecodeError):
        scopes = ()
    except Exception:
        scopes = ()
    if not scopes:
        return deterministic
    if deterministic.resolved:
        # Un seul remplacement d’un scope lexical large est admissible : il peut
        # lever une ambiguïté réelle (p. ex. « machine à café » mal rangée dans
        # Alimentation vers Petit électroménager). À l’inverse, un éclatement en
        # plusieurs univers voisins traduit une hypothèse d’usage non formulée
        # (« tennis clothing » → homme, femme et chaussures) ; dans ce cas, la
        # continuité taxonomique déterministe prévaut.
        may_replace_single_broad_scope = (
            len(deterministic.scopes) == 1
            and deterministic.scopes[0].subcategory is None
            and len(scopes) == 1
        )
        if may_replace_single_broad_scope:
            original = deterministic.scopes[0]
            candidate = scopes[0]
            # À catégorie identique, un sous-rayon proposé par le modèle doit
            # déjà être démontrable depuis le texte par la taxonomie. Sans cela,
            # « tennis clothing » pourrait devenir arbitrairement Running ; le
            # scope large prouvé reste alors la seule base vérifiable.
            taxonomic_subcategory = taxonomy.classify_subcategory(
                original.category,
                name=_normalize_compounds(raw_request),
            )
            if (
                candidate.category == original.category
                and candidate.subcategory is not None
                and candidate.subcategory != taxonomic_subcategory
            ):
                scopes = deterministic.scopes
        else:
            refined: list[IntentScope] = []
            for original in deterministic.scopes:
                semantic = next(
                    (
                        candidate for candidate in scopes
                        if candidate.category == original.category
                        and (original.subcategory is None or candidate.subcategory == original.subcategory)
                    ),
                    None,
                )
                refined.append(semantic or original)
            scopes = tuple(refined)
    return GeneralIntent(
        raw_request=deterministic.raw_request,
        locale=deterministic.locale,
        scopes=scopes,
        terms=deterministic.terms,
        required_title_phrases=deterministic.required_title_phrases,
        budget_eur=deterministic.budget_eur,
    )


def resolve_intent(raw_request: str, locale: str = "fr") -> GeneralIntent:
    """Résout le texte complet puis chacun de ses segments en rayons FILON.

    Une demande multi-produit conserve plusieurs scopes. Aucun scope ne se crée si
    la taxonomie ne reconnaît pas la formulation : l’appelant peut alors s’abstenir
    explicitement plutôt que d’ouvrir tout le catalogue sur un mot ambigu.
    """
    raw = " ".join((raw_request or "").split())
    candidates = [raw, *[part for part in _SPLIT_SCOPES.split(raw) if part]]
    scopes: list[IntentScope] = []
    seen: set[tuple[str, str | None]] = set()
    for candidate in candidates:
        scope = _scope_for(candidate)
        if scope is None:
            continue
        key = (scope.category, scope.subcategory)
        if key not in seen:
            seen.add(key)
            scopes.append(scope)
    return GeneralIntent(
        raw_request=raw,
        locale=locale if locale in {"fr", "nl", "en"} else "fr",
        scopes=tuple(scopes),
        terms=_tokens(raw),
        required_title_phrases=_model_phrases(raw),
        budget_eur=_budget(raw),
    )
