"""Resolver hiérarchique Entity Resolution v1, shadow et explicable."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any


RESOLVER_VERSION = "entity-resolution-shadow-v1"
POLICY_VERSION = "entity-resolution-policy-v1"
MAX_CANDIDATES = 100
STRONG_SIGNALS = {
    "mpn",
    "model",
    "storage",
    "memory",
    "capacity",
    "size",
    "color",
    "generation",
    "edition",
    "condition",
    "pack_quantity",
    "product_role",
}
VARIANT_SIGNALS = STRONG_SIGNALS - {"mpn", "model"}
WEAK_SIGNALS = {"brand", "title", "image", "taxonomy"}


class EntityResolverError(ValueError):
    """Profil, roster ou preuve hors contrat."""


@dataclass(frozen=True)
class ResolverEvidence:
    raw_source_record_id: int
    source_type: str
    source_ref: str
    observed_at: str
    signal: str
    field: str
    normalized_value: str
    strength: str
    role: str
    transformation: str
    transformation_version: str

    def as_contract(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class ResolverConflict:
    field: str
    reason_code: str
    evidence_raw_source_ids: tuple[int, ...]

    def as_contract(self) -> dict[str, Any]:
        return {
            "field": self.field,
            "reason_code": self.reason_code,
            "evidence_raw_source_ids": list(self.evidence_raw_source_ids),
        }


@dataclass(frozen=True)
class EntityDecision:
    subject_type: str
    resolution: str
    canonical_id: int | None
    candidate_ids: tuple[int, ...]
    confidence_score: float | None
    reason_codes: tuple[str, ...]
    evidence: tuple[ResolverEvidence, ...]
    conflicts: tuple[ResolverConflict, ...]

    def as_contract(self) -> dict[str, Any]:
        return {
            "contract_version": "1.0.0",
            "subject_type": self.subject_type,
            "resolution": self.resolution,
            "canonical_id": self.canonical_id,
            "candidate_ids": list(self.candidate_ids),
            "confidence_score": self.confidence_score,
            "reason_codes": list(self.reason_codes),
            "resolver_version": RESOLVER_VERSION,
            "policy_version": POLICY_VERSION,
            "evidence": [item.as_contract() for item in self.evidence],
            "conflicts": [item.as_contract() for item in self.conflicts],
        }


@dataclass(frozen=True)
class _Profile:
    candidate_id: int | None
    raw_source_record_id: int
    source_type: str
    source_ref: str
    observed_at: str
    gtins: tuple[str, ...]
    supplied_identifier: bool
    invalid_identifier: bool
    signals: Mapping[str, Mapping[str, Any]]


@dataclass(frozen=True)
class _CandidateMatch:
    profile: _Profile
    strong_matches: tuple[str, ...]
    weak_matches: tuple[str, ...]
    evidence: tuple[ResolverEvidence, ...]
    conflicts: tuple[ResolverConflict, ...]


def _gtin(value: Any) -> str | None:
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        return None
    text = str(value).strip()
    if not text.isdigit() or len(text) not in {8, 12, 13, 14}:
        return None
    digits = [int(character) for character in text]
    check = (10 - sum(
        digit * (3 if index % 2 == 0 else 1)
        for index, digit in enumerate(reversed(digits[:-1]))
    ) % 10) % 10
    return text if digits[-1] == check else None


def _profile(payload: Mapping[str, Any], *, candidate: bool) -> _Profile:
    if not isinstance(payload, Mapping):
        raise EntityResolverError("profile must be an object")
    candidate_id = payload.get("candidate_id")
    if candidate:
        if isinstance(candidate_id, bool) or not isinstance(candidate_id, int) or candidate_id <= 0:
            raise EntityResolverError("candidate_id must be positive")
    elif candidate_id is not None:
        raise EntityResolverError("subject cannot carry candidate_id")
    raw_id = payload.get("raw_source_record_id")
    if isinstance(raw_id, bool) or not isinstance(raw_id, int) or raw_id <= 0:
        raise EntityResolverError("raw_source_record_id must be positive")
    source_type = payload.get("source_type")
    source_ref = payload.get("source_ref")
    observed_at = payload.get("observed_at")
    if not isinstance(source_type, str) or not source_type.strip():
        raise EntityResolverError("source_type must be non-empty")
    if not isinstance(source_ref, str) or not source_ref.strip():
        raise EntityResolverError("source_ref must be non-empty")
    if isinstance(observed_at, datetime):
        if observed_at.tzinfo is None or observed_at.utcoffset() is None:
            raise EntityResolverError("observed_at must include an offset")
        observed = observed_at.isoformat()
    elif isinstance(observed_at, str) and observed_at.strip():
        try:
            parsed = datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise EntityResolverError("observed_at must be a date-time") from exc
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise EntityResolverError("observed_at must include an offset")
        observed = observed_at.strip()
    else:
        raise EntityResolverError("observed_at must be a date-time")

    identifiers = payload.get("identifiers", {})
    if not isinstance(identifiers, Mapping):
        raise EntityResolverError("identifiers must be an object")
    valid: set[str] = set()
    supplied = False
    invalid = False
    for key in ("gtin", "ean", "ean13", "upc"):
        if key not in identifiers or identifiers[key] in (None, ""):
            continue
        supplied = True
        normalized = _gtin(identifiers[key])
        if normalized is not None:
            valid.add(normalized)
        else:
            invalid = True

    raw_signals = payload.get("signals")
    if not isinstance(raw_signals, Sequence) or isinstance(raw_signals, (str, bytes, bytearray)):
        raise EntityResolverError("signals must be an array")
    signals: dict[str, Mapping[str, Any]] = {}
    if len(raw_signals) > 32:
        raise EntityResolverError("signals roster is too large")
    for raw in raw_signals:
        if not isinstance(raw, Mapping):
            raise EntityResolverError("signal must be an object")
        name = raw.get("signal")
        status = raw.get("status")
        values = raw.get("normalized_values")
        if (
            not isinstance(name, str)
            or name in signals
            or status not in {"observed", "candidate_only", "unknown", "invalid", "conflict"}
            or not isinstance(values, Sequence)
            or isinstance(values, (str, bytes, bytearray))
            or any(not isinstance(value, str) or not value or len(value) > 512 for value in values)
        ):
            raise EntityResolverError("signal contract is invalid")
        signals[name] = raw
    return _Profile(
        candidate_id=candidate_id if candidate else None,
        raw_source_record_id=raw_id,
        source_type=source_type.strip(),
        source_ref=source_ref.strip(),
        observed_at=observed,
        gtins=tuple(sorted(valid)),
        supplied_identifier=supplied,
        invalid_identifier=invalid,
        signals=signals,
    )


def _values(profile: _Profile, signal: str, *, statuses: set[str]) -> set[str]:
    item = profile.signals.get(signal)
    if item is None or item.get("status") not in statuses:
        return set()
    return set(item.get("normalized_values", ()))


def _signal_evidence(profile: _Profile, signal: str, value: str) -> ResolverEvidence:
    item = profile.signals[signal]
    fields = item.get("source_fields")
    field = fields[0] if isinstance(fields, Sequence) and fields else signal
    return ResolverEvidence(
        raw_source_record_id=profile.raw_source_record_id,
        source_type=profile.source_type,
        source_ref=profile.source_ref,
        observed_at=profile.observed_at,
        signal="variant_attribute" if signal in VARIANT_SIGNALS else signal,
        field=str(field),
        normalized_value=value[:191],
        strength=str(item.get("strength")),
        role=str(item.get("role")),
        transformation=str(item.get("transformation", "entity_signal_extraction")),
        transformation_version=str(item.get("transformation_version", "unknown")),
    )


def _gtin_evidence(profile: _Profile, value: str) -> ResolverEvidence:
    return ResolverEvidence(
        raw_source_record_id=profile.raw_source_record_id,
        source_type=profile.source_type,
        source_ref=profile.source_ref,
        observed_at=profile.observed_at,
        signal="gtin",
        field="identifier",
        normalized_value=value,
        strength="exact",
        role="primary",
        transformation="exact_gtin_phase1",
        transformation_version="v1",
    )


def _candidate_match(subject: _Profile, candidate: _Profile) -> _CandidateMatch | None:
    strong: list[str] = []
    weak: list[str] = []
    evidence: list[ResolverEvidence] = []
    conflicts: list[ResolverConflict] = []

    if candidate.invalid_identifier or len(candidate.gtins) > 1:
        conflicts.append(
            ResolverConflict(
                field="identifier",
                reason_code="identifier_conflict",
                evidence_raw_source_ids=tuple(sorted({subject.raw_source_record_id, candidate.raw_source_record_id})),
            )
        )

    subject_brand = _values(subject, "brand", statuses={"observed"})
    candidate_brand = _values(candidate, "brand", statuses={"observed"})
    brands_match = bool(subject_brand & candidate_brand)
    subject_mpn = _values(subject, "mpn", statuses={"observed"})
    candidate_mpn = _values(candidate, "mpn", statuses={"observed"})
    if subject_mpn & candidate_mpn:
        if brands_match:
            strong.append("mpn")
        elif subject_brand and candidate_brand:
            conflicts.append(
                ResolverConflict(
                    field="mpn",
                    reason_code="scope_mismatch",
                    evidence_raw_source_ids=tuple(sorted({subject.raw_source_record_id, candidate.raw_source_record_id})),
                )
            )
        else:
            weak.append("mpn")
    elif subject_mpn and candidate_mpn and brands_match:
        conflicts.append(
            ResolverConflict(
                field="mpn",
                reason_code="model_conflict",
                evidence_raw_source_ids=tuple(sorted({subject.raw_source_record_id, candidate.raw_source_record_id})),
            )
        )

    for signal in sorted(STRONG_SIGNALS - {"mpn"}):
        left = _values(subject, signal, statuses={"observed"})
        right = _values(candidate, signal, statuses={"observed"})
        shared = left & right
        if shared:
            strong.append(signal)
            value = sorted(shared)[0]
            evidence.extend((_signal_evidence(subject, signal, value), _signal_evidence(candidate, signal, value)))
        elif left and right:
            reason = "model_conflict" if signal == "model" else "variant_attribute_conflict"
            conflicts.append(
                ResolverConflict(
                    field=signal,
                    reason_code=reason,
                    evidence_raw_source_ids=tuple(sorted({subject.raw_source_record_id, candidate.raw_source_record_id})),
                )
            )
    if "mpn" in strong:
        value = sorted(subject_mpn & candidate_mpn)[0]
        evidence.extend((_signal_evidence(subject, "mpn", value), _signal_evidence(candidate, "mpn", value)))
        brand_value = sorted(subject_brand & candidate_brand)[0]
        evidence.extend((_signal_evidence(subject, "brand", brand_value), _signal_evidence(candidate, "brand", brand_value)))

    for signal in sorted(WEAK_SIGNALS | (STRONG_SIGNALS - {"mpn"})):
        if signal in strong:
            continue
        left = _values(subject, signal, statuses={"candidate_only", "observed"})
        right = _values(candidate, signal, statuses={"candidate_only", "observed"})
        shared = left & right
        if shared:
            weak.append(signal)
            value = sorted(shared)[0]
            evidence.extend((_signal_evidence(subject, signal, value), _signal_evidence(candidate, signal, value)))

    profile_conflicts = [
        signal
        for profile in (subject, candidate)
        for signal, item in profile.signals.items()
        if item.get("status") in {"conflict", "invalid"}
    ]
    for signal in sorted(set(profile_conflicts)):
        conflicts.append(
            ResolverConflict(
                field=signal,
                reason_code="model_conflict" if signal in {"mpn", "model"} else "variant_attribute_conflict",
                evidence_raw_source_ids=tuple(sorted({subject.raw_source_record_id, candidate.raw_source_record_id})),
            )
        )
    if not strong and not weak and not conflicts:
        return None
    return _CandidateMatch(
        profile=candidate,
        strong_matches=tuple(sorted(set(strong))),
        weak_matches=tuple(sorted(set(weak))),
        evidence=tuple(evidence[:64]),
        conflicts=tuple(sorted(set(conflicts), key=lambda item: (item.field, item.reason_code))),
    )


def _reason_codes(match: _CandidateMatch) -> tuple[str, ...]:
    reasons: set[str] = set()
    if "mpn" in match.strong_matches:
        reasons.add("brand_scoped_mpn")
    if "model" in match.strong_matches:
        reasons.add("structured_model_agreement")
    if set(match.strong_matches) & VARIANT_SIGNALS:
        reasons.add("structured_variant_agreement")
    if match.weak_matches:
        reasons.add("candidate_generation_only")
    for conflict in match.conflicts:
        reasons.add(conflict.reason_code)
    return tuple(sorted(reasons)) or ("insufficient_evidence",)


def resolve_entity_candidates(
    subject_payload: Mapping[str, Any],
    candidate_payloads: Sequence[Mapping[str, Any]],
    *,
    subject_type: str,
) -> EntityDecision:
    """Résout un roster borné sans permettre au score de lever un veto."""

    if subject_type not in {"product_model", "variant"}:
        raise EntityResolverError("subject_type is invalid")
    if not isinstance(candidate_payloads, Sequence) or isinstance(candidate_payloads, (str, bytes, bytearray)):
        raise EntityResolverError("candidates must be an array")
    if len(candidate_payloads) > MAX_CANDIDATES:
        raise EntityResolverError("candidate roster is too large")
    subject = _profile(subject_payload, candidate=False)
    candidates = [_profile(payload, candidate=True) for payload in candidate_payloads]
    candidate_ids = [profile.candidate_id for profile in candidates]
    if len(set(candidate_ids)) != len(candidate_ids):
        raise EntityResolverError("candidate ids must be unique")

    if subject.invalid_identifier or len(subject.gtins) > 1:
        return EntityDecision(
            subject_type=subject_type,
            resolution="UNRESOLVED",
            canonical_id=None,
            candidate_ids=(),
            confidence_score=None,
            reason_codes=("identifier_conflict",),
            evidence=(),
            conflicts=(),
        )
    if subject.gtins:
        exact = [
            candidate
            for candidate in candidates
            if not candidate.invalid_identifier and candidate.gtins == subject.gtins
        ]
        if len(exact) == 1:
            gtin = subject.gtins[0]
            return EntityDecision(
                subject_type=subject_type,
                resolution="EXACT_VERIFIED",
                canonical_id=exact[0].candidate_id,
                candidate_ids=(int(exact[0].candidate_id),),
                confidence_score=1.0,
                reason_codes=("exact_global_identifier",),
                evidence=(_gtin_evidence(subject, gtin), _gtin_evidence(exact[0], gtin)),
                conflicts=(),
            )
        if len(exact) > 1:
            ids = tuple(sorted(int(candidate.candidate_id) for candidate in exact))
            raw_ids = tuple(sorted({subject.raw_source_record_id, *(candidate.raw_source_record_id for candidate in exact)}))
            evidence = tuple(_gtin_evidence(profile, subject.gtins[0]) for profile in (subject, *exact))
            return EntityDecision(
                subject_type=subject_type,
                resolution="AMBIGUOUS",
                canonical_id=None,
                candidate_ids=ids,
                confidence_score=1.0,
                reason_codes=("multiple_candidates",),
                evidence=evidence,
                conflicts=(ResolverConflict("candidate_set", "multiple_candidates", raw_ids),),
            )
        return EntityDecision(
            subject_type=subject_type,
            resolution="UNRESOLVED",
            canonical_id=None,
            candidate_ids=(),
            confidence_score=None,
            reason_codes=("missing_signal",),
            evidence=(),
            conflicts=(),
        )

    matches = [match for candidate in candidates if (match := _candidate_match(subject, candidate)) is not None]
    if not matches:
        return EntityDecision(
            subject_type=subject_type,
            resolution="UNRESOLVED",
            canonical_id=None,
            candidate_ids=(),
            confidence_score=None,
            reason_codes=("missing_signal",),
            evidence=(),
            conflicts=(),
        )
    if len(matches) > 1:
        ids = tuple(sorted(int(match.profile.candidate_id) for match in matches))
        evidence = tuple(item for match in matches for item in match.evidence)[:64]
        raw_ids = tuple(sorted({subject.raw_source_record_id, *(match.profile.raw_source_record_id for match in matches)}))
        return EntityDecision(
            subject_type=subject_type,
            resolution="AMBIGUOUS",
            canonical_id=None,
            candidate_ids=ids,
            confidence_score=None,
            reason_codes=("multiple_candidates",),
            evidence=evidence,
            conflicts=(ResolverConflict("candidate_set", "multiple_candidates", raw_ids),),
        )

    match = matches[0]
    candidate_id = int(match.profile.candidate_id)
    if match.conflicts:
        return EntityDecision(
            subject_type=subject_type,
            resolution="AMBIGUOUS",
            canonical_id=None,
            candidate_ids=(candidate_id,),
            confidence_score=None,
            reason_codes=_reason_codes(match),
            evidence=match.evidence,
            conflicts=match.conflicts,
        )
    if len(match.strong_matches) >= 2:
        score = min(0.99, 0.9 + 0.02 * len(match.strong_matches))
        return EntityDecision(
            subject_type=subject_type,
            resolution="HIGH_CONFIDENCE",
            canonical_id=candidate_id,
            candidate_ids=(candidate_id,),
            confidence_score=round(score, 4),
            reason_codes=_reason_codes(match),
            evidence=match.evidence,
            conflicts=(),
        )
    return EntityDecision(
        subject_type=subject_type,
        resolution="PROBABLE",
        canonical_id=None,
        candidate_ids=(candidate_id,),
        confidence_score=round(min(0.89, 0.4 + 0.15 * len(match.strong_matches) + 0.03 * len(match.weak_matches)), 4),
        reason_codes=_reason_codes(match),
        evidence=match.evidence,
        conflicts=(),
    )


def confidence_is_finite(decision: EntityDecision) -> bool:
    return decision.confidence_score is None or math.isfinite(decision.confidence_score)
