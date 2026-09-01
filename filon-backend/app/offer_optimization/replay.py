"""Replay borné Offer Optimization Phase 8.

Le replay consomme Product Ranking et Offer Truth sans inventer la fiabilité
marchand absente de la production. Il peut donc s'abstenir honnêtement tout en
qualifiant le câblage et l'idempotence.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from sqlalchemy import select

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db import session as db
from app.offer_truth.models import OfferTruthSnapshot
from app.product_ranking.models import ProductRankingCandidate, ProductRankingRun

from .engine import (
    AvailabilityFact,
    MoneyFact,
    OfferCandidateFacts,
    OptimizationRequest,
    ScoreFact,
    optimize_offers,
)
from .persistence import persist_offer_optimization


REPLAY_VERSION = "offer-optimization-production-replay/v1"
MAX_REPLAY_RUNS = 100
MAX_OFFERS_PER_RUN = 100


@dataclass(frozen=True)
class OfferOptimizationReplayReport:
    schema_version: str
    replay_version: str
    mode: str
    evaluated_at: str
    after_product_ranking_run_id: int
    limit: int
    scanned_runs: int
    scanned_offers: int
    selected_offers: int
    eligible_offers: int
    unoptimizable_offers: int
    ineligible_offers: int
    abstained_runs: int
    runs_created: int
    runs_existing: int
    candidates_created: int
    candidates_existing: int
    last_product_ranking_run_id: int | None
    evaluation_id: str


def _validate_window(after_product_ranking_run_id: int, limit: int) -> tuple[int, int]:
    if (
        isinstance(after_product_ranking_run_id, bool)
        or not isinstance(after_product_ranking_run_id, int)
        or after_product_ranking_run_id < 0
    ):
        raise ValueError("after_product_ranking_run_id must be a non-negative integer")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_REPLAY_RUNS:
        raise ValueError(f"limit must be between 1 and {MAX_REPLAY_RUNS}")
    return after_product_ranking_run_id, limit


def _refs(claim: Mapping[str, Any] | None) -> tuple[str, ...]:
    if not isinstance(claim, Mapping):
        return ()
    evidence = claim.get("evidence")
    if not isinstance(evidence, list):
        return ()
    refs: list[str] = []
    for item in evidence:
        if not isinstance(item, Mapping):
            continue
        raw_id = item.get("raw_source_record_id")
        field = item.get("field")
        version = item.get("transformation_version")
        if isinstance(raw_id, int) and raw_id > 0 and isinstance(field, str) and field:
            refs.append(f"raw:{raw_id}:{field}:{version or 'unknown'}")
    return tuple(dict.fromkeys(refs))


def _money(claim: Mapping[str, Any] | None) -> MoneyFact:
    if not isinstance(claim, Mapping):
        return MoneyFact("unknown")
    state = claim.get("state")
    value = claim.get("value")
    refs = _refs(claim)
    if state != "known" or not isinstance(value, Mapping):
        return MoneyFact(state if state in {"unknown", "invalid", "conflict"} else "unknown")
    amount = value.get("amount_decimal")
    currency = value.get("currency")
    if not isinstance(amount, str) or not isinstance(currency, str):
        return MoneyFact("invalid")
    return MoneyFact("known", amount, currency, refs)


def _availability(claim: Mapping[str, Any] | None) -> AvailabilityFact:
    if not isinstance(claim, Mapping):
        return AvailabilityFact("unknown")
    state = claim.get("state")
    value = claim.get("value")
    if state != "known":
        return AvailabilityFact(state if state in {"unknown", "invalid", "conflict"} else "unknown")
    if value not in {"in_stock", "out_of_stock", "preorder"}:
        return AvailabilityFact("invalid")
    return AvailabilityFact("known", value, _refs(claim))


def _freshness(claim: Mapping[str, Any] | None) -> ScoreFact:
    if not isinstance(claim, Mapping) or claim.get("state") != "fresh":
        return ScoreFact("unknown")
    value = claim.get("value")
    if not isinstance(value, Mapping):
        return ScoreFact("invalid")
    try:
        age = Decimal(str(value.get("age_seconds")))
        ttl = Decimal(str(value.get("ttl_seconds")))
    except (InvalidOperation, ValueError):
        return ScoreFact("invalid")
    if not age.is_finite() or not ttl.is_finite() or age < 0 or ttl <= 0 or age > ttl:
        return ScoreFact("invalid")
    score = (Decimal("1") - age / ttl).quantize(Decimal("0.000001"))
    return ScoreFact("known", format(score, "f"), _refs(claim))


async def _latest_offer_snapshots(
    session,
    *,
    product_ref: str | None,
    evaluated_at: datetime,
) -> list[OfferTruthSnapshot]:
    if product_ref is None or not product_ref.startswith("variant:"):
        return []
    suffix = product_ref.removeprefix("variant:")
    if not suffix.isdigit() or int(suffix) < 1:
        return []
    rows = (
        (
            await session.execute(
                select(OfferTruthSnapshot)
                .where(
                    OfferTruthSnapshot.variant_id == int(suffix),
                    OfferTruthSnapshot.evaluated_at <= evaluated_at.replace(tzinfo=None),
                )
                .order_by(
                    OfferTruthSnapshot.offer_id,
                    OfferTruthSnapshot.evaluated_at.desc(),
                    OfferTruthSnapshot.id.desc(),
                )
                .limit(MAX_OFFERS_PER_RUN * 5)
            )
        )
        .scalars()
        .all()
    )
    latest: dict[int, OfferTruthSnapshot] = {}
    for row in rows:
        latest.setdefault(row.offer_id, row)
    return list(latest.values())[:MAX_OFFERS_PER_RUN]


def _candidate(snapshot: OfferTruthSnapshot, product_ref: str) -> OfferCandidateFacts:
    claims = snapshot.claims_json if isinstance(snapshot.claims_json, Mapping) else {}
    # Merchant Intelligence conserve volontairement des compteurs, pas un score
    # synthétique de fiabilité. Le replay n'en fabrique donc aucun.
    return OfferCandidateFacts(
        offer_ref=f"offer:{snapshot.offer_id}",
        product_ref=product_ref,
        truth_status=snapshot.offer_status,
        price=_money(claims.get("price")),
        shipping=_money(claims.get("shipping")),
        availability=_availability(claims.get("stock")),
        merchant_reliability=ScoreFact("unknown"),
        freshness=_freshness(claims.get("freshness")),
    )


async def replay_offer_optimization_batch(
    session,
    *,
    evaluated_at: datetime,
    after_product_ranking_run_id: int = 0,
    limit: int = 10,
    apply: bool = False,
) -> OfferOptimizationReplayReport:
    after_product_ranking_run_id, limit = _validate_window(
        after_product_ranking_run_id, limit
    )
    if evaluated_at.tzinfo is None:
        raise ValueError("evaluated_at must include a timezone")
    evaluated = evaluated_at.astimezone(timezone.utc)
    runs = (
        (
            await session.execute(
                select(ProductRankingRun)
                .where(ProductRankingRun.id > after_product_ranking_run_id)
                .order_by(ProductRankingRun.id)
                .limit(limit)
            )
        )
        .scalars()
        .all()
    )
    counters = {
        key: 0
        for key in (
            "offers",
            "SELECTED",
            "ELIGIBLE",
            "UNOPTIMIZABLE",
            "INELIGIBLE",
            "abstained_runs",
            "runs_created",
            "runs_existing",
            "candidates_created",
            "candidates_existing",
        )
    }
    identities: list[dict[str, object]] = []
    for run in runs:
        top = await session.scalar(
            select(ProductRankingCandidate).where(
                ProductRankingCandidate.run_id == run.id,
                ProductRankingCandidate.status == "RANKED",
                ProductRankingCandidate.product_rank == 1,
            )
        )
        product_ref = top.entity_ref if top is not None else None
        request = OptimizationRequest(
            f"p8:{run.id}",
            run.outcome,
            product_ref,
            1 if product_ref is not None else None,
        )
        snapshots = await _latest_offer_snapshots(
            session, product_ref=product_ref, evaluated_at=evaluated
        )
        candidates = [_candidate(snapshot, product_ref) for snapshot in snapshots if product_ref]
        optimization = optimize_offers(request, candidates)
        report = await persist_offer_optimization(
            session,
            product_ranking_run=run,
            snapshot_ids={f"offer:{snapshot.offer_id}": snapshot.id for snapshot in snapshots},
            evaluated_at=evaluated,
            optimization=optimization,
            apply=apply,
        )
        counters["offers"] += len(optimization.evaluations)
        for candidate in optimization.evaluations:
            counters[candidate.status] += 1
        counters["abstained_runs"] += optimization.outcome == "ABSTAINED"
        for key in ("runs_created", "runs_existing", "candidates_created", "candidates_existing"):
            counters[key] += getattr(report, key)
        identities.append(
            {
                "product_ranking_run_id": run.id,
                "result_digest": optimization.result_digest,
                "run_key": report.run_key,
            }
        )
    payload = json.dumps(identities, sort_keys=True, separators=(",", ":")).encode()
    return OfferOptimizationReplayReport(
        "offer-optimization-replay-report/v1",
        REPLAY_VERSION,
        "apply" if apply else "dry_run",
        evaluated.isoformat().replace("+00:00", "Z"),
        after_product_ranking_run_id,
        limit,
        len(runs),
        counters["offers"],
        counters["SELECTED"],
        counters["ELIGIBLE"],
        counters["UNOPTIMIZABLE"],
        counters["INELIGIBLE"],
        counters["abstained_runs"],
        counters["runs_created"],
        counters["runs_existing"],
        counters["candidates_created"],
        counters["candidates_existing"],
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


async def _run(args: argparse.Namespace) -> OfferOptimizationReplayReport:
    settings = get_settings()
    configure_logging(settings.debug)
    if args.apply and not settings.offer_optimization_shadow_enabled:
        raise RuntimeError("OFFER_OPTIMIZATION_SHADOW_ENABLED is required for --apply")
    if not db.is_enabled():
        raise RuntimeError("DATABASE_URL is required")
    await db.prepare_schema()
    async with db.session_scope() as session:
        if session is None:
            raise RuntimeError("database session unavailable")
        return await replay_offer_optimization_batch(
            session,
            evaluated_at=args.evaluated_at,
            after_product_ranking_run_id=args.after_product_ranking_run_id,
            limit=args.limit,
            apply=args.apply,
        )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Replay borné Offer Optimization shadow Phase 8")
    parser.add_argument("--evaluated-at", required=True, type=_parse_evaluated_at)
    parser.add_argument("--after-product-ranking-run-id", type=int, default=0)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--apply", action="store_true")
    return parser


def main() -> None:
    report = asyncio.run(_run(_parser().parse_args()))
    print(json.dumps(asdict(report), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
