"""CLI entry point for the continuous intraday watcher.

Usage::

    source automation/trading_env.sh
    uv run python main_watcher.py --execute-orders

The watcher is the production trading loop: an in-process trigger
runner that consults Multica agents (per-stock for holdings and
candidates, global for portfolio/risk) only when state actually moves.
Tier-1 hard rules (stop-loss, hard take-profit, ``max_positions``
overflow, stale unfilled cancel) execute in code without an agent
consult.

Boot order:

1. ``source automation/trading_env.sh`` — exports ``KIWOOM_USE_MOCK``,
   ``MULTICA_PROJECT``, ``KIWOOM_LIVE_CONFIRM`` …
2. ``--execute-orders`` flips routing on. In live mode it ALSO requires
   ``KIWOOM_LIVE_CONFIRM=YES_I_REALLY_WANT_TO_TRADE``.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import signal
import sys
from typing import Sequence

from src.config import Settings
from src.services.watcher import IntradayWatcher, WatcherConfig
from src.constants.universe import UNIVERSE_LEADERS, UNIVERSE_MODES


def parse_watchlist_arg(raw: str | None) -> list[str] | None:
    """Parse a comma-separated watchlist argument into unique stock codes."""

    if raw is None:
        return None

    codes: list[str] = []
    for part in raw.split(","):
        code = part.strip()
        if not code:
            continue
        # KRX tickers are 6 alphanumeric chars (mostly digits, but specialty
        # securities like SPACs / M-class can embed letters — e.g. 0088M0).
        if len(code) != 6 or not code.isalnum():
            raise ValueError(f"Invalid stock code in watchlist: {code}")
        if code not in codes:
            codes.append(code)
    return codes or None


def _build_arg_parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""

    p = argparse.ArgumentParser(
        description=(
            "Continuous Kiwoom intraday watcher. Replaces the 30-min cron "
            "with trigger-driven dispatch."
        )
    )
    p.add_argument("--watchlist", help="Comma-separated 6-char stock codes")
    p.add_argument("--leaders-limit", type=int, default=10)
    p.add_argument("--candidate-limit", type=int, default=5)
    p.add_argument(
        "--candidate-scan-multiplier",
        type=int,
        default=2,
        help="How many leaderboard rows to detail-scan per candidate slot",
    )
    p.add_argument(
        "--stock-detail-cache-ttl-seconds",
        type=float,
        default=75.0,
        help="TTL for per-stock quote/orderbook/daily detail reuse inside the watcher",
    )
    p.add_argument("--max-positions", type=int, default=3)
    p.add_argument("--max-new-positions", type=int, default=1)
    p.add_argument("--position-budget-pct", type=int, default=10)
    p.add_argument(
        "--auto-buy-min-score",
        type=int,
        default=14,
        help="Min score for the strategy planner's internal auto-buy hint",
    )

    p.add_argument(
        "--poll-interval-seconds",
        type=int,
        default=30,
        help="Active polling interval during market hours",
    )
    p.add_argument(
        "--off-hours-interval-seconds",
        type=int,
        default=600,
        help="Sleep window when market is closed",
    )

    p.add_argument("--stop-loss-pct", type=float, default=-3.0)
    p.add_argument("--hard-take-profit-pct", type=float, default=8.0)
    p.add_argument("--stale-unfilled-minutes", type=int, default=5)

    p.add_argument("--holding-swing-pct", type=float, default=2.0)
    p.add_argument("--intraday-high-drop-pct", type=float, default=1.5)
    p.add_argument(
        "--holding-dedup-profit-delta-pct",
        type=float,
        default=1.5,
        help="직전 holding ACTION이 no-op(HOLD)이고 수익률 변화가 이 %% 미만이면 holding_swing 재dispatch skip. 0=비활성",
    )
    p.add_argument(
        "--candidate-dedup-score-delta",
        type=float,
        default=1.0,
        help=(
            "스크리너가 REJECT한 종목은 점수가 이만큼 오르기 전까지 재dispatch skip. "
            "점수가 게이트 근처에서 진동하면 같은 종목이 쿨다운마다 '신규'로 재판정된다. 0=비활성"
        ),
    )
    p.add_argument("--new-candidate-min-score", type=int, default=14)
    p.add_argument(
        "--min-market-cap-krw",
        type=int,
        default=0,
        help="신규 진입 종목 최소 시가총액(원). 0=필터 끔. 예: 5000000000000 = 5조 (대형주만)",
    )
    p.add_argument(
        "--leaders-market-tp",
        default="000",
        help="leaderboard 시장구분: 000=전체, 001=KOSPI만(대형주 전략), 101=KOSDAQ만",
    )
    p.add_argument(
        "--day-change-min",
        type=float,
        default=1.0,
        help="신규 후보 당일 상승률 하한(%%). 대형주 전략은 0.5 권장",
    )
    p.add_argument(
        "--day-change-max",
        type=float,
        default=29.5,
        help="신규 후보 당일 상승률 상한(%%). 대형주 전략은 10 권장",
    )
    p.add_argument(
        "--entry-mode",
        default="momentum",
        choices=["momentum", "below_ma"],
        help="진입 전략: momentum(급등 추격) | below_ma(이평 하회 눌림목 매수)",
    )
    p.add_argument(
        "--ma-period",
        type=int,
        default=20,
        help="below_ma 모드 이동평균 기간(일). 기본 20",
    )
    p.add_argument(
        "--record-candidate-scores",
        action="store_true",
        help=(
            "밴드 통과 후보의 점수 분포를 /app/output/candidate_scores.jsonl에 "
            "누적(관측 전용). dispatch는 임계를 넘긴 순간만 남기므로, 임계가 "
            "적정한지 판단하려면 그 아래 분포가 필요하다"
        ),
    )
    p.add_argument(
        "--enable-realtime-orders",
        action="store_true",
        help=(
            "키움 실시간 주문체결(00) 스트림을 구독해 원장 대사를 즉시 반영. "
            "폴링(ka10075/ka10076)이 여전히 진실원천이고 이건 지연을 줄일 뿐이다 "
            "— 소켓이 끊긴 동안의 이벤트는 재전송되지 않는다. 즉시 체결된 주문이 "
            "미체결 목록에 안 떠서 원장이 SUBMITTED로 멈추던 문제(2026-08-26)를 "
            "겨냥한다"
        ),
    )
    p.add_argument(
        "--universe-mode",
        default=UNIVERSE_LEADERS,
        choices=list(UNIVERSE_MODES),
        help=(
            "후보 유니버스: leaders(등락률·거래량·거래대금 상위 = 오늘 움직인 종목) "
            "| roster(고정 대형주 풀) | both. below_ma는 조용한 눌림목을 사므로 "
            "movers 리더보드와 거의 겹치지 않는다 — src/constants/universe.py 참고"
        ),
    )
    p.add_argument("--api-failure-threshold", type=int, default=3)
    p.add_argument("--unfilled-threshold", type=int, default=5)
    p.add_argument("--periodic-review-minutes", type=int, default=30)
    p.add_argument(
        "--regime-stability-ticks",
        type=int,
        default=3,
        help=(
            "regime_flip fires only after the new label holds for this many "
            "consecutive ticks. At 3 (90s at poll=30) a breadth reading "
            "sitting on the 0.85 risk_off line woke the PM squad six times on "
            "2026-09-22. Dispatch only: the entry veto is recomputed every "
            "tick and extreme_risk_off ignores this window."
        ),
    )

    p.add_argument("--cooldown-seconds", type=int, default=300)
    p.add_argument("--agent-timeout-seconds", type=int, default=180)
    p.add_argument("--agent-poll-seconds", type=int, default=10)
    p.add_argument(
        "--disable-agent-peer-review",
        action="store_true",
        help="Disable peer cross-review after a consequential primary ACTION",
    )
    p.add_argument(
        "--agent-peer-review-timeout-seconds",
        type=int,
        default=60,
        help="Timeout for the peer-review run",
    )
    p.add_argument(
        "--agent-peer-review-poll-seconds",
        type=int,
        default=10,
        help="Polling interval for peer-review runs",
    )
    p.add_argument(
        "--disable-agent-arbitration",
        action="store_true",
        help="Disable coordinator arbitration when primary and peer ACTION differ",
    )
    p.add_argument(
        "--agent-arbitration-timeout-seconds",
        type=int,
        default=60,
        help="Timeout for coordinator arbitration runs",
    )
    p.add_argument(
        "--agent-arbitration-poll-seconds",
        type=int,
        default=10,
        help="Polling interval for coordinator arbitration runs",
    )
    p.add_argument("--stale-price-delta-pct", type=float, default=1.5)

    p.add_argument(
        "--notify-routine-pm-actions",
        action="store_true",
        help=(
            "Send Discord pings even for routine PM HOLD/ACKNOWLEDGE on "
            "periodic_review and regime_flip. Default off — these fire every "
            "30 min and were drowning out the signal channel."
        ),
    )

    # Daily new-entry circuit breaker. All default to 0 = disabled, so the
    # watcher behaves exactly as before unless one is set. These gate NEW
    # BUYS ONLY — stop-loss, take-profit, agent sells and stale-order cancels
    # keep working while the breaker is tripped.
    p.add_argument(
        "--max-daily-loss-pct",
        type=float,
        default=0.0,
        help=(
            "Stop opening new positions once today's account loss reaches this "
            "percent of total assets. Positive magnitude (e.g. 3.0 = -3%%). "
            "0 disables. Latches for the KST trading day; resets next trading day."
        ),
    )
    p.add_argument(
        "--max-daily-loss-krw",
        type=int,
        default=0,
        help=(
            "Stop opening new positions once today's account loss reaches this "
            "many KRW. Positive magnitude. 0 disables."
        ),
    )
    p.add_argument(
        "--max-daily-new-entries",
        type=int,
        default=0,
        help=(
            "Maximum new positions opened per KST trading day. 0 disables. "
            "Counts submitted AND unknown-state orders. Needs no broker P&L, "
            "so this limit is usable today without the acknowledgement below."
        ),
    )
    p.add_argument(
        "--acknowledge-daily-loss-source-verified",
        action="store_true",
        help=(
            "Assert that Kiwoom's daily P&L field (kt00004 `tdy_lspft`) has "
            "been validated against a LIVE account: realized-only vs "
            "unrealized-inclusive, sign convention, and whether commission "
            "and tax are already deducted. WITHOUT this flag the two loss "
            "limits above are armed but NOT enforceable and block every new "
            "entry outright, because a below-threshold reading from a source "
            "of unknown meaning is not evidence of a safe account. "
            "Protective sells, stop-loss, take-profit and cancels are never "
            "affected either way. Do not set this without doing the "
            "validation — see services/daily_risk.py for the procedure."
        ),
    )

    p.add_argument(
        "--execute-orders",
        action="store_true",
        help=(
            "Mode-aware order routing. In mock mode all orders submit. "
            "In live mode ALSO requires KIWOOM_LIVE_CONFIRM=YES_I_REALLY_WANT_TO_TRADE."
        ),
    )
    p.add_argument(
        "--disable-new-entries",
        action="store_true",
        help="Block all new buys while leaving protective sells and order cancellations enabled",
    )
    p.add_argument(
        "--status-port",
        type=int,
        default=int(os.environ.get("KIWOOM_WATCHER_STATUS_PORT", "0") or 0),
        help=(
            "If set (>0), expose an in-process Starlette HTTP server on this "
            "port serving /state /recent /health for the dashboard."
        ),
    )
    p.add_argument(
        "--status-host",
        default=os.environ.get("KIWOOM_WATCHER_STATUS_HOST", "0.0.0.0"),
        help="Bind host for the status server",
    )
    p.add_argument(
        "--log-level",
        default=os.environ.get("KIWOOM_WATCHER_LOG_LEVEL", "INFO"),
    )
    return p


def _build_config(args: argparse.Namespace) -> WatcherConfig:
    return WatcherConfig(
        poll_interval_seconds=args.poll_interval_seconds,
        off_hours_interval_seconds=args.off_hours_interval_seconds,
        stop_loss_pct=args.stop_loss_pct,
        hard_take_profit_pct=args.hard_take_profit_pct,
        stale_unfilled_minutes=args.stale_unfilled_minutes,
        holding_swing_pct=args.holding_swing_pct,
        intraday_high_drop_pct=args.intraday_high_drop_pct,
        holding_dedup_profit_delta_pct=args.holding_dedup_profit_delta_pct,
        candidate_dedup_score_delta=args.candidate_dedup_score_delta,
        new_candidate_min_score=args.new_candidate_min_score,
        api_failure_threshold=args.api_failure_threshold,
        unfilled_threshold=args.unfilled_threshold,
        periodic_review_minutes=args.periodic_review_minutes,
        regime_stability_ticks=args.regime_stability_ticks,
        stale_price_delta_pct=args.stale_price_delta_pct,
        cooldown_seconds=args.cooldown_seconds,
        agent_timeout_seconds=args.agent_timeout_seconds,
        agent_poll_seconds=args.agent_poll_seconds,
        agent_peer_review_enabled=not args.disable_agent_peer_review,
        agent_peer_review_timeout_seconds=args.agent_peer_review_timeout_seconds,
        agent_peer_review_poll_seconds=args.agent_peer_review_poll_seconds,
        agent_arbitration_enabled=not args.disable_agent_arbitration,
        agent_arbitration_timeout_seconds=args.agent_arbitration_timeout_seconds,
        agent_arbitration_poll_seconds=args.agent_arbitration_poll_seconds,
        leaders_limit=args.leaders_limit,
        candidate_limit=args.candidate_limit,
        max_positions=args.max_positions,
        max_new_positions=args.max_new_positions,
        position_budget_pct=args.position_budget_pct,
        auto_buy_min_score=args.auto_buy_min_score,
        candidate_scan_multiplier=args.candidate_scan_multiplier,
        min_market_cap_krw=args.min_market_cap_krw,
        leaders_market_tp=args.leaders_market_tp,
        day_change_min=args.day_change_min,
        day_change_max=args.day_change_max,
        entry_mode=args.entry_mode,
        universe_mode=args.universe_mode,
        record_candidate_scores=args.record_candidate_scores,
        enable_realtime_orders=args.enable_realtime_orders,
        ma_period=args.ma_period,
        stock_detail_cache_ttl_seconds=args.stock_detail_cache_ttl_seconds,
        watchlist=parse_watchlist_arg(args.watchlist) or [],
        max_daily_loss_pct=args.max_daily_loss_pct,
        max_daily_loss_krw=args.max_daily_loss_krw,
        max_daily_new_entries=args.max_daily_new_entries,
        daily_loss_source_verified=bool(
            args.acknowledge_daily_loss_source_verified
        ),
        execute_orders=bool(args.execute_orders),
        new_entries_enabled=not args.disable_new_entries,
        notify_routine_pm_actions=bool(args.notify_routine_pm_actions),
    )


async def _run(args: argparse.Namespace) -> int:
    settings = Settings()

    confirm_live = False
    if args.execute_orders and not settings.use_mock:
        if os.environ.get("KIWOOM_LIVE_CONFIRM") != "YES_I_REALLY_WANT_TO_TRADE":
            print(
                "--execute-orders in LIVE mode requires env "
                "KIWOOM_LIVE_CONFIRM=YES_I_REALLY_WANT_TO_TRADE. Aborting.",
                file=sys.stderr,
            )
            return 2
        confirm_live = True

    config = _build_config(args)
    config.confirm_live_orders = confirm_live

    watcher = IntradayWatcher(settings, config)

    loop = asyncio.get_running_loop()

    def _on_signal(sig: int) -> None:
        logging.getLogger("kiwoom.watcher").info("signal %d — stopping", sig)
        watcher.stop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _on_signal, sig)
        except NotImplementedError:
            # Windows / non-mainthread fallback: rely on KeyboardInterrupt
            pass

    if args.status_port > 0:
        # Run watcher loop and status HTTP server concurrently. The server
        # exits cleanly when the watcher's stop() flips the asyncio Event,
        # because uvicorn.Server respects should_exit.
        from src.services.watcher_status_server import build_status_app
        import uvicorn

        app = build_status_app(watcher.status, ledger_view=watcher.ledger_view)
        config_uv = uvicorn.Config(
            app,
            host=args.status_host,
            port=args.status_port,
            log_level=str(args.log_level).lower(),
            access_log=False,
            lifespan="off",
        )
        server = uvicorn.Server(config_uv)

        async def _stop_server_when_watcher_stops() -> None:
            # Poll the watcher's stop event; once tripped, signal uvicorn.
            while not watcher._stop_event.is_set():
                try:
                    await asyncio.wait_for(watcher._stop_event.wait(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
            server.should_exit = True

        await asyncio.gather(
            watcher.run(),
            server.serve(),
            _stop_server_when_watcher_stops(),
        )
    else:
        await watcher.run()
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    logging.basicConfig(
        level=getattr(logging, str(args.log_level).upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    try:
        return asyncio.run(_run(args))
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
