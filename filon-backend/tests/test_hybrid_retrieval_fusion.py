"""Fusion product-first Phase 5F."""

from __future__ import annotations

from dataclasses import fields

import pytest

from app.hybrid_retrieval.fusion import (
    FUSION_VERSION,
    FusionError,
    FusionSourceHit,
    reciprocal_rank_fusion,
)


QUERY_DIGEST = "sha256:" + "1" * 64
VERSIONS = {"LEXICAL": "lex/v1", "STRUCTURED": "structured/v1", "SEMANTIC": "semantic/v1"}


def _fuse(hits, **kwargs):
    return reciprocal_rank_fusion(
        hits,
        query_digest=QUERY_DIGEST,
        snapshot_ref="snapshot:test:1",
        index_versions=VERSIONS,
        **kwargs,
    )


def test_rrf_rewards_multi_source_evidence_and_preserves_provenance():
    result = _fuse((
        FusionSourceHit("LEXICAL", 2, "variant:1", (1,), "lex:1"),
        FusionSourceHit("STRUCTURED", 1, "variant:1", (2,), "structured:1"),
        FusionSourceHit("LEXICAL", 1, "variant:2", (3,), "lex:2"),
    ))
    assert result.outcome == "CANDIDATES"
    assert result.fusion_version == FUSION_VERSION
    assert result.candidates[0].entity_ref == "variant:1"
    assert result.candidates[0].offer_ids == (1, 2)
    assert {item.source_type for item in result.candidates[0].source_evidence} == {"LEXICAL", "STRUCTURED"}


def test_duplicate_source_hits_keep_best_rank_and_one_product():
    result = _fuse((
        FusionSourceHit("LEXICAL", 3, "variant:1", (1,), "lex:3"),
        FusionSourceHit("LEXICAL", 1, "variant:1", (2,), "lex:1"),
    ))
    assert len(result.candidates) == 1
    assert result.candidates[0].offer_ids == (1, 2)
    assert result.candidates[0].source_evidence[0].source_rank == 1


def test_semantic_only_unresolved_never_becomes_candidate():
    result = _fuse((FusionSourceHit("SEMANTIC", 1, None, (), "semantic:1"),))
    assert result.outcome == "AMBIGUOUS"
    assert result.candidates == ()
    assert result.unresolved_hits == 1


def test_upstream_ambiguity_guard_wins_over_arbitrary_first_candidate():
    result = _fuse(
        (FusionSourceHit("LEXICAL", 1, "variant:1", (1,), "lex:1"),),
        ambiguity_guard=True,
    )
    assert result.outcome == "AMBIGUOUS"
    assert result.candidates == ()


def test_digest_is_reproducible_and_commits_to_rank():
    hits = (FusionSourceHit("LEXICAL", 1, "variant:1", (1,), "lex:1"),)
    first = _fuse(hits)
    second = _fuse(hits)
    changed = _fuse((FusionSourceHit("LEXICAL", 2, "variant:1", (1,), "lex:1"),))
    assert first.result_digest == second.result_digest
    assert first.result_digest != changed.result_digest


def test_fusion_contract_has_no_affiliate_or_commission_input():
    names = {field.name for field in fields(FusionSourceHit)}
    assert "commission" not in names
    assert "affiliate" not in names
    assert "merchant_id" not in names


def test_invalid_unresolved_offer_attachment_fails_closed():
    with pytest.raises(FusionError, match="unresolved"):
        _fuse((FusionSourceHit("SEMANTIC", 1, None, (99,), "semantic:1"),))
