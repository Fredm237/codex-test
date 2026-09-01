from __future__ import annotations

import json
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from pathlib import Path

from jsonschema import Draft202012Validator

from app.buy_wait.engine import (
    BuyWaitRequest,
    DecisionConfidence,
    PriceObservation,
    decide_buy_wait,
)


ROOT = Path(__file__).resolve().parents[2] / "contracts" / "buy-wait" / "v2"


def test_buy_wait_schema_and_synthetic_examples_are_valid() -> None:
    schema = json.loads((ROOT / "buy-wait-decision.schema.json").read_text())
    validator = Draft202012Validator(schema)
    for name in ("buy-now.json", "wait.json", "abstain.json"):
        payload = json.loads((ROOT / "examples" / name).read_text())
        assert list(validator.iter_errors(payload)) == []


def test_buy_wait_manifest_is_fail_closed() -> None:
    manifest = json.loads((ROOT / "manifest.json").read_text())
    assert manifest["outcomes"] == ["BUY_NOW", "WAIT", "ABSTAIN"]
    assert manifest["future_observations_allowed"] is False
    assert manifest["raw_context_retained"] is False


def test_action_without_backtest_or_claims_is_rejected() -> None:
    schema = json.loads((ROOT / "buy-wait-decision.schema.json").read_text())
    payload = json.loads((ROOT / "examples" / "buy-now.json").read_text())
    payload["backtest_profile_ref"] = None
    payload["claims"] = []
    assert list(Draft202012Validator(schema).iter_errors(payload))


def test_engine_output_conforms_to_the_public_contract() -> None:
    now = datetime(2026, 9, 1, 12, tzinfo=UTC)
    prices = ("100", "101", "99", "102", "100", "98", "101", "80")
    history = tuple(
        PriceObservation(
            amount,
            "EUR",
            now - timedelta(days=(7 - index) * 2),
            True,
            (f"price:{index}",),
        )
        for index, amount in enumerate(prices)
    )
    decision = decide_buy_wait(
        BuyWaitRequest(
            "contract:engine",
            now,
            "offer:1",
            "variant:1",
            history[-1],
            history,
            DecisionConfidence(
                "CALIBRATED", "0.900000", 1000,
                "confidence:decision:v1", ("confidence:evidence",),
            ),
            "backtest:buy-wait:v2:holdout",
        )
    )
    payload = json.loads(json.dumps(asdict(decision)))
    schema = json.loads((ROOT / "buy-wait-decision.schema.json").read_text())
    assert list(Draft202012Validator(schema).iter_errors(payload)) == []
