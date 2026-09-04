"""Lecteur sombre V2 : mesure la chaîne sans modifier le lecteur Core v1.

Le module reconstruit uniquement les requêtes synthétiques du replay P5H,
compare les identifiants de candidats en mémoire et persiste des agrégats.
Ni la requête reconstruite, ni une liste de candidats, ni un payload marchand
ne sont conservés. Aucun endpoint public n'importe ce module.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import math
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timezone
from typing import Any, Sequence

from sqlalchemy import and_, func, select

from app.buy_wait.models import BuyWaitDecisionRun
from app.confidence.models import ConfidenceCalibrationRun
from app.constraint_engine.models import ConstraintEvaluationRun
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db import models as core_models
from app.db import session as db
from app.hybrid_retrieval.models import (
    HybridRetrievalCandidate,
    HybridRetrievalRun,
)
from app.hybrid_retrieval.replay import _document
from app.offer_optimization.models import OfferOptimizationRun
from app.product_ontology.models import ProductOntologySnapshot
from app.product_ranking.models import ProductRankingRun
from app.services.currency import normalize_currency_code
from app.services.freshness import offer_observation_is_fresh
from app.services.offer_evidence import load_offer_evidence
from app.services.search import relevance_order, search_clause
from app.v2_chain.models import V2ChainExecution, V2DarkReadObservation


COMPARISON_VERSION = "v2-dark-reader/v1"
MAX_DARK_READ_ROWS = 100
MAX_CORE_SCAN_ROWS = 250
MAX_CORE_CANDIDATES = 50


class V2DarkReaderError(RuntimeError):
    """La comparaison ne peut pas être qualifiée honnêtement."""


@dataclass(frozen=True)
class DarkReadEvaluation:
    hybrid_run_id: int
    query_digest: str
    core_outcome: str
    v2_outcome: str
    core_candidate_count: int
    v2_candidate_count: int
    intersection_count: int
    overlap_ppm: int
    top1_state: str
    chain_complete: bool
    terminal_outcome: str
    terminal_offer_state: str
    safety_state: str
    observation_key: str


@dataclass(frozen=True)
class V2DarkReadReport:
    schema_version: str
    comparison_version: str
    mode: str
    evaluated_at: str
    after_hybrid_run_id: int
    limit: int
    scanned: int
    complete: int
    incomplete: int
    safe: int
    abstained: int
    invalid: int
    core_candidates: int
    v2_candidates: int
    intersections: int
    top1_matches: int
    observations_created: int
    observations_existing: int
    last_hybrid_run_id: int | None
    evaluation_id: str


@dataclass(frozen=True)
class _ChainState:
    complete: bool
    terminal_outcome: str
    selected_offer_id: int | None
    safety_state: str


def _canonical(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("evaluated_at must include a timezone")
    return value.astimezone(timezone.utc)


def _validate_window(after_hybrid_run_id: int, limit: int) -> tuple[int, int]:
    if (
        isinstance(after_hybrid_run_id, bool)
        or not isinstance(after_hybrid_run_id, int)
        or after_hybrid_run_id < 0
    ):
        raise ValueError("after_hybrid_run_id must be a non-negative integer")
    if (
        isinstance(limit, bool)
        or not isinstance(limit, int)
        or not 1 <= limit <= MAX_DARK_READ_ROWS
    ):
        raise ValueError(f"limit must be between 1 and {MAX_DARK_READ_ROWS}")
    return after_hybrid_run_id, limit


def _snapshot_id(snapshot_ref: str) -> int | None:
    prefix = "product-ontology:"
    if not isinstance(snapshot_ref, str) or not snapshot_ref.startswith(prefix):
        return None
    try:
        value = int(snapshot_ref.removeprefix(prefix))
    except ValueError:
        return None
    return value if value > 0 else None


def _offer_ref_id(value: str | None) -> int | None:
    if not isinstance(value, str):
        return None
    candidate = value.removeprefix("offer:")
    try:
        offer_id = int(candidate)
    except ValueError:
        return None
    return offer_id if offer_id > 0 else None


async def _latest_child(session, model, foreign_key, parent_id: int):
    return await session.scalar(
        select(model).where(foreign_key == parent_id).order_by(model.id.desc()).limit(1)
    )


async def _chain_state(
    session,
    retrieval: HybridRetrievalRun,
) -> _ChainState:
    constraint = await _latest_child(
        session,
        ConstraintEvaluationRun,
        ConstraintEvaluationRun.retrieval_run_id,
        retrieval.id,
    )
    if constraint is None:
        return _ChainState(False, "INCOMPLETE", None, "INCOMPLETE")
    ranking = await _latest_child(
        session,
        ProductRankingRun,
        ProductRankingRun.constraint_run_id,
        constraint.id,
    )
    if ranking is None:
        return _ChainState(False, "INCOMPLETE", None, "INCOMPLETE")
    optimization = await _latest_child(
        session,
        OfferOptimizationRun,
        OfferOptimizationRun.product_ranking_run_id,
        ranking.id,
    )
    if optimization is None:
        return _ChainState(False, "INCOMPLETE", None, "INCOMPLETE")
    confidence = await _latest_child(
        session,
        ConfidenceCalibrationRun,
        ConfidenceCalibrationRun.offer_optimization_run_id,
        optimization.id,
    )
    if confidence is None:
        return _ChainState(False, "INCOMPLETE", None, "INCOMPLETE")
    decision = await _latest_child(
        session,
        BuyWaitDecisionRun,
        BuyWaitDecisionRun.confidence_run_id,
        confidence.id,
    )
    if decision is None:
        return _ChainState(False, "INCOMPLETE", None, "INCOMPLETE")

    invalid = retrieval.outcome == "ERROR"
    abstained = (
        retrieval.outcome in {"NO_MATCH", "AMBIGUOUS"}
        or constraint.outcome in {"NO_ELIGIBLE_CANDIDATE", "ABSTAINED"}
        or ranking.outcome in {"NO_ELIGIBLE_PRODUCT", "ABSTAINED"}
        or optimization.outcome in {"NO_ELIGIBLE_OFFER", "ABSTAINED"}
        or confidence.outcome == "ABSTAINED"
        or decision.outcome == "ABSTAIN"
    )
    return _ChainState(
        complete=True,
        terminal_outcome=decision.outcome,
        selected_offer_id=_offer_ref_id(decision.selected_offer_ref),
        safety_state="INVALID" if invalid else ("ABSTAIN" if abstained else "SAFE"),
    )


async def _v2_candidate_ids(
    session,
    retrieval_run_id: int,
) -> tuple[int, ...]:
    rows = (
        (
            await session.execute(
                select(HybridRetrievalCandidate)
                .where(
                    HybridRetrievalCandidate.run_id == retrieval_run_id,
                    HybridRetrievalCandidate.candidate_status == "ELIGIBLE_SHADOW",
                )
                .order_by(HybridRetrievalCandidate.candidate_rank)
            )
        )
        .scalars()
        .all()
    )
    result: list[int] = []
    seen: set[int] = set()
    for row in rows:
        for value in row.offer_ids_json or []:
            if (
                isinstance(value, int)
                and not isinstance(value, bool)
                and value > 0
                and value not in seen
            ):
                result.append(value)
                seen.add(value)
    return tuple(result)


async def _core_candidate_ids(
    session,
    *,
    query: str,
    evaluated_at: datetime,
) -> tuple[int, ...]:
    clause = search_clause(query)
    order = relevance_order(query)
    if clause is None or order is None:
        return ()
    offers = (
        (
            await session.execute(
                select(core_models.Offer)
                .join(
                    core_models.Merchant,
                    core_models.Offer.merchant_id == core_models.Merchant.id,
                )
                .where(
                    and_(
                        clause,
                        core_models.Merchant.joined.is_(True),
                        func.trim(core_models.Merchant.name) != "",
                        core_models.Offer.is_canonical.is_(True),
                        core_models.Offer.is_adult.is_(False),
                        core_models.Offer.price.is_not(None),
                        core_models.Offer.price > 0,
                        core_models.Offer.currency.is_not(None),
                        func.trim(core_models.Offer.currency) != "",
                        core_models.Offer.in_stock.is_(True),
                    )
                )
                .order_by(order, core_models.Offer.price, core_models.Offer.id)
                .limit(MAX_CORE_SCAN_ROWS)
            )
        )
        .scalars()
        .all()
    )
    evidence = await load_offer_evidence(session, list(offers), current_only=True)
    result: list[int] = []
    for offer in offers:
        proof = evidence.get(offer.id)
        price = offer.price
        if (
            proof is None
            or price is None
            or isinstance(price, bool)
            or not math.isfinite(price)
            or price <= 0
            or normalize_currency_code(offer.currency) is None
            or offer.in_stock is not True
            or not offer_observation_is_fresh(
                proof.current_observed_at,
                now=evaluated_at,
            )
        ):
            continue
        result.append(offer.id)
        if len(result) == MAX_CORE_CANDIDATES:
            break
    return tuple(result)


async def _query_for_run(
    session,
    retrieval: HybridRetrievalRun,
) -> tuple[str | None, bool]:
    snapshot_id = _snapshot_id(retrieval.snapshot_ref)
    if snapshot_id is None or retrieval.raw_query_retained is not False:
        return None, False
    row = (
        await session.execute(
            select(ProductOntologySnapshot, core_models.Offer)
            .join(
                core_models.Offer,
                ProductOntologySnapshot.offer_id == core_models.Offer.id,
            )
            .where(ProductOntologySnapshot.id == snapshot_id)
        )
    ).one_or_none()
    if row is None:
        return None, False
    try:
        query = _document(*row).query
    except Exception:
        return None, False
    digest = "sha256:" + hashlib.sha256(query.encode("utf-8")).hexdigest()
    return (query, digest == retrieval.query_digest)


def _match_state(left: int | None, right: int | None) -> str:
    if left is None or right is None:
        return "UNKNOWN"
    return "MATCH" if left == right else "MISMATCH"


async def evaluate_run(
    session,
    retrieval: HybridRetrievalRun,
    *,
    evaluated_at: datetime,
) -> DarkReadEvaluation:
    """Compare un run V2 au lecteur lexical Core, sans conserver la requête."""

    evaluated = _aware(evaluated_at)
    query, query_valid = await _query_for_run(session, retrieval)
    v2_ids = await _v2_candidate_ids(session, retrieval.id)
    core_ids = (
        await _core_candidate_ids(session, query=query, evaluated_at=evaluated)
        if query is not None and query_valid
        else ()
    )
    chain = await _chain_state(session, retrieval)
    core_set = set(core_ids)
    v2_set = set(v2_ids)
    intersection = len(core_set & v2_set)
    union = len(core_set | v2_set)
    overlap_ppm = round(intersection * 1_000_000 / union) if union else 0
    top1_state = _match_state(
        core_ids[0] if core_ids else None,
        v2_ids[0] if v2_ids else None,
    )
    terminal_offer_state = (
        "UNKNOWN"
        if chain.selected_offer_id is None or not core_ids
        else ("MATCH" if chain.selected_offer_id in core_set else "MISMATCH")
    )
    safety_state = chain.safety_state if query_valid else "INVALID"
    payload = {
        "comparison_version": COMPARISON_VERSION,
        "hybrid_run_id": retrieval.id,
        "evaluated_at": evaluated.isoformat().replace("+00:00", "Z"),
    }
    return DarkReadEvaluation(
        hybrid_run_id=retrieval.id,
        query_digest=retrieval.query_digest,
        core_outcome=(
            "INVALID"
            if not query_valid
            else ("CANDIDATES" if core_ids else "NO_MATCH")
        ),
        v2_outcome=retrieval.outcome,
        core_candidate_count=len(core_ids),
        v2_candidate_count=len(v2_ids),
        intersection_count=intersection,
        overlap_ppm=overlap_ppm,
        top1_state=top1_state,
        chain_complete=chain.complete,
        terminal_outcome=chain.terminal_outcome,
        terminal_offer_state=terminal_offer_state,
        safety_state=safety_state,
        observation_key=_digest(payload),
    )


async def assert_stable_shadow_state(session) -> None:
    """Refuse une mesure pendant qu'un writer catalogue ou V2 est actif."""

    catalog_active = await session.scalar(
        select(core_models.CatalogSyncRun.id)
        .where(core_models.CatalogSyncRun.status == "running")
        .limit(1)
    )
    if catalog_active is not None:
        raise V2DarkReaderError("catalog sync is active")
    v2_active = await session.scalar(
        select(V2ChainExecution.id)
        .where(V2ChainExecution.status == "running")
        .limit(1)
    )
    if v2_active is not None:
        raise V2DarkReaderError("V2 chain execution is active")


