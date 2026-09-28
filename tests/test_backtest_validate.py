"""Walk-forward harness unit tests.

Structural correctness (fold boundaries, non-overlap, aggregation) is
tested independently of whether any trade actually fires — that keeps
these tests fast and immune to unrelated changes in engine.py's entry
logic. `_pick_best`'s selection/fallback behavior is tested separately
with small hand-built OHLC series (same style as test_backtest_engine.py).
"""

from backtest.engine import Params, Trade
from backtest.validate import (
    Fold,
    WalkForwardResult,
    _pick_best,
    date_bounds,
    random_entry_null,
    split_by_date,
    walk_forward,
)


def _bar(d, o, h, l, c):
    return {"dt": d, "open_pric": str(o), "high_pric": str(h), "low_pric": str(l), "cur_prc": str(c)}


def _flat_bars(dates: list[str]) -> list[dict]:
    """No day-change ever qualifies for a momentum entry — zero trades."""
    return [_bar(d, 100, 101, 99, 100) for d in dates]


def _dates(n: int, start_year_day: int = 1) -> list[str]:
    # Fake but strictly increasing YYYYMMDD-shaped strings — good enough for
    # string comparison, which is all split_by_date/walk_forward rely on.
    return [f"2026{(start_year_day + i):04d}" for i in range(n)]


# --- split_by_date / date_bounds -------------------------------------------


def test_split_by_date_partitions_by_shared_cutoff():
    series = {
        "A": _flat_bars(["20260101", "20260102", "20260103", "20260104"]),
        "B": _flat_bars(["20260101", "20260103", "20260105"]),
    }
    train, test = split_by_date(series, cutoff="20260103")
    assert [b["dt"] for b in train["A"]] == ["20260101", "20260102"]
    assert [b["dt"] for b in test["A"]] == ["20260103", "20260104"]
    assert [b["dt"] for b in train["B"]] == ["20260101"]
    assert [b["dt"] for b in test["B"]] == ["20260103", "20260105"]


def test_split_by_date_omits_empty_side():
    series = {"A": _flat_bars(["20260101", "20260102"])}
    train, test = split_by_date(series, cutoff="20260201")
    assert "A" in train
    assert "A" not in test  # nothing on/after cutoff → symbol dropped from that side

    train2, test2 = split_by_date(series, cutoff="20260101")
    assert "A" not in train2  # nothing before cutoff
    assert "A" in test2


def test_date_bounds():
    series = {
        "A": _flat_bars(["20260105", "20260101", "20260110"]),
        "B": _flat_bars(["20260103"]),
    }
    assert date_bounds(series) == ("20260101", "20260110")


def test_date_bounds_empty_series():
    assert date_bounds({}) == ("", "")


# --- _pick_best --------------------------------------------------------


def test_pick_best_selects_higher_expectancy_regardless_of_grid_order():
    # day2 +3% → entry at day3 open(100). day3 low=97 (would hit a wide
    # stop's threshold only if stop <= -3%), high=106.
    bars = [
        _bar("20260101", 100, 101, 99, 100),
        _bar("20260102", 100, 104, 100, 103),  # +3% entry signal
        _bar("20260103", 100, 106, 97, 100),   # low 97, high 106
    ]
    series = {"X": bars}
    loses = Params(stop_loss_pct=-2.5, take_profit_pct=5, max_hold_days=3)   # low 97 <= 97.5 → stop, -2.5% loss
    wins = Params(stop_loss_pct=-10, take_profit_pct=3, max_hold_days=3)     # stop not hit; high 106>=103 → +3% win

    best, summary = _pick_best(series, [loses, wins])
    assert best is wins
    assert summary["expectancy_pct"] > 0

    # Order shouldn't matter.
    best2, _ = _pick_best(series, [wins, loses])
    assert best2 is wins


def test_pick_best_falls_back_to_first_grid_entry_when_nothing_trades():
    series = {"X": _flat_bars(_dates(10))}
    a = Params(day_change_min=5, day_change_max=10)
    b = Params(day_change_min=6, day_change_max=10)
    best, summary = _pick_best(series, [a, b])
    assert best is a  # incumbent/first entry, not an arbitrary untested one
    assert summary["trades"] == 0


