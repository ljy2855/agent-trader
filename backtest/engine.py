"""Pure backtest engine — no I/O, fully unit-testable.

The simulation models the strategy's entry/exit rules on daily OHLC:

- **Entry**: momentum uses the close-vs-prevclose change band; below_ma
  uses the live shallow-discount band and an MA including the signal close.
  The optional crossover variant is separate research, not the live rule.
  Fill at the NEXT day's open. Market-cap is assumed satisfied because the
  universe is pre-filtered; historical constituents are not reconstructed.
- **Exit**, scanning each held day's OHLC:
  - opening gaps execute at the open, not an unreachable stop/target
  - stop-loss: low <= entry * (1 + stop_loss_pct/100) → fill at the stop
  - take-profit: high >= entry * (1 + take_profit_pct/100) → fill at the target
  - if both touch the same day, assume STOP fills first (conservative — we
    can't see intrabar order on daily data)
  - otherwise after max_hold_days, exit at that day's close
- **Costs**: adverse per-side slippage, buy fee on entry, sell fee and tax
  on exit proceeds. Rates are fixed scenario assumptions, not a tax history.

A trade's return is net of costs. Expectancy/win-rate/payoff/MDD are derived
from the trade list.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from math import isfinite

from src.services.entry_rules import BELOW_MA_MAX_DIP_PCT, is_shallow_dip


@dataclass
class Params:
    day_change_min: float = 0.5
    day_change_max: float = 10.0
    stop_loss_pct: float = -2.5
    take_profit_pct: float = 5.0
    max_hold_days: int = 3
    # Entry signal:
    #   "momentum"        — prev-close change in [day_change_min, max]
    #   "below_ma"        — close < MA(ma_period) * (1 - ma_discount_pct/100)
    #                        ("저렴해질 때" — 이동평균 아래로 눌렸을 때 매수)
    #   "drop_from_high"  — close <= rolling N-day high * (1 - drop_from_high_pct/100)
    entry_mode: str = "momentum"
    ma_period: int = 20
    ma_discount_pct: float = 0.0   # below_ma: 이평 대비 추가 할인 요구
    ma_max_dip_pct: float = BELOW_MA_MAX_DIP_PCT
    ma_entry_style: str = "band"
    high_lookback: int = 20
    drop_from_high_pct: float = 5.0
    fee_pct: float = 0.015
    tax_pct: float = 0.20
    slippage_bps: float = 0.0

    def __post_init__(self) -> None:
        if self.entry_mode not in {"momentum", "below_ma", "drop_from_high"}:
            raise ValueError("unsupported entry_mode")
        if self.ma_entry_style not in {"band", "crossover"}:
            raise ValueError("ma_entry_style must be band or crossover")
        if min(self.ma_period, self.high_lookback, self.max_hold_days) < 1:
            raise ValueError("lookbacks and max_hold_days must be positive")
        numeric = (
            self.day_change_min, self.day_change_max, self.stop_loss_pct,
            self.take_profit_pct, self.ma_discount_pct, self.ma_max_dip_pct,
            self.fee_pct, self.tax_pct, self.slippage_bps,
        )
        if not all(isfinite(value) for value in numeric):
            raise ValueError("parameters must be finite")
        if not -100 < self.stop_loss_pct < 0 or self.take_profit_pct <= 0:
            raise ValueError("invalid stop/take thresholds")
        if not 0 <= self.ma_discount_pct < self.ma_max_dip_pct < 100:
            raise ValueError("invalid MA discount band")
        if min(self.fee_pct, self.tax_pct, self.slippage_bps) < 0 or self.slippage_bps >= 10000:
            raise ValueError("invalid transaction costs")


@dataclass
class Trade:
    code: str
    entry_date: str
    entry_price: float
    exit_date: str
    exit_price: float
    reason: str  # "stop" | "take" | "max_hold"
    gross_pct: float
    net_pct: float  # after costs


@dataclass
class Result:
    trades: list[Trade] = field(default_factory=list)

    @property
    def n(self) -> int:
        return len(self.trades)

    def summary(self) -> dict:
        """Trade statistics; chained full-notional returns are not portfolio equity."""
        if not self.trades:
            return {"trades": 0}
        nets = [t.net_pct for t in self.trades]
        wins = [x for x in nets if x > 0]
        losses = [x for x in nets if x <= 0]
        # simple (non-compounded) sum of pct returns, and compounded equity
        equity = 1.0
        peak = 1.0
        mdd = 0.0
        for x in nets:
            equity *= 1 + x / 100
            peak = max(peak, equity)
            mdd = min(mdd, equity / peak - 1)
        avg_win = sum(wins) / len(wins) if wins else 0.0
        avg_loss = sum(losses) / len(losses) if losses else 0.0
        win_rate = len(wins) / len(nets)
        expectancy = sum(nets) / len(nets)
        by_reason: dict[str, int] = {}
        for t in self.trades:
            by_reason[t.reason] = by_reason.get(t.reason, 0) + 1
        return {
            "return_basis": "sequential_full_notional_trade_proxy_not_account_equity",
            "trades": len(nets),
            "win_rate_pct": round(win_rate * 100, 1),
            "expectancy_pct": round(expectancy, 3),
            "avg_win_pct": round(avg_win, 2),
            "avg_loss_pct": round(avg_loss, 2),
            "payoff": round(avg_win / abs(avg_loss), 2) if avg_loss else None,
            "total_return_pct": round((equity - 1) * 100, 1),
            "max_drawdown_pct": round(mdd * 100, 1),
            "exits": by_reason,
        }


def _f(v) -> float | None:
    try:
        s = str(v).replace("+", "").strip()
        value = abs(float(s))
        return value if isfinite(value) and value > 0 else None
    except (TypeError, ValueError):
        return None


def _entry_signal(rows: list[dict], i: int, p: Params) -> bool:
    """True if an entry fires at bar ``i`` (filled next day's open).

    ``rows`` is normalized chronological OHLC. Modes:
      momentum       — prev-close change in band (chase strength)
      below_ma       — close pressed below its MA (저렴해질 때 매수 = mean-reversion)
      drop_from_high — close pulled back from a recent rolling high
    """
    mode = p.entry_mode
    if mode == "momentum":
        prev_c = rows[i - 1]["c"]
        chg = (rows[i]["c"] - prev_c) / prev_c * 100 if prev_c else 0.0
        return p.day_change_min <= chg <= p.day_change_max
    if mode == "below_ma":
        if p.ma_entry_style == "band":
            if i < p.ma_period - 1:
                return False
            average = sum(row["c"] for row in rows[i - p.ma_period + 1:i + 1]) / p.ma_period
            return is_shallow_dip(
                rows[i]["c"], average,
                minimum_pct=p.ma_discount_pct, maximum_pct=p.ma_max_dip_pct,
            )
        if i <= p.ma_period:
            return False
        ma = sum(rows[k]["c"] for k in range(i - p.ma_period, i)) / p.ma_period
        thresh = ma * (1 - p.ma_discount_pct / 100)
        prev_ma = sum(rows[k]["c"] for k in range(i - 1 - p.ma_period, i - 1)) / p.ma_period
        return rows[i]["c"] < thresh and rows[i - 1]["c"] >= prev_ma * (1 - p.ma_discount_pct / 100)
    if mode == "drop_from_high":
        if i < p.high_lookback:
            return False
        hh = max(rows[k]["h"] for k in range(i - p.high_lookback, i + 1))
        return rows[i]["c"] <= hh * (1 - p.drop_from_high_pct / 100)
    return False


def normalize_rows(bars: list[dict]) -> list[dict]:
    """Kiwoom bar dicts → chronological ``{d,o,h,l,c}`` rows (bad rows dropped)."""
    rows = []
    for b in bars:
        o, h, l = _f(b.get("open_pric")), _f(b.get("high_pric")), _f(b.get("low_pric"))
        c = _f(b.get("cur_prc") if b.get("cur_prc") is not None else b.get("close_pric"))
        d = str(b.get("dt") or b.get("date") or "")
        if None in (o, h, l, c) or not d:
            continue
        rows.append({"d": d, "o": o, "h": h, "l": l, "c": c})
    rows.sort(key=lambda r: r["d"])
    return rows


def simulate_exits(
    code: str,
    rows: list[dict],
    p: Params,
    entry_fn: Callable[[list[dict], int], bool],
    *,
    entry_start_date: str | None = None,
) -> list[Trade]:
    """Walk ``rows``, opening a trade wherever ``entry_fn`` fires, and apply
    the stop/take/max-hold exit rules.

    Split out from ``backtest_symbol`` so alternative entry rules — notably
    the random-entry null model in ``validate.random_entry_null`` — reuse
    the *exact* exit path. If the control model reimplemented these rules,
    any divergence would silently corrupt the strategy-vs-null comparison
    it exists to make.
    """
    slippage = p.slippage_bps / 10000
    trades: list[Trade] = []
    i = 1
    n = len(rows)
    while i < n - 1:
        if entry_start_date is not None and rows[i + 1]["d"] < entry_start_date:
            i += 1
            continue
        if not entry_fn(rows, i):
            i += 1
            continue
        # entry at next day's open
        entry = rows[i + 1]["o"] * (1 + slippage)
        entry_date = rows[i + 1]["d"]
        stop_px = entry * (1 + p.stop_loss_pct / 100)
        take_px = entry * (1 + p.take_profit_pct / 100)
        exit_px = exit_date = reason = None
        for j in range(i + 1, min(i + 1 + p.max_hold_days, n)):
            bar = rows[j]
            if bar["o"] <= stop_px:
                exit_px, exit_date, reason = bar["o"], bar["d"], "stop"
                break
            if bar["o"] >= take_px:
                exit_px, exit_date, reason = bar["o"], bar["d"], "take"
                break
            hit_stop = bar["l"] <= stop_px
            hit_take = bar["h"] >= take_px
            if hit_stop:  # conservative: stop fills first on same-day double-touch
                exit_px, exit_date, reason = stop_px, bar["d"], "stop"
                break
            if hit_take:
                exit_px, exit_date, reason = take_px, bar["d"], "take"
                break
        if exit_px is None:  # max-hold close-out
            j = min(i + p.max_hold_days, n - 1)
            exit_px, exit_date, reason = rows[j]["c"], rows[j]["d"], "max_hold"
        exit_px *= 1 - slippage
        gross = (exit_px - entry) / entry * 100
        net = (exit_px * (1 - (p.fee_pct + p.tax_pct) / 100) / (entry * (1 + p.fee_pct / 100)) - 1) * 100
        trades.append(Trade(code, entry_date, entry, exit_date, exit_px, reason, round(gross, 3), round(net, 3)))
        # resume after the exit bar (no overlapping positions)
        i = max(j + 1, i + 1)
    return trades


def backtest_symbol(
    code: str, bars: list[dict], p: Params, *, entry_start_date: str | None = None
) -> list[Trade]:
    """Run the entry/exit rules over one symbol's daily bars.

    ``bars`` must be chronological (oldest first), each with
    open_pric/high_pric/low_pric and close (cur_prc). Overlapping positions
    are not opened — once in a trade, new entries wait until it closes.
    """
    rows = normalize_rows(bars)
    return simulate_exits(
        code, rows, p, lambda rows, index: _entry_signal(rows, index, p),
        entry_start_date=entry_start_date,
    )


def run_backtest(
    series: dict[str, list[dict]], p: Params, *, entry_start_date: str | None = None
) -> Result:
    """Backtest a universe: {code: [bars]} → aggregated Result."""
    res = Result()
    for code, bars in series.items():
        res.trades.extend(backtest_symbol(code, bars, p, entry_start_date=entry_start_date))
    res.trades.sort(key=lambda t: t.entry_date)
    return res
