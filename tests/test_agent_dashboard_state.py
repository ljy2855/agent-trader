"""State the Agent tab needs to read the situation, not just the counters.

The tab was redesigned on 2026-09-24 after it showed cycle 0 and a dash in
every field on a holiday morning — indistinguishable from a dead watcher. Three
server-side pieces make the new view possible, and each is pinned here:

* a candidate board that says how far each name got and what stopped it,
* the previous process's snapshot, restored and labelled instead of zeros,
* the market session and next open, from the same calendar the watcher uses.
"""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.agent_overview import market_session_overview  # noqa: E402
from src.services import watcher as watcher_module  # noqa: E402
from src.services.candidate_journal import in_band  # noqa: E402
from src.services.krx_calendar import next_regular_session_open  # noqa: E402
from src.services.watcher_status import (  # noqa: E402
    WatcherStatusRegistry,
    summarize_candidates,
)
from tests.test_watcher import _build_watcher, _config  # noqa: E402

KST = ZoneInfo("Asia/Seoul")


def _row(code, score, *, eligible=True, dip=1.0, reasons=None, name=None):
    return {
        "stock_code": code,
        "stock_name": name or code,
        "score": score,
        "eligible": eligible,
        "ma_dip_pct": dip,
        "day_change_pct": -0.5,
        "reasons": reasons or [],
    }


# --- candidate board --------------------------------------------------------


def test_board_is_a_funnel_from_scanned_to_the_gate():
    rows = [
        _row("A", 9),                                    # qualifies
        _row("B", 7),                                    # eligible, under the gate
        _row("C", 9, eligible=False, reasons=["극단적 시장 약세 (진입 불가)"]),
        _row("D", 5, eligible=False, dip=-1.2, reasons=["이평 위 (저렴하지 않음)"]),
    ]
    board = summarize_candidates(
        rows, min_score=8, available_slots=0, at="t", in_band=in_band
    )

    assert board["scanned"] == 4
    assert board["in_band"] == 3        # D sits above the MA
    assert board["eligible"] == 2
    assert board["qualified"] == 1
    assert board["available_slots"] == 0


def test_qualifiers_lead_the_board_even_when_a_vetoed_name_scores_higher():
    """A 10 that cannot be bought is less interesting than the 8 that can."""

    rows = [_row("VETO", 10, eligible=False, reasons=["x"]), _row("OK", 8)]
    board = summarize_candidates(rows, min_score=8, available_slots=1, at=None)

    assert [r["stock_code"] for r in board["top"]] == ["OK", "VETO"]
    assert board["top"][0]["qualified"] is True


def test_only_the_deciding_reason_is_kept():
    rows = [_row("C", 6, eligible=False, reasons=["시총 미달 (대형주 아님)", "스프레드"])]
    board = summarize_candidates(rows, min_score=8, available_slots=1, at=None)

    assert board["top"][0]["blocked_by"] == "시총 미달 (대형주 아님)"


def test_board_is_capped_and_survives_junk_rows():
    rows = [_row(str(i), i % 10) for i in range(30)] + ["junk", None]
    board = summarize_candidates(rows, min_score=8, available_slots=1, at=None, limit=5)

    assert board["scanned"] == 30
    assert len(board["top"]) == 5


def test_without_a_band_predicate_the_count_is_unknown_not_zero():
    """Zero would claim no name was in the dip band."""

    board = summarize_candidates([_row("A", 9)], min_score=8, available_slots=1, at=None)
    assert board["in_band"] is None


# --- registry ---------------------------------------------------------------


def test_board_and_last_session_are_absent_until_published():
    snap = WatcherStatusRegistry().snapshot()
    assert snap["candidates"] is None
    assert snap["last_session"] is None


def test_board_and_last_session_are_published():
    reg = WatcherStatusRegistry()
    reg.set_candidates({"scanned": 30})
    reg.set_last_session({"last_tick_at": "2026-09-23T15:29:55+09:00"})

    snap = reg.snapshot()
    assert snap["candidates"] == {"scanned": 30}
    assert snap["last_session"]["last_tick_at"].startswith("2026-09-23")


# --- the watcher publishes, persists and restores ---------------------------


