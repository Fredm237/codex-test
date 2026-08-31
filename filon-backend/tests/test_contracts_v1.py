"""Compatibility suite des contrats publics FILON v1."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.agents import decision, price_compare, product_search
from app.schemas.advise import Offer


CONTRACTS = Path(__file__).resolve().parents[2] / "contracts" / "v1"


def _json(relative: str) -> dict:
    return json.loads((CONTRACTS / relative).read_text(encoding="utf-8"))


def test_manifest_v1_est_fige_et_tous_les_artefacts_existent():
    manifest = _json("manifest.json")
    assert manifest["contract_version"] == "1.0.0"
    assert manifest["status"] == "frozen"
    assert manifest["compatibility"]["unknown"] == "null_is_not_zero_false_or_true"
    for relative in [*manifest["artifacts"].values(), *manifest["examples"].values()]:
        assert (CONTRACTS / relative).is_file(), relative


def test_advise_unknown_reste_null_du_snapshot_au_modele():
    snapshot = _json("examples/advise-offer.unknown.json")
    offer = Offer(**snapshot)
    assert offer.delivery_cost is None
    assert offer.in_stock is None
    assert offer.currency == "EUR"
    assert offer.observed_at is None
    assert offer.model_dump()["delivery_cost"] is None
    assert offer.model_dump()["in_stock"] is None
    assert offer.model_dump()["currency"] == "EUR"
    assert offer.model_dump()["observed_at"] is None

    schema = _json("advise-offer.schema.json")
    assert "null" in schema["properties"]["delivery_cost"]["type"]
    assert "null" in schema["properties"]["in_stock"]["type"]
    assert "null" in schema["properties"]["observed_at"]["type"]
    assert "string" in schema["properties"]["currency"]["type"]


@pytest.mark.parametrize(
    ("field", "value"),
    [("price", 0), ("delivery_cost", -1), ("delivery_days", -1), ("warranty_months", -1)],
)
def test_les_valeurs_monetaires_et_durees_invalides_sont_refusees(field, value):
    payload = {"merchant": "Partenaire", "price": 10.0, field: value}
    with pytest.raises(ValidationError):
        Offer(**payload)


@pytest.mark.asyncio
async def test_stock_inconnu_n_est_pas_eligible_au_comparateur():
    state = {
        "candidates": [
            {
                "product_id": "p-unknown",
                "offers": [
                    {"merchant": "Partenaire", "price": 10.0, "in_stock": None}
                ],
            }
        ]
    }
    result = await price_compare.run(state)
    entry = result["enriched"]["p-unknown"]
    assert "best_offer" not in entry
    assert entry["eligibility"] == "availability_unknown_or_unavailable"


@pytest.mark.asyncio
async def test_absence_de_catalogue_reel_ne_declenche_aucune_demo(monkeypatch):
    async def empty_search(*_args, **_kwargs):
        return []

    monkeypatch.setattr(product_search, "search_products", empty_search)
    state = {
        "query": "ordinateur",
        "criteria": type("Criteria", (), {"budget_max": None, "category": None})(),
        "trace": [],
    }
    result = await product_search.run(state)
    assert result["candidates"] == []
    assert "démonstration" not in " ".join(result["trace"])


@pytest.mark.asyncio
async def test_livraison_inconnue_n_est_pas_annoncee_comme_gratuite_ou_incluse():
    state = {
        "candidates": [
            {"product_id": "p-1", "name": "Produit observé", "relevance": 1.0}
        ],
        "enriched": {
            "p-1": {
                "best_offer": {
                    "merchant": "Partenaire",
                    "price": 25.0,
                    "delivery_cost": None,
                    "in_stock": True,
                },
                "market_avg": 25.0,
                "history": None,
                "cashback": None,
                "promo": None,
                "reviews": None,
            }
        },
        "trace": [],
    }
    result = await decision.run(state)
    recommendation = result["recommendation"]
    assert recommendation["verdict"] == "attendre"
    assert "hors frais de livraison non renseignés" in recommendation["headline"]
    assert "tout compris" not in recommendation["headline"]
