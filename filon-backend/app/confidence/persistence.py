"""Writer shadow append-only et idempotent Confidence Phase 9."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from sqlalchemy import select

from app.offer_optimization.models import OfferOptimizationRun

from .engine import ConfidenceReport, PROBABILITY_DIMENSIONS
from .models import ConfidenceCalibrationRun, ConfidenceDimensionRecord


PERSISTENCE_VERSION = "confidence-shadow-writer/v1"


class ConfidencePersistenceError(RuntimeError):
    """Écriture impossible à prouver ou replay divergent."""


@dataclass(frozen=True)
class PersistenceReport:
    schema_version: str
    persistence_version: str
    mode: str
    run_key: str
    outcome: str
    dimensions: int
    calibrated_dimensions: int
    runs_created: int
    runs_existing: int
    dimensions_created: int
    dimensions_existing: int
    result_digest: str
    evaluation_id: str


def _canonical(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _digest(value) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _naive_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ConfidencePersistenceError("evaluated_at must include a timezone")
    return value.astimezone(timezone.utc).replace(tzinfo=None)


async def persist_confidence(
    session,
    *,
    offer_optimization_run: OfferOptimizationRun,
    evaluated_at: datetime,
    confidence: ConfidenceReport,
    apply: bool = False,
) -> PersistenceReport:
    if offer_optimization_run.id is None:
        raise ConfidencePersistenceError("offer optimization run must be persisted")
    if confidence.raw_context_retained:
        raise ConfidencePersistenceError("raw context retention is forbidden")
    if tuple(item.dimension for item in confidence.dimensions) != PROBABILITY_DIMENSIONS:
        raise ConfidencePersistenceError("confidence dimensions are incomplete or unordered")
    payload = {
        "offer_optimization_run_key": offer_optimization_run.run_key,
        "context_digest": confidence.context_digest,
        "policy_version": confidence.policy_version,
        "outcome": confidence.outcome,
        "result_digest": confidence.result_digest,
        "evaluated_at": _naive_utc(evaluated_at).isoformat() + "Z",
        "dimensions": [asdict(item) for item in confidence.dimensions],
        "evidence_coverage": asdict(confidence.evidence_coverage),
    }
    run_key = _digest(payload)
    runs_created = runs_existing = dimensions_created = dimensions_existing = 0
    if apply:
        existing = await session.scalar(
            select(ConfidenceCalibrationRun).where(ConfidenceCalibrationRun.run_key == run_key)
        )
        if existing is not None:
            rows = (
                (
                    await session.execute(
                        select(ConfidenceDimensionRecord)
                        .where(ConfidenceDimensionRecord.run_id == existing.id)
                        .order_by(ConfidenceDimensionRecord.id)
                    )
                )
                .scalars()
                .all()
            )
            if existing.result_digest != confidence.result_digest or len(rows) != len(confidence.dimensions):
                raise ConfidencePersistenceError("confidence replay divergence")
            runs_existing = 1
            dimensions_existing = len(rows)
        else:
            coverage = confidence.evidence_coverage
            calibrated = sum(item.state == "CALIBRATED" for item in confidence.dimensions)
            run = ConfidenceCalibrationRun(
                run_key=run_key,
                offer_optimization_run_id=offer_optimization_run.id,
                context_digest=confidence.context_digest,
                raw_context_retained=False,
                policy_version=confidence.policy_version,
                outcome=confidence.outcome,
                dimension_count=len(confidence.dimensions),
                calibrated_dimension_count=calibrated,
                evidence_coverage_state=coverage.state,
                evidence_coverage_ratio=coverage.ratio_decimal,
                evidence_observed_count=coverage.observed_evidence_count,
                evidence_required_count=coverage.required_evidence_count,
                evidence_refs_json=list(coverage.evidence_refs),
                result_digest=confidence.result_digest,
                evaluated_at=_naive_utc(evaluated_at),
            )
            session.add(run)
            await session.flush()
            rows = [
                ConfidenceDimensionRecord(
                    run_id=run.id,
                    dimension=item.dimension,
                    state=item.state,
                    probability_decimal=item.probability_decimal,
                    sample_size=item.sample_size,
                    profile_ref=item.profile_ref,
                    reason_codes_json=list(item.reason_codes),
                    evidence_refs_json=list(item.evidence_refs),
                )
                for item in confidence.dimensions
            ]
            session.add_all(rows)
            await session.flush()
            await session.commit()
            runs_created = 1
            dimensions_created = len(rows)
    evaluation_id = "sha256:" + _digest(
        {"run_key": run_key, "result_digest": confidence.result_digest}
    )
    return PersistenceReport(
        "confidence-persistence-report/v1",
        PERSISTENCE_VERSION,
        "apply" if apply else "dry_run",
        run_key,
        confidence.outcome,
        len(confidence.dimensions),
        sum(item.state == "CALIBRATED" for item in confidence.dimensions),
        runs_created,
        runs_existing,
        dimensions_created,
        dimensions_existing,
        confidence.result_digest,
        evaluation_id,
    )
