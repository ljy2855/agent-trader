"""Account return against a market index — pure functions, no I/O.

The system had no benchmark of any kind until 2026-09-21. Over 2026-08-21 to
09-18 the account returned +0.12% while KOSPI returned about +6.5%, and
nothing in the dashboard, the digest or the daily wrap showed that gap; it
had to be found by hand. §10.0 predicted exactly this outcome from the
backtest (random entry beat the strategy; long-hold gains were market beta),
so the number that would confirm or refute it deserves to be on the wall.

This is measurement, not a trading input. Nothing here feeds the entry or
exit path.

⚠️ Total-asset history (kt00002) includes deposits and withdrawals — it is
not a P&L series. `src/dashboard.py:_build_asset_series` already says so in
its own note. Treating it as return would have silently reported the
2026-08-07 withdrawal of 500,000 as a -28.5% loss. Two defences here:

1. Returns are **chained day by day**, so an external flow corrupts one
   day rather than the whole window (a start/end comparison spreads it
   across every number).
2. A day whose move is larger than trading could produce is dropped from
   the chain and reported.

Neither is a substitute for a real cash-flow feed, and Kiwoom's catalog has
no deposits/withdrawals history API. A flow smaller than the bound is
indistinguishable from return and will be counted as one — `excluded_days`
and `note` exist so the reader knows the limit rather than trusting a number
that looks exact.
"""

from __future__ import annotations

from typing import Any

# KRX caps a single name at ±30% a day. With position_budget_pct=60 and
# max_positions=1 the account cannot move more than about ±18% on trading
# alone, so ±20% leaves headroom for a config change without ever tripping
# on a real session. It is deliberately loose: a false positive silently
# deletes a real trading day from the comparison, which is worse than
# letting a small flow through, because the flow at least gets reported.
MAX_PLAUSIBLE_DAILY_MOVE_PCT = 20.0


def _as_float(value: Any) -> float | None:
    if value in ("", None):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).replace(",", "").strip()
    if not text:
        return None
    sign = 1.0
    if text[0] == "+":
        text = text[1:]
    elif text[0] == "-":
        sign = -1.0
        text = text[1:]
    try:
        return sign * float(text)
    except ValueError:
        return None


def _normalize_day(value: Any) -> str | None:
    """Return YYYY-MM-DD from either that form or Kiwoom's YYYYMMDD."""

    text = str(value or "").strip()
    if len(text) == 10 and text[4] == "-" and text[7] == "-":
        return text
    if len(text) == 8 and text.isdigit():
        return f"{text[:4]}-{text[4:6]}-{text[6:]}"
    return None


def index_series(bars: list[dict[str, Any]]) -> dict[str, float]:
    """{YYYY-MM-DD: close} from ka20006 rows, rescaled to index points.

    The vendor multiplies index prices by 100 and drops the decimal point:
    KOSPI's 2026-09-18 close of 6894.23 arrives as "689423". Read raw it is
    a hundred times too large, which still plots as a plausible curve and
    only shows up as a wrong return.
    """

    out: dict[str, float] = {}
    for row in bars or []:
        if not isinstance(row, dict):
            continue
        day = _normalize_day(row.get("dt"))
        close = _as_float(row.get("cur_prc"))
        if day and close and close > 0:
            out[day] = close / 100.0
    return out


def account_series(points: list[dict[str, Any]]) -> dict[str, float]:
    """{YYYY-MM-DD: total assets} from the kt00002-derived points."""

    out: dict[str, float] = {}
    for row in points or []:
        if not isinstance(row, dict):
            continue
        day = _normalize_day(row.get("date") or row.get("dt"))
        value = _as_float(row.get("value") or row.get("prsm_dpst_aset_amt"))
        if day and value and value > 0:
            out[day] = value
    return out


