import math
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from app.intelligence.contracts import Availability, CoreOfferSnapshot
from app.intelligence.general_decision import compose_general_plan
from app.intelligence.intent_resolution import resolve_intent
from app.services import taxonomy


def offer(
    offer_id: int,
    name: str,
    category: str,
    subcategory: str | None,
    price: float | None,
    *,
    currency: str | None = "EUR",
    availability: Availability = "in_stock",
) -> CoreOfferSnapshot:
    return CoreOfferSnapshot(
        offer_id=offer_id,
        catalog_product_id=None,
        name=name,
        brand="Test",
        filon_category=category,
        filon_subcategory=subcategory,
        offer_kind=taxonomy.PHYSICAL_PRODUCT,
        price=price,
        currency=currency,
        availability=availability,
        image_url="https://example.test/item.jpg",
        deep_link="https://example.test/item",
        merchant_id=1,
        merchant_name="Test",
        merchant_region="BE",
        observed_at=datetime.now(UTC),
    )


def test_plan_general_selectionne_des_offres_prouvees_dans_un_scope_unique():
    intent = resolve_intent("Tenniskleding voor vrouwen onder 200 €", "nl")
    solution = compose_general_plan(
        intent,
        [
            offer(1, "Tennis Shirt Femme", taxonomy.SPORT, "Vêtements de sport", 40.0),
            offer(2, "Tennis Shoes Femme", taxonomy.SPORT, "Chaussures de sport", 80.0),
            offer(3, "Ballon de football", taxonomy.SPORT, "Sports collectifs", 20.0),
        ],
    )

    assert solution["decision"] == "recommend"
    assert [item["name"] for item in solution["items"]] == ["Tennis Shirt Femme"]
    assert solution["total_known_price"]["amount"] == 40.0


def test_plan_general_exige_un_resultat_par_scope_multi_produits():
    intent = resolve_intent("ordinateur portable et sac à dos sous 1000 €", "fr")
    solution = compose_general_plan(
        intent,
        [
            offer(1, "Ordinateur portable étudiant", taxonomy.INFORMATIQUE, "Ordinateurs portables", 700.0),
            offer(2, "Sac à dos ordinateur", taxonomy.BAGAGERIE, "Sacs à dos", 90.0),
        ],
    )

    assert solution["decision"] == "recommend"
    assert {item["filon_category"] for item in solution["items"]} == {taxonomy.INFORMATIQUE, taxonomy.BAGAGERIE}
    assert solution["total_known_price"]["amount"] == 790.0


def test_plan_general_s_abstient_si_aucune_offre_du_scope_ne_respecte_le_budget():
    intent = resolve_intent("ordinateur portable sous 500 €", "fr")
    solution = compose_general_plan(
        intent,
        [offer(1, "Ordinateur portable étudiant", taxonomy.INFORMATIQUE, "Ordinateurs portables", 700.0)],
    )

    assert solution["decision"] == "abstain"
    assert solution["rejection_reason"] == "budget_unreachable"
    assert solution["style_score"] is None
    assert solution["confidence_score"] is None
    assert solution["confidence_band"] == "not_calibrated"
    assert "confidence_not_calibrated" in solution["unknowns"]


def test_plan_general_s_abstient_si_le_prix_est_inconnu():
    intent = resolve_intent("ordinateur portable sous 500 €", "fr")

    solution = compose_general_plan(
        intent,
        [
            offer(
                1,
                "Ordinateur portable étudiant",
                taxonomy.INFORMATIQUE,
                "Ordinateurs portables",
                None,
            )
        ],
    )

    assert solution["decision"] == "abstain"
    assert solution["rejection_reason"] == "no_eligible_offer"
    assert solution["items"] == []


@pytest.mark.parametrize("price", [0.0, -1.0, math.nan, math.inf, -math.inf])
def test_plan_general_s_abstient_si_le_prix_n_est_pas_fini_et_positif(price):
    intent = resolve_intent("ordinateur portable sous 500 €", "fr")

    solution = compose_general_plan(
        intent,
        [
            offer(
                1,
                "Ordinateur portable étudiant",
                taxonomy.INFORMATIQUE,
                "Ordinateurs portables",
                price,
            )
        ],
    )

    assert solution["decision"] == "abstain"
    assert solution["rejection_reason"] == "no_eligible_offer"
    assert solution["items"] == []


