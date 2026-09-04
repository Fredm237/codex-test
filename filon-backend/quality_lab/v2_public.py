"""Gate autoritaire CANARY vers PUBLIC pour la chaîne V2 atomique."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass


RESPONSE_TYPES = frozenset({"ABSTAIN", "BUY_NOW", "WAIT"})


@dataclass(frozen=True)
class V2PublicEvidence:
    shadow_gate_authorized: bool
    readiness_and_5xx_green: bool
    minimum_paired_observations: int
    minimum_observations_per_response_type: int
    paired_observations: int
    p95_latency_delta_us: int | None
    v2_fallbacks: int
    v2_reader_errors: int
    invalid_or_incomplete: int
    raw_query_retained: int
    v2_served: int
    provenance_complete: int
    requested_response_types: tuple[str, ...]
    served_response_types: tuple[str, ...]
    served_response_type_counts: dict[str, int]
    failure_injection_green: bool
    rollback_to_shadow_green: bool
    backup_restore_green: bool
    capacity_and_alerting_green: bool
    inherited_regressions_green: bool
    no_integrity_recovery_security_blocker: bool


@dataclass(frozen=True)
class V2PublicGateReport:
    schema_version: str
    status: str
    gates: dict[str, bool]
    authorized_response_types: tuple[str, ...]
    blocked_response_types: tuple[str, ...]
    blocker_codes: tuple[str, ...]
    evaluation_id: str

    def to_dict(self) -> dict[str, object]:
        return json.loads(_canonical(asdict(self)))


def _canonical(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _validate(evidence: V2PublicEvidence) -> None:
    integers = (
        evidence.minimum_paired_observations,
        evidence.minimum_observations_per_response_type,
        evidence.paired_observations,
        evidence.v2_fallbacks,
        evidence.v2_reader_errors,
        evidence.invalid_or_incomplete,
        evidence.raw_query_retained,
        evidence.v2_served,
        evidence.provenance_complete,
    )
    if any(isinstance(value, bool) or not isinstance(value, int) for value in integers):
        raise ValueError("public evidence counts must be integers")
    if (
        evidence.minimum_paired_observations < 1
        or evidence.minimum_observations_per_response_type < 1
    ):
        raise ValueError("minimum observations must be positive")
    if any(value < 0 for value in integers[2:]):
        raise ValueError("public evidence counts must be non-negative")
    if evidence.p95_latency_delta_us is not None and (
        isinstance(evidence.p95_latency_delta_us, bool)
        or not isinstance(evidence.p95_latency_delta_us, int)
    ):
        raise ValueError("p95 latency delta must be an integer or null")
    requested = set(evidence.requested_response_types)
    served = set(evidence.served_response_types)
    if (
        not requested
        or len(requested) != len(evidence.requested_response_types)
        or not requested <= RESPONSE_TYPES
    ):
        raise ValueError("requested response types are invalid")
    if (
        len(served) != len(evidence.served_response_types)
        or not served <= RESPONSE_TYPES
    ):
        raise ValueError("served response types are invalid")
    counts = evidence.served_response_type_counts
    if set(counts) != served or any(
        isinstance(value, bool) or not isinstance(value, int) or value < 0
        for value in counts.values()
    ):
        raise ValueError("served response type counts are invalid")


def evaluate_canary_to_public(evidence: V2PublicEvidence) -> V2PublicGateReport:
    """Autorise uniquement les types demandés dont toutes les preuves sont vertes."""

    _validate(evidence)
    requested = set(evidence.requested_response_types)
    served = set(evidence.served_response_types)
    gates = {
        "shadow_gate": evidence.shadow_gate_authorized,
        "runtime_health": (
            evidence.readiness_and_5xx_green and evidence.v2_reader_errors == 0
        ),
        "safety_invariants": (
            evidence.invalid_or_incomplete == 0
            and evidence.raw_query_retained == 0
        ),
        "paired_sample": (
            evidence.paired_observations >= evidence.minimum_paired_observations
        ),
        "latency_non_inferiority": (
            evidence.p95_latency_delta_us is not None
            and evidence.p95_latency_delta_us <= 0
        ),
        "error_non_inferiority": evidence.v2_fallbacks == 0,
        "provenance": (
            evidence.v2_served > 0
            and evidence.provenance_complete == evidence.v2_served
        ),
        "response_type_coverage": (
            requested == served
            and all(
                evidence.served_response_type_counts[value]
                >= evidence.minimum_observations_per_response_type
                for value in requested
            )
        ),
        "failure_injection": evidence.failure_injection_green,
        "rollback_to_shadow": evidence.rollback_to_shadow_green,
        "operations": (
            evidence.backup_restore_green and evidence.capacity_and_alerting_green
        ),
        "regressions_and_blockers": (
            evidence.inherited_regressions_green
            and evidence.no_integrity_recovery_security_blocker
        ),
    }
    status = "PUBLIC_AUTHORIZED" if all(gates.values()) else "PUBLIC_HOLD"
    authorized = tuple(sorted(requested)) if status == "PUBLIC_AUTHORIZED" else ()
    blocked = tuple(sorted(RESPONSE_TYPES - set(authorized)))
    blockers = [name.upper() for name, passed in gates.items() if not passed]
    blockers.extend(f"RESPONSE_TYPE_OFF:{value}" for value in blocked)
    payload = {
        "evidence": asdict(evidence),
        "gates": gates,
        "authorized_response_types": authorized,
        "blocked_response_types": blocked,
    }
    return V2PublicGateReport(
        schema_version="v2-canary-to-public-gate/v1",
        status=status,
        gates=gates,
        authorized_response_types=authorized,
        blocked_response_types=blocked,
        blocker_codes=tuple(blockers),
        evaluation_id=_digest(payload),
    )
