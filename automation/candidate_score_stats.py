#!/usr/bin/env python3
"""Summarise the candidate score journal — is the dispatch gate set right?

Reads the JSONL the watcher appends (`--record-candidate-scores`) and reports
the distribution of scores among candidates that passed the below_ma dip
gate. A dispatch only ever records a score that already cleared the gate, so
this is the only view of how far short the rest fell.

Usage:
    python automation/candidate_score_stats.py [--path P] [--days N]
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

DEFAULT_PATH = os.environ.get(
    "CANDIDATE_JOURNAL_PATH", "/app/output/candidate_scores.jsonl"
)


def load(path: Path, days: int | None) -> list[dict]:
    if not path.exists():
        print(f"저널 없음: {path}", file=sys.stderr)
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    if days:
        keep = sorted({r.get("trading_day", "") for r in records})[-days:]
        records = [r for r in records if r.get("trading_day") in keep]
    return records


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", default=DEFAULT_PATH)
    ap.add_argument("--days", type=int, default=0, help="최근 N 거래일만")
    args = ap.parse_args()

    records = load(Path(args.path), args.days or None)
    if not records:
        print("표본 0건 — 아직 밴드 통과 후보가 기록되지 않았습니다.")
        return 0

    gates = {r.get("min_score") for r in records}
    gate = max(g for g in gates if isinstance(g, int)) if gates else 0
    days = sorted({r.get("trading_day") for r in records if r.get("trading_day")})

    # Per (day, code) best score: a name sampled 40 times in a day is one
    # observation of that name, not forty.
    best: dict[tuple[str, str], dict] = {}
    for rec in records:
        for row in rec.get("band") or []:
            key = (rec.get("trading_day"), row.get("code"))
            cur = best.get(key)
            if cur is None or (row.get("score") or 0) > (cur.get("score") or 0):
                best[key] = {**row, "day": rec.get("trading_day")}

    scores = [b.get("score") or 0 for b in best.values()]
    print(f"기간 {days[0]} ~ {days[-1]} ({len(days)}거래일) · "
          f"스냅샷 {len(records)}건 · 종목-일 표본 {len(scores)}건 · 게이트 {gate}\n")

    print("점수 분포 (종목-일 기준, 각 종목의 당일 최고점):")
    hist = Counter(scores)
    for score in range(min(hist), max(hist) + 1):
        n = hist.get(score, 0)
        mark = " ←게이트" if score == gate else ""
        print(f"  {score:>2}점  {'█' * n}{'' if n else '·'} {n}{mark}")

    passed = sum(1 for s in scores if s >= gate)
    print(f"\n게이트 통과 {passed}건 / {len(scores)}건 ({passed/len(scores)*100:.0f}%)")
    print(f"중앙값 {statistics.median(scores):.1f} · 평균 {statistics.mean(scores):.1f} "
          f"· 최고 {max(scores)}")
    short = [s for s in scores if s < gate]
    if short:
        print(f"미달분 최고 {max(short)}점 (게이트까지 {gate - max(short)}점)")

    per_day: dict[str, list[int]] = defaultdict(list)
    for (day, _), row in best.items():
        per_day[day].append(row.get("score") or 0)
    print("\n거래일별 밴드 종목 수 / 최고점:")
    for day in days:
        vals = per_day.get(day, [])
        top = max(vals) if vals else 0
        flag = " ✅통과" if top >= gate else ""
        print(f"  {day}  {len(vals):>2}종목  최고 {top}점{flag}")

    # Slot occupancy — the gate that leaves no other trace. At zero slots
    # `detect_tier2_new_candidates` returns before building an event, so a
    # qualifying candidate is simply never put to the screener. Measured
    # 2026-08-19..09-18: 78.7% of snapshots held a gate-passing candidate
    # against 5 entries in 23 trading days. This is where that shows up.
    slot_aware = [r for r in records if isinstance(r.get("available_slots"), int)]
    if slot_aware:
        qualifying = [
            r for r in slot_aware
            if any(
                row.get("eligible") and (row.get("score") or 0) >= (r.get("min_score") or gate)
                for row in r.get("band") or []
            )
        ]
        starved = [r for r in qualifying if r["available_slots"] <= 0]
        print(f"\n슬롯 점유 (슬롯 기록이 있는 {len(slot_aware)}스냅샷 기준):")
        if qualifying:
            print(f"  게이트 통과 후보 있음      {len(qualifying)}건 "
                  f"({len(qualifying)/len(slot_aware)*100:.0f}%)")
            print(f"  └ 슬롯 0이라 미질의       {len(starved)}건 "
                  f"({len(starved)/len(qualifying)*100:.0f}%)  ← 막힌 기회")
        else:
            print("  게이트 통과 후보 없음")
        per_day_starved = Counter(
            r.get("trading_day") for r in starved if r.get("trading_day")
        )
        if per_day_starved:
            print("  거래일별 미질의:")
            for day in sorted(per_day_starved):
                print(f"    {day}  {per_day_starved[day]:>3}건")
    elif records:
        print("\n슬롯 점유: 기록 없음 "
              "(available_slots는 2026-09-21 배포부터 기록된다)")

    blocked = Counter()
    for b in best.values():
        for reason in b.get("blocked_by") or []:
            blocked[reason] += 1
    if blocked:
        print("\n밴드 통과 후 남은 거절 사유:")
        for reason, n in blocked.most_common():
            print(f"  {n:>3}건  {reason}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