@pytest.mark.parametrize(
    "currency",
    [None, "", "   ", "unknown", "ABC", "XXX", "XTS"],
)
def test_plan_general_s_abstient_si_la_devise_est_inconnue(currency):
    # Le cas sans budget verrouille aussi le caller public Intelligence : une
    # devise factice ne doit pas passer seulement parce qu'aucune comparaison
    # avec l'euro n'est demandée.
    intent = resolve_intent("ordinateur portable", "fr")

    solution = compose_general_plan(
        intent,
        [
            offer(
                1,
                "Ordinateur portable étudiant",
                taxonomy.INFORMATIQUE,
                "Ordinateurs portables",
                400.0,
                currency=currency,
            )
        ],
    )

    assert solution["decision"] == "abstain"
    assert solution["rejection_reason"] == "no_eligible_offer"
    assert solution["items"] == []


def test_plan_general_normalise_la_devise_prouvee_avant_de_l_exposer():
    intent = resolve_intent("ordinateur portable", "fr")

    solution = compose_general_plan(
        intent,
        [
            offer(
                1,
                "Ordinateur portable étudiant",
                taxonomy.INFORMATIQUE,
                "Ordinateurs portables",
                400.0,
                currency=" eur ",
            )
        ],
    )

    assert solution["decision"] == "recommend"
    assert solution["total_known_price"]["currency"] == "EUR"
    assert solution["items"][0]["currency"] == "EUR"
    assert solution["items"][0]["evidence"][0]["value"] == "400.00 EUR"
    assert all(
        evidence["confidence"] is None
        for evidence in solution["items"][0]["evidence"]
    )


def test_plan_general_s_abstient_si_le_stock_est_inconnu():
    intent = resolve_intent("ordinateur portable sous 500 €", "fr")

    solution = compose_general_plan(
        intent,
        [
            offer(
                1,
                "Ordinateur portable étudiant",
                taxonomy.INFORMATIQUE,
                "Ordinateurs portables",
                400.0,
                availability="unknown",
            )
        ],
    )

    assert solution["decision"] == "abstain"
    assert solution["rejection_reason"] == "no_eligible_offer"
    assert solution["items"] == []


@pytest.mark.parametrize(
    "observed_at",
    [
        None,
        datetime.now(UTC) - timedelta(hours=73),
        datetime.now(UTC) + timedelta(hours=1),
    ],
)
def test_plan_general_s_abstient_si_observation_absente_ou_expiree(observed_at):
    intent = resolve_intent("ordinateur portable sous 500 €", "fr")
    stale = replace(
        offer(
            1,
            "Ordinateur portable étudiant",
            taxonomy.INFORMATIQUE,
            "Ordinateurs portables",
            400.0,
        ),
        observed_at=observed_at,
    )

    solution = compose_general_plan(intent, [stale])

    assert solution["decision"] == "abstain"
    assert solution["rejection_reason"] == "no_eligible_offer"
    assert solution["items"] == []


def test_plan_general_ignore_les_offres_incompletes_si_une_offre_est_eligible():
    intent = resolve_intent("ordinateur portable sous 500 €", "fr")

    solution = compose_general_plan(
        intent,
        [
            offer(
                1,
                "Ordinateur portable étudiant sans prix",
                taxonomy.INFORMATIQUE,
                "Ordinateurs portables",
                None,
            ),
            offer(
                3,
                "Ordinateur portable étudiant sans devise",
                taxonomy.INFORMATIQUE,
                "Ordinateurs portables",
                350.0,
                currency=None,
            ),
            offer(
                4,
                "Ordinateur portable étudiant stock inconnu",
                taxonomy.INFORMATIQUE,
                "Ordinateurs portables",
                400.0,
                availability="unknown",
            ),
            offer(
                2,
                "Ordinateur portable étudiant disponible",
                taxonomy.INFORMATIQUE,
                "Ordinateurs portables",
                450.0,
            ),
        ],
    )

    assert solution["decision"] == "recommend"
    assert [item["offer_id"] for item in solution["items"]] == [2]
    assert solution["total_known_price"] == {
        "amount": 450.0,
        "currency": "EUR",
        "scope": "items_only",
    }
    assert solution["confidence_score"] is None
    assert solution["confidence_band"] == "not_calibrated"
    assert "confidence_not_calibrated" in solution["unknowns"]