def exposure_series(points: list[dict[str, Any]]) -> dict[str, float]:
    """{YYYY-MM-DD: invested fraction of assets}, from total minus cash.

    kt00002 carries `entr` (settled cash) next to the total, so the equity
    share is the remainder.

    ⚠️ `entr` settles on T+2 while the total is marked to market today, so
    inside the settlement window the remainder is only the position's
    *unrealised P&L*, not its value. Measured 2026-08-26: the KB금융 buy
    filled that morning at 165,300 and the day read 1,028원 of exposure —
    the gain, because the purchase was already netted out of the total but
    not yet out of `entr`. The bias therefore **understates** exposure for
    two sessions after a buy and overstates it for two after a sale.

    On this account, shifting the cash leg by one to three sessions moves
    the measured average between 8% and 14% (2026-09-24). That is precise
    enough for its only job — showing that an account holding roughly a
    tenth of its assets cannot be judged against a fully invested index —
    and nowhere near precise enough to be a position report.

    Settlement can also put cash briefly above the total (2026-09-16 read
    -0.1%), so the fraction is clamped into [0, 1] rather than reported as a
    negative holding that does not exist.
    """

    out: dict[str, float] = {}
    for row in points or []:
        if not isinstance(row, dict):
            continue
        day = _normalize_day(row.get("date") or row.get("dt"))
        total = _as_float(row.get("value") or row.get("prsm_dpst_aset_amt"))
        cash = _as_float(row.get("cash") if row.get("cash") is not None
                         else row.get("entr"))
        if day and total and total > 0 and cash is not None:
            out[day] = min(1.0, max(0.0, (total - cash) / total))
    return out


def _chain(returns: list[float]) -> float:
    total = 1.0
    for r in returns:
        total *= 1.0 + r
    return (total - 1.0) * 100.0


# Trailing lengths reported alongside the full window. One window is a
# choice, and the choice can decide the verdict: measured 2026-09-21 on the
# same account, alpha ran from +16.57p over 54 trading days to -10.87p over
# 32, because KOSPI peaked on 2026-06-22 and sold off hard in early August.
# Anyone reading a single number is reading a window someone picked.
TRAILING_WINDOWS = (20, 60)


class _Span:
    """Chained result for one list of days."""

    __slots__ = ("account_pct", "index_pct", "matched_pct", "exposure",
                 "used_days", "excluded")

    def __init__(self, account_pct, index_pct, matched_pct, exposure,
                 used_days, excluded):
        self.account_pct = account_pct
        self.index_pct = index_pct
        self.matched_pct = matched_pct      # index return at the account's exposure
        self.exposure = exposure            # mean invested fraction, or None
        self.used_days = used_days
        self.excluded = excluded


def _measure(
    days: list[str],
    acct: dict[str, float],
    idx: dict[str, float],
    max_daily_move_pct: float,
    expo: dict[str, float] | None = None,
) -> _Span:
    """Chain the legs over the same days, dropping suspected cash flows.

    The third leg is the index return *at the account's own exposure*: each
    day's index move scaled by how much of the account was actually invested
    going into that day. Comparing a mostly-cash account to a fully invested
    index measures the cash position, not the stock picking, so this leg is
    what separates the two.
    """

    acct_returns: list[float] = []
    idx_returns: list[float] = []
    matched_returns: list[float] = []
    exposures: list[float] = []
    excluded: list[dict[str, Any]] = []

    for prev, cur in zip(days, days[1:]):
        a0, a1 = acct[prev], acct[cur]
        i0, i1 = idx[prev], idx[cur]
        if a0 <= 0 or i0 <= 0:
            continue
        a_ret = (a1 - a0) / a0
        if abs(a_ret) * 100.0 > max_daily_move_pct:
            # Larger than trading can produce, so almost certainly a deposit
            # or withdrawal. Drop the index leg for the same day too — the
            # comparison is only meaningful over identical spans.
            excluded.append(
                {
                    "date": cur,
                    "change_pct": round(a_ret * 100.0, 2),
                    "reason": "매매로 설명 불가한 급변 — 입출금 추정",
                }
            )
            continue
        i_ret = (i1 - i0) / i0
        acct_returns.append(a_ret)
        idx_returns.append(i_ret)
        if expo is not None and prev in expo:
            # Exposure entering the day is what earns that day's move.
            e = expo[prev]
            exposures.append(e)
            matched_returns.append(i_ret * e)

    return _Span(
        _chain(acct_returns),
        _chain(idx_returns),
        _chain(matched_returns) if matched_returns else None,
        (sum(exposures) / len(exposures)) if exposures else None,
        len(acct_returns),
        excluded,
    )


