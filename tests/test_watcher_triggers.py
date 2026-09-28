"""Unit tests for the pure watcher trigger-detection functions."""

from __future__ import annotations

import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

os.environ.setdefault("KIWOOM_APPKEY", "dummy-appkey")
os.environ.setdefault("KIWOOM_SECRETKEY", "dummy-secretkey")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.services.watcher_triggers import (  # noqa: E402
    ROLE_EVALUATOR,
    ROLE_PM,
    ROLE_RISK,
    ROLE_SCREENER,
    ROLE_SELF,
    KST,
    detect_tier1_holding_rules,
    detect_tier1_position_overflow,
    detect_tier1_stale_orders,
    detect_tier2_extreme_risk_off,
    detect_tier2_global_health,
    detect_tier2_holding_swings,
    detect_tier2_new_candidates,
    detect_tier2_periodic_review,
    detect_tier2_regime_flip,
    detect_tier2_regime_label_flip,
)


def _now() -> datetime:
    return datetime(2026, 5, 3, 10, 0, 0, tzinfo=KST)


# -- Tier 1 ---------------------------------------------------------------


def test_stop_loss_fires_at_or_below_threshold():
    holdings = [
        {"stock_code": "001", "stock_name": "A", "profit_rate": -3.0, "quantity": 10},
        {"stock_code": "002", "stock_name": "B", "profit_rate": -2.5, "quantity": 5},
    ]
    out = detect_tier1_holding_rules(
        holdings, stop_loss_pct=-3.0, hard_take_profit_pct=8.0, now=_now()
    )
    types = [(t.stock_code, t.trigger_type) for t in out]
    assert ("001", "stop_loss") in types
    # B is above -3% so no trigger
    assert all(c != "002" for c, _ in types)
    assert all(t.tier == 1 and t.target_role == ROLE_SELF for t in out)


def test_hard_take_profit_fires_at_or_above_threshold():
    holdings = [
        {"stock_code": "001", "profit_rate": 8.0, "quantity": 10},
        {"stock_code": "002", "profit_rate": 9.5, "quantity": 5},
        {"stock_code": "003", "profit_rate": 5.0, "quantity": 5},
    ]
    out = detect_tier1_holding_rules(
        holdings, stop_loss_pct=-3.0, hard_take_profit_pct=8.0, now=_now()
    )
    types = {t.stock_code: t.trigger_type for t in out}
    assert types == {"001": "hard_take_profit", "002": "hard_take_profit"}


def test_stop_loss_priority_over_take_profit_when_both_appear():
    holdings = [
        {"stock_code": "001", "profit_rate": -4.0, "quantity": 1},  # only stop_loss
    ]
    out = detect_tier1_holding_rules(
        holdings, stop_loss_pct=-3.0, hard_take_profit_pct=8.0, now=_now()
    )
    assert len(out) == 1
    assert out[0].trigger_type == "stop_loss"


def test_position_overflow_picks_weakest():
    holdings = [
        {"stock_code": "001", "profit_rate": 1.0, "quantity": 5},
        {"stock_code": "002", "profit_rate": -2.0, "quantity": 5},  # weakest
        {"stock_code": "003", "profit_rate": 5.0, "quantity": 5},
        {"stock_code": "004", "profit_rate": 0.5, "quantity": 5},
    ]
    out = detect_tier1_position_overflow(holdings, max_positions=3, now=_now())
    assert len(out) == 1
    assert out[0].stock_code == "002"
    assert out[0].suggested_action == "sell_market"


def test_position_overflow_no_trigger_when_under_cap():
    holdings = [{"stock_code": "001", "profit_rate": 1.0, "quantity": 5}]
    out = detect_tier1_position_overflow(holdings, max_positions=3, now=_now())
    assert out == []


def test_stale_orders_use_ord_tm_today():
    now = _now()
    # 6 minutes earlier
    six_min_earlier = (now - timedelta(minutes=6)).strftime("%H%M%S")
    open_orders = [
        {
            "ord_no": "12345",
            "stk_cd": "001",
            "stk_nm": "Stale",
            "ord_tm": six_min_earlier,
            "ord_qty": "10",
            "ord_uv": "1000",
        },
        # Recent — should not fire
        {
            "ord_no": "67890",
            "stk_cd": "002",
            "ord_tm": now.strftime("%H%M%S"),
        },
        # No timestamp — skipped
        {"ord_no": "00000", "stk_cd": "003"},
    ]
    out = detect_tier1_stale_orders(open_orders, stale_minutes=5, now=now)
    assert len(out) == 1
    assert out[0].stock_code == "001"
    assert out[0].suggested_action == "cancel_order"
    assert out[0].metadata["order_no"] == "12345"


