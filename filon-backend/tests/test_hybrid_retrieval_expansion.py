"""Sources structurée et sémantique expand-only Phase 5E."""

from __future__ import annotations

from app.hybrid_retrieval.expand_only import combine_expand_only
from app.hybrid_retrieval.lexical import LexicalResult
from app.hybrid_retrieval.semantic import SemanticDocument, retrieve_semantic
from app.hybrid_retrieval.structured import (
    StructuredDocument,
    intent_from_query,
    retrieve_structured,
)


def test_structured_source_respects_explicit_attribute_and_identity():
    intent = intent_from_query("smartphone storage 128GB")
    result = retrieve_structured(
        intent,
        (
            StructuredDocument("a", "variant:1", "smartphone", "PRIMARY_PRODUCT", {"storage": "128GB"}, (1,)),
            StructuredDocument("b", "variant:2", "smartphone", "PRIMARY_PRODUCT", {"storage": "256GB"}, (2,)),
            StructuredDocument("c", None, "smartphone", "PRIMARY_PRODUCT", {"storage": "128GB"}, ()),
        ),
    )
    assert result.outcome == "CANDIDATES"
    assert [hit.entity_ref for hit in result.hits] == ["variant:1"]


def test_generic_structured_scope_is_ambiguous_not_first_row():
    result = retrieve_structured(
        intent_from_query("telefoon"),
        (StructuredDocument("a", "variant:1", "smartphone", "PRIMARY_PRODUCT", {}, (1,)),),
    )
    assert result.outcome == "AMBIGUOUS"
    assert result.hits == ()


def test_semantic_only_candidate_stays_quarantined_and_unresolved():
    result = retrieve_semantic(
        "quiet comfortable headphones",
        (SemanticDocument("a", None, "headphones", (99,)),),
    )
    assert result.outcome == "EXPANDED"
    assert result.hits[0].entity_ref is None
    assert result.hits[0].candidate_status == "QUARANTINED"
    assert result.hits[0].offer_ids == ()


def test_explicit_unknown_identifier_blocks_semantic_dilution():
    result = retrieve_semantic(
        "Synthetic Missing headphones ZXQ",
        (SemanticDocument("a", "variant:1", "headphones", (1,)),),
    )
    assert result.outcome == "ABSTAINED"
    assert result.hits == ()


def test_expand_only_union_never_promotes_unresolved_semantic_hit():
    semantic = retrieve_semantic(
        "quiet comfortable headphones",
        (SemanticDocument("a", None, "headphones", (99,)),),
    )
    combined = combine_expand_only(
        LexicalResult("NO_MATCH", (), ("no_match",)),
        retrieve_structured(intent_from_query("quiet comfortable headphones"), ()),
        semantic,
    )
    assert combined.outcome == "AMBIGUOUS"
    assert combined.candidates == ()
    assert "no_resolved_entity" in combined.reason_codes
