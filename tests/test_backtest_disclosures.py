"""The dip-with-news study: windows, episodes and the clustered comparison."""

from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backtest.disclosures import (  # noqa: E402
    Observation,
    any_filing,
    build_observations,
    episode_starts,
    filing_dates,
    month_bootstrap_diff,
)
from src.services.disclosures import EARNINGS, EVENT  # noqa: E402


def test_filing_window_includes_its_start_and_excludes_its_end_unless_asked():
    dates = ["20250103", "20250106", "20250110"]

    assert any_filing(dates, "20250103", "20250106", include_end=False)
    assert not any_filing(dates, "20250104", "20250106", include_end=False)
    assert any_filing(dates, "20250104", "20250106", include_end=True)
    assert not any_filing([], "20250101", "20251231", include_end=True)


def test_episode_starts_mark_only_the_first_day_of_a_run():
    assert episode_starts([False, True, True, False, True]) == [False, True, False, False, True]
    assert episode_starts([True, True]) == [True, False]


def test_filing_dates_keep_only_the_wanted_categories_sorted():
    rows = {
        "005930": [
            {"rcept_dt": "20250310", "report_nm": "단일판매ㆍ공급계약체결"},
            {"rcept_dt": "20250105", "report_nm": "영업(잠정)실적(공정공시)"},
            {"rcept_dt": "20250106", "report_nm": "기업설명회(IR)개최(안내공시)"},
        ]
    }

    assert filing_dates(rows, (EARNINGS, EVENT)) == {"005930": ["20250105", "20250310"]}
    assert filing_dates(rows, (EARNINGS,)) == {"005930": ["20250105"]}


def _flat_series(days=30, codes=12, dip_code="000001"):
    """Flat prices at 100; one code steps down to 98 on day 25, into the MA20 band."""

    base = date(2026, 1, 1)
    dates = [(base + timedelta(days=i)).strftime("%Y%m%d") for i in range(days)]
    series = {}
    for k in range(codes):
        code = f"{k:06d}"
        closes = [100.0] * days
        if code == dip_code:
            closes = [100.0] * 25 + [98.0] * (days - 25)
        series[code] = [
            {"dt": d, "open_pric": str(c), "high_pric": str(c), "low_pric": str(c), "cur_prc": str(c)}
            for d, c in zip(dates, closes)
        ]
    return series, dates


def _episode(series, filings):
    (obs,) = [o for o in build_observations(series, filings) if o.episode_start]
    return obs


def test_news_window_ends_before_the_signal_day():
    """A filing dated on the signal day may have come after the close: not 'before'."""

    series, dates = _flat_series()
    filings = {code: [] for code in series}

    filings["000001"] = [
        {"rcept_dt": dates[24], "report_nm": "연결재무제표기준영업(잠정)실적(공정공시)"}
    ]
    obs = _episode(series, filings)
    assert obs.day == dates[25]
    assert obs.news_before and obs.earnings_before and not obs.event_before

    filings["000001"] = [{"rcept_dt": dates[25], "report_nm": "단일판매ㆍ공급계약체결"}]
    obs = _episode(series, filings)
    assert not obs.news_before and obs.news_incl_day

    filings["000001"] = [{"rcept_dt": dates[24], "report_nm": "기업설명회(IR)개최(안내공시)"}]
    obs = _episode(series, filings)
    assert not obs.news_before and not obs.news_incl_day


def _obs(day, in_group, value):
    o = Observation(
        code="x",
        day=day,
        episode_start=True,
        news_before=in_group,
        news_incl_day=in_group,
        earnings_before=False,
        event_before=False,
        trailing_excess=None,
    )
    o.excess[5] = value
    return o


def test_month_bootstrap_reports_the_group_difference_reproducibly():
    obs = []
    for month in range(1, 9):
        for k in range(3):
            obs.append(_obs(f"2025{month:02d}{k + 1:02d}", True, 1.0 + 0.1 * k))
            obs.append(_obs(f"2025{month:02d}{k + 10:02d}", False, 0.1 * k))

    result = month_bootstrap_diff(obs, lambda o: o.news_before, 5, draws=300)

    assert (result["n_yes"], result["n_no"], result["months"]) == (24, 24, 8)
    assert result["diff"] == 1.0
    assert result["ci_low"] <= 1.0 <= result["ci_high"]
    assert result == month_bootstrap_diff(obs, lambda o: o.news_before, 5, draws=300)


def test_month_bootstrap_declines_a_thin_group():
    obs = [_obs("20250101", True, 1.0)] * 5 + [_obs(f"2025{m:02d}01", False, 0.0) for m in range(1, 13)] * 5

    assert month_bootstrap_diff(obs, lambda o: o.news_before, 5) is None
