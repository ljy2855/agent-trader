"""Backtest CLI.

Four phases:
  1) fetch        — populate the daily-bar cache (run in-cluster where Kiwoom is reachable)
  2) run/sweep    — backtest the cached universe with given params, or compare a fixed grid
  3) walkforward  — rolling train/test validation (see validate.py)
  4) significance — is the edge real, or search noise? (see statistics.py)

`run`/`sweep` answer "how did these params do on the whole cache?" — that
number is in-sample (every param here was chosen by looking at this same
cache; see validate.py's module docstring). Before trusting a parameter
change enough to deploy it, run `walkforward` (does it survive unseen
data?) AND `significance` (is it distinguishable from luck, given how
many variants were tried?). A parameter change that fails either has no
business going to a live account.

Examples:
  python -m backtest.run fetch
  python -m backtest.run run --stop -2.5 --take 5 --max-hold 3
  python -m backtest.run sweep
  python -m backtest.run walkforward --train-days 180 --test-days 60
  python -m backtest.run significance --n-trials 40
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from typing import Any

from .engine import Params, run_backtest
from .data import fetch_universe, load_cache, KOSPI_LARGECAP
from .statistics import (
    block_performance,
    bootstrap_expectancy_ci,
    deflated_sharpe_ratio,
    make_block_edges,
    pbo_cscv,
)
from .validate import random_entry_null, walk_forward


def _print_summary(label: str, summary: dict) -> None:
    if summary.get("trades", 0) == 0:
        print(f"  {label}: 거래 0건")
        return
    print(
        f"  {label}: n={summary['trades']} 승률={summary['win_rate_pct']}% "
        f"기대값={summary['expectancy_pct']}%/거래 "
        f"payoff={summary['payoff']} 거래단순연결={summary['total_return_pct']}% "
        f"연결MDD={summary['max_drawdown_pct']}% (실계좌 성과 아님) exits={summary['exits']}"
    )


async def _fetch(args) -> None:
    sys.path.insert(0, ".")
    from src.config import Settings
    from src.services.kiwoom_client import KiwoomClient

    c = KiwoomClient(Settings())
    try:
        await c.request_access_token()
        print(f"Fetching {len(KOSPI_LARGECAP)} symbols (base_date={args.base or 'today'})...")
        series = await fetch_universe(c, base_date=args.base)
        total = sum(len(v) for v in series.values())
        print(f"Done. {len(series)} symbols, {total} bars cached.")
    finally:
        await c.close()


def _run(args) -> None:
    series = load_cache()
    if not series:
        print("캐시 없음 — 먼저 `python -m backtest.run fetch` 실행 (in-cluster).")
        sys.exit(1)
    p = Params(
        day_change_min=args.dc_min, day_change_max=args.dc_max,
        stop_loss_pct=args.stop, take_profit_pct=args.take,
        max_hold_days=args.max_hold,
        entry_mode=args.entry_mode,
        ma_period=args.ma_period,
        ma_entry_style=args.ma_entry_style,
        ma_max_dip_pct=args.ma_max_dip,
        fee_pct=args.fee_pct,
        tax_pct=args.tax_pct,
        slippage_bps=args.slippage_bps,
    )
    res = run_backtest(series, p)
    s = res.summary()
    print(f"\n=== Backtest (universe {len(series)}종목, "
          f"진입 {p.entry_mode}/{p.ma_entry_style}, "
          f"손절 {p.stop_loss_pct}% / 익절 {p.take_profit_pct}% / max_hold {p.max_hold_days}일) ===")
    print(f"  비용 가정: 편도 수수료 {p.fee_pct}% · 매도세 {p.tax_pct}% · 편도 슬리피지 {p.slippage_bps}bp")
    _print_summary("결과", s)
    if args.json:
        print(json.dumps(s, ensure_ascii=False, indent=2))


def candidate_grid(max_hold: int = 3) -> list[tuple[str, Params]]:
    """The strategy variants under comparison, incumbent first.

    Shared by sweep / walkforward / significance so all three judge the
    same candidate set — a PBO computed over a different grid than the
    one actually used for selection would understate overfitting.

    Incumbent = current live config (k8s/kiwoom-watcher.yaml). Order
    matters: `validate._pick_best` falls back to element 0 when a fold's
    train slice can't discriminate, so the incumbent must stay first and
    never silently drift to an untested corner. Keep the labels honest —
    they drifted stale once already (said "-2.5/+5" while live had moved
    to -4/+8/below_ma).
    """
    return [
        ("라이브 진입밴드 일봉 proxy(below_ma,ma20,-4/+8)",
         Params(entry_mode="below_ma", ma_period=20, stop_loss_pct=-4, take_profit_pct=8, max_hold_days=max_hold)),
        ("momentum(-4/+8)",
         Params(entry_mode="momentum", stop_loss_pct=-4, take_profit_pct=8, max_hold_days=max_hold)),
        ("below_ma 타이트(-2.5/+5)",
         Params(entry_mode="below_ma", ma_period=20, stop_loss_pct=-2.5, take_profit_pct=5, max_hold_days=max_hold)),
        ("below_ma ma10",
         Params(entry_mode="below_ma", ma_period=10, stop_loss_pct=-4, take_profit_pct=8, max_hold_days=max_hold)),
        ("below_ma 넓게(-3/+8/5d)",
         Params(entry_mode="below_ma", ma_period=20, stop_loss_pct=-3, take_profit_pct=8, max_hold_days=5)),
        ("momentum 진입넓게(0.5~20)",
         Params(entry_mode="momentum", day_change_max=20, stop_loss_pct=-4, take_profit_pct=8, max_hold_days=max_hold)),
    ]


def _sweep(args) -> None:
    series = load_cache()
    if not series:
        print("캐시 없음 — 먼저 fetch.")
        sys.exit(1)
    print(f"\n=== Parameter sweep (universe {len(series)}종목) — 전부 in-sample, "
          f"배포 전엔 `walkforward` + `significance`로 재확인 ===")
    for label, p in candidate_grid():
        _print_summary(label, run_backtest(series, p).summary())


def _significance(args) -> None:
    """Is the incumbent's edge real, or an artifact of the search?"""
    series = load_cache()
    if not series:
        print("캐시 없음 — 먼저 fetch.")
        sys.exit(1)

    grid = candidate_grid(args.max_hold)
    results = {label: run_backtest(series, p) for label, p in grid}
    incumbent_label = grid[0][0]

    print(f"\n=== 통계적 유의성 (universe {len(series)}종목, 후보 {len(grid)}개) ===")

    # --- 1. bootstrap CI on the incumbent -------------------------------
    inc_trades = results[incumbent_label].trades
    ci = bootstrap_expectancy_ci(inc_trades, n_resamples=args.resamples)
    print(f"\n[1] 부트스트랩 신뢰구간 — {incumbent_label}")
    if ci is None:
        print("  거래 0건 — 계산 불가")
    else:
        print(f"  기대값 {ci.point}%/거래 · {int(ci.confidence*100)}% CI "
              f"[{ci.lower}, {ci.upper}] · n={ci.n_trades}")
        print(f"  P(기대값>0) = {ci.p_positive}")
        if ci.excludes_zero:
            print("  🟢 CI가 0을 포함하지 않음 — 방향성은 통계적으로 구분됨")
        else:
            print("  🔴 CI가 0을 가로지름 — 이 표본으로는 '엣지 없음'과 구분 불가")

    # --- 2. PBO across the grid -----------------------------------------
    all_dates = sorted({
        str(b.get("dt") or b.get("date") or "")
        for bars in series.values() for b in bars
        if (b.get("dt") or b.get("date"))
    })
    print(f"\n[2] 과최적화 확률 (PBO, CSCV) — 블록 {args.blocks}개")
    try:
        edges = make_block_edges(all_dates, args.blocks)
        perf = {
            label: block_performance(res.trades, edges)
            for label, res in results.items()
        }
        pbo = pbo_cscv(perf)
    except ValueError as exc:
        print(f"  계산 불가: {exc}")
        pbo = None
    if pbo is not None:
        print(f"  PBO = {pbo.pbo}  ({pbo.n_splits} splits · 후보 {pbo.n_strategies}개)")
        print(f"  IS 우승자의 평균 OOS 상대순위 = {pbo.median_oos_rank} (1=최상위)")
        print(f"  {pbo.verdict}")
        # PBO only measures whether the *ranking* survives OOS. If every
        # candidate is equally edgeless, the ranking transfers fine and PBO
        # looks green — so say so explicitly rather than let a lone 🟢 read
        # as "this works".
        if pbo.pbo < 0.25 and ci is not None and not ci.excludes_zero:
            print("  ⚠️ 단, PBO는 '후보 간 순위가 전이되는가'만 본다. [1]에서 기대값이 "
                  "0과 구분되지 않으므로 이 🟢는 '엣지 있음'이 아니라 "
                  "'후보들이 고르게 무의미함'으로 읽어야 한다.")

    # --- 3. Deflated Sharpe for the incumbent ---------------------------
    print(f"\n[3] Deflated Sharpe Ratio — n_trials={args.n_trials}")
    trial_sharpes = []
    for res in results.values():
        nets = [t.net_pct for t in res.trades]
        if len(nets) > 2:
            from statistics import mean as _m, pstdev as _sd
            s = _sd(nets)
            if s > 0:
                trial_sharpes.append(_m(nets) / s)
    dsr = deflated_sharpe_ratio(
        [t.net_pct for t in inc_trades],
        n_trials=args.n_trials,
        trial_sharpes=trial_sharpes or None,
    )
    if dsr is None:
        print("  계산 불가 (표본 부족 또는 무분산)")
    else:
        print(f"  관측 Sharpe(거래당) = {dsr.sharpe} · "
              f"귀무가설 하 기대 최대치 = {dsr.sharpe_benchmark}")
        print(f"  DSR = {dsr.dsr} · skew={dsr.skew} kurt={dsr.kurtosis} n={dsr.n_obs}")
        print(f"  {dsr.verdict}")

    # --- 4. random-entry null model -------------------------------------
    # The other three tests all assume the *comparison set* is other
    # strategies. This one asks the more basic question they can't:
    # does the entry signal beat no signal at all? On a one-regime cache
    # that's the difference between alpha and market drift.
    print(f"\n[4] 무작위 진입 대조군 (seed {args.null_seeds}개, 청산규칙 동일)")
    null = random_entry_null(series, grid[0][1], n_seeds=args.null_seeds)
    if null is None:
        print("  계산 불가 (거래 0건)")
    else:
        print(f"  전략 {null.strategy_expectancy:+.3f}%/거래 (n={null.n_strategy_trades}) vs "
              f"무작위 {null.null_expectancy:+.3f}%/거래 (n≈{null.n_null_trades_avg})")
        print(f"  알파 = {null.alpha:+.3f}%  ·  무작위가 전략을 이긴 비율 = {null.p_value:.0%}")
        print(f"  {null.verdict}")

    print("\n  ⚠️ 위 지표는 시뮬레이션 거래목록의 통계적 불확실성만 측정한다. "
          "생존편향 universe나 다음날 시가 체결 가정은 [4]로도 잡히지 않는다.")

    if args.json:
        print(json.dumps({
            "incumbent": incumbent_label,
            "bootstrap_ci": vars(ci) if ci else None,
            "pbo": {k: v for k, v in vars(pbo).items() if k != "logits"} if pbo else None,
            "dsr": vars(dsr) if dsr else None,
            "null_model": vars(null) if null else None,
        }, ensure_ascii=False, indent=2))


