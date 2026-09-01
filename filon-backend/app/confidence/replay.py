"""Replay borné Confidence Phase 9.

La production ne contient pas encore de corpus de résultats labellisés et de
profils empiriques ratifiés. Le replay refuse donc de fabriquer une probabilité
depuis les résultats des phases précédentes : il persiste une abstention
explicite, ce qui qualifie le câblage shadow et l'idempotence sans survendre la
confiance.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from sqlalchemy import select

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db import session as db
from app.offer_optimization.models import OfferOptimizationRun

from .engine import ConfidenceRequest, CoverageInput, calibrate_confidence
from .persistence import persist_confidence


REPLAY_VERSION = "confidence-production-replay/v1"
MAX_REPLAY_RUNS = 100


@dataclass(frozen=True)
class ConfidenceReplayReport:
    schema_version: str
    replay_version: str
    mode: str
    evaluated_at: str
    after_offer_optimization_run_id: int
    limit: int
    scanned_runs: int
    calibrated_runs: int
    partial_runs: int
    abstained_runs: int
    calibrated_dimensions: int
    unknown_dimensions: int
    runs_created: int
    runs_existing: int
    dimensions_created: int
    dimensions_existing: int
    last_offer_optimization_run_id: int | None
    evaluation_id: str


def _validate_window(after_offer_optimization_run_id: int, limit: int) -> tuple[int, int]:
    if (
        isinstance(after_offer_optimization_run_id, bool)
        or not isinstance(after_offer_optimization_run_id, int)
        or after_offer_optimization_run_id < 0
    ):
        raise ValueError("after_offer_optimization_run_id must be a non-negative integer")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_REPLAY_RUNS:
        raise ValueError(f"limit must be between 1 and {MAX_REPLAY_RUNS}")
    return after_offer_optimization_run_id, limit


async def replay_confidence_batch(
    session,
    *,
    evaluated_at: datetime,
    after_offer_optimization_run_id: int = 0,
    limit: int = 10,
    apply: bool = False,
) -> ConfidenceReplayReport:
    after_offer_optimization_run_id, limit = _validate_window(
        after_offer_optimization_run_id, limit
    )
    if evaluated_at.tzinfo is None:
        raise ValueError("evaluated_at must include a timezone")
    evaluated = evaluated_at.astimezone(timezone.utc)
    runs = (
        (
            await session.execute(
                select(OfferOptimizationRun)
                .where(OfferOptimizationRun.id > after_offer_optimization_run_id)
                .order_by(OfferOptimizationRun.id)
                .limit(limit)
            )
        )
        .scalars()
        .all()
    )
    counters = {
        key: 0
        for key in (
            "CONFIDENCE_CALIBRATED",
            "PARTIAL_CONFIDENCE",
            "ABSTAINED",
            "calibrated_dimensions",
            "unknown_dimensions",
            "runs_created",
            "runs_existing",
            "dimensions_created",
            "dimensions_existing",
        )
    }
    identities: list[dict[str, object]] = []
    for run in runs:
        request = ConfidenceRequest(
            context_ref=f"p9:{run.id}",
            signals=(),
            evidence_coverage=CoverageInput(0, 0),
        )
        confidence = calibrate_confidence(request, ())
        report = await persist_confidence(
            session,
            offer_optimization_run=run,
            evaluated_at=evaluated,
            confidence=confidence,
            apply=apply,
        )
        counters[confidence.outcome] += 1
        counters["calibrated_dimensions"] += sum(
            item.state == "CALIBRATED" for item in confidence.dimensions
        )
        counters["unknown_dimensions"] += sum(
            item.state == "UNKNOWN" for item in confidence.dimensions
        )
        for key in (
            "runs_created",
            "runs_existing",
            "dimensions_created",
            "dimensions_existing",
        ):
            counters[key] += getattr(report, key)
        identities.append(
            {
                "offer_optimization_run_id": run.id,
                "result_digest": confidence.result_digest,
                "run_key": report.run_key,
            }
        )
    payload = json.dumps(identities, sort_keys=True, separators=(",", ":")).encode()
    return ConfidenceReplayReport(
        "confidence-replay-report/v1",
        REPLAY_VERSION,
        "apply" if apply else "dry_run",
        evaluated.isoformat().replace("+00:00", "Z"),
        after_offer_optimization_run_id,
        limit,
        len(runs),
        counters["CONFIDENCE_CALIBRATED"],
        counters["PARTIAL_CONFIDENCE"],
        counters["ABSTAINED"],
        counters["calibrated_dimensions"],
        counters["unknown_dimensions"],
        counters["runs_created"],
        counters["runs_existing"],
        counters["dimensions_created"],
        counters["dimensions_existing"],
        runs[-1].id if runs else None,
        "sha256:" + hashlib.sha256(payload).hexdigest(),
    )


def _parse_evaluated_at(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise argparse.ArgumentTypeError("evaluated-at must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise argparse.ArgumentTypeError("evaluated-at must include a timezone")
    return parsed


async def _run(args: argparse.Namespace) -> ConfidenceReplayReport:
    settings = get_settings()
    configure_logging(settings.debug)
    if args.apply and not settings.confidence_shadow_enabled:
        raise RuntimeError("CONFIDENCE_SHADOW_ENABLED is required for --apply")
    if not db.is_enabled():
        raise RuntimeError("DATABASE_URL is required")
    await db.prepare_schema()
    async with db.session_scope() as session:
        if session is None:
            raise RuntimeError("database session unavailable")
        return await replay_confidence_batch(
            session,
            evaluated_at=args.evaluated_at,
            after_offer_optimization_run_id=args.after_offer_optimization_run_id,
            limit=args.limit,
            apply=args.apply,
        )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Replay borné Confidence shadow Phase 9")
    parser.add_argument("--evaluated-at", required=True, type=_parse_evaluated_at)
    parser.add_argument("--after-offer-optimization-run-id", type=int, default=0)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--apply", action="store_true")
    return parser


def main() -> None:
    report = asyncio.run(_run(_parser().parse_args()))
    print(json.dumps(asdict(report), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
