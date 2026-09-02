"""Writer shadow et effacement vérifié Personal Commerce Phase 18."""

from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from sqlalchemy import delete, func, select

from app.buy_wait.models import BuyWaitDecisionRun

from .engine import PersonalCommerceRequest, PersonalCommerceResult
from .models import PersonalCommerceDecisionRun, PersonalCommerceErasureReceipt


PERSISTENCE_VERSION = "personal-commerce-shadow-writer/v1"


class PersonalCommercePersistenceError(RuntimeError):
    """Écriture, replay ou effacement impossible à prouver."""


@dataclass(frozen=True)
class PersistenceReport:
    schema_version: str
    persistence_version: str
    mode: str
    run_key: str
    outcome: str
    action: str
    runs_created: int
    runs_existing: int
    result_digest: str
    evaluation_id: str


@dataclass(frozen=True)
class ErasureReport:
    schema_version: str
    mode: str
    request_key: str
    matched_records: int
    erased_records: int
    receipts_created: int
    receipts_existing: int
    verified_empty: bool


@dataclass(frozen=True)
class PersonalCommerceExportRecord:
    decision_ref: str
    evaluated_at: str
    outcome: str
    action: str
    selected_solution_ref: str | None
    selected_solution_kind: str | None
    matched_preference_count: int
    reason_codes: tuple[str, ...]
    retention_expires_at: str


@dataclass(frozen=True)
class PersonalCommerceExport:
    schema_version: str
    exported_at: str
    storage_scope: str
    raw_context_retained: bool
    record_count: int
    records: tuple[PersonalCommerceExportRecord, ...]


@dataclass(frozen=True)
class RetentionPurgeReport:
    schema_version: str
    mode: str
    purge_key: str
    as_of: str
    matched_records: int
    erased_records: int
    receipts_created: int
    receipts_existing: int
    verified_empty: bool


