"""Replay borné Personal Commerce Phase 18.

La production ne possède pas encore de cohorte consentante ni de solutions
Phase 17 persistées. Le replay propage donc chaque run BUY/WAIT réel sous forme
d'abstention sans sujet, sans préférence et sans contexte brut.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from sqlalchemy import select

from app.buy_wait.models import BuyWaitDecisionRun
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db import session as db

from .engine import PersonalCommerceRequest, decide_personal_commerce
from .persistence import persist_personal_commerce


REPLAY_VERSION = "personal-commerce-production-replay/v1"
MAX_REPLAY_RUNS = 100


@dataclass(frozen=True)
class PersonalCommerceReplayReport:
    schema_version: str
    replay_version: str
    mode: str
    evaluated_at: str
    after_buy_wait_run_id: int
    limit: int
    scanned_runs: int
    selected_runs: int
    abstained_runs: int
    runs_created: int
    runs_existing: int
    last_buy_wait_run_id: int | None
    evaluation_id: str


def _validate_window(after_buy_wait_run_id: int, limit: int) -> tuple[int, int]:
    if isinstance(after_buy_wait_run_id, bool) or not isinstance(after_buy_wait_run_id, int) or after_buy_wait_run_id < 0:
        raise ValueError("after_buy_wait_run_id must be a non-negative integer")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_REPLAY_RUNS:
        raise ValueError(f"limit must be between 1 and {MAX_REPLAY_RUNS}")
    return after_buy_wait_run_id, limit


async def replay_personal_commerce_batch(
    session,
    *,
    evaluated_at: datetime,
    after_buy_wait_run_id: int = 0,
    limit: int = 10,
    apply: bool = False,
) -> PersonalCommerceReplayReport:
    after_buy_wait_run_id, limit = _validate_window(after_buy_wait_run_id, limit)
    if evaluated_at.tzinfo is None:
        raise ValueError("evaluated_at must include a timezone")
    evaluated = evaluated_at.astimezone(timezone.utc)
    runs = (
        (
            await session.execute(
                select(BuyWaitDecisionRun)
                .where(BuyWaitDecisionRun.id > after_buy_wait_run_id)
                .order_by(BuyWaitDecisionRun.id)
                .limit(limit)
            )
        ).scalars().all()
    )
    counters = {"selected": 0, "abstained": 0, "created": 0, "existing": 0}
    identities: list[dict[str, object]] = []
    for run in runs:
        request = PersonalCommerceRequest(
            objective_ref=f"buy-wait:{run.id}",
            personalization_consent=False,
            allowed_solution_kinds=("outfit", "setup", "kit", "routine"),
            maximum_budget=None,
            currency=None,
        )
        decision = decide_personal_commerce(request, ())
        report = await persist_personal_commerce(
            session,
            buy_wait_run=run,
            request=request,
            decision=decision,
            evaluated_at=evaluated,
            apply=apply,
        )
        counters["selected" if decision.outcome == "SOLUTION_SELECTED" else "abstained"] += 1
        counters["created"] += report.runs_created
        counters["existing"] += report.runs_existing
        identities.append({
            "buy_wait_run_id": run.id,
            "result_digest": decision.result_digest,
            "run_key": report.run_key,
        })
    payload = json.dumps(identities, sort_keys=True, separators=(",", ":")).encode()
    return PersonalCommerceReplayReport(
        "personal-commerce-replay-report/v1",
        REPLAY_VERSION,
        "apply" if apply else "dry_run",
        evaluated.isoformat().replace("+00:00", "Z"),
        after_buy_wait_run_id,
        limit,
        len(runs),
        counters["selected"],
        counters["abstained"],
        counters["created"],
        counters["existing"],
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


async def _run(args: argparse.Namespace) -> PersonalCommerceReplayReport:
    settings = get_settings()
    configure_logging(settings.debug)
    if args.apply and not settings.personal_commerce_shadow_enabled:
        raise RuntimeError("PERSONAL_COMMERCE_SHADOW_ENABLED is required for --apply")
    if not db.is_enabled():
        raise RuntimeError("DATABASE_URL is required")
    await db.prepare_schema()
    async with db.session_scope() as session:
        if session is None:
            raise RuntimeError("database session unavailable")
        return await replay_personal_commerce_batch(
            session,
            evaluated_at=args.evaluated_at,
            after_buy_wait_run_id=args.after_buy_wait_run_id,
            limit=args.limit,
            apply=args.apply,
        )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Replay borné Personal Commerce shadow Phase 18")
    parser.add_argument("--evaluated-at", required=True, type=_parse_evaluated_at)
    parser.add_argument("--after-buy-wait-run-id", type=int, default=0)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--apply", action="store_true")
    return parser


def main() -> None:
    report = asyncio.run(_run(_parser().parse_args()))
    print(json.dumps(asdict(report), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
