"""Writer shadow append-only et idempotent Product Ranking."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Mapping

from sqlalchemy import select

from app.constraint_engine.models import ConstraintEvaluationRun

from .engine import ProductRanking
from .models import ProductRankingCandidate, ProductRankingRun


PERSISTENCE_VERSION = "product-ranking-shadow-writer/v1"


class ProductRankingPersistenceError(RuntimeError):
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
        raise ProductRankingPersistenceError("evaluated_at must include a timezone")
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def _entity_type(entity_ref: str) -> str:
    value = entity_ref.split(":", 1)[0].upper()
    if value not in {"PRODUCT", "MODEL", "VARIANT"}:
        raise ProductRankingPersistenceError("entity ref type is unsupported")
    return value


async def persist_product_ranking(
    session,
    *,
    constraint_run: ConstraintEvaluationRun,
    candidate_ids: Mapping[str, int],
    evaluated_at: datetime,
    ranking: ProductRanking,
    apply: bool = False,
) -> PersistenceReport:
    if constraint_run.id is None:
        raise ProductRankingPersistenceError("constraint run must be persisted")
    if ranking.raw_context_retained:
        raise ProductRankingPersistenceError("raw context retention is forbidden")
    if set(candidate_ids) != {item.entity_ref for item in ranking.candidates}:
        raise ProductRankingPersistenceError("constraint candidate mapping is incomplete")
    payload = {
        "constraint_run_key": constraint_run.run_key,
        "context_digest": ranking.context_digest,
        "policy_version": ranking.policy_version,
        "vertical": ranking.vertical,
        "outcome": ranking.outcome,
        "result_digest": ranking.result_digest,
        "evaluated_at": _naive_utc(evaluated_at).isoformat() + "Z",
        "candidates": [asdict(item) for item in ranking.candidates],
    }
    run_key = _digest(payload)
    runs_created = runs_existing = candidates_created = candidates_existing = 0
    if apply:
        existing = await session.scalar(select(ProductRankingRun).where(ProductRankingRun.run_key == run_key))
        if existing is not None:
            rows = (
                (
                    await session.execute(
                        select(ProductRankingCandidate)
                        .where(ProductRankingCandidate.run_id == existing.id)
                        .order_by(ProductRankingCandidate.id)
                    )
                )
                .scalars()
                .all()
            )
            if existing.result_digest != ranking.result_digest or len(rows) != len(ranking.candidates):
                raise ProductRankingPersistenceError("product ranking replay divergence")
            runs_existing = 1
            candidates_existing = len(rows)
        else:
            counts = {
                status: sum(item.status == status for item in ranking.candidates)
                for status in ("RANKED", "UNRANKABLE", "INELIGIBLE")
            }
            run = ProductRankingRun(
                run_key=run_key,
                constraint_run_id=constraint_run.id,
                context_digest=ranking.context_digest,
                raw_context_retained=False,
                policy_version=ranking.policy_version,
                vertical=ranking.vertical,
                outcome=ranking.outcome,
                candidate_count=len(ranking.candidates),
                ranked_count=counts["RANKED"],
                unrankable_count=counts["UNRANKABLE"],
                ineligible_count=counts["INELIGIBLE"],
                result_digest=ranking.result_digest,
                evaluated_at=_naive_utc(evaluated_at),
            )
            session.add(run)
            await session.flush()
            rows = [
                ProductRankingCandidate(
                    run_id=run.id,
                    constraint_candidate_id=candidate_ids[item.entity_ref],
                    entity_type=_entity_type(item.entity_ref),
                    entity_ref=item.entity_ref,
                    status=item.status,
                    product_rank=item.rank,
                    utility=item.utility,
                    dimensions_json=[asdict(dimension) for dimension in item.dimensions],
                    reason_codes_json=list(item.reason_codes),
                )
                for item in ranking.candidates
            ]
            session.add_all(rows)
            await session.flush()
            await session.commit()
            runs_created = 1
            candidates_created = len(rows)
    evaluation_id = "sha256:" + _digest({"run_key": run_key, "result_digest": ranking.result_digest})
    return PersistenceReport(
        "product-ranking-persistence-report/v1",
        PERSISTENCE_VERSION,
        "apply" if apply else "dry_run",
        run_key,
        ranking.outcome,
        len(ranking.candidates),
        runs_created,
        runs_existing,
        candidates_created,
        candidates_existing,
        ranking.result_digest,
        evaluation_id,
    )
