from app.intelligence.contracts import CoreOfferSnapshot
from app.intelligence.general_decision import compose_general_plan
from app.intelligence.intent_resolution import resolve_intent
from app.services import taxonomy


def offer(offer_id: int, name: str, category: str, subcategory: str | None, price: float) -> CoreOfferSnapshot:
    return CoreOfferSnapshot(
        offer_id=offer_id,
        catalog_product_id=None,
        name=name,
        brand="Test",
        filon_category=category,
        filon_subcategory=subcategory,
        offer_kind=taxonomy.PHYSICAL_PRODUCT,
        price=price,
        currency="EUR",
        availability="in_stock",
        image_url="https://example.test/item.jpg",
        deep_link="https://example.test/item",
        merchant_id=1,
        merchant_name="Test",
        merchant_region="BE",
        observed_at=None,
    )


def test_plan_general_selectionne_des_offres_prouvees_dans_un_scope_unique():
    intent = resolve_intent("Tenniskleding onder 200 €", "nl")
    solution = compose_general_plan(
        intent,
        [
            offer(1, "Tennis Shirt Femme", taxonomy.SPORT, "Vêtements de sport", 40.0),
            offer(2, "Tennis Shoes Femme", taxonomy.SPORT, "Chaussures de sport", 80.0),
            offer(3, "Ballon de football", taxonomy.SPORT, "Sports collectifs", 20.0),
        ],
    )

    assert solution["decision"] == "recommend"
    assert [item["name"] for item in solution["items"]] == ["Tennis Shirt Femme", "Tennis Shoes Femme"]
    assert solution["total_known_price"]["amount"] == 120.0


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
    intent = resolve_intent("tennis clothing under €200", "en")
    solution = compose_general_plan(
        intent,
        [
            offer(1, "Balles de tennis 6.5 cm", taxonomy.SPORT, "Fitness & Musculation", 1.8),
            offer(2, "Filet de tennis multifonction", taxonomy.SPORT, "Sports collectifs", 8.19),
            offer(3, "T-shirt Tennis Court Femme", taxonomy.SPORT, "Vêtements de sport", 24.99),
        ],
    )

    assert solution["decision"] == "recommend"
    assert [item["name"] for item in solution["items"]] == ["T-shirt Tennis Court Femme"]
