"""Scheduler privé et borné des writers de la chaîne V2.

Ce module n'est importé par aucune route publique. Un Cron externe peut
l'exécuter après la synchronisation catalogue ; il s'abstient tant que le
catalogue écrit, lorsqu'une chaîne V2 détient déjà le lease ou lorsqu'aucun
nouveau RawSourceRecord Awin n'est disponible.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.db import models as core_models
from app.db import session as db
from app.observations.models import RawSourceRecord
from app.product_ranking.engine import VERTICAL_WEIGHTS
from app.v2_chain.execution import (
    V2ChainAlreadyRunning,
    interrupt_stale_execution,
    next_after_raw_id,
    run_journaled_v2_shadow_chain,
)
from app.v2_chain.models import V2ChainExecution
from app.v2_chain.orchestrator import MAX_CHAIN_ROWS, V2ChainCheckpoints


log = get_logger("v2_chain_scheduler")


def _valid_campaign(value: object) -> bool:
    if not isinstance(value, str) or not value.startswith("sha256:"):
        return False
    digest = value.removeprefix("sha256:")
    return len(digest) == 64 and all(
        character in "0123456789abcdef" for character in digest
    )


@dataclass(frozen=True)
class V2ScheduleReceipt:
    schema_version: str
    status: str
    vertical: str
    row_limit: int
    after_raw_id: int
    latest_raw_id: int
    due: bool
    execution_id: int | None = None
    evaluation_id: str | None = None
    active_execution_id: int | None = None
    active_heartbeat_at: str | None = None
    heartbeat_age_seconds: int | None = None
    stale_recovery_eligible: bool = False
    recovery_source_execution_id: int | None = None
    raw_payload_retained: bool = False


def _validate_configuration(vertical: str, limit: int) -> None:
    settings = get_settings()
    if settings.database_schema_mode != "alembic":
        raise RuntimeError("V2 scheduler requires DATABASE_SCHEMA_MODE=alembic")
    if settings.v2_chain_mode not in {"shadow", "dark", "canary", "public"}:
        raise RuntimeError("V2 scheduler requires an active V2_CHAIN_MODE")
    if not _valid_campaign(settings.v2_chain_campaign_id):
        raise RuntimeError("V2 scheduler requires an exact campaign digest")
    if vertical not in VERTICAL_WEIGHTS:
        raise RuntimeError("V2 scheduler vertical is unsupported")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_CHAIN_ROWS:
        raise RuntimeError(f"V2 scheduler limit must be between 1 and {MAX_CHAIN_ROWS}")
    if not db.is_enabled():
        raise RuntimeError("V2 scheduler requires DATABASE_URL")


async def _catalog_sync_active(session) -> bool:
    active = await session.scalar(
        select(core_models.CatalogSyncRun.id)
        .where(core_models.CatalogSyncRun.status == "running")
        .limit(1)
    )
    return active is not None


async def _v2_chain_active(session) -> bool:
    active = await session.scalar(
        select(V2ChainExecution.id)
        .where(V2ChainExecution.status == "running")
        .limit(1)
    )
    return active is not None


async def _active_v2_lease(
    session,
    *,
    stale_after_seconds: int,
) -> dict[str, object]:
    row = (
        await session.execute(
            select(V2ChainExecution.id, V2ChainExecution.heartbeat_at)
            .where(V2ChainExecution.status == "running")
            .limit(1)
        )
    ).one_or_none()
    if row is None:
        return {}
    heartbeat = row.heartbeat_at
    if heartbeat.tzinfo is None:
        heartbeat = heartbeat.replace(tzinfo=timezone.utc)
    else:
        heartbeat = heartbeat.astimezone(timezone.utc)
    age_seconds = max(
        0,
        int((datetime.now(timezone.utc) - heartbeat).total_seconds()),
    )
    return {
        "active_execution_id": int(row.id),
        "active_heartbeat_at": heartbeat.isoformat().replace("+00:00", "Z"),
        "heartbeat_age_seconds": age_seconds,
        "stale_recovery_eligible": age_seconds > stale_after_seconds,
    }


async def _latest_terminal_recovery(
    session,
    *,
    vertical: str,
    after_raw_id: int,
    campaign_id: str,
) -> V2ChainExecution | None:
    return await session.scalar(
        select(V2ChainExecution)
        .where(
            V2ChainExecution.mode == "apply",
            V2ChainExecution.vertical == vertical,
            V2ChainExecution.campaign_id == campaign_id,
            V2ChainExecution.after_raw_id == after_raw_id,
            V2ChainExecution.last_raw_source_id == after_raw_id,
            V2ChainExecution.status.in_(("failed", "interrupted")),
        )
        .order_by(V2ChainExecution.id.desc())
        .limit(1)
    )


async def _latest_awin_raw_id(session) -> int:
    value = await session.scalar(
        select(func.max(RawSourceRecord.id)).where(
            RawSourceRecord.source_type == "awin_feed"
        )
    )
    return int(value or 0)


def _receipt(
    *,
    status: str,
    vertical: str,
    limit: int,
    after_raw_id: int,
    latest_raw_id: int,
    execution_id: int | None = None,
    evaluation_id: str | None = None,
    lease: dict[str, object] | None = None,
    recovery_source_execution_id: int | None = None,
) -> V2ScheduleReceipt:
    return V2ScheduleReceipt(
        schema_version="v2-shadow-schedule-receipt/v1",
        status=status,
        vertical=vertical,
        row_limit=limit,
        after_raw_id=after_raw_id,
        latest_raw_id=latest_raw_id,
        due=latest_raw_id > after_raw_id,
        execution_id=execution_id,
        evaluation_id=evaluation_id,
        recovery_source_execution_id=recovery_source_execution_id,
        **(lease or {}),
    )


async def _state(
    session,
    *,
    vertical: str,
    campaign_id: str,
) -> tuple[str, int, int]:
    after_raw_id = await next_after_raw_id(
        session,
        vertical=vertical,
        campaign_id=campaign_id,
    )
    latest_raw_id = await _latest_awin_raw_id(session)
    if await _catalog_sync_active(session):
        return "catalog_syncing", after_raw_id, latest_raw_id
    if await _v2_chain_active(session):
        return "v2_running", after_raw_id, latest_raw_id
    if latest_raw_id <= after_raw_id:
        return "fresh", after_raw_id, latest_raw_id
    recovery = await _latest_terminal_recovery(
        session,
        vertical=vertical,
        after_raw_id=after_raw_id,
        campaign_id=campaign_id,
    )
    if recovery is not None:
        return (
            "v2_resume_due"
            if recovery.status == "interrupted"
            else "v2_failed"
        ), after_raw_id, latest_raw_id
    return "due", after_raw_id, latest_raw_id


async def preflight(*, vertical: str, limit: int) -> V2ScheduleReceipt:
    """Retourne l'état du Cron sans lancer de writer V2."""

    _validate_configuration(vertical, limit)
    settings = get_settings()
    await db.prepare_schema()
    async with db.session_scope() as session:
        if session is None:
            raise RuntimeError("V2 scheduler database session unavailable")
        status, after_raw_id, latest_raw_id = await _state(
            session,
            vertical=vertical,
            campaign_id=settings.v2_chain_campaign_id,
        )
        lease = (
            await _active_v2_lease(
                session,
                stale_after_seconds=settings.v2_chain_stale_after_seconds,
            )
            if status == "v2_running"
            else None
        )
        recovery = (
            await _latest_terminal_recovery(
                session,
                vertical=vertical,
                after_raw_id=after_raw_id,
                campaign_id=settings.v2_chain_campaign_id,
            )
            if status in {"v2_resume_due", "v2_failed"}
            else None
        )
    return _receipt(
        status=status,
        vertical=vertical,
        limit=limit,
        after_raw_id=after_raw_id,
        latest_raw_id=latest_raw_id,
        lease=lease,
        recovery_source_execution_id=(
            recovery.id if recovery is not None else None
        ),
    )


