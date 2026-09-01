"""Reciprocal Rank Fusion product-first, reproductible et sourcée."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Mapping, Sequence


FUSION_VERSION = "hybrid-rrf-product-first/v1"
RRF_K = 60
MAX_FUSED_CANDIDATES = 500
SOURCE_TYPES = frozenset({"LEXICAL", "STRUCTURED", "SEMANTIC"})


class FusionError(ValueError):
    """Entrée de fusion hors contrat."""


@dataclass(frozen=True)
class FusionSourceHit:
    source_type: str
    source_rank: int
    entity_ref: str | None
    offer_ids: tuple[int, ...]
    evidence_ref: str


@dataclass(frozen=True)
class FusedSourceEvidence:
    source_type: str
    source_rank: int
    evidence_ref: str


@dataclass(frozen=True)
class FusedCandidate:
    candidate_rank: int
    entity_ref: str
    rrf_score: float
    offer_ids: tuple[int, ...]
    source_evidence: tuple[FusedSourceEvidence, ...]


@dataclass(frozen=True)
class FusionResult:
    outcome: str
    candidates: tuple[FusedCandidate, ...]
    reason_codes: tuple[str, ...]
    unresolved_hits: int
    result_digest: str
    fusion_version: str = FUSION_VERSION


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _validate_hit(hit: FusionSourceHit) -> None:
    if hit.source_type not in SOURCE_TYPES:
        raise FusionError("source type is invalid")
    if isinstance(hit.source_rank, bool) or not isinstance(hit.source_rank, int) or hit.source_rank < 1:
        raise FusionError("source rank is invalid")
    if hit.entity_ref is not None and (not isinstance(hit.entity_ref, str) or not hit.entity_ref):
        raise FusionError("entity ref is invalid")
    if not isinstance(hit.evidence_ref, str) or not hit.evidence_ref:
        raise FusionError("evidence ref is required")
    if any(isinstance(value, bool) or not isinstance(value, int) or value < 1 for value in hit.offer_ids):
        raise FusionError("offer ids are invalid")
    if hit.entity_ref is None and hit.offer_ids:
        raise FusionError("unresolved hit cannot attach offers")


def reciprocal_rank_fusion(
    hits: Sequence[FusionSourceHit],
    *,
    query_digest: str,
    snapshot_ref: str,
    index_versions: Mapping[str, str],
    ambiguity_guard: bool = False,
    limit: int = 50,
) -> FusionResult:
    """Fusionne les rangs par entité, jamais les scores bruts entre sources."""

    if not isinstance(query_digest, str) or not query_digest.startswith("sha256:") or len(query_digest) != 71:
        raise FusionError("query digest is invalid")
    if not isinstance(snapshot_ref, str) or not snapshot_ref:
        raise FusionError("snapshot ref is required")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_FUSED_CANDIDATES:
        raise FusionError("limit must be between 1 and 500")
    if not isinstance(index_versions, Mapping) or any(
        source not in SOURCE_TYPES or not isinstance(version, str) or not version
        for source, version in index_versions.items()
    ):
        raise FusionError("index versions are invalid")

    grouped: dict[str, dict[str, object]] = {}
    unresolved = 0
    for hit in hits:
        if not isinstance(hit, FusionSourceHit):
            raise FusionError("hits must be FusionSourceHit values")
        _validate_hit(hit)
        if hit.entity_ref is None:
            unresolved += 1
            continue
        payload = grouped.setdefault(
            hit.entity_ref,
            {"offers": set(), "by_source": {}},
        )
        payload["offers"].update(hit.offer_ids)  # type: ignore[union-attr]
        by_source: dict[str, FusionSourceHit] = payload["by_source"]  # type: ignore[assignment]
        current = by_source.get(hit.source_type)
        if current is None or hit.source_rank < current.source_rank:
            by_source[hit.source_type] = hit

    digest_input = {
        "fusion_version": FUSION_VERSION,
        "rrf_k": RRF_K,
        "query_digest": query_digest,
        "snapshot_ref": snapshot_ref,
        "index_versions": dict(sorted(index_versions.items())),
        "ambiguity_guard": ambiguity_guard,
        "hits": [asdict(hit) for hit in hits],
    }
    digest = "sha256:" + hashlib.sha256(_canonical_json(digest_input).encode("utf-8")).hexdigest()
    if ambiguity_guard:
        return FusionResult("AMBIGUOUS", (), ("ambiguous_intent",), unresolved, digest)
    if not grouped:
        if unresolved:
            return FusionResult("AMBIGUOUS", (), ("no_resolved_entity",), unresolved, digest)
        return FusionResult("NO_MATCH", (), ("no_match",), 0, digest)

    scored: list[tuple[str, float, set[int], tuple[FusedSourceEvidence, ...]]] = []
    for entity_ref, payload in grouped.items():
        by_source: dict[str, FusionSourceHit] = payload["by_source"]  # type: ignore[assignment]
        score = sum(1.0 / (RRF_K + hit.source_rank) for hit in by_source.values())
        evidence = tuple(
            FusedSourceEvidence(source, hit.source_rank, hit.evidence_ref)
            for source, hit in sorted(by_source.items())
        )
        scored.append((entity_ref, score, payload["offers"], evidence))  # type: ignore[arg-type]
    scored.sort(key=lambda item: (-item[1], -len(item[3]), item[0]))
    candidates = tuple(
        FusedCandidate(
            candidate_rank=index,
            entity_ref=entity_ref,
            rrf_score=round(score, 12),
            offer_ids=tuple(sorted(offers)),
            source_evidence=evidence,
        )
        for index, (entity_ref, score, offers, evidence) in enumerate(scored[:limit], start=1)
    )
    return FusionResult("CANDIDATES", candidates, ("retrieval_candidates",), unresolved, digest)
