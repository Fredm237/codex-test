from __future__ import annotations

from types import SimpleNamespace

from quality_lab.v2_dark_reader import MIN_REAL_WINDOWS, evaluate_dark_reader_gate


def _observation(**overrides):
    values = {
        "chain_complete": True,
        "safety_state": "ABSTAIN",
        "raw_query_retained": False,
        "top1_state": "MATCH",
        "overlap_ppm": 1_000_000,
        "terminal_outcome": "ABSTAIN",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_dark_reader_gate_requires_thirty_real_complete_windows() -> None:
    hold = evaluate_dark_reader_gate(
        _observation() for _ in range(MIN_REAL_WINDOWS - 1)
    )
    ready = evaluate_dark_reader_gate(
        _observation() for _ in range(MIN_REAL_WINDOWS)
    )

    assert hold.status == "DARK_READER_HOLD"
    assert "INSUFFICIENT_REAL_DARK_WINDOWS" in hold.limitations
    assert ready.status == "DARK_READER_QUALIFIED"
    assert ready.observations == 30
    assert ready.top1_matches == 30
    assert ready.mean_overlap_ppm == 1_000_000


def test_dark_reader_gate_fails_closed_on_integrity_or_privacy() -> None:
    rows = [_observation() for _ in range(MIN_REAL_WINDOWS)]
    rows[0] = _observation(
        chain_complete=False,
        safety_state="INVALID",
        raw_query_retained=True,
        top1_state="UNKNOWN",
        terminal_outcome="INCOMPLETE",
    )

    report = evaluate_dark_reader_gate(rows)

    assert report.status == "DARK_READER_HOLD"
    assert report.gates == {
        "minimum_real_windows": True,
        "all_chains_complete": False,
        "zero_invalid": False,
        "zero_raw_query_retention": False,
    }
    assert "INCOMPLETE_V2_CHAIN_OBSERVATION" in report.limitations
    assert "INVALID_DARK_OBSERVATION" in report.limitations
    assert "RAW_QUERY_RETENTION_VIOLATION" in report.limitations


def test_core_agreement_is_reported_but_not_treated_as_ground_truth() -> None:
    rows = [
        _observation(top1_state="MISMATCH", overlap_ppm=250_000)
        for _ in range(MIN_REAL_WINDOWS)
    ]

    report = evaluate_dark_reader_gate(rows)

    assert report.status == "DARK_READER_QUALIFIED"
    assert report.comparable_top1 == 30
    assert report.top1_matches == 0
    assert report.mean_overlap_ppm == 250_000
    assert report.limitations == (
        "NO_EXTERNAL_HUMAN_GROUND_TRUTH / NON_BLOCKING",
    )
