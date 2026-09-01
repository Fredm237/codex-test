"""Adaptateur lexical product-first, déterministe et borné.

La voie SQL utilise directement ``ILIKE`` sur les colonnes indexées par
``pg_trgm``. La voie pure partage la même normalisation avec le Quality Lab et
permet de qualifier le comportement sans base ni changement du lecteur public.
"""

from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import dataclass
from typing import Mapping, Sequence


LEXICAL_ADAPTER_VERSION = "hybrid-lexical-pgtrgm/v1"
LEXICAL_NORMALIZATION_VERSION = "hybrid-lexical-normalization/v1"
MAX_QUERY_TERMS = 12
MAX_CANDIDATES = 500

_TOKEN = re.compile(r"[a-z0-9]+(?:[/.-][a-z0-9]+)*")
_STOPWORDS = frozenset({
    "a", "an", "and", "avec", "de", "des", "du", "een", "en", "et",
    "for", "het", "la", "le", "les", "met", "of", "pour", "the", "un",
    "une", "van", "voor", "with",
})
_ALIASES = {
    "telephone": "smartphone",
    "telefoon": "smartphone",
    "phone": "smartphone",
    "smartphone": "smartphone",
    "ordinateur": "laptop",
    "portable": "laptop",
    "notebook": "laptop",
    "laptop": "laptop",
    "casque": "headphones",
    "koptelefoon": "headphones",
    "headphone": "headphones",
    "headphones": "headphones",
    "veste": "jacket",
    "jas": "jacket",
    "jacket": "jacket",
    "climatiseur": "airconditioner",
    "airco": "airconditioner",
    "airconditioner": "airconditioner",
    "pneu": "tyre",
    "band": "tyre",
    "tyre": "tyre",
}
_ATTRIBUTE_KEYS = frozenset({"capacity", "color", "memory", "size", "storage"})
_ACCESSORY_TERMS = frozenset({
    "adapter", "bag", "case", "cover", "filter", "protective", "replacement",
})


class LexicalRetrievalError(ValueError):
    """Entrée lexicale invalide : l'adaptateur échoue fermé."""


@dataclass(frozen=True)
class LexicalDocument:
    document_ref: str
    entity_ref: str | None
    brand: str | None
    model: str | None
    product_type: str | None
    product_role: str | None
    attributes: Mapping[str, str]
    offer_ids: tuple[int, ...]


@dataclass(frozen=True)
class LexicalHit:
    entity_ref: str
    score: float
    source_rank: int
    offer_ids: tuple[int, ...]
    evidence_fields: tuple[str, ...]
    source_type: str = "LEXICAL"
    score_semantics: str = "deterministic_token_coverage"


@dataclass(frozen=True)
class LexicalResult:
    outcome: str
    hits: tuple[LexicalHit, ...]
    reason_codes: tuple[str, ...]
    adapter_version: str = LEXICAL_ADAPTER_VERSION


