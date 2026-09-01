"""Adaptateur lexical shadow Phase 5D."""

from __future__ import annotations

from sqlalchemy.dialects import postgresql

from app.hybrid_retrieval.lexical import (
    LEXICAL_ADAPTER_VERSION,
    LexicalDocument,
    LexicalRetrievalError,
    build_offer_lexical_statement,
    retrieve_lexical,
)


def _document(
    ref: str | None,
    model: str,
    *,
    attribute: str = "128GB",
    offer_ids: tuple[int, ...] = (1,),
) -> LexicalDocument:
    return LexicalDocument(
        document_ref=f"doc:{model}:{offer_ids}",
        entity_ref=ref,
        brand="Example Mobile",
        model=model,
        product_type="smartphone",
        product_role="PRIMARY_PRODUCT",
        attributes={"storage": attribute},
        offer_ids=offer_ids,
    )


def test_exact_product_is_first_and_provenance_is_explicit():
    result = retrieve_lexical(
        "téléphone Example Mobile Phone Pro 15",
        (
            _document("variant:2", "Alternative 15", attribute="256GB"),
            _document("variant:1", "Phone Pro 15"),
        ),
    )
    assert result.outcome == "CANDIDATES"
    assert result.adapter_version == LEXICAL_ADAPTER_VERSION
    assert result.hits[0].entity_ref == "variant:1"
    assert result.hits[0].source_type == "LEXICAL"
    assert "model" in result.hits[0].evidence_fields


def test_no_match_and_generic_ambiguity_fail_closed():
    documents = (_document("variant:1", "Phone Pro 15"), _document("variant:2", "Alternative 15"))
    assert retrieve_lexical("Synthetic Missing smartphone ZXQ", documents).outcome == "NO_MATCH"
    assert retrieve_lexical("telefoon", documents).outcome == "AMBIGUOUS"


def test_explicit_attribute_conflict_is_not_returned():
    result = retrieve_lexical(
        "Phone Pro 15 storage 128GB",
        (_document("variant:2", "Phone Pro 15", attribute="256GB"),),
    )
    assert result.outcome == "NO_MATCH"
    assert result.hits == ()


def test_duplicate_offer_rows_are_grouped_by_resolved_entity():
    result = retrieve_lexical(
        "Example Mobile Phone Pro 15",
        (
            _document("variant:1", "Phone Pro 15", offer_ids=(1,)),
            _document("variant:1", "Phone Pro 15", offer_ids=(2, 3)),
        ),
    )
    assert len(result.hits) == 1
    assert result.hits[0].offer_ids == (1, 2, 3)


def test_unresolved_match_never_becomes_resolved_entity():
    result = retrieve_lexical("Example Mobile Phone Pro 15", (_document(None, "Phone Pro 15"),))
    assert result.outcome == "AMBIGUOUS"
    assert result.hits == ()


def test_postgresql_statement_uses_index_compatible_ilike_and_is_bounded():
    statement = build_offer_lexical_statement("téléphone Example Mobile", limit=50)
    sql = str(statement.compile(dialect=postgresql.dialect()))
    assert " ILIKE " in sql
    assert "lower(offers.name)" not in sql
    assert "offers.product_id IS NOT NULL" in sql
    assert statement._limit_clause.value == 50


def test_empty_query_and_invalid_limit_fail_closed():
    import pytest

    with pytest.raises(LexicalRetrievalError, match="no lexical term"):
        retrieve_lexical(" et de ", ())
    with pytest.raises(LexicalRetrievalError, match="limit"):
        build_offer_lexical_statement("phone", limit=0)
