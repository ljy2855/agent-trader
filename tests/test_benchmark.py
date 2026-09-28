"""Account-vs-index comparison.

The reason this exists: over 2026-08-21..09-18 the account returned +0.12%
while KOSPI returned about +6.5%, and nothing in the system showed the gap.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.services import benchmark  # noqa: E402
from src.services import market  # noqa: E402


def _bar(day: str, close_points: float) -> dict:
    """One ka20006 row. Close is given in real points and scaled like the wire."""

    return {"dt": day, "cur_prc": str(int(round(close_points * 100)))}


def _point(day: str, value: float) -> dict:
    return {"date": day, "value": str(int(value))}


def _point_cash(day: str, value: float, cash: float) -> dict:
    """A point that also carries kt00002's `entr`, so exposure is known."""

    return {"date": day, "value": str(int(value)), "cash": str(int(cash))}


# --- the x100 wire format ---------------------------------------------------


def test_index_close_is_rescaled_from_the_wire_format():
    """Measured: KOSPI's 2026-09-18 close of 6894.23 arrives as "689423".

    Read raw it is a hundred times too large — still a plausible-looking
    curve, wrong only in the return.
    """

    assert market.index_bar_close({"cur_prc": "689423"}) == 6894.23
    assert benchmark.index_series([{"dt": "20260918", "cur_prc": "689423"}]) == {
        "2026-09-18": 6894.23
    }


def test_unreadable_index_rows_are_dropped_not_zeroed():
    series = benchmark.index_series(
        [
            {"dt": "20260918", "cur_prc": "689423"},
            {"dt": "20260917", "cur_prc": ""},
            {"dt": "", "cur_prc": "680000"},
            {"dt": "20260916", "cur_prc": "0"},
            "not a row",
        ]
    )
    assert series == {"2026-09-18": 6894.23}


def test_kiwoom_and_iso_dates_both_parse():
    assert benchmark.account_series([_point("2026-09-18", 1_000_000)]) == {
        "2026-09-18": 1_000_000.0
    }
    assert benchmark.account_series(
        [{"dt": "20260918", "prsm_dpst_aset_amt": "1000000"}]
    ) == {"2026-09-18": 1_000_000.0}


# --- the comparison ---------------------------------------------------------


def test_flat_account_against_a_rising_index_shows_negative_alpha():
    """The week that prompted this: account flat, index up."""

    days = ["2026-09-14", "2026-09-15", "2026-09-16", "2026-09-17"]
    account = [_point(d, 1_000_000) for d in days]
    index = [_bar(d.replace("-", ""), c) for d, c in zip(days, [100, 102, 104, 106])]

    out = benchmark.build_comparison(account, index)

    assert out["available"] is True
    assert out["account_return_pct"] == 0.0
    assert out["index_return_pct"] == 6.0
    assert out["alpha_pct"] == -6.0
    assert out["compared_days"] == 3


def test_only_days_present_in_both_series_are_compared():
    """A holiday on one side must shorten the window, not bridge across it."""

    account = [
        _point("2026-09-14", 1_000_000),
        _point("2026-09-15", 1_010_000),
        _point("2026-09-16", 1_020_000),
    ]
    index = [_bar("20260914", 100), _bar("20260916", 110)]

    out = benchmark.build_comparison(account, index)

    assert out["start_date"] == "2026-09-14"
    assert out["end_date"] == "2026-09-16"
    assert out["compared_days"] == 1
    # 9/15 is absent from the index, so its account move is not counted either.
    assert out["account_return_pct"] == 2.0


# --- external cash flows ----------------------------------------------------


def test_a_withdrawal_is_excluded_rather_than_counted_as_loss():
    """Measured: 2026-08-07, 1,756,640 -> 1,256,640 (a 500,000 withdrawal).

    A start/end comparison reports that as roughly -28% and makes every
    number in the window wrong. This is the case the whole module is
    shaped around.
    """

    days = ["2026-08-06", "2026-08-07", "2026-08-10", "2026-08-11"]
    values = [1_756_640, 1_256_640, 1_262_640, 1_268_640]
    account = [_point(d, v) for d, v in zip(days, values)]
    index = [_bar(d.replace("-", ""), c) for d, c in zip(days, [100, 100, 101, 102])]

    out = benchmark.build_comparison(account, index)

    assert [e["date"] for e in out["excluded_days"]] == ["2026-08-07"]
    assert out["excluded_days"][0]["change_pct"] < -20

    # The surviving days are real trading: 1,256,640 -> 1,268,640.
    assert out["account_return_pct"] == 0.95
    # Naive start/end would have been about -27.8%; nothing near it survives.
    assert out["account_return_pct"] > 0

    # The index leg drops the same day, so both sides span identical time.
    assert out["index_return_pct"] == 2.0
    assert "입출금" in out["note"]