def test_stale_orders_use_ord_tmd():
    now = _now()
    six_min_earlier = (now - timedelta(minutes=6)).strftime("%Y%m%d%H%M%S")
    open_orders = [
        {"ord_no": "abc", "stk_cd": "X", "ord_tmd": six_min_earlier, "ord_qty": "1"}
    ]
    out = detect_tier1_stale_orders(open_orders, stale_minutes=5, now=now)
    assert len(out) == 1
    assert out[0].metadata["order_no"] == "abc"


# -- Tier 2 per-stock -----------------------------------------------------


def test_holding_swing_fires_on_tick_delta():
    prev = {"001": {"current_price": 100.0}}
    holdings = [
        {"stock_code": "001", "stock_name": "A", "current_price": 103.0, "quantity": 1},
    ]
    out = detect_tier2_holding_swings(
        holdings,
        prev,
        swing_pct=2.0,
        high_drop_pct=1.5,
        now=_now(),
    )
    assert len(out) == 1
    assert out[0].trigger_type == "holding_swing"
    assert out[0].target_role == ROLE_EVALUATOR
    assert out[0].snapshot["delta_pct"] is not None


def test_holding_swing_fires_on_high_drop():
    prev = {"001": {"current_price": 100.0}}
    holdings = [
        {
            "stock_code": "001",
            "current_price": 100.0,
            "intraday_high": 103.0,  # -2.91% from high (>= 1.5%)
            "quantity": 1,
        }
    ]
    out = detect_tier2_holding_swings(
        holdings, prev, swing_pct=10.0, high_drop_pct=1.5, now=_now()
    )
    assert len(out) == 1
    assert "고점 이탈" in out[0].reason


def test_holding_swing_skips_when_no_prev_and_no_high():
    holdings = [{"stock_code": "001", "current_price": 100.0, "quantity": 1}]
    out = detect_tier2_holding_swings({}, {}, swing_pct=2.0, high_drop_pct=1.5, now=_now())
    assert out == []
    out = detect_tier2_holding_swings(holdings, {}, swing_pct=2.0, high_drop_pct=1.5, now=_now())
    assert out == []


def test_new_candidates_only_emits_unseen_eligible_above_threshold():
    rows = [
        {"stock_code": "A", "score": 16, "eligible": True, "stock_name": "A"},
        {"stock_code": "B", "score": 14, "eligible": True, "stock_name": "B"},
        {"stock_code": "C", "score": 18, "eligible": False, "stock_name": "C"},
        {"stock_code": "D", "score": 20, "eligible": True, "stock_name": "D"},
    ]
    out = detect_tier2_new_candidates(
        rows,
        prev_codes={"A"},
        min_score=15,
        available_slots=2,
        now=_now(),
    )
    codes = [t.stock_code for t in out]
    # A is in prev_codes → skipped. B too low score. C not eligible.
    # D passes. Only one slot used since A was skipped before slot count.
    assert codes == ["D"]
    assert out[0].target_role == ROLE_SCREENER


def test_new_candidates_respects_slot_budget():
    rows = [
        {"stock_code": "A", "score": 18, "eligible": True},
        {"stock_code": "B", "score": 17, "eligible": True},
        {"stock_code": "C", "score": 20, "eligible": True},
    ]
    out = detect_tier2_new_candidates(
        rows, prev_codes=set(), min_score=15, available_slots=2, now=_now()
    )
    # Sorted by -score → C (20), A (18). 2 slots only.
    assert [t.stock_code for t in out] == ["C", "A"]


def test_new_candidates_zero_slots_emits_nothing():
    rows = [{"stock_code": "A", "score": 50, "eligible": True}]
    out = detect_tier2_new_candidates(
        rows, prev_codes=set(), min_score=15, available_slots=0, now=_now()
    )
    assert out == []


