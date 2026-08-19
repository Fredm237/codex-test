from app.intelligence.intent_resolution import resolve_intent
from app.services import taxonomy


def test_resout_des_intentions_generales_multilingues_vers_le_meme_rayon():
    requests = (
        "Des vêtements de tennis pour femme sous 150 €",
        "Tenniskleding voor dames onder 150 €",
        "Women's tennis clothing under €150",
    )
    for request in requests:
        intent = resolve_intent(request, "fr")
        assert intent.resolved
        assert intent.scopes[0].category == taxonomy.SPORT
        assert intent.budget_eur == 150.0


def test_resout_des_segments_multi_produits_sans_ouvrir_un_rayon_ambigu():
    intent = resolve_intent("ordinateur portable et sac à dos sous 1000 €", "fr")

    assert {scope.category for scope in intent.scopes} >= {taxonomy.INFORMATIQUE, taxonomy.BAGAGERIE}
    assert intent.budget_eur == 1000.0


def test_conserve_une_reference_de_modele_sans_lire_le_budget_comme_modele():
    intent = resolve_intent("iPhone 15 sous 600 €", "fr")

    assert intent.required_title_phrases == ("iphone 15",)
    assert intent.budget_eur == 600.0


def test_ne_cree_pas_de_rayon_lorsque_la_taxonomie_ne_reconnait_pas_la_demande():
    intent = resolve_intent("objet imaginaire inexistant", "fr")

    assert intent.resolved is False
    assert intent.scopes == ()
