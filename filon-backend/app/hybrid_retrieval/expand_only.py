"""Agrégation P5E des sources, avant la fusion/ranking P5F."""

from __future__ import annotations

from dataclasses import dataclass

from .lexical import LexicalResult
from .semantic import SemanticResult
from .structured import StructuredResult


EXPAND_ONLY_VERSION = "hybrid-expand-only/v1"


@dataclass(frozen=True)
class ExpandedCandidate:
    entity_ref: str
    offer_ids: tuple[int, ...]
    source_types: tuple[str, ...]


@dataclass(frozen=True)
class ExpandOnlyResult:
    outcome: str
    candidates: tuple[ExpandedCandidate, ...]
    reason_codes: tuple[str, ...]
    version: str = EXPAND_ONLY_VERSION


def combine_expand_only(
    lexical: LexicalResult,
    structured: StructuredResult,
    semantic: SemanticResult,
) -> ExpandOnlyResult:
    """Union sourcée sans score inter-source et sans promotion semantic-only."""

    grouped: dict[str, dict[str, set]] = {}
    for hit in lexical.hits:
        payload = grouped.setdefault(hit.entity_ref, {"offers": set(), "sources": set()})
        payload["offers"].update(hit.offer_ids)
        payload["sources"].add("LEXICAL")
    for hit in structured.hits:
        payload = grouped.setdefault(hit.entity_ref, {"offers": set(), "sources": set()})
        payload["offers"].update(hit.offer_ids)
        payload["sources"].add("STRUCTURED")
    for hit in semantic.hits:
        if hit.entity_ref is None:
            continue
        payload = grouped.setdefault(hit.entity_ref, {"offers": set(), "sources": set()})
        payload["offers"].update(hit.offer_ids)
        payload["sources"].add("SEMANTIC")

    generic_ambiguity = lexical.outcome == "AMBIGUOUS" or structured.outcome == "AMBIGUOUS"
    unresolved_semantic = any(hit.entity_ref is None for hit in semantic.hits)
    if generic_ambiguity and not lexical.hits:
        return ExpandOnlyResult("AMBIGUOUS", (), ("ambiguous_intent",))
    if grouped:
        candidates = tuple(
            ExpandedCandidate(
                entity_ref=entity_ref,
                offer_ids=tuple(sorted(payload["offers"])),
                source_types=tuple(sorted(payload["sources"])),
            )
            for entity_ref, payload in sorted(grouped.items())
        )
        return ExpandOnlyResult("CANDIDATES", candidates, ("retrieval_candidates",))
    if unresolved_semantic:
        return ExpandOnlyResult(
            "AMBIGUOUS",
            (),
            ("no_resolved_entity", "semantic_abstained"),
        )
    return ExpandOnlyResult("NO_MATCH", (), ("no_match",))
