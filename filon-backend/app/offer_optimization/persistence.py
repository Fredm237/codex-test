"""Writer shadow append-only et idempotent Offer Optimization."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Mapping

from sqlalchemy import select

from app.product_ranking.models import ProductRankingRun

from .engine import OfferOptimization
from .models import OfferOptimizationCandidate, OfferOptimizationRun


PERSISTENCE_VERSION = "offer-optimization-shadow-writer/v2"


class OfferOptimizationPersistenceError(RuntimeError):
    """Écriture impossible à prouver ou replay divergent."""


@dataclass(frozen=True)
class PersistenceReport:
    schema_version: str
    persistence_version: str
    mode: str
    run_key: str
    outcome: str
    candidates: int
    runs_created: int
    runs_existing: int
    candidates_created: int
    candidates_existing: int
    result_digest: str
    evaluation_id: str


def _canonical(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _digest(value) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _naive_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise OfferOptimizationPersistenceError("evaluated_at must include a timezone")
    return value.astimezone(timezone.utc).replace(tzinfo=None)


async def persist_offer_optimization(
    session,
    *,
    product_ranking_run: ProductRankingRun,
    snapshot_ids: Mapping[str, int],
    evaluated_at: datetime,
    optimization: OfferOptimization,
    apply: bool = False,
) -> PersistenceReport:
    if product_ranking_run.id is None:
        raise OfferOptimizationPersistenceError("product ranking run must be persisted")
    if optimization.raw_context_retained:
        raise OfferOptimizationPersistenceError("raw context retention is forbidden")
    if set(snapshot_ids) != {item.offer_ref for item in optimization.evaluations}:
        raise OfferOptimizationPersistenceError("offer truth snapshot mapping is incomplete")
    payload = {
        "product_ranking_run_key": product_ranking_run.run_key,
        "context_digest": optimization.context_digest,
        "policy_version": optimization.policy_version,
        "outcome": optimization.outcome,
        "selected_product_ref": optimization.selected_product_ref,
        "selected_offer_ref": optimization.selected_offer_ref,
        "result_digest": optimization.result_digest,
        "evaluated_at": _naive_utc(evaluated_at).isoformat() + "Z",
        "evaluations": [asdict(item) for item in optimization.evaluations],
    }
    run_key = _digest(payload)
    runs_created = runs_existing = candidates_created = candidates_existing = 0
    if apply:
        existing = await session.scalar(
            select(OfferOptimizationRun).where(OfferOptimizationRun.run_key == run_key)
        )
        if existing is not None:
            rows = (
                (
                    await session.execute(
                        select(OfferOptimizationCandidate)
                        .where(OfferOptimizationCandidate.run_id == existing.id)
                        .order_by(OfferOptimizationCandidate.id)
                    )
                )
                .scalars()
                .all()
            )
            if (
                existing.result_digest != optimization.result_digest
                or existing.selected_offer_ref != optimization.selected_offer_ref
                or len(rows) != len(optimization.evaluations)
            ):
                raise OfferOptimizationPersistenceError("offer optimization replay divergence")
            runs_existing = 1
            candidates_existing = len(rows)
        else:
            counts = {
                status: sum(item.status == status for item in optimization.evaluations)
                for status in ("SELECTED", "ELIGIBLE", "UNOPTIMIZABLE", "INELIGIBLE")
            }
            run = OfferOptimizationRun(
                run_key=run_key,
                product_ranking_run_id=product_ranking_run.id,
                context_digest=optimization.context_digest,
                raw_context_retained=False,
                policy_version=optimization.policy_version,
                outcome=optimization.outcome,
                selected_product_ref=optimization.selected_product_ref,
                selected_offer_ref=optimization.selected_offer_ref,
                candidate_count=len(optimization.evaluations),
                selected_count=counts["SELECTED"],
                eligible_count=counts["ELIGIBLE"],
                unoptimizable_count=counts["UNOPTIMIZABLE"],
                ineligible_count=counts["INELIGIBLE"],
                result_digest=optimization.result_digest,
                evaluated_at=_naive_utc(evaluated_at),
            )
            session.add(run)
            await session.flush()
            rows = [
                OfferOptimizationCandidate(
                    run_id=run.id,
                    offer_truth_snapshot_id=snapshot_ids[item.offer_ref],
                    offer_ref=item.offer_ref,
                    product_ref=item.product_ref,
                    status=item.status,
                    selection_rank=item.selection_rank,
                    total_cost=item.total_cost,
                    cashback_amount=item.cashback_amount,
                    landed_cost=item.landed_cost,
                    currency=item.currency,
                    return_period_days=item.return_period_days,
                    merchant_reliability=item.merchant_reliability,
                    freshness=item.freshness,
                    reason_codes_json=list(item.reason_codes),
                    evidence_refs_json=list(item.evidence_refs),
                )
                for item in optimization.evaluations
            ]
            session.add_all(rows)
            await session.flush()
            await session.commit()
            runs_created = 1
            candidates_created = len(rows)
    evaluation_id = "sha256:" + _digest(
        {"run_key": run_key, "result_digest": optimization.result_digest}
    )
    return PersistenceReport(
        "offer-optimization-persistence-report/v1",
        PERSISTENCE_VERSION,
        "apply" if apply else "dry_run",
        run_key,
        optimization.outcome,
        len(optimization.evaluations),
        runs_created,
        runs_existing,
        candidates_created,
        candidates_existing,
        optimization.result_digest,
        evaluation_id,
    )
