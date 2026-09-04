from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import models as core_models  # noqa: F401
from app.db.base import Base
from app.v2_chain.control import _parser, build_promotion_control
from app.v2_chain.coverage_funnel import FUNNEL_STAGES
from app.v2_chain.models import V2ChainExecution, V2LiveDarkReadObservation


NOW = datetime(2026, 9, 4, 14, tzinfo=timezone.utc)
CAMPAIGN = "sha256:" + "d" * 64
STAGES = [
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
]


@pytest.mark.asyncio
async def test_promotion_control_exposes_only_aggregate_state() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with sessions() as session:
            started = NOW.replace(tzinfo=None)
            evaluation_id = "sha256:" + "1" * 64
            session.add(
                V2ChainExecution(
                    execution_key="1" * 64,
                    mode="apply",
                    status="succeeded",
                    evaluated_at=started,
                    vertical="smartphones",
                    after_raw_id=0,
                    row_limit=10,
                    last_raw_source_id=10,
                    checkpoints_json={},
                    completed_stages_json=STAGES,
                    campaign_id=CAMPAIGN,
                    execution_kind="progression",
                    window_metrics_json={
                        "schema_version": "v2-window-metrics/v1",
                        "evaluation_identity": evaluation_id,
                        "errors": 0,
                        "unknown": 2,
                        "ABSTAIN": 1,
                        "coverage_funnel": dict(
                            zip(FUNNEL_STAGES, (10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0))
                        ),
                    },
                    report_evaluation_id=evaluation_id,
                    heartbeat_at=started + timedelta(seconds=1),
                    finished_at=started + timedelta(seconds=1),
                )
            )
            session.add(
                V2LiveDarkReadObservation(
                    observation_key="2" * 64,
                    campaign_id=CAMPAIGN,
                    comparison_version="v2-live-dark-comparison/v1",
                    surface="advise",
                    vertical="smartphones",
                    locale="fr",
                    country_code="BE",
                    core_outcome="CANDIDATES",
                    v2_outcome="ABSTAIN",
                    classification="AMBIGUOUS",
                    core_candidate_count=1,
                    v2_candidate_count=0,
                    core_latency_us=1_000,
                    v2_latency_us=1_500,
                    chain_complete=True,
                    safety_state="ABSTAIN",
                    provenance_complete=True,
                    raw_query_retained=False,
                    evaluated_at=started,
                )
            )
            await session.commit()

            report = await build_promotion_control(
                session,
                campaign_id=CAMPAIGN,
                mode="dark",
                evaluated_at=NOW,
            )

            assert report.mode == "dark"
            assert report.last_terminal_window.cursor_end == 10
            assert report.cursor_by_vertical == {"smartphones": 10}
            assert report.unknown == 2
            assert report.abstain == 1
            assert report.dark_observations == 1
            assert report.dark_differences == 1
            assert report.safety_violations == 0
            assert report.coverage_status == "PENDING"
            assert report.canary_status == "NOT_AUTHORIZED"
            assert report.rollback_status == "NOT_PROVEN"
            assert "raw_query" not in str(report.to_dict())
    finally:
        await engine.dispose()


def test_promotion_control_cli_requires_an_explicit_aware_timestamp() -> None:
    args = _parser().parse_args(["--evaluated-at", "2026-09-04T14:00:00Z"])

    assert args.evaluated_at == NOW
