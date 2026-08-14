"""Pertinence stricte des recherches assistant à modèle explicite."""

from app.services.catalog_search import _required_name_terms


def test_iphone_request_requires_iphone_in_the_merchant_title():
    assert _required_name_terms("un iPhone sous 1 000 €", "smartphone") == ("iphone",)


def test_named_product_terms_are_preserved_even_when_a_category_anchor_exists():
    assert _required_name_terms("un MacBook pour les études", "laptop") == ("macbook",)
    assert _required_name_terms("un Galaxy Android", "smartphone") == ("galaxy",)


def test_generic_smartphone_request_remains_open_to_the_catalogue_category():
    assert _required_name_terms("un smartphone sous 400 €", "smartphone") == ()
