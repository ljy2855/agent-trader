"""Which inputs carry cross-sectional information, and can the account use it?

This is the first step of any signal redesign: before choosing weights you
have to know whether there is anything to weight. The live score was designed
without this step and turned out to have none — `automation/signal_efficacy.py`
measured corr -0.014 against day-demeaned forward returns on 320 live
observations, and the `ma20_dip` feature here reproduces that independently
from daily bars (|t| < 1.6 at every horizon, in all three thirds of a 600-day
sample).

Three measurements, in the order that decides things:

1. **Rank IC** — per session, Spearman correlation between a feature's
   ranking of the roster and the forward return's ranking. Cross-sectional by
   construction, so the market factor cancels; averaging over sessions and
   bootstrapping *by session* keeps correlated names inside a day from
   counting as independent evidence.

2. **Sub-period stability** — the same feature over contiguous thirds. A full
   sample t-stat is what §10.0's PBO/DSR work exists to distrust. Measured
   2026-09-24: `rev_1d` held at t +3.05 / +2.92 / +3.10, while low volatility
   ran t +5.42 / +5.67 / **+0.41** — strong overall and gone in the most
   recent third, which a single number would have hidden.

3. **Basket breadth net of cost** — the part that decided the answer. A KOSPI
   round trip costs 0.23% (0.015% commission each way plus the 0.20% transfer
   tax), and this is where §10.0's "costs eat the edge" reappears:

        top 1  : excess -0.018%/day  (t -0.13)   <- what the live portfolio holds
        top 3  : excess +0.114%/day  (t  1.39)
        top 10 : excess +0.094%/day  (t  2.35)
        top 15 : excess +0.079%/day  (t  2.80)

   The effect is real and it broadens, but **every basket loses to the toll**
   at daily turnover, and the single most extreme name — the only thing a
   one-position account can hold — captures none of it. So the binding
   constraint is the portfolio and the tax, not the scoring formula. A
   redesigned score changes the first column and none of the others.

⚠️ Multiple testing. Every feature x horizon pair is another lottery ticket.
`expected_max_abs_t` is printed beside the results for the same reason
`significance` deflates a Sharpe: with 56 cells, the largest |t| under a pure
null is already about 2.8.

⚠️ The roster carries survivorship bias (see src/constants/universe.py), so
these are relative statements about a fixed pool, not clean historical
estimates.
"""

from __future__ import annotations

import math
import random
import statistics as st
from typing import Any, Callable, Iterable, Sequence

# 0.015% commission each way + 0.20% KOSPI transfer tax on the sell.
ROUND_TRIP_COST_PCT = 0.23

Feature = Callable[[str, str], float | None]


def spearman(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    """Rank correlation, ties averaged. None when the sample is too thin."""

    n = len(xs)
    if n < 6 or n != len(ys):
        return None

    def ranks(values: Sequence[float]) -> list[float]:
        order = sorted(range(n), key=lambda i: values[i])
        out = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and values[order[j + 1]] == values[order[i]]:
                j += 1
            shared = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                out[order[k]] = shared
            i = j + 1
        return out

    rx, ry = ranks(xs), ranks(ys)
    mx, my = st.mean(rx), st.mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) ** 0.5) * (
        sum((b - my) ** 2 for b in ry) ** 0.5
    )
    return num / den if den else None


def daily_ic(
    feature: Feature,
    forward: Callable[[str, str, int], float | None],
    codes: Iterable[str],
    sessions: Sequence[str],
    horizon: int,
    min_names: int = 10,
) -> list[float]:
    """One rank IC per session — the unit of evidence for everything below."""

    codes = list(codes)
    out: list[float] = []
    for i, day in enumerate(sessions):
        if i + horizon >= len(sessions):
            continue
        xs: list[float] = []
        ys: list[float] = []
        for code in codes:
            f = feature(code, day)
            r = forward(code, day, horizon)
            if f is not None and r is not None:
                xs.append(f)
                ys.append(r)
        if len(xs) >= min_names:
            ic = spearman(xs, ys)
            if ic is not None:
                out.append(ic)
    return out


