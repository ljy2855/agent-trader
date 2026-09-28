"""The agents' per-stock tools must read the numbers the watcher trades on."""

from __future__ import annotations

from src.services import strategy
from src.services.stock_tools import summarize_daily_bars, summarize_quote


def _bars(today_close=98_000, today_low=97_500, today_volume=2_500_000, prior=24):
    """Newest first: today, then ``prior`` flat days at 100,000."""

    rows = [
        {
            "date": "20260923", "open_pric": "99000", "high_pric": "99500",
            "low_pric": str(today_low), "close_pric": f"-{today_close}",
            "trde_qty": str(today_volume),
        }
    ]
    for i in range(prior):
        rows.append(
            {
                "date": f"2026082{i % 10}", "open_pric": "100000", "high_pric": "101000",
                "low_pric": "99000", "close_pric": "100000", "trde_qty": "1000000",
            }
        )
    return rows


def test_daily_bar_indicators():
    out = summarize_daily_bars(_bars(), stock_code="005930")
    ind = out["indicators"]

    # MA20 = (98,000 + 19 × 100,000) / 20 = 99,900; the close sits 1.90% under it.
    assert ind["ma"] == 99_900
    assert ind["ma_dip_pct"] == 1.9
    assert ind["volume_ratio_20d"] == 2.5
    assert ind["prior_20d_low"] == 99_000
    assert ind["new_20d_low"] is True
    assert out["bars"][0] == {
        "date": "20260923", "open": 99_000, "high": 99_500,
        "low": 97_500, "close": 98_000, "volume": 2_500_000,
    }


def test_close_above_the_ma_reads_as_a_negative_dip():
    ind = summarize_daily_bars(_bars(today_close=103_000, today_low=99_500), stock_code="X")[
        "indicators"
    ]
    assert ind["ma_dip_pct"] < 0
    assert ind["new_20d_low"] is False


def test_too_few_bars_gives_none_rather_than_a_short_window():
    ind = summarize_daily_bars(_bars(prior=9), stock_code="X")["indicators"]

    # A 10-bar "MA20" or "20-day low" would be a different indicator under
    # the same name.
    assert ind["ma"] is None
    assert ind["ma_dip_pct"] is None
    assert ind["volume_ratio_20d"] is None
    assert ind["prior_20d_low"] is None
    assert ind["new_20d_low"] is None


def test_tool_and_watcher_compute_the_same_dip_and_volume_ratio():
    """One function, one number: the tool must agree with the live scorer."""

    bars = _bars()
    detail = {
        "quote": {
            "stk_nm": "삼성전자", "cur_prc": "-98000", "open_pric": "99000",
            "high_pric": "99500", "pred_close_pric": "100000", "flu_rt": "-2.00",
            "flo_stkcnt": "5846279", "upl_pric": "130000",
        },
        "orderbook": {
            "tot_buy_req": "1000", "tot_sel_req": "1000",
            "buy_fpr_bid": "97900", "sel_fpr_bid": "98000",
        },
        "daily_bars": bars,
    }
    _, row = strategy._score_candidate(
        {"stock_code": "005930", "sources": ["roster"]},
        detail,
        {"regime": "neutral", "market_data_complete": True},
        entry_mode="below_ma",
        ma_period=20,
    )
    ind = summarize_daily_bars(bars, stock_code="005930")["indicators"]

    assert row["ma_dip_pct"] == ind["ma_dip_pct"] == 1.9
    assert row["volume_ratio_20d"] == ind["volume_ratio_20d"] == 2.5
    assert row["ma_value"] == 99_900
    assert row["ma_period"] == 20
    assert row["market_cap_krw"] == 98_000 * 5_846_279 * 1000
    # 상한가 130,000까지 (130,000 − 98,000) / 98,000 = 32.65%.
    assert row["upper_limit_distance_pct"] == 32.65


def test_quote_summary():
    quote = {
        "stk_nm": "삼성전자", "date": "20260923", "tm": "153000",
        "pred_close_pric": "276500", "upl_pric": "+359000", "lst_pric": "-194000",
        "flo_stkcnt": "5846279", "cur_prc": "+286500", "flu_rt": "+3.62",
        "pred_rt": "+114.91", "open_pric": "+284500", "high_pric": "+286500",
        "low_pric": "+281000", "trde_qty": "20864376", "trde_prica": "5926487",
        "sel_1bid": "+286500", "buy_1bid": "+286000",
        "sel_1bid_req": "97775", "buy_1bid_req": "42115",
        "tot_buy_req": "443260", "tot_sel_req": "489605",
    }
    out = summarize_quote(quote, stock_code="005930")

    assert out["price"] == 286_500
    assert out["change_pct"] == 3.62
    assert out["lower_limit"] == 194_000
    assert out["upper_limit_distance_pct"] == 25.31
    assert out["lower_limit_distance_pct"] == 32.29
    assert out["spread_pct"] == 0.175
    assert out["orderbook_ratio"] == 0.91
    assert out["market_cap_krw"] == 286_500 * 5_846_279 * 1000
    assert out["asks"] == [{"price": 286_500, "quantity": 97_775}]
    assert out["as_of"] == "20260923 153000"


def test_quote_summary_survives_an_empty_payload():
    out = summarize_quote({}, stock_code="005930")

    assert out["price"] is None
    assert out["market_cap_krw"] is None
    assert out["orderbook_ratio"] is None
    assert out["bids"] == [] and out["asks"] == []
