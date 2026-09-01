"""Writer shadow append-only et idempotent BUY/WAIT V2 Phase 10."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from sqlalchemy import select

from app.confidence.models import ConfidenceCalibrationRun

from .engine import BuyWaitDecision
from .models import BuyWaitDecisionRun


PERSISTENCE_VERSION = "buy-wait-shadow-writer/v1"


class BuyWaitPersistenceError(RuntimeError):
    """Écriture impossible à prouver ou replay divergent."""


@dataclass(frozen=True)
class PersistenceReport:
    schema_version: str
    persistence_version: str
    mode: str
    run_key: str
    outcome: str
    runs_created: int
    runs_existing: int
    result_digest: str
    evaluation_id: str


def _canonical(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _digest(value) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _naive_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise BuyWaitPersistenceError("evaluated_at must include a timezone")
    return value.astimezone(timezone.utc).replace(tzinfo=None)


async def persist_buy_wait(
    session,
    *,
    confidence_run: ConfidenceCalibrationRun,
    evaluated_at: datetime,
    decision: BuyWaitDecision,
    apply: bool = False,
) -> PersistenceReport:
    if confidence_run.id is None:
        raise BuyWaitPersistenceError("confidence run must be persisted")
    if decision.raw_context_retained or decision.future_observations_used:
        raise BuyWaitPersistenceError("raw context or future observation retention is forbidden")
    if decision.outcome in {"BUY_NOW", "WAIT"} and (
        not decision.claims or not decision.evidence_refs or not decision.backtest_profile_ref
    ):
        raise BuyWaitPersistenceError("action decision requires claims, provenance and backtest")
    payload = {
        "confidence_run_key": confidence_run.run_key,
        "evaluated_at": _naive_utc(evaluated_at).isoformat() + "Z",
        "decision": asdict(decision),
    }
    run_key = _digest(payload)
    created = existing_count = 0
    if apply:
        existing = await session.scalar(
            select(BuyWaitDecisionRun).where(BuyWaitDecisionRun.run_key == run_key)
        )
        if existing is not None:
            if existing.result_digest != decision.result_digest or existing.outcome != decision.outcome:
                raise BuyWaitPersistenceError("buy-wait replay divergence")
            existing_count = 1
        else:
            row = BuyWaitDecisionRun(
                run_key=run_key,
                confidence_run_id=confidence_run.id,
                context_digest=decision.context_digest,
                raw_context_retained=False,
                policy_version=decision.policy_version,
                outcome=decision.outcome,
                selected_offer_ref=decision.selected_offer_ref,
                selected_product_ref=decision.selected_product_ref,
                current_price_decimal=decision.current_price_decimal,
                currency=decision.currency,
                history_samples=decision.history_samples,
                tracked_days=decision.tracked_days,
                current_percentile_decimal=decision.current_percentile_decimal,
                decision_confidence_decimal=decision.decision_confidence_decimal,
                backtest_profile_ref=decision.backtest_profile_ref,
                future_observations_used=False,
                reason_codes_json=list(decision.reason_codes),
                claims_json=[asdict(item) for item in decision.claims],
                evidence_refs_json=list(decision.evidence_refs),
                result_digest=decision.result_digest,
                evaluated_at=_naive_utc(evaluated_at),
            )
            session.add(row)
            await session.flush()
            await session.commit()
            created = 1
    return PersistenceReport(
        "buy-wait-persistence-report/v1", PERSISTENCE_VERSION,
        "apply" if apply else "dry_run", run_key, decision.outcome,
        created, existing_count, decision.result_digest,
        "sha256:" + _digest({"run_key": run_key, "result_digest": decision.result_digest}),
    )