def summarize_ic(
    ics: Sequence[float], draws: int = 3000, seed: int = 20260924
) -> dict[str, Any] | None:
    """Mean IC with a session-blocked bootstrap interval and a t-stat."""

    if len(ics) < 30:
        return None
    mean = st.mean(ics)
    sd = st.stdev(ics)
    # Dispersion that is zero — or only floating-point residue away from it —
    # has no t-stat. Both wrong answers are available here: dividing by an
    # exact 0 guard reports t=0.0, which reads as "nothing here", while the
    # residue that Spearman actually leaves (1.0 vs 0.9999999999999999) gives
    # t = 2.8e17, which reads as overwhelming proof. A feature whose per
    # session IC never varies is mis-wired, not miraculous, so say there is
    # no t and let the degenerate interval carry the mean.
    degenerate = sd <= max(abs(mean), 1.0) * 1e-12
    t = None if (degenerate and mean) else (
        0.0 if degenerate else mean / (sd / math.sqrt(len(ics)))
    )
    rng = random.Random(seed)
    n = len(ics)
    means = sorted(
        st.mean(ics[rng.randrange(n)] for _ in range(n)) for _ in range(draws)
    )
    return {
        "sessions": n,
        "mean_ic": round(mean, 4),
        "t": None if t is None else round(t, 2),
        "ci_low": round(means[int(draws * 0.025)], 4),
        "ci_high": round(means[int(draws * 0.975)], 4),
    }


def expected_max_abs_t(n_tests: int) -> float:
    """Largest |t| a pure null would produce across n independent cells.

    The bar a result has to clear before it is worth a second look. Without
    it, 56 cells produce two or three "significant" findings by construction.
    """

    return math.sqrt(2 * math.log(n_tests)) if n_tests > 1 else 0.0


def subperiod_ics(
    feature: Feature,
    forward: Callable[[str, str, int], float | None],
    codes: Iterable[str],
    sessions: Sequence[str],
    horizon: int,
    parts: int = 3,
) -> list[dict[str, Any]]:
    """The same measurement over contiguous, non-overlapping slices."""

    codes = list(codes)
    n = len(sessions)
    out: list[dict[str, Any]] = []
    for p in range(parts):
        lo, hi = n * p // parts, n * (p + 1) // parts
        window = sessions[lo:hi]
        ics = daily_ic(feature, forward, codes, window, horizon)
        row: dict[str, Any] = {
            "start": window[0] if window else None,
            "end": window[-1] if window else None,
        }
        row.update(summarize_ic(ics) or {"sessions": len(ics), "mean_ic": None})
        out.append(row)
    return out


def basket_excess(
    feature: Feature,
    forward: Callable[[str, str, int], float | None],
    codes: Iterable[str],
    sessions: Sequence[str],
    horizon: int,
    top_n: int,
    min_names: int = 20,
) -> dict[str, Any] | None:
    """Top-N basket return minus the equal-weighted universe, per holding.

    Excess over the same universe on the same days, because §10.0 established
    that raw returns over this sample mostly re-measure a bull market: a
    60-day hold showed +3.79% while random entry showed +4.01%.

    Holdings are non-overlapping, so `net_pct` charges the round trip once
    per holding rather than pretending a position is free to roll.
    """

    codes = list(codes)
    excess: list[float] = []
    for i in range(0, len(sessions) - horizon, horizon):
        day = sessions[i]
        rows: list[tuple[float, float]] = []
        for code in codes:
            f = feature(code, day)
            r = forward(code, day, horizon)
            if f is not None and r is not None:
                rows.append((f, r))
        if len(rows) < min_names:
            continue
        rows.sort(key=lambda row: -row[0])
        picked = [r for _, r in rows[:top_n]]
        excess.append(st.mean(picked) - st.mean(r for _, r in rows))
    if len(excess) < 25:
        return None
    mean = st.mean(excess)
    sd = st.stdev(excess)
    return {
        "top_n": top_n,
        "horizon": horizon,
        "holdings": len(excess),
        "excess_pct": round(mean, 3),
        "net_pct": round(mean - ROUND_TRIP_COST_PCT, 3),
        "t": round(mean / (sd / math.sqrt(len(excess))), 2) if sd else 0.0,
    }


__all__ = [
    "ROUND_TRIP_COST_PCT",
    "basket_excess",
    "daily_ic",
    "expected_max_abs_t",
    "spearman",
    "subperiod_ics",
    "summarize_ic",
]