def test_plan_general_s_abstient_plutot_que_comparer_des_devises_sans_fx():
    intent = resolve_intent("ordinateur portable", "fr")

    solution = compose_general_plan(
        intent,
        [
            offer(
                1,
                "Ordinateur portable étudiant EUR",
                taxonomy.INFORMATIQUE,
                "Ordinateurs portables",
                90.0,
                currency="EUR",
            ),
            offer(
                2,
                "Ordinateur portable étudiant JPY",
                taxonomy.INFORMATIQUE,
                "Ordinateurs portables",
                100.0,
                currency="JPY",
            ),
        ],
    )

    assert solution["decision"] == "abstain"
    assert solution["rejection_reason"] == "currency_not_comparable"
    assert solution["items"] == []


def test_plan_general_budget_eur_ignore_une_offre_etrangere_concurrente():
    intent = resolve_intent("ordinateur portable sous 500 €", "fr")

    solution = compose_general_plan(
        intent,
        [
            offer(
                1,
                "Ordinateur portable étudiant EUR",
                taxonomy.INFORMATIQUE,
                "Ordinateurs portables",
                400.0,
                currency="EUR",
            ),
            offer(
                2,
                "Ordinateur portable étudiant USD",
                taxonomy.INFORMATIQUE,
                "Ordinateurs portables",
                350.0,
                currency="USD",
            ),
        ],
    )

    assert solution["decision"] == "recommend"
    assert [item["offer_id"] for item in solution["items"]] == [1]
    assert solution["total_known_price"]["currency"] == "EUR"


def test_plan_general_s_abstient_si_le_total_multi_scope_deborde():
    intent = resolve_intent("ordinateur portable et sac à dos", "fr")

    solution = compose_general_plan(
        intent,
        [
            offer(
                1,
                "Ordinateur portable étudiant",
                taxonomy.INFORMATIQUE,
                "Ordinateurs portables",
                1e308,
            ),
            offer(
                2,
                "Sac à dos ordinateur",
                taxonomy.BAGAGERIE,
                "Sacs à dos",
                1e308,
            ),
        ],
    )

    assert solution["decision"] == "abstain"
    assert solution["rejection_reason"] == "non_finite_total"
    assert solution["total_known_price"] is None



def test_plan_general_recommande_un_scope_prouve_meme_sans_terme_libre_dans_le_titre():
    from app.intelligence.intent_resolution import GeneralIntent, IntentScope

    intent = GeneralIntent(
        raw_request="kampeeruitrusting onder 300 €",
        locale="nl",
        scopes=(IntentScope(taxonomy.SPORT, "Camping & Randonnée", "kampeeruitrusting", ("kampeer", "uitrusting")),),
        terms=("kampeer", "uitrusting"),
        required_title_phrases=(),
        budget_eur=300.0,
    )
    solution = compose_general_plan(
        intent,
        [offer(1, "Tente familiale 4 personnes", taxonomy.SPORT, "Camping & Randonnée", 120.0)],
    )

    assert solution["decision"] == "recommend"
    assert solution["items"][0]["name"] == "Tente familiale 4 personnes"



def test_plan_general_exige_une_preuve_de_vetement_quand_la_demande_le_precise():
    intent = resolve_intent("tenniskleding onder 200 €", "nl")
    solution = compose_general_plan(
        intent,
        [
            offer(1, "Balles tennis de table Enebe Haut à partir de 3+1", taxonomy.SPORT, "Fitness & Musculation", 2.5),
            offer(2, "Filet de tennis multifonction", taxonomy.SPORT, "Sports collectifs", 8.19),
            offer(3, "T-shirt Tennis Court Unisex", taxonomy.SPORT, "Vêtements de sport", 24.99),
        ],
    )

    assert solution["decision"] == "recommend"
    assert [item["name"] for item in solution["items"]] == ["T-shirt Tennis Court Unisex"]



