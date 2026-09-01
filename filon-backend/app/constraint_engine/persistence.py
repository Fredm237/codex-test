"""Writer shadow append-only et idempotent Constraint Engine."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from sqlalchemy import select

from app.hybrid_retrieval.models import HybridRetrievalRun

from .engine import CandidateEvaluation, ConstraintEvaluation
from .models import ConstraintCandidateEvaluation, ConstraintEvaluationRun


PERSISTENCE_VERSION = "constraint-engine-shadow-writer/v1"


class ConstraintPersistenceError(RuntimeError):
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


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _naive_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ConstraintPersistenceError("evaluated_at must include a timezone")
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def _entity_type(entity_ref: str) -> str:
    value = entity_ref.split(":", 1)[0].upper()
    if value not in {"PRODUCT", "MODEL", "VARIANT"}:
        raise ConstraintPersistenceError("entity ref type is unsupported")
    return value


async def persist_constraint_evaluation(
    session,
    *,
    retrieval_run: HybridRetrievalRun,
    candidate_ids: Mapping[str, int],
    evaluated_at: datetime,
    evaluation: ConstraintEvaluation,
    apply: bool = False,
) -> PersistenceReport:
    if retrieval_run.id is None:
        raise ConstraintPersistenceError("retrieval run must be persisted")
    if evaluation.raw_context_retained:
        raise ConstraintPersistenceError("raw context retention is forbidden")
    if set(candidate_ids) != {item.entity_ref for item in evaluation.candidates}:
        raise ConstraintPersistenceError("retrieval candidate mapping is incomplete")
    payload = {
        "retrieval_run_key": retrieval_run.run_key,
        "context_digest": evaluation.context_digest,
        "policy_version": evaluation.policy_version,
        "outcome": evaluation.outcome,
        "result_digest": evaluation.result_digest,
        "evaluated_at": _naive_utc(evaluated_at).isoformat() + "Z",
        "candidates": [asdict(item) for item in evaluation.candidates],
    }
    run_key = _digest(payload)
    runs_created = runs_existing = candidates_created = candidates_existing = 0
    if apply:
        existing = await session.scalar(
            select(ConstraintEvaluationRun).where(ConstraintEvaluationRun.run_key == run_key)
        )
        if existing is not None:
            rows = (
                (
                    await session.execute(
                        select(ConstraintCandidateEvaluation)
                        .where(ConstraintCandidateEvaluation.run_id == existing.id)
                        .order_by(ConstraintCandidateEvaluation.id)
                    )
                )
                .scalars()
                .all()
            )
            if existing.result_digest != evaluation.result_digest or len(rows) != len(evaluation.candidates):
                raise ConstraintPersistenceError("constraint evaluation replay divergence")
            runs_existing = 1
            candidates_existing = len(rows)
        else:
            counts = {
                status: sum(item.status == status for item in evaluation.candidates)
                for status in ("ELIGIBLE", "EXCLUDED", "UNKNOWN")
            }
            run = ConstraintEvaluationRun(
                run_key=run_key,
                retrieval_run_id=retrieval_run.id,
                context_digest=evaluation.context_digest,
                raw_context_retained=False,
                policy_version=evaluation.policy_version,
                outcome=evaluation.outcome,
                candidate_count=len(evaluation.candidates),
                eligible_count=counts["ELIGIBLE"],
                excluded_count=counts["EXCLUDED"],
                unknown_count=counts["UNKNOWN"],
                result_digest=evaluation.result_digest,
                evaluated_at=_naive_utc(evaluated_at),
            )
            session.add(run)
            await session.flush()
            rows = [
                ConstraintCandidateEvaluation(
                    run_id=run.id,
                    retrieval_candidate_id=candidate_ids[item.entity_ref],
                    entity_type=_entity_type(item.entity_ref),
                    entity_ref=item.entity_ref,
                    status=item.status,
                    hard_results_json=[asdict(result) for result in item.hard_constraints],
                    preference_results_json=[asdict(result) for result in item.preferences],
                    reason_codes_json=list(item.reason_codes),
                )
                for item in evaluation.candidates
            ]
            session.add_all(rows)
            await session.flush()
            await session.commit()
            runs_created = 1
            candidates_created = len(rows)
    evaluation_id = "sha256:" + _digest({"run_key": run_key, "result_digest": evaluation.result_digest})
    return PersistenceReport(
        schema_version="constraint-persistence-report/v1",
        persistence_version=PERSISTENCE_VERSION,
        mode="apply" if apply else "dry_run",
        run_key=run_key,
        outcome=evaluation.outcome,
        candidates=len(evaluation.candidates),
        runs_created=runs_created,
        runs_existing=runs_existing,
        candidates_created=candidates_created,
        candidates_existing=candidates_existing,
        result_digest=evaluation.result_digest,
        evaluation_id=evaluation_id,
    )
