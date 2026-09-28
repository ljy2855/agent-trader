"""The IC harness has to be able to find an edge and to refuse a fake one.

It is the instrument a signal redesign would be judged by, so a negative
result from it only means something if a positive result is reachable.
"""

from __future__ import annotations

import sys
import zlib
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backtest import ic  # noqa: E402

# Long enough that thirds and 5-session holdings both clear the module's
# own minimums — otherwise a test would be asserting against `None`.
SESSIONS = [f"2026{m:02d}{d:02d}" for m in range(1, 13) for d in range(1, 29)]
CODES = [f"C{i:02d}" for i in range(20)]


def _stable(*parts: str) -> int:
    """CRC32, not `hash` — str hashing is salted per process, and a test that
    passes on one run and fails on the next is worse than no test."""

    return zlib.crc32("|".join(parts).encode())


def _oracle(strength: float):
    """A feature that knows the future, scaled by `strength`.

    Returns are fixed per (code, session) so the feature and the forward
    return describe the same world.
    """

    def payoff(code: str, day: str) -> float:
        return ((_stable(code, day) % 2001) - 1000) / 100.0

    def forward(code: str, day: str, horizon: int) -> float | None:
        i = SESSIONS.index(day)
        return None if i + horizon >= len(SESSIONS) else payoff(code, day)

    def feature(code: str, day: str) -> float | None:
        noise = ((_stable(day, code, "n") % 2001) - 1000) / 100.0
        return strength * payoff(code, day) + (1 - strength) * noise

    return feature, forward


# --- spearman ---------------------------------------------------------------


def test_spearman_is_one_for_a_perfect_ordering_and_minus_one_reversed():
    xs = [1, 2, 3, 4, 5, 6, 7]
    assert ic.spearman(xs, xs) == pytest.approx(1.0)
    assert ic.spearman(xs, list(reversed(xs))) == pytest.approx(-1.0)


def test_spearman_refuses_a_sample_too_thin_to_rank():
    assert ic.spearman([1, 2, 3], [1, 2, 3]) is None


def test_a_constant_column_has_no_correlation_rather_than_a_crash():
    assert ic.spearman([1, 2, 3, 4, 5, 6], [7] * 6) is None


# --- the instrument ---------------------------------------------------------


def test_a_real_edge_is_found():
    feature, forward = _oracle(0.6)
    ics = ic.daily_ic(feature, forward, CODES, SESSIONS, 1)
    out = ic.summarize_ic(ics)

    assert out["mean_ic"] > 0.4
    assert out["t"] > 10
    assert out["ci_low"] > 0


def test_a_noiseless_signal_does_not_report_t_as_zero():
    """Zero dispersion with a non-zero mean is the strongest evidence there
    is. Dividing by it once reported t=0.0, which reads as "nothing here"."""

    feature, forward = _oracle(1.0)
    out = ic.summarize_ic(ic.daily_ic(feature, forward, CODES, SESSIONS, 1))

    assert out["mean_ic"] > 0.99
    assert out["t"] is None
    assert out["ci_low"] > 0.99


def test_a_feature_with_no_information_is_not_mistaken_for_one():
    feature, forward = _oracle(0.0)
    out = ic.summarize_ic(ic.daily_ic(feature, forward, CODES, SESSIONS, 1))

    assert abs(out["mean_ic"]) < 0.2
    assert out["ci_low"] < 0 < out["ci_high"]


def test_too_few_sessions_report_nothing_rather_than_a_number():
    feature, forward = _oracle(1.0)
    assert ic.summarize_ic(ic.daily_ic(feature, forward, CODES, SESSIONS[:10], 1)) is None
    assert ic.basket_excess(feature, forward, CODES, SESSIONS[:10], 1, top_n=3) is None


def test_the_bootstrap_is_deterministic_so_a_rerun_reproduces_the_interval():
    feature, forward = _oracle(0.5)
    ics = ic.daily_ic(feature, forward, CODES, SESSIONS, 1)
    assert ic.summarize_ic(ics) == ic.summarize_ic(ics)


# --- multiple testing -------------------------------------------------------


def test_the_multiple_testing_bar_grows_with_the_number_of_cells():
    """56 cells — the 2026-09-24 sweep — already expect |t| ≈ 2.8 from noise."""

    assert ic.expected_max_abs_t(1) == 0.0
    assert 2.7 < ic.expected_max_abs_t(56) < 2.9
    assert ic.expected_max_abs_t(200) > ic.expected_max_abs_t(56)


# --- sub-periods ------------------------------------------------------------


def test_subperiods_are_contiguous_and_cover_the_sample():
    feature, forward = _oracle(1.0)
    parts = ic.subperiod_ics(feature, forward, CODES, SESSIONS, 1, parts=3)

    assert len(parts) == 3
    assert parts[0]["start"] == SESSIONS[0]
    assert parts[-1]["end"] == SESSIONS[-1]
    # An edge present throughout must show in every slice — that is the whole
    # point of looking at thirds (low volatility passed overall and died in
    # the last third, 2026-09-24).
    assert all(p["mean_ic"] > 0.8 for p in parts)


# --- baskets and cost -------------------------------------------------------


def test_the_basket_is_measured_against_the_same_universe_not_raw_return():
    """A rising market must not read as skill. Every name gains the same 5%,
    so any basket's excess is exactly zero."""

    def forward(code, day, horizon):
        i = SESSIONS.index(day)
        return None if i + horizon >= len(SESSIONS) else 5.0

    def feature(code, day):
        return float(CODES.index(code))

    out = ic.basket_excess(feature, forward, CODES, SESSIONS, 1, top_n=3)
    assert out["excess_pct"] == 0.0


def test_the_round_trip_toll_is_charged_once_per_holding():
    feature, forward = _oracle(1.0)
    out = ic.basket_excess(feature, forward, CODES, SESSIONS, 1, top_n=3)

    assert out["excess_pct"] - out["net_pct"] == pytest.approx(
        ic.ROUND_TRIP_COST_PCT
    )
    assert ic.ROUND_TRIP_COST_PCT == 0.23


def test_an_edge_smaller_than_the_toll_reports_a_negative_net():
    """The finding this module exists to make legible: rev_1d's top-10 basket
    earned +0.094%/day against a 0.23% round trip."""

    def forward(code, day, horizon):
        i = SESSIONS.index(day)
        if i + horizon >= len(SESSIONS):
            return None
        return 0.1 if CODES.index(code) < 3 else 0.0

    def feature(code, day):
        return -float(CODES.index(code))

    out = ic.basket_excess(feature, forward, CODES, SESSIONS, 1, top_n=3)
    assert out["excess_pct"] > 0
    assert out["net_pct"] < 0


def test_non_overlapping_holdings_do_not_reuse_a_session():
    feature, forward = _oracle(1.0)
    five = ic.basket_excess(feature, forward, CODES, SESSIONS, 5, top_n=3)
    one = ic.basket_excess(feature, forward, CODES, SESSIONS, 1, top_n=3)

    assert five["holdings"] < one["holdings"]
    assert five["holdings"] <= len(SESSIONS) // 5 + 1
