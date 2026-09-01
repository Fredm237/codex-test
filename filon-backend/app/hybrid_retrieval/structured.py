"""Source structurée Hybrid Retrieval, fail-closed et product-first."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from .lexical import lexical_terms


STRUCTURED_ADAPTER_VERSION = "hybrid-structured-ontology/v1"
MAX_STRUCTURED_CANDIDATES = 500
_PRODUCT_TYPES = frozenset({
    "airconditioner", "headphones", "jacket", "laptop", "smartphone", "tyre",
})
_ATTRIBUTE_KEYS = frozenset({"capacity", "color", "memory", "size", "storage"})


class StructuredRetrievalError(ValueError):
    """Entrée structurée invalide."""


@dataclass(frozen=True)
class StructuredIntent:
    product_type: str | None
    constraints: Mapping[str, str]
    specificity_terms: tuple[str, ...]


@dataclass(frozen=True)
class StructuredDocument:
    document_ref: str
    entity_ref: str | None
    product_type: str | None
    product_role: str | None
    attributes: Mapping[str, str]
    offer_ids: tuple[int, ...]


@dataclass(frozen=True)
class StructuredHit:
    entity_ref: str
    source_rank: int
    offer_ids: tuple[int, ...]
    evidence_fields: tuple[str, ...]
    source_type: str = "STRUCTURED"


@dataclass(frozen=True)
class StructuredResult:
    outcome: str
    hits: tuple[StructuredHit, ...]
    reason_codes: tuple[str, ...]
    adapter_version: str = STRUCTURED_ADAPTER_VERSION


def intent_from_query(query: str) -> StructuredIntent:
    terms = lexical_terms(query)
    product_types = [term for term in terms if term in _PRODUCT_TYPES]
    product_type = product_types[0] if len(set(product_types)) == 1 else None
    constraints: dict[str, str] = {}
    for index, term in enumerate(terms[:-1]):
        if term in _ATTRIBUTE_KEYS:
            constraints[term] = terms[index + 1]
    specificity = tuple(
        term
        for term in terms
        if term != product_type and term not in constraints and term not in constraints.values()
    )
    return StructuredIntent(product_type, constraints, specificity)


def retrieve_structured(
    intent: StructuredIntent,
    documents: Sequence[StructuredDocument],
    *,
    limit: int = 50,
) -> StructuredResult:
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_STRUCTURED_CANDIDATES:
        raise StructuredRetrievalError("limit must be between 1 and 500")
    if intent.product_type is None:
        return StructuredResult("ABSTAINED", (), ("intent_unresolved",))
    grouped: dict[str, set[int]] = {}
    unresolved = 0
    for document in documents:
        if not isinstance(document, StructuredDocument):
            raise StructuredRetrievalError("documents must be StructuredDocument values")
        if document.product_type != intent.product_type:
            continue
        if document.product_role not in {None, "PRIMARY_PRODUCT"}:
            continue
        normalized_attributes = {
            str(key).strip().lower(): str(value).strip().lower()
            for key, value in document.attributes.items()
        }
        if any(normalized_attributes.get(key) != value.lower() for key, value in intent.constraints.items()):
            continue
        if document.entity_ref is None:
            unresolved += 1
            continue
        grouped.setdefault(document.entity_ref, set()).update(document.offer_ids)

    # Un scope générique n'est pas un choix de produit, même si la fenêtre
    # structurée courante ne contient qu'une ligne.
    if not intent.specificity_terms and not intent.constraints:
        return StructuredResult("AMBIGUOUS", (), ("ambiguous_intent",))
    if not grouped:
        if unresolved:
            return StructuredResult("AMBIGUOUS", (), ("no_resolved_entity",))
        return StructuredResult("NO_MATCH", (), ("no_match",))
    hits = tuple(
        StructuredHit(
            entity_ref=entity_ref,
            source_rank=index,
            offer_ids=tuple(sorted(offers)),
            evidence_fields=("product_type", *tuple(sorted(intent.constraints))),
        )
        for index, (entity_ref, offers) in enumerate(sorted(grouped.items()), start=1)
        if index <= limit
    )
    return StructuredResult("CANDIDATES", hits, ("retrieval_candidates",))
