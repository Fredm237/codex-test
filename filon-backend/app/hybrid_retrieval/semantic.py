"""Source sémantique optionnelle, expand-only et sans pouvoir identitaire."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Sequence


SEMANTIC_ADAPTER_VERSION = "hybrid-semantic-expand-only/v1"
MAX_SEMANTIC_CANDIDATES = 500
_HARD_IDENTIFIER = re.compile(r"\b[A-Z0-9]{3,}\b")
_HINTS = {
    "comfortable": "headphones",
    "quiet": "headphones",
    "noise": "headphones",
    "silencieux": "headphones",
    "confortable": "headphones",
    "comfortabel": "headphones",
    "stil": "headphones",
}
_TYPE_ALIASES = {
    "airco": "air conditioner",
    "climatiseur": "air conditioner",
    "conditioner": "air conditioner",
    "smartphone": "smartphone",
    "telephone": "smartphone",
    "telefoon": "smartphone",
    "phone": "smartphone",
    "laptop": "laptop",
    "ordinateur": "laptop",
    "portable": "laptop",
    "headphones": "headphones",
    "casque": "headphones",
    "koptelefoon": "headphones",
    "jacket": "jacket",
    "veste": "jacket",
    "jas": "jacket",
    "tyre": "tyre",
    "pneu": "tyre",
    "band": "tyre",
}


class SemanticRetrievalError(ValueError):
    """Entrée sémantique invalide."""


@dataclass(frozen=True)
class SemanticDocument:
    document_ref: str
    entity_ref: str | None
    product_type: str | None
    offer_ids: tuple[int, ...]


@dataclass(frozen=True)
class SemanticHit:
    entity_ref: str | None
    candidate_status: str
    score: float
    source_rank: int
    offer_ids: tuple[int, ...]
    source_type: str = "SEMANTIC"
    score_semantics: str = "deterministic_semantic_proxy"


@dataclass(frozen=True)
class SemanticResult:
    outcome: str
    hits: tuple[SemanticHit, ...]
    reason_codes: tuple[str, ...]
    adapter_version: str = SEMANTIC_ADAPTER_VERSION


def _fold(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    return "".join(character for character in normalized if not unicodedata.combining(character)).lower()


def retrieve_semantic(
    query: str,
    documents: Sequence[SemanticDocument],
    *,
    limit: int = 50,
) -> SemanticResult:
    if not isinstance(query, str) or not query.strip():
        raise SemanticRetrievalError("query must be non-empty")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_SEMANTIC_CANDIDATES:
        raise SemanticRetrievalError("limit must be between 1 and 500")
    # Une référence explicite inconnue ne peut jamais être diluée en voisinage
    # sémantique. Elle appartient au lexical exact ou au no-match.
    if _HARD_IDENTIFIER.search(query):
        return SemanticResult("ABSTAINED", (), ("semantic_abstained",))
    words = set(re.findall(r"[a-z0-9]+", _fold(query)))
    concepts = {_HINTS[word] for word in words if word in _HINTS}
    if not concepts:
        return SemanticResult("ABSTAINED", (), ("semantic_abstained",))
    # Une préférence sémantique explicite peut être rattachée au type nommé
    # dans la requête. Le type reste observé ; il n'est pas inventé par le proxy.
    concepts.update(_TYPE_ALIASES[word] for word in words if word in _TYPE_ALIASES)
    hits: list[SemanticHit] = []
    for document in documents:
        if not isinstance(document, SemanticDocument):
            raise SemanticRetrievalError("documents must be SemanticDocument values")
        if document.product_type not in concepts:
            continue
        hits.append(
            SemanticHit(
                entity_ref=document.entity_ref,
                candidate_status=("ELIGIBLE_SHADOW" if document.entity_ref else "QUARANTINED"),
                score=0.75,
                source_rank=len(hits) + 1,
                offer_ids=document.offer_ids if document.entity_ref else (),
            )
        )
        if len(hits) == limit:
            break
    if not hits:
        return SemanticResult("ABSTAINED", (), ("semantic_abstained",))
    return SemanticResult("EXPANDED", tuple(hits), ("retrieval_candidates",))
