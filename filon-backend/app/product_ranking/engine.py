"""Moteur déterministe Product Ranking Phase 7.

Le moteur classe des identités produit déjà déclarées ``ELIGIBLE`` par le
Constraint Engine. Il ne choisit aucune offre, ne lit aucune commission et
s'abstient dès qu'une dimension nécessaire n'est pas prouvée.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Mapping, Sequence


RANKING_POLICY_VERSION = "product-ranking-policy/v1"
DIMENSIONS = ("need_fit", "product_quality", "value", "evidence")
FACT_STATES = {"known", "unknown", "invalid", "conflict"}
ELIGIBILITY_STATES = {"ELIGIBLE", "EXCLUDED", "UNKNOWN"}

# Les poids sont un contrat par verticale, jamais une formule universelle.
VERTICAL_WEIGHTS: dict[str, dict[str, Decimal]] = {
    "smartphones": {
        "need_fit": Decimal("0.35"),
        "product_quality": Decimal("0.30"),
        "value": Decimal("0.25"),
        "evidence": Decimal("0.10"),
    },
    "laptops": {
        "need_fit": Decimal("0.35"),
        "product_quality": Decimal("0.30"),
        "value": Decimal("0.25"),
        "evidence": Decimal("0.10"),
    },
    "audio": {
        "need_fit": Decimal("0.30"),
        "product_quality": Decimal("0.35"),
        "value": Decimal("0.25"),
        "evidence": Decimal("0.10"),
    },
    "fashion": {
        "need_fit": Decimal("0.35"),
        "product_quality": Decimal("0.25"),
        "value": Decimal("0.25"),
        "evidence": Decimal("0.15"),
    },
    "appliances_hvac": {
        "need_fit": Decimal("0.30"),
        "product_quality": Decimal("0.35"),
        "value": Decimal("0.25"),
        "evidence": Decimal("0.10"),
    },
    "tyres": {
        "need_fit": Decimal("0.35"),
        "product_quality": Decimal("0.35"),
        "value": Decimal("0.20"),
        "evidence": Decimal("0.10"),
    },
}


class ProductRankingError(ValueError):
    """Entrée hors contrat ou classement impossible à défendre."""


@dataclass(frozen=True)
class ScoreFact:
    state: str
    value: str | None = None
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.state not in FACT_STATES:
            raise ProductRankingError("score fact state is invalid")
        if self.state == "known" and self.value is None:
            raise ProductRankingError("known score fact requires a value")
        if self.state != "known" and self.value is not None:
            raise ProductRankingError("non-known score fact cannot carry a value")
        if any(not isinstance(item, str) or not item for item in self.evidence_refs):
            raise ProductRankingError("evidence refs must be non-empty strings")
        if len(set(self.evidence_refs)) != len(self.evidence_refs):
            raise ProductRankingError("evidence refs must be unique")


@dataclass(frozen=True)
class RankingCandidateFacts:
    entity_ref: str
    eligibility_status: str
    dimensions: Mapping[str, ScoreFact]

    def __post_init__(self) -> None:
        prefix, separator, suffix = self.entity_ref.partition(":")
        if not separator or prefix not in {"product", "model", "variant"} or not suffix:
            raise ProductRankingError("candidate entity ref is invalid")
        if self.eligibility_status not in ELIGIBILITY_STATES:
            raise ProductRankingError("candidate eligibility status is invalid")
        if set(self.dimensions) != set(DIMENSIONS):
            raise ProductRankingError("candidate dimensions must match the ranking contract")
        if any(not isinstance(value, ScoreFact) for value in self.dimensions.values()):
            raise ProductRankingError("candidate dimensions are invalid")


@dataclass(frozen=True)
class RankingRequest:
    context_ref: str
    vertical: str

    def __post_init__(self) -> None:
        if not self.context_ref:
            raise ProductRankingError("context ref is required")
        if self.vertical not in VERTICAL_WEIGHTS:
            raise ProductRankingError("vertical is unsupported")


@dataclass(frozen=True)
class DimensionEvaluation:
    name: str
    status: str
    value: str | None
    weight: str
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True)
class CandidateRanking:
    entity_ref: str
    status: str
    rank: int | None
    utility: str | None
    dimensions: tuple[DimensionEvaluation, ...]
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class ProductRanking:
    schema_version: str
    policy_version: str
    vertical: str
    context_digest: str
    raw_context_retained: bool
    outcome: str
    candidates: tuple[CandidateRanking, ...]
    ranked_entity_refs: tuple[str, ...]
    result_digest: str


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _score(fact: ScoreFact) -> Decimal | None:
    if fact.state != "known" or not fact.evidence_refs:
        return None
    try:
        value = Decimal(fact.value or "")
    except InvalidOperation:
        return None
    if not value.is_finite() or value < 0 or value > 1:
        return None
    return value


def _dimension_evaluations(
    candidate: RankingCandidateFacts,
    weights: Mapping[str, Decimal],
) -> tuple[tuple[DimensionEvaluation, ...], dict[str, Decimal]]:
    evaluations: list[DimensionEvaluation] = []
    values: dict[str, Decimal] = {}
    for name in DIMENSIONS:
        fact = candidate.dimensions[name]
        value = _score(fact)
        status = "KNOWN" if value is not None else fact.state.upper()
        if fact.state == "known" and value is None:
            status = "INVALID"
        evaluations.append(
            DimensionEvaluation(
                name=name,
                status=status,
                value=format(value, "f") if value is not None else None,
                weight=format(weights[name], "f"),
                evidence_refs=fact.evidence_refs,
            )
        )
        if value is not None:
            values[name] = value
    return tuple(evaluations), values


def rank_products(
    request: RankingRequest,
    candidates: Sequence[RankingCandidateFacts],
) -> ProductRanking:
    refs = [candidate.entity_ref for candidate in candidates]
    if len(set(refs)) != len(refs):
        raise ProductRankingError("candidate entity refs must be unique")
    weights = VERTICAL_WEIGHTS[request.vertical]
    if set(weights) != set(DIMENSIONS) or sum(weights.values()) != Decimal("1.00"):
        raise ProductRankingError("vertical weights are invalid")

    provisional: list[CandidateRanking] = []
    scored: list[tuple[Decimal, str, tuple[DimensionEvaluation, ...]]] = []
    for candidate in candidates:
        dimensions, values = _dimension_evaluations(candidate, weights)
        if candidate.eligibility_status != "ELIGIBLE":
            provisional.append(
                CandidateRanking(
                    candidate.entity_ref,
                    "INELIGIBLE",
                    None,
                    None,
                    dimensions,
                    (f"constraint_status_{candidate.eligibility_status.lower()}",),
                )
            )
            continue
        if set(values) != set(DIMENSIONS):
            missing = tuple(
                f"dimension_{candidate.dimensions[name].state}:{name}"
                if candidate.dimensions[name].state != "known"
                else f"dimension_invalid:{name}"
                for name in DIMENSIONS
                if name not in values
            )
            provisional.append(
                CandidateRanking(
                    candidate.entity_ref,
                    "UNRANKABLE",
                    None,
                    None,
                    dimensions,
                    missing,
                )
            )
            continue
        utility = sum(values[name] * weights[name] for name in DIMENSIONS).quantize(
            Decimal("0.000001"), rounding=ROUND_HALF_UP
        )
        scored.append((utility, candidate.entity_ref, dimensions))

    ranked: list[CandidateRanking] = []
    for rank, (utility, entity_ref, dimensions) in enumerate(
        sorted(scored, key=lambda item: (-item[0], item[1])), start=1
    ):
        ranked.append(
            CandidateRanking(
                entity_ref,
                "RANKED",
                rank,
                format(utility, "f"),
                dimensions,
                ("all_dimensions_known_and_sourced",),
            )
        )
    combined = tuple(ranked + sorted(provisional, key=lambda item: item.entity_ref))
    outcome = (
        "RANKED_PRODUCTS"
        if ranked
        else "ABSTAINED"
        if any(item.eligibility_status == "ELIGIBLE" for item in candidates)
        else "NO_ELIGIBLE_PRODUCT"
    )
    context_digest = _digest(
        {
            "context_ref": request.context_ref,
            "vertical": request.vertical,
            "weights": {key: format(value, "f") for key, value in weights.items()},
        }
    )
    result_payload = {
        "policy_version": RANKING_POLICY_VERSION,
        "vertical": request.vertical,
        "context_digest": context_digest,
        "outcome": outcome,
        "candidates": [asdict(item) for item in combined],
    }
    return ProductRanking(
        schema_version="product-ranking/v1",
        policy_version=RANKING_POLICY_VERSION,
        vertical=request.vertical,
        context_digest=context_digest,
        raw_context_retained=False,
        outcome=outcome,
        candidates=combined,
        ranked_entity_refs=tuple(item.entity_ref for item in ranked),
        result_digest=_digest(result_payload),
    )
