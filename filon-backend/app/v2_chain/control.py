"""Vue de contrôle unique de la promotion V2, dérivée des journaux."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from sqlalchemy import select

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db import session as db
from app.v2_chain.coverage_funnel import evaluate_coverage_funnel
from app.v2_chain.models import (
    V2CanaryReadObservation,
    V2ChainExecution,
    V2LiveDarkReadObservation,
    V2PromotionReceipt,
)


MAX_CONTROL_ROWS = 10_000


class V2PromotionControlError(ValueError):
    """La vue de contrôle ne peut pas être calculée honnêtement."""


@dataclass(frozen=True)
class V2WindowPointer:
    execution_id: int
    status: str
    vertical: str
    cursor_start: int
    cursor_end: int
    heartbeat_at: str
    finished_at: str | None


@dataclass(frozen=True)
class V2PromotionControlReport:
    schema_version: str
    evaluated_at: str
    campaign_id: str
    mode: str
    current_window: V2WindowPointer | None
    last_terminal_window: V2WindowPointer | None
    cursor_by_vertical: dict[str, int]
    execution_error_rate_ppm: int | None
    p95_window_ms: int | None
    coverage_status: str
    unknown: int
    abstain: int
    fallback: int
    safety_violations: int
    dark_differences: int
    dark_observations: int
    canary_observations: int
    canary_status: str
    rollback_status: str
    evaluation_id: str

    def to_dict(self) -> dict[str, object]:
        return json.loads(_canonical(asdict(self)))


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _valid_digest(value: object) -> bool:
    if not isinstance(value, str) or not value.startswith("sha256:"):
        return False
    suffix = value.removeprefix("sha256:")
    return len(suffix) == 64 and all(character in "0123456789abcdef" for character in suffix)


def _utc(value: datetime | None) -> str | None:
    if value is None:
        return None
    aware = value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)
    return aware.isoformat().replace("+00:00", "Z")


def _pointer(execution: V2ChainExecution | None) -> V2WindowPointer | None:
    if execution is None:
        return None
    return V2WindowPointer(
        execution_id=execution.id,
        status=execution.status,
        vertical=execution.vertical,
        cursor_start=execution.after_raw_id,
        cursor_end=execution.last_raw_source_id,
        heartbeat_at=_utc(execution.heartbeat_at) or "",
        finished_at=_utc(execution.finished_at),
    )


def _p95_window_ms(executions: list[V2ChainExecution]) -> int | None:
    durations = sorted(
        max(0, math.ceil((item.finished_at - item.started_at).total_seconds() * 1_000))
        for item in executions
        if item.finished_at is not None
    )
    if not durations:
        return None
    return durations[max(1, math.ceil(len(durations) * 0.95)) - 1]


async def build_promotion_control(
    session,
    *,
    campaign_id: str,
    mode: str,
    evaluated_at: datetime,
    promotion_receipt_evaluation_id: str | None = None,
) -> V2PromotionControlReport:
    """Calcule la vue sans lire ni conserver de payload utilisateur."""

    if not _valid_digest(campaign_id):
        raise V2PromotionControlError("campaign id must be a sha256 digest")
    if mode not in {"off", "shadow", "dark", "canary", "public"}:
        raise V2PromotionControlError("V2 mode is invalid")
    if evaluated_at.tzinfo is None:
        raise V2PromotionControlError("evaluated_at must include a timezone")
    if promotion_receipt_evaluation_id is not None and not _valid_digest(
        promotion_receipt_evaluation_id
    ):
        raise V2PromotionControlError("promotion receipt id is invalid")

    executions = list(
        (
            await session.execute(
                select(V2ChainExecution)
                .where(V2ChainExecution.campaign_id == campaign_id)
                .order_by(V2ChainExecution.id)
                .limit(MAX_CONTROL_ROWS + 1)
            )
        )
        .scalars()
        .all()
    )
    dark = list(
        (
            await session.execute(
                select(V2LiveDarkReadObservation)
                .where(V2LiveDarkReadObservation.campaign_id == campaign_id)
                .order_by(V2LiveDarkReadObservation.id)
                .limit(MAX_CONTROL_ROWS + 1)
            )
        )
        .scalars()
        .all()
    )
    receipt = (
        await session.scalar(
            select(V2PromotionReceipt).where(
                V2PromotionReceipt.evaluation_id == promotion_receipt_evaluation_id
            )
        )
        if promotion_receipt_evaluation_id is not None
        else None
    )
    canary_gate_id = (
        receipt.gate_evaluation_id
        if receipt is not None and receipt.promotion_stage == "shadow_to_canary"
        else receipt.source_gate_evaluation_id
        if receipt is not None and receipt.promotion_stage == "canary_to_public"
        else None
    )
    canary = (
        list(
            (
                await session.execute(
                    select(V2CanaryReadObservation)
                    .where(V2CanaryReadObservation.gate_evaluation_id == canary_gate_id)
                    .order_by(V2CanaryReadObservation.id)
                    .limit(MAX_CONTROL_ROWS + 1)
                )
            )
            .scalars()
            .all()
        )
        if canary_gate_id is not None
        else []
    )
    if any(len(rows) > MAX_CONTROL_ROWS for rows in (executions, dark, canary)):
        raise V2PromotionControlError("promotion control exceeds the bounded audit limit")
    running = [item for item in executions if item.status == "running"]
    terminal = [item for item in executions if item.status != "running"]
    completed = [item for item in terminal if item.finished_at is not None]
    cursor_by_vertical: dict[str, int] = {}
    for item in executions:
        if item.status == "succeeded" and item.mode == "apply":
            cursor_by_vertical[item.vertical] = max(
                cursor_by_vertical.get(item.vertical, 0),
                item.last_raw_source_id,
            )
    metrics = [
        item.window_metrics_json
        for item in executions
        if item.status == "succeeded" and isinstance(item.window_metrics_json, dict)
    ]
    terminal_count = len(terminal)
    failed_count = sum(item.status in {"failed", "interrupted"} for item in terminal)
    funnel = await evaluate_coverage_funnel(
        session,
        campaign_id=campaign_id,
        evaluated_at=evaluated_at,
    )
    safety = sum(item.safety_state == "INVALID" for item in dark)
    safety += sum(
        item.v2_latency_us is not None
        and (
            item.safety_state not in {"SAFE", "ABSTAIN"}
            or item.chain_complete is not True
            or item.provenance_complete is not True
            or item.eligibility_status != "eligible"
        )
        for item in canary
    )
    canary_status = receipt.status if receipt is not None else "NOT_AUTHORIZED"
    rollback = (
        "PROOF_REFERENCED"
        if receipt is not None
        and receipt.gates_json.get("dark_reader_rollback") is True
        and "dark_reader_rollback_ref" in receipt.proof_refs_json
        else "NOT_PROVEN"
    )
    identity = {
        "evaluated_at": evaluated_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "campaign_id": campaign_id,
        "mode": mode,
        "current_window": asdict(_pointer(running[-1])) if running else None,
        "last_terminal_window": asdict(_pointer(terminal[-1])) if terminal else None,
        "cursor_by_vertical": cursor_by_vertical,
        "execution_error_rate_ppm": (
            round(failed_count * 1_000_000 / terminal_count) if terminal_count else None
        ),
        "p95_window_ms": _p95_window_ms(completed),
        "coverage_status": funnel.status,
        "unknown": sum(int(item.get("unknown", 0)) for item in metrics),
        "abstain": sum(int(item.get("ABSTAIN", 0)) for item in metrics),
        "fallback": sum(item.source == "core_v1" for item in canary),
        "safety_violations": safety,
        "dark_differences": sum(
            item.classification not in {"BOTH_VALID", "V2_ABSTAINS_CORRECTLY", "V2_UNSUPPORTED"}
            for item in dark
        ),
        "dark_observations": len(dark),
        "canary_observations": len(canary),
        "canary_status": canary_status,
        "rollback_status": rollback,
    }
    return V2PromotionControlReport(
        schema_version="v2-promotion-control/v1",
        current_window=_pointer(running[-1]) if running else None,
        last_terminal_window=_pointer(terminal[-1]) if terminal else None,
        evaluation_id=_digest(identity),
        **{key: value for key, value in identity.items() if key not in {"current_window", "last_terminal_window"}},
    )


def _parse_evaluated_at(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise argparse.ArgumentTypeError("evaluated-at must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise argparse.ArgumentTypeError("evaluated-at must include a timezone")
    return parsed


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Afficher le contrôle privé de promotion V2"
    )
    parser.add_argument("--evaluated-at", type=_parse_evaluated_at, required=True)
    return parser


async def _run_cli(args: argparse.Namespace) -> V2PromotionControlReport:
    settings = get_settings()
    configure_logging(settings.debug)
    if settings.database_schema_mode != "alembic":
        raise RuntimeError("V2 promotion control requires DATABASE_SCHEMA_MODE=alembic")
    if not db.is_enabled():
        raise RuntimeError("V2 promotion control requires DATABASE_URL")
    await db.prepare_schema()
    async with db.session_scope() as session:
        if session is None:
            raise RuntimeError("V2 promotion control database session unavailable")
        return await build_promotion_control(
            session,
            campaign_id=settings.v2_chain_campaign_id,
            mode=settings.v2_chain_mode,
            evaluated_at=args.evaluated_at,
            promotion_receipt_evaluation_id=(
                settings.v2_promotion_receipt_evaluation_id
            ),
        )


def main(argv: list[str] | None = None) -> int:
    try:
        report = asyncio.run(_run_cli(_parser().parse_args(argv)))
    except Exception as exc:  # pragma: no cover - dépendances réelles
        print(json.dumps({"status": "refused", "error_type": type(exc).__name__}))
        return 1
    print(json.dumps(report.to_dict(), separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
