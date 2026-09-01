"""Replay borné et persistance shadow des décisions Entity Resolution Phase 2.

La commande est en lecture seule par défaut. ``--apply`` exige le flag Phase 2
et n'écrit que dans les deux tables d'expansion dédiées. Une même version ne
peut jamais être réécrite avec un contenu différent : le replay échoue fermé.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.db import session as db
from app.observations.models import Observation, RawSourceRecord
from app.product_graph.entity_resolution import (
    MAX_CANDIDATES,
    POLICY_VERSION,
    RESOLVER_VERSION,
    STRONG_SIGNALS,
    EntityDecision,
    resolve_entity_candidates,
)
from app.product_graph.entity_signals import (
    EXTRACTOR_VERSION,
    project_entity_signals,
)
from app.product_graph.models import (
    GraphEntityResolutionDecision,
    GraphEntitySignalProjection,
    GraphOfferVariantLink,
)


log = get_logger("product_graph.entity_replay")
MAX_REPLAY_ROWS = 10_000
IDENTIFIER_FIELDS = ("gtin", "ean", "ean13", "upc")
CANDIDATE_WEAK_SIGNALS = {"title", "image"}


class EntityReplayError(RuntimeError):
    """Replay impossible à prouver sans masquer un conflit."""


@dataclass(frozen=True)
class EntityReplayReport:
    mode: str
    scanned: int
    projected: int
    missing_offer_links: int
    candidate_profiles: int
    exact_verified: int
    high_confidence: int
    probable: int
    ambiguous: int
    unresolved: int
    signal_projections_created: int
    signal_projections_existing: int
    decisions_created: int
    decisions_existing: int
    last_raw_source_id: int | None
    evaluation_id: str


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
    # PostgreSQL DateTime historique est sans timezone mais FILON stocke ces
    # timestamps en UTC. L'explicitation fait partie du profil rejouable.
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def _profile(raw: RawSourceRecord) -> dict[str, Any]:
    observed_at = _aware(raw.observed_at)
    projection = project_entity_signals(
        raw.payload_json,
        raw_source_record_id=raw.id,
        source_type=raw.source_type,
        source_ref=raw.source_ref,
        observed_at=observed_at,
    )
    identifiers = {
        field: raw.payload_json[field]
        for field in IDENTIFIER_FIELDS
        if field in raw.payload_json and raw.payload_json[field] not in (None, "")
    }
    return {
        "raw_source_record_id": raw.id,
        "source_type": raw.source_type,
        "source_ref": raw.source_ref,
        "observed_at": observed_at.isoformat(),
        "identifiers": identifiers,
        "signals": [signal.as_contract() for signal in projection.signals],
    }


def _identifier_keys(profile: dict[str, Any]) -> set[str]:
    identifiers = profile.get("identifiers")
    if not isinstance(identifiers, dict):
        return set()
    return {
        str(value).strip()
        for value in identifiers.values()
        if not isinstance(value, bool)
        and isinstance(value, (str, int))
        and str(value).strip()
    }


def _signal_keys(
    profile: dict[str, Any],
    *,
    names: set[str],
    statuses: set[str],
) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for signal in profile.get("signals", ()):
        if (
            not isinstance(signal, dict)
            or signal.get("signal") not in names
            or signal.get("status") not in statuses
        ):
            continue
        for value in signal.get("normalized_values", ()):
            if isinstance(value, str) and value:
                keys.add((str(signal["signal"]), value))
    return keys


def _candidate_roster(
    subject: dict[str, Any],
    candidate_profiles: dict[int, dict[str, Any]],
) -> list[dict[str, Any]]:
    identifier_index: dict[str, set[int]] = defaultdict(set)
    strong_index: dict[tuple[str, str], set[int]] = defaultdict(set)
    weak_index: dict[tuple[str, str], set[int]] = defaultdict(set)
    for candidate_id, profile in candidate_profiles.items():
        for key in _identifier_keys(profile):
            identifier_index[key].add(candidate_id)
        for key in _signal_keys(
            profile,
            names=set(STRONG_SIGNALS),
            statuses={"observed"},
        ):
            strong_index[key].add(candidate_id)
        for key in _signal_keys(
            profile,
            names=CANDIDATE_WEAK_SIGNALS,
            statuses={"observed", "candidate_only"},
        ):
            weak_index[key].add(candidate_id)

    candidate_ids: set[int] = set()
    for key in _identifier_keys(subject):
        candidate_ids.update(identifier_index.get(key, ()))
    if not candidate_ids:
        for key in _signal_keys(
            subject,
            names=set(STRONG_SIGNALS),
            statuses={"observed"},
        ):
            candidate_ids.update(strong_index.get(key, ()))
    if not candidate_ids:
        for key in _signal_keys(
            subject,
            names=CANDIDATE_WEAK_SIGNALS,
            statuses={"observed", "candidate_only"},
        ):
            candidate_ids.update(weak_index.get(key, ()))
    if len(candidate_ids) > MAX_CANDIDATES:
        raise EntityReplayError(
            f"candidate roster exceeds the fail-closed bound ({len(candidate_ids)})"
        )
    return [
        {**candidate_profiles[candidate_id], "candidate_id": candidate_id}
        for candidate_id in sorted(candidate_ids)
    ]


async def _offer_map(session, raw_ids: list[int]) -> dict[int, int]:
    if not raw_ids:
        return {}
    rows = (
        await session.execute(
            select(Observation.raw_source_record_id, Observation.offer_id)
            .where(
                Observation.raw_source_record_id.in_(raw_ids),
                Observation.offer_id.is_not(None),
            )
            .distinct()
        )
    ).all()
    grouped: dict[int, set[int]] = defaultdict(set)
    for raw_id, offer_id in rows:
        grouped[int(raw_id)].add(int(offer_id))
    conflicts = [raw_id for raw_id, offer_ids in grouped.items() if len(offer_ids) > 1]
    if conflicts:
        raise EntityReplayError("raw source points to multiple Core offers")
    return {raw_id: next(iter(offer_ids)) for raw_id, offer_ids in grouped.items()}


async def _variant_map(session) -> dict[int, int]:
    rows = (
        await session.execute(
            select(
                GraphOfferVariantLink.raw_source_record_id,
                GraphOfferVariantLink.variant_id,
            ).where(
                GraphOfferVariantLink.resolution == "resolved",
                GraphOfferVariantLink.variant_id.is_not(None),
            )
        )
    ).all()
    grouped: dict[int, set[int]] = defaultdict(set)
    for raw_id, variant_id in rows:
        grouped[int(raw_id)].add(int(variant_id))
    if any(len(variant_ids) > 1 for variant_ids in grouped.values()):
        raise EntityReplayError("raw source resolves to multiple canonical variants")
    return {raw_id: next(iter(variant_ids)) for raw_id, variant_ids in grouped.items()}


async def _stored_profiles(session) -> dict[int, dict[str, Any]]:
    rows = (
        await session.execute(
            select(GraphEntitySignalProjection).where(
                GraphEntitySignalProjection.extractor_version == EXTRACTOR_VERSION
            )
        )
    ).scalars().all()
    return {row.raw_source_record_id: row.profile_json for row in rows}


def _canonical_profiles(
    profiles_by_raw: dict[int, dict[str, Any]],
    variant_by_raw: dict[int, int],
) -> dict[int, dict[str, Any]]:
    canonical: dict[int, dict[str, Any]] = {}
    canonical_raw: dict[int, int] = {}
    for raw_id, variant_id in sorted(variant_by_raw.items()):
        profile = profiles_by_raw.get(raw_id)
        if profile is None:
            continue
        if variant_id not in canonical or raw_id < canonical_raw[variant_id]:
            canonical[variant_id] = profile
            canonical_raw[variant_id] = raw_id
    return canonical


async def _persist_profile(
    session,
    *,
    profile: dict[str, Any],
) -> bool:
    raw_id = int(profile["raw_source_record_id"])
    projection_key = _digest(
        {
            "raw_source_record_id": raw_id,
            "extractor_version": EXTRACTOR_VERSION,
            "profile": profile,
        }
    )
    existing = await session.scalar(
        select(GraphEntitySignalProjection).where(
            GraphEntitySignalProjection.raw_source_record_id == raw_id,
            GraphEntitySignalProjection.extractor_version == EXTRACTOR_VERSION,
        )
    )
    if existing is not None:
        if existing.projection_key != projection_key or existing.profile_json != profile:
            raise EntityReplayError("signal replay divergence")
        return False
    observed_at = datetime.fromisoformat(str(profile["observed_at"]))
    session.add(
        GraphEntitySignalProjection(
            projection_key=projection_key,
            raw_source_record_id=raw_id,
            source_type=str(profile["source_type"]),
            source_ref=str(profile["source_ref"]),
            observed_at=observed_at.replace(tzinfo=None),
            extractor_version=EXTRACTOR_VERSION,
            profile_json=profile,
        )
    )
    await session.flush()
    return True


async def _persist_decision(
    session,
    *,
    raw_id: int,
    offer_id: int,
    observed_at: datetime,
    decision: EntityDecision,
) -> bool:
    contract = decision.as_contract()
    decision_key = _digest(
        {
            "raw_source_record_id": raw_id,
            "offer_id": offer_id,
            "extractor_version": EXTRACTOR_VERSION,
            "decision": contract,
        }
    )
    existing = await session.scalar(
        select(GraphEntityResolutionDecision).where(
            GraphEntityResolutionDecision.raw_source_record_id == raw_id,
            GraphEntityResolutionDecision.resolver_version == RESOLVER_VERSION,
            GraphEntityResolutionDecision.policy_version == POLICY_VERSION,
        )
    )
    if existing is not None:
        if existing.decision_key != decision_key:
            raise EntityReplayError("decision replay divergence")
        return False
    session.add(
        GraphEntityResolutionDecision(
            decision_key=decision_key,
            raw_source_record_id=raw_id,
            offer_id=offer_id,
            subject_type=decision.subject_type,
            resolution=decision.resolution,
            canonical_variant_id=decision.canonical_id,
            candidate_ids_json=list(decision.candidate_ids),
            confidence_score=decision.confidence_score,
            reason_codes_json=list(decision.reason_codes),
            evidence_json=[item.as_contract() for item in decision.evidence],
            conflicts_json=[item.as_contract() for item in decision.conflicts],
            extractor_version=EXTRACTOR_VERSION,
            resolver_version=RESOLVER_VERSION,
            policy_version=POLICY_VERSION,
            observed_at=_aware(observed_at).replace(tzinfo=None),
        )
    )
    await session.flush()
    return True


async def replay_entity_resolution_batch(
    session,
    *,
    after_raw_id: int = 0,
    limit: int = 1_000,
    apply: bool = False,
) -> EntityReplayReport:
    """Projette et décide au plus ``limit`` raws, en ordre primaire stable."""

    if isinstance(after_raw_id, bool) or not isinstance(after_raw_id, int) or after_raw_id < 0:
        raise ValueError("after_raw_id must be a non-negative integer")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_REPLAY_ROWS:
        raise ValueError(f"limit must be between 1 and {MAX_REPLAY_ROWS}")
    raws = (
        (
            await session.execute(
                select(RawSourceRecord)
                .where(
                    RawSourceRecord.source_type == "awin_feed",
                    RawSourceRecord.id > after_raw_id,
                )
                .order_by(RawSourceRecord.id)
                .limit(limit)
            )
        )
        .scalars()
        .all()
    )
    raw_ids = [raw.id for raw in raws]
    offers = await _offer_map(session, raw_ids)
    projected = {raw.id: _profile(raw) for raw in raws if raw.id in offers}
    profiles_by_raw = await _stored_profiles(session)
    profiles_by_raw.update(projected)
    variants = await _variant_map(session)
    candidate_profiles = _canonical_profiles(profiles_by_raw, variants)

    decisions: list[tuple[RawSourceRecord, int, EntityDecision]] = []
    states: dict[str, int] = defaultdict(int)
    for raw in raws:
        offer_id = offers.get(raw.id)
        if offer_id is None:
            continue
        profile = projected[raw.id]
        decision = resolve_entity_candidates(
            profile,
            _candidate_roster(profile, candidate_profiles),
            subject_type="variant",
        )
        states[decision.resolution] += 1
        decisions.append((raw, offer_id, decision))

    signal_created = signal_existing = decision_created = decision_existing = 0
    if apply:
        for raw_id in sorted(projected):
            if await _persist_profile(session, profile=projected[raw_id]):
                signal_created += 1
            else:
                signal_existing += 1
        for raw, offer_id, decision in decisions:
            if await _persist_decision(
                session,
                raw_id=raw.id,
                offer_id=offer_id,
                observed_at=raw.observed_at,
                decision=decision,
            ):
                decision_created += 1
            else:
                decision_existing += 1
        await session.commit()

    evaluation_id = _digest(
        [
            {
                "raw_source_record_id": raw.id,
                "offer_id": offer_id,
                "decision": decision.as_contract(),
            }
            for raw, offer_id, decision in decisions
        ]
    )
    return EntityReplayReport(
        mode="apply" if apply else "dry_run",
        scanned=len(raws),
        projected=len(projected),
        missing_offer_links=len(raws) - len(projected),
        candidate_profiles=len(candidate_profiles),
        exact_verified=states["EXACT_VERIFIED"],
        high_confidence=states["HIGH_CONFIDENCE"],
        probable=states["PROBABLE"],
        ambiguous=states["AMBIGUOUS"],
        unresolved=states["UNRESOLVED"],
        signal_projections_created=signal_created,
        signal_projections_existing=signal_existing,
        decisions_created=decision_created,
        decisions_existing=decision_existing,
        last_raw_source_id=raws[-1].id if raws else None,
        evaluation_id=f"sha256:{evaluation_id}",
    )


async def _run(args: argparse.Namespace) -> EntityReplayReport:
    settings = get_settings()
    configure_logging(settings.debug)
    if args.apply and not settings.entity_resolution_shadow_enabled:
        raise RuntimeError("ENTITY_RESOLUTION_SHADOW_ENABLED is required for --apply")
    if not db.is_enabled():
        raise RuntimeError("DATABASE_URL is required")
    await db.prepare_schema()
    async with db.session_scope() as session:
        if session is None:
            raise RuntimeError("database session unavailable")
        return await replay_entity_resolution_batch(
            session,
            after_raw_id=args.after_raw_id,
            limit=args.limit,
            apply=args.apply,
        )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Replay borné Entity Resolution shadow Phase 2",
    )
    parser.add_argument("--after-raw-id", type=int, default=0)
    parser.add_argument("--limit", type=int, default=1_000)
    parser.add_argument("--apply", action="store_true")
    return parser


def main() -> None:
    report = asyncio.run(_run(_parser().parse_args()))
    print(json.dumps(asdict(report), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
