"""Policy de claims sourcés et d'éligibilité fail-closed."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import select

from app.evidence_engine import models
from app.offer_graph.models import GraphOfferObservation
from app.product_graph.models import GraphOfferVariantLink


POLICY_VERSION = "claim-eligibility-shadow-v1"
OFFER_CLAIM_TTL = timedelta(hours=72)
ATOMIC_CLAIMS = (
    "PRICE_OBSERVED",
    "AVAILABILITY_OBSERVED",
    "MERCHANT_LINK_OBSERVED",
    "VARIANT_IDENTITY_EXACT",
)
STRONG_CLAIMS = (
    "LOWEST_OBSERVED_PRICE",
    "BEST_VERIFIED_OFFER",
    "BUY_NOW",
    "WAIT",
    "HIGH_CONFIDENCE",
    "CERTIFIED_REFURB",
    "MAX_CASHBACK",
)


class EvidencePolicyError(ValueError):
    """Entrée ou horloge hors contrat."""


@dataclass(frozen=True)
class ClaimEvaluation:
    claim_code: str
    subject_type: str
    subject_ref: str
    value: Any | None
    knowledge_status: str
    source_type: str
    source_ref: str
    confidence: None
    observed_at: datetime
    evaluated_at: datetime
    valid_until: datetime | None
    eligibility: str
    reason_code: str


@dataclass(frozen=True)
class DecisionEvaluation:
    highest_stage: str
    decision_eligible: bool
    blocker_reason: str


def _fresh(observed_at: datetime, evaluated_at: datetime) -> bool:
    return observed_at <= evaluated_at <= observed_at + OFFER_CLAIM_TTL


def _claim(
    observation: GraphOfferObservation,
    *,
    evaluated_at: datetime,
    code: str,
    value: Any | None,
    eligible: bool,
    reason: str,
    expires: bool = True,
    missing_eligibility: str = "unknown",
) -> ClaimEvaluation:
    return ClaimEvaluation(
        claim_code=code,
        subject_type="offer",
        subject_ref=f"offer:{observation.offer_id}",
        value=value if eligible else None,
        knowledge_status="VERIFIED" if eligible else "UNKNOWN",
        source_type="offer_graph",
        source_ref=f"graph_offer_observation:{observation.id}",
        confidence=None,
        observed_at=observation.observed_at,
        evaluated_at=evaluated_at,
        valid_until=(observation.observed_at + OFFER_CLAIM_TTL if expires else None),
        eligibility="eligible" if eligible else missing_eligibility,
        reason_code="eligible_verified" if eligible else reason,
    )


async def evaluate_offer_claims(
    session,
    *,
    observation: GraphOfferObservation,
    evaluated_at: datetime,
) -> tuple[tuple[ClaimEvaluation, ...], DecisionEvaluation]:
    if evaluated_at.tzinfo is not None:
        raise EvidencePolicyError("evaluated_at must be UTC-naive internally")
    if observation.id is None or observation.raw_source_record_id <= 0:
        raise EvidencePolicyError("offer observation must be persisted")
    link = None
    if observation.offer_variant_link_id is not None:
        link = await session.get(
            GraphOfferVariantLink,
            observation.offer_variant_link_id,
        )
    identity_resolved = bool(
        link is not None
        and link.resolution == "resolved"
        and link.raw_source_record_id == observation.raw_source_record_id
        and link.offer_id == observation.offer_id
    )
    fresh = _fresh(observation.observed_at, evaluated_at)

    price_ok = bool(
        fresh
        and observation.price_state == "known"
        and observation.price_amount is not None
        and observation.price_currency is not None
    )
    availability_known = bool(fresh and observation.availability != "unknown")
    in_stock = bool(fresh and observation.availability == "in_stock")
    link_ok = bool(fresh and observation.merchant_url_state == "known")
    identity_ok = bool(
        observation.observed_at <= evaluated_at and identity_resolved
    )
    claims = [
        _claim(
            observation,
            evaluated_at=evaluated_at,
            code="PRICE_OBSERVED",
            value={
                "amount": format(Decimal(observation.price_amount), "f"),
                "currency": observation.price_currency,
            }
            if price_ok
            else None,
            eligible=price_ok,
            reason=(
                "price_stale"
                if observation.price_state == "known"
                else "price_invalid"
                if observation.price_state == "invalid"
                else "price_unknown"
            ),
        ),
        _claim(
            observation,
            evaluated_at=evaluated_at,
            code="AVAILABILITY_OBSERVED",
            value=observation.availability if availability_known else None,
            eligible=availability_known,
            reason=(
                "availability_unknown"
                if observation.availability == "unknown"
                else "availability_stale"
            ),
        ),
        _claim(
            observation,
            evaluated_at=evaluated_at,
            code="MERCHANT_LINK_OBSERVED",
            value={"url": observation.merchant_url} if link_ok else None,
            eligible=link_ok,
            reason=(
                "merchant_link_stale"
                if observation.merchant_url_state == "known"
                else "merchant_link_invalid"
                if observation.merchant_url_state == "invalid"
                else "merchant_link_unknown"
            ),
        ),
        _claim(
            observation,
            evaluated_at=evaluated_at,
            code="VARIANT_IDENTITY_EXACT",
            value={"variant_id": link.variant_id} if identity_ok else None,
            eligible=identity_ok,
            reason="identity_unresolved",
            expires=False,
        ),
    ]
    strong_reasons = {
        "LOWEST_OBSERVED_PRICE": "coverage_insufficient",
        "BEST_VERIFIED_OFFER": "country_shipping_unknown",
        "BUY_NOW": "calibration_missing",
        "WAIT": "calibration_missing",
        "HIGH_CONFIDENCE": "calibration_missing",
        "CERTIFIED_REFURB": "certification_missing",
        "MAX_CASHBACK": "cashback_coverage_missing",
    }
    for code in STRONG_CLAIMS:
        claims.append(
            _claim(
                observation,
                evaluated_at=evaluated_at,
                code=code,
                value=None,
                eligible=False,
                reason=strong_reasons[code],
                missing_eligibility="ineligible",
            )
        )

    if identity_ok and price_ok and in_stock and link_ok:
        decision = DecisionEvaluation(
            highest_stage="RANKABLE",
            decision_eligible=False,
            blocker_reason="country_shipping_unknown",
        )
    elif identity_ok and price_ok:
        decision = DecisionEvaluation(
            highest_stage="COMPARABLE",
            decision_eligible=False,
            blocker_reason=(
                "availability_unknown"
                if not availability_known
                else "out_of_stock"
                if not in_stock
                else "merchant_link_unknown"
            ),
        )
    else:
        decision = DecisionEvaluation(
            highest_stage="DISCOVERABLE",
            decision_eligible=False,
            blocker_reason="identity_unresolved" if not identity_ok else "price_unknown",
        )
    return tuple(claims), decision


async def persist_offer_evaluation(
    session,
    *,
    observation: GraphOfferObservation,
    claims: tuple[ClaimEvaluation, ...],
    decision: DecisionEvaluation,
) -> tuple[int, bool]:
    if tuple(claim.claim_code for claim in claims) != ATOMIC_CLAIMS + STRONG_CLAIMS:
        raise EvidencePolicyError("claim roster is incomplete or reordered")
    created_claims = 0
    for claim in claims:
        existing = await session.scalar(
            select(models.EvidenceClaimRecord.id).where(
                models.EvidenceClaimRecord.offer_observation_id == observation.id,
                models.EvidenceClaimRecord.claim_code == claim.claim_code,
                models.EvidenceClaimRecord.policy_version == POLICY_VERSION,
                models.EvidenceClaimRecord.evaluated_at == claim.evaluated_at,
            )
        )
        if existing is not None:
            continue
        session.add(
            models.EvidenceClaimRecord(
                raw_source_record_id=observation.raw_source_record_id,
                offer_observation_id=observation.id,
                subject_type=claim.subject_type,
                subject_ref=claim.subject_ref,
                claim_code=claim.claim_code,
                value_json=claim.value,
                knowledge_status=claim.knowledge_status,
                source_type=claim.source_type,
                source_ref=claim.source_ref,
                confidence=claim.confidence,
                observed_at=claim.observed_at,
                evaluated_at=claim.evaluated_at,
                valid_until=claim.valid_until,
                eligibility=claim.eligibility,
                reason_code=claim.reason_code,
                policy_version=POLICY_VERSION,
            )
        )
        created_claims += 1
    existing_decision = await session.scalar(
        select(models.DecisionEligibilityRecord.id).where(
            models.DecisionEligibilityRecord.offer_observation_id == observation.id,
            models.DecisionEligibilityRecord.policy_version == POLICY_VERSION,
            models.DecisionEligibilityRecord.evaluated_at == claims[0].evaluated_at,
        )
    )
    decision_created = existing_decision is None
    if decision_created:
        session.add(
            models.DecisionEligibilityRecord(
                raw_source_record_id=observation.raw_source_record_id,
                offer_observation_id=observation.id,
                offer_id=observation.offer_id,
                highest_stage=decision.highest_stage,
                decision_eligible=decision.decision_eligible,
                blocker_reason=decision.blocker_reason,
                evaluated_at=claims[0].evaluated_at,
                policy_version=POLICY_VERSION,
            )
        )
    await session.flush()
    return created_claims, decision_created