def test_plan_general_ne_suppose_pas_le_genre_dans_une_demande_vestimentaire():
    intent = resolve_intent("tenniskleding onder 200 €", "nl")
    solution = compose_general_plan(
        intent,
        [
            offer(0, "Kids' Quick-Dry Running Set - Breathable Short Sleeve & Shorts", taxonomy.SPORT, "Running", 1.0),
            offer(1, "T-shirt Tennis Joma Femme", taxonomy.SPORT, "Vêtements de sport", 1.5),
            offer(2, "Tennissokken - Unisex - Multi wit", taxonomy.SPORT, "Vêtements de sport", 3.99),
        ],
    )

    assert solution["decision"] == "recommend"
    assert [item["name"] for item in solution["items"]] == ["Tennissokken - Unisex - Multi wit"]



def test_plan_general_dun_kit_ecarte_un_composant_minime_au_profit_dun_equipement_utilisable():
    from app.intelligence.intent_resolution import GeneralIntent, IntentScope

    intent = GeneralIntent(
        raw_request="camping equipment under €300",
        locale="en",
        scopes=(
            IntentScope(
                taxonomy.SPORT,
                "Camping & Randonnée",
                "camping equipment under €300",
                ("tent", "sleeping bag", "camping mattress", "stove"),
            ),
        ),
        terms=("camping", "equipment"),
        required_title_phrases=(),
        budget_eur=300.0,
    )
    solution = compose_general_plan(
        intent,
        [
            offer(1, "Piquet de tente BW 25 cm occasion", taxonomy.SPORT, "Camping & Randonnée", 1.99),
            offer(2, "Tasse camping Regatta", taxonomy.SPORT, "Camping & Randonnée", 3.99),
            offer(3, "Matelas de camping autogonflant 2 personnes", taxonomy.SPORT, "Camping & Randonnée", 49.99),
        ],
    )

    assert solution["decision"] == "recommend"
    assert [item["name"] for item in solution["items"]] == ["Matelas de camping autogonflant 2 personnes"]



def test_plan_general_ecarte_un_outil_de_montre_au_profit_dune_montre_connectee():
    intent = resolve_intent("montre connectée sous 250 €", "fr")
    solution = compose_general_plan(
        intent,
        [
            offer(1, "Outil Métallique OEM pour Couvercles de Montres", taxonomy.BIJOUX, "Montres", 1.13),
            offer(2, "Montre connectée GPS avec cardio", taxonomy.BIJOUX, "Montres", 129.0),
        ],
    )

    assert solution["decision"] == "recommend"
    assert [item["name"] for item in solution["items"]] == ["Montre connectée GPS avec cardio"]


def test_plan_general_ecarte_une_piece_de_camera_au_profit_dun_appareil_autonome():
    intent = resolve_intent("camera equipment under €800", "en")
    solution = compose_general_plan(
        intent,
        [
            offer(1, "Rear camera glass and inner frame service pack", taxonomy.PHOTO, None, 15.52),
            offer(2, "Mirrorless camera body with interchangeable lens", taxonomy.PHOTO, None, 499.0),
        ],
    )

    assert solution["decision"] == "recommend"
    assert [item["name"] for item in solution["items"]] == ["Mirrorless camera body with interchangeable lens"]



def test_plan_general_conserve_le_qualificatif_explicite_dune_montre_connectee():
    intent = resolve_intent("montre connectée sous 250 €", "fr")
    solution = compose_general_plan(
        intent,
        [
            offer(1, "Montre digitale enfant avec projection d'images", taxonomy.BIJOUX, "Montres", 9.74),
            offer(2, "Montre connectée sport GPS avec cardio", taxonomy.BIJOUX, "Montres", 129.0),
        ],
    )

    assert solution["decision"] == "recommend"
    assert [item["name"] for item in solution["items"]] == ["Montre connectée sport GPS avec cardio"]


