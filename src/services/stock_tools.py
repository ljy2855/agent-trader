"""Compact per-stock views for the agents: one quote, one daily-bar series.

The agents are told to re-check price, orderbook, volume and the MA20 before
judging a holding or a candidate. Until 2026-09-27 no tool fit that job. The
evaluator invented eight tool names (`get_stock_daily_bars`, `get_stock_ohlcv`,
`get_stock_chart`, ...) thirteen times, then scraped Naver's chart API and ran
into Yahoo's rate limit. `get_market_snapshot` did carry a quote, but buried in
leaderboards and sector tables, and with five daily bars — too few for the MA20
the whole strategy is built on.

Both summaries reuse the strategy's own helpers, so an agent checking MA20 gets
the number the watcher scored with rather than a second opinion.
"""

from __future__ import annotations

from typing import Any

from .entry_rules import moving_average_discount
from .strategy import (
    VOLUME_AVERAGE_DAYS,
    _to_int,
    _to_ratio,
    limit_distance_pct,
    moving_average,
    to_price,
    volume_ratio_vs_average,
)

ORDERBOOK_LEVELS = 5


def _round(value: float | None, digits: int = 2) -> float | None:
    return round(value, digits) if value is not None else None


def summarize_quote(quote: dict[str, Any], *, stock_code: str) -> dict[str, Any]:
    """Reduce a ka10007 quote to what a trading judgment reads.

    ka10007 already carries ten orderbook levels, the price limits and the
    listed-share count, so one call covers price, book, limits and market cap.
    """

    price = to_price(quote.get("cur_prc"))
    listed_thousands = _to_int(quote.get("flo_stkcnt"))
    upper = to_price(quote.get("upl_pric"))
    lower = to_price(quote.get("lst_pric"))
    best_bid = to_price(quote.get("buy_1bid"))
    best_ask = to_price(quote.get("sel_1bid"))
    total_bid = _to_int(quote.get("tot_buy_req"))
    total_ask = _to_int(quote.get("tot_sel_req"))

    def levels(side: str) -> list[dict[str, int | None]]:
        rows = []
        for i in range(1, ORDERBOOK_LEVELS + 1):
            level_price = to_price(quote.get(f"{side}_{i}bid"))
            if not level_price:
                continue
            rows.append(
                {"price": level_price, "quantity": _to_int(quote.get(f"{side}_{i}bid_req"))}
            )
        return rows

    spread_pct = None
    if best_bid and best_ask and best_bid > 0:
        spread_pct = (best_ask - best_bid) / best_bid * 100

    return {
        "stock_code": stock_code,
        "stock_name": quote.get("stk_nm") or stock_code,
        "as_of": " ".join(str(quote.get(k) or "") for k in ("date", "tm")).strip() or None,
        "price": price,
        "change_pct": _to_ratio(quote.get("flu_rt")),
        "prev_close": to_price(quote.get("pred_close_pric")),
        "open": to_price(quote.get("open_pric")),
        "high": to_price(quote.get("high_pric")),
        "low": to_price(quote.get("low_pric")),
        "upper_limit": upper,
        "lower_limit": lower,
        "upper_limit_distance_pct": _round(limit_distance_pct(price, upper)),
        "lower_limit_distance_pct": _round(limit_distance_pct(price, lower)),
        "volume": _to_int(quote.get("trde_qty")),
        # 전일 같은 시각이 아니라 전일 하루 전체 대비다 — 장 초반엔 낮게 나온다.
        "volume_vs_prev_day_pct": _to_ratio(quote.get("pred_rt")),
        "trade_value_million_krw": _to_int(quote.get("trde_prica")),
        "market_cap_krw": (
            price * listed_thousands * 1000 if price and listed_thousands else None
        ),
        "best_bid": best_bid,
        "best_ask": best_ask,
        "spread_pct": _round(spread_pct, 3),
        "bids": levels("buy"),
        "asks": levels("sel"),
        "total_bid_quantity": total_bid,
        "total_ask_quantity": total_ask,
        # Same definition the watcher scores with: 매수잔량 / 매도잔량.
        "orderbook_ratio": (
            _round(total_bid / max(total_ask, 1)) if total_bid is not None and total_ask is not None else None
        ),
    }


def summarize_daily_bars(
    bars: list[dict[str, Any]],
    *,
    stock_code: str,
    ma_period: int = 20,
) -> dict[str, Any]:
    """Compact OHLCV rows plus the indicators the skills judge a trend by.

    ``ma_dip_pct`` keeps the watcher's sign: positive means the latest close
    sits that far below the MA. During a session the latest bar is today's,
    so its close is the current price and its volume is partial.
    """

    rows = [
        {
            "date": b.get("date") or b.get("dt"),
            "open": to_price(b.get("open_pric")),
            "high": to_price(b.get("high_pric")),
            "low": to_price(b.get("low_pric")),
            "close": to_price(b.get("close_pric") or b.get("cur_prc")),
            "volume": _to_int(b.get("trde_qty")),
        }
        for b in bars
        if isinstance(b, dict)
    ]

    latest = rows[0] if rows else {}
    prior = rows[1 : VOLUME_AVERAGE_DAYS + 1]
    prior_lows = [r["low"] for r in prior if r.get("low")]
    prior_highs = [r["high"] for r in prior if r.get("high")]
    full_window = len(prior) >= VOLUME_AVERAGE_DAYS
    low_20d = min(prior_lows) if full_window and prior_lows else None
    high_20d = max(prior_highs) if full_window and prior_highs else None

    ma = moving_average(bars, ma_period)
    ma5 = moving_average(bars, 5)
    volume_ratio = volume_ratio_vs_average(bars)
    latest_low = latest.get("low")

    return {
        "stock_code": stock_code,
        "bars": rows,
        "indicators": {
            "latest_date": latest.get("date"),
            "latest_close": latest.get("close"),
            "ma_period": ma_period,
            "ma": _round(ma),
            "ma_dip_pct": _round(moving_average_discount(latest.get("close"), ma)),
            "ma5": _round(ma5),
            "volume_ratio_20d": _round(volume_ratio),
            "prior_20d_low": low_20d,
            "prior_20d_high": high_20d,
            # 저점 갱신: 오늘 저가가 직전 20거래일 최저가 아래로 내려갔는가.
            "new_20d_low": (
                bool(latest_low and low_20d and latest_low < low_20d)
                if low_20d is not None
                else None
            ),
        },
    }


__all__ = ["summarize_daily_bars", "summarize_quote"]
