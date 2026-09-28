"""Does a dip with company news behave differently from a dip without it?

The live strategy buys a shallow pullback below MA20 on the premise that the
business has not changed and the price will come back. Studies of large
price moves say the premise holds only when the move carries no information:
moves with public news tend to continue, moves without it tend to reverse
(Chan 2003; Savor 2012 — found mostly in small stocks, so whether it holds
for this large-cap roster is exactly what is being asked).

Design — fixed before any return was computed:

- Universe and prices: the roster's daily-bar cache (``backtest/cache``).
- Signal: the live below_ma band on the close of day t (MA20 including that
  close, 0 < dip <= 5%). The unit is the **episode start**, the first band day
  after a day outside it, so a stock sitting in the band for a week counts
  once. All band days are reported as a secondary view.
- News: a filing that `src.services.disclosures.classify_disclosure` puts in
  EARNINGS or EVENT (rules fixed from filing names alone), dated
  ``date(t-5) <= D < date(t)``: the five sessions before the signal day,
  weekends and holidays in between included, the signal day itself excluded.
  DART dates carry no time, so a filing dated t may have come after the
  close; a secondary window that includes day t is shown with that caveat.
- Outcome: return from the close of t to the close of t+h minus the roster's
  equal-weighted return over the same span, h = 1, 5, 10. **Primary: h = 5.**
- Idiosyncratic dip: the stock's return over t-5..t minus the roster's, split
  at the median of the signal set — "fell alone" against "fell with the
  market". This is what the new trigger field measures live.
- Uncertainty: bootstrap over calendar months (each draw resamples whole
  months), because signals on the same days — and 5- or 10-day windows on
  neighbouring days — are not independent. ``z`` is the difference over its
  bootstrap standard error; with this many cells, a pure null already
  produces a largest |z| around ``expected_max_abs_t``.

Primary hypothesis: episode starts preceded by news have a lower 5-day excess
return than those without (difference news − no news < 0).
"""

from __future__ import annotations

import bisect
import random
import statistics as st
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Iterable

from src.services.disclosures import EARNINGS, EVENT, classify_disclosure

from .engine import Params, _entry_signal, normalize_rows
from .ic import expected_max_abs_t

HORIZONS = (1, 5, 10)
PRIMARY_HORIZON = 5
NEWS_LOOKBACK_SESSIONS = 5
IDIOSYNCRATIC_LOOKBACK = 5
_SIGNAL = Params(entry_mode="below_ma", ma_period=20)


@dataclass
class Observation:
    code: str
    day: str
    episode_start: bool
    news_before: bool
    news_incl_day: bool
    earnings_before: bool
    event_before: bool
    trailing_excess: float | None
    excess: dict[int, float] = field(default_factory=dict)

    @property
    def month(self) -> str:
        return self.day[:6]


def filing_dates(
    disclosures: dict[str, list[dict[str, Any]]], categories: Iterable[str]
) -> dict[str, list[str]]:
    """Sorted filing dates per stock code, for filings in ``categories``."""

    wanted = frozenset(categories)
    out: dict[str, list[str]] = {}
    for code, rows in disclosures.items():
        out[code] = sorted(
            str(row.get("rcept_dt"))
            for row in rows
            if row.get("rcept_dt") and classify_disclosure(row.get("report_nm")) in wanted
        )
    return out


def any_filing(dates: list[str], start: str, end: str, *, include_end: bool) -> bool:
    """Is there a date in [start, end) — or [start, end] with ``include_end``?"""

    lo = bisect.bisect_left(dates, start)
    hi = bisect.bisect_right(dates, end) if include_end else bisect.bisect_left(dates, end)
    return hi > lo


def episode_starts(flags: list[bool]) -> list[bool]:
    """True where a signal fires and the previous bar did not."""

    return [flag and (i == 0 or not flags[i - 1]) for i, flag in enumerate(flags)]


def build_observations(
    series: dict[str, list[dict[str, Any]]],
    disclosures: dict[str, list[dict[str, Any]]],
) -> list[Observation]:
    rows_by_code = {code: normalize_rows(bars) for code, bars in series.items()}
    closes = {code: {r["d"]: r["c"] for r in rows} for code, rows in rows_by_code.items()}
    sessions = sorted({d for c in closes.values() for d in c})
    pos = {d: i for i, d in enumerate(sessions)}
    news = filing_dates(disclosures, (EARNINGS, EVENT))
    earnings = filing_dates(disclosures, (EARNINGS,))
    events = filing_dates(disclosures, (EVENT,))

    def span_returns(d0: str, d1: str) -> dict[str, float]:
        out = {}
        for code, c in closes.items():
            if d0 in c and d1 in c and c[d0] > 0:
                out[code] = c[d1] / c[d0] - 1
        return out

    cache: dict[tuple[str, str], dict[str, float]] = {}

    def returns(d0: str, d1: str) -> dict[str, float]:
        if (d0, d1) not in cache:
            cache[(d0, d1)] = span_returns(d0, d1)
        return cache[(d0, d1)]

    def excess(code: str, d0: str, d1: str) -> float | None:
        r = returns(d0, d1)
        if code not in r or len(r) < 10:
            return None
        return (r[code] - st.mean(r.values())) * 100

    observations: list[Observation] = []
    for code, rows in rows_by_code.items():
        if code not in disclosures:
            continue  # no filing history fetched — cannot tell news from none
        flags = [_entry_signal(rows, i, _SIGNAL) for i in range(len(rows))]
        starts = episode_starts(flags)
        for i, fired in enumerate(flags):
            if not fired:
                continue
            day = rows[i]["d"]
            t = pos[day]
            if t < max(NEWS_LOOKBACK_SESSIONS, IDIOSYNCRATIC_LOOKBACK):
                continue
            window_start = sessions[t - NEWS_LOOKBACK_SESSIONS]
            obs = Observation(
                code=code,
                day=day,
                episode_start=starts[i],
                news_before=any_filing(news.get(code, []), window_start, day, include_end=False),
                news_incl_day=any_filing(news.get(code, []), window_start, day, include_end=True),
                earnings_before=any_filing(earnings.get(code, []), window_start, day, include_end=False),
                event_before=any_filing(events.get(code, []), window_start, day, include_end=False),
                trailing_excess=excess(code, sessions[t - IDIOSYNCRATIC_LOOKBACK], day),
            )
            for h in HORIZONS:
                if t + h < len(sessions):
                    value = excess(code, day, sessions[t + h])
                    if value is not None:
                        obs.excess[h] = value
            observations.append(obs)
    return observations