def test_plan_general_dun_kit_neerlandais_ecarte_un_composant_de_reglage():
    from app.intelligence.intent_resolution import GeneralIntent, IntentScope

    intent = GeneralIntent(
        raw_request="fietsuitrusting onder 500 €",
        locale="nl",
        scopes=(IntentScope(taxonomy.SPORT, "Cyclisme", "fietsuitrusting onder 500 €", ("fietshelm", "fietslamp", "fietsslot")),),
        terms=("fiets", "uitrusting"),
        required_title_phrases=(),
        budget_eur=500.0,
    )
    solution = compose_general_plan(
        intent,
        [
            offer(1, "Ajusteur de rebond Fox Factory FIT4", taxonomy.SPORT, "Cyclisme", 10.0),
            offer(2, "Fietshelm met verstelbaar vizier", taxonomy.SPORT, "Cyclisme", 59.0),
        ],
    )

    assert solution["decision"] == "recommend"
    assert [item["name"] for item in solution["items"]] == ["Fietshelm met verstelbaar vizier"]



def test_plan_general_prefere_un_smartphone_prouve_a_un_bijou_pour_telephone():
    from app.intelligence.intent_resolution import GeneralIntent, IntentScope

    intent = GeneralIntent(
        raw_request="smartphone under €400",
        locale="en",
        scopes=(IntentScope(taxonomy.TELEPHONIE, "Smartphones", "smartphone under €400", ("smartphone", "mobile phone", "android", "iphone")),),
        terms=("smartphone",),
        required_title_phrases=(),
        budget_eur=400.0,
    )
    solution = compose_general_plan(
        intent,
        [
            offer(1, "Mobile phone leather bracelet chain for iPhone", taxonomy.TELEPHONIE, "Smartphones", 3.31),
            offer(2, "Smartphone video rig with hand grip", taxonomy.TELEPHONIE, "Smartphones", 3.99),
            offer(3, "3-in-1 smartphone ventilator Lightning USB-C Micro-USB", taxonomy.TELEPHONIE, "Smartphones", 7.99),
            offer(4, "Selfie stick phone tripod with Bluetooth remote", taxonomy.TELEPHONIE, "Smartphones", 9.09),
            offer(5, "Precision screwdriver set for computer and smartphone", taxonomy.TELEPHONIE, "Smartphones", 10.28),
            offer(6, "Pocket photo printer for smartphone with WiFi Bluetooth", taxonomy.TELEPHONIE, "Smartphones", 10.89),
            offer(7, "Interactive smartphone for children aged 2 to 6", taxonomy.TELEPHONIE, "Smartphones", 14.55),
            offer(8, "Educational Paw Patrol smartphone toy", taxonomy.TELEPHONIE, "Smartphones", 16.04),
            offer(9, "Senior mobile phone with 4G", taxonomy.TELEPHONIE, "Smartphones", 29.99),
            offer(10, "Smartphone-controlled thermometer with app sensors", taxonomy.TELEPHONIE, "Smartphones", 33.99),
            offer(11, "Android smartphone with 128 GB storage", taxonomy.TELEPHONIE, "Smartphones", 249.0),
        ],
    )

    assert solution["decision"] == "recommend"
    assert [item["name"] for item in solution["items"]] == ["Android smartphone with 128 GB storage"]


def test_plan_general_exige_la_preuve_dune_reduction_de_bruit_explicitement_demandee():
    from app.intelligence.intent_resolution import GeneralIntent, IntentScope

    intent = GeneralIntent(
        raw_request="casque à réduction de bruit sous 200 €",
        locale="fr",
        scopes=(IntentScope(taxonomy.TV_SON, "Casques audio", "casque à réduction de bruit sous 200 €", ("casque", "réduction de bruit", "bluetooth", "sans fil", "noise cancelling")),),
        terms=("casque", "reduction", "bruit"),
        required_title_phrases=(),
        budget_eur=200.0,
    )
    solution = compose_general_plan(
        intent,
        [
            offer(1, "Ecouteurs sans fil Bluetooth", taxonomy.TV_SON, "Casques audio", 14.06),
            offer(2, "Casque Bluetooth à réduction de bruit active", taxonomy.TV_SON, "Casques audio", 119.0),
        ],
    )

    assert solution["decision"] == "recommend"
    assert [item["name"] for item in solution["items"]] == ["Casque Bluetooth à réduction de bruit active"]



