"""Writer append-only et idempotent des résultats Hybrid Retrieval."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from sqlalchemy import select

from .fusion import FusionResult
from .models import HybridRetrievalCandidate, HybridRetrievalRun


PERSISTENCE_VERSION = "hybrid-retrieval-shadow-writer/v1"


class HybridRetrievalPersistenceError(RuntimeError):
    """Écriture impossible à prouver ou replay divergent."""


@dataclass(frozen=True)
class PersistenceReport:
    schema_version: str
    persistence_version: str
    mode: str
    run_key: str
    outcome: str
    candidates: int
    runs_created: int
    runs_existing: int
    candidates_created: int
    candidates_existing: int
    result_digest: str
    evaluation_id: str


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _naive_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise HybridRetrievalPersistenceError("evaluated_at must include a timezone")
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def _entity_type(entity_ref: str) -> str:
    prefix = entity_ref.split(":", 1)[0].upper()
    if prefix not in {"PRODUCT", "MODEL", "VARIANT"}:
        raise HybridRetrievalPersistenceError("entity ref type is unsupported")
    return prefix


def _payload(
    *,
    query_ref: str,
    query_digest: str,
    locale: str,
    country_code: str | None,
    intent: Mapping[str, Any],
    sources: Sequence[Mapping[str, Any]],
    retrieval_version: str,
    index_versions: Mapping[str, str],
    snapshot_ref: str,
    evaluated_at: datetime,
    fusion: FusionResult,
) -> dict[str, Any]:
    if locale not in {"fr", "nl", "en"}:
        raise HybridRetrievalPersistenceError("locale is invalid")
    if not query_ref or not snapshot_ref or not retrieval_version:
        raise HybridRetrievalPersistenceError("run references are required")
    if not query_digest.startswith("sha256:") or len(query_digest) != 71:
        raise HybridRetrievalPersistenceError("query digest is invalid")
    if country_code is not None and (len(country_code) != 2 or country_code.upper() != country_code):
        raise HybridRetrievalPersistenceError("country code is invalid")
    evaluated = _naive_utc(evaluated_at).isoformat() + "Z"
    return {
        "query_ref": query_ref,
        "query_digest": query_digest,
        "raw_query_retained": False,
        "locale": locale,
        "country_code": country_code,
        "intent": dict(intent),
        "sources": [dict(source) for source in sources],
        "outcome": fusion.outcome,
        "reason_codes": list(fusion.reason_codes),
        "retrieval_version": retrieval_version,
        "fusion_version": fusion.fusion_version,
        "index_versions": dict(sorted(index_versions.items())),
        "snapshot_ref": snapshot_ref,
        "result_digest": fusion.result_digest,
        "evaluated_at": evaluated,
        "candidates": [asdict(candidate) for candidate in fusion.candidates],
    }


async def persist_fusion_result(
    session,
    *,
    query_ref: str,
    query_digest: str,
    locale: str,
    country_code: str | None,
    intent: Mapping[str, Any],
    sources: Sequence[Mapping[str, Any]],
    retrieval_version: str,
    index_versions: Mapping[str, str],
    snapshot_ref: str,
    evaluated_at: datetime,
    fusion: FusionResult,
    apply: bool = False,
) -> PersistenceReport:
    payload = _payload(
        query_ref=query_ref,
        query_digest=query_digest,
        locale=locale,
        country_code=country_code,
        intent=intent,
        sources=sources,
        retrieval_version=retrieval_version,
        index_versions=index_versions,
        snapshot_ref=snapshot_ref,
        evaluated_at=evaluated_at,
        fusion=fusion,
    )
    run_key = _digest(payload)
    runs_created = runs_existing = candidates_created = candidates_existing = 0
    if apply:
        existing = await session.scalar(
            select(HybridRetrievalRun).where(HybridRetrievalRun.run_key == run_key)
        )
        if existing is not None:
            rows = (
                (
                    await session.execute(
                        select(HybridRetrievalCandidate)
                        .where(HybridRetrievalCandidate.run_id == existing.id)
                        .order_by(HybridRetrievalCandidate.candidate_rank)
                    )
                )
                .scalars()
                .all()
            )
            if existing.result_digest != fusion.result_digest or len(rows) != len(fusion.candidates):
                raise HybridRetrievalPersistenceError("hybrid retrieval replay divergence")
            runs_existing = 1
            candidates_existing = len(rows)
        else:
            run = HybridRetrievalRun(
                run_key=run_key,
                query_ref=query_ref,
                query_digest=query_digest,
                raw_query_retained=False,
                locale=locale,
                country_code=country_code,
                intent_json=dict(intent),
                sources_json=[dict(source) for source in sources],
                outcome=fusion.outcome,
                reason_codes_json=list(fusion.reason_codes),
                retrieval_version=retrieval_version,
                fusion_version=fusion.fusion_version,
                index_versions_json=dict(index_versions),
                snapshot_ref=snapshot_ref,
                result_digest=fusion.result_digest,
                evaluated_at=_naive_utc(evaluated_at),
            )
            session.add(run)
            await session.flush()
            rows = [
                HybridRetrievalCandidate(
                    run_id=run.id,
                    candidate_rank=candidate.candidate_rank,
                    candidate_status="ELIGIBLE_SHADOW",
                    entity_type=_entity_type(candidate.entity_ref),
                    entity_ref=candidate.entity_ref,
                    group_key=candidate.entity_ref,
                    rrf_score=f"{candidate.rrf_score:.12f}",
                    offer_ids_json=list(candidate.offer_ids),
                    source_evidence_json=[asdict(item) for item in candidate.source_evidence],
                )
                for candidate in fusion.candidates
            ]
            session.add_all(rows)
            await session.flush()
            await session.commit()
            runs_created = 1
            candidates_created = len(rows)
    evaluation_id = "sha256:" + _digest({"run_key": run_key, "result_digest": fusion.result_digest})
    return PersistenceReport(
        schema_version="hybrid-retrieval-persistence-report/v1",
        persistence_version=PERSISTENCE_VERSION,
        mode="apply" if apply else "dry_run",
        run_key=run_key,
        outcome=fusion.outcome,
        candidates=len(fusion.candidates),
        runs_created=runs_created,
        runs_existing=runs_existing,
        candidates_created=candidates_created,
        candidates_existing=candidates_existing,
        result_digest=fusion.result_digest,
        evaluation_id=evaluation_id,
    )