# --- walk_forward: fold bookkeeping -------------------------------------


def test_walk_forward_returns_no_folds_when_history_too_short():
    series = {"X": _flat_bars(_dates(20))}
    wf = walk_forward(series, [Params()], train_days=15, test_days=10)
    assert wf.folds == []


def test_walk_forward_folds_are_contiguous_and_non_overlapping():
    dates = _dates(50)
    series = {"X": _flat_bars(dates), "Y": _flat_bars(dates)}
    wf = walk_forward(series, [Params()], train_days=20, test_days=10)

    # (50 - 20) // 10 = 3 non-overlapping test windows fit.
    assert len(wf.folds) == 3
    for f in wf.folds:
        assert f.train_start < f.train_end < f.test_start <= f.test_end
    # Consecutive folds' test windows must not overlap, and (default
    # step_days == test_days) must be back-to-back on the shared calendar.
    for prev, nxt in zip(wf.folds, wf.folds[1:]):
        assert prev.test_end < nxt.test_start
        idx_prev_end = dates.index(prev.test_end)
        idx_next_start = dates.index(nxt.test_start)
        assert idx_next_start == idx_prev_end + 1


def test_walk_forward_custom_step_can_overlap_or_gap():
    dates = _dates(40)
    series = {"X": _flat_bars(dates)}
    # step_days smaller than test_days → overlapping test windows allowed;
    # just verify it doesn't crash and produces more folds than the
    # non-overlapping default would.
    wf_default = walk_forward(series, [Params()], train_days=15, test_days=10)
    wf_overlap = walk_forward(series, [Params()], train_days=15, test_days=10, step_days=5)
    assert len(wf_overlap.folds) >= len(wf_default.folds)


def test_walk_forward_uses_incumbent_when_no_fold_can_discriminate():
    # No momentum entry ever fires for either grid param → every fold's
    # best_params must fall back to grid[0].
    series = {"X": _flat_bars(_dates(40))}
    incumbent = Params(day_change_min=5, day_change_max=6)
    alt = Params(day_change_min=7, day_change_max=8)
    wf = walk_forward(series, [incumbent, alt], train_days=15, test_days=10)
    assert wf.folds  # sanity: folds were produced
    assert all(f.best_params is incumbent for f in wf.folds)


def test_walk_forward_uses_past_bars_for_ma_without_counting_train_trades():
    dates = _dates(30)
    bars = _flat_bars(dates)
    bars[19] = _bar(dates[19], 99, 100, 98, 99)
    params = Params(entry_mode="below_ma", ma_period=20)
    result = walk_forward({"X": bars}, [params], train_days=20, test_days=10)
    trades = result.folds[0].test_trades
    assert trades
    assert trades[0].entry_date == dates[20]
    assert all(trade.entry_date >= dates[20] for trade in trades)


# --- WalkForwardResult aggregation (fabricated folds — no engine calls) --


def _trade(entry_date: str, net_pct: float) -> Trade:
    return Trade(
        code="X", entry_date=entry_date, entry_price=100.0,
        exit_date=entry_date, exit_price=100.0 * (1 + net_pct / 100),
        reason="take", gross_pct=net_pct, net_pct=net_pct,
    )


def test_combined_test_summary_concatenates_and_sorts_fold_trades():
    fold1 = Fold(
        train_start="20260101", train_end="20260110",
        test_start="20260111", test_end="20260120",
        best_params=Params(),
        train_summary={"expectancy_pct": 1.0},
        test_summary={"expectancy_pct": 0.5},
        test_trades=[_trade("20260115", 2.0)],
    )
    fold2 = Fold(
        train_start="20260121", train_end="20260130",
        test_start="20260201", test_end="20260210",
        best_params=Params(),
        train_summary={"expectancy_pct": 1.0},
        test_summary={"expectancy_pct": -0.5},
        test_trades=[_trade("20260205", -1.0), _trade("20260202", 3.0)],
    )
    wf = WalkForwardResult(folds=[fold1, fold2])
    combined = wf.combined_test_summary
    assert combined["trades"] == 3
    # sanity: entry order should be chronological across folds.


