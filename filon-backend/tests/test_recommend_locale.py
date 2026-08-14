"""Locale des annotations produites par l'assistant catalogue."""

from app.services.recommend import _OFFER_NOTICES, _response_locale


def test_supported_locales_are_preserved():
    assert _response_locale("fr") == "fr"
    assert _response_locale("nl") == "nl"
    assert _response_locale("en") == "en"


def test_locale_regions_are_normalised_for_the_stream_contract():
    assert _response_locale("fr-BE") == "fr"
    assert _response_locale("nl-BE") == "nl"
    assert _response_locale("en-GB") == "en"


def test_unknown_or_missing_locale_falls_back_to_french():
    assert _response_locale(None) == "fr"
    assert _response_locale("de") == "fr"
    assert _response_locale("") == "fr"


def test_offer_notices_are_localised_and_do_not_claim_a_universal_warranty():
    assert _OFFER_NOTICES["fr"] == {"delivery": "voir marchand", "warranty": "conditions marchand"}
    assert _OFFER_NOTICES["nl"] == {"delivery": "bekijk verkoper", "warranty": "voorwaarden verkoper"}
    assert _OFFER_NOTICES["en"] == {"delivery": "see merchant", "warranty": "merchant terms"}


def _decision(scope: str, level: str) -> dict:
    return {
        "recommendation_scope": scope,
        "score_observed": 50,
        "score_possible": 75,
        "confidence": "moyenne",
        "signals": [],
        "missing": ["shipping_cost"],
        "facts": {"currency": "EUR", "merchants_compared": 2, "offers_compared": 2},
        "price_verdict": {"level": level},
    }


def test_real_card_exposes_the_same_decision_and_does_not_make_a_premature_buy_claim():
    from app.services.recommend import _build_real_card

    product = {
        "offer_id": 17,
        "product_ean": "1234567890123",
        "name": "Produit vérifié",
        "price": 99,
        "currency": "GBP",
        "merchant": "Marchand test",
        "link": None,
        "decision": _decision("meilleur_prix_observe", "insuffisant"),
    }
    card = _build_real_card(0, product, {"label": "Budget"}, "🛍️", "fr")

    assert card["offer_id"] == 17
    assert card["product_ean"] == "1234567890123"
    assert card["currency"] == "GBP"
    assert card["decision"] == product["decision"]
    assert card["evidence_score"] == 67
    assert card["buy"] is False


def test_real_card_marks_a_buy_moment_only_when_observed_price_and_history_are_favourable():
    from app.services.recommend import _build_real_card

    product = {
        "offer_id": 18,
        "product_ean": "1234567890124",
        "name": "Produit suivi",
        "price": 99,
        "merchant": "Marchand test",
        "link": None,
        "decision": _decision("meilleur_prix_observe", "bon"),
    }
    card = _build_real_card(0, product, {}, "🛍️", "fr")

    assert card["buy"] is True