def _observation_values(
    evaluation: DarkReadEvaluation,
    *,
    evaluated_at: datetime,
) -> dict[str, Any]:
    return {
        "observation_key": evaluation.observation_key,
        "hybrid_run_id": evaluation.hybrid_run_id,
        "query_digest": evaluation.query_digest,
        "raw_query_retained": False,
        "comparison_version": COMPARISON_VERSION,
        "core_outcome": evaluation.core_outcome,
        "v2_outcome": evaluation.v2_outcome,
        "core_candidate_count": evaluation.core_candidate_count,
        "v2_candidate_count": evaluation.v2_candidate_count,
        "intersection_count": evaluation.intersection_count,
        "overlap_ppm": evaluation.overlap_ppm,
        "top1_state": evaluation.top1_state,
        "chain_complete": evaluation.chain_complete,
        "terminal_outcome": evaluation.terminal_outcome,
        "terminal_offer_state": evaluation.terminal_offer_state,
        "safety_state": evaluation.safety_state,
        "evaluated_at": evaluated_at.astimezone(UTC).replace(tzinfo=None),
    }


async def compare_dark_window(
    session,
    *,
    evaluated_at: datetime,
    after_hybrid_run_id: int = 0,
    limit: int = 25,
    apply: bool = False,
) -> V2DarkReadReport:
    """Mesure une fenêtre stable et persiste uniquement ses agrégats."""

    after_hybrid_run_id, limit = _validate_window(after_hybrid_run_id, limit)
    evaluated = _aware(evaluated_at)
    await assert_stable_shadow_state(session)
    runs = (
        (
            await session.execute(
                select(HybridRetrievalRun)
                .where(HybridRetrievalRun.id > after_hybrid_run_id)
                .order_by(HybridRetrievalRun.id)
                .limit(limit)
            )
        )
        .scalars()
        .all()
    )
    evaluations = [
        await evaluate_run(session, run, evaluated_at=evaluated) for run in runs
    ]
    created = existing = 0
    if apply:
        for evaluation in evaluations:
            values = _observation_values(evaluation, evaluated_at=evaluated)
            stored = await session.scalar(
                select(V2DarkReadObservation).where(
                    V2DarkReadObservation.observation_key
                    == evaluation.observation_key
                )
            )
            if stored is not None:
                if any(getattr(stored, key) != value for key, value in values.items()):
                    raise V2DarkReaderError("dark reader replay divergence")
                existing += 1
                continue
            session.add(V2DarkReadObservation(**values))
            created += 1
        # Une ingestion apparue pendant la lecture invalide la fenêtre entière.
        await assert_stable_shadow_state(session)
        await session.commit()

    payloads = [asdict(evaluation) for evaluation in evaluations]
    return V2DarkReadReport(
        schema_version="v2-dark-read-report/v1",
        comparison_version=COMPARISON_VERSION,
        mode="apply" if apply else "dry_run",
        evaluated_at=evaluated.isoformat().replace("+00:00", "Z"),
        after_hybrid_run_id=after_hybrid_run_id,
        limit=limit,
        scanned=len(evaluations),
        complete=sum(item.chain_complete for item in evaluations),
        incomplete=sum(not item.chain_complete for item in evaluations),
        safe=sum(item.safety_state == "SAFE" for item in evaluations),
        abstained=sum(item.safety_state == "ABSTAIN" for item in evaluations),
        invalid=sum(item.safety_state == "INVALID" for item in evaluations),
        core_candidates=sum(item.core_candidate_count for item in evaluations),
        v2_candidates=sum(item.v2_candidate_count for item in evaluations),
        intersections=sum(item.intersection_count for item in evaluations),
        top1_matches=sum(item.top1_state == "MATCH" for item in evaluations),
        observations_created=created,
        observations_existing=existing,
        last_hybrid_run_id=runs[-1].id if runs else None,
        evaluation_id="sha256:" + _digest(payloads),
    )