def _walkforward(args) -> None:
    series = load_cache()
    if not series:
        print("캐시 없음 — 먼저 fetch.")
        sys.exit(1)
    grid = [p for _label, p in candidate_grid(args.max_hold)]
    wf = walk_forward(series, grid, train_days=args.train_days, test_days=args.test_days)
    print(f"\n=== Walk-forward (universe {len(series)}종목, "
          f"train={args.train_days}봉/test={args.test_days}봉) ===")
    if not wf.folds:
        print("  fold 0개 — 캐시 기간이 train+test보다 짧습니다. "
              "--train-days/--test-days를 줄이거나 캐시 기간을 늘리세요.")
        return
    for i, f in enumerate(wf.folds, 1):
        p = f.best_params
        print(f"\n  fold {i}: train {f.train_start}~{f.train_end} → test {f.test_start}~{f.test_end}")
        print(f"    선택 params: entry={p.entry_mode} ma={p.ma_period} "
              f"stop={p.stop_loss_pct} take={p.take_profit_pct}")
        _print_summary("    train(IS)", f.train_summary)
        _print_summary("    test (OOS)", f.test_summary)

    combined = wf.combined_test_summary
    wfe = wf.walk_forward_efficiency
    print(f"\n  === 결합 OOS 결과 (신뢰할 숫자 — {len(wf.folds)} fold 연결) ===")
    _print_summary("  combined OOS", combined)
    if combined.get("trades", 0) < 30:
        print(f"  ⚠️ OOS 거래 {combined.get('trades', 0)}건 — 30건 미만은 방향성 참고만, "
              f"통계적 결론 내리지 말 것")
    print(f"  Walk-Forward Efficiency: {wfe if wfe is not None else 'N/A (모든 fold IS 기대값<=0)'}")
    if wfe is not None and wfe < 0.5:
        print("  ⚠️ WFE < 0.5 — in-sample 우위가 out-of-sample에서 크게 무너짐. "
              "과최적화 의심, 이 파라미터의 라이브 반영은 보류 권장.")
    if args.json:
        print(json.dumps(
            {
                "folds": [
                    {
                        "train_start": f.train_start, "train_end": f.train_end,
                        "test_start": f.test_start, "test_end": f.test_end,
                        "train_summary": f.train_summary, "test_summary": f.test_summary,
                    }
                    for f in wf.folds
                ],
                "combined_test_summary": combined,
                "walk_forward_efficiency": wfe,
            },
            ensure_ascii=False, indent=2,
        ))