async def run_once(*, vertical: str, limit: int) -> V2ScheduleReceipt:
    """Exécute au plus une fenêtre V2 lorsque son amont est stable."""

    _validate_configuration(vertical, limit)
    settings = get_settings()
    await db.prepare_schema()
    async with db.session_scope() as session:
        if session is None:
            raise RuntimeError("V2 scheduler database session unavailable")
        status, after_raw_id, latest_raw_id = await _state(
            session,
            vertical=vertical,
            campaign_id=settings.v2_chain_campaign_id,
        )
        if status not in {"due", "v2_resume_due"}:
            lease = (
                await _active_v2_lease(
                    session,
                    stale_after_seconds=settings.v2_chain_stale_after_seconds,
                )
                if status == "v2_running"
                else None
            )
            recovery = (
                await _latest_terminal_recovery(
                    session,
                    vertical=vertical,
                    after_raw_id=after_raw_id,
                    campaign_id=settings.v2_chain_campaign_id,
                )
                if status == "v2_failed"
                else None
            )
            return _receipt(
                status=status,
                vertical=vertical,
                limit=limit,
                after_raw_id=after_raw_id,
                latest_raw_id=latest_raw_id,
                lease=lease,
                recovery_source_execution_id=(
                    recovery.id if recovery is not None else None
                ),
            )
        recovery = None
        execution_limit = limit
        execution_evaluated_at = datetime.now(timezone.utc)
        execution_checkpoints = None
        if status == "v2_resume_due":
            recovery = await _latest_terminal_recovery(
                session,
                vertical=vertical,
                after_raw_id=after_raw_id,
                campaign_id=settings.v2_chain_campaign_id,
            )
            if recovery is None or recovery.status != "interrupted":
                raise RuntimeError("V2 interrupted execution is unavailable")
            execution_limit = recovery.row_limit
            execution_evaluated_at = (
                recovery.evaluated_at.replace(tzinfo=timezone.utc)
                if recovery.evaluated_at.tzinfo is None
                else recovery.evaluated_at.astimezone(timezone.utc)
            )
            try:
                execution_checkpoints = V2ChainCheckpoints(
                    **recovery.checkpoints_json
                )
            except (TypeError, ValueError) as exc:
                raise RuntimeError(
                    "V2 interrupted execution checkpoints are invalid"
                ) from exc
        try:
            report = await run_journaled_v2_shadow_chain(
                session,
                evaluated_at=execution_evaluated_at,
                vertical=vertical,
                after_raw_id=after_raw_id,
                limit=execution_limit,
                apply=True,
                checkpoints=execution_checkpoints,
                campaign_id=settings.v2_chain_campaign_id,
                execution_kind=("recovery" if recovery is not None else "progression"),
                source_execution_id=(recovery.id if recovery is not None else None),
            )
        except V2ChainAlreadyRunning:
            lease = await _active_v2_lease(
                session,
                stale_after_seconds=settings.v2_chain_stale_after_seconds,
            )
            return _receipt(
                status="v2_running",
                vertical=vertical,
                limit=execution_limit,
                after_raw_id=after_raw_id,
                latest_raw_id=latest_raw_id,
                lease=lease,
                recovery_source_execution_id=(
                    recovery.id if recovery is not None else None
                ),
            )
    return _receipt(
        status="succeeded",
        vertical=vertical,
        limit=execution_limit,
        after_raw_id=after_raw_id,
        latest_raw_id=latest_raw_id,
        execution_id=report.execution_id,
        evaluation_id=report.evaluation_id,
        recovery_source_execution_id=(
            recovery.id if recovery is not None else None
        ),
    )


