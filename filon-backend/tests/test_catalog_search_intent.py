"""Pertinence stricte des recherches assistant à modèle explicite."""

from app.services import taxonomy
from app.services.catalog_search import (
    _catalogue_intent,
    _coffee_automation_requirement,
    _INTENT_PRIMARY_SCOPE,
    _intent_primary_impostor_terms,
    _intent_primary_scope,
    _intent_search_terms,
    _intent_search_clause,
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


def test_noise_cancelling_headphone_synonyms_are_alternative_search_terms():
    intent = _catalogue_intent("casque à réduction de bruit sous 300 euros")
    required = _required_name_terms("casque à réduction de bruit sous 300 euros", "casque")
    clause = _intent_search_clause(" ".join(required), intent, required)

    assert intent is not None
    assert required == ("reduction de bruit", "noise", "cancel")
    assert "anc" not in required
    assert getattr(clause.operator, "__name__", "") == "or_"


def test_generic_smartphone_search_covers_actual_phone_title_families():
    terms = _intent_search_terms("smartphone")

    assert "smartphone" in terms
    assert "iphone" in terms
    assert "galaxy" in terms
    assert "pixel" in terms
    assert _intent_search_terms("inconnu") == ()


def test_smartphone_search_excludes_observed_non_phone_impostors():
    terms = _intent_primary_impostor_terms("smartphone")

    assert "onduleur" in terms
    assert "app-sensoren" in terms
    assert _intent_primary_impostor_terms("laptop") == ()
    assert _intent_primary_impostor_terms("casque") == ()


def test_headphone_request_excludes_explicit_earbuds_from_a_headphone_intent():
    assert _catalogue_intent("casque à réduction de bruit") is not None
    assert _catalogue_intent("écouteur à réduction de bruit") is None


def test_explicit_smartphone_part_is_not_misrepresented_as_a_complete_phone():
    assert _catalogue_intent("batterie iphone 15") is None
    assert _catalogue_intent("écran iphone 15") is None


def test_coffee_machine_intent_uses_the_appliance_scope_and_keeps_capsules_explicit():
    intent = _catalogue_intent("machine a cafe automatique sous 500 euros")

    assert intent is not None
    assert intent[0] == "coffee_machine"
    assert _INTENT_PRIMARY_SCOPE["coffee_machine"] == (taxonomy.ELECTROMENAGER, "Petit électroménager")
    assert "espresso" in _intent_search_terms("coffee_machine")
    assert _catalogue_intent("capsules de cafe") is None


def test_coffee_automation_is_an_explicit_requirement_and_never_an_inference():
    assert _coffee_automation_requirement("machine a cafe automatique") == "automatic"
    assert _coffee_automation_requirement("machine à café semi-automatique") == "semi"
    assert _coffee_automation_requirement("machine à expresso") is None


def test_named_model_searches_the_model_before_the_generic_category_anchor():
    iphone_intent = _catalogue_intent("iphone 15")
    generic_intent = _catalogue_intent("smartphone sous 400 €")

    assert _search_query_for("iphone 15", iphone_intent) == ("iphone 15", ("iphone", "15"))
    assert _search_query_for("smartphone sous 400 €", generic_intent) == ("smartphone", ())
