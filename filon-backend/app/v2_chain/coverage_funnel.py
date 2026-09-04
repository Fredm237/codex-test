"""Diagnostic de couverture P0→P10 dérivé des fenêtres persistées."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from sqlalchemy import select

from app.v2_chain.models import V2ChainExecution


MAX_FUNNEL_ROWS = 10_000
FUNNEL_STAGES = (
    "raw",
    "identified",
    "resolved",
    "verified_offer",
    "ontology_verified",
    "retrieved",
    "eligible",
    "rankable",
    "optimizable",
    "calibrated",
    "actionable",
)
REQUIRED_WINDOW_STAGES = frozenset(
    {
        "product_identity",
        "entity_resolution",
        "offer_graph",
        "merchant_intelligence",
        "evidence_engine",
        "offer_truth",
        "product_ontology",
        "hybrid_retrieval",
        "constraint_engine",
        "product_ranking",
        "offer_optimization",
        "confidence",
        "buy_wait",
    }
)


class V2CoverageFunnelError(ValueError):
    """Le journal ne permet pas un funnel borné et honnête."""


@dataclass(frozen=True)
class V2CoverageStage:
    stage: str
    records: int
    coverage_of_raw_ppm: int | None
    retention_from_previous_ppm: int | None


@dataclass(frozen=True)
class V2CoverageFunnelReport:
    schema_version: str
    evaluated_at: str
    campaign_id: str
    status: str
    execution_rows: int
    valid_terminal_windows: int
    active_windows: int
    failed_windows: int
    interrupted_windows: int
    contiguous: bool
    monotone_counts: bool
    stages: tuple[V2CoverageStage, ...]
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


def _aware(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise V2CoverageFunnelError("evaluated_at must include a timezone")
    return value.astimezone(timezone.utc)


def _metric(value: object, stage: str) -> int | None:
    if not isinstance(value, dict):
        return None
    funnel = value.get("coverage_funnel")
    if not isinstance(funnel, dict):
        return None
    count = funnel.get(stage)
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        return None
    return count


def _valid_window(execution: V2ChainExecution) -> bool:
    metrics = execution.window_metrics_json
    return (
        execution.mode == "apply"
        and execution.execution_kind in {"progression", "recovery"}
        and execution.status == "succeeded"
        and execution.finished_at is not None
        and execution.last_raw_source_id > execution.after_raw_id
        and set(execution.completed_stages_json or []) == REQUIRED_WINDOW_STAGES
        and isinstance(metrics, dict)
        and metrics.get("schema_version") == "v2-window-metrics/v1"
        and metrics.get("errors") == 0
        and metrics.get("evaluation_identity") == execution.report_evaluation_id
        and all(_metric(metrics, stage) is not None for stage in FUNNEL_STAGES)
    )


def _ppm(numerator: int, denominator: int) -> int | None:
    if denominator == 0:
        return None
    return round(numerator * 1_000_000 / denominator)


async def evaluate_coverage_funnel(
    session,
    *,
    campaign_id: str,
    evaluated_at: datetime,
) -> V2CoverageFunnelReport:
    """Agrège toutes les fenêtres de campagne, sans sélection favorable."""

    if not _valid_digest(campaign_id):
        raise V2CoverageFunnelError("campaign id must be a sha256 digest")
    evaluated = _aware(evaluated_at)
    executions = list(
        (
            await session.execute(
                select(V2ChainExecution)
                .where(V2ChainExecution.campaign_id == campaign_id)
                .order_by(V2ChainExecution.id)
                .limit(MAX_FUNNEL_ROWS + 1)
            )
        )
        .scalars()
        .all()
    )
    if len(executions) > MAX_FUNNEL_ROWS:
        raise V2CoverageFunnelError("coverage funnel exceeds the bounded audit limit")

    windows = [item for item in executions if _valid_window(item)]
    last_by_vertical: dict[str, int] = {}
    contiguous = bool(windows)
    for item in windows:
        previous = last_by_vertical.get(item.vertical)
        if previous is not None and item.after_raw_id != previous:
            contiguous = False
        last_by_vertical[item.vertical] = item.last_raw_source_id

    totals = {
        stage: sum(_metric(item.window_metrics_json, stage) or 0 for item in windows)
        for stage in FUNNEL_STAGES
    }
    monotone = all(
        totals[current] <= totals[previous]
        for previous, current in zip(FUNNEL_STAGES, FUNNEL_STAGES[1:])
    )
    stages = tuple(
        V2CoverageStage(
            stage=stage,
            records=totals[stage],
            coverage_of_raw_ppm=_ppm(totals[stage], totals["raw"]),
            retention_from_previous_ppm=(
                None
                if index == 0
                else _ppm(totals[stage], totals[FUNNEL_STAGES[index - 1]])
            ),
        )
        for index, stage in enumerate(FUNNEL_STAGES)
    )
    active = sum(item.status == "running" for item in executions)
    ready = (
        len(windows) >= 30
        and active == 0
        and contiguous
        and monotone
        and totals["raw"] > 0
    )
    status = "READY" if ready else "PENDING"
    identity = {
        "evaluated_at": evaluated.isoformat().replace("+00:00", "Z"),
        "campaign_id": campaign_id,
        "status": status,
        "execution_rows": len(executions),
        "valid_terminal_windows": len(windows),
        "active_windows": active,
        "failed_windows": sum(item.status == "failed" for item in executions),
        "interrupted_windows": sum(item.status == "interrupted" for item in executions),
        "contiguous": contiguous,
        "monotone_counts": monotone,
        "stages": tuple(asdict(stage) for stage in stages),
    }
    return V2CoverageFunnelReport(
        schema_version="v2-coverage-funnel/v1",
        evaluated_at=identity["evaluated_at"],
        campaign_id=campaign_id,
        status=status,
        execution_rows=len(executions),
        valid_terminal_windows=len(windows),
        active_windows=active,
        failed_windows=identity["failed_windows"],
        interrupted_windows=identity["interrupted_windows"],
        contiguous=contiguous,
        monotone_counts=monotone,
        stages=stages,
        evaluation_id=_digest(identity),
    )


def render_coverage_funnel_markdown(report: V2CoverageFunnelReport) -> str:
    """Rend un reçu lisible sans payload ni contexte brut."""

    lines = [
        "# V2 Coverage Funnel",
        "",
        f"- Verdict : **{report.status}**",
        f"- Campagne : `{report.campaign_id}`",
        f"- Fenêtres terminales valides : **{report.valid_terminal_windows}**",
        f"- Fenêtres actives : **{report.active_windows}**",
        f"- Échecs observés : **{report.failed_windows}**",
        f"- Interruptions observées : **{report.interrupted_windows}**",
        f"- Curseurs contigus : **{'oui' if report.contiguous else 'non'}**",
        f"- Comptages monotones : **{'oui' if report.monotone_counts else 'non'}**",
        "",
        "| Étape | Records | Couverture du RAW | Rétention de l'étape précédente |",
        "|---|---:|---:|---:|",
    ]
    for stage in report.stages:
        raw = "n/a" if stage.coverage_of_raw_ppm is None else f"{stage.coverage_of_raw_ppm / 10_000:.2f}%"
        previous = (
            "n/a"
            if stage.retention_from_previous_ppm is None
            else f"{stage.retention_from_previous_ppm / 10_000:.2f}%"
        )
        lines.append(f"| {stage.stage} | {stage.records} | {raw} | {previous} |")
    lines.extend(("", f"Evaluation : `{report.evaluation_id}`", ""))
    return "\n".join(lines)