async def interrupt_stale_once(*, vertical: str, limit: int) -> V2ScheduleReceipt:
    """Clôt au plus un lease stale, sans lancer son successeur.

    Cette commande est volontairement distincte de ``run_once``. L'opérateur
    doit d'abord désactiver le schedule et inspecter le heartbeat ; une
    occurrence normale ne transforme jamais seule un lease frais ou stale.
    """

    _validate_configuration(vertical, limit)
    settings = get_settings()
    await db.prepare_schema()
    async with db.session_scope() as session:
        if session is None:
            raise RuntimeError("V2 scheduler database session unavailable")
        status, after_raw_id, latest_raw_id = await _state(
            session,
            vertical=vertical,
            campaign_id=settings.v2_chain_campaign_id,
        )
        if status != "v2_running":
            return _receipt(
                status=status,
                vertical=vertical,
                limit=limit,
                after_raw_id=after_raw_id,
                latest_raw_id=latest_raw_id,
            )
        stale_before = datetime.now(timezone.utc) - timedelta(
            seconds=settings.v2_chain_stale_after_seconds
        )
        interrupted = await interrupt_stale_execution(
            session,
            stale_before=stale_before,
        )
        lease = (
            await _active_v2_lease(
                session,
                stale_after_seconds=settings.v2_chain_stale_after_seconds,
            )
            if not interrupted
            else None
        )
    return _receipt(
        status="v2_interrupted" if interrupted else "v2_running",
        vertical=vertical,
        limit=limit,
        after_raw_id=after_raw_id,
        latest_raw_id=latest_raw_id,
        lease=lease,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Cron privé de progression de la chaîne V2 shadow"
    )
    parser.add_argument("--vertical", required=True, choices=tuple(VERTICAL_WEIGHTS))
    parser.add_argument("--limit", type=int, default=MAX_CHAIN_ROWS)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--interrupt-stale", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        settings = get_settings()
        configure_logging(settings.debug)
        if args.check and args.interrupt_stale:
            raise RuntimeError("--check and --interrupt-stale are mutually exclusive")
        operation = (
            preflight
            if args.check
            else interrupt_stale_once
            if args.interrupt_stale
            else run_once
        )
        receipt = asyncio.run(operation(vertical=args.vertical, limit=args.limit))
    except Exception as exc:  # pragma: no cover - dépendances réelles
        print(
            json.dumps(
                {"status": "refused", "error_type": type(exc).__name__},
                sort_keys=True,
            )
        )
        return 1
    print(json.dumps(asdict(receipt), separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
