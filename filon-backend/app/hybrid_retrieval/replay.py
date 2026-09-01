"""Replay réel borné Hybrid Retrieval Phase 5H."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from sqlalchemy import select

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db import models as core_models
from app.db import session as db
from app.product_ontology.models import ProductOntologySnapshot

from .fusion import FusionSourceHit, reciprocal_rank_fusion
from .lexical import LEXICAL_ADAPTER_VERSION, LexicalDocument, retrieve_lexical
from .persistence import persist_fusion_result
from .semantic import SEMANTIC_ADAPTER_VERSION, SemanticDocument, retrieve_semantic
from .structured import (
    STRUCTURED_ADAPTER_VERSION,
    StructuredDocument,
    intent_from_query,
    retrieve_structured,
)


REPLAY_VERSION = "hybrid-retrieval-production-replay/v1"
MAX_REPLAY_ROWS = 1_000


class HybridRetrievalReplayError(RuntimeError):
    """Replay impossible à qualifier sans inventer de preuve."""


@dataclass(frozen=True)
class ReplayDocument:
    snapshot_id: int
    entity_ref: str
    offer_id: int
    query: str
    brand: str | None
    model: str
    product_type: str | None
    product_role: str | None
    attributes: Mapping[str, str]


@dataclass(frozen=True)
class HybridRetrievalReplayReport:
    schema_version: str
    replay_version: str
    mode: str
    evaluated_at: str
    after_snapshot_id: int
    limit: int
    scanned: int
    candidates: int
    candidate_runs: int
    no_match_runs: int
    ambiguous_runs: int
    top1_target_hits: int
    runs_created: int
    runs_existing: int
    candidates_created: int
    candidates_existing: int
    last_snapshot_id: int | None
    evaluation_id: str


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise HybridRetrievalReplayError("evaluated_at must include a timezone")
    return value.astimezone(timezone.utc)


def _validate_window(after_snapshot_id: int, limit: int) -> tuple[int, int]:
    if isinstance(after_snapshot_id, bool) or not isinstance(after_snapshot_id, int) or after_snapshot_id < 0:
        raise ValueError("after_snapshot_id must be a non-negative integer")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_REPLAY_ROWS:
        raise ValueError(f"limit must be between 1 and {MAX_REPLAY_ROWS}")
    return after_snapshot_id, limit


def _classification_type(snapshot: ProductOntologySnapshot) -> str | None:
    claim = snapshot.classification_json.get("product_type", {})
    if not isinstance(claim, Mapping) or claim.get("state") != "known":
        return None
    value = claim.get("value")
    if not isinstance(value, Mapping):
        return None
    key = value.get("concept_key")
    return str(key) if isinstance(key, str) and key else None


def _attributes(snapshot: ProductOntologySnapshot) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in snapshot.attributes_json:
        if not isinstance(item, Mapping) or item.get("state") != "known":
            continue
        key = item.get("attribute_key")
        value = item.get("value")
        if not isinstance(key, str) or not isinstance(value, Mapping):
            continue
        raw = value.get("value")
        unit = value.get("unit")
        if isinstance(raw, (str, int)) and not isinstance(raw, bool):
            result[key] = f"{raw}{unit or ''}"
    return result


def _document(snapshot: ProductOntologySnapshot, offer: core_models.Offer) -> ReplayDocument:
    if snapshot.variant_id is None:
        raise HybridRetrievalReplayError("snapshot identity is unresolved")
    model = (offer.name or "").strip()
    if not model:
        raise HybridRetrievalReplayError("offer name is missing")
    brand = offer.brand.strip() if isinstance(offer.brand, str) and offer.brand.strip() else None
    query = " ".join(value for value in (brand, model) if value)
    role = snapshot.product_role_json.get("value")
    return ReplayDocument(
        snapshot_id=snapshot.id,
        entity_ref=f"variant:{snapshot.variant_id}",
        offer_id=offer.id,
        query=query,
        brand=brand,
        model=model,
        product_type=_classification_type(snapshot),
        product_role=str(role) if isinstance(role, str) else None,
        attributes=_attributes(snapshot),
    )


async def replay_hybrid_retrieval_batch(
    session,
    *,
    evaluated_at: datetime,
    after_snapshot_id: int = 0,
    limit: int = 100,
    apply: bool = False,
) -> HybridRetrievalReplayReport:
    after_snapshot_id, limit = _validate_window(after_snapshot_id, limit)
    evaluated = _aware(evaluated_at)
    rows = (
        await session.execute(
            select(ProductOntologySnapshot, core_models.Offer)
            .join(core_models.Offer, ProductOntologySnapshot.offer_id == core_models.Offer.id)
            .where(
                ProductOntologySnapshot.id > after_snapshot_id,
                ProductOntologySnapshot.variant_id.is_not(None),
            )
            .order_by(ProductOntologySnapshot.id)
            .limit(limit)
        )
    ).all()
    documents = [_document(snapshot, offer) for snapshot, offer in rows]
    lexical_documents = tuple(
        LexicalDocument(
            document_ref=f"product-ontology:{item.snapshot_id}",
            entity_ref=item.entity_ref,
            brand=item.brand,
            model=item.model,
            product_type=item.product_type,
            product_role=item.product_role,
            attributes=item.attributes,
            offer_ids=(item.offer_id,),
        )
        for item in documents
    )
    structured_documents = tuple(
        StructuredDocument(
            document_ref=f"product-ontology:{item.snapshot_id}",
            entity_ref=item.entity_ref,
            product_type=item.product_type,
            product_role=item.product_role,
            attributes=item.attributes,
            offer_ids=(item.offer_id,),
        )
        for item in documents
    )
    semantic_documents = tuple(
        SemanticDocument(
            document_ref=f"product-ontology:{item.snapshot_id}",
            entity_ref=item.entity_ref,
            product_type=item.product_type,
            offer_ids=(item.offer_id,),
        )
        for item in documents
    )
    counters = {
        "candidates": 0,
        "CANDIDATES": 0,
        "NO_MATCH": 0,
        "AMBIGUOUS": 0,
        "top1": 0,
        "runs_created": 0,
        "runs_existing": 0,
        "candidates_created": 0,
        "candidates_existing": 0,
    }
    identities: list[dict[str, Any]] = []
    index_versions = {
        "LEXICAL": LEXICAL_ADAPTER_VERSION,
        "STRUCTURED": STRUCTURED_ADAPTER_VERSION,
        "SEMANTIC": SEMANTIC_ADAPTER_VERSION,
    }
    for target in documents:
        lexical = retrieve_lexical(target.query, lexical_documents, limit=50)
        intent = intent_from_query(target.query)
        structured = retrieve_structured(intent, structured_documents, limit=50)
        semantic = retrieve_semantic(target.query, semantic_documents, limit=50)
        hits = [
            FusionSourceHit("LEXICAL", hit.source_rank, hit.entity_ref, hit.offer_ids, f"product-ontology:{target.snapshot_id}:lexical:{hit.source_rank}")
            for hit in lexical.hits
        ]
        hits.extend(
            FusionSourceHit("STRUCTURED", hit.source_rank, hit.entity_ref, hit.offer_ids, f"product-ontology:{target.snapshot_id}:structured:{hit.source_rank}")
            for hit in structured.hits
        )
        hits.extend(
            FusionSourceHit("SEMANTIC", hit.source_rank, hit.entity_ref, hit.offer_ids, f"product-ontology:{target.snapshot_id}:semantic:{hit.source_rank}")
            for hit in semantic.hits
        )
        query_digest = "sha256:" + hashlib.sha256(target.query.encode("utf-8")).hexdigest()
        fusion = reciprocal_rank_fusion(
            hits,
            query_digest=query_digest,
            snapshot_ref=f"product-ontology:{target.snapshot_id}",
            index_versions=index_versions,
            ambiguity_guard=(
                lexical.outcome == "AMBIGUOUS"
                or (structured.outcome == "AMBIGUOUS" and lexical.outcome != "CANDIDATES")
            ),
            limit=50,
        )
        report = await persist_fusion_result(
            session,
            query_ref=f"p5h:{target.snapshot_id}",
            query_digest=query_digest,
            locale="fr",
            country_code=None,
            intent={
                "status": "PARTIAL",
                "product_type": target.product_type,
                "raw_query_retained": False,
            },
            sources=[
                {"source_type": "LEXICAL", "outcome": lexical.outcome, "candidate_count": len(lexical.hits)},
                {"source_type": "STRUCTURED", "outcome": structured.outcome, "candidate_count": len(structured.hits)},
                {"source_type": "SEMANTIC", "outcome": semantic.outcome, "candidate_count": len(semantic.hits)},
            ],
            retrieval_version=REPLAY_VERSION,
            index_versions=index_versions,
            snapshot_ref=f"product-ontology:{target.snapshot_id}",
            evaluated_at=evaluated,
            fusion=fusion,
            apply=apply,
        )
        counters["candidates"] += len(fusion.candidates)
        counters[fusion.outcome] += 1
        counters["top1"] += bool(fusion.candidates and fusion.candidates[0].entity_ref == target.entity_ref)
        counters["runs_created"] += report.runs_created
        counters["runs_existing"] += report.runs_existing
        counters["candidates_created"] += report.candidates_created
        counters["candidates_existing"] += report.candidates_existing
        identities.append({
            "snapshot_id": target.snapshot_id,
            "query_digest": query_digest,
            "result_digest": fusion.result_digest,
            "outcome": fusion.outcome,
            "candidate_count": len(fusion.candidates),
        })
    return HybridRetrievalReplayReport(
        schema_version="hybrid-retrieval-replay-report/v1",
        replay_version=REPLAY_VERSION,
        mode="apply" if apply else "dry_run",
        evaluated_at=evaluated.isoformat().replace("+00:00", "Z"),
        after_snapshot_id=after_snapshot_id,
        limit=limit,
        scanned=len(documents),
        candidates=counters["candidates"],
        candidate_runs=counters["CANDIDATES"],
        no_match_runs=counters["NO_MATCH"],
        ambiguous_runs=counters["AMBIGUOUS"],
        top1_target_hits=counters["top1"],
        runs_created=counters["runs_created"],
        runs_existing=counters["runs_existing"],
        candidates_created=counters["candidates_created"],
        candidates_existing=counters["candidates_existing"],
        last_snapshot_id=documents[-1].snapshot_id if documents else None,
        evaluation_id="sha256:" + _digest(identities),
    )


def _parse_evaluated_at(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise argparse.ArgumentTypeError("evaluated-at must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise argparse.ArgumentTypeError("evaluated-at must include a timezone")
    return parsed


async def _run(args: argparse.Namespace) -> HybridRetrievalReplayReport:
    settings = get_settings()
    configure_logging(settings.debug)
    if args.apply and not settings.hybrid_retrieval_shadow_enabled:
        raise RuntimeError("HYBRID_RETRIEVAL_SHADOW_ENABLED is required for --apply")
    if not db.is_enabled():
        raise RuntimeError("DATABASE_URL is required")
    await db.prepare_schema()
    async with db.session_scope() as session:
        if session is None:
            raise RuntimeError("database session unavailable")
        return await replay_hybrid_retrieval_batch(
            session,
            evaluated_at=args.evaluated_at,
            after_snapshot_id=args.after_snapshot_id,
            limit=args.limit,
            apply=args.apply,
        )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Replay borné Hybrid Retrieval shadow Phase 5")
    parser.add_argument("--evaluated-at", required=True, type=_parse_evaluated_at)
    parser.add_argument("--after-snapshot-id", type=int, default=0)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--apply", action="store_true")
    return parser


def main() -> None:
    report = asyncio.run(_run(_parser().parse_args()))
    print(json.dumps(asdict(report), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