def test_new_candidate_snapshot_carries_the_below_ma_thesis():
    """The screener is asked to judge a MA20 pullback; it needs the MA20.

    Until 2026-09-27 the snapshot dropped `ma_dip_pct` and carried
    momentum-era `breakout`/`high_price`, and the screener kept deferring
    score-8 names because "MA20 이격·거래량 배수가 트리거에 없다".
    """

    row = {
        "stock_code": "005930", "stock_name": "삼성전자", "score": 9, "eligible": True,
        "ma_dip_pct": 1.9, "ma_period": 20, "ma_value": 99_900,
        "volume_ratio_20d": 2.5, "upper_limit_distance_pct": 32.65,
        "market_cap_krw": 572_935_342_000_000, "day_change_pct": -2.0,
        "orderbook_ratio": 1.0, "spread_pct": 0.1, "current_price": 98_000,
        "high_price": 99_500, "breakout": False, "sources": ["roster"],
        "entry_order_type_code": "0", "entry_price": 97_900,
    }
    [event] = detect_tier2_new_candidates(
        [row], prev_codes=set(), min_score=8, available_slots=1, now=_now()
    )
    snap = event.snapshot

    for key in ("ma_dip_pct", "ma_period", "ma_value", "volume_ratio_20d",
                "upper_limit_distance_pct", "market_cap_krw"):
        assert snap[key] == row[key], key
    # Not only for the agent: the buy path rescores from this dict (sources
    # carry the source bonus) and prices the stale check off current_price.
    for key in ("score", "sources", "current_price", "entry_order_type_code", "entry_price"):
        assert snap[key] == row[key], key
    assert "breakout" not in snap
    assert "high_price" not in snap
    assert "MA20 1.90% 하회" in event.reason


def test_new_candidate_reason_without_a_moving_average_names_the_day_change():
    row = {"stock_code": "A", "score": 9, "eligible": True, "day_change_pct": 3.1}
    [event] = detect_tier2_new_candidates(
        [row], prev_codes=set(), min_score=8, available_slots=1, now=_now()
    )
    assert "day_change=3.1%" in event.reason


# -- Tier 2 global --------------------------------------------------------


def test_regime_flip_fires_on_label_change():
    out = detect_tier2_regime_flip(
        regime={"regime": "risk_off"},
        prev_regime={"regime": "risk_on"},
        now=_now(),
    )
    assert len(out) == 1
    assert out[0].trigger_type == "regime_flip"
    assert out[0].target_role == ROLE_PM


def test_regime_flip_no_fire_on_first_tick():
    out = detect_tier2_regime_flip(
        regime={"regime": "neutral"}, prev_regime=None, now=_now()
    )
    assert out == []


def test_extreme_risk_off_fires_on_transition():
    out = detect_tier2_regime_flip(
        regime={"regime": "risk_off", "extreme_risk_off": True},
        prev_regime={"regime": "risk_off", "extreme_risk_off": False},
        now=_now(),
    )
    types = [t.trigger_type for t in out]
    assert "extreme_risk_off" in types


def test_extreme_risk_off_no_fire_when_already_set():
    out = detect_tier2_regime_flip(
        regime={"regime": "risk_off", "extreme_risk_off": True},
        prev_regime={"regime": "risk_off", "extreme_risk_off": True},
        now=_now(),
    )
    types = [t.trigger_type for t in out]
    assert "extreme_risk_off" not in types


def test_label_flip_split_only_emits_label_change():
    out = detect_tier2_regime_label_flip(
        regime={"regime": "risk_off", "extreme_risk_off": True},
        prev_stable_regime={"regime": "risk_on"},
        now=_now(),
    )
    assert len(out) == 1
    assert out[0].trigger_type == "regime_flip"


def test_label_flip_split_skips_when_baseline_none():
    """The watcher passes None while debouncing; no fire allowed."""

    out = detect_tier2_regime_label_flip(
        regime={"regime": "risk_off"},
        prev_stable_regime=None,
        now=_now(),
    )
    assert out == []


def test_extreme_risk_off_split_fires_immediately():
    out = detect_tier2_extreme_risk_off(
        regime={"regime": "risk_off", "extreme_risk_off": True},
        prev_regime={"regime": "risk_off", "extreme_risk_off": False},
        now=_now(),
    )
    assert len(out) == 1
    assert out[0].trigger_type == "extreme_risk_off"


