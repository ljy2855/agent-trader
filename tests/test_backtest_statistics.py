"""Statistical significance tooling tests.

Each tool is checked against a case whose answer is known by construction
(a pure-noise strategy set must yield PBO ≈ 0.5; a CI on a strongly
positive series must exclude zero; DSR must fall as n_trials rises), so
these stay meaningful independent of the engine's entry logic.
"""

import pytest

from backtest.engine import Trade
from backtest.statistics import (
    block_performance,
    bootstrap_expectancy_ci,
    deflated_sharpe_ratio,
    expected_max_sharpe,
    make_block_edges,
    pbo_cscv,
)


def _trade(entry_date: str, net_pct: float) -> Trade:
    return Trade(
        code="X", entry_date=entry_date, entry_price=100.0,
        exit_date=entry_date, exit_price=100.0 * (1 + net_pct / 100),
        reason="take", gross_pct=net_pct, net_pct=net_pct,
    )


# --- bootstrap CI ---------------------------------------------------------


def test_bootstrap_ci_excludes_zero_for_strong_positive_edge():
    trades = [_trade(f"2026{i:04d}", 5.0) for i in range(50)]  # zero variance, all +5
    ci = bootstrap_expectancy_ci(trades, n_resamples=500)
    assert ci is not None
    assert ci.point == 5.0
    assert ci.excludes_zero
    assert ci.p_positive == 1.0


def test_bootstrap_ci_straddles_zero_for_symmetric_noise():
    # +1/-1 alternating → true expectancy 0; CI must not claim an edge.
    trades = [_trade(f"2026{i:04d}", 1.0 if i % 2 == 0 else -1.0) for i in range(200)]
    ci = bootstrap_expectancy_ci(trades, n_resamples=800)
    assert ci is not None
    assert not ci.excludes_zero
    assert 0.2 < ci.p_positive < 0.8  # coin-flip-ish, not a one-sided verdict


def test_bootstrap_ci_is_deterministic_for_a_given_seed():
    trades = [_trade(f"2026{i:04d}", (i % 7) - 3.0) for i in range(60)]
    a = bootstrap_expectancy_ci(trades, n_resamples=300, seed=42)
    b = bootstrap_expectancy_ci(trades, n_resamples=300, seed=42)
    assert (a.lower, a.upper) == (b.lower, b.upper)


def test_bootstrap_ci_none_on_empty_trades():
    assert bootstrap_expectancy_ci([]) is None


# --- block bucketing ------------------------------------------------------


def test_make_block_edges_partitions_dates():
    dates = [f"2026{i:04d}" for i in range(1, 101)]
    edges = make_block_edges(dates, 4)
    assert len(edges) == 5
    assert edges[0] == dates[0]
    assert edges[-1] == dates[-1]
    assert edges == sorted(edges)


def test_make_block_edges_rejects_too_few_dates():
    with pytest.raises(ValueError):
        make_block_edges(["20260101", "20260102"], 4)


def test_block_performance_buckets_by_entry_date_and_scores_empty_as_zero():
    edges = ["20260101", "20260110", "20260120", "20260130"]  # 3 blocks
    trades = [
        _trade("20260105", 2.0),   # block 0
        _trade("20260107", 4.0),   # block 0 → mean 3.0
        _trade("20260125", -1.0),  # block 2
    ]
    perf = block_performance(trades, edges)
    assert perf == [3.0, 0.0, -1.0]  # block 1 had no trades → 0.0


def test_block_performance_includes_final_boundary_date():
    edges = ["20260101", "20260110", "20260120"]
    perf = block_performance([_trade("20260120", 5.0)], edges)
    assert perf[-1] == 5.0  # last block is closed on the right


# --- PBO / CSCV -----------------------------------------------------------


def test_pbo_is_high_when_block_performance_is_pure_noise():
    # Strategies whose per-block ranking is shuffled have no persistent
    # skill → the IS winner should land below the OOS median about half
    # the time (PBO ≈ 0.5), the canonical "overfit selection" signature.
    perf = {
        "a": [3.0, -3.0, 3.0, -3.0, 3.0, -3.0],
        "b": [-3.0, 3.0, -3.0, 3.0, -3.0, 3.0],
        "c": [1.0, -1.0, -1.0, 1.0, 1.0, -1.0],
        "d": [-1.0, 1.0, 1.0, -1.0, -1.0, 1.0],
    }
    res = pbo_cscv(perf)
    assert res is not None
    assert res.n_blocks == 6
    assert res.n_splits == 20  # C(6,3)
    assert res.pbo > 0.4  # anti-correlated pairs → winner flips OOS


def test_pbo_is_low_when_one_strategy_dominates_every_block():
    # Persistent skill: "good" wins in-sample AND out-of-sample everywhere.
    perf = {
        "good": [5.0, 5.0, 5.0, 5.0, 5.0, 5.0],
        "mid": [1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
        "bad": [-2.0, -2.0, -2.0, -2.0, -2.0, -2.0],
    }
    res = pbo_cscv(perf)
    assert res is not None
    assert res.pbo == 0.0
    assert res.median_oos_rank > 0.8  # winner stays top-ranked OOS


def test_pbo_requires_even_block_count():
    with pytest.raises(ValueError):
        pbo_cscv({"a": [1.0, 2.0, 3.0], "b": [3.0, 2.0, 1.0]})


def test_pbo_requires_matching_block_counts():
    with pytest.raises(ValueError):
        pbo_cscv({"a": [1.0, 2.0], "b": [1.0, 2.0, 3.0, 4.0]})


def test_pbo_none_with_fewer_than_two_strategies():
    assert pbo_cscv({"only": [1.0, 2.0]}) is None


# --- Deflated Sharpe Ratio ------------------------------------------------


def test_expected_max_sharpe_grows_with_trial_count():
    # More tries → a higher bar the observed Sharpe must clear.
    few = expected_max_sharpe(5, 0.04)
    many = expected_max_sharpe(500, 0.04)
    assert 0 < few < many


def test_expected_max_sharpe_zero_for_single_trial():
    assert expected_max_sharpe(1, 0.04) == 0.0


def test_dsr_falls_as_declared_trial_count_rises():
    # Same returns, but admitting a wider search must deflate confidence.
    returns = [1.0, 2.0, -0.5, 1.5, 0.8, -0.2, 1.2, 0.9, 1.1, -0.3] * 5
    honest = deflated_sharpe_ratio(returns, n_trials=2)
    fished = deflated_sharpe_ratio(returns, n_trials=1000)
    assert honest is not None and fished is not None
    assert honest.dsr > fished.dsr
    assert fished.sharpe_benchmark > honest.sharpe_benchmark


def test_dsr_none_for_degenerate_series():
    assert deflated_sharpe_ratio([1.0, 1.0], n_trials=5) is None       # too few
    assert deflated_sharpe_ratio([2.0] * 10, n_trials=5) is None        # zero variance