def _validate_configuration(*, apply: bool) -> None:
    settings = get_settings()
    if settings.database_schema_mode != "alembic":
        raise RuntimeError("V2 dark reader requires DATABASE_SCHEMA_MODE=alembic")
    if settings.v2_chain_mode != "dark":
        raise RuntimeError("V2 dark reader requires V2_CHAIN_MODE=dark")
    if settings.v2_canary_reader_enabled or settings.v2_public_reader_enabled:
        raise RuntimeError("V2 dark reader forbids canary/public readers")
    if apply and not db.is_enabled():
        raise RuntimeError("V2 dark reader requires DATABASE_URL")


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
        description="Comparaison dark V2/Core v1 sans exposition publique"
    )
    evaluated_group = parser.add_mutually_exclusive_group(required=True)
    evaluated_group.add_argument("--evaluated-at", type=_parse_evaluated_at)
    evaluated_group.add_argument("--evaluated-at-now", action="store_true")
    parser.add_argument("--after-hybrid-run-id", type=int, default=0)
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--apply", action="store_true")
    return parser


async def _run(args: argparse.Namespace) -> V2DarkReadReport:
    _validate_configuration(apply=args.apply)
    settings = get_settings()
    configure_logging(settings.debug)
    if not db.is_enabled():
        raise RuntimeError("V2 dark reader requires DATABASE_URL")
    await db.prepare_schema()
    async with db.session_scope() as session:
        if session is None:
            raise RuntimeError("V2 dark reader database session unavailable")
        return await compare_dark_window(
            session,
            evaluated_at=(
                datetime.now(timezone.utc)
                if args.evaluated_at_now
                else args.evaluated_at
            ),
            after_hybrid_run_id=args.after_hybrid_run_id,
            limit=args.limit,
            apply=args.apply,
        )


def main(argv: Sequence[str] | None = None) -> int:
    try:
        report = asyncio.run(_run(_parser().parse_args(argv)))
    except Exception as exc:  # pragma: no cover - dépendances réelles
        print(
            json.dumps(
                {"status": "refused", "error_type": type(exc).__name__},
                sort_keys=True,
            )
        )
        return 1
    print(json.dumps(asdict(report), separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