def _fold(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    return "".join(character for character in normalized if not unicodedata.combining(character)).lower()


def _tokens(value: str) -> tuple[str, ...]:
    tokens: list[str] = []
    folded = _fold(value).replace("air conditioner", "airconditioner")
    for raw in _TOKEN.findall(folded):
        if raw in _STOPWORDS:
            continue
        canonical = _ALIASES.get(raw, raw)
        if canonical not in tokens:
            tokens.append(canonical)
        if len(tokens) == MAX_QUERY_TERMS:
            break
    return tuple(tokens)


def lexical_terms(query: str) -> tuple[str, ...]:
    if not isinstance(query, str):
        raise LexicalRetrievalError("query must be a string")
    terms = _tokens(query.strip())
    if not terms:
        raise LexicalRetrievalError("query has no lexical term")
    return terms


def _attribute_constraints(query: str) -> dict[str, str]:
    raw = _TOKEN.findall(_fold(query))
    constraints: dict[str, str] = {}
    for index, token in enumerate(raw[:-1]):
        if token in _ATTRIBUTE_KEYS:
            constraints[token] = _ALIASES.get(raw[index + 1], raw[index + 1])
    return constraints


def _document_surface(document: LexicalDocument) -> tuple[tuple[str, ...], dict[str, str]]:
    attributes = {
        _fold(str(key)): _fold(str(value))
        for key, value in document.attributes.items()
        if str(key).strip() and str(value).strip()
    }
    joined = " ".join(filter(None, (document.brand, document.model, document.product_type)))
    joined += " " + " ".join(f"{key} {value}" for key, value in attributes.items())
    return _tokens(joined), attributes


def _score(query: str, terms: tuple[str, ...], document: LexicalDocument) -> tuple[float, tuple[str, ...]] | None:
    if (
        document.product_role not in {None, "PRIMARY_PRODUCT"}
        and not set(terms).intersection(_ACCESSORY_TERMS)
    ):
        return None
    document_terms, attributes = _document_surface(document)
    constraints = _attribute_constraints(query)
    if any(attributes.get(key) != value for key, value in constraints.items()):
        return None
    overlap = tuple(term for term in terms if term in document_terms)
    coverage = len(overlap) / len(terms)
    folded_query = _fold(query)
    model = _fold(document.model or "").strip()
    brand = _fold(document.brand or "").strip()
    exact_model = bool(model and model in folded_query)
    exact_brand = bool(brand and brand in folded_query)
    if coverage < 0.5 and not exact_model:
        return None
    score = coverage * 10.0 + (8.0 if exact_model else 0.0) + (2.0 if exact_brand else 0.0)
    evidence: list[str] = ["tokens"]
    if exact_model:
        evidence.append("model")
    if exact_brand:
        evidence.append("brand")
    if constraints:
        evidence.append("attributes")
    return score, tuple(evidence)


def retrieve_lexical(
    query: str,
    documents: Sequence[LexicalDocument],
    *,
    limit: int = 50,
) -> LexicalResult:
    """Retourne une fenêtre product-first sans inventer d'identité."""

    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_CANDIDATES:
        raise LexicalRetrievalError("limit must be between 1 and 500")
    terms = lexical_terms(query)
    grouped: dict[str, dict[str, object]] = {}
    unresolved_matches = 0
    for document in documents:
        if not isinstance(document, LexicalDocument):
            raise LexicalRetrievalError("documents must be LexicalDocument values")
        scored = _score(query, terms, document)
        if scored is None:
            continue
        if document.entity_ref is None:
            unresolved_matches += 1
            continue
        score, evidence = scored
        current = grouped.setdefault(
            document.entity_ref,
            {"score": score, "offers": set(), "evidence": set()},
        )
        current["score"] = max(float(current["score"]), score)
        current["offers"].update(document.offer_ids)  # type: ignore[union-attr]
        current["evidence"].update(evidence)  # type: ignore[union-attr]

    ranked = sorted(grouped.items(), key=lambda item: (-float(item[1]["score"]), item[0]))
    # Une requête réduite à un type générique ne départage pas plusieurs
    # entités. Renvoyer AMBIGUOUS empêche le premier prix ou le premier marchand
    # de devenir implicitement la réponse.
    if len(terms) == 1 and len(ranked) > 1:
        return LexicalResult("AMBIGUOUS", (), ("ambiguous_intent",))
    if not ranked:
        if unresolved_matches:
            return LexicalResult("AMBIGUOUS", (), ("no_resolved_entity",))
        return LexicalResult("NO_MATCH", (), ("no_match",))

    hits = tuple(
        LexicalHit(
            entity_ref=entity_ref,
            score=round(float(payload["score"]), 8),
            source_rank=index,
            offer_ids=tuple(sorted(payload["offers"])),  # type: ignore[arg-type]
            evidence_fields=tuple(sorted(payload["evidence"])),  # type: ignore[arg-type]
        )
        for index, (entity_ref, payload) in enumerate(ranked[:limit], start=1)
    )
    return LexicalResult("CANDIDATES", hits, ("retrieval_candidates",))


def build_offer_lexical_statement(query: str, *, limit: int = 50):
    """Construit la requête PostgreSQL bornée, sans exécuter ni hydrater.

    PostgreSQL compile ``Column.ilike`` en ``ILIKE`` sur la colonne brute ; le
    GIN ``gin_trgm_ops`` existant reste donc utilisable, contrairement à
    ``lower(column) LIKE``.
    """

    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_CANDIDATES:
        raise LexicalRetrievalError("limit must be between 1 and 500")
    terms = lexical_terms(query)
    from sqlalchemy import and_, or_, select

    from app.db.models import Offer

    clauses = [
        or_(Offer.name.ilike(f"%{term}%"), Offer.brand.ilike(f"%{term}%"))
        for term in terms
    ]
    return (
        select(
            Offer.id,
            Offer.product_id,
            Offer.name,
            Offer.brand,
            Offer.merchant_id,
        )
        .where(
            and_(
                *clauses,
                Offer.is_canonical.is_(True),
                Offer.is_adult.is_(False),
                Offer.product_id.isnot(None),
            )
        )
        .limit(limit)
    )