def _ic(args) -> None:
    """Which inputs carry cross-sectional information — see backtest/ic.py.

    This runs before choosing weights, not after. The live score was built
    without it and has none (corr -0.014 against day-demeaned forward
    returns, measured on 320 live observations 2026-09-24).
    """

    import statistics as _st

    from . import ic as ic_mod
    from .data import load_cache

    series = load_cache()
    if not series:
        print("캐시가 비어 있다 — 먼저 `python -m backtest.run fetch`")
        return

    closes: dict[str, dict[str, float]] = {}
    for code, rows in series.items():
        by_day: dict[str, float] = {}
        for row in rows:
            day = str(row.get("dt") or "")
            try:
                price = abs(float(row.get("cur_prc") or 0))
            except (TypeError, ValueError):
                continue
            if len(day) == 8 and price > 0:
                by_day[day] = price
        if by_day:
            closes[code] = by_day

    sessions = sorted({d for s in closes.values() for d in s})
    pos = {d: i for i, d in enumerate(sessions)}
    codes = sorted(closes)

    def _ret(code: str, d0: str, d1: str) -> float | None:
        s = closes[code]
        if d0 not in s or d1 not in s or s[d0] <= 0:
            return None
        return (s[d1] - s[d0]) / s[d0] * 100.0

    def forward(code: str, day: str, horizon: int) -> float | None:
        i = pos.get(day)
        if i is None or i + horizon >= len(sessions):
            return None
        return _ret(code, day, sessions[i + horizon])

    def _window(code: str, day: str, n: int) -> list[float] | None:
        i = pos.get(day)
        if i is None or i < n:
            return None
        vals = [
            r for k in range(i - n + 1, i + 1)
            if (r := _ret(code, sessions[k - 1], sessions[k])) is not None
        ]
        return vals if len(vals) >= n * 3 // 4 else None

    def ma_dip(code: str, day: str) -> float | None:
        i = pos.get(day)
        if i is None or i < 19 or day not in closes[code]:
            return None
        vals = [closes[code][sessions[k]] for k in range(i - 19, i + 1)
                if sessions[k] in closes[code]]
        if len(vals) < 15:
            return None
        avg = _st.mean(vals)
        return (avg - closes[code][day]) / avg * 100.0 if avg else None

    def rev_1d(code: str, day: str) -> float | None:
        i = pos.get(day)
        if i is None or i < 1:
            return None
        r = _ret(code, sessions[i - 1], day)
        return None if r is None else -r

    def low_vol(code: str, day: str) -> float | None:
        vals = _window(code, day, 20)
        return None if vals is None else -_st.pstdev(vals)

    def mom_20d(code: str, day: str) -> float | None:
        i = pos.get(day)
        return None if i is None or i < 20 else _ret(code, sessions[i - 20], day)

    features = {
        "ma20_dip(현행)": ma_dip,
        "rev_1d": rev_1d,
        "low_vol_20d": low_vol,
        "mom_20d": mom_20d,
    }
    horizons = [int(x) for x in args.horizons.split(",") if x.strip()]
    baskets = [int(x) for x in args.baskets.split(",") if x.strip()]

    report: dict[str, Any] = {"sessions": len(sessions), "codes": len(codes),
                             "ic": {}, "subperiods": {}, "baskets": {}}
    for name, fn in features.items():
        report["ic"][name] = {
            h: ic_mod.summarize_ic(
                ic_mod.daily_ic(fn, forward, codes, sessions, h)
            )
            for h in horizons
        }
        report["subperiods"][name] = ic_mod.subperiod_ics(
            fn, forward, codes, sessions, horizons[0]
        )
        report["baskets"][name] = [
            b for n in baskets
            if (b := ic_mod.basket_excess(
                fn, forward, codes, sessions, horizons[0], n)) is not None
        ]

    cells = sum(1 for f in report["ic"].values() for v in f.values() if v)
    report["cells_tested"] = cells
    report["expected_max_abs_t"] = round(ic_mod.expected_max_abs_t(cells), 2)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return

    print(f"세션 {len(sessions)} · 종목 {len(codes)} · "
          f"왕복비용 {ic_mod.ROUND_TRIP_COST_PCT}%")
    print(f"\n{'피처':<16}{'h':>4}{'세션':>7}{'IC':>10}{'t':>8}{'95% CI':>22}")
    print("-" * 70)
    for name, per_h in report["ic"].items():
        for h, s in per_h.items():
            if not s:
                continue
            # `t` is None when per-session IC never varied — see ic.py.
            t_txt = "     n/a" if s["t"] is None else f"{s['t']:>8.2f}"
            print(f"{name:<16}{h:>4}{s['sessions']:>7}{s['mean_ic']:>+10.4f}"
                  f"{t_txt}   [{s['ci_low']:>+7.4f},{s['ci_high']:>+7.4f}]")
    print(f"\n{cells}개 셀 검정 — 귀무가설 하 최대 |t| 기대값 "
          f"≈ {report['expected_max_abs_t']}  (이걸 못 넘으면 볼 것 없음)")

    print(f"\n구간 안정성 (h={horizons[0]}d, 3등분)")
    print("-" * 70)
    for name, parts in report["subperiods"].items():
        cells_txt = "  ".join(
            f"{p['start']}~{p['end']} IC {p['mean_ic']:+.4f} "
            f"t {'n/a' if p.get('t') is None else format(p['t'], '+.2f')}"
            if p.get("mean_ic") is not None else "표본부족"
            for p in parts
        )
        print(f"  {name:<16} {cells_txt}")

    print(f"\n상위 N 바스켓, h={horizons[0]}d, 등가중 대비 초과 (net = 비용 차감)")
    print("-" * 70)
    print(f"  {'피처':<16}{'topN':>6}{'보유수':>7}{'초과':>10}{'net':>10}{'t':>7}")
    for name, rows in report["baskets"].items():
        for b in rows:
            print(f"  {name:<16}{b['top_n']:>6}{b['holdings']:>7}"
                  f"{b['excess_pct']:>+9.3f}%{b['net_pct']:>+9.3f}%{b['t']:>7.2f}")