def test_plan_general_ecarte_un_peripherique_vr_du_smartphone_principal():
    from app.intelligence.intent_resolution import GeneralIntent, IntentScope

    intent = GeneralIntent(
        raw_request="smartphone under €400",
        locale="en",
        scopes=(IntentScope(taxonomy.TELEPHONIE, "Smartphones", "smartphone under €400", ("smartphone", "mobile phone", "android", "iphone")),),
        terms=("smartphone",),
        required_title_phrases=(),
        budget_eur=400.0,
    )
    solution = compose_general_plan(
        intent,
        [
            offer(1, "Virtual reality glasses for smartphone", taxonomy.TELEPHONIE, "Smartphones", 6.4),
            offer(2, "Android smartphone with 128 GB storage", taxonomy.TELEPHONIE, "Smartphones", 249.0),
        ],
    )

    assert solution["decision"] == "recommend"
    assert [item["name"] for item in solution["items"]] == ["Android smartphone with 128 GB storage"]



def test_plan_general_s_abstient_dans_un_scope_large_sans_preuve_titre_du_produit_demande():
    from app.intelligence.intent_resolution import GeneralIntent, IntentScope

    intent = GeneralIntent(
        raw_request="machine à laver sous 600 euros",
        locale="fr",
        scopes=(IntentScope(taxonomy.ELECTROMENAGER, None, "machine à laver", ("machine à laver", "lave linge", "washing machine")),),
        terms=("machine", "laver"),
        required_title_phrases=(),
        budget_eur=600.0,
    )
    solution = compose_general_plan(
        intent,
        [offer(1, "Frigo HP2", taxonomy.ELECTROMENAGER, None, 89.0)],
    )

    assert solution["decision"] == "abstain"
    assert solution["rejection_reason"] == "no_verified_scope"


def test_plan_general_ecarte_les_satellites_generiques_observes_dans_l_audit_large():
    from app.intelligence.intent_resolution import GeneralIntent, IntentScope

    intent = GeneralIntent(
        raw_request="robot vacuum under 300 euros",
        locale="en",
        scopes=(IntentScope(taxonomy.ELECTROMENAGER, "Aspirateurs", "robot vacuum", ("robot vacuum", "robot aspirateur")),),
        terms=("robot", "vacuum"),
        required_title_phrases=(),
        budget_eur=300.0,
    )
    solution = compose_general_plan(
        intent,
        [
            offer(1, "Brosse pour Xiaomi Robot Vacuum", taxonomy.ELECTROMENAGER, "Aspirateurs", 4.35),
            offer(2, "Robot vacuum with self-emptying station", taxonomy.ELECTROMENAGER, "Aspirateurs", 229.0),
        ],
    )

    assert solution["decision"] == "recommend"
    assert [item["name"] for item in solution["items"]] == ["Robot vacuum with self-emptying station"]



def test_plan_general_nutilise_pas_les_mots_semantiques_pour_autoriser_un_accessoire_non_demande():
    from app.intelligence.intent_resolution import GeneralIntent, IntentScope

    intent = GeneralIntent(
        raw_request="smartwatch under 200 euros",
        locale="en",
        scopes=(IntentScope(taxonomy.BIJOUX, "Montres", "smartwatch under 200 euros", ("smartwatch", "watch strap", "watch band")),),
        terms=("smartwatch",),
        required_title_phrases=(),
        budget_eur=200.0,
    )
    solution = compose_general_plan(
        intent,
        [
            offer(1, "Smartwatch magnetic watch strap 20 mm", taxonomy.BIJOUX, "Montres", 3.89),
            offer(2, "Smartwatch with heart-rate monitor", taxonomy.BIJOUX, "Montres", 79.0),
        ],
    )

    assert solution["decision"] == "recommend"
    assert [item["name"] for item in solution["items"]] == ["Smartwatch with heart-rate monitor"]