def test_an_exclusion_warns_that_endpoints_will_not_reconcile():
    """Measured on live data: index_start 6257.45, index_end 6894.23.

    Endpoint arithmetic gives 10.18% but the chained figure was 10.84%,
    because 2026-08-07's index move dropped out with the withdrawal. Both
    sides must span identical days, so the gap is correct — and a reader
    who divides the endpoints must not conclude the number is broken.
    """

    days = ["2026-08-06", "2026-08-07", "2026-08-10"]
    account = [_point(d, v) for d, v in zip(days, [1_756_640, 1_256_640, 1_262_640])]
    index = [_bar(d.replace("-", ""), c) for d, c in zip(days, [100, 90, 95])]

    out = benchmark.build_comparison(account, index)

    assert len(out["excluded_days"]) == 1
    # The 100 -> 90 leg is gone with it; only 90 -> 95 is chained.
    assert out["index_return_pct"] == 5.56
    assert out["index_start"] == 100.0 and out["index_end"] == 95.0
    assert "일치하지 않는다" in out["note"]


def test_a_flow_smaller_than_the_bound_is_admitted_and_the_note_says_so():
    """Honesty about the limit: there is no cash-flow feed to check against.

    A 5% deposit is indistinguishable from a 5% gain here. The number must
    not pretend otherwise.
    """

    days = ["2026-09-14", "2026-09-15"]
    account = [_point("2026-09-14", 1_000_000), _point("2026-09-15", 1_050_000)]
    index = [_bar("20260914", 100), _bar("20260915", 100)]

    out = benchmark.build_comparison(account, index)

    assert out["excluded_days"] == []
    assert out["account_return_pct"] == 5.0
    assert "입출금 내역 API가 없어" in out["note"]


def test_a_limit_move_on_a_real_session_is_not_mistaken_for_a_flow():
    """The bound must never delete a genuine trading day.

    KRX caps a name at ±30%; at budget 60% / max_positions 1 the account
    tops out near ±18%, so a hard day still has to survive.
    """

    account = [_point("2026-09-14", 1_000_000), _point("2026-09-15", 1_180_000)]
    index = [_bar("20260914", 100), _bar("20260915", 105)]

    out = benchmark.build_comparison(account, index)

    assert out["excluded_days"] == []
    assert out["account_return_pct"] == 18.0


# --- window sensitivity -----------------------------------------------------


def test_trailing_windows_are_reported_alongside_the_full_span():
    """One window is a choice, and the choice can decide the verdict.

    Measured 2026-09-21 on this account: alpha ran +16.57p over 54 trading
    days and -10.87p over 32, because KOSPI peaked 2026-06-22 and sold off
    in early August. A single number is a window somebody picked.
    """

    # Index falls for ten days, then recovers. Account flat throughout.
    closes = [100, 95, 90, 85, 80, 78, 80, 85, 90, 95, 100]
    days = [f"2026-09-{d:02d}" for d in range(1, 12)]
    account = [_point(d, 1_000_000) for d in days]
    index = [_bar(d.replace("-", ""), c) for d, c in zip(days, closes)]

    out = benchmark.build_comparison(account, index, trailing_windows=(5,))

    # Over the whole span the index round-trips, so alpha is ~0 ...
    assert out["alpha_pct"] == 0.0
    # ... while the trailing half only sees the recovery, and the flat
    # account looks badly behind.
    assert len(out["windows"]) == 1
    recent = out["windows"][0]
    assert recent["trading_days"] == 5
    assert recent["index_return_pct"] == 28.21
    assert recent["alpha_pct"] == -28.21


def test_a_window_longer_than_the_data_is_skipped_not_padded():
    """Asking for 60 days of a 3-day history must not invent history."""

    days = ["2026-09-14", "2026-09-15", "2026-09-16"]
    account = [_point(d, 1_000_000) for d in days]
    index = [_bar(d.replace("-", ""), c) for d, c in zip(days, [100, 101, 102])]

    out = benchmark.build_comparison(account, index, trailing_windows=(60,))

    assert out["windows"] == []
    assert out["compared_days"] == 2


# --- exposure ---------------------------------------------------------------


def test_exposure_is_the_share_of_assets_not_in_cash():
    assert benchmark.exposure_series(
        [{"date": "2026-09-18", "value": "1000000", "cash": "700000"}]
    ) == {"2026-09-18": 0.3}
    # Kiwoom's own field name works too, zero-padded as it arrives.
    assert benchmark.exposure_series(
        [{"dt": "20260918", "prsm_dpst_aset_amt": "000001000000",
          "entr": "000000250000"}]
    ) == {"2026-09-18": 0.75}


