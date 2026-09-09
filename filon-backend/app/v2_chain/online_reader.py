"""Lecteur V2 P5→P10 en mémoire, factuel et fermé par défaut.

Ce module n'est jamais appelé directement par une route. Seul ``live_router``
peut l'invoquer après autorisation persistée, éligibilité et contrôle de
fraîcheur. Il traverse la chaîne réelle sans écriture et sans inventer les
dimensions de ranking, profils de confiance ou faits marchands encore absents.
Lorsque P5/P6 disposent toutefois de prix, devise, stock et fraîcheur prouvés,
il peut rendre une liste d'options factuelles. Cette liste n'est ni un classement
de qualité, ni une recommandation BUY/WAIT.
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
from app.hybrid_retrieval.fusion import (
    FusionResult,
    FusionSourceHit,
    reciprocal_rank_fusion,
)
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
from app.services.freshness import format_utc_timestamp, offer_observation_is_fresh
from app.services.offer_evidence import OfferEvidence, load_offer_evidence
from app.services.offer_market_evidence import (
    OfferMarketEvidence,
    load_offer_listing_markets,
)
from app.v2_chain.canary import V2CanaryPayload


ONLINE_READER_VERSION = "v2-online-reader/v2"
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


@dataclass(frozen=True)
class V2OnlineInspection:
    """Index et candidats exacts utilisés par une lecture en ligne.

    L'inspection reste en mémoire. Elle lie la fraîcheur aux snapshots qui ont
    effectivement produit les candidats, au lieu de laisser un snapshot global
    sans rapport avec la requête autoriser une réponse fondée sur des données
    plus anciennes.
    """

    request_key: str
    evaluated_at: datetime
    documents: tuple[ReplayDocument, ...]
    query_digest: str
    retrieval: FusionResult
    data_age_seconds: int | None
    dependencies_admissible: bool


def _query_digest(query: str) -> str:
    return "sha256:" + hashlib.sha256(query.strip().encode("utf-8")).hexdigest()


def _request_key(request: V2OnlineReadRequest) -> str:
    canonical = "\x1f".join(
        (
            _query_digest(request.query),
            request.vertical,
            request.locale,
            request.country_code or "",
            request.budget_amount_decimal or "",
            request.budget_currency or "",
        )
    )
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


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


async def _documents(
    session,
) -> tuple[tuple[ReplayDocument, ...], dict[int, datetime]]:
    rows = (await session.execute(_latest_snapshot_statement())).all()
    result: list[ReplayDocument] = []
    evaluated_at_by_snapshot: dict[int, datetime] = {}
    for snapshot, offer in rows:
        try:
            document = _document(snapshot, offer)
        except Exception:
            # Une ligne incomplète ne devient jamais un document implicite.
            continue
        result.append(document)
        snapshot_evaluated_at = snapshot.evaluated_at
        if snapshot_evaluated_at.tzinfo is None:
            snapshot_evaluated_at = snapshot_evaluated_at.replace(
                tzinfo=timezone.utc
            )
        evaluated_at_by_snapshot[document.snapshot_id] = (
            snapshot_evaluated_at.astimezone(timezone.utc)
        )
    return tuple(result), evaluated_at_by_snapshot


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


def _proven_current_offers(
    offers: list[core_models.Offer],
    evidence_by_offer: Mapping[int, OfferEvidence],
    *,
    evaluated_at: datetime,
) -> list[core_models.Offer]:
    """Conserve seulement l'état marchand rapproché d'un relevé append-only."""

    return [
        offer
        for offer in offers
        if (
            (evidence := evidence_by_offer.get(offer.id)) is not None
            and evidence.current_observed_at is not None
            and offer_observation_is_fresh(
                evidence.current_observed_at,
                now=evaluated_at,
            )
        )
    ]


def _price_fact(
    offers: list[core_models.Offer],
    evidence_by_offer: Mapping[int, OfferEvidence],
    *,
    evaluated_at: datetime,
) -> Fact:
    valid: list[tuple[float, str, int]] = []
    for offer in _proven_current_offers(
        offers,
        evidence_by_offer,
        evaluated_at=evaluated_at,
    ):
        evidence = evidence_by_offer[offer.id]
        currency = evidence.currency
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


def _candidate_facts(
    entity_ref: str,
    offers: list[core_models.Offer],
    evidence_by_offer: Mapping[int, OfferEvidence],
    market_evidence_by_offer: Mapping[int, tuple[OfferMarketEvidence, ...]],
    *,
    evaluated_at: datetime,
) -> CandidateFacts:
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
    current = _proven_current_offers(
        offers,
        evidence_by_offer,
        evaluated_at=evaluated_at,
    )
    stock_refs = tuple(f"offer:{offer.id}:stock" for offer in current)
    if current:
        availability = Fact(
            "known",
            "in_stock",
            stock_refs,
        )
    elif all(offer.in_stock is False for offer in offers):
        availability = Fact("known", "out_of_stock", stock_refs)
    elif offers:
        availability = Fact("unknown", evidence_refs=stock_refs)
    else:
        availability = Fact("unknown")

    fresh_market_evidence = tuple(
        evidence
        for offer in current
        for evidence in market_evidence_by_offer.get(offer.id, ())
        if offer_observation_is_fresh(evidence.observed_at, now=evaluated_at)
    )
    country_values = sorted({item.country_code for item in fresh_market_evidence})
    countries = (
        Fact(
            "known",
            country_values,
            tuple(sorted({item.evidence_ref for item in fresh_market_evidence})),
        )
        if country_values
        else Fact("unknown")
    )
    return CandidateFacts(
        entity_ref=entity_ref,
        price=_price_fact(
            offers,
            evidence_by_offer,
            evaluated_at=evaluated_at,
        ),
        countries=countries,
        availability=availability,
        adult_restricted=Fact(
            "known",
            any(offer.is_adult is True for offer in offers),
            tuple(f"offer:{offer.id}:adult" for offer in offers),
        ),
        attributes={},
        preference_facts={},
    )


def _option_items(
    *,
    request: V2OnlineReadRequest,
    retrieval: FusionResult,
    constraints,
    by_id: Mapping[int, core_models.Offer],
    merchant_by_id: Mapping[int, core_models.Merchant],
    evidence_by_offer: Mapping[int, OfferEvidence],
    market_evidence_by_offer: Mapping[int, tuple[OfferMarketEvidence, ...]],
    evaluated_at: datetime,
) -> tuple[dict[str, object], ...]:
    """Matérialise au plus cinq options prouvées, dans l'ordre P5.

    L'ordre est celui de la fusion retrieval. Il ne devient jamais une note de
    qualité et le prix n'est utilisé qu'entre offres de même entité.
    """

    eligible = {
        candidate.entity_ref
        for candidate in constraints.candidates
        if candidate.status == "ELIGIBLE"
    }
    items: list[dict[str, object]] = []
    for candidate in retrieval.candidates:
        if candidate.entity_ref not in eligible:
            continue
        candidate_offers = _proven_current_offers(
            [by_id[value] for value in candidate.offer_ids if value in by_id],
            evidence_by_offer,
            evaluated_at=evaluated_at,
        )
        if request.country_code is not None:
            candidate_offers = [
                offer
                for offer in candidate_offers
                if any(
                    evidence.country_code == request.country_code
                    and offer_observation_is_fresh(
                        evidence.observed_at,
                        now=evaluated_at,
                    )
                    for evidence in market_evidence_by_offer.get(offer.id, ())
                )
            ]
        if request.budget_currency is not None:
            candidate_offers = [
                offer
                for offer in candidate_offers
                if evidence_by_offer[offer.id].currency == request.budget_currency
            ]
        candidate_offers.sort(key=lambda offer: (float(offer.price), offer.id))
        if not candidate_offers:
            continue
        offer = candidate_offers[0]
        merchant = merchant_by_id.get(offer.merchant_id)
        evidence = evidence_by_offer[offer.id]
        currency = evidence.currency
        observed_at = format_utc_timestamp(evidence.current_observed_at)
        if (
            merchant is None
            or currency is None
            or observed_at is None
            or offer.price is None
        ):
            continue
        items.append(
            {
                "entity_ref": candidate.entity_ref,
                "offer_ref": f"offer:{offer.id}",
                "name": offer.name,
                "brand": offer.brand,
                "image_url": offer.image_url,
                "merchant": merchant.name,
                "merchant_ref": f"merchant:{merchant.id}",
                "price": {"amount": f"{float(offer.price):.2f}", "currency": currency},
                "availability": "in_stock",
                "listing_market": request.country_code,
                "observed_at": observed_at,
                "destination_url": offer.deep_link or offer.product_url,
                "ranking_basis": "retrieval_and_hard_constraints_only",
                "unknowns": [
                    "shipping_cost",
                    "delivery_time",
                    "returns",
                    "cashback",
                    "product_quality",
                    "buy_wait",
                ],
                "evidence_refs": [
                    f"offer:{offer.id}:price",
                    f"offer:{offer.id}:stock",
                    *[
                        evidence.evidence_ref
                        for evidence in market_evidence_by_offer.get(offer.id, ())
                        if request.country_code is not None
                        and evidence.country_code == request.country_code
                        and offer_observation_is_fresh(
                            evidence.observed_at,
                            now=evaluated_at,
                        )
                    ],
                    *[
                        source.evidence_ref
                        for source in candidate.source_evidence
                    ],
                ],
            }
        )
        if len(items) == 5:
            break
    return tuple(items)


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


async def inspect_v2_online(
    session,
    request: V2OnlineReadRequest,
    *,
    evaluated_at: datetime,
) -> V2OnlineInspection:
    """Prépare une lecture et mesure la fraîcheur de ses preuves exactes."""

    if evaluated_at.tzinfo is None:
        raise V2OnlineReaderError("evaluated_at must include a timezone")
    evaluated = evaluated_at.astimezone(timezone.utc)
    documents, snapshot_times = await _documents(session)
    query_digest, retrieval = _retrieval(request, documents)
    candidate_entities = {
        candidate.entity_ref for candidate in retrieval.candidates
    }
    used_snapshot_ids = {
        document.snapshot_id
        for document in documents
        if document.entity_ref in candidate_entities
    }
    used_times = [
        snapshot_times[snapshot_id]
        for snapshot_id in sorted(used_snapshot_ids)
        if snapshot_id in snapshot_times
    ]
    future_evidence = any(value > evaluated for value in used_times)
    dependencies_admissible = bool(used_times) and not future_evidence
    data_age_seconds = (
        max(int((evaluated - value).total_seconds()) for value in used_times)
        if dependencies_admissible
        else None
    )
    return V2OnlineInspection(
        request_key=_request_key(request),
        evaluated_at=evaluated,
        documents=documents,
        query_digest=query_digest,
        retrieval=retrieval,
        data_age_seconds=data_age_seconds,
        dependencies_admissible=dependencies_admissible,
    )


async def read_v2_online(
    session,
    request: V2OnlineReadRequest,
    *,
    evaluated_at: datetime,
    inspection: V2OnlineInspection | None = None,
) -> V2CanaryPayload:
    """Exécute P5→P10 sans persistance et retourne une abstention prouvée."""

    if evaluated_at.tzinfo is None:
        raise V2OnlineReaderError("evaluated_at must include a timezone")
    evaluated = evaluated_at.astimezone(timezone.utc)
    prepared = inspection or await inspect_v2_online(
        session,
        request,
        evaluated_at=evaluated,
    )
    if (
        prepared.request_key != _request_key(request)
        or prepared.evaluated_at != evaluated
    ):
        raise V2OnlineReaderError("online inspection does not match the request")
    documents = prepared.documents
    query_digest = prepared.query_digest
    retrieval = prepared.retrieval
    offer_ids = sorted(
        {
            offer_id
            for candidate in retrieval.candidates
            for offer_id in candidate.offer_ids
        }
    )
    offer_rows = (
        (
            await session.execute(
                select(core_models.Offer, core_models.Merchant)
                .join(
                    core_models.Merchant,
                    core_models.Offer.merchant_id == core_models.Merchant.id,
                )
                .where(core_models.Offer.id.in_(offer_ids))
            )
        )
        .all()
        if offer_ids
        else []
    )
    offers = [offer for offer, _merchant in offer_rows]
    by_id = {offer.id: offer for offer in offers}
    merchant_by_id = {merchant.id: merchant for _offer, merchant in offer_rows}
    evidence_by_offer = await load_offer_evidence(
        session,
        offers,
        current_only=True,
    )
    market_evidence_by_offer = await load_offer_listing_markets(session, offer_ids)
    candidate_facts = [
        _candidate_facts(
            candidate.entity_ref,
            [by_id[value] for value in candidate.offer_ids if value in by_id],
            evidence_by_offer,
            market_evidence_by_offer,
            evaluated_at=evaluated,
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
            "online reader downstream decision stages must remain fail-closed"
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
    items = _option_items(
        request=request,
        retrieval=retrieval,
        constraints=constraints,
        by_id=by_id,
        merchant_by_id=merchant_by_id,
        evidence_by_offer=evidence_by_offer,
        market_evidence_by_offer=market_evidence_by_offer,
        evaluated_at=evaluated,
    )
    outcome = "FACTUAL_OPTIONS" if items else "ABSTAIN"
    response = {
        "schema_version": "v2-online-response/v2",
        "reader_version": ONLINE_READER_VERSION,
        "outcome": outcome,
        "query_digest": query_digest,
        "reason_codes": (
            [
                "factual_options_only",
                "product_quality_not_claimed",
                "buy_wait_not_calibrated",
            ]
            if items
            else [
                "v2_actionable_evidence_incomplete",
                f"retrieval_{retrieval.outcome.lower()}",
                f"ranking_{ranking.outcome.lower()}",
                "confidence_not_calibrated",
            ]
        ),
        "items": [dict(item) for item in items],
        "provenance": [dict(item) for item in provenance],
        "raw_query_retained": False,
    }
    return V2CanaryPayload(
        response=response,
        chain_complete=True,
        safety_state="SAFE" if items else "ABSTAIN",
        provenance_complete=True,
        response_type=outcome,
    )
