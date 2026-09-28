"""The measurement that settled §10.0's open question has to stay honest.

Its conclusion — that the live score carries no cross-sectional information —
is only as good as the two corrections it makes: day-demeaning (so a rising
market is not mistaken for skill) and blocking by session (so 303 correlated
signals are not counted as 303 independent ones). Both are pinned here, along
with the degenerate inputs that would otherwise produce a confident number
from nothing.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from automation import signal_efficacy as se  # noqa: E402


def _line(day: str, band: list[dict], gate: int | None = 8) -> str:
    rec: dict = {"trading_day": day, "band": band}
    if gate is not None:
        rec["min_score"] = gate
    return json.dumps(rec, ensure_ascii=False)


def _entry(code: str, score: int, eligible: bool = True) -> dict:
    return {"code": code, "name": code, "score": score, "eligible": eligible}


# --- reading the journal ----------------------------------------------------


def test_a_name_counts_as_signalled_only_when_it_could_be_dispatched():
    """Eligible AND at the gate — that is the condition the watcher uses."""

    scan = se.collapse_journal([
        _line("2026-09-14", [
            _entry("AAA", 9),                      # eligible at the gate
            _entry("BBB", 9, eligible=False),      # scored but vetoed
            _entry("CCC", 7),                      # eligible, under the gate
        ]),
    ])

    day = scan["20260914"]
    assert day["AAA"]["signalled"] is True
    assert day["BBB"]["signalled"] is False
    assert day["CCC"]["signalled"] is False
    # All three were still scanned, so all three are available as controls.
    assert set(day) == {"AAA", "BBB", "CCC"}


def test_the_session_keeps_its_strongest_claim_and_any_dispatch():
    """The journal samples every 120s, so one name appears hundreds of times."""

    scan = se.collapse_journal([
        _line("2026-09-14", [_entry("AAA", 6, eligible=False)]),
        _line("2026-09-14", [_entry("AAA", 9)]),
        _line("2026-09-14", [_entry("AAA", 7, eligible=False)]),
    ])

    assert scan["20260914"]["AAA"] == {"score": 9, "signalled": True}


def test_a_gateless_record_falls_back_to_the_live_threshold():
    """The journal is append-only and predates some fields."""

    scan = se.collapse_journal([_line("2026-09-14", [_entry("AAA", 8)], gate=None)])
    assert scan["20260914"]["AAA"]["signalled"] is True


def test_unreadable_lines_are_skipped_rather_than_stopping_the_run():
    scan = se.collapse_journal([
        "not json",
        "",
        _line("2026-09-14", [_entry("AAA", 9)]),
        json.dumps({"trading_day": "nonsense", "band": [_entry("ZZZ", 9)]}),
        json.dumps({"trading_day": "2026-09-15", "band": [{"code": "BBB"}]}),
    ])

    assert set(scan) == {"20260914"}


# --- forward returns --------------------------------------------------------


CAL = ["20260914", "20260915", "20260916", "20260917", "20260918"]
CLOSES = {"AAA": {d: p for d, p in zip(CAL, [100, 110, 120, 130, 140])}}


def test_forward_return_counts_sessions_not_calendar_days():
    assert se.forward_return(CLOSES, CAL, "AAA", "20260914", 1) == 10.0
    assert se.forward_return(CLOSES, CAL, "AAA", "20260914", 2) == 20.0


def test_a_horizon_past_the_data_is_none_rather_than_padded():
    """Near the end of the journal there is no future yet. Reporting the last
    available close instead would quietly shorten the horizon."""

    assert se.forward_return(CLOSES, CAL, "AAA", "20260918", 1) is None
    assert se.forward_return(CLOSES, CAL, "AAA", "20260917", 5) is None
    assert se.forward_return(CLOSES, CAL, "MISSING", "20260914", 1) is None


# --- the two corrections ----------------------------------------------------


def test_a_rising_market_is_not_counted_as_skill():
    """Every name gains 10%; the signal picked one of them. Demeaning has to
    leave nothing, or the measure just reports the market."""

    closes = {c: {d: p for d, p in zip(CAL, [100, 110, 120, 130, 140])}
              for c in ("AAA", "BBB", "CCC", "DDD")}
    scan = se.collapse_journal([
        _line("2026-09-14", [
            _entry("AAA", 9),
            _entry("BBB", 5, eligible=False),
            _entry("CCC", 5, eligible=False),
            _entry("DDD", 5, eligible=False),
        ]),
    ])

    assert se.session_spreads(scan, closes, CAL, 1) == [0.0]
    assert se.score_rank_quality(scan, closes, CAL, 1)["correlation"] in (0.0, None)


def test_a_session_without_enough_control_names_is_dropped():
    """One signal and one other name is not a cross-section."""

    closes = {c: {d: p for d, p in zip(CAL, [100, 110, 120, 130, 140])}
              for c in ("AAA", "BBB")}
    scan = se.collapse_journal([
        _line("2026-09-14", [_entry("AAA", 9), _entry("BBB", 5, eligible=False)]),
    ])

    assert se.session_spreads(scan, closes, CAL, 1) == []


def test_the_bootstrap_resamples_sessions_so_a_thin_sample_stays_wide():
    """The trap this avoids: 303 signals from 26 correlated sessions read as
    303 independent draws, and the interval comes out several times too tight."""

    spreads = [-1.0, +2.0, -3.0, +1.0, -2.0, +0.5, -1.5, +2.5]
    out = se.bootstrap(spreads)

    assert out["sessions"] == 8
    assert out["ci_low"] < out["mean"] < out["ci_high"]
    # Eight noisy sessions cannot produce a confident sign.
    assert out["ci_low"] < 0 < out["ci_high"]
    # Deterministic, so a re-run reproduces the interval.
    assert se.bootstrap(spreads) == out


def test_too_few_sessions_report_nothing_instead_of_a_number():
    assert se.bootstrap([0.1, 0.2, 0.3]) is None


def test_a_signal_that_does_work_is_measured_as_positive():
    """The instrument has to be able to find an edge, or a negative result
    proves nothing about the strategy."""

    days = [f"202609{d:02d}" for d in range(1, 13)]
    winner = {d: 100.0 * (1.02 ** i) for i, d in enumerate(days)}
    flat = {d: 100.0 for d in days}
    closes = {"AAA": winner, "BBB": flat, "CCC": flat, "DDD": flat, "EEE": flat}
    scan = se.collapse_journal([
        _line(d, [_entry("AAA", 9)] + [
            _entry(c, 5, eligible=False) for c in ("BBB", "CCC", "DDD", "EEE")
        ])
        for d in days
    ])

    spreads = se.session_spreads(scan, closes, days, 1)
    assert spreads and all(s > 0 for s in spreads)
    assert se.bootstrap(spreads)["p_positive"] == 1.0
    assert se.score_rank_quality(scan, closes, days, 1)["correlation"] > 0.5


def test_the_report_counts_sessions_separately_from_signals():
    """Reporting only the signal count is what made two years of waiting look
    necessary — and what would overstate this measurement's precision."""

    closes = {c: {d: p for d, p in zip(CAL, [100, 110, 120, 130, 140])}
              for c in ("AAA", "BBB", "CCC", "DDD")}
    scan = se.collapse_journal([
        _line(f"2026-09-{d}", [
            _entry("AAA", 9), _entry("BBB", 9),
            _entry("CCC", 5, eligible=False), _entry("DDD", 5, eligible=False),
        ])
        for d in ("14", "15", "16")
    ])

    report = se.build_report(scan, closes, CAL, horizons=(1,))

    assert report["sessions"] == 3
    assert report["signals"] == 6
    assert report["scanned_pairs"] == 12
    assert "세션" in se.format_report(report)