def _plan_with_candidates(*args, **kwargs):
    async def _():
        return {
            "success": True,
            "holdings": [],
            "regime": {"regime": "risk_off"},
            "candidate_rows": [_row("000270", 9, name="기아"), _row("005930", 5)],
            "portfolio": {"open_order_count": 0},
        }
    return _()


def test_a_tick_publishes_the_board(monkeypatch):
    w = _build_watcher(config=_config(new_candidate_min_score=8))
    monkeypatch.setattr(watcher_module, "plan_intraday_momentum_strategy", _plan_with_candidates)

    async def run():
        await w._tick()
        await w._cancel_in_flight()

    asyncio.run(run())

    board = w.status.snapshot()["candidates"]
    assert board["qualified"] == 1
    assert board["top"][0]["stock_name"] == "기아"
    assert board["at"] is not None


def test_the_persisted_snapshot_carries_the_session_the_dashboard_shows(tmp_path, monkeypatch):
    w = _build_watcher(config=_config(new_candidate_min_score=8))
    w._state_path = tmp_path / "watcher_state.json"
    monkeypatch.setattr(watcher_module, "plan_intraday_momentum_strategy", _plan_with_candidates)

    async def run():
        await w._tick()
        await w._cancel_in_flight()

    asyncio.run(run())
    w._persist_state()

    saved = json.loads(w._state_path.read_text())
    assert saved["candidates"]["qualified"] == 1
    assert saved["candidate_slots"]["qualified_ticks"] == 1
    assert saved["portfolio"]["candidate_count"] == 2

    # A new process reads it back as the last session.
    fresh = _build_watcher()
    fresh._state_path = w._state_path
    restored = fresh._load_previous_state()
    assert restored["candidates"]["top"][0]["stock_code"] == "000270"
    assert restored["last_tick_at"] == saved["last_tick_at"]


def test_no_usable_previous_snapshot_means_no_last_session(tmp_path):
    w = _build_watcher()

    w._state_path = tmp_path / "missing.json"
    assert w._load_previous_state() is None

    w._state_path = tmp_path / "corrupt.json"
    w._state_path.write_text("{not json")
    assert w._load_previous_state() is None

    # A process that stopped before its first tick has nothing to show.
    w._state_path = tmp_path / "never_ticked.json"
    w._state_path.write_text(json.dumps({"cycle_count": 0, "last_tick_at": None}))
    assert w._load_previous_state() is None


# --- market session -----------------------------------------------------------


def _at(text: str) -> datetime:
    return datetime.fromisoformat(text).replace(tzinfo=KST)


def test_a_holiday_names_itself_and_points_at_the_next_open():
    """The morning this was built: Chuseok, next open Monday."""

    s = market_session_overview(_at("2026-09-24 13:00"))
    assert s["phase"] == "holiday"
    assert s["reason"] == "추석 연휴"
    assert s["next_open"].startswith("2026-09-28T09:00")
    assert s["is_open"] is False


def test_session_phases_through_a_trading_day():
    assert market_session_overview(_at("2026-09-28 08:30"))["phase"] == "pre_open"
    assert market_session_overview(_at("2026-09-28 10:00"))["phase"] == "open"
    assert market_session_overview(_at("2026-09-28 16:00"))["phase"] == "after_close"
    assert market_session_overview(_at("2026-09-26 10:00"))["reason"] == "주말"


def test_next_open_skips_to_tomorrow_once_today_has_opened():
    opens, uncertain = next_regular_session_open(_at("2026-09-28 10:00"))
    assert opens == _at("2026-09-29 09:00")
    assert uncertain is False


def test_an_unverified_special_session_is_returned_but_flagged():
    """Skipping it would name a later day as "next open" on a day the market
    may well trade (2026-11-19, the CSAT)."""

    opens, uncertain = next_regular_session_open(_at("2026-11-18 16:00"))
    assert opens.date().isoformat() == "2026-11-19"
    assert uncertain is True


def test_past_the_supported_calendar_there_is_no_next_open():
    """2027 is not verified; inventing a date would be worse than none."""

    assert next_regular_session_open(_at("2026-12-31 16:00")) is None
    assert market_session_overview(_at("2026-12-31 16:00"))["next_open"] is None