def test_extreme_risk_off_suppressed_when_market_data_incomplete():
    """A failed index read zeroes breadth, which reads as a crash.

    The 2026-07-29/30 DNS fault paged the PM squad twice this way. The flag
    is still True (new entries stay vetoed) — only the dispatch is skipped.
    """

    out = detect_tier2_extreme_risk_off(
        regime={
            "regime": "risk_off",
            "extreme_risk_off": True,
            "market_data_complete": False,
        },
        prev_regime={"regime": "risk_on", "extreme_risk_off": False},
        now=_now(),
    )
    assert out == []


def test_extreme_risk_off_fires_on_real_crash_after_degraded_tick():
    """A degraded tick must not become the baseline that eats a real crash."""

    out = detect_tier2_extreme_risk_off(
        regime={
            "regime": "risk_off",
            "extreme_risk_off": True,
            "market_data_complete": True,
        },
        prev_regime={
            "regime": "risk_off",
            "extreme_risk_off": True,
            "market_data_complete": False,
        },
        now=_now(),
    )
    assert len(out) == 1
    assert out[0].trigger_type == "extreme_risk_off"


def test_label_flip_suppressed_when_market_data_incomplete():
    out = detect_tier2_regime_label_flip(
        regime={"regime": "risk_off", "market_data_complete": False},
        prev_stable_regime={"regime": "risk_on"},
        now=_now(),
    )
    assert out == []


def test_regime_triggers_fire_when_flag_absent():
    """Regimes predating the flag (and test stubs) must keep firing."""

    assert (
        detect_tier2_extreme_risk_off(
            regime={"regime": "risk_off", "extreme_risk_off": True},
            prev_regime={"regime": "risk_on", "extreme_risk_off": False},
            now=_now(),
        )
        != []
    )
    assert (
        detect_tier2_regime_label_flip(
            regime={"regime": "risk_off"},
            prev_stable_regime={"regime": "risk_on"},
            now=_now(),
        )
        != []
    )


def test_global_health_fires_when_thresholds_hit():
    out = detect_tier2_global_health(
        api_failure_count=3,
        open_order_count=6,
        api_failure_threshold=3,
        unfilled_threshold=5,
        now=_now(),
    )
    types = [t.trigger_type for t in out]
    assert "api_failures" in types
    assert "unfilled_overflow" in types
    assert all(t.target_role == ROLE_RISK for t in out)


def test_global_health_no_fire_below_thresholds():
    out = detect_tier2_global_health(
        api_failure_count=2,
        open_order_count=4,
        api_failure_threshold=3,
        unfilled_threshold=5,
        now=_now(),
    )
    assert out == []


def test_periodic_review_fires_on_first_tick():
    out = detect_tier2_periodic_review(
        last_review_at=None, interval_minutes=30, now=_now()
    )
    assert len(out) == 1
    assert out[0].trigger_type == "periodic_review"


def test_periodic_review_suppressed_inside_interval():
    last = _now() - timedelta(minutes=10)
    out = detect_tier2_periodic_review(
        last_review_at=last, interval_minutes=30, now=_now()
    )
    assert out == []


def test_periodic_review_fires_after_interval():
    last = _now() - timedelta(minutes=31)
    out = detect_tier2_periodic_review(
        last_review_at=last, interval_minutes=30, now=_now()
    )
    assert len(out) == 1


# -- Cooldown / scope keys ------------------------------------------------


def test_scope_key_distinguishes_global_per_role():
    pm_event = detect_tier2_periodic_review(None, interval_minutes=30, now=_now())[0]
    risk_events = detect_tier2_global_health(
        api_failure_count=3,
        open_order_count=0,
        api_failure_threshold=3,
        unfilled_threshold=999,
        now=_now(),
    )
    assert pm_event.scope_key().startswith("global:")
    assert risk_events[0].scope_key().startswith("global:")
    assert pm_event.scope_key() != risk_events[0].scope_key()


# --- extreme_risk_off exit hysteresis ---------------------------------------
#
# 2026-09-02: primary_breadth sat at 0.19 against a 0.20 threshold and
# oscillated across it, arming the rising edge 8 times in one session (80 of
# 183 snapshots read extreme). Every firing paged the PM squad onto a
# day-scoped issue whose thread each later run re-read, which is what
# exhausted the codex quota for the day.


def _regime(*, extreme, sticky=None, complete=True):
    r = {
        "regime": "risk_off",
        "extreme_risk_off": extreme,
        "market_data_complete": complete,
    }
    if sticky is not None:
        r["extreme_risk_off_sticky"] = sticky
    return r