def main() -> None:
    ap = argparse.ArgumentParser(prog="backtest.run")
    sub = ap.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("fetch", help="일봉 캐시 채우기 (in-cluster)")
    f.add_argument("--base", default=None, help="기준일 YYYYMMDD (기본 오늘)")

    r = sub.add_parser("run", help="단일 파라미터 백테스트")
    r.add_argument("--dc-min", type=float, default=0.5)
    r.add_argument("--dc-max", type=float, default=10.0)
    r.add_argument("--stop", type=float, default=-4.0)
    r.add_argument("--take", type=float, default=8.0)
    r.add_argument("--entry-mode", choices=["below_ma", "momentum", "drop_from_high"], default="below_ma")
    r.add_argument("--ma-period", type=int, default=20)
    r.add_argument("--ma-entry-style", choices=["band", "crossover"], default="band")
    r.add_argument("--ma-max-dip", type=float, default=5.0)
    r.add_argument("--fee-pct", type=float, default=0.015)
    r.add_argument("--tax-pct", type=float, default=0.20, help="매도세 가정(%), 실제 계좌/기간에 맞게 지정")
    r.add_argument("--slippage-bps", type=float, default=0.0, help="편도 불리한 체결 가정(bp); 0/5/10으로 민감도 비교")
    r.add_argument("--max-hold", type=int, default=3)
    r.add_argument("--json", action="store_true")

    sub.add_parser("sweep", help="파라미터 그리드 비교 (in-sample)")

    wf = sub.add_parser("walkforward", help="rolling train/test 검증 (배포 전 과최적화 체크)")
    wf.add_argument("--train-days", type=int, default=180, help="train window (거래일 수)")
    wf.add_argument("--test-days", type=int, default=60, help="test window (거래일 수)")
    wf.add_argument("--max-hold", type=int, default=3)
    wf.add_argument("--json", action="store_true")

    sg = sub.add_parser("significance", help="부트스트랩 CI + PBO + Deflated Sharpe")
    sg.add_argument("--blocks", type=int, default=10,
                    help="CSCV 시간 블록 수 (짝수). 클수록 정밀하나 C(S,S/2)로 비용 급증")
    sg.add_argument("--n-trials", type=int, default=40,
                    help="DSR 다중검정 보정용 '실제로 시도한 설정 수'. "
                         "과거 세션의 튜닝까지 정직하게 포함할 것 (과소 신고 = 가짜 합격)")
    sg.add_argument("--resamples", type=int, default=2000, help="부트스트랩 반복 횟수")
    sg.add_argument("--null-seeds", type=int, default=20,
                    help="무작위 진입 대조군 seed 수 (많을수록 p_value 안정)")
    sg.add_argument("--max-hold", type=int, default=3)
    sg.add_argument("--json", action="store_true")

    icp = sub.add_parser(
        "ic",
        help="피처별 횡단면 정보량(rank IC) + 구간 안정성 + 비용 차감 바스켓",
    )
    icp.add_argument("--horizons", default="1,5,10,20")
    icp.add_argument("--baskets", default="1,3,5,10,15",
                     help="상위 N 바스켓 크기. 라이브는 max_positions=1이다")
    icp.add_argument("--json", action="store_true")

    args = ap.parse_args()
    if args.cmd == "fetch":
        asyncio.run(_fetch(args))
    elif args.cmd == "ic":
        _ic(args)
    elif args.cmd == "run":
        _run(args)
    elif args.cmd == "sweep":
        _sweep(args)
    elif args.cmd == "walkforward":
        _walkforward(args)
    elif args.cmd == "significance":
        _significance(args)


if __name__ == "__main__":
    main()
