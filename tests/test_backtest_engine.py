"""Backtest engine unit tests — synthetic OHLC drives each exit branch."""

import pytest

from backtest.engine import Params, backtest_symbol, run_backtest, _entry_signal, normalize_rows


def _bar(d, o, h, l, c):
    return {"dt": d, "open_pric": str(o), "high_pric": str(h), "low_pric": str(l), "cur_prc": str(c)}


def test_entry_triggers_on_band_and_exits_take_profit():
    # day2 closes +5% vs day1 → entry at day3 open(100); day3 high hits +5% target.
    bars = [
        _bar("20260101", 100, 101, 99, 100),   # day1 close 100
        _bar("20260102", 100, 106, 100, 105),  # day2 close 105 = +5% → entry signal
        _bar("20260103", 100, 106, 99, 103),   # day3 open 100, high 106 ≥ 105 take
    ]
    p = Params(day_change_min=0.5, day_change_max=10, stop_loss_pct=-2.5, take_profit_pct=5, max_hold_days=3)
    trades = backtest_symbol("X", bars, p)
    assert len(trades) == 1
    t = trades[0]
    assert t.reason == "take"
    assert t.entry_price == 100 and t.exit_price == 105  # +5% target
    assert t.gross_pct == 5.0
    expected = (105 * (1 - 0.00215) / (100 * (1 + 0.00015)) - 1) * 100
    assert t.net_pct == round(expected, 3)


def test_exits_stop_loss_and_stop_wins_double_touch():
    # day3 low hits stop AND high hits take same day → stop fills first (conservative).
    bars = [
        _bar("20260101", 100, 101, 99, 100),
        _bar("20260102", 100, 104, 100, 103),  # +3% entry signal
        _bar("20260103", 100, 106, 97, 100),   # low 97 ≤ 97.5 stop, high 106 ≥ 105 take
    ]
    p = Params(stop_loss_pct=-2.5, take_profit_pct=5, max_hold_days=3)
    t = backtest_symbol("X", bars, p)[0]
    assert t.reason == "stop"
    assert abs(t.exit_price - 97.5) < 1e-9  # entry 100 * (1 - 2.5%)


def test_max_hold_closes_at_close():
    # neither stop nor take within max_hold → close at last held bar's close.
    bars = [
        _bar("20260101", 100, 101, 99, 100),
        _bar("20260102", 100, 104, 100, 103),  # +3% entry
        _bar("20260103", 100, 102, 99, 101),   # no stop/take
        _bar("20260104", 101, 103, 100, 102),  # close 102
    ]
    p = Params(stop_loss_pct=-2.5, take_profit_pct=5, max_hold_days=2)
    t = backtest_symbol("X", bars, p)[0]
    assert t.reason == "max_hold"


def test_no_entry_outside_band():
    # day2 +0.3% is below dc_min 0.5 → no trade.
    bars = [
        _bar("20260101", 100, 101, 99, 100),
        _bar("20260102", 100, 101, 100, 100.3),
        _bar("20260103", 100, 101, 99, 100),
    ]
    assert backtest_symbol("X", bars, Params(day_change_min=0.5)) == []


def test_summary_metrics():
    # one win (+4.77 net), one loss → win_rate 50, expectancy computed.
    bars = [
        _bar("20260101", 100, 101, 99, 100),
        _bar("20260102", 100, 106, 100, 105),  # +5% → entry day3
        _bar("20260103", 100, 106, 99, 103),   # take +5%
        _bar("20260104", 103, 104, 102, 103),
        _bar("20260105", 103, 108, 103, 107),  # +3.9% vs 103 → entry day6
        _bar("20260106", 107, 108, 103, 104),  # low 103 ≤ 104.3 stop
    ]
    res = run_backtest({"X": bars}, Params(stop_loss_pct=-2.5, take_profit_pct=5, max_hold_days=3))
    s = res.summary()
    assert s["trades"] == 2
    assert s["win_rate_pct"] == 50.0
    assert "expectancy_pct" in s and "max_drawdown_pct" in s


