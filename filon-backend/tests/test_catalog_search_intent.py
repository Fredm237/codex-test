"""Pertinence stricte des recherches assistant à modèle explicite."""

from app.services.catalog_search import _catalogue_intent, _required_name_terms, _search_query_for


def test_iphone_request_requires_iphone_in_the_merchant_title():
    assert _required_name_terms("un iPhone sous 1 000 €", "smartphone") == ("iphone",)


def test_named_product_terms_are_preserved_even_when_a_category_anchor_exists():
    assert _required_name_terms("un MacBook pour les études", "laptop") == ("macbook",)
    assert _required_name_terms("un Galaxy Android", "smartphone") == ("galaxy",)


def test_generic_smartphone_request_remains_open_to_the_catalogue_category():
    assert _required_name_terms("un smartphone sous 400 €", "smartphone") == ()


def test_named_model_searches_the_model_before_the_generic_category_anchor():
    iphone_intent = _catalogue_intent("iphone 15")
    generic_intent = _catalogue_intent("smartphone sous 400 €")

    assert _search_query_for("iphone 15", iphone_intent) == ("iphone", ("iphone",))
    assert _search_query_for("smartphone sous 400 €", generic_intent) == ("smartphone", ())