def test_settlement_can_put_cash_above_assets_and_is_clamped():
    """Measured 2026-09-16: entr exceeded the total by 744원 after a sale.

    T+2 settlement, not a short position. Reporting -0.1% exposure would be
    reporting a holding that does not exist.
    """

    assert benchmark.exposure_series(
        [{"date": "2026-09-16", "value": "1264232", "cash": "1264976"}]
    ) == {"2026-09-16": 0.0}


def test_a_cash_account_in_a_rally_is_not_blamed_on_stock_picking():
    """The case that prompted this: 2026-07-27..09-23.

    The account ran about 8% invested while KOSPI rose 5.44%, and the -6.9p
    headline alpha read as "the picks are bad" when almost all of it was the
    idle cash. Splitting it points at the right lever.
    """

    days = ["2026-09-14", "2026-09-15", "2026-09-16", "2026-09-17"]
    # Entirely in cash, flat account, index up 6%.
    account = [_point_cash(d, 1_000_000, 1_000_000) for d in days]
    index = [_bar(d.replace("-", ""), c) for d, c in zip(days, [100, 102, 104, 106])]

    out = benchmark.build_comparison(account, index)

    assert out["avg_exposure_pct"] == 0.0
    assert out["alpha_pct"] == -6.0
    # Every point of it is the cash, none of it is selection.
    assert out["cash_drag_pct"] == -6.0
    assert out["selection_alpha_pct"] == 0.0


def test_a_fully_invested_account_has_no_cash_drag():
    days = ["2026-09-14", "2026-09-15", "2026-09-16"]
    account = [_point_cash(d, v, 0) for d, v in zip(days, [1_000_000, 1_010_000, 1_020_100])]
    index = [_bar(d.replace("-", ""), c) for d, c in zip(days, [100, 102, 104])]

    out = benchmark.build_comparison(account, index)

    assert out["avg_exposure_pct"] == 100.0
    assert out["cash_drag_pct"] == 0.0
    # With no cash to blame, selection carries the whole gap.
    assert out["selection_alpha_pct"] == out["alpha_pct"]


def test_the_split_always_adds_back_to_alpha():
    """cash drag + selection must reconstruct the headline, or the decomposition
    is telling two different stories about one number."""

    days = [f"2026-09-{d:02d}" for d in (14, 15, 16, 17, 18)]
    account = [
        _point_cash(d, v, c)
        for d, v, c in zip(
            days,
            [1_000_000, 1_004_000, 1_002_000, 1_009_000, 1_006_000],
            [600_000, 600_000, 400_000, 400_000, 900_000],
        )
    ]
    index = [_bar(d.replace("-", ""), c)
             for d, c in zip(days, [100, 101, 100.5, 103, 102])]

    out = benchmark.build_comparison(account, index)

    assert out["cash_drag_pct"] + out["selection_alpha_pct"] == out["alpha_pct"]
    assert 0.0 < out["avg_exposure_pct"] < 100.0
    assert "T+2" in out["exposure_note"]


def test_points_without_a_cash_leg_report_no_exposure_at_all():
    """Older callers pass value-only points. Inventing an exposure of zero
    for them would say the account was in cash, which is a claim."""

    days = ["2026-09-14", "2026-09-15", "2026-09-16"]
    account = [_point(d, 1_000_000) for d in days]
    index = [_bar(d.replace("-", ""), c) for d, c in zip(days, [100, 101, 102])]

    out = benchmark.build_comparison(account, index)

    assert out["available"] is True
    assert "avg_exposure_pct" not in out
    assert "selection_alpha_pct" not in out
    assert "exposure_note" not in out


def test_trailing_windows_carry_their_own_exposure():
    """Exposure moves, so a window's split has to be measured on that window."""

    days = [f"2026-09-{d:02d}" for d in range(1, 12)]
    # All cash for the first half, fully invested for the second.
    cash = [1_000_000] * 6 + [0] * 5
    account = [_point_cash(d, 1_000_000, c) for d, c in zip(days, cash)]
    index = [_bar(d.replace("-", ""), 100) for d in days]

    out = benchmark.build_comparison(account, index, trailing_windows=(4,))

    assert out["avg_exposure_pct"] < 60.0
    assert out["windows"][0]["avg_exposure_pct"] == 100.0


# --- degenerate input -------------------------------------------------------


def test_a_single_overlapping_day_reports_unavailable_not_zero():
    """One day is no return. Zero would read as "flat", which is a claim."""

    out = benchmark.build_comparison(
        [_point("2026-09-18", 1_000_000)], [_bar("20260918", 100)]
    )
    assert out["available"] is False
    assert "2일 이상" in out["reason"]


def test_empty_input_is_unavailable():
    assert benchmark.build_comparison([], [])["available"] is False
