"""Lecteur V2 P5→P10 en mémoire, limité aux abstentions qualifiables.

Ce module n'est relié à aucune route. Il permet de prouver qu'une requête
fermée traverse la chaîne de lecture réelle sans écriture et sans inventer les
dimensions de ranking, profils de confiance ou faits marchands encore absents.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Mapping

from sqlalchemy import func, select

from app.buy_wait.engine import (
    BuyWaitRequest,
    DecisionConfidence,
    decide_buy_wait,
)
from app.confidence.engine import (
    ConfidenceRequest,
    CoverageInput,
    calibrate_confidence,
)
from app.constraint_engine.engine import (
    CandidateFacts,
    ConstraintRequest,
    Fact,
    HardConstraint,
    evaluate_constraints,
)
from app.db import models as core_models
from app.hybrid_retrieval.fusion import FusionSourceHit, reciprocal_rank_fusion
from app.hybrid_retrieval.lexical import (
    LEXICAL_ADAPTER_VERSION,
    LexicalDocument,
    retrieve_lexical,
)
from app.hybrid_retrieval.replay import ReplayDocument, _document
from app.hybrid_retrieval.semantic import (
    SEMANTIC_ADAPTER_VERSION,
    SemanticDocument,
    retrieve_semantic,
)
from app.hybrid_retrieval.structured import (
    STRUCTURED_ADAPTER_VERSION,
    StructuredDocument,
    intent_from_query,
    retrieve_structured,
)
from app.offer_optimization.engine import OptimizationRequest, optimize_offers
from app.product_ontology.models import ProductOntologySnapshot
from app.product_ranking.engine import (
    VERTICAL_WEIGHTS,
    RankingCandidateFacts,
    RankingRequest,
    ScoreFact,
    rank_products,
)
from app.services.currency import normalize_currency_code
from app.v2_chain.canary import V2CanaryPayload


ONLINE_READER_VERSION = "v2-online-reader/v1"
MAX_QUERY_LENGTH = 512
MAX_DOCUMENTS = 1_000
MAX_CANDIDATES = 50


class V2OnlineReaderError(ValueError):
    """La requête de lecture V2 ne respecte pas le contrat fermé."""


@dataclass(frozen=True)
class V2OnlineReadRequest:
    query: str
    vertical: str
    locale: str = "fr"
    country_code: str | None = None
    budget_amount_decimal: str | None = None
    budget_currency: str | None = None

    def __post_init__(self) -> None:
        if (
            not isinstance(self.query, str)
            or not self.query.strip()
            or len(self.query) > MAX_QUERY_LENGTH
        ):
            raise V2OnlineReaderError("query must be non-empty and bounded")
        if self.vertical not in VERTICAL_WEIGHTS:
            raise V2OnlineReaderError("vertical is unsupported")
        if self.locale not in {"fr", "nl", "en"}:
            raise V2OnlineReaderError("locale is unsupported")
        if self.country_code is not None and (
            len(self.country_code) != 2
            or self.country_code.upper() != self.country_code
        ):
            raise V2OnlineReaderError("country code is invalid")
        if (self.budget_amount_decimal is None) != (self.budget_currency is None):
            raise V2OnlineReaderError("budget amount and currency must be paired")
        if self.budget_amount_decimal is not None:
            try:
                budget = Decimal(self.budget_amount_decimal)
            except InvalidOperation as exc:
                raise V2OnlineReaderError("budget amount is invalid") from exc
            if not budget.is_finite() or budget <= 0:
                raise V2OnlineReaderError("budget amount is invalid")
            if normalize_currency_code(self.budget_currency) != self.budget_currency:
                raise V2OnlineReaderError("budget currency is invalid")


def _query_digest(query: str) -> str:
    return "sha256:" + hashlib.sha256(query.strip().encode("utf-8")).hexdigest()


def _latest_snapshot_statement():
    latest = (
        select(
            ProductOntologySnapshot.offer_id.label("offer_id"),
            func.max(ProductOntologySnapshot.id).label("snapshot_id"),
        )
        .group_by(ProductOntologySnapshot.offer_id)
        .subquery()
    )
    return (
        select(ProductOntologySnapshot, core_models.Offer)
        .join(latest, ProductOntologySnapshot.id == latest.c.snapshot_id)
        .join(
            core_models.Offer,
            ProductOntologySnapshot.offer_id == core_models.Offer.id,
        )
        .where(
            ProductOntologySnapshot.variant_id.is_not(None),
            ProductOntologySnapshot.ontology_status.in_(("VERIFIED", "PARTIAL")),
            core_models.Offer.is_canonical.is_(True),
            core_models.Offer.is_adult.is_(False),
        )
        .order_by(ProductOntologySnapshot.id.desc())
        .limit(MAX_DOCUMENTS)
    )


async def _documents(session) -> tuple[ReplayDocument, ...]:
    rows = (await session.execute(_latest_snapshot_statement())).all()
    result: list[ReplayDocument] = []
    for snapshot, offer in rows:
        try:
            result.append(_document(snapshot, offer))
        except Exception:
            # Une ligne incomplète ne devient jamais un document implicite.
            continue
    return tuple(result)


def _retrieval(
    request: V2OnlineReadRequest,
    documents: tuple[ReplayDocument, ...],
):
    query = request.query.strip()
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
    evidence_by_entity: dict[str, int] = {}
    for item in documents:
        evidence_by_entity[item.entity_ref] = min(
            item.snapshot_id,
            evidence_by_entity.get(item.entity_ref, item.snapshot_id),
        )

    lexical = retrieve_lexical(query, lexical_documents, limit=MAX_CANDIDATES)
    structured = retrieve_structured(
        intent_from_query(query),
        structured_documents,
        limit=MAX_CANDIDATES,
    )
    semantic = retrieve_semantic(query, semantic_documents, limit=MAX_CANDIDATES)
    hits = [
        FusionSourceHit(
            "LEXICAL",
            hit.source_rank,
            hit.entity_ref,
            hit.offer_ids,
            f"product-ontology:{evidence_by_entity[hit.entity_ref]}:lexical",
        )
        for hit in lexical.hits
    ]
    hits.extend(
        FusionSourceHit(
            "STRUCTURED",
            hit.source_rank,
            hit.entity_ref,
            hit.offer_ids,
            f"product-ontology:{evidence_by_entity[hit.entity_ref]}:structured",
        )
        for hit in structured.hits
    )
    hits.extend(
        FusionSourceHit(
            "SEMANTIC",
            hit.source_rank,
            hit.entity_ref,
            hit.offer_ids,
            f"product-ontology:{evidence_by_entity[hit.entity_ref]}:semantic",
        )
        for hit in semantic.hits
        if hit.entity_ref is not None
    )
    digest = _query_digest(query)
    snapshot_ref = (
        f"online-index:{max(item.snapshot_id for item in documents)}"
        if documents
        else "online-index:empty"
    )
    fusion = reciprocal_rank_fusion(
        hits,
        query_digest=digest,
        snapshot_ref=snapshot_ref,
        index_versions={
            "LEXICAL": LEXICAL_ADAPTER_VERSION,
            "STRUCTURED": STRUCTURED_ADAPTER_VERSION,
            "SEMANTIC": SEMANTIC_ADAPTER_VERSION,
        },
        ambiguity_guard=(
            lexical.outcome == "AMBIGUOUS"
            or (
                structured.outcome == "AMBIGUOUS"
                and lexical.outcome != "CANDIDATES"
            )
        ),
        limit=MAX_CANDIDATES,
    )
    return digest, fusion


def _price_fact(offers: list[core_models.Offer]) -> Fact:
    valid: list[tuple[float, str, int]] = []
    for offer in offers:
        currency = normalize_currency_code(offer.currency)
        price = offer.price
        if (
            currency is not None
            and price is not None
            and not isinstance(price, bool)
            and math.isfinite(price)
            and price > 0
        ):
            valid.append((float(price), currency, offer.id))
    if not valid:
        return Fact("unknown")
    currencies = {item[1] for item in valid}
    refs = tuple(f"offer:{item[2]}:price" for item in sorted(valid))
    if len(currencies) != 1:
        return Fact("conflict", evidence_refs=refs)
    amount, currency, offer_id = min(valid)
    return Fact(
        "known",
        {"amount": f"{amount:.2f}", "currency": currency},
        (f"offer:{offer_id}:price",),
    )


def _candidate_facts(entity_ref: str, offers: list[core_models.Offer]) -> CandidateFacts:
    if not offers:
        return CandidateFacts(
            entity_ref,
            Fact("unknown"),
            Fact("unknown"),
            Fact("unknown"),
            Fact("unknown"),
            {},
            {},
        )
    stock_refs = tuple(f"offer:{offer.id}:stock" for offer in offers)
    if any(offer.in_stock is True for offer in offers):
        availability = Fact(
            "known",
            "in_stock",
            tuple(
                f"offer:{offer.id}:stock"
                for offer in offers
                if offer.in_stock is True
            ),
        )
    elif all(offer.in_stock is False for offer in offers):
        availability = Fact("known", "out_of_stock", stock_refs)
    else:
        availability = Fact("unknown", evidence_refs=stock_refs)
    return CandidateFacts(
        entity_ref=entity_ref,
        price=_price_fact(offers),
        countries=Fact("unknown"),
        availability=availability,
        adult_restricted=Fact(
            "known",
            any(offer.is_adult is True for offer in offers),
            tuple(f"offer:{offer.id}:adult" for offer in offers),
        ),
        attributes={},
        preference_facts={},
    )


def _constraints(request: V2OnlineReadRequest) -> tuple[HardConstraint, ...]:
    values: list[HardConstraint] = [
        HardConstraint(
            "availability",
            "AVAILABILITY_REQUIRED",
            {"value": "in_stock"},
        ),
        HardConstraint(
            "adult-safety",
            "ADULT_SAFETY",
            {"adult_allowed": False},
        ),
    ]
    if request.country_code is not None:
        values.append(
            HardConstraint(
                "country",
                "COUNTRY_ALLOWED",
                {"country_code": request.country_code},
            )
        )
    if request.budget_amount_decimal is not None:
        values.append(
            HardConstraint(
                "budget",
                "BUDGET_MAX",
                {
                    "maximum": {
                        "amount": request.budget_amount_decimal,
                        "currency": request.budget_currency,
                    }
                },
            )
        )
    return tuple(values)


def _provenance(stage_results: Mapping[str, object]) -> tuple[dict[str, str], ...]:
    result: list[dict[str, str]] = []
    for stage, value in stage_results.items():
        digest = getattr(value, "result_digest", None)
        if not isinstance(digest, str) or not digest.startswith("sha256:"):
            raise V2OnlineReaderError("stage provenance is incomplete")
        result.append({"stage": stage, "result_digest": digest})
    return tuple(result)


async def read_v2_online(
    session,
    request: V2OnlineReadRequest,
    *,
    evaluated_at: datetime,
) -> V2CanaryPayload:
    """Exécute P5→P10 sans persistance et retourne une abstention prouvée."""

    if evaluated_at.tzinfo is None:
        raise V2OnlineReaderError("evaluated_at must include a timezone")
    evaluated = evaluated_at.astimezone(timezone.utc)
    documents = await _documents(session)
    query_digest, retrieval = _retrieval(request, documents)
    offer_ids = sorted(
        {
            offer_id
            for candidate in retrieval.candidates
            for offer_id in candidate.offer_ids
        }
    )
    offers = (
        (
            await session.execute(
                select(core_models.Offer).where(core_models.Offer.id.in_(offer_ids))
            )
        )
        .scalars()
        .all()
        if offer_ids
        else []
    )
    by_id = {offer.id: offer for offer in offers}
    candidate_facts = [
        _candidate_facts(
            candidate.entity_ref,
            [by_id[value] for value in candidate.offer_ids if value in by_id],
        )
        for candidate in retrieval.candidates
    ]
    constraints = evaluate_constraints(
        ConstraintRequest(
            context_ref=f"v2-online:{query_digest}",
            hard_constraints=_constraints(request),
        ),
        candidate_facts,
    )
    ranking = rank_products(
        RankingRequest(f"v2-online:{query_digest}", request.vertical),
        tuple(
            RankingCandidateFacts(
                candidate.entity_ref,
                candidate.status,
                {
                    "need_fit": ScoreFact("unknown"),
                    "product_quality": ScoreFact("unknown"),
                    "value": ScoreFact("unknown"),
                    "evidence": ScoreFact("unknown"),
                },
            )
            for candidate in constraints.candidates
        ),
    )
    optimization = optimize_offers(
        OptimizationRequest(
            context_ref=f"v2-online:{query_digest}",
            ranking_outcome=ranking.outcome,
            selected_product_ref=None,
            selected_product_rank=None,
        ),
        (),
    )
    confidence = calibrate_confidence(
        ConfidenceRequest(
            context_ref=f"v2-online:{query_digest}",
            signals=(),
            evidence_coverage=CoverageInput(0, 0),
        ),
        (),
    )
    decision = decide_buy_wait(
        BuyWaitRequest(
            context_ref=f"v2-online:{query_digest}",
            evaluated_at=evaluated,
            selected_offer_ref=None,
            selected_product_ref=None,
            current=None,
            history=(),
            decision_confidence=DecisionConfidence(
                "UNKNOWN",
                None,
                0,
                None,
                (),
            ),
            backtest_profile_ref=None,
        )
    )
    if (
        ranking.outcome not in {"ABSTAINED", "NO_ELIGIBLE_PRODUCT"}
        or optimization.outcome != "ABSTAINED"
        or confidence.outcome != "ABSTAINED"
        or decision.outcome != "ABSTAIN"
    ):
        raise V2OnlineReaderError(
            "online reader may only expose its qualified abstention path"
        )
    stages = {
        "hybrid_retrieval": retrieval,
        "constraint_engine": constraints,
        "product_ranking": ranking,
        "offer_optimization": optimization,
        "confidence": confidence,
        "buy_wait": decision,
    }
    provenance = _provenance(stages)
    response = {
        "schema_version": "v2-online-response/v1",
        "reader_version": ONLINE_READER_VERSION,
        "outcome": "ABSTAIN",
        "query_digest": query_digest,
        "reason_codes": [
            "v2_actionable_evidence_incomplete",
            f"retrieval_{retrieval.outcome.lower()}",
            f"ranking_{ranking.outcome.lower()}",
            "confidence_not_calibrated",
        ],
        "items": [],
        "provenance": [dict(item) for item in provenance],
        "raw_query_retained": False,
    }
    return V2CanaryPayload(
        response=response,
        chain_complete=True,
        safety_state="ABSTAIN",
        provenance_complete=True,
        response_type="ABSTAIN",
    )
