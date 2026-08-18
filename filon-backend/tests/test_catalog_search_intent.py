"""Pertinence stricte des recherches assistant à modèle explicite."""

from app.services import taxonomy
from app.services.catalog_search import (
    _catalogue_intent,
    _INTENT_PRIMARY_SCOPE,
    _intent_primary_scope,
    _required_name_terms,
    _search_query_for,
)


def test_iphone_request_requires_iphone_in_the_merchant_title():
    assert _required_name_terms("un iPhone sous 1 000 €", "smartphone") == ("iphone",)


def test_named_product_terms_are_preserved_even_when_a_category_anchor_exists():
    assert _required_name_terms("un MacBook pour les études", "laptop") == ("macbook",)
    assert _required_name_terms("un Galaxy Android", "smartphone") == ("galaxy",)


def test_generic_smartphone_request_remains_open_to_the_catalogue_category():
    assert _required_name_terms("un smartphone sous 400 €", "smartphone") == ()


def test_primary_product_intents_have_an_explicit_core_scope():
    smartphone_scope = _intent_primary_scope("smartphone")
    laptop_scope = _intent_primary_scope("laptop")
    headset_scope = _intent_primary_scope("casque")

    assert smartphone_scope is not None
    assert laptop_scope is not None
    assert headset_scope is not None
    # Le contrat associe chaque intention à un sous-rayon public stable : un
    # résultat qui ne le porte pas ne peut plus être recommandé comme principal.
    assert _INTENT_PRIMARY_SCOPE["smartphone"] == (taxonomy.TELEPHONIE, "Smartphones")
    assert _INTENT_PRIMARY_SCOPE["laptop"] == (taxonomy.INFORMATIQUE, "Ordinateurs portables")
    assert _INTENT_PRIMARY_SCOPE["casque"] == (taxonomy.TV_SON, "Casques audio")
    assert _intent_primary_scope("inconnu") is None


def test_explicit_smartphone_part_is_not_misrepresented_as_a_complete_phone():
    assert _catalogue_intent("batterie iphone 15") is None
    assert _catalogue_intent("écran iphone 15") is None


def test_named_model_searches_the_model_before_the_generic_category_anchor():
    iphone_intent = _catalogue_intent("iphone 15")
    generic_intent = _catalogue_intent("smartphone sous 400 €")

    assert _search_query_for("iphone 15", iphone_intent) == ("iphone 15", ("iphone", "15"))
    assert _search_query_for("smartphone sous 400 €", generic_intent) == ("smartphone", ())
