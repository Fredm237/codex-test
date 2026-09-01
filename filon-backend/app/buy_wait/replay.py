"""Replay borné BUY/WAIT V2 Phase 10.

La production ne possède pas encore de profil temporel par produit ratifié.
Le replay propage donc l'absence de sélection/historique en abstention au lieu
de fabriquer une action BUY ou WAIT.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from sqlalchemy import select

from app.confidence.models import ConfidenceCalibrationRun
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db import session as db

from .engine import BuyWaitRequest, DecisionConfidence, decide_buy_wait
from .persistence import persist_buy_wait


REPLAY_VERSION = "buy-wait-production-replay/v1"
MAX_REPLAY_RUNS = 100


@dataclass(frozen=True)
class BuyWaitReplayReport:
    schema_version: str
    replay_version: str
    mode: str
    evaluated_at: str
    after_confidence_run_id: int
    limit: int
    scanned_runs: int
    buy_now_runs: int
    wait_runs: int
    abstained_runs: int
    runs_created: int
    runs_existing: int
    last_confidence_run_id: int | None
    evaluation_id: str


def _validate_window(after_confidence_run_id: int, limit: int) -> tuple[int, int]:
    if isinstance(after_confidence_run_id, bool) or not isinstance(after_confidence_run_id, int) or after_confidence_run_id < 0:
        raise ValueError("after_confidence_run_id must be a non-negative integer")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_REPLAY_RUNS:
        raise ValueError(f"limit must be between 1 and {MAX_REPLAY_RUNS}")
    return after_confidence_run_id, limit


async def replay_buy_wait_batch(
    session,
    *,
    evaluated_at: datetime,
    after_confidence_run_id: int = 0,
    limit: int = 10,
    apply: bool = False,
) -> BuyWaitReplayReport:
    after_confidence_run_id, limit = _validate_window(after_confidence_run_id, limit)
    if evaluated_at.tzinfo is None:
        raise ValueError("evaluated_at must include a timezone")
    evaluated = evaluated_at.astimezone(timezone.utc)
    runs = (
        (
            await session.execute(
                select(ConfidenceCalibrationRun)
                .where(ConfidenceCalibrationRun.id > after_confidence_run_id)
                .order_by(ConfidenceCalibrationRun.id)
                .limit(limit)
            )
        ).scalars().all()
    )
    counters = {"BUY_NOW": 0, "WAIT": 0, "ABSTAIN": 0, "created": 0, "existing": 0}
    identities: list[dict[str, object]] = []
    for run in runs:
        request = BuyWaitRequest(
            context_ref=f"p10:{run.id}",
            evaluated_at=evaluated,
            selected_offer_ref=None,
            selected_product_ref=None,
            current=None,
            history=(),
            decision_confidence=DecisionConfidence("UNKNOWN", None, 0, None, ()),
            backtest_profile_ref=None,
        )
        decision = decide_buy_wait(request)
        report = await persist_buy_wait(
            session, confidence_run=run, evaluated_at=evaluated,
            decision=decision, apply=apply,
        )
        counters[decision.outcome] += 1
        counters["created"] += report.runs_created
        counters["existing"] += report.runs_existing
        identities.append({
            "confidence_run_id": run.id,
            "result_digest": decision.result_digest,
            "run_key": report.run_key,
        })
    payload = json.dumps(identities, sort_keys=True, separators=(",", ":")).encode()
    return BuyWaitReplayReport(
        "buy-wait-replay-report/v1", REPLAY_VERSION,
        "apply" if apply else "dry_run",
        evaluated.isoformat().replace("+00:00", "Z"),
        after_confidence_run_id, limit, len(runs),
        counters["BUY_NOW"], counters["WAIT"], counters["ABSTAIN"],
        counters["created"], counters["existing"],
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


async def _run(args: argparse.Namespace) -> BuyWaitReplayReport:
    settings = get_settings()
    configure_logging(settings.debug)
    if args.apply and not settings.buy_wait_shadow_enabled:
        raise RuntimeError("BUY_WAIT_SHADOW_ENABLED is required for --apply")
    if not db.is_enabled():
        raise RuntimeError("DATABASE_URL is required")
    await db.prepare_schema()
    async with db.session_scope() as session:
        if session is None:
            raise RuntimeError("database session unavailable")
        return await replay_buy_wait_batch(
            session, evaluated_at=args.evaluated_at,
            after_confidence_run_id=args.after_confidence_run_id,
            limit=args.limit, apply=args.apply,
        )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Replay borné BUY/WAIT V2 shadow Phase 10")
    parser.add_argument("--evaluated-at", required=True, type=_parse_evaluated_at)
    parser.add_argument("--after-confidence-run-id", type=int, default=0)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--apply", action="store_true")
    return parser


def main() -> None:
    report = asyncio.run(_run(_parser().parse_args()))
    print(json.dumps(asdict(report), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
