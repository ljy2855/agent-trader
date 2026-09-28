#!/usr/bin/env python3
"""Does the live entry signal pick better names than the universe it scans?

§10.0 says the one thing the backtest cannot judge is the *live* score — the
LLM/orderbook layer that only exists in production — and that only a live
sample can settle it. It then puts that sample at 100+ closed trades, which at
0.22 entries a day is about two years away.

That framing missed what was already on disk. `candidate_scores.jsonl` records
every name the live scorer looked at, with its live score, every 120 seconds.
Those are the signal's own outputs — thousands of them — and the forward return
of each name is observable from daily bars. The signal is testable now, without
placing a single additional trade.

First run, 2026-09-24, over 2026-08-19..09-23 (4,774 snapshots, 26 sessions):

    corr(score, day-demeaned 5d return) = -0.014  (n=320)
    5d  spread vs non-signal names: -1.02p/session, P(signal better) = 0.07
    10d spread vs non-signal names: -1.85p/session, P(signal better) = 0.06

A working score would order the cross-section. This one does not order it at
all, and what separation exists points the wrong way.

Two things make the arithmetic honest, and both matter more than the sample
size:

* **Day-demeaning.** On a day the whole market rises, any pick looks good.
  Subtracting the cross-sectional mean of everything scanned that day leaves
  only what selection contributed.
* **Blocking by session.** 303 signals are not 303 independent observations —
  they come from 26 sessions and 30 correlated large caps. The bootstrap
  resamples whole sessions, so correlation inside a session is preserved
  instead of being counted as extra evidence. Pooling would have reported a
  confidence interval several times too tight.

Usage (in-cluster, where the journal and the API both live):
    python automation/signal_efficacy.py                 # full report
    python automation/signal_efficacy.py --horizons 1,5  # pick horizons
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

JOURNAL_PATH = os.getenv("CANDIDATE_JOURNAL_PATH", "/app/output/candidate_scores.jsonl")
DEFAULT_HORIZONS = (1, 3, 5, 10)
BOOTSTRAP_DRAWS = 10_000
# Fixed so a re-run reproduces the interval; the sampling is the estimate, not
# a source of news.
BOOTSTRAP_SEED = 20260924


# --- pure core --------------------------------------------------------------


def collapse_journal(lines: Iterable[str]) -> dict[str, dict[str, dict[str, Any]]]:
    """{day: {code: {score, signalled}}} from raw journal lines.

    A name is `signalled` if it was ever eligible at or above the gate that
    session — exactly the condition that dispatches the screener, so the set
    is the one the live system would have asked about. The score kept is the
    session's best, because that is the strongest claim the scorer made.

    Records predating a field (the journal is append-only and has grown) are
    read on their own terms rather than dropped.
    """

    out: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        day = str(rec.get("trading_day") or "").replace("-", "")
        # `isdigit` matters: any eight-character string passes a length check,
        # and a bad day would become its own session with its own "spread".
        if len(day) != 8 or not day.isdigit():
            continue
        gate = rec.get("min_score")
        gate = 8 if gate is None else gate
        for entry in rec.get("band") or []:
            if not isinstance(entry, dict):
                continue
            code, score = entry.get("code"), entry.get("score")
            if not code or not isinstance(score, (int, float)):
                continue
            signalled = bool(entry.get("eligible")) and score >= gate
            cur = out[day].get(code)
            if cur is None:
                out[day][code] = {"score": score, "signalled": signalled}
            else:
                cur["score"] = max(cur["score"], score)
                cur["signalled"] = cur["signalled"] or signalled
    return dict(out)


def forward_return(
    closes: dict[str, dict[str, float]],
    calendar: list[str],
    code: str,
    day: str,
    horizon: int,
) -> float | None:
    """Percent change from `day`'s close to `horizon` sessions later.

    None when either end is missing, which is the right answer near the end
    of the data — padding it would invent history.
    """

    series = closes.get(code)
    if not series or day not in series:
        return None
    try:
        i = calendar.index(day)
    except ValueError:
        return None
    if i + horizon >= len(calendar):
        return None
    later = calendar[i + horizon]
    if later not in series:
        return None
    start = series[day]
    if start <= 0:
        return None
    return (series[later] - start) / start * 100.0


def session_spreads(
    scan: dict[str, dict[str, dict[str, Any]]],
    closes: dict[str, dict[str, float]],
    calendar: list[str],
    horizon: int,
    min_control: int = 3,
) -> list[float]:
    """Per session: mean(signalled) - mean(the rest of what was scanned).

    The control is the same universe on the same day, which is what makes
    this a test of selection rather than of the market. Sessions without a
    signal, or with too thin a control to average, contribute nothing.
    """

    spreads: list[float] = []
    for day in sorted(scan):
        hit: list[float] = []
        rest: list[float] = []
        for code, info in scan[day].items():
            r = forward_return(closes, calendar, code, day, horizon)
            if r is None:
                continue
            (hit if info["signalled"] else rest).append(r)
        if hit and len(rest) >= min_control:
            spreads.append(st.mean(hit) - st.mean(rest))
    return spreads


def bootstrap(
    values: list[float], draws: int = BOOTSTRAP_DRAWS, seed: int = BOOTSTRAP_SEED
) -> dict[str, float] | None:
    """Resample the given units — sessions, not signals — with replacement."""

    if len(values) < 5:
        return None
    rng = random.Random(seed)
    means = []
    n = len(values)
    for _ in range(draws):
        means.append(st.mean(values[rng.randrange(n)] for _ in range(n)))
    means.sort()
    return {
        "mean": round(st.mean(values), 3),
        "ci_low": round(means[int(draws * 0.025)], 3),
        "ci_high": round(means[int(draws * 0.975)], 3),
        "p_positive": round(sum(1 for m in means if m > 0) / draws, 3),
        "sessions": n,
    }


def score_rank_quality(
    scan: dict[str, dict[str, dict[str, Any]]],
    closes: dict[str, dict[str, float]],
    calendar: list[str],
    horizon: int,
    min_names: int = 5,
) -> dict[str, Any]:
    """Correlation of score with day-demeaned return, plus a bucket table.

    This is the sharpest question available: forget thresholds, does a higher
    score mean a better name *that day*? A working score is clearly positive.
    """

    pairs: list[tuple[float, float]] = []
    buckets: dict[int, list[float]] = defaultdict(list)
    for day in sorted(scan):
        rows = []
        for code, info in scan[day].items():
            r = forward_return(closes, calendar, code, day, horizon)
            if r is not None:
                rows.append((info["score"], r))
        if len(rows) < min_names:
            continue
        mean_day = st.mean(r for _, r in rows)
        for score, r in rows:
            excess = r - mean_day
            pairs.append((score, excess))
            buckets[int(score)].append(excess)

    table = [
        {
            "score": s,
            "n": len(v),
            "excess_pct": round(st.mean(v), 2),
            "win_pct": round(sum(1 for x in v if x > 0) / len(v) * 100, 1),
        }
        for s, v in sorted(buckets.items())
        if len(v) >= 25
    ]

    corr = None
    if len(pairs) >= 30:
        xs = [a for a, _ in pairs]
        ys = [b for _, b in pairs]
        mx, my = st.mean(xs), st.mean(ys)
        num = sum((a - mx) * (b - my) for a, b in pairs)
        den = (sum((a - mx) ** 2 for a in xs) ** 0.5) * (
            sum((b - my) ** 2 for b in ys) ** 0.5
        )
        corr = round(num / den, 3) if den else None

    return {"correlation": corr, "observations": len(pairs), "by_score": table}


def build_report(
    scan: dict[str, dict[str, dict[str, Any]]],
    closes: dict[str, dict[str, float]],
    calendar: list[str],
    horizons: Iterable[int] = DEFAULT_HORIZONS,
) -> dict[str, Any]:
    signals = sum(
        1 for day in scan for info in scan[day].values() if info["signalled"]
    )
    report: dict[str, Any] = {
        "sessions": len(scan),
        "scanned_pairs": sum(len(v) for v in scan.values()),
        "signals": signals,
        "start_day": min(scan) if scan else None,
        "end_day": max(scan) if scan else None,
        "horizons": {},
        "rank_quality": score_rank_quality(scan, closes, calendar, 5),
    }
    for h in horizons:
        stats = bootstrap(session_spreads(scan, closes, calendar, h))
        report["horizons"][h] = stats
    return report


def format_report(report: dict[str, Any]) -> str:
    lines = [
        "라이브 신호 유효성 — 신호 종목 vs 같은 날 같은 유니버스의 나머지",
        f"  구간 {report['start_day']}~{report['end_day']} · "
        f"{report['sessions']}세션 · 스캔 {report['scanned_pairs']}건 · "
        f"신호 {report['signals']}건",
        "",
        f"  {'구간':<6}{'세션':>5}{'세션당 초과':>13}{'95% CI':>22}{'P(신호 우위)':>14}",
    ]
    for h, s in report["horizons"].items():
        if not s:
            lines.append(f"  {h}일{'':<4}{'표본 부족':>16}")
            continue
        lines.append(
            f"  {h}일{'':<3}{s['sessions']:>5}{s['mean']:>+12.3f}p"
            f"   [{s['ci_low']:>+6.3f}, {s['ci_high']:>+6.3f}]{s['p_positive']:>13.2f}"
        )
    rq = report["rank_quality"]
    lines += [
        "",
        f"  점수의 서열 품질: corr(score, 당일 평균 제거 5일 수익률) = "
        f"{rq['correlation']} (n={rq['observations']})",
        "  — 작동하는 점수라면 뚜렷한 양수여야 한다.",
    ]
    for row in rq["by_score"]:
        lines.append(
            f"    score {row['score']:>2} : n={row['n']:>5}"
            f"  초과 {row['excess_pct']:>+6.2f}%  승률 {row['win_pct']:>5.1f}%"
        )
    return "\n".join(lines)


# --- I/O --------------------------------------------------------------------


async def _load_closes(codes: set[str], base_date: str) -> tuple[dict, list[str]]:
    from src.config import Settings
    from src.services.kiwoom_client import KiwoomClient
    from src.services.market import get_stock_daily_chart

    client = KiwoomClient(Settings())
    closes: dict[str, dict[str, float]] = {}
    try:
        for code in sorted(codes):
            try:
                r = await get_stock_daily_chart(
                    client, stock_code=code, base_date=base_date
                )
            except Exception as exc:  # noqa: BLE001 — a missing name is not fatal
                print(f"  {code}: 조회 실패 {str(exc)[:50]}", file=sys.stderr)
                continue
            series: dict[str, float] = {}
            for row in r.get("daily_chart") or []:
                day = str(row.get("dt") or "")
                try:
                    close = abs(float(row.get("cur_prc") or 0))
                except (TypeError, ValueError):
                    continue
                if len(day) == 8 and close > 0:
                    series[day] = close
            if series:
                closes[code] = series
    finally:
        await client.close()
    calendar = sorted({d for s in closes.values() for d in s})
    return closes, calendar


async def _main() -> int:
    from datetime import datetime
    from zoneinfo import ZoneInfo

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--journal", default=JOURNAL_PATH)
    ap.add_argument("--horizons", default="1,3,5,10")
    ap.add_argument("--json", action="store_true", help="기계 판독용 JSON 출력")
    args = ap.parse_args()

    path = Path(args.journal)
    if not path.exists():
        print(f"저널이 없다: {path}", file=sys.stderr)
        return 1
    with path.open(encoding="utf-8") as fh:
        scan = collapse_journal(fh)
    if not scan:
        print("저널에 읽을 레코드가 없다", file=sys.stderr)
        return 1

    codes = {c for day in scan.values() for c in day}
    base = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y%m%d")
    closes, calendar = await _load_closes(codes, base)
    if not calendar:
        print("일봉을 하나도 받지 못했다", file=sys.stderr)
        return 1

    horizons = [int(x) for x in args.horizons.split(",") if x.strip()]
    report = build_report(scan, closes, calendar, horizons)
    print(json.dumps(report, ensure_ascii=False, indent=1) if args.json
          else format_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