def test_plan_general_exige_une_chaussure_lorsque_la_demande_le_precise():
    from app.intelligence.intent_resolution import GeneralIntent, IntentScope

    intent = GeneralIntent(
        raw_request="hardloopschoenen onder 150 euro",
        locale="nl",
        scopes=(IntentScope(taxonomy.CHAUSSURES, None, "hardloopschoenen", ("running shoes", "hardloopschoenen")),),
        terms=("hardloopschoenen",),
        required_title_phrases=(),
        budget_eur=150.0,
    )
    solution = compose_general_plan(
        intent,
        [
            offer(1, "Hardloopvest met LED en telefoonvak", taxonomy.CHAUSSURES, None, 24.19),
            offer(2, "Hardloopschoenen met demping", taxonomy.CHAUSSURES, None, 79.0),
        ],
    )

    assert solution["decision"] == "recommend"
    assert [item["name"] for item in solution["items"]] == ["Hardloopschoenen met demping"]



def test_plan_general_ne_permet_pas_aux_expansions_semantiques_dautoriser_un_satellite_non_demande():
    from app.intelligence.intent_resolution import GeneralIntent, IntentScope

    intent = GeneralIntent(
        raw_request="elektrische fiets onder 1200 euro",
        locale="nl",
        scopes=(IntentScope(taxonomy.SPORT, "Cyclisme", "elektrische fiets onder 1200 euro", ("elektrische fiets", "fiets batterij", "fietszadel")),),
        terms=("elektrische", "fiets"),
        required_title_phrases=(),
        budget_eur=1200.0,
    )
    solution = compose_general_plan(
        intent,
        [
            offer(1, "Batterie vélo électrique tige de selle", taxonomy.SPORT, "Cyclisme", 320.0),
            offer(2, "Selle de vélo électrique confort", taxonomy.SPORT, "Cyclisme", 83.99),
            offer(3, "Vélo électrique urbain 500 Wh", taxonomy.SPORT, "Cyclisme", 899.0),
        ],
    )

    assert solution["decision"] == "recommend"
    assert [item["name"] for item in solution["items"]] == ["Vélo électrique urbain 500 Wh"]



def test_plan_general_prefere_un_produit_substantiel_sous_budget_a_un_accessoire_minimal_du_meme_scope():
    from app.intelligence.intent_resolution import GeneralIntent, IntentScope

    intent = GeneralIntent(
        raw_request="elektrische fiets onder 1200 euro",
        locale="nl",
        scopes=(IntentScope(taxonomy.SPORT, "Cyclisme", "elektrische fiets onder 1200 euro", ("fiets",)),),
        terms=("elektrische", "fiets"),
        required_title_phrases=(),
        budget_eur=1200.0,
    )
    solution = compose_general_plan(
        intent,
        [
            offer(1, "Monzana Fietsenrek 2 Fietsen", taxonomy.SPORT, "Cyclisme", 41.99),
            offer(2, "Vélo électrique pliant U4", taxonomy.SPORT, "Cyclisme", 558.99),
        ],
    )

    assert solution["decision"] == "recommend"
    assert [item["name"] for item in solution["items"]] == ["Vélo électrique pliant U4"]



def test_plan_general_s_abstient_lorsqu_un_scope_ne_contient_que_des_satellites():
    intent = resolve_intent("ordinateur portable sous 700 €", "fr")
    solution = compose_general_plan(
        intent,
        [offer(1, "Ramsvik Laptop Case", taxonomy.INFORMATIQUE, "Ordinateurs portables", 35.0)],
    )

    assert solution["decision"] == "abstain"
    assert solution["items"] == []



def test_plan_general_prefere_un_produit_principal_representatif_a_un_objet_minimal_sous_le_meme_budget():
    intent = resolve_intent("laptop onder 700 euro", "nl")
    solution = compose_general_plan(
        intent,
        [
            offer(1, "VTech Challenger Laptop", taxonomy.INFORMATIQUE, "Ordinateurs portables", 41.45),
            offer(2, "HP 17 Ordinateur portable 17 pouces", taxonomy.INFORMATIQUE, "Ordinateurs portables", 379.0),
        ],
    )

    assert solution["decision"] == "recommend"
    assert [item["name"] for item in solution["items"]] == ["HP 17 Ordinateur portable 17 pouces"]