def test_below_ma_entry_signal():
    # 20일 평평(100) 후 95로 dip → below_ma 진입. 직전 바는 MA 위(>=100).
    from backtest.engine import _entry_signal, Params
    rows = [{"d": f"2026{i:04d}", "o": 100, "h": 101, "l": 99, "c": 100.0} for i in range(20)]
    rows.append({"d": "20260021", "o": 100, "h": 100, "l": 94, "c": 95.0})  # dip below MA
    p = Params(entry_mode="below_ma", ma_period=20)
    assert _entry_signal(rows, 20, p) is True   # close 95 < MA 100
    assert _entry_signal(rows, 19, p) is False  # at MA, no dip


def test_drop_from_high_entry_signal():
    from backtest.engine import _entry_signal, Params
    rows = [{"d": f"2026{i:04d}", "o": 100, "h": 110, "l": 99, "c": 100.0} for i in range(20)]
    rows.append({"d": "20260021", "o": 100, "h": 100, "l": 94, "c": 95.0})  # 95 vs high 110 = -13.6%
    p = Params(entry_mode="drop_from_high", high_lookback=20, drop_from_high_pct=5)
    assert _entry_signal(rows, 20, p) is True   # 95 <= 110*0.95=104.5


def test_gap_below_stop_exits_at_open_not_unavailable_stop_price():
    bars = [
        _bar("20260101", 100, 101, 99, 100),
        _bar("20260102", 100, 104, 100, 103),
        _bar("20260103", 100, 101, 99, 100),
        _bar("20260104", 80, 85, 75, 82),
    ]
    trade = backtest_symbol("X", bars, Params(stop_loss_pct=-4, take_profit_pct=8))[0]
    assert trade.reason == "stop"
    assert trade.exit_price == 80
    assert trade.gross_pct == -20


def test_gap_above_target_executes_before_later_intraday_stop():
    bars = [
        _bar("20260101", 100, 101, 99, 100),
        _bar("20260102", 100, 104, 100, 103),
        _bar("20260103", 100, 101, 99, 100),
        _bar("20260104", 110, 115, 90, 100),
    ]
    trade = backtest_symbol("X", bars, Params(stop_loss_pct=-4, take_profit_pct=8))[0]
    assert trade.reason == "take"
    assert trade.exit_price == 110


@pytest.mark.parametrize("style", ["band", "crossover"])
def test_ma_signal_never_reads_future_bars(style):
    rows = [{"c": 100.0} for _ in range(20)] + [{"c": 99.0}, {"c": 98.0}]
    params = Params(entry_mode="below_ma", ma_entry_style=style)
    for index in (20, 21):
        expected = _entry_signal(rows[:index + 1], index, params)
        assert _entry_signal(rows + [{"c": 1000000.0}], index, params) == expected


def test_below_ma_band_accepts_sustained_shallow_dip_but_not_deep_decline():
    rows = [{"c": 100.0} for _ in range(20)] + [{"c": 99.0}, {"c": 98.0}]
    params = Params(entry_mode="below_ma")
    assert _entry_signal(rows, 21, params)
    rows[21] = {"c": 80.0}
    assert not _entry_signal(rows, 21, params)


def test_slippage_is_adverse_on_both_sides():
    bars = [
        _bar("20260101", 100, 101, 99, 100),
        _bar("20260102", 100, 104, 100, 103),
        _bar("20260103", 100, 101, 99, 100),
    ]
    base = backtest_symbol("X", bars, Params())[0]
    stressed = backtest_symbol("X", bars, Params(slippage_bps=10))[0]
    assert stressed.entry_price > base.entry_price
    assert stressed.exit_price < base.exit_price
    assert stressed.net_pct < base.net_pct


@pytest.mark.parametrize("price", ["0", "NaN", "Infinity"])
def test_invalid_prices_are_not_tradeable(price):
    assert normalize_rows([_bar("20260101", price, 101, 99, 100)]) == []


@pytest.mark.parametrize("overrides", [
    {"ma_period": 0}, {"max_hold_days": 0}, {"stop_loss_pct": -100},
    {"slippage_bps": -1}, {"tax_pct": float("nan")}, {"ma_entry_style": "invalid"},
])
def test_invalid_backtest_parameters_are_rejected(overrides):
    with pytest.raises(ValueError):
        Params(**overrides)