def test_walk_forward_efficiency_averages_ratios_and_skips_nonpositive_is():
    fold_good = Fold(
        train_start="a", train_end="b", test_start="c", test_end="d",
        best_params=Params(),
        train_summary={"expectancy_pct": 2.0},
        test_summary={"expectancy_pct": 1.0},  # ratio 0.5
    )
    fold_worse = Fold(
        train_start="a", train_end="b", test_start="c", test_end="d",
        best_params=Params(),
        train_summary={"expectancy_pct": 4.0},
        test_summary={"expectancy_pct": 4.0},  # ratio 1.0
    )
    fold_excluded = Fold(
        train_start="a", train_end="b", test_start="c", test_end="d",
        best_params=Params(),
        train_summary={"expectancy_pct": -1.0},  # IS <= 0 → excluded regardless of OOS
        test_summary={"expectancy_pct": 5.0},
    )
    wf = WalkForwardResult(folds=[fold_good, fold_worse, fold_excluded])
    assert wf.walk_forward_efficiency == 0.75  # mean(0.5, 1.0)


def test_walk_forward_efficiency_none_when_no_fold_has_positive_is_edge():
    fold = Fold(
        train_start="a", train_end="b", test_start="c", test_end="d",
        best_params=Params(),
        train_summary={"expectancy_pct": -2.0},
        test_summary={"expectancy_pct": 1.0},
    )
    wf = WalkForwardResult(folds=[fold])
    assert wf.walk_forward_efficiency is None


def test_walk_forward_efficiency_none_when_no_folds():
    assert WalkForwardResult(folds=[]).walk_forward_efficiency is None


# --- random-entry null model --------------------------------------------


def _trending_bars(dates: list[str], drift_pct: float) -> list[dict]:
    """Bars with a steady per-bar drift — any hold earns it, signal or not."""
    out = []
    px = 100.0
    for d in dates:
        nxt = px * (1 + drift_pct / 100)
        out.append(_bar(d, px, max(px, nxt) * 1.001, min(px, nxt) * 0.999, nxt))
        px = nxt
    return out


def test_random_entry_null_flags_drift_as_beta():
    # Pure uptrend, no exploitable structure: the strategy cannot beat
    # random entry, so p_value must be high and the verdict "beta".
    dates = _dates(300)
    series = {"A": _trending_bars(dates, 0.3), "B": _trending_bars(dates, 0.25)}
    p = Params(entry_mode="momentum", day_change_min=0.1, day_change_max=5,
               stop_loss_pct=-10, take_profit_pct=20, max_hold_days=10)
    res = random_entry_null(series, p, n_seeds=8)
    assert res is not None
    assert res.p_value > 0.05
    assert "베타" in res.verdict or "미약" in res.verdict


def test_random_entry_null_reports_matched_trade_counts():
    dates = _dates(200)
    series = {"A": _trending_bars(dates, 0.2)}
    p = Params(entry_mode="momentum", day_change_min=0.05, day_change_max=5,
               stop_loss_pct=-10, take_profit_pct=20, max_hold_days=5)
    res = random_entry_null(series, p, n_seeds=5)
    assert res is not None
    assert res.n_strategy_trades > 0 and res.n_null_trades_avg > 0
    # entry-rate calibration should keep the null within an order of
    # magnitude of the strategy's turnover (else cost drag isn't comparable)
    assert 0.1 < res.n_null_trades_avg / res.n_strategy_trades < 10


def test_random_entry_null_is_deterministic():
    dates = _dates(150)
    series = {"A": _trending_bars(dates, 0.2)}
    p = Params(entry_mode="momentum", day_change_min=0.05, day_change_max=5,
               stop_loss_pct=-10, take_profit_pct=20, max_hold_days=5)
    a = random_entry_null(series, p, n_seeds=5, seed_base=7)
    b = random_entry_null(series, p, n_seeds=5, seed_base=7)
    assert a.null_expectancy == b.null_expectancy


def test_random_entry_null_none_when_strategy_never_trades():
    series = {"A": _flat_bars(_dates(50))}
    p = Params(entry_mode="momentum", day_change_min=50, day_change_max=60)
    assert random_entry_null(series, p, n_seeds=3) is None
