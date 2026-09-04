from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import models as core_models  # noqa: F401
from app.db.base import Base
from app.v2_chain.models import V2PromotionProof
from app.v2_chain.proof_registry import (
    V2PromotionProofError,
    record_promotion_proof,
    verify_registered_proofs,
)


SCOPE = "sha256:" + "a" * 64
ARTIFACT = "sha256:" + "b" * 64
VERIFIED_AT = datetime(2026, 9, 4, 12, tzinfo=timezone.utc)
KIND = "single_alembic_head_ref"


async def _database():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    return engine, async_sessionmaker(engine, expire_on_commit=False)


async def _record(session, **overrides):
    values = {
        "scope_ref": SCOPE,
        "proof_kind": KIND,
        "artifact_ref": "test:alembic/single-head",
        "artifact_digest": ARTIFACT,
        "verifier_version": "pytest-v1",
        "verification_status": "VERIFIED",
        "verified_at": VERIFIED_AT,
        "apply": True,
    }
    values.update(overrides)
    return await record_promotion_proof(session, **values)


@pytest.mark.asyncio
async def test_proof_registry_is_dry_run_append_only_and_idempotent() -> None:
    engine, sessions = await _database()
    try:
        async with sessions() as session:
            dry = await _record(session, apply=False)
            assert dry.status == "dry_run"
            assert await session.scalar(
                select(func.count()).select_from(V2PromotionProof)
            ) == 0

            created = await _record(session)
            replay = await _record(session)
            await session.commit()

            assert created.status == "created"
            assert replay.status == "existing"
            assert replay.proof_id == created.proof_id
            assert replay.proof_ref == created.proof_ref
            row = await session.scalar(
                select(V2PromotionProof).where(
                    V2PromotionProof.proof_ref == created.proof_ref
                )
            )
            assert row is not None
            assert row.raw_payload_retained is False
            assert not hasattr(row, "artifact_payload")
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_only_verified_proof_for_exact_scope_and_kind_resolves() -> None:
    engine, sessions = await _database()
    try:
        async with sessions() as session:
            verified = await _record(session)
            rejected = await _record(
                session,
                proof_kind="postgresql_migration_ref",
                artifact_ref="test:postgresql/migration",
                artifact_digest="sha256:" + "c" * 64,
                verification_status="REJECTED",
            )
            await session.commit()

            resolved = await verify_registered_proofs(
                session,
                scope_ref=SCOPE,
                proof_refs={KIND: verified.proof_ref},
                expected_keys=frozenset({KIND}),
            )
            wrong_scope = await verify_registered_proofs(
                session,
                scope_ref="sha256:" + "d" * 64,
                proof_refs={KIND: verified.proof_ref},
                expected_keys=frozenset({KIND}),
            )
            rejected_result = await verify_registered_proofs(
                session,
                scope_ref=SCOPE,
                proof_refs={"postgresql_migration_ref": rejected.proof_ref},
                expected_keys=frozenset({"postgresql_migration_ref"}),
            )

            assert resolved == {KIND: True}
            assert wrong_scope == {KIND: False}
            assert rejected_result == {"postgresql_migration_ref": False}
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_registry_rejects_unsafe_locator_and_unverifiable_digest() -> None:
    engine, sessions = await _database()
    try:
        async with sessions() as session:
            with pytest.raises(V2PromotionProofError, match="safe locator"):
                await _record(session, artifact_ref="https://user:secret@example.test")
            with pytest.raises(V2PromotionProofError, match="artifact_digest"):
                await _record(session, artifact_digest="green")
            with pytest.raises(V2PromotionProofError, match="unsupported"):
                await _record(session, proof_kind="invented_gate_ref")
    finally:
        await engine.dispose()