def test_plan_general_exige_le_qualificatif_explicite_distinctif_du_scope():
    intent = resolve_intent("chaise de bureau sous 300 euros", "fr")
    solution = compose_general_plan(
        intent,
        [
            offer(1, "Chaises pliantes Brixy lot de 4", taxonomy.MAISON, "Meubles", 60.39),
            offer(2, "Chaise de bureau ergonomique réglable", taxonomy.MAISON, "Meubles", 149.0),
        ],
    )

    assert solution["decision"] == "recommend"
    assert [item["name"] for item in solution["items"]] == ["Chaise de bureau ergonomique réglable"]


def test_plan_general_ne_replie_pas_un_scope_precis_sur_un_titre_sans_sa_phrase_de_preuve():
    from app.intelligence.intent_resolution import GeneralIntent, IntentScope

    intent = GeneralIntent(
        raw_request="machine à laver sous 600 euros",
        locale="fr",
        scopes=(
            IntentScope(
                taxonomy.ELECTROMENAGER,
                "Gros électroménager",
                "machine à laver sous 600 euros",
                ("machine à laver", "lave-linge", "washing machine"),
            ),
        ),
        terms=("machine", "laver"),
        required_title_phrases=(),
        budget_eur=600.0,
    )
    solution = compose_general_plan(
        intent,
        [
            offer(1, "Four à pizza électrique VEVOR", taxonomy.ELECTROMENAGER, "Gros électroménager", 164.25),
            offer(2, "Lave-linge hublot 8 kg", taxonomy.ELECTROMENAGER, "Gros électroménager", 429.0),
        ],
    )

    assert solution["decision"] == "recommend"
    assert [item["name"] for item in solution["items"]] == ["Lave-linge hublot 8 kg"]



def test_plan_general_s_abstient_pour_une_machine_semi_automatique_quand_automatique_est_exigee():
    from app.intelligence.intent_resolution import GeneralIntent, IntentScope

    intent = GeneralIntent(
        raw_request="automatische koffiemachine onder 500 euro",
        locale="nl",
        scopes=(
            IntentScope(
                taxonomy.ELECTROMENAGER,
                "Petit électroménager",
                "automatische koffiemachine onder 500 euro",
                ("koffiemachine", "automatische koffiemachine", "espressomachine"),
            ),
        ),
        terms=("automatische", "koffiemachine"),
        required_title_phrases=(),
        budget_eur=500.0,
    )
    solution = compose_general_plan(
        intent,
        [
            offer(
                1,
                "HiBREW H10A Machine à café expresso semiautomatique 20 bars",
                taxonomy.ELECTROMENAGER,
                "Petit électroménager",
                199.0,
            )
        ],
    )

    assert solution["decision"] == "abstain"
    assert solution["rejection_reason"] == "no_verified_scope"



def test_plan_general_s_abstient_dans_un_sous_rayon_precis_sans_preuve_de_phrase_produit():
    from app.intelligence.intent_resolution import GeneralIntent, IntentScope

    intent = GeneralIntent(
        raw_request="sleeping bag under 150 euros",
        locale="en",
        scopes=(
            IntentScope(
                taxonomy.SPORT,
                "Camping & Randonnée",
                "sleeping bag under 150 euros",
                ("sleeping bag", "sac de couchage", "camping sleeping bag"),
            ),
        ),
        terms=("sleeping", "bag"),
        required_title_phrases=(),
        budget_eur=150.0,
    )
    solution = compose_general_plan(
        intent,
        [offer(1, "T-shirt randonnée adidas Multi Terrex Homme", taxonomy.SPORT, "Camping & Randonnée", 30.0)],
    )

    assert solution["decision"] == "abstain"
    assert solution["rejection_reason"] == "no_verified_scope"