def build_comparison(
    account_points: list[dict[str, Any]],
    index_bars: list[dict[str, Any]],
    *,
    max_daily_move_pct: float = MAX_PLAUSIBLE_DAILY_MOVE_PCT,
    trailing_windows: tuple[int, ...] = TRAILING_WINDOWS,
) -> dict[str, Any]:
    """Chained account return vs index return over their common days.

    Only days present in both series are used, so a market holiday or a
    gap on either side shortens the window instead of inventing a move
    across it. Both sides are chained over the *same* day list, which is
    what makes the difference an excess return rather than two unrelated
    numbers printed next to each other.

    ``windows`` carries the same measurement over shorter trailing spans,
    because the full window is still one arbitrary choice and this account's
    alpha swings from +16.57p to -10.87p depending on which one is taken.
    Reporting several is what stops a single flattering or alarming span
    from reading as the answer.
    """

    acct = account_series(account_points)
    idx = index_series(index_bars)
    expo = exposure_series(account_points) or None
    days = sorted(set(acct) & set(idx))

    if len(days) < 2:
        return {
            "available": False,
            "reason": (
                f"겹치는 거래일 {len(days)}일 — 비교하려면 2일 이상 필요하다"
            ),
        }

    span = _measure(days, acct, idx, max_daily_move_pct, expo)
    account_pct, index_pct, used_days, excluded = (
        span.account_pct, span.index_pct, span.used_days, span.excluded
    )

    if used_days == 0:
        return {
            "available": False,
            "reason": "비교 가능한 날이 없다 (전부 제외됨)",
            "excluded_days": excluded,
        }

    windows = []
    for length in sorted(set(trailing_windows)):
        if length >= len(days):
            continue
        tail = days[-(length + 1):]
        w = _measure(tail, acct, idx, max_daily_move_pct, expo)
        if w.used_days:
            row = {
                "trading_days": w.used_days,
                "start_date": tail[0],
                "account_return_pct": round(w.account_pct, 2),
                "index_return_pct": round(w.index_pct, 2),
                "alpha_pct": round(w.account_pct - w.index_pct, 2),
            }
            if w.matched_pct is not None:
                row["avg_exposure_pct"] = round(w.exposure * 100.0, 1)
                row["selection_alpha_pct"] = round(
                    w.account_pct - w.matched_pct, 2
                )
            windows.append(row)

    note = (
        "총자산 시계열은 입출금을 포함한다. 일별 수익률을 체인해 한 번의 "
        "입출금이 구간 전체를 오염시키지 않게 했고, 매매로 설명 불가한 "
        f"±{max_daily_move_pct:g}% 초과 급변일은 제외했다. "
        "키움에 입출금 내역 API가 없어 그보다 작은 입출금은 수익률에 섞인다."
    )
    if excluded:
        note += (
            f" 제외 {len(excluded)}일 — 제외일은 지수 쪽에서도 같이 빠지므로"
            " (양쪽이 같은 날을 덮어야 한다) 위 수익률은 index_start·index_end를"
            " 직접 나눈 값과 일치하지 않는다."
        )

    out = {
        "available": True,
        "start_date": days[0],
        "end_date": days[-1],
        "compared_days": used_days,
        "account_return_pct": round(account_pct, 2),
        "index_return_pct": round(index_pct, 2),
        "alpha_pct": round(account_pct - index_pct, 2),
        "index_start": round(idx[days[0]], 2),
        "index_end": round(idx[days[-1]], 2),
        "windows": windows,
        "excluded_days": excluded,
        "note": note,
    }

    if span.matched_pct is not None:
        # Split the headline gap into the part that is simply not being
        # invested and the part that is stock picking. Measured 2026-09-24
        # the account ran ~8% invested, so almost the whole of a -6.9p alpha
        # was the cash, and reading that number as "the picks are bad" would
        # have pointed at the wrong lever.
        out["avg_exposure_pct"] = round(span.exposure * 100.0, 1)
        out["index_return_at_exposure_pct"] = round(span.matched_pct, 2)
        out["cash_drag_pct"] = round(span.matched_pct - index_pct, 2)
        out["selection_alpha_pct"] = round(account_pct - span.matched_pct, 2)
        out["exposure_note"] = (
            f"기간 평균 투자비중 {span.exposure * 100.0:.1f}%. "
            "α는 전액 투자 지수와의 차이라 대기 현금이 그대로 음수로 잡힌다 — "
            f"현금 대기분 {span.matched_pct - index_pct:+.2f}p와 "
            f"종목 선택분 {account_pct - span.matched_pct:+.2f}p로 나눠 읽을 것. "
            "투자비중은 예수금(entr) 기준이고 T+2 정산 동안은 평가손익만 "
            "잡히므로 매수 직후를 과소평가한다 — 분해 비율은 ±1%p 정도 "
            "흔들리지만 어느 쪽 항이 큰지는 바뀌지 않는다."
        )
    return out
