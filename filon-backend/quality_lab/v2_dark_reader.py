"""Gate mesurable du lecteur sombre V2, sans oracle humain inventé."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping


MIN_REAL_WINDOWS = 30


@dataclass(frozen=True)
class V2DarkReaderGateReport:
    schema_version: str
    status: str
    observations: int
    complete: int
    invalid: int
    raw_queries_retained: int
    safe: int
    abstained: int
    comparable_top1: int
    top1_matches: int
    mean_overlap_ppm: int | None
    terminal_outcomes: tuple[str, ...]
    gates: dict[str, bool]
    limitations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _value(item: object, name: str, default: Any = None) -> Any:
    if isinstance(item, Mapping):
        return item.get(name, default)
    return getattr(item, name, default)


def evaluate_dark_reader_gate(
    observations: Iterable[object],
) -> V2DarkReaderGateReport:
    """Agrège les seules preuves objectives disponibles en shadow.

    Le taux d'accord V2/Core est exposé, mais ne devient pas un seuil qualité
    arbitraire : Core v1 n'est pas une vérité terrain humaine. Les blocages
    autoritaires sont l'intégrité, la complétude et la confidentialité.
    """

    rows = tuple(observations)
    complete = sum(bool(_value(item, "chain_complete", False)) for item in rows)
    invalid = sum(_value(item, "safety_state") == "INVALID" for item in rows)
    raw_queries = sum(
        bool(_value(item, "raw_query_retained", False)) for item in rows
    )
    safe = sum(_value(item, "safety_state") == "SAFE" for item in rows)
    abstained = sum(_value(item, "safety_state") == "ABSTAIN" for item in rows)
    comparable = [
        item
        for item in rows
        if _value(item, "top1_state") in {"MATCH", "MISMATCH"}
    ]
    overlaps = [
        int(_value(item, "overlap_ppm"))
        for item in rows
        if isinstance(_value(item, "overlap_ppm"), int)
        and not isinstance(_value(item, "overlap_ppm"), bool)
    ]
    gates = {
        "minimum_real_windows": len(rows) >= MIN_REAL_WINDOWS,
        "all_chains_complete": complete == len(rows) and bool(rows),
        "zero_invalid": invalid == 0,
        "zero_raw_query_retention": raw_queries == 0,
    }
    limitations = ["NO_EXTERNAL_HUMAN_GROUND_TRUTH / NON_BLOCKING"]
    if not gates["minimum_real_windows"]:
        limitations.append("INSUFFICIENT_REAL_DARK_WINDOWS")
    if not gates["all_chains_complete"]:
        limitations.append("INCOMPLETE_V2_CHAIN_OBSERVATION")
    if invalid:
        limitations.append("INVALID_DARK_OBSERVATION")
    if raw_queries:
        limitations.append("RAW_QUERY_RETENTION_VIOLATION")
    return V2DarkReaderGateReport(
        schema_version="v2-dark-reader-gate-report/v1",
        status=(
            "DARK_READER_QUALIFIED"
            if all(gates.values())
            else "DARK_READER_HOLD"
        ),
        observations=len(rows),
        complete=complete,
        invalid=invalid,
        raw_queries_retained=raw_queries,
        safe=safe,
        abstained=abstained,
        comparable_top1=len(comparable),
        top1_matches=sum(
            _value(item, "top1_state") == "MATCH" for item in comparable
        ),
        mean_overlap_ppm=(
            round(sum(overlaps) / len(overlaps)) if overlaps else None
        ),
        terminal_outcomes=tuple(
            sorted(
                {
                    str(_value(item, "terminal_outcome"))
                    for item in rows
                    if _value(item, "terminal_outcome") is not None
                }
            )
        ),
        gates=gates,
        limitations=tuple(limitations),
    )
