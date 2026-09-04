"""Gate autoritaire SHADOW vers CANARY pour la chaîne V2 atomique."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any


REQUIRED_RESPONSE_TYPES = frozenset({"BUY_NOW", "WAIT", "ABSTAIN"})


@dataclass(frozen=True)
class V2CanaryEvidence:
    single_alembic_head: bool
    postgresql_migration_green: bool
    expand_only_rollback_green: bool
    replay_idempotent: bool
    cursor_monotone: bool
    single_execution_proven: bool
    inherited_benchmarks_green: bool
    safety_invariants_green: bool
    real_terminal_windows: int
    performance_distribution_ready: bool
    collision_exercise_green: bool
    stale_interruption_green: bool
    recovery_replay_green: bool
    dark_reader_qualified: bool
    dark_reader_rollback_green: bool
    observed_response_types: tuple[str, ...]


@dataclass(frozen=True)
class V2CanaryGateReport:
    schema_version: str
    status: str
    gates: dict[str, bool]
    blocked_response_types: tuple[str, ...]
    blocker_codes: tuple[str, ...]
    evaluation_id: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _digest(value: object) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def evaluate_shadow_to_canary(evidence: V2CanaryEvidence) -> V2CanaryGateReport:
    if (
        isinstance(evidence.real_terminal_windows, bool)
        or not isinstance(evidence.real_terminal_windows, int)
        or evidence.real_terminal_windows < 0
    ):
        raise ValueError("real_terminal_windows must be a non-negative integer")
    observed = set(evidence.observed_response_types)
    if any(value not in REQUIRED_RESPONSE_TYPES for value in observed):
        raise ValueError("observed response type is unsupported")
    if len(observed) != len(evidence.observed_response_types):
        raise ValueError("observed response types must be unique")

    blocked_types = tuple(sorted(REQUIRED_RESPONSE_TYPES - observed))
    gates = {
        "migration_and_rollback": (
            evidence.single_alembic_head
            and evidence.postgresql_migration_green
            and evidence.expand_only_rollback_green
        ),
        "idempotent_chain_replay": evidence.replay_idempotent,
        "monotone_single_execution": (
            evidence.cursor_monotone and evidence.single_execution_proven
        ),
        "inherited_benchmarks": evidence.inherited_benchmarks_green,
        "safety_invariants": evidence.safety_invariants_green,
        "thirty_terminal_windows": evidence.real_terminal_windows >= 30,
        "performance_distribution": evidence.performance_distribution_ready,
        "recovery_exercises": (
            evidence.collision_exercise_green
            and evidence.stale_interruption_green
            and evidence.recovery_replay_green
        ),
        "dark_reader": evidence.dark_reader_qualified,
        "dark_reader_rollback": evidence.dark_reader_rollback_green,
    }
    blockers = [name.upper() for name, passed in gates.items() if not passed]
    # Un type non observé ne bloque pas les autres types : il reste
    # explicitement OFF dans la cohorte canary.
    blockers.extend(f"RESPONSE_TYPE_OFF:{value}" for value in blocked_types)
    payload = {
        "evidence": asdict(evidence),
        "gates": gates,
        "blocked_response_types": blocked_types,
    }
    return V2CanaryGateReport(
        schema_version="v2-shadow-to-canary-gate/v1",
        status=(
            "CANARY_AUTHORIZED"
            if all(gates.values()) and bool(observed)
            else "CANARY_HOLD"
        ),
        gates=gates,
        blocked_response_types=blocked_types,
        blocker_codes=tuple(blockers),
        evaluation_id=_digest(payload),
    )
