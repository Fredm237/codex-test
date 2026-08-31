"""Locale des annotations produites par l'assistant catalogue."""

from copy import deepcopy
from datetime import UTC, datetime, timedelta

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
    observed_at = datetime.now(UTC).isoformat()
    return {
        "version": 3,
        "recommendation_scope": scope,
        "confidence": "not_calibrated",
        "signals": [
            {"key": "availability", "status": "positive", "in_stock": True},
            {"key": "freshness", "status": "positive", "age_hours": 1},
        ],
        "evidence": [
            {
                "key": "price",
                "state": "observed",
                "observed_at": observed_at,
                "value": {"amount": 99, "currency": "EUR"},
            },
            {
                "key": "availability",
                "state": "observed",
                "value": {"in_stock": True},
            },
            {
                "key": "freshness",
                "state": "observed",
                "observed_at": observed_at,
                "value": {"age_hours": 1, "status": "fresh"},
            },
        ],
        "missing": ["shipping_cost"],
        "facts": {
            "item_price": 99,
            "currency": "EUR",
            "merchants_compared": 2,
            "offers_compared": 2,
            "last_observed_at": observed_at,
        },
        "price_verdict": {
            "level": level,
            "basis": "price_history",
            "confidence": "not_calibrated",
        },
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
    card = _build_real_card(
        0,
        product,
        {"label": "Budget", "alt": "Produit absent du catalogue"},
        "🛍️",
        "fr",
    )

    assert card["offer_id"] == 17
    assert card["product_ean"] == "1234567890123"
    assert card["currency"] == "GBP"
    assert card["in_stock"] is True
    assert card["observed_at"] == product["decision"]["facts"]["last_observed_at"]
    assert card["decision"] == product["decision"]
    assert card["evidence_current"] is False
    assert "evidence_score" not in card
    assert card["buy"] is False
    assert card["alt"] is None
    assert card["cashback"] is None
    assert card["rank"] == "Offre indexée"
    assert card["why"] == (
        "Offre issue du catalogue indexé ; vérifiez les conditions chez le marchand."
    )


def test_real_card_marks_a_buy_moment_only_when_observed_price_and_history_are_favourable():
    from app.services.recommend import _build_real_card

    product = {
        "offer_id": 18,
        "product_ean": "1234567890124",
        "name": "Produit suivi",
        "price": 99,
        "currency": "EUR",
        "merchant": "Marchand test",
        "link": None,
        "decision": _decision("meilleur_prix_observe", "bon"),
    }
    card = _build_real_card(0, product, {}, "🛍️", "fr")

    assert card["evidence_current"] is True
    assert card["buy"] is True


def test_real_card_preserves_decimal_price_and_matches_the_decision_fact():
    from app.services.recommend import _build_real_card

    decision = _decision("meilleur_prix_observe", "bon")
    decision["facts"]["item_price"] = 99.99
    decision["evidence"][0]["value"]["amount"] = 99.99
    card = _build_real_card(
        0,
        {
            "offer_id": 181,
            "name": "Produit au prix décimal",
            "price": 99.99,
            "currency": "EUR",
            "merchant": "Marchand test",
            "decision": decision,
        },
        {},
        "🛒️",
        "fr",
    )

    assert card["price"] == 99.99
    assert card["decision"]["facts"]["item_price"] == 99.99
    assert card["evidence_current"] is True
    assert card["buy"] is True


def test_real_decision_shape_can_support_buy_only_with_all_required_evidence():
    from app.services.decision import compute_decision
    from app.services.recommend import _build_real_card

    now = datetime.now(UTC)
    history = [
        (120.0, now - timedelta(days=8)),
        (115.0, now - timedelta(days=7)),
        (110.0, now - timedelta(days=5)),
        (100.0, now - timedelta(days=3)),
        (90.0, now - timedelta(days=1)),
        (80.0, now),
    ]
    decision = compute_decision(
        price=80.0,
        currency="EUR",
        history=history,
        history_currency="EUR",
        cheapest_elsewhere=80.0,
        comparison_currency="EUR",
        merchants_count=2,
        offers_count=2,
        in_stock=True,
        now=now,
    )

    assert decision["recommendation_scope"] == "meilleur_prix_observe"
    assert decision["price_verdict"]["level"] in {"excellent", "bon"}
    card = _build_real_card(
        0,
        {
            "name": "Produit complètement documenté",
            "price": 80,
            "currency": "EUR",
            "merchant": "Marchand test",
            "decision": decision,
        },
        {},
        "🛒️",
        "fr",
    )

    assert card["evidence_current"] is True
    assert card["buy"] is True


def test_real_cache_requires_the_explicit_current_evidence_marker():
    from app.services.recommend import _build_real_card, _revalidate_cached_cards

    card = _build_real_card(
        0,
        {
            "offer_id": 182,
            "name": "Produit documenté",
            "price": 99,
            "currency": "EUR",
            "merchant": "Marchand test",
            "decision": _decision("meilleur_prix_observe", "bon"),
        },
        {},
        "🛒️",
        "fr",
    )
    cached = {"real": True, "offers": 1, "cards": [card]}

    assert card["evidence_current"] is True
    assert _revalidate_cached_cards(deepcopy(cached)) is True

    missing_marker = deepcopy(cached)
    missing_marker["cards"][0].pop("evidence_current")
    assert _revalidate_cached_cards(missing_marker) is False

    false_marker = deepcopy(cached)
    false_marker["cards"][0]["evidence_current"] = False
    assert _revalidate_cached_cards(false_marker) is False


def test_real_card_keeps_a_missing_currency_unknown_and_blocks_a_favourable_claim():
    from app.services.recommend import _build_real_card

    product = {
        "offer_id": 19,
        "product_ean": "1234567890125",
        "name": "Produit sans devise",
        "price": 1,
        "currency": None,
        "merchant": "Marchand test",
        "link": None,
        # Même une décision amont incohérente ne doit pas contourner le
        # garde-fou du dernier caller qui construit la carte publique.
        "decision": _decision("meilleur_prix_observe", "bon"),
    }

    card = _build_real_card(0, product, {}, "🛒️", "fr")

    assert card["currency"] is None
    assert card["evidence_current"] is False
    assert card["buy"] is False


def test_real_card_blocks_buy_when_decision_currency_does_not_match_offer():
    from app.services.recommend import _build_real_card

    decision = _decision("meilleur_prix_observe", "bon")
    decision["facts"]["currency"] = "GBP"
    card = _build_real_card(
        0,
        {
            "name": "Produit EUR",
            "price": 99,
            "currency": "EUR",
            "merchant": "Marchand test",
            "decision": decision,
        },
        {},
        "🛒️",
        "fr",
    )

    assert card["buy"] is False


def test_real_card_blocks_buy_when_stock_is_unknown():
    from app.services.recommend import _build_real_card

    decision = _decision("meilleur_prix_observe", "bon")
    decision["signals"][0] = {"key": "availability", "status": "unknown"}
    card = _build_real_card(
        0,
        {
            "name": "Produit au stock inconnu",
            "price": 99,
            "currency": "EUR",
            "merchant": "Marchand test",
            "decision": decision,
        },
        {},
        "🛒️",
        "fr",
    )

    assert card["buy"] is False


def test_real_card_blocks_buy_when_observation_is_stale():
    from app.services.freshness import OFFER_RECOMMENDATION_MAX_AGE_HOURS
    from app.services.recommend import _build_real_card

    decision = _decision("meilleur_prix_observe", "bon")
    decision["signals"][1] = {
        "key": "freshness",
        "status": "warning",
        "age_hours": OFFER_RECOMMENDATION_MAX_AGE_HOURS + 1,
    }
    card = _build_real_card(
        0,
        {
            "name": "Produit ancien",
            "price": 99,
            "currency": "EUR",
            "merchant": "Marchand test",
            "decision": decision,
        },
        {},
        "🛒️",
        "fr",
    )

    assert card["buy"] is False


def test_real_card_blocks_buy_when_observed_at_contradicts_a_fresh_signal():
    from app.services.recommend import _build_real_card

    decision = _decision("meilleur_prix_observe", "bon")
    decision["facts"]["last_observed_at"] = "2000-01-01T00:00:00+00:00"
    card = _build_real_card(
        0,
        {
            "name": "Produit à date ancienne",
            "price": 99,
            "currency": "EUR",
            "merchant": "Marchand test",
            "decision": decision,
        },
        {},
        "🛒️",
        "fr",
    )

    assert card["buy"] is False


def test_real_card_does_not_replace_an_explicit_stale_snapshot_with_decision_facts():
    from app.services.recommend import _build_real_card

    card = _build_real_card(
        0,
        {
            "name": "Produit au snapshot explicitement ancien",
            "price": 99,
            "currency": "EUR",
            "merchant": "Marchand test",
            "in_stock": True,
            "observed_at": "2000-01-01T00:00:00+00:00",
            "decision": _decision("meilleur_prix_observe", "bon"),
        },
        {},
        "🛒️",
        "fr",
    )

    assert card["observed_at"] is None
    assert card["evidence_current"] is False
    assert card["buy"] is False


def test_real_card_blocks_buy_without_a_historical_verdict_basis():
    from app.services.recommend import _build_real_card

    decision = _decision("meilleur_prix_observe", "bon")
    decision["price_verdict"].pop("basis")
    card = _build_real_card(
        0,
        {
            "name": "Produit sans provenance historique",
            "price": 99,
            "currency": "EUR",
            "merchant": "Marchand test",
            "decision": decision,
        },
        {},
        "🛒️",
        "fr",
    )

    assert card["buy"] is False


def test_real_card_blocks_buy_without_canonical_evidence_dimensions():
    from app.services.recommend import _build_real_card

    decision = _decision("meilleur_prix_observe", "bon")
    decision.pop("evidence")
    card = _build_real_card(
        0,
        {
            "name": "Produit sans preuves canoniques",
            "price": 99,
            "currency": "EUR",
            "merchant": "Marchand test",
            "decision": decision,
        },
        {},
        "🛒️",
        "fr",
    )

    assert card["buy"] is False


def test_real_card_blocks_buy_when_decision_price_does_not_match_card():
    from app.services.recommend import _build_real_card

    decision = _decision("meilleur_prix_observe", "bon")
    decision["facts"]["item_price"] = 80
    card = _build_real_card(
        0,
        {
            "name": "Produit mal apparié",
            "price": 999,
            "currency": "EUR",
            "merchant": "Marchand test",
            "decision": decision,
        },
        {},
        "🛒️",
        "fr",
    )

    assert card["buy"] is False


def test_real_card_blocks_buy_without_a_dated_observation():
    from app.services.recommend import _build_real_card

    decision = _decision("meilleur_prix_observe", "bon")
    decision["facts"]["last_observed_at"] = None
    card = _build_real_card(
        0,
        {
            "name": "Produit sans observation datée",
            "price": 99,
            "currency": "EUR",
            "merchant": "Marchand test",
            "decision": decision,
        },
        {},
        "🛒️",
        "fr",
    )

    assert card["buy"] is False