CRASH = _regime(extreme=True, sticky=True)
IN_BAND = _regime(extreme=False, sticky=True)   # cleared entry, not exit
RECOVERED = _regime(extreme=False, sticky=False)


def test_crash_from_calm_still_fires_immediately():
    """Hysteresis must not delay the signal on the way in."""

    assert len(detect_tier2_extreme_risk_off(CRASH, RECOVERED)) == 1


def test_wobble_back_over_the_line_does_not_re_fire():
    """The 09-02 loop: a metric hugging the threshold re-crossing it."""

    assert detect_tier2_extreme_risk_off(CRASH, IN_BAND) == []


def test_sitting_in_the_band_does_not_fire():
    assert detect_tier2_extreme_risk_off(IN_BAND, CRASH) == []


def test_edge_re_arms_once_the_market_clears_the_exit_band():
    """Suppression must not outlive the condition that justified it."""

    assert detect_tier2_extreme_risk_off(RECOVERED, CRASH) == []
    assert len(detect_tier2_extreme_risk_off(CRASH, RECOVERED)) == 1


def test_regimes_without_the_sticky_flag_behave_as_before():
    """Older state files and hand-built dicts must not change meaning."""

    old_crash = {"regime": "risk_off", "extreme_risk_off": True}
    old_calm = {"regime": "risk_off", "extreme_risk_off": False}

    assert len(detect_tier2_extreme_risk_off(old_crash, old_calm)) == 1
    assert detect_tier2_extreme_risk_off(old_crash, old_crash) == []


def test_a_degraded_prior_still_does_not_suppress_a_real_crash():
    """Unchanged: an outage sets both flags, but must not become baseline."""

    degraded = _regime(extreme=True, sticky=True, complete=False)

    assert len(detect_tier2_extreme_risk_off(CRASH, degraded)) == 1


# --- stale-order timestamps -------------------------------------------------
#
# This Tier-1 rule had never fired in production. ka10075 sends the order time
# as `tm`; the detector read only `ord_tm`/`ord_tmd`, so every real row failed
# to parse and was skipped in silence. The tests missed it because their
# fixtures used the names the parser looked for, not the ones the broker
# sends. On 2026-09-04 a limit buy rested from 15:22 while the loop ran to
# 15:29 -- past the 5-minute threshold -- and the exchange cancelled it at the
# close instead of us.


def test_ka10075_rows_are_read_the_way_the_broker_sends_them():
    """`tm` is the field name in the spec, and what production returns."""

    now = datetime(2026, 9, 4, 15, 29, 51, tzinfo=KST)
    row = {
        "ord_no": "419694",
        "stk_cd": "005930",
        "stk_nm": "삼성전자",
        "ord_qty": "1",
        "oso_qty": "1",
        "tm": "152232",
    }

    (event,) = detect_tier1_stale_orders([row], stale_minutes=5, now=now)

    assert event.suggested_action == "cancel_order"
    assert event.metadata["order_no"] == "419694"
    assert event.snapshot["age_minutes"] == pytest.approx(7.3, abs=0.1)


@pytest.mark.parametrize(
    "field", ["tm", "ord_tm", "cntr_tm"], ids=["ka10075", "ka10076", "execution"]
)
def test_every_time_field_the_queries_use_is_understood(field):
    now = datetime(2026, 9, 4, 15, 30, tzinfo=KST)

    out = detect_tier1_stale_orders(
        [{"ord_no": "1", "stk_cd": "X", field: "152000"}], stale_minutes=5, now=now
    )

    assert len(out) == 1


def test_a_fresh_order_is_still_left_alone():
    now = datetime(2026, 9, 4, 15, 25, tzinfo=KST)

    assert detect_tier1_stale_orders(
        [{"ord_no": "1", "stk_cd": "X", "tm": "152232"}], stale_minutes=5, now=now
    ) == []


def test_an_unreadable_time_is_skipped_but_logged(caplog):
    """Cancelling on a guessed age is worse -- but silence is how this hid."""

    now = datetime(2026, 9, 4, 15, 30, tzinfo=KST)

    with caplog.at_level(logging.WARNING, logger="kiwoom.watcher.triggers"):
        out = detect_tier1_stale_orders(
            [{"ord_no": "1", "stk_cd": "X"}], stale_minutes=5, now=now
        )

    assert out == []
    assert any("no readable order time" in r.message for r in caplog.records)
