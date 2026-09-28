"""Candidate score journal — band detection, sampling, and fault tolerance."""

import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from src.services.candidate_journal import (
    CandidateJournal,
    build_record,
    in_band,
)

KST = ZoneInfo("Asia/Seoul")
T0 = datetime(2026, 8, 19, 10, 0, tzinfo=KST)


def _row(code, score, dip, *, eligible=True, reasons=None):
    return {
        "stock_code": code,
        "stock_name": f"종목{code}",
        "score": score,
        "ma_dip_pct": dip,
        "eligible": eligible,
        "reasons": reasons or [],
    }


# --- band detection -------------------------------------------------------


def test_in_band_accepts_a_shallow_dip():
    assert in_band(_row("A", 8, 3.0))


def test_in_band_rejects_above_the_moving_average():
    """dip <= 0 means the price is at or above the MA — not cheap."""

    assert not in_band(_row("A", 8, 0.0))
    assert not in_band(_row("A", 8, -1.5))


def test_in_band_rejects_a_broken_trend():
    assert not in_band(_row("A", 8, 5.01))


def test_in_band_rejects_a_missing_dip():
    """Not enough daily bars to compute the MA."""

    assert not in_band(_row("A", 8, None))
    assert not in_band({"stock_code": "A", "score": 8})


def test_band_detection_ignores_reason_wording():
    """Keyed on the number, so rewording a Korean message cannot break it."""

    row = _row("A", 8, 2.0, eligible=False, reasons=["극단적 매도 우위 (투매)"])
    assert in_band(row)


# --- record shape ---------------------------------------------------------


def test_build_record_returns_none_when_nothing_is_in_band():
    assert build_record(
        now=T0, regime={}, candidate_rows=[_row("A", 9, -2.0)], min_score=8
    ) is None


def test_build_record_sorts_by_score_and_keeps_the_gate():
    rec = build_record(
        now=T0,
        regime={"regime": "risk_off", "extreme_risk_off": True},
        candidate_rows=[_row("A", 5, 1.0), _row("B", 9, 2.0), _row("C", 7, 3.0)],
        min_score=8,
    )
    assert [b["score"] for b in rec["band"]] == [9, 7, 5]
    assert rec["min_score"] == 8
    assert rec["regime"] == "risk_off"
    assert rec["extreme_risk_off"] is True
    assert rec["trading_day"] == "2026-08-19"
    assert rec["scanned"] == 3


def test_slot_count_is_recorded_so_blocked_opportunity_is_countable():
    """At zero slots the detector returns before building any event.

    The screener is never asked and nothing anywhere says why. Measured
    2026-08-19..09-18: 78.7% of snapshots held a gate-passing candidate,
    5 entries in 23 trading days, a position open 83% of the time. This
    field is what turns that from a hand-noticed coincidence into a number.
    """

    rec = build_record(
        now=T0,
        regime={},
        candidate_rows=[_row("A", 9, 2.0)],
        min_score=8,
        available_slots=0,
        holding_count=1,
    )
    assert rec["available_slots"] == 0
    assert rec["holding_count"] == 1
    # The candidate still gets recorded — it qualified, it just had nowhere
    # to go. That pairing is the whole point.
    assert rec["band"][0]["score"] == 9
    assert rec["band"][0]["eligible"] is True


def test_records_written_before_the_field_existed_still_parse():
    """`candidate_scores.jsonl` already holds 4,220 snapshots without it.

    Omitting the key rather than writing a null keeps the old and new rows
    the same shape to every reader that uses `.get`.
    """

    rec = build_record(
        now=T0, regime={}, candidate_rows=[_row("A", 9, 2.0)], min_score=8
    )
    assert "available_slots" not in rec
    assert "holding_count" not in rec


def test_build_record_reports_non_dip_blockers_only():
    """The dip already passed; what else stopped it is the useful part."""

    rec = build_record(
        now=T0,
        regime={},
        candidate_rows=[
            _row("A", 7, 2.0, eligible=False,
                 reasons=["극단적 매도 우위 (투매)", "이평 위 (저렴하지 않음)"])
        ],
        min_score=8,
    )
    assert rec["band"][0]["blocked_by"] == ["극단적 매도 우위 (투매)"]


# --- sampling / durability ------------------------------------------------


def test_journal_writes_then_rate_limits(tmp_path):
    path = tmp_path / "scores.jsonl"
    j = CandidateJournal(path, min_interval_seconds=120)
    rows = [_row("A", 7, 2.0)]

    assert j.record(now=T0, regime={}, candidate_rows=rows, min_score=8)
    assert j.record(
        now=T0 + timedelta(seconds=30), regime={}, candidate_rows=rows, min_score=8
    ) is None
    assert j.record(
        now=T0 + timedelta(seconds=120), regime={}, candidate_rows=rows, min_score=8
    )

    lines = path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["band"][0]["code"] == "A"


def test_empty_band_does_not_consume_the_sampling_slot(tmp_path):
    """A skipped write must not delay the next real sample."""

    j = CandidateJournal(tmp_path / "s.jsonl", min_interval_seconds=120)
    assert j.record(now=T0, regime={}, candidate_rows=[_row("A", 7, -1.0)],
                    min_score=8) is None
    assert j.record(now=T0, regime={}, candidate_rows=[_row("A", 7, 2.0)],
                    min_score=8) is not None


def test_disabled_journal_is_inert(tmp_path):
    j = CandidateJournal(None)
    assert not j.enabled
    assert j.record(now=T0, regime={}, candidate_rows=[_row("A", 7, 2.0)],
                    min_score=8) is None


def test_unwritable_path_is_swallowed(tmp_path):
    """Observability must never take a trading tick down."""

    blocker = tmp_path / "blocker"
    blocker.write_text("not a directory")
    j = CandidateJournal(blocker / "scores.jsonl")
    assert j.record(now=T0, regime={}, candidate_rows=[_row("A", 7, 2.0)],
                    min_score=8) is None
