"""Verrou et journal persistants pour une exécution V2 mono-instance."""

from __future__ import annotations

import asyncio
import secrets
from dataclasses import asdict, replace
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from app.v2_chain.models import V2ChainExecution
from app.v2_chain.orchestrator import (
    V2ChainCheckpoints,
    V2ChainReport,
    capture_checkpoints,
    run_v2_shadow_chain,
    validate_v2_chain_request,
)


class V2ChainAlreadyRunning(RuntimeError):
    """Un autre déclencheur détient déjà le verrou persistant."""


def _utc_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def _start_execution(
    session,
    *,
    evaluated_at: datetime,
    vertical: str,
    after_raw_id: int,
    limit: int,
    apply: bool,
    checkpoints: V2ChainCheckpoints,
) -> int:
    now = _utc_naive()
    execution = V2ChainExecution(
        execution_key=secrets.token_hex(32),
        mode="apply" if apply else "dry_run",
        status="running",
        evaluated_at=evaluated_at.astimezone(timezone.utc).replace(tzinfo=None),
        vertical=vertical,
        after_raw_id=after_raw_id,
        row_limit=limit,
        last_raw_source_id=after_raw_id,
        checkpoints_json=asdict(checkpoints),
        completed_stages_json=[],
        heartbeat_at=now,
    )
    session.add(execution)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        active = await session.scalar(
            select(V2ChainExecution.id).where(V2ChainExecution.status == "running")
        )
        if active is not None:
            raise V2ChainAlreadyRunning(
                "another V2 chain execution is already running"
            ) from exc
        raise
    await session.refresh(execution)
    return execution.id


async def _record_stage(session, execution_id: int, stage_name: str) -> None:
    execution = await session.get(V2ChainExecution, execution_id)
    if execution is None or execution.status != "running":
        raise RuntimeError("V2 chain execution lease is no longer active")
    completed = list(execution.completed_stages_json or [])
    if stage_name not in completed:
        completed.append(stage_name)
    execution.completed_stages_json = completed
    execution.heartbeat_at = _utc_naive()
    await session.commit()


async def _finish_execution(
    session,
    execution_id: int,
    *,
    status: str,
    evaluation_id: str | None = None,
    last_raw_source_id: int | None = None,
    failure_reason: str | None = None,
) -> None:
    now = _utc_naive()
    result = await session.execute(
        update(V2ChainExecution)
        .where(
            V2ChainExecution.id == execution_id,
            V2ChainExecution.status == "running",
        )
        .values(
            status=status,
            heartbeat_at=now,
            finished_at=now,
            report_evaluation_id=evaluation_id,
            last_raw_source_id=(
                last_raw_source_id
                if last_raw_source_id is not None
                else V2ChainExecution.last_raw_source_id
            ),
            failure_reason=failure_reason,
        )
    )
    if result.rowcount != 1:
        await session.rollback()
        raise RuntimeError("V2 chain execution lease is no longer active")
    await session.commit()


async def interrupt_stale_execution(session, *, stale_before: datetime) -> int:
    """Termine honnêtement un lease stale, sans démarrer de successeur."""

    if stale_before.tzinfo is None:
        raise ValueError("stale_before must include a timezone")
    now = _utc_naive()
    result = await session.execute(
        update(V2ChainExecution)
        .where(
            V2ChainExecution.status == "running",
            V2ChainExecution.heartbeat_at
            < stale_before.astimezone(timezone.utc).replace(tzinfo=None),
        )
        .values(
            status="interrupted",
            heartbeat_at=now,
            finished_at=now,
            failure_reason="stale_heartbeat",
        )
    )
    await session.commit()
    return int(result.rowcount or 0)


async def next_after_raw_id(session) -> int:
    """Retourne le curseur du dernier apply terminalement réussi."""

    value = await session.scalar(
        select(V2ChainExecution.last_raw_source_id)
        .where(
            V2ChainExecution.status == "succeeded",
            V2ChainExecution.mode == "apply",
        )
        .order_by(V2ChainExecution.id.desc())
        .limit(1)
    )
    return int(value or 0)


async def run_journaled_v2_shadow_chain(
    session,
    *,
    evaluated_at: datetime,
    vertical: str,
    after_raw_id: int = 0,
    limit: int = 10,
    apply: bool = False,
    checkpoints: V2ChainCheckpoints | None = None,
) -> V2ChainReport:
    """Exécute la chaîne sous lease unique et consigne chaque étape."""

    captured = checkpoints or await capture_checkpoints(session)
    validate_v2_chain_request(
        evaluated_at=evaluated_at,
        vertical=vertical,
        after_raw_id=after_raw_id,
        limit=limit,
        checkpoints=captured,
    )
    execution_id = await _start_execution(
        session,
        evaluated_at=evaluated_at,
        vertical=vertical,
        after_raw_id=after_raw_id,
        limit=limit,
        apply=apply,
        checkpoints=captured,
    )

    async def on_stage_complete(stage_name: str) -> None:
        await _record_stage(session, execution_id, stage_name)

    try:
        report = await run_v2_shadow_chain(
            session,
            evaluated_at=evaluated_at,
            vertical=vertical,
            after_raw_id=after_raw_id,
            limit=limit,
            apply=apply,
            checkpoints=captured,
            on_stage_complete=on_stage_complete,
        )
    except BaseException as exc:
        await session.rollback()
        terminal_status = (
            "interrupted"
            if isinstance(exc, (asyncio.CancelledError, KeyboardInterrupt))
            else "failed"
        )
        await _finish_execution(
            session,
            execution_id,
            status=terminal_status,
            failure_reason=type(exc).__name__[:64],
        )
        raise
    await _finish_execution(
        session,
        execution_id,
        status="succeeded",
        evaluation_id=report.evaluation_id,
        last_raw_source_id=(
            report.stages["product_identity"].get("last_raw_source_id")
            or after_raw_id
        ),
    )
    return replace(report, execution_id=execution_id)
