"""Accumulate real fills into a statistics-ready ledger.

The backtest can never answer this system's one genuinely open question.
It replays daily OHLC against an entry rule, but the live watcher adds
things no historical data reproduces: the score≥8 gate over live
orderbook depth, LLM screener/evaluator judgments, and stale-price
rejection. So "below_ma has no edge in backtest" (CLAUDE.md §10.0)
leaves open whether *the deployed system* has one.

Answering that needs live fills recorded in a form you can run statistics
over. Today they live in three places that resist analysis: per-day
Multica issues, hand-written notes in ``automation/memory_live.md``, and
the broker's own 당일매매일지 which only covers the current session. This
script appends each day's closed round-trips to a JSONL ledger so
expectancy can be estimated with the same tools the backtest uses
(``backtest.statistics.bootstrap_expectancy_ci``).

Two modes:
  ``--append``  fetch today's journal (ka10170) and add new rows.
                Idempotent per (date, stock_code) — safe to re-run.
  ``--stats``   summarize the accumulated ledger with a confidence
                interval, so the answer is "expectancy X% ± Y at n=Z",
                never a bare average over a handful of trades.

Read-only against the broker: it queries the trading journal and writes
a local file. It never places, cancels, or modifies an order.

⚠️ Sample size governs everything here. Published guidance puts ~30
trades at the bare minimum for a mean to mean anything and 100+ before
treating an edge as real; this account is at n≈1-2 as of 2026-07-25. The
``--stats`` output states n prominently and refuses to editorialize below
30 for exactly that reason.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

KST = timezone(timedelta(hours=9))
LEDGER_PATH = Path(os.environ.get("LIVE_LEDGER_PATH", "/app/output/live_trades.jsonl"))

# Round-trip friction assumed when the broker doesn't itemize it, matching
# backtest/engine.py's Params defaults (fee 0.015%×2 + KOSPI 거래세 0.20%).
FALLBACK_COST_PCT = 0.015 * 2 + 0.20


def _f(value) -> float | None:
    if value in ("", None):
        return None
    text = str(value).replace(",", "").strip()
    if not text:
        return None
    sign = -1.0 if text[0] == "-" else 1.0
    text = text.lstrip("+-")
    try:
        return sign * float(text)
    except ValueError:
        return None


def _pick(row: dict, *keys):
    for k in keys:
        v = row.get(k)
        if v not in ("", None):
            return v
    return None


def normalize_journal_row(row: dict, trade_date: str) -> dict | None:
    """One 당일매매일지 row → a ledger record, or None if not a closed trade.

    Only rows with a realized sell are kept: an open position has no
    return yet, and counting it would bias expectancy toward whatever is
    currently held.

    ``net_pct`` prefers the broker's own ``prft_rt`` (already net of fees
    and tax on the realized portion). When absent it is derived from the
    average prices and the assumed round-trip cost, and ``net_pct_source``
    records which path was taken so mixed-provenance rows stay auditable.
    """
    code = str(_pick(row, "stk_cd", "code") or "").strip()
    sell_qty = _f(_pick(row, "sell_qty", "sel_qty"))
    if not code or not sell_qty or sell_qty <= 0:
        return None

    buy_avg = _f(_pick(row, "buy_avg_pric", "buy_uv"))
    sell_avg = _f(_pick(row, "sel_avg_pric", "sell_uv"))
    profit_rate = _f(_pick(row, "prft_rt", "pl_rt", "lspft_rt"))

    if profit_rate is not None:
        net_pct, source = profit_rate, "broker_prft_rt"
    elif buy_avg and sell_avg and buy_avg > 0:
        net_pct = (sell_avg - buy_avg) / buy_avg * 100 - FALLBACK_COST_PCT
        source = "derived_from_avg_prices"
    else:
        return None

    return {
        "trade_date": trade_date,
        "stock_code": code,
        "stock_name": str(_pick(row, "stk_nm", "item_nm", "name") or code),
        "buy_qty": _f(_pick(row, "buy_qty", "qty")),
        "buy_avg_price": buy_avg,
        "sell_qty": sell_qty,
        "sell_avg_price": sell_avg,
        "profit_loss_krw": _f(_pick(row, "pl_amt", "tdy_sel_pl", "lspft_amt")),
        "commission_tax_krw": _f(_pick(row, "cmsn_alm_tax", "tdy_trde_cmsn")),
        "net_pct": round(net_pct, 4),
        "net_pct_source": source,
        "recorded_at": datetime.now(KST).isoformat(),
    }


def load_ledger(path: Path = None) -> list[dict]:
    p = path or LEDGER_PATH
    if not p.exists():
        return []
    rows = []
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue  # tolerate a torn final line rather than lose the ledger
    return rows


def append_records(records: list[dict], path: Path = None) -> int:
    """Append records not already present for their (date, code). Returns count."""
    p = path or LEDGER_PATH
    existing = {(r.get("trade_date"), r.get("stock_code")) for r in load_ledger(p)}
    fresh = [r for r in records if (r["trade_date"], r["stock_code"]) not in existing]
    if not fresh:
        return 0
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a") as fh:
        for r in fresh:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    return len(fresh)


async def _append_today() -> int:
    from src.config import Settings
    from src.services import account
    from src.services.kiwoom_client import KiwoomClient

    client = KiwoomClient(Settings())
    try:
        await client.request_access_token()
        result = await account.get_daily_trading_journal(client)
    finally:
        await client.close()

    rows = result.get("trading_journal_data") or []
    if not isinstance(rows, list):
        rows = []
    today = datetime.now(KST).strftime("%Y-%m-%d")
    records = [
        rec for rec in (normalize_journal_row(r, today) for r in rows if isinstance(r, dict))
        if rec
    ]
    added = append_records(records)
    print(f"{today}: 매매일지 {len(rows)}행 → 청산거래 {len(records)}건 → 신규 {added}건 기록")
    if records and not added:
        print("  (이미 기록됨 — idempotent skip)")
    return 0


def _print_stats() -> int:
    from backtest.statistics import bootstrap_expectancy_ci
    from backtest.engine import Trade

    rows = load_ledger()
    if not rows:
        print(f"원장 비어 있음 ({LEDGER_PATH}). `--append`를 장 마감 후 실행하세요.")
        return 0

    nets = [r["net_pct"] for r in rows if isinstance(r.get("net_pct"), (int, float))]
    n = len(nets)
    wins = [x for x in nets if x > 0]
    print(f"\n=== 라이브 체결 원장 ({LEDGER_PATH}) ===")
    print(f"  거래 {n}건 · 기간 {rows[0].get('trade_date')} ~ {rows[-1].get('trade_date')}")
    if not n:
        return 0
    print(f"  평균 {sum(nets)/n:+.3f}%/거래 · 승률 {len(wins)/n*100:.1f}% "
          f"({len(wins)}승 {n-len(wins)}패)")
    total_krw = sum(r.get("profit_loss_krw") or 0 for r in rows)
    fees = sum(r.get("commission_tax_krw") or 0 for r in rows)
    print(f"  실현손익 합계 {total_krw:+,.0f}원 · 수수료/세금 {fees:,.0f}원")

    # Reuse the backtest CI machinery so live and simulated numbers are
    # computed identically and stay directly comparable.
    trades = [
        Trade(code=r.get("stock_code", ""), entry_date=r.get("trade_date", ""),
              entry_price=r.get("buy_avg_price") or 0.0,
              exit_date=r.get("trade_date", ""),
              exit_price=r.get("sell_avg_price") or 0.0,
              reason="live", gross_pct=r["net_pct"], net_pct=r["net_pct"])
        for r in rows if isinstance(r.get("net_pct"), (int, float))
    ]
    ci = bootstrap_expectancy_ci(trades, n_resamples=5000)
    if ci:
        print(f"  95% CI [{ci.lower:+.3f}, {ci.upper:+.3f}] · P(기대값>0)={ci.p_positive}")

    if n < 30:
        print(f"\n  ⚠️ n={n} — 표본이 30건 미만이라 어떤 결론도 내릴 수 없다. "
              f"평균의 부호는 노이즈다.")
    elif n < 100:
        print(f"\n  🟡 n={n} — 방향성 참고는 가능하나 100건 전까지는 잠정.")
    else:
        verdict = ("🟢 CI가 0을 제외 — 라이브 엣지의 통계적 근거"
                   if ci and ci.excludes_zero
                   else "🔴 CI가 0을 포함 — 100건+에도 엣지 미확인")
        print(f"\n  {verdict}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="live_trade_journal")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--append", action="store_true", help="오늘 매매일지를 원장에 추가")
    g.add_argument("--stats", action="store_true", help="누적 원장 통계 요약")
    args = ap.parse_args()
    return asyncio.run(_append_today()) if args.append else _print_stats()


if __name__ == "__main__":
    sys.exit(main())