def month_bootstrap_diff(
    observations: list[Observation],
    in_group,
    horizon: int,
    *,
    draws: int = 2000,
    seed: int = 20260928,
) -> dict[str, Any] | None:
    """Mean excess in and out of a group, and their difference, month-clustered."""

    by_month: dict[str, list[tuple[bool, float]]] = defaultdict(list)
    for obs in observations:
        if horizon in obs.excess:
            by_month[obs.month].append((bool(in_group(obs)), obs.excess[horizon]))
    months = sorted(by_month)
    pooled = [pair for m in months for pair in by_month[m]]
    yes = [v for g, v in pooled if g]
    no = [v for g, v in pooled if not g]
    if len(yes) < 10 or len(no) < 10 or len(months) < 6:
        return None
    diff = st.mean(yes) - st.mean(no)
    rng = random.Random(seed)
    samples: list[float] = []
    for _ in range(draws):
        drawn = [pair for _ in months for pair in by_month[months[rng.randrange(len(months))]]]
        a = [v for g, v in drawn if g]
        b = [v for g, v in drawn if not g]
        if a and b:
            samples.append(st.mean(a) - st.mean(b))
    samples.sort()
    se = st.stdev(samples) if len(samples) > 1 else float("nan")
    return {
        "n_yes": len(yes),
        "n_no": len(no),
        "mean_yes": round(st.mean(yes), 3),
        "mean_no": round(st.mean(no), 3),
        "diff": round(diff, 3),
        "ci_low": round(samples[int(len(samples) * 0.025)], 3),
        "ci_high": round(samples[int(len(samples) * 0.975)], 3),
        "z": round(diff / se, 2) if se and se == se else None,
        "months": len(months),
    }


def run_study(
    series: dict[str, list[dict[str, Any]]],
    disclosures: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    observations = build_observations(series, disclosures)
    episodes = [o for o in observations if o.episode_start]
    trailing = sorted(o.trailing_excess for o in episodes if o.trailing_excess is not None)
    median_trailing = trailing[len(trailing) // 2] if trailing else 0.0

    def fell_alone(o: Observation) -> bool:
        return o.trailing_excess is not None and o.trailing_excess < median_trailing

    splits = {
        "news_before (1차)": (episodes, lambda o: o.news_before),
        "earnings_before": (episodes, lambda o: o.earnings_before),
        "event_before": (episodes, lambda o: o.event_before),
        "news_incl_day (당일 포함)": (episodes, lambda o: o.news_incl_day),
        "news_before · 모든 밴드일": (observations, lambda o: o.news_before),
        "fell_alone (혼자 더 빠짐)": (
            [o for o in episodes if o.trailing_excess is not None],
            fell_alone,
        ),
    }
    report: dict[str, Any] = {
        "episodes": len(episodes),
        "band_days": len(observations),
        "median_trailing_excess": round(median_trailing, 3),
        "splits": {},
    }
    cells = 0
    for name, (obs, group) in splits.items():
        report["splits"][name] = {}
        for h in HORIZONS:
            result = month_bootstrap_diff(obs, group, h)
            report["splits"][name][h] = result
            cells += result is not None
    report["cells"] = cells
    report["expected_max_abs_t"] = round(expected_max_abs_t(cells), 2)

    # 2x2 at the primary horizon: does news matter differently for a dip the
    # stock took alone versus one it took with the market?
    table: dict[str, dict[str, Any]] = {}
    for news_label, news_flag in (("news", True), ("no_news", False)):
        for dip_label, alone in (("fell_alone", True), ("fell_with_market", False)):
            values = [
                o.excess[PRIMARY_HORIZON]
                for o in episodes
                if o.trailing_excess is not None
                and PRIMARY_HORIZON in o.excess
                and o.news_before == news_flag
                and fell_alone(o) == alone
            ]
            table[f"{news_label}·{dip_label}"] = {
                "n": len(values),
                "mean": round(st.mean(values), 3) if values else None,
            }
    report["table_h5"] = table
    return report


__all__ = [
    "HORIZONS",
    "Observation",
    "any_filing",
    "build_observations",
    "episode_starts",
    "filing_dates",
    "month_bootstrap_diff",
    "run_study",
]
