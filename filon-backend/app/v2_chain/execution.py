"""Verrou et journal persistants pour une exécution V2 mono-instance."""

from __future__ import annotations

import asyncio
import hashlib
import json
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


def _valid_campaign(value: str | None) -> bool:
    if not isinstance(value, str) or not value.startswith("sha256:"):
        return False
    digest = value.removeprefix("sha256:")
    return len(digest) == 64 and all(
        character in "0123456789abcdef" for character in digest
    )


def _campaign_fields(
    *,
    campaign_id: str | None,
    execution_kind: str | None,
    source_execution_id: int | None,
) -> tuple[str | None, str | None, int | None]:
    if campaign_id is None and execution_kind is None and source_execution_id is None:
        return None, None, None
    if not _valid_campaign(campaign_id):
        raise ValueError("V2 campaign id must be a sha256 digest")
    if execution_kind not in {"progression", "replay", "recovery"}:
        raise ValueError("V2 execution kind is invalid")
    if execution_kind == "progression" and source_execution_id is not None:
        raise ValueError("V2 progression cannot reference a source execution")
    if execution_kind in {"replay", "recovery"} and (
        isinstance(source_execution_id, bool)
        or not isinstance(source_execution_id, int)
        or source_execution_id < 1
    ):
        raise ValueError("V2 replay/recovery requires a source execution")
    return campaign_id, execution_kind, source_execution_id


def _integer(stage: dict[str, object], field: str) -> int:
    value = stage.get(field, 0)
    return int(value) if isinstance(value, int) and not isinstance(value, bool) else 0


def window_metrics(report: V2ChainReport) -> dict[str, object]:
    """Projette le funnel demandé sans confondre les compteurs des étapes."""

    stages = report.stages
    identity = stages.get("product_identity", {})
    entity = stages.get("entity_resolution", {})
    offer_graph = stages.get("offer_graph", {})
    offer_truth = stages.get("offer_truth", {})
    ontology = stages.get("product_ontology", {})
    retrieval = stages.get("hybrid_retrieval", {})
    constraints = stages.get("constraint_engine", {})
    ranking = stages.get("product_ranking", {})
    optimization = stages.get("offer_optimization", {})
    confidence = stages.get("confidence", {})
    decision = stages.get("buy_wait", {})
    snapshot_payload = {
        "after_raw_id": report.after_raw_id,
        "last_raw_source_id": identity.get("last_raw_source_id"),
        "checkpoints": asdict(report.checkpoints),
    }
    snapshot = "sha256:" + hashlib.sha256(
        json.dumps(snapshot_payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    coverage_funnel = {
        "raw": _integer(identity, "scanned"),
        "identified": _integer(identity, "resolved"),
        "resolved": sum(
            _integer(entity, field)
            for field in ("exact_verified", "high_confidence", "probable")
        ),
        "verified_offer": _integer(offer_truth, "verified"),
        "ontology_verified": _integer(ontology, "verified"),
        "retrieved": _integer(retrieval, "candidate_runs"),
        "eligible": _integer(constraints, "eligible_candidates"),
        "rankable": _integer(ranking, "ranked_candidates"),
        "optimizable": _integer(optimization, "eligible_offers"),
        "calibrated": _integer(confidence, "calibrated_runs"),
        "actionable": (
            _integer(decision, "buy_now_runs")
            + _integer(decision, "wait_runs")
        ),
    }
    return {
        "schema_version": "v2-window-metrics/v1",
        "source_snapshot": snapshot,
        "records_scanned": _integer(identity, "scanned"),
        "records_accepted": _integer(offer_graph, "eligible"),
        "records_rejected": _integer(offer_graph, "ineligible"),
        "unknown": _integer(offer_graph, "unknown"),
        "unresolved": _integer(entity, "unresolved"),
        "quarantined": max(
            _integer(identity, "quarantined"),
            _integer(offer_graph, "quarantine"),
        ),
        "rankable": _integer(ranking, "ranked_candidates"),
        "unrankable": _integer(ranking, "unrankable_candidates"),
        "optimizable": _integer(optimization, "eligible_offers"),
        "unoptimizable": _integer(optimization, "unoptimizable_offers"),
        "confidence": {
            "calibrated": _integer(confidence, "calibrated_runs"),
            "partial": _integer(confidence, "partial_runs"),
            "abstained": _integer(confidence, "abstained_runs"),
        },
        "BUY_NOW": _integer(decision, "buy_now_runs"),
        "WAIT": _integer(decision, "wait_runs"),
        "ABSTAIN": _integer(decision, "abstained_runs"),
        "coverage_funnel": coverage_funnel,
        "errors": 0,
        "evaluation_identity": report.evaluation_id,
    }


async def _start_execution(
    session,
    *,
    evaluated_at: datetime,
    vertical: str,
    after_raw_id: int,
    limit: int,
    apply: bool,
    checkpoints: V2ChainCheckpoints,
    campaign_id: str | None,
    execution_kind: str | None,
    source_execution_id: int | None,
) -> int:
    campaign_id, execution_kind, source_execution_id = _campaign_fields(
        campaign_id=campaign_id,
        execution_kind=execution_kind,
        source_execution_id=source_execution_id,
    )
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
        campaign_id=campaign_id,
        execution_kind=execution_kind,
        source_execution_id=source_execution_id,
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
    metrics: dict[str, object] | None = None,
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
            window_metrics_json=metrics,
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


async def next_after_raw_id(
    session,
    *,
    vertical: str | None = None,
    campaign_id: str | None = None,
) -> int:
    """Retourne le curseur du dernier apply réussi pour une verticale.

    Le filtre est optionnel pour conserver le contrat des replays historiques.
    Le scheduler continu le fournit toujours : deux verticales ne doivent
    jamais consommer mutuellement leur curseur.
    """

    statement = select(V2ChainExecution.last_raw_source_id).where(
        V2ChainExecution.status == "succeeded",
        V2ChainExecution.mode == "apply",
    )
    if vertical is not None:
        statement = statement.where(V2ChainExecution.vertical == vertical)
    if campaign_id is not None:
        if not _valid_campaign(campaign_id):
            raise ValueError("V2 campaign id must be a sha256 digest")
        statement = statement.where(
            V2ChainExecution.campaign_id == campaign_id,
            V2ChainExecution.execution_kind.in_(("progression", "recovery")),
        )
    value = await session.scalar(
        statement.order_by(V2ChainExecution.id.desc()).limit(1)
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
    campaign_id: str | None = None,
    execution_kind: str | None = None,
    source_execution_id: int | None = None,
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
        campaign_id=campaign_id,
        execution_kind=execution_kind,
        source_execution_id=source_execution_id,
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
            metrics=(
                {"schema_version": "v2-window-metrics/v1", "errors": 1}
                if campaign_id is not None
                else None
            ),
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
        metrics=window_metrics(report) if campaign_id is not None else None,
    )
    return replace(report, execution_id=execution_id)