def _canonical(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _digest(value) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _subject_hmac(subject_ref: str, subject_digest_secret: str | None) -> str:
    if (
        subject_digest_secret is None
        or not 32 <= len(subject_digest_secret) <= 256
        or not subject_digest_secret.isascii()
        or subject_digest_secret != subject_digest_secret.strip()
        or any(character.isspace() or not character.isprintable() for character in subject_digest_secret)
    ):
        raise PersonalCommercePersistenceError(
            "subject digest secret must be 32-256 ASCII characters"
        )
    digest = hmac.new(
        subject_digest_secret.encode("utf-8"),
        subject_ref.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return "sha256:" + digest


def _naive_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise PersonalCommercePersistenceError("timestamp must include a timezone")
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def _subject_digest(
    request: PersonalCommerceRequest,
    subject_ref: str | None,
    subject_digest_secret: str | None,
) -> str | None:
    if request.personalization_consent:
        if not subject_ref or len(subject_ref) > 256:
            raise PersonalCommercePersistenceError("consented decision requires a bounded subject ref")
        return _subject_hmac(subject_ref, subject_digest_secret)
    if subject_ref is not None or subject_digest_secret is not None:
        raise PersonalCommercePersistenceError(
            "non-consented decision cannot carry subject material"
        )
    return None


def _retention_expiry(
    request: PersonalCommerceRequest,
    evaluated_at: datetime,
    retention_expires_at: datetime | None,
) -> datetime | None:
    if request.personalization_consent:
        if retention_expires_at is None:
            raise PersonalCommercePersistenceError(
                "consented decision requires a retention expiry"
            )
        expiry = _naive_utc(retention_expires_at)
        if expiry <= evaluated_at:
            raise PersonalCommercePersistenceError(
                "retention expiry must be after evaluation"
            )
        return expiry
    if retention_expires_at is not None:
        raise PersonalCommercePersistenceError(
            "non-consented decision cannot define personal retention"
        )
    return None


async def persist_personal_commerce(
    session,
    *,
    buy_wait_run: BuyWaitDecisionRun,
    request: PersonalCommerceRequest,
    decision: PersonalCommerceResult,
    evaluated_at: datetime,
    subject_ref: str | None = None,
    subject_digest_secret: str | None = None,
    retention_expires_at: datetime | None = None,
    apply: bool = False,
) -> PersistenceReport:
    if buy_wait_run.id is None:
        raise PersonalCommercePersistenceError("buy-wait run must be persisted")
    if decision.raw_context_retained or decision.utility_score is not None:
        raise PersonalCommercePersistenceError("raw context and uncalibrated scores are forbidden")
    if decision.measurement_status != "not_calibrated":
        raise PersonalCommercePersistenceError("unknown measurement status")
    expected_objective_digest = "sha256:" + _digest(asdict(request))
    if decision.objective_digest != expected_objective_digest:
        raise PersonalCommercePersistenceError("decision does not match the request")
    if not request.personalization_consent and (
        decision.outcome != "ABSTAINED"
        or decision.action != "ABSTAIN"
        or "personalization_consent_missing" not in decision.reason_codes
    ):
        raise PersonalCommercePersistenceError("missing consent must remain an abstention")
    if (
        (decision.action == "BUY" and buy_wait_run.outcome != "BUY_NOW")
        or (decision.action == "WAIT" and buy_wait_run.outcome != "WAIT")
    ):
        raise PersonalCommercePersistenceError("purchase action diverges from buy-wait evidence")
    evaluated = _naive_utc(evaluated_at)
    subject_digest = _subject_digest(request, subject_ref, subject_digest_secret)
    retention_expiry = _retention_expiry(request, evaluated, retention_expires_at)
    payload = {
        "buy_wait_run_key": buy_wait_run.run_key,
        "evaluated_at": evaluated.isoformat() + "Z",
        "subject_digest": subject_digest,
        "retention_expires_at": (
            retention_expiry.isoformat() + "Z" if retention_expiry is not None else None
        ),
        "decision": asdict(decision),
    }
    run_key = _digest(payload)
    created = existing_count = 0
    if apply:
        existing = await session.scalar(
            select(PersonalCommerceDecisionRun).where(PersonalCommerceDecisionRun.run_key == run_key)
        )
        if existing is not None:
            if (
                existing.result_digest != decision.result_digest
                or existing.outcome != decision.outcome
                or existing.action != decision.action
            ):
                raise PersonalCommercePersistenceError("personal commerce replay divergence")
            existing_count = 1
        else:
            session.add(PersonalCommerceDecisionRun(
                run_key=run_key,
                buy_wait_run_id=buy_wait_run.id,
                subject_digest=subject_digest,
                personalization_consent=request.personalization_consent,
                retention_expires_at=retention_expiry,
                objective_digest=decision.objective_digest,
                raw_context_retained=False,
                policy_version=decision.policy_version,
                outcome=decision.outcome,
                action=decision.action,
                selected_solution_ref=decision.selected_solution_ref,
                selected_solution_kind=decision.selected_solution_kind,
                matched_preference_count=len(decision.matched_preference_ids),
                eligible_count=decision.eligible_count,
                rejected_count=decision.rejected_count,
                measurement_status=decision.measurement_status,
                reason_codes_json=list(decision.reason_codes),
                result_digest=decision.result_digest,
                evaluated_at=evaluated,
            ))
            await session.flush()
            await session.commit()
            created = 1
    return PersistenceReport(
        "personal-commerce-persistence-report/v1",
        PERSISTENCE_VERSION,
        "apply" if apply else "dry_run",
        run_key,
        decision.outcome,
        decision.action,
        created,
        existing_count,
        decision.result_digest,
        "sha256:" + _digest({"run_key": run_key, "result_digest": decision.result_digest}),
    )


async def export_personal_commerce(
    session,
    *,
    subject_ref: str,
    subject_digest_secret: str,
    exported_at: datetime,
) -> PersonalCommerceExport:
    if not subject_ref or len(subject_ref) > 256:
        raise PersonalCommercePersistenceError("subject ref is required and bounded")
    subject_digest = _subject_hmac(subject_ref, subject_digest_secret)
    exported = _naive_utc(exported_at)
    rows = (
        (
            await session.execute(
                select(PersonalCommerceDecisionRun)
                .where(PersonalCommerceDecisionRun.subject_digest == subject_digest)
                .order_by(PersonalCommerceDecisionRun.evaluated_at, PersonalCommerceDecisionRun.id)
            )
        ).scalars().all()
    )
    records = tuple(
        PersonalCommerceExportRecord(
            decision_ref="sha256:" + _digest({
                "run_key": row.run_key,
                "result_digest": row.result_digest,
            }),
            evaluated_at=row.evaluated_at.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
            outcome=row.outcome,
            action=row.action,
            selected_solution_ref=row.selected_solution_ref,
            selected_solution_kind=row.selected_solution_kind,
            matched_preference_count=row.matched_preference_count,
            reason_codes=tuple(row.reason_codes_json),
            retention_expires_at=(
                row.retention_expires_at.replace(tzinfo=timezone.utc)
                .isoformat()
                .replace("+00:00", "Z")
            ),
        )
        for row in rows
    )
    return PersonalCommerceExport(
        "personal-commerce-portable-export/v1",
        exported.isoformat() + "Z",
        "server_shadow",
        False,
        len(records),
        records,
    )


async def erase_personal_commerce(
    session,
    *,
    subject_ref: str,
    erasure_request_ref: str,
    erased_at: datetime,
    subject_digest_secret: str,
    apply: bool = False,
) -> ErasureReport:
    if not subject_ref or len(subject_ref) > 256:
        raise PersonalCommercePersistenceError("subject ref is required and bounded")
    if not erasure_request_ref or len(erasure_request_ref) > 256:
        raise PersonalCommercePersistenceError("erasure request ref is required and bounded")
    subject_digest = _subject_hmac(subject_ref, subject_digest_secret)
    request_key = _digest({
        "subject_digest": subject_digest,
        "erasure_request_ref": erasure_request_ref,
    })
    existing_receipt = await session.scalar(
        select(PersonalCommerceErasureReceipt).where(
            PersonalCommerceErasureReceipt.request_key == request_key
        )
    )
    matched = int(await session.scalar(
        select(func.count()).select_from(PersonalCommerceDecisionRun).where(
            PersonalCommerceDecisionRun.subject_digest == subject_digest
        )
    ) or 0)
    if existing_receipt is not None:
        if matched != 0 or not existing_receipt.verified_empty:
            raise PersonalCommercePersistenceError("erasure replay is not empty")
        return ErasureReport(
            "personal-commerce-erasure-report/v1", "apply", request_key,
            0, existing_receipt.erased_records, 0, 1, True,
        )
    if not apply:
        return ErasureReport(
            "personal-commerce-erasure-report/v1", "dry_run", request_key,
            matched, 0, 0, 0, matched == 0,
        )
    await session.execute(
        delete(PersonalCommerceDecisionRun).where(
            PersonalCommerceDecisionRun.subject_digest == subject_digest
        )
    )
    await session.flush()
    remaining = int(await session.scalar(
        select(func.count()).select_from(PersonalCommerceDecisionRun).where(
            PersonalCommerceDecisionRun.subject_digest == subject_digest
        )
    ) or 0)
    if remaining != 0:
        await session.rollback()
        raise PersonalCommercePersistenceError("personal commerce erasure not verified")
    session.add(PersonalCommerceErasureReceipt(
        request_key=request_key,
        erased_records=matched,
        verified_empty=True,
        raw_context_retained=False,
        erased_at=_naive_utc(erased_at),
    ))
    await session.flush()
    await session.commit()
    return ErasureReport(
        "personal-commerce-erasure-report/v1", "apply", request_key,
        matched, matched, 1, 0, True,
    )


async def purge_expired_personal_commerce(
    session,
    *,
    as_of: datetime,
    apply: bool = False,
) -> RetentionPurgeReport:
    cutoff = _naive_utc(as_of)
    purge_key = _digest({
        "kind": "personal_commerce_retention",
        "as_of": cutoff.isoformat() + "Z",
    })
    existing_receipt = await session.scalar(
        select(PersonalCommerceErasureReceipt).where(
            PersonalCommerceErasureReceipt.request_key == purge_key
        )
    )
    predicate = (
        PersonalCommerceDecisionRun.retention_expires_at.is_not(None)
        & (PersonalCommerceDecisionRun.retention_expires_at <= cutoff)
    )
    matched = int(await session.scalar(
        select(func.count()).select_from(PersonalCommerceDecisionRun).where(predicate)
    ) or 0)
    if existing_receipt is not None:
        if matched != 0 or not existing_receipt.verified_empty:
            raise PersonalCommercePersistenceError("retention replay is not empty")
        return RetentionPurgeReport(
            "personal-commerce-retention-report/v1",
            "apply",
            purge_key,
            cutoff.isoformat() + "Z",
            0,
            existing_receipt.erased_records,
            0,
            1,
            True,
        )
    if not apply:
        return RetentionPurgeReport(
            "personal-commerce-retention-report/v1",
            "dry_run",
            purge_key,
            cutoff.isoformat() + "Z",
            matched,
            0,
            0,
            0,
            matched == 0,
        )
    await session.execute(delete(PersonalCommerceDecisionRun).where(predicate))
    await session.flush()
    remaining = int(await session.scalar(
        select(func.count()).select_from(PersonalCommerceDecisionRun).where(predicate)
    ) or 0)
    if remaining != 0:
        await session.rollback()
        raise PersonalCommercePersistenceError("retention purge not verified")
    session.add(PersonalCommerceErasureReceipt(
        request_key=purge_key,
        erased_records=matched,
        verified_empty=True,
        raw_context_retained=False,
        erased_at=cutoff,
    ))
    await session.flush()
    await session.commit()
    return RetentionPurgeReport(
        "personal-commerce-retention-report/v1",
        "apply",
        purge_key,
        cutoff.isoformat() + "Z",
        matched,
        matched,
        1,
        0,
        True,
    )
