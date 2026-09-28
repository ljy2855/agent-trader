"""Continuous intraday watcher — replaces the 30-min cron with a
trigger-driven loop that hands soft judgment off to Multica agents.

Architecture (matches the agreed design):

* **Tier 1** — hard, deterministic rules execute immediately in code:
  stop-loss, hard take-profit, ``max_positions`` overflow, stale
  unfilled order. No agent consult; no waiting.
* **Tier 2** — soft judgments dispatch a comment to a Multica per-stock
  or per-role issue, asynchronously poll the agent's next completed
  run, and either apply the parsed ACTION tag or discard it on stale
  state.

Concurrency model:

* Per-stock lock: at most one in-flight Tier-2 dispatch per stock.
* Per-role global lock for portfolio-level dispatches (PM, risk).
* Cooldown window per ``(scope, trigger_type)`` to prevent flapping.
* 90-second agent timeout; on timeout the slot is cleared and an
  incident comment posted.
* Stale check on response: if the *current* observation diverges from
  the snapshot captured at trigger time (price ±X%, regime flip,
  position state changed), the ACTION is discarded and the watcher
  re-evaluates on the next tick.

The watcher reuses ``plan_intraday_momentum_strategy`` to source its
state (holdings, regime, candidate scores, open orders). It calls the
planner with ``execute_orders=False`` — order routing is the watcher's
job, gated by tier and ACTION.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from collections import deque
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timedelta
from math import floor, isfinite
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo

from ..config import Settings
from . import order as order_service
from . import watcher_triggers as triggers
from .discord_notify import DiscordNotifier
from .kiwoom_client import KiwoomClient
from .daily_risk import (
    DailyEntryBreaker,
    DailyRiskLimits,
    read_account_daily_snapshot,
)
from ..constants.universe import UNIVERSE_LEADERS
from .candidate_journal import CandidateJournal, in_band as journal_in_band
from .krx_calendar import (
    SESSION_CLOSED,
    SESSION_UNCERTAIN,
    KrxSessionStatus,
    is_krx_regular_session_open,
    krx_regular_session_status,
)
from .multica_dispatch import MulticaDispatcher, extract_action_tag
from . import order_ledger
from .order_ledger import (
    STORAGE_NETWORK,
    LedgerStorageSafety,
    OrderLedger,
    OrderLedgerError,
    UnsafeLedgerStorageError,
)
from .order_result import (
    EXPOSURE_STATES,
    ORDER_STATE_FAILED,
    ORDER_STATE_FILLED,
    ORDER_STATE_SUBMITTED,
    ORDER_STATE_UNKNOWN,
    OrderApplyResult,
)
from .realtime_stream import RealtimeOrderStream
from .strategy import (
    _normalize_holding_rows,
    _safe_budget_amount,
    _score_candidate,
    plan_intraday_momentum_strategy,
    to_price,
)
from .watcher_status import (
    TriggerLogEntry,
    WatcherStatusRegistry,
    summarize_candidates,
)
from .watcher_triggers import (
    ROLE_EVALUATOR,
    ROLE_PM,
    ROLE_RISK,
    ROLE_SCREENER,
    ROLE_SELF,
    TriggerEvent,
)

KST = ZoneInfo("Asia/Seoul")
DEFAULT_STATE_PATH = (
    Path(__file__).resolve().parents[2] / "output" / "watcher_state.json"
)
DEFAULT_CANDIDATE_JOURNAL_PATH = (
    Path(__file__).resolve().parents[2] / "output" / "candidate_scores.jsonl"
)

log = logging.getLogger("kiwoom.watcher")


# ---------------------------------------------------------------------------
# Failure attribution
# ---------------------------------------------------------------------------

# Pipeline stage an operational failure is attributed to. ``api_failure_count``
# only ever tracked the planner, so an account/market/multica outage *after*
# the planner returned left every counter at zero while the tick silently
# degraded (P1-3). Each category counts failures for the life of the process
# and remembers the most recent one, so `/state` answers both "what is
# breaking" and "when did it last break".
FAILURE_PLANNER = "planner"
FAILURE_ACCOUNT = "account"
FAILURE_MARKET = "market"
FAILURE_MULTICA = "multica"
FAILURE_ORDER = "order"
FAILURE_TIER2_TASK = "tier2_task"

FAILURE_CATEGORIES = (
    FAILURE_PLANNER,
    FAILURE_ACCOUNT,
    FAILURE_MARKET,
    FAILURE_MULTICA,
    FAILURE_ORDER,
    FAILURE_TIER2_TASK,
)

# How many failing reads to name before truncating. A cycle can degrade every
# leg at once (a DNS fault does exactly that), and the detail string goes to
# `/state`, Discord and the trigger log.
_MAX_DEGRADED_SOURCES = 4


def _describe_degraded_sources(result: dict[str, Any]) -> str:
    """Summarize which upstream reads made a cycle report success=False."""

    degraded = result.get("degraded_sources")
    if not isinstance(degraded, list) or not degraded:
        # Older plan payloads (and stubs) carry no breakdown. Say so plainly
        # rather than echoing the plan's fixed success message.
        return "planner success=false (no source breakdown)"

    parts: list[str] = []
    for entry in degraded[:_MAX_DEGRADED_SOURCES]:
        if not isinstance(entry, dict):
            continue
        name = entry.get("source") or "unknown"
        cause = entry.get("error") or entry.get("return_msg")
        parts.append(f"{name}: {cause}" if cause else str(name))
    remaining = len(degraded) - len(parts)
    if remaining > 0:
        parts.append(f"(+{remaining} more)")
    return "planner degraded — " + "; ".join(parts)

# Credentials that can surface inside an exception message — multica CLI
# output echoes argv, httpx errors embed URLs, and Kiwoom errors can carry
# auth headers. Detail strings land in Discord, `/state` and the trigger log,
# so they get scrubbed on the way out.
_SECRET_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"(?i)bearer\s+[\w\-.=+/]+"), "Bearer ***"),
    (
        re.compile(
            # The key may be quoted (JSON) or bare (argv), hence the optional
            # quotes on both sides of the separator.
            r"(?i)\b(appkey|secretkey|secret|token|password|authorization|api[-_]?key)"
            r"\b[\"']?\s*[=:]\s*[\"']?[\w\-.=+/]+[\"']?"
        ),
        r"\1=***",
    ),
)

# Discord embeds and the trigger log both stay readable well under this.
_ERROR_DETAIL_LIMIT = 300


def sanitize_error_detail(
    error: BaseException | str, *, limit: int = _ERROR_DETAIL_LIMIT
) -> str:
    """Render an exception as a short, secret-free, single-line string.

    Raw exception text is not safe to publish: multica CLI failures quote the
    command line, and httpx errors quote URLs. Collapsing to one line also
    keeps a multi-page stack dump from flooding a Discord embed — the full
    traceback still goes to the structured log via ``log.exception``.
    """

    if isinstance(error, BaseException):
        message = str(error).strip()
        text = f"{type(error).__name__}: {message}" if message else type(error).__name__
    else:
        text = str(error).strip()

    for pattern, replacement in _SECRET_PATTERNS:
        text = pattern.sub(replacement, text)
    text = " ".join(text.split())
    if len(text) > limit:
        text = text[: limit - 1] + "…"
    return text


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class WatcherConfig:
    """Runtime configuration for the watcher."""

    # Polling cadence
    poll_interval_seconds: int = 30
    off_hours_interval_seconds: int = 600

    # Tier 1 thresholds
    stop_loss_pct: float = -3.0
    hard_take_profit_pct: float = 8.0
    stale_unfilled_minutes: int = 5

    # Tier 2 thresholds
    holding_swing_pct: float = 2.0
    intraday_high_drop_pct: float = 1.5
    # Skip re-dispatching a holding_swing when the prior ACTION for that stock
    # was a no-op (HOLD/ACKNOWLEDGE) and profit_rate has moved less than this
    # since — a held name idling in the ±2% band re-fired every cooldown and
    # burned agent calls (엠앤씨솔루션 6/16: 20+ HOLD repeats). 0 disables.
    holding_dedup_profit_delta_pct: float = 1.5
    # Skip re-dispatching a new_candidate the screener already REJECTed,
    # until its score improves by at least this much. Scores oscillate
    # across the gate tick by tick, so a name that qualifies, gets
    # rejected, drops a point and re-qualifies looks 'newly qualified'
    # again every cooldown: 2026-08-25 spent 113 dispatches on 7 names
    # (셀트리온 36, LG화학 28), every one REJECT, and exhausted the
    # agent-backend quota mid-session. 0 disables.
    candidate_dedup_score_delta: float = 1.0
    new_candidate_min_score: int = 14
    api_failure_threshold: int = 3
    unfilled_threshold: int = 5
    periodic_review_minutes: int = 30

    # Regime debounce: emit regime_flip only when the new label persists
    # for this many consecutive ticks. extreme_risk_off ignores this and
    # fires immediately (a crash needs an immediate notification).
    regime_stability_ticks: int = 3

    # Stale-check on agent response
    stale_price_delta_pct: float = 1.5

    # Cooldown per (scope_key, trigger_type) — suppress re-fires
    cooldown_seconds: int = 300

    # Agent timeout. Bumped after dry-runs showed cold-start + live-data
    # checks pushing PM cycles past the old boundary.
    agent_timeout_seconds: int = 180
    agent_poll_seconds: int = 10
    agent_peer_review_enabled: bool = True
    agent_peer_review_timeout_seconds: int = 60
    agent_peer_review_poll_seconds: int = 10
    agent_arbitration_enabled: bool = True
    agent_arbitration_timeout_seconds: int = 60
    agent_arbitration_poll_seconds: int = 10

    # Strategy params (passthrough to plan_intraday_momentum_strategy)
    leaders_limit: int = 10
    candidate_limit: int = 5
    max_positions: int = 3
    max_new_positions: int = 1
    position_budget_pct: int = 10
    auto_buy_min_score: int = 14
    candidate_scan_multiplier: int = 2
    stock_detail_cache_ttl_seconds: float = 75.0
    min_market_cap_krw: int = 0  # 0 = filter off; >0 restricts new entries to large-caps
    leaders_market_tp: str = "000"  # "001" = KOSPI-only universe (large-cap strategy)
    day_change_min: float = 1.0  # candidate entry band lower bound (%) — momentum mode
    day_change_max: float = 29.5  # candidate entry band upper bound (%) — momentum mode
    entry_mode: str = "momentum"  # "momentum" | "below_ma" (mean-reversion 눌림목)
    ma_period: int = 20  # below_ma mode: MA length
    universe_mode: str = UNIVERSE_LEADERS  # leaders | roster | both
    # Append in-band candidate scores to /app/output for gate calibration.
    record_candidate_scores: bool = False
    # Subscribe to Kiwoom's realtime 주문체결 stream and feed its rows to the
    # ledger. Off by default: the polled reconciliation is the authority and
    # works without it, so this is an accelerator that has to earn its place
    # in a live session before it becomes the default.
    enable_realtime_orders: bool = False
    watchlist: list[str] = field(default_factory=list)

    # Daily new-entry circuit breaker. All three default to 0 = disabled so
    # existing deployments behave exactly as before until opted in. Only the
    # buy path consults these; sells, stop-loss, take-profit and cancels are
    # never gated. See services/daily_risk.py.
    max_daily_loss_pct: float = 0.0
    max_daily_loss_krw: int = 0
    max_daily_new_entries: int = 0
    # Operator acknowledgement that the daily-loss source (`tdy_lspft`) has
    # been validated against a live account. Until this is set, the two loss
    # limits above are armed but NOT enforceable and block new entries
    # outright — see services/daily_risk.py "Loss-source verification".
    # Never set this from code.
    daily_loss_source_verified: bool = False

    # Execution gates — same shape as strategy_cycle.py
    execute_orders: bool = False
    confirm_live_orders: bool = False
    new_entries_enabled: bool = True

    # Discord notification filtering. By default we skip the noisy
    # `periodic_review` HOLD/ACKNOWLEDGE pings (PM standby reports every
    # 30 min when nothing changed) so the channel stays signal-heavy.
    # Set true via `--notify-routine-pm-actions` for verbose debugging.
    notify_routine_pm_actions: bool = False


# Tier-1 suggested_actions that close the position itself. A decision formed
# before one of these is genuinely obsolete: the code path already sold. A
# cancel is deliberately absent — see `_handle_trigger`.
POSITION_CLOSING_ACTIONS = frozenset({"sell_market"})


# ---------------------------------------------------------------------------
# In-flight tracking
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class InFlightTask:
    """One Tier-2 dispatch awaiting an agent response."""

    scope_key: str
    trigger: TriggerEvent
    started_at: datetime
    issue_id: str
    task: asyncio.Task[Any]


# ---------------------------------------------------------------------------
# Watcher
# ---------------------------------------------------------------------------


def _format_profit_rate(rate: Any) -> str:
    """Render a holding's return, distinguishing "unknown" from "flat".

    Defaulting a missing rate to 0 tells the agent the position is flat when
    nobody actually knows, which is the worse of the two errors: a flat
    position invites HOLD.
    """

    if isinstance(rate, bool) or not isinstance(rate, (int, float)):
        return "수익률 미상"
    return f"{rate:+.2f}%"


def _best_bid_from_detail(
    detail: dict[str, Any] | None,
) -> tuple[int | None, str]:
    """Best bid for a protective sell, and why there isn't one when there isn't.

    Selling a limit at the standing best bid is the "fills now, but never
    below what I saw" order. `buy_fpr_bid` is 최우선 매수호가 -- the same
    field `strategy` scores spreads from -- and it comes straight off the
    book, so it is already on a valid tick.

    Three ways to come back empty, and all three are ordinary rather than
    exceptional: `_is_still_valid` returns early without fetching on a
    global-scope trigger or a snapshot with no price, the book call can
    fail inside the bundle, and a stock can genuinely have no bid (a
    limit-down with the bid side cleared out). The caller exits at market
    for all three; the reason is returned so the log can say which.
    """

    if not detail:
        return None, "시세 번들 없음"
    orderbook = detail.get("orderbook") or {}
    if not orderbook:
        return None, "호가 조회 실패"
    bid = to_price(orderbook.get("buy_fpr_bid"))
    if not bid or bid <= 0:
        return None, "최우선 매수호가 없음"
    return bid, ""


class IntradayWatcher:
    """Continuous trigger-driven trader."""

    def __init__(
        self,
        settings: Settings,
        config: WatcherConfig,
        *,
        dispatcher: MulticaDispatcher | None = None,
        client: KiwoomClient | None = None,
        notifier: DiscordNotifier | None = None,
        status: WatcherStatusRegistry | None = None,
        state_path: Path = DEFAULT_STATE_PATH,
        breaker: DailyEntryBreaker | None = None,
        ledger: OrderLedger | None = None,
        ledger_mountinfo_reader: Callable[[], str] | None = None,
        candidate_journal: CandidateJournal | None = None,
    ):
        self._settings = settings
        self._config = config
        self._dispatcher = dispatcher or MulticaDispatcher()
        self._owns_client = client is None
        self._client = client or KiwoomClient(settings)
        mode_label = os.environ.get(
            "TRADING_MODE_LABEL",
            "🟡 MOCK" if settings.use_mock else "🔴 LIVE",
        )
        self._notifier = notifier or DiscordNotifier(
            username=f"Kiwoom Watcher {mode_label}",
            prefix=f"[{mode_label}] ",
        )
        self._status = status or WatcherStatusRegistry()
        self._state_path = state_path
        # Score-distribution journal (observability only — a write
        # failure is swallowed rather than risking the tick).
        self._candidate_journal = candidate_journal or CandidateJournal(
            DEFAULT_CANDIDATE_JOURNAL_PATH
            if config.record_candidate_scores
            else None
        )
        self._stop_event = asyncio.Event()
        self._buy_lock = asyncio.Lock()
        self._protective_trigger_at: dict[str, datetime] = {}
        # New-entry-only circuit breaker. Constructed even when every limit
        # is 0 so `/state` always reports its shape; a disabled breaker
        # allows everything.
        self._breaker = breaker or DailyEntryBreaker(
            DailyRiskLimits(
                max_daily_loss_pct=config.max_daily_loss_pct,
                max_daily_loss_krw=config.max_daily_loss_krw,
                max_daily_new_entries=config.max_daily_new_entries,
                loss_source_verified=config.daily_loss_source_verified,
            )
        )
        # Durable order-intent ledger. A construction failure is not fatal —
        # it degrades to "no new buys" while every protective path keeps
        # working, which is the policy in services/order_ledger.py.
        self._ledger: OrderLedger | None = ledger
        self._ledger_error: str | None = None
        self._ledger_storage_safety: LedgerStorageSafety | None = (
            ledger.storage_safety if ledger is not None else None
        )
        self._last_ledger_alert_reason: str | None = None
        if self._ledger is None:
            try:
                ledger_kwargs: dict[str, Any] = {}
                if ledger_mountinfo_reader is not None:
                    ledger_kwargs["mountinfo_reader"] = ledger_mountinfo_reader
                self._ledger = OrderLedger(**ledger_kwargs)
                self._ledger_storage_safety = self._ledger.storage_safety
            except UnsafeLedgerStorageError as exc:
                self._ledger_storage_safety = exc.safety
                self._ledger_error = sanitize_error_detail(exc)
                log.error("order ledger unavailable: %s", exc)
            except OrderLedgerError as exc:
                self._ledger_error = sanitize_error_detail(exc)
                log.error("order ledger unavailable: %s", self._ledger_error)
        # Most recent open-order rows, kept so the oversell guard and
        # reconciliation can run without re-querying the account.
        self._last_open_orders: list[dict[str, Any]] = []

        # Mutable state
        # Last breaker state-error we alerted on, so a persistent fault does
        # not re-page every tick.
        self._last_breaker_state_error: str | None = None
        self._last_calendar_uncertainty_reason: str | None = None
        self._warned_loss_source_unverified = False
        self._prev_holdings: dict[str, dict[str, Any]] = {}
        self._intraday_high: dict[str, float] = {}
        self._prev_regime: dict[str, Any] | None = None
        # Last regime label that we already announced as a flip — used as
        # the baseline for the next debounced flip detection.
        self._last_emitted_regime: str | None = None
        # Rolling window of regime labels for the N-tick debounce.
        self._regime_history: deque[str] = deque(
            maxlen=max(self._config.regime_stability_ticks, 1)
        )
        # Codes that *qualified* for dispatch last tick (eligible and at or
        # above the score gate) — not merely codes that were scanned.
        self._prev_qualified_codes: set[str] = set()
        self._api_failure_count: int = 0
        self._last_periodic_review_at: datetime | None = None
        self._cooldowns: dict[str, datetime] = {}  # cooldown_key -> expiry
        # Last applied holding ACTION per stock code: (action, profit_rate, at).
        # Used to skip re-dispatching a holding_swing that would just repeat a
        # no-op (HOLD) while the position idles — see holding_dedup gate.
        self._last_holding_action: dict[
            str, tuple[str, float | None, datetime, str]
        ] = {}
        self._realtime: RealtimeOrderStream | None = None
        # stock -> (ACTION, score, at) of the last screener verdict.
        self._last_candidate_action: dict[str, tuple[str, float | None, datetime]] = {}
        # The portfolio-exposure gates count holdings ∪ the watcher's own
        # in-flight buys, so an order that has not yet shown up in the
        # 30s-polled account still counts — that is what closed the race that
        # let 6/12 stack 5 orders past max_positions. That in-flight set used
        # to be an in-memory dict with a TTL, which a restart erased; it now
        # comes from the durable order ledger (`_ledger.unresolved_*`).
        self._in_flight: dict[str, InFlightTask] = {}
        self._last_known_run_id: dict[str, str] = {}  # issue_id -> run_id
        self._trigger_log: dict[str, TriggerLogEntry] = {}  # scope_key -> log entry
        self._cycle_count = 0
        self._last_tick_at: datetime | None = None
        self._last_error: str | None = None

    @property
    def status(self) -> WatcherStatusRegistry:
        """Read-only handle for the status server."""

        return self._status

    # -- public lifecycle -----------------------------------------------------

    async def run(self) -> None:
        """Run the watcher until ``stop`` is called or market closes."""

        log.info(
            "watcher start: mode=%s execute=%s poll=%ss",
            "mock" if self._settings.use_mock else "live",
            self._config.execute_orders,
            self._config.poll_interval_seconds,
        )
        # Read before the first tick overwrites it — see `set_last_session`.
        self._status.set_last_session(self._load_previous_state())
        self._status.mark_started(
            mode="mock" if self._settings.use_mock else "live",
            execute_orders=self._config.execute_orders,
            poll_interval_seconds=self._config.poll_interval_seconds,
            # Publish the effective config so observers read what this process is
            # actually running rather than reconstructing it from code defaults.
            config=asdict(self._config),
        )
        await self._notifier.info(
            "Watcher 시작",
            f"poll={self._config.poll_interval_seconds}s "
            f"execute_orders={self._config.execute_orders}",
        )
        if self._ledger_error:
            await self._alert_ledger_fault_once(self._ledger_error)
        # Settle anything left hanging by the previous process before we are
        # allowed to open new exposure. A crash between `INTENDED` and the API
        # call, or a lost response, leaves a row only the broker can resolve.
        # Both broker views, not just executions: an order left working at
        # the broker shows up in the open-order query and nowhere else, and
        # without it a still-live order would look unmatched forever.
        await self._reconcile_ledger(fetch_open_orders=True, fetch_executions=True)
        self._start_realtime_orders()
        try:
            while not self._stop_event.is_set():
                session = self._market_session_status()
                if session.state == SESSION_CLOSED:
                    await self._sleep_with_stop(
                        self._config.off_hours_interval_seconds
                    )
                    continue
                if session.state == SESSION_UNCERTAIN:
                    if session.reason != self._last_calendar_uncertainty_reason:
                        self._last_calendar_uncertainty_reason = session.reason
                        log.error(
                            "KRX calendar uncertain — protective cycle continues, "
                            "new buys fail closed: %s",
                            session.reason,
                        )
                        await self._safe_notify_error(
                            "⚠️ KRX 캘린더 불확실 — 신규 매수 차단",
                            f"{session.reason}\n"
                            "보호매도·Tier-1 손절·주문취소를 위해 감시 루프는 "
                            "계속 실행합니다.",
                        )
                else:
                    self._last_calendar_uncertainty_reason = None
                try:
                    await self._tick(now=session.observed_at)
                except Exception as exc:
                    self._last_error = str(exc)
                    self._status.mark_tick_error(str(exc))
                    log.exception("watcher tick failed: %s", exc)
                    if self._api_failure_count >= self._config.api_failure_threshold:
                        await self._notifier.error(
                            "Watcher 연속 오류",
                            f"연속 실패 {self._api_failure_count}회: {exc}",
                        )
                self._persist_state()
                await self._sleep_with_stop(self._config.poll_interval_seconds)
        finally:
            if self._realtime is not None:
                await self._realtime.stop()
            await self._cancel_in_flight()
            if self._owns_client:
                await self._client.close()
            log.info("watcher stop: cycles=%d", self._cycle_count)
            self._status.mark_stopped()
            await self._notifier.info(
                "Watcher 종료",
                f"cycles={self._cycle_count} last_error={self._last_error or '없음'}",
            )

    # -- realtime order stream ----------------------------------------------

    def _start_realtime_orders(self) -> None:
        """Subscribe to 주문체결, if enabled and there is a ledger to feed."""

        if not self._config.enable_realtime_orders:
            return
        if self._ledger is None:
            log.info("realtime orders disabled: no ledger to reconcile into")
            return
        self._realtime = RealtimeOrderStream(
            self._settings,
            self._client.token_manager.get_valid_token,
            self._on_realtime_rows,
            on_rejection=self._on_realtime_rejection,
            # Without this the socket replays a cached token forever once it
            # expires — which is what happens over a weekend, when REST stops
            # polling and nothing else refreshes it.
            refresh_token=self._client.token_manager.force_refresh,
        )
        self._realtime.start()

    async def _on_realtime_rows(self, rows: list[dict[str, Any]]) -> None:
        """Reconcile the ledger against a pushed order event.

        Fed as ``executions`` because a 주문체결 frame reports what the broker
        did to an order, which is what the execution view carries; the
        open-order argument is left out so an absent working order is never
        inferred from a stream that only speaks about orders it mentions.

        ``broker_views_complete=False`` is the important part. That flag is
        what licenses the UNKNOWN protective-sell release, and this is a
        single event about a single order -- not the fully paginated
        both-views sweep that release rule requires. Only the polled path
        gets to make that claim.
        """

        if self._ledger is None:
            return
        try:
            report = self._ledger.reconcile(
                executions=rows, broker_views_complete=False
            )
        except OrderLedgerError as exc:
            self._record_failure(FAILURE_ORDER, exc)
            return
        if report.resolved or report.adopted_order_no:
            log.info("realtime reconciled: %s", report.to_dict())

    async def _on_realtime_rejection(self, ident: str, reason: str) -> None:
        """Surface a broker refusal the moment it happens.

        Worth its own path because a rejection used to reach only Discord and
        the ledger's `reason` column: on 2026-08-31 seven exits were refused
        308003 and the logs said nothing at all.
        """

        log.warning("realtime order rejected: %s — %s", ident, reason)
        await self._safe_notify_error(
            "주문 거부 (실시간)", f"{ident} — {reason}"
        )

    def stop(self) -> None:
        """Signal the watcher loop to exit at the next checkpoint."""

        self._stop_event.set()

    # -- one tick -------------------------------------------------------------

    async def _tick(self, *, now: datetime | None = None) -> None:
        """Run the planner once and dispatch any newly-fired triggers."""

        self._cycle_count += 1
        self._last_tick_at = now or datetime.now(KST)
        protective_holdings_observed = False

        async def observe_holdings(rows: list[dict[str, Any]]) -> None:
            nonlocal protective_holdings_observed
            protective_holdings_observed = True
            await self._handle_protective_holdings(rows)

        try:
            result = await plan_intraday_momentum_strategy(
                self._client,
                self._settings,
                watchlist=self._config.watchlist or None,
                leaders_limit=self._config.leaders_limit,
                candidate_limit=self._config.candidate_limit,
                max_positions=self._config.max_positions,
                max_new_positions=self._config.max_new_positions,
                position_budget_pct=self._config.position_budget_pct,
                execute_orders=False,
                auto_buy_min_score=self._config.auto_buy_min_score,
                candidate_scan_multiplier=self._config.candidate_scan_multiplier,
                stock_detail_cache_ttl_seconds=self._config.stock_detail_cache_ttl_seconds,
                min_market_cap_krw=self._config.min_market_cap_krw,
                leaders_market_tp=self._config.leaders_market_tp,
                day_change_min=self._config.day_change_min,
                day_change_max=self._config.day_change_max,
                entry_mode=self._config.entry_mode,
                ma_period=self._config.ma_period,
                universe_mode=self._config.universe_mode,
                holding_observer=observe_holdings,
            )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            self._api_failure_count += 1
            self._record_failure(FAILURE_PLANNER, exc)
            log.warning("planner failed (%s consecutive)", self._api_failure_count)
            raise

        # `_api_failure_count` means "how many consecutive cycles have had a
        # broken data path", and it gates the risk-manager health trigger. It
        # is therefore resolved once, after every required path of this cycle
        # has been attempted — resetting it the moment the planner succeeded
        # meant a permanently-failing account query bumped it 0 → 1 every
        # tick and the threshold was unreachable. A cycle counts once no
        # matter how many of its paths broke.
        cycle_failed = False

        if not result.get("success"):
            cycle_failed = True
            # `message` is a fixed string on both the success and failure paths,
            # so recording it produced a counter that said "Built intraday
            # strategy plan" 140 times and never said what broke. Name the
            # failing reads instead, and log them: this path swallows market
            # transport errors into success=False without raising, so the log
            # line is the only trace once /state is overwritten.
            detail = _describe_degraded_sources(result)
            self._record_failure(FAILURE_PLANNER, detail)
            log.warning("planner degraded: %s", detail)

        holdings = self._enrich_holdings(result.get("holdings", []))
        regime = result.get("regime", {}) or {}
        candidate_rows = result.get("candidate_rows", []) or []

        # The first gate a candidate meets, computed once here and handed
        # to both the journal and the detector below. Two copies of this
        # arithmetic would be free to drift, which is how the stale-cancel
        # parser went three months without firing.
        available_slots = min(
            max(self._config.max_positions - len(holdings), 0),
            self._config.max_new_positions,
        )

        # Record what the scorer saw before any gate consumes it. Only a
        # dispatch survives otherwise, and a dispatch by definition already
        # cleared the gate — so the scores that fell short, the ones that say
        # whether the gate is set right, were never observable. `available_slots`
        # rides along because at zero the detector returns before building any
        # event: the screener is never asked, and without this the day leaves
        # no record that there was anything to ask about.
        self._candidate_journal.record(
            # `now` is an optional test hook and may be None; `_last_tick_at`
            # is the resolved timestamp this tick already settled on.
            now=self._last_tick_at,
            regime=regime,
            candidate_rows=candidate_rows,
            min_score=self._config.new_candidate_min_score,
            available_slots=available_slots,
            holding_count=len(holdings),
        )
        # Same fact, published where the digest can see it. The journal lives
        # on the watcher's PVC; the digest only speaks HTTP.
        qualifying = [
            row
            for row in candidate_rows
            if isinstance(row, dict)
            and row.get("eligible")
            and (row.get("score") or 0) >= self._config.new_candidate_min_score
        ]
        top = max(qualifying, key=lambda r: r.get("score") or 0, default=None)
        self._status.record_candidate_slots(
            trading_day=self._last_tick_at.astimezone(KST).strftime("%Y-%m-%d"),
            available_slots=available_slots,
            top_score=(top or {}).get("score"),
            top_name=(top or {}).get("stock_name") or (top or {}).get("stock_code"),
        )
        self._status.set_candidates(
            summarize_candidates(
                candidate_rows,
                min_score=self._config.new_candidate_min_score,
                available_slots=available_slots,
                at=self._last_tick_at.isoformat() if self._last_tick_at else None,
                in_band=journal_in_band,
            )
        )
        portfolio = result.get("portfolio", {}) or {}

        # Feed the new-entry breaker before any trigger is handled, so a
        # candidate firing this tick is judged against this tick's account
        # state. Exits are never gated by it.
        await self._update_entry_breaker(portfolio, now=now)

        open_order_count = int(portfolio.get("open_order_count") or 0)
        # Open-order rows aren't returned by the planner, so fetch them when
        # anything needs them. Two independent reasons, and the ledger's is
        # not derivable from the stale-cancel config: an unresolved intent
        # must be reconciled even with `stale_unfilled_minutes=0` or a
        # planner that reports `open_order_count=0`.
        wants_stale_check = (
            open_order_count > 0 and self._config.stale_unfilled_minutes > 0
        )
        wants_reconcile = self._has_unresolved_intents()
        wants_sell_absence_check = (
            wants_reconcile and self._has_unknown_sell_intents()
        )
        open_orders: list[dict[str, Any]] = []
        open_orders_complete = False
        reconcile_executions: list[dict[str, Any]] = []
        executions_complete = False
        if wants_stale_check or wants_reconcile:
            try:
                open_orders = await self._fetch_open_orders()
                self._last_open_orders = open_orders
                open_orders_complete = True
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001 - degrade, don't abort
                # Losing this query only costs us stale-order detection for one
                # tick. Letting it abort `_tick` cost us the *whole* tick —
                # stop-loss detection included — while leaving every failure
                # counter at zero (P1-3). The cached view is left alone so the
                # oversell guard keeps its last good data.
                cycle_failed = True
                detail = self._record_failure(FAILURE_ACCOUNT, exc)
                log.warning("open-order fetch failed: %s", detail)

        # Executions are the only view that can settle an order which never
        # rested on the book. A marketable buy that fills on submission is
        # absent from the open-order list from the very first poll, so an
        # open-order-only reconciliation can never advance it past SUBMITTED:
        # 2026-08-26 held KB금융 all session while its intent stayed unresolved
        # and warned 708 times, blocking further buys of that code. Fetch this
        # whenever anything is unresolved, not just for the UNKNOWN-sell
        # release — one extra call per tick, and only while work is pending.
        #
        # `broker_views_complete` stays gated on the sell-absence check below:
        # that flag licenses the bounded RELEASE of a protective sell, which
        # is a much stronger claim than "this buy filled".
        if wants_reconcile:
            try:
                reconcile_executions = await self._fetch_executions()
                executions_complete = True
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001 - exits still continue
                cycle_failed = True
                detail = self._record_failure(FAILURE_ACCOUNT, exc)
                log.warning("execution fetch failed during reconciliation: %s", detail)

        # Both required data paths have now been attempted, so the consecutive
        # counter can be settled. It must be settled before the triggers are
        # built — `detect_tier2_global_health` reads it below.
        if cycle_failed:
            self._api_failure_count += 1
            log.warning(
                "cycle data path degraded (%d consecutive)", self._api_failure_count
            )
        else:
            self._api_failure_count = 0

        # Settle whatever this tick's broker view can explain. Open orders
        # normally suffice; UNKNOWN protective sells additionally pay for the
        # execution view because only a complete pair may advance RELEASED.
        if wants_reconcile:
            await self._reconcile_ledger(
                open_orders=self._last_open_orders,
                executions=reconcile_executions,
                broker_views_complete=(
                    open_orders_complete and executions_complete
                    if wants_sell_absence_check
                    else False
                ),
            )

        events: list[TriggerEvent] = []
        if not protective_holdings_observed:
            events += triggers.detect_tier1_holding_rules(
                holdings,
                stop_loss_pct=self._config.stop_loss_pct,
                hard_take_profit_pct=self._config.hard_take_profit_pct,
            )
            events += triggers.detect_tier1_position_overflow(
                holdings, max_positions=self._config.max_positions
            )
        events += triggers.detect_tier1_stale_orders(
            open_orders, stale_minutes=self._config.stale_unfilled_minutes
        )
        events += triggers.detect_tier2_holding_swings(
            holdings,
            self._prev_holdings,
            swing_pct=self._config.holding_swing_pct,
            high_drop_pct=self._config.intraday_high_drop_pct,
        )
        events += triggers.detect_tier2_new_candidates(
            candidate_rows,
            self._prev_qualified_codes,
            min_score=self._config.new_candidate_min_score,
            available_slots=available_slots,
        )
        # Regime debounce: only emit regime_flip when the new label has
        # been stable across N consecutive ticks. This stops borderline
        # ±0.1 KOSPI/KOSDAQ noise from flipping the global PM trigger
        # multiple times per session. extreme_risk_off skips the gate —
        # a real crash needs an immediate signal, not a debounce wait.
        # A degraded index read classifies as "risk_off" off zeroed breadth,
        # so a tick without a complete read sits out the debounce entirely:
        # it can't enter the stability window, can't become the baseline, and
        # can't fabricate the recovery flip ("risk_off -> risk_on"). The whole
        # block is skipped rather than just the append — `_last_emitted_regime`
        # is the record of what we announced, and advancing it on a tick whose
        # trigger the detector suppresses would consume a flip we never sent.
        cur_regime_label = (regime or {}).get("regime")
        regime_complete = bool((regime or {}).get("market_data_complete", True))
        if regime_complete:
            if cur_regime_label:
                self._regime_history.append(cur_regime_label)
            regime_baseline = self._build_regime_flip_baseline(cur_regime_label)
            if regime_baseline is not None:
                events += triggers.detect_tier2_regime_label_flip(
                    regime, regime_baseline
                )
                self._last_emitted_regime = cur_regime_label
        events += triggers.detect_tier2_extreme_risk_off(regime, self._prev_regime)
        events += triggers.detect_tier2_global_health(
            api_failure_count=self._api_failure_count,
            open_order_count=open_order_count,
            api_failure_threshold=self._config.api_failure_threshold,
            unfilled_threshold=self._config.unfilled_threshold,
        )
        events += triggers.detect_tier2_periodic_review(
            self._last_periodic_review_at,
            interval_minutes=self._config.periodic_review_minutes,
        )

        for event in events:
            await self._handle_trigger(event, planner_result=result)

        self._prev_holdings = {h["stock_code"]: h for h in holdings if h.get("stock_code")}
        self._prev_regime = regime
        # Track what qualified, not what was scanned. Under the movers
        # leaderboards a name dropping off and returning read as "new", so
        # scanning was a fair proxy. A fixed roster scores the same 30 codes
        # every tick, which made every one of them permanently un-new after
        # tick 1 and silenced new_candidate entirely (2026-08-19/20: 186
        # snapshots held a candidate that was eligible and past the gate, and
        # not one dispatched). Re-fire spacing is the per-stock cooldown's
        # job — `stock:<code>|new_candidate`, 300s — not this set's.
        self._prev_qualified_codes = {
            row.get("stock_code")
            for row in candidate_rows
            if isinstance(row, dict)
            and row.get("stock_code")
            and row.get("eligible")
            and (row.get("score") or 0) >= self._config.new_candidate_min_score
        }

        self._purge_expired_cooldowns()
        self._status.mark_tick(
            regime=regime,
            holding_count=len(holdings),
            open_order_count=open_order_count,
            candidate_count=len(candidate_rows),
            api_failure_count=self._api_failure_count,
        )
        self._status.set_cooldowns(self._cooldowns)
        self._status.set_daily_entry_breaker(self._breaker.to_dict())

    # -- state enrichment ----------------------------------------------------

    async def _handle_protective_holdings(self, holdings: list[dict[str, Any]]) -> None:
        """Apply hard exits before discretionary market scans can delay or fail."""

        enriched = self._enrich_holdings(holdings)
        events = triggers.detect_tier1_holding_rules(
            enriched,
            stop_loss_pct=self._config.stop_loss_pct,
            hard_take_profit_pct=self._config.hard_take_profit_pct,
        )
        events += triggers.detect_tier1_position_overflow(
            enriched, max_positions=self._config.max_positions
        )
        for event in events:
            await self._handle_trigger(event, planner_result={"holdings": enriched})

    def _enrich_holdings(self, holdings: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Track intraday high per holding so high-drop triggers work."""

        out: list[dict[str, Any]] = []
        for raw in holdings:
            if not isinstance(raw, dict):
                continue
            holding = dict(raw)
            code = holding.get("stock_code")
            cur = holding.get("current_price")
            try:
                cur_f = float(cur) if cur is not None else None
            except (TypeError, ValueError):
                cur_f = None
            if code and cur_f and cur_f > 0:
                prev_high = self._intraday_high.get(code, 0.0)
                if cur_f > prev_high:
                    self._intraday_high[code] = cur_f
                holding["intraday_high"] = self._intraday_high[code]
            out.append(holding)
        return out

    async def _fetch_open_orders(self) -> list[dict[str, Any]]:
        """Pull the latest unexecuted orders.

        Raises when the query did not succeed. ``account._run_account_query``
        turns transport and business errors into a result dict, so a bare
        ``.get(...)`` would hand back an empty list and make a failed query
        indistinguishable from "no open orders" — which would tell the
        oversell guard that nothing is working at the broker.
        """

        from . import account as account_service

        result = await account_service.get_unexecuted_orders(
            self._client, "0", "0", "0"
        )
        if not result.get("success"):
            raise RuntimeError(
                "unexecuted-orders query failed: "
                f"{result.get('message') or result.get('error') or '?'}"
            )
        if result.get("warning"):
            # ka10075 absence is safety evidence only after every pagination
            # page was consumed. The account wrapper warns when its request
            # cap is reached; treating that truncated view as empty could
            # release an UNKNOWN sell while its row is merely on a later page.
            raise RuntimeError(
                "unexecuted-orders query incomplete: "
                f"{result.get('warning')}"
            )
        rows = result.get("unexecuted_orders_data", [])
        return rows if isinstance(rows, list) else []

    # -- daily entry breaker -------------------------------------------------

    async def _update_entry_breaker(
        self, portfolio: dict[str, Any], *, now: datetime | None = None
    ) -> None:
        """Roll the trading day, feed today's account P&L, alert on a trip.

        Runs every tick. The roll is what performs the next-trading-day reset:
        the watcher sleeps through the close and wakes on a new KST date.
        """

        rolled = self._breaker.roll_day(now)
        if rolled and self._breaker.enabled:
            await self._notifier.info(
                "일일 서킷브레이커 리셋",
                f"새 거래일 {self._breaker.state.trading_day} — 신규 진입 재개",
            )
        if not self._breaker.enabled:
            return

        # An armed-but-unenforceable loss limit means zero new buys all
        # session. Say so once, loudly, or the operator just sees the watcher
        # mysteriously never entering anything.
        if (
            self._breaker.limits.loss_source_unverified
            and not self._warned_loss_source_unverified
        ):
            self._warned_loss_source_unverified = True
            log.error(
                "daily loss limits armed but tdy_lspft is unverified — "
                "all new entries blocked"
            )
            await self._safe_notify_error(
                "⚠️ 일일 손실 한도 미검증 — 신규 매수 전면 차단",
                "손익 데이터 소스(tdy_lspft)가 실계좌 검증되지 않아 "
                "손실 한도를 집행할 수 없습니다. 임계 미만이어도 신규 매수는 "
                "차단됩니다.\n"
                "손절·익절·매도·주문취소는 계속 동작합니다.\n"
                "신규 진입 건수 한도(--max-daily-new-entries)만 쓰거나, "
                "실계좌 검증 후 --acknowledge-daily-loss-source-verified 를 "
                "지정하세요.",
            )

        # Surface an untrustworthy breaker state once per distinct cause.
        # Without this the operator only sees buys quietly not happening —
        # the reason would sit in the trigger log and `/state` and nowhere
        # they get paged for.
        state_error = self._breaker.to_dict().get("state_error")
        if state_error != self._last_breaker_state_error:
            self._last_breaker_state_error = state_error
            if state_error:
                log.error("daily entry breaker state unusable: %s", state_error)
                await self._safe_notify_error(
                    "⚠️ 일일 서킷브레이커 상태 신뢰 불가 — 신규 매수 차단",
                    f"{state_error}\n"
                    "손절·익절·매도·주문취소는 계속 동작합니다. "
                    "상태 파일을 점검하거나 삭제 후 재기동하세요.",
                )

        snapshot = read_account_daily_snapshot(portfolio)
        if not snapshot.valid:
            # Not fatal on its own: `check_new_entry` decides whether this
            # actually has to block a buy (a KRW-only limit can still be
            # judged when just the denominator is missing).
            log.warning(
                "daily risk account snapshot unusable: %s", snapshot.reason
            )
        tripped = self._breaker.observe(snapshot)
        if tripped is not None:
            log.error("daily entry breaker tripped: %s", tripped.reason)
            await self._safe_notify_error(
                "🛑 일일 서킷브레이커 발동 — 신규 매수 중단",
                f"{tripped.reason}\n"
                "손절·익절·매도·주문취소는 계속 동작합니다. "
                f"다음 거래일에 자동 해제됩니다.",
            )

    # -- order ledger --------------------------------------------------------

    def _require_ledger(self) -> OrderLedger:
        """The ledger, or raise so the buy path can fail closed."""

        if self._ledger is None:
            raise OrderLedgerError(self._ledger_error or "order ledger unavailable")
        return self._ledger

    async def _alert_ledger_fault_once(self, detail: str) -> None:
        """Page once per distinct ledger fault while preserving exit liveness."""

        safety = self._ledger_storage_safety
        alert_key = (
            f"unsafe-storage:{safety.ledger_path}:{safety.fs_type}"
            if safety is not None and safety.state == STORAGE_NETWORK
            else detail
        )
        if alert_key == self._last_ledger_alert_reason:
            return
        self._last_ledger_alert_reason = alert_key
        if safety is not None and safety.state == STORAGE_NETWORK:
            await self._safe_notify_error(
                "🛑 주문 원장 네트워크 파일시스템 감지 — 신규 매수 차단",
                f"{safety.reason}\n"
                "복구: 기존 원장 audit를 보존한 채 local block filesystem으로 "
                "옮기거나 client/server DB로 전환하고 watcher를 재기동한 뒤 "
                "`/state`의 order_ledger.storage_safety를 확인하세요. "
                "보호매도·Tier-1 손절·주문취소는 계속 동작합니다.",
            )
            return
        await self._safe_notify_error(
            "🛑 주문 원장 오류 — 신규 매수 차단",
            f"{detail}\n"
            "원장 저장소를 점검하고 watcher를 재기동하세요. "
            "보호매도·Tier-1 손절·주문취소는 계속 동작합니다.",
        )

    def _settle_intent(self, intent, result: OrderApplyResult) -> None:
        """Write the order API's verdict back onto the intent.

        Best-effort on purpose: the order is already gone, and raising here
        would turn a bookkeeping failure into a lost result. The fault is
        counted and alerted instead, and the intent stays unresolved — which
        keeps blocking, the safe direction.
        """

        if self._ledger is None or intent is None:
            return
        try:
            self._ledger.apply_order_result(
                intent.intent_id,
                submitted=result.submitted,
                unknown=result.state == ORDER_STATE_UNKNOWN,
                order_no=result.order_no,
                reason=result.reason,
            )
        except OrderLedgerError as exc:
            detail = self._record_failure(FAILURE_ORDER, exc)
            log.error(
                "order ledger update failed for intent %s (state stays "
                "unresolved and keeps blocking): %s",
                intent.intent_id,
                detail,
            )

    async def _record_protective_intent(
        self,
        *,
        stock_code: str,
        side: str,
        quantity: int,
        price: int | None,
        origin: str,
        decision_scope: str | None = None,
    ) -> tuple[Any, str | None]:
        """Record an exit intent. Returns ``(intent, refusal_reason)``.

        ``(None, None)`` means the ledger could not record it — a fault must
        not trap the account in a position, so the caller places the order
        anyway after paging: an unrecorded exit is a bookkeeping problem, a
        blocked exit is an unbounded loss. That policy is unchanged.

        ``(None, reason)`` is different: the ledger is telling us this exact
        exit is already in flight or already done in this bucket, so the
        caller must skip rather than double it.
        """

        if self._ledger is None:
            await self._alert_ledger_fault_once(
                self._ledger_error or "order ledger unavailable"
            )
            return None, None
        try:
            registration = self._ledger.record_intent(
                stock_code=stock_code,
                side=side,
                quantity=quantity,
                price=price,
                origin=origin,
                decision_scope=decision_scope,
            )
            if not registration.may_submit:
                # NOT the same thing as a ledger fault. This is the ledger
                # telling us the identical exit already went out inside this
                # bucket, or already completed. Sending it again would not be
                # an exit, it would be a double — and the oversell guard
                # exists for the same reason. A different quantity, or the
                # next bucket, is a new decision and proceeds normally, so
                # this cannot trap a position.
                log.warning(
                    "protective %s on %s skipped (%s): %s",
                    side, stock_code, registration.outcome, registration.reason,
                )
                return None, registration.reason or "동일 결정 중복"
            return registration.intent, None
        except OrderLedgerError as exc:
            detail = self._record_failure(FAILURE_ORDER, exc)
            log.error(
                "order ledger record failed for protective %s on %s — "
                "proceeding with the order anyway: %s",
                side, stock_code, detail,
            )
            await self._alert_ledger_fault_once(detail)
            # Ledger fault: proceed with the order. Policy unchanged.
            return None, None

    async def _sellable_quantity_now(
        self, stock_code: str, held_quantity: int
    ) -> int:
        """Sellable quantity against a freshly refreshed broker view.

        The cached open orders are only guaranteed fresh when the tick
        happened to fetch them, and that used to hinge on the stale-cancel
        config — with ``stale_unfilled_minutes=0`` the cache stayed empty and
        a pre-existing broker sell order was invisible to the oversell guard.
        Exits therefore refresh on their own behalf.

        A failed refresh does **not** block the exit. Trapping the account in
        a position is the worse outcome, so we fall back to the cached view
        plus our own ledger intents and alert. Residual risk in that state:
        a sell order placed outside this watcher (or before the cache was
        last good) is invisible, so the order may exceed the holding and be
        rejected by the broker — a rejection, not an oversell, since Kiwoom
        will not fill beyond the position.
        """

        complete, rows, fills = await self._fetch_broker_views(executions=True)
        if self._ledger is not None:
            try:
                if self._ledger.unresolved():
                    report = self._ledger.reconcile(
                        open_orders=rows,
                        executions=fills,
                        broker_views_complete=complete,
                    )
                    if report.released:
                        log.warning(
                            "released %d UNKNOWN protective sell intent(s) "
                            "after repeated complete broker absence",
                            report.released,
                        )
            except OrderLedgerError as exc:
                # A ledger fault must not turn this freshness check into an
                # exit gate. `_sellable_quantity` will fall back to broker
                # rows alone and the protective order path will alert again
                # if it cannot persist the next attempt.
                self._record_failure(FAILURE_ORDER, exc)
        if not complete:
            await self._safe_notify_error(
                "⚠️ 청산 전 미체결 조회 실패 — 체결 조회 포함, 주문은 그대로 집행",
                f"{stock_code} 보호 주문 수량 산정에 완전한 최신 미체결/체결 "
                "내역을 쓰지 못해 "
                "캐시 + 원장 기준으로 계산합니다.\n"
                "청산을 막는 것이 더 위험하므로 주문은 집행합니다. "
                "외부에서 낸 매도 주문이 있으면 브로커가 수량 초과로 거부할 수 있습니다.",
            )
        return self._sellable_quantity(stock_code, held_quantity)

    def _sellable_quantity(self, stock_code: str, held_quantity: int) -> int:
        """Shares we may sell without overselling, from the current cache.

        Held minus whatever is already working as a sell. The broker's own
        open-order view and our unresolved sell intents are combined with
        ``max`` rather than summed: right after we submit, the same order is
        usually present in both, and double-counting it would block a
        legitimate exit.
        """

        broker_open = order_ledger.open_sell_quantity(
            self._last_open_orders, stock_code
        )
        ledger_open = 0
        if self._ledger is not None:
            try:
                ledger_open = self._ledger.unresolved_sell_quantity(stock_code)
            except OrderLedgerError as exc:
                # Fall back to the broker view rather than blocking an exit.
                log.warning(
                    "ledger sell-quantity lookup failed for %s: %s", stock_code, exc
                )
        working = max(broker_open, ledger_open)
        return max(held_quantity - working, 0)

    def _has_unresolved_intents(self) -> bool:
        """Whether anything is still awaiting the broker's verdict.

        A ledger read failure answers ``True``: not knowing is a reason to go
        look, and the only cost of a spurious ``True`` is one account query.
        """

        if self._ledger is None:
            return False
        try:
            return bool(self._ledger.unresolved())
        except OrderLedgerError as exc:
            self._record_failure(FAILURE_ORDER, exc)
            return True

    def _has_unknown_sell_intents(self) -> bool:
        """Whether the bounded protective-sell release policy needs both APIs."""

        if self._ledger is None:
            return False
        try:
            return any(
                intent.state == order_ledger.STATE_UNKNOWN
                for intent in self._ledger.unresolved(side=order_ledger.SIDE_SELL)
            )
        except OrderLedgerError as exc:
            self._record_failure(FAILURE_ORDER, exc)
            return True

    async def _refresh_open_orders(self) -> bool:
        """Pull the broker's live open orders into the cache. Returns success.

        The cache is only overwritten on success — replacing a good view with
        an empty list because one query failed would blind the oversell guard
        exactly when it matters.
        """

        try:
            rows = await self._fetch_open_orders()
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001 - caller decides the policy
            self._record_failure(FAILURE_ACCOUNT, exc)
            log.warning("open-order refresh failed: %s", sanitize_error_detail(exc))
            return False
        self._last_open_orders = rows
        return True

    async def _fetch_broker_views(
        self, *, executions: bool
    ) -> tuple[bool, list[dict[str, Any]], list[dict[str, Any]]]:
        """Pull fresh open orders (and optionally fills) from the broker.

        Returns ``(complete, open_orders, executions)``. ``complete`` is False
        if any query failed — callers that gate on this must treat that as
        "unknown", never as "clear".
        """

        complete = await self._refresh_open_orders()
        rows = list(self._last_open_orders)
        fills: list[dict[str, Any]] = []
        if executions:
            try:
                fills = await self._fetch_executions()
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001 - caller decides the policy
                self._record_failure(FAILURE_ACCOUNT, exc)
                complete = False
        return complete, rows, fills

    async def _reconcile_ledger(
        self,
        *,
        open_orders: list[dict[str, Any]] | None = None,
        executions: list[dict[str, Any]] | None = None,
        broker_views_complete: bool | None = None,
        fetch_open_orders: bool = False,
        fetch_executions: bool = False,
    ) -> bool:
        """Match unresolved intents against what the broker actually holds.

        Returns whether the pass completed on data we actually retrieved —
        the buy path needs that distinction, because reconciling against a
        query that failed proves nothing.

        A requested fetch happens **before** the "nothing pending" check. An
        empty ledger is not evidence that the broker is idle: it says only
        that *we* have no record, which is exactly the state a fresh install,
        a wiped volume, or a manually placed order leaves behind.

        Runs at startup (open orders *and* executions — anything could have
        happened while we were down) and every tick where something is
        unresolved. The buy path uses :meth:`_broker_gate_for_new_buy`, which
        additionally inspects the broker view directly.
        """

        if self._ledger is None:
            return False

        complete = bool(broker_views_complete)
        rows = open_orders
        fills: list[dict[str, Any]] = list(executions or [])
        if rows is None and (fetch_open_orders or fetch_executions):
            complete, rows, fills = await self._fetch_broker_views(
                executions=fetch_executions
            )
        elif rows is None:
            rows = self._last_open_orders

        try:
            pending = self._ledger.unresolved()
        except OrderLedgerError as exc:
            self._record_failure(FAILURE_ORDER, exc)
            return False
        if not pending:
            return complete

        try:
            report = self._ledger.reconcile(
                open_orders=rows,
                executions=fills,
                broker_views_complete=complete,
            )
        except OrderLedgerError as exc:
            self._record_failure(FAILURE_ORDER, exc)
            return False

        if report.resolved or report.adopted_order_no or report.absence_resets:
            log.info("order ledger reconciled: %s", report.to_dict())
        if report.still_unresolved:
            log.warning(
                "order ledger has %d unresolved intent(s) after reconciliation "
                "— new buys for those codes stay blocked",
                report.still_unresolved,
            )
        return complete

    async def _broker_gate_for_new_buy(self, stock_code: str) -> str | None:
        """Fresh broker check run before every new buy. Reason to block, or None.

        Two distinct questions, and the ledger can only answer the first:

        1. Do *we* have an unsettled order for this stock? — reconciled here
           against the fresh views so a fill that already happened stops
           blocking, and a still-working order keeps blocking.
        2. Does the **broker** have a working buy for this stock that we have
           no record of? — placed by hand, by an older build, or by another
           process. A clean ledger says nothing about these, so before this
           check a fresh install could happily duplicate an existing order.

        External orders are only *blocked on*, never adopted into the ledger:
        we did not place them, we do not know their lifecycle, and inventing
        an intent for one would make our own bookkeeping lie. Blocking is
        sufficient and cannot mis-attribute anything.

        Any query or ledger failure returns a block reason — "we could not
        check" must never read as "clear".
        """

        complete, rows, fills = await self._fetch_broker_views(executions=True)
        if self._ledger is not None:
            try:
                if self._ledger.unresolved():
                    self._ledger.reconcile(
                        open_orders=rows,
                        executions=fills,
                        broker_views_complete=complete,
                    )
            except OrderLedgerError as exc:
                detail = self._record_failure(FAILURE_ORDER, exc)
                return (
                    f"신규 매수 전 원장 대사 실패 ({detail}) — "
                    "확인 불가로 매수 보류 (매도/취소는 허용)"
                )
        if not complete:
            return (
                "신규 매수 전 브로커 조회 실패 (미체결/체결) — "
                "확인 불가로 매수 보류 (매도/취소는 허용)"
            )

        working = order_ledger.open_buy_quantity(
            rows, stock_code, include_unclassified=True
        )
        if working > 0:
            return (
                f"브로커에 미체결 매수 {working}주 잔존 (원장 기록 없음 — "
                "수동/외부 주문 가능) — 중복 매수 차단"
            )
        return None

    def _ledger_snapshot(
        self, *, recent_limit: int = 20, audit_limit: int = 50
    ) -> dict[str, Any]:
        """Ledger health + unresolved intents, for `/state`."""

        storage_safety = (
            self._ledger_storage_safety.to_dict()
            if self._ledger_storage_safety is not None
            else None
        )
        if self._ledger is None:
            return {
                "available": False,
                "error": self._ledger_error,
                "storage_safety": storage_safety,
            }
        try:
            pending = self._ledger.unresolved()
            recent = self._ledger.recent(recent_limit)
            audit = self._ledger.audit_events(limit=audit_limit)
        except OrderLedgerError as exc:
            return {
                "available": False,
                "error": sanitize_error_detail(exc),
                "storage_safety": storage_safety,
            }
        return {
            "available": True,
            "error": None,
            "path": str(self._ledger.path) if self._ledger.path else None,
            "storage_safety": storage_safety,
            "unresolved_count": len(pending),
            "unresolved": [i.to_dict() for i in pending],
            "recent": [i.to_dict() for i in recent],
            "recent_audit": audit,
        }

    def ledger_view(
        self, *, limit: int = 50, trading_day: str | None = None
    ) -> dict[str, Any]:
        """Read-only ledger view for the status server's `/ledger`.

        The agents' route to the ledger used to be `kubectl exec` into this
        pod and a raw SQLite query (2026-09-17 RCA) — cluster-admin to read a
        table. `trading_day` (YYYY-MM-DD, as the ledger stores it) narrows the
        recent intents to one session; unresolved intents are always listed
        because they are what blocks the next buy.
        """

        limit = max(1, min(int(limit), 200))
        view = self._ledger_snapshot(recent_limit=limit, audit_limit=limit)
        if trading_day and view.get("available"):
            view["recent"] = [
                row for row in view["recent"] if row.get("trading_day") == trading_day
            ]
            view["trading_day"] = trading_day
        return view

    async def _fetch_executions(self) -> list[dict[str, Any]]:
        """Today's fills, used to settle intents we lost track of.

        ka10076 params are all "everything": ``qry_tp=0`` 전체 (not per-stock),
        ``sell_tp=0`` 전체 (both sides), ``stex_tp=0`` 통합 (all venues). A
        narrower value here would silently return fewer rows and leave
        intents unresolved, which blocks buying.
        """

        from . import account as account_service

        result = await account_service.get_execution_info(
            self._client, qry_tp="0", sell_tp="0", stex_tp="0"
        )
        if not result.get("success"):
            # Same reasoning as `_fetch_open_orders`: an empty list from a
            # failed query would read as "nothing filled today".
            raise RuntimeError(
                "execution query failed: "
                f"{result.get('message') or result.get('error') or '?'}"
            )
        if result.get("warning"):
            raise RuntimeError(
                f"execution query incomplete: {result.get('warning')}"
            )
        rows = result.get("execution_data", [])
        return rows if isinstance(rows, list) else []

    # -- failure attribution -------------------------------------------------

    def _record_failure(self, category: str, error: BaseException | str) -> str:
        """Count a failure against ``category`` and return the safe detail."""

        detail = sanitize_error_detail(error)
        self._status.record_failure(category=category, detail=detail)
        self._last_error = f"{category}: {detail}"
        return detail

    def _mark_late_outcome(
        self,
        entry: TriggerLogEntry,
        *,
        outcome: str,
        detail: str,
        scope_key: str,
    ) -> bool:
        """Record a failure/cancellation outcome unless one is already set.

        A stage that fails *after* the trigger reached a terminal outcome —
        the order was submitted and only the Discord push blew up — must not
        relabel a live order as ``failed``. The error is still counted and
        logged; only the outcome label is protected.
        """

        if entry.outcome is not None:
            log.warning(
                "late %s after outcome=%s on %s: %s",
                outcome,
                entry.outcome,
                scope_key,
                detail,
            )
            return False
        self._status.mark_outcome(entry, outcome=outcome, detail=detail)
        return True

    # -- trigger routing -----------------------------------------------------

    async def _handle_trigger(
        self, event: TriggerEvent, *, planner_result: dict[str, Any]
    ) -> None:
        """Apply Tier-1 immediately or spawn a Tier-2 dispatch task.

        One trigger's failure must not take out the rest of the tick. A
        multica outage while dispatching the first Tier-2 event used to abort
        ``_tick`` outright, skipping every later event in the list — including
        Tier-1 stop-losses. Now the failure is contained, attributed and
        counted, and the loop moves on to the next trigger.
        """

        if self._is_in_cooldown(event):
            return
        if event.tier != 1 and event.scope_key() in self._in_flight:
            return  # already processing this scope
        if self._should_skip_holding_swing(event):
            return  # repeat no-op on an idling holding — don't burn an agent call
        if self._should_skip_new_candidate(event):
            return  # already rejected at this score — don't burn an agent call

        self._set_cooldown(event)
        # Only a Tier-1 action that liquidates the position invalidates an
        # older agent decision for that stock. `cancel_order` is Tier 1 and
        # protective too, but it withdraws an *order*, not the holding — and
        # it frees the shares, so an exit formed just before it is more
        # executable afterwards, not less. Treating the two alike let a
        # stale-order cancel swallow a CUT_LOSS that arrived seconds later.
        if (
            event.tier == 1
            and event.stock_code
            and event.suggested_action in POSITION_CLOSING_ACTIONS
        ):
            self._protective_trigger_at[order_ledger.normalize_stock_code(event.stock_code)] = datetime.now(KST)

        entry = self._status.record_trigger(
            trigger_type=event.trigger_type,
            tier=event.tier,
            scope=event.scope,
            target_role=event.target_role,
            stock_code=event.stock_code,
            stock_name=event.stock_name,
            reason=event.reason,
            detected_at=event.detected_at,
        )

        # Attribute by the path's dominant external dependency: Tier-1 talks to
        # the order API, Tier-2 dispatch talks to multica.
        category = FAILURE_ORDER if event.tier == 1 else FAILURE_MULTICA
        try:
            if event.tier == 1:
                await self._execute_tier1(event, entry)
                return

            # Tier 2
            if event.trigger_type == "periodic_review":
                self._last_periodic_review_at = event.detected_at

            await self._dispatch_tier2(event, entry, planner_result=planner_result)
        except asyncio.CancelledError:
            # Shutdown, not a fault. Let the cancellation continue to unwind.
            self._mark_late_outcome(
                entry,
                outcome="cancelled",
                detail="watcher 종료 중 취소",
                scope_key=event.scope_key(),
            )
            raise
        except Exception as exc:  # noqa: BLE001 - operational containment
            detail = self._record_failure(category, exc)
            log.exception(
                "trigger handling failed: %s tier=%d category=%s",
                event.cooldown_key(),
                event.tier,
                category,
            )
            self._mark_late_outcome(
                entry,
                outcome="failed",
                detail=detail,
                scope_key=event.scope_key(),
            )
            await self._safe_notify_error(
                f"Tier{event.tier} 처리 실패 · {event.trigger_type}",
                f"{event.stock_name or event.target_role} "
                f"({event.stock_code or '-'}) — {detail}",
            )

    async def _safe_notify_error(self, title: str, description: str) -> None:
        """Send a Discord error that can never itself break the caller.

        The notifier is best-effort by design (no retry, silent failure), but
        it is reached from inside exception handlers — a raise here would
        replace the original fault with a confusing one.
        """

        try:
            await self._notifier.error(title, description)
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001 - notification is best-effort
            log.warning("discord error notification failed: %s", exc)

    def _should_skip_holding_swing(self, event: TriggerEvent) -> bool:
        """Suppress a holding_swing whose dispatch would just repeat a no-op.

        A held name oscillating in the ±2% band re-fires holding_swing every
        cooldown; if the evaluator's last call returned a no-op (HOLD/
        ACKNOWLEDGE) and profit_rate has barely moved since, re-dispatching is
        pure agent-call waste. Skip until profit_rate moves past the threshold.

        Safe: Tier-1 stop_loss/take_profit fire in code regardless of this, so
        an idling position is still protected at the extremes. A prior SELL
        ACTION (TRIM/TAKE_PROFIT/CUT_LOSS/ROTATE) that actually reached the
        broker never suppresses — we keep tracking a position being exited.
        profit_rate missing → don't skip.

        A sell the broker *refused* is treated as the no-op it was. The
        exemption above exists to watch an exit in progress, and a rejected
        order started none: the position is untouched, so the next tick asks
        the same question and gets the same answer. On 2026-08-31 that loop
        ran 7 times on one name while every exit was rejected 308003, piling
        48 comments onto a single issue -- and because each agent run re-reads
        the whole thread, it exhausted the codex quota for the day. The order
        bug is fixed, but the amplifier is worth closing on its own: any
        future exit failure would do this again.
        """

        delta = self._config.holding_dedup_profit_delta_pct
        if delta <= 0 or event.trigger_type != "holding_swing" or not event.stock_code:
            return False
        last = self._last_holding_action.get(event.stock_code)
        if last is None:
            return False
        action, prev_profit, _at, outcome = last
        exit_is_working = outcome in EXPOSURE_STATES
        if action not in ("HOLD", "ACKNOWLEDGE") and exit_is_working:
            return False  # a sell is live at the broker — keep tracking it
        cur_profit = event.snapshot.get("profit_rate")
        if cur_profit is None or prev_profit is None:
            return False  # can't compare — dispatch to be safe
        try:
            if abs(float(cur_profit) - float(prev_profit)) >= delta:
                return False  # moved enough to re-evaluate
        except (TypeError, ValueError):
            return False
        log.info(
            "holding_swing skipped (dedup): %s last=%s/%s profit %.2f→%.2f (Δ<%.1f)",
            event.stock_code, action, outcome,
            float(prev_profit), float(cur_profit), delta,
        )
        return True

    def _should_skip_new_candidate(self, event: TriggerEvent) -> bool:
        """Suppress a new_candidate the screener already turned down.

        Scores drift across the gate tick by tick, and the qualified-set that
        drives novelty only knows "was it qualified last tick". So a name that
        qualifies, is REJECTed, slips one point, and re-qualifies reads as
        newly qualified again, and re-dispatches every cooldown. On 2026-08-25
        that spent 113 screener calls on 7 names — 셀트리온 36, LG화학 28 —
        every one REJECT, and drained the agent backend's quota mid-session.

        Only an *improvement* re-opens the question: a score falling further
        below what was already rejected is not new information. Anything other
        than REJECT (TIER1/TIER2) never suppresses — an approval must reach
        the buy path. Verdicts are scoped to the trading day, matching the
        per-day issue thread, so yesterday's REJECT cannot mute today.
        """

        delta = self._config.candidate_dedup_score_delta
        if delta <= 0 or event.trigger_type != "new_candidate" or not event.stock_code:
            return False
        last = self._last_candidate_action.get(event.stock_code)
        if last is None:
            return False
        action, prev_score, at = last
        if action != "REJECT":
            return False  # approved — must not be suppressed
        if at.astimezone(KST).date() != datetime.now(KST).date():
            return False  # a new session re-opens every name
        cur_score = event.snapshot.get("score")
        if cur_score is None or prev_score is None:
            return False  # can't compare — dispatch to be safe
        try:
            if float(cur_score) - float(prev_score) >= delta:
                return False  # materially stronger than what was rejected
        except (TypeError, ValueError):
            return False
        log.info(
            "new_candidate skipped (dedup): %s last=REJECT score %.1f→%.1f (Δ<%.1f)",
            event.stock_code, float(prev_score), float(cur_score), delta,
        )
        return True

    def _is_in_cooldown(self, event: TriggerEvent) -> bool:
        expiry = self._cooldowns.get(event.cooldown_key())
        if expiry is None:
            return False
        if datetime.now(KST) >= expiry:
            self._cooldowns.pop(event.cooldown_key(), None)
            return False
        return True

    def _set_cooldown(self, event: TriggerEvent) -> None:
        seconds = self._config.cooldown_seconds
        if event.tier == 1:
            seconds = min(seconds, max(1, self._config.poll_interval_seconds))
        self._cooldowns[event.cooldown_key()] = datetime.now(KST) + timedelta(
            seconds=seconds
        )

    def _purge_expired_cooldowns(self) -> None:
        """Drop cooldown entries whose expiry has already passed.

        Without this the registry reports stale entries forever (the
        ``_is_in_cooldown`` lazy-purge only runs on the next fire of
        the same key). Periodic cleanup keeps `/state` readable.
        """

        now = datetime.now(KST)
        expired = [k for k, v in self._cooldowns.items() if now >= v]
        for k in expired:
            self._cooldowns.pop(k, None)

    def _build_regime_flip_baseline(
        self, cur_label: str | None
    ) -> dict[str, Any] | None:
        """Return the prev-stable regime baseline for label-flip detection,
        or ``None`` when the label has not yet stabilized into a flip.

        Rules:

        * If we have not yet seen a full debounce window of identical
          labels, return ``None`` (suppress fire).
        * If the stable label matches the last one we already announced,
          return ``None`` (no actual change).
        * Otherwise return the previously-announced regime so the detect
          function can produce the trigger.
        """

        window = max(self._config.regime_stability_ticks, 1)
        if not cur_label:
            return None
        if len(self._regime_history) < window:
            return None
        if any(label != cur_label for label in self._regime_history):
            return None
        if self._last_emitted_regime is None:
            # First stable read of the session — record it but don't fire.
            self._last_emitted_regime = cur_label
            return None
        if self._last_emitted_regime == cur_label:
            return None
        return {"regime": self._last_emitted_regime}

    # -- tier 1 execution ----------------------------------------------------

    async def _execute_tier1(
        self, event: TriggerEvent, entry: TriggerLogEntry
    ) -> OrderApplyResult:
        """Place orders directly for hard-rule triggers.

        Returns what actually happened. ``submitted`` means Kiwoom booked the
        request — never that it filled; the trigger log used to record
        ``executed`` here, which made the dashboard and the ops digest claim
        fills that had not happened (P1-4).
        """

        action = event.suggested_action or event.trigger_type
        log.info(
            "tier1: %s %s %s — %s",
            event.trigger_type,
            event.stock_code,
            event.stock_name,
            event.reason,
        )
        if not self._can_execute_orders():
            log.info("tier1 dry-run (execute disabled): %s", event.cooldown_key())
            self._status.mark_outcome(
                entry, outcome="dry_run", detail="execute_orders=False",
            )
            await self._notifier.warn(
                f"Tier1 dry-run · {event.trigger_type}",
                f"{event.stock_name} ({event.stock_code}) — {event.reason}\n"
                f"execute_orders=False 라 주문은 보류됨",
            )
            return OrderApplyResult.skipped(action, "execute_orders=False")

        order_result: dict[str, Any] | None = None
        intent = None
        if event.suggested_action == "sell_market":
            qty = event.snapshot.get("quantity")
            if not qty:
                return self._record_tier1_no_order(
                    entry,
                    OrderApplyResult.skipped(action, "quantity missing"),
                )
            # Oversell guard: a stop-loss re-firing while an earlier exit is
            # still working at the broker must not sell the same shares twice.
            code = str(event.stock_code or "")
            sell_qty = await self._sellable_quantity_now(code, int(qty))
            if sell_qty <= 0:
                log.info(
                    "tier1 sell skipped: %s already covered by working sells", code
                )
                return self._record_tier1_no_order(
                    entry,
                    OrderApplyResult.skipped(
                        action, "기존 매도 주문이 보유 수량을 이미 커버 — 중복 매도 차단"
                    ),
                )
            if sell_qty < int(qty):
                log.info(
                    "tier1 sell clamped for %s: %s → %d", code, qty, sell_qty
                )
            intent, duplicate = await self._record_protective_intent(
                stock_code=code,
                side=order_ledger.SIDE_SELL,
                quantity=sell_qty,
                price=None,
                origin=event.trigger_type,
                decision_scope=event.trigger_type,
            )
            if duplicate is not None:
                return self._record_tier1_no_order(
                    entry, OrderApplyResult.skipped(action, duplicate)
                )
            order_result = await order_service.place_stock_sell_order(
                self._client,
                stk_cd=event.stock_code or "",
                ord_qty=str(sell_qty),
                order_type_code="3",  # market
            )
        elif event.suggested_action == "cancel_order":
            order_no = event.metadata.get("order_no")
            qty = event.snapshot.get("qty") or "0"
            if not order_no:
                return self._record_tier1_no_order(
                    entry,
                    OrderApplyResult.skipped(action, "order_no missing"),
                )
            # Cancels are recorded for audit but never gated: cancelling
            # reduces exposure, so a ledger fault must not stand in the way.
            intent, duplicate = await self._record_protective_intent(
                stock_code=str(event.stock_code or ""),
                side=order_ledger.SIDE_CANCEL,
                quantity=int(qty) if str(qty).isdigit() else 0,
                price=None,
                origin=event.trigger_type,
                decision_scope=event.trigger_type,
            )
            if duplicate is not None:
                return self._record_tier1_no_order(
                    entry, OrderApplyResult.skipped(action, duplicate)
                )
            order_result = await order_service.cancel_stock_order(
                self._client,
                orig_ord_no=str(order_no),
                stk_cd=event.stock_code or "",
                cncl_qty=str(qty),
            )
        else:
            # A tier-1 trigger with no order mapping (or none suggested) is a
            # notice, not a trade. Previously this returned with the trigger
            # left permanently uncompleted in the status feed.
            log.info(
                "tier1 no order mapping: %s action=%s",
                event.cooldown_key(),
                event.suggested_action,
            )
            return self._record_tier1_no_order(
                entry,
                OrderApplyResult.informational(
                    action, f"주문 매핑 없음 (suggested_action={event.suggested_action})"
                ),
            )

        result = OrderApplyResult.from_order_response(action, order_result)
        self._settle_intent(intent, result)
        detail = " · ".join(
            part for part in (action, result.reason) if part
        )
        self._status.mark_outcome(entry, outcome=result.state, detail=detail or None)

        target = f"{event.stock_name} ({event.stock_code})"
        if result.state == ORDER_STATE_SUBMITTED:
            order_line = f"\n주문번호: {result.order_no}" if result.order_no else ""
            await self._notifier.success(
                f"Tier1 주문 접수 · {event.trigger_type}",
                f"{target} — {event.reason}\n"
                f"브로커 접수 완료 (체결 확인 아님){order_line}",
            )
        elif result.state == ORDER_STATE_UNKNOWN:
            # The request went out and the answer was lost. Re-firing the same
            # rule could double the order, so this needs a human, not a retry.
            log.error(
                "tier1 order state unknown: %s — %s",
                event.cooldown_key(),
                result.reason,
            )
            await self._notifier.error(
                f"Tier1 접수 불명 · {event.trigger_type}",
                f"{target} — {event.reason}\n"
                f"{result.reason or '응답 유실'}\n"
                "브로커 접수 여부 미확인 — 재주문 금지, 미체결/체결 조회로 확인 필요",
            )
        else:
            log.warning(
                "tier1 order rejected: %s — %s",
                event.cooldown_key(),
                result.reason,
            )
            await self._notifier.error(
                f"Tier1 실패 · {event.trigger_type}",
                f"{target} — {result.reason or '?'}",
            )
        return result

    def _record_tier1_no_order(
        self, entry: TriggerLogEntry, result: OrderApplyResult
    ) -> OrderApplyResult:
        """Complete a tier-1 trigger that never reached the order API."""

        self._status.mark_outcome(
            entry, outcome=result.state, detail=result.reason,
        )
        return result

    def _can_execute_orders(self) -> bool:
        """Mirror the strategy_cycle gate for the watcher."""

        if not self._config.execute_orders:
            return False
        if self._settings.use_mock:
            return True
        return bool(self._config.confirm_live_orders)

    def _should_notify_tier2_action(
        self,
        event: TriggerEvent,
        action: str,
        outcome: str,
    ) -> bool:
        """Filter routine no-op Tier-2 ACTIONs out of Discord.

        Anything that put an order in front of the broker (`submitted`, and
        `filled` once reconciliation exists) plus screener candidate decisions
        always notify. PM/risk standby reports (HOLD/ACKNOWLEDGE on
        periodic_review or regime_flip) are suppressed by default — they
        fire every 30 min and drown out the signal channel.
        """

        if self._config.notify_routine_pm_actions:
            return True
        if outcome in (ORDER_STATE_SUBMITTED, ORDER_STATE_FILLED):
            return True
        if event.trigger_type in ("periodic_review", "regime_flip") and (
            action.upper() in ("HOLD", "ACKNOWLEDGE")
        ):
            return False
        return True

    async def _notify_tier2_outcome(
        self,
        event: TriggerEvent,
        action: str,
        result: OrderApplyResult,
        peer_response,
    ) -> None:
        """Push the Tier-2 result to Discord using what the apply really did."""

        target = (
            f"{event.stock_name or event.target_role} ({event.stock_code or '-'})"
        )
        peer_suffix = (
            f" · 교차검토={peer_response.action}"
            if peer_response is not None
            else ""
        )

        if result.state == ORDER_STATE_FAILED:
            # Log it too. A rejected protective sell used to reach Discord and
            # the ledger's `reason` column and nowhere else, so 7 failed exits
            # on 2026-08-31 left the log completely silent.
            log.warning(
                "tier2 order rejected: %s action=%s — %s",
                event.cooldown_key(),
                action,
                result.reason,
            )
            await self._notifier.error(
                f"Tier2 주문 실패 · {event.trigger_type}",
                f"{target} — ACTION={action} · {result.reason or '사유 미상'}",
            )
            return
        if result.state == ORDER_STATE_UNKNOWN:
            # Same hazard as the Tier-1 unknown path: the order may exist.
            log.error(
                "tier2 order state unknown: %s action=%s — %s",
                event.cooldown_key(),
                action,
                result.reason,
            )
            await self._notifier.error(
                f"Tier2 접수 불명 · {event.trigger_type}",
                f"{target} — ACTION={action} · {result.reason or '응답 유실'}\n"
                "브로커 접수 여부 미확인 — 재주문 금지, 미체결/체결 조회로 확인 필요",
            )
            return

        if not self._should_notify_tier2_action(event, action, result.state):
            return

        title = f"Tier2 ACTION={action} · {event.trigger_type}"
        body = f"{target} — {event.reason}{peer_suffix}"
        if result.state == ORDER_STATE_SUBMITTED:
            title = f"Tier2 주문 접수 · ACTION={action} · {event.trigger_type}"
            order_line = f"\n주문번호: {result.order_no}" if result.order_no else ""
            body = (
                f"{target} — {event.reason}{peer_suffix}\n"
                f"브로커 접수 완료 (체결 확인 아님){order_line}"
            )
        elif result.reason:
            body = f"{target} — {event.reason} · {result.reason}{peer_suffix}"
        await self._notifier.success(title, body)

    # -- tier 2 dispatch -----------------------------------------------------

    async def _dispatch_tier2(
        self,
        event: TriggerEvent,
        entry: TriggerLogEntry,
        *,
        planner_result: dict[str, Any],
    ) -> None:
        """Post the trigger comment and spawn a polling task."""

        issue = await self._ensure_issue_for(event)
        if issue is None:
            log.warning("tier2 dispatch skipped — no issue: %s", event.cooldown_key())
            self._status.mark_outcome(
                entry, outcome="dispatch_failed", detail="no issue",
            )
            return

        comment = self._build_trigger_comment(event, planner_result)
        prev_run = await self._dispatcher.latest_completed_run(issue.id)
        prev_run_id = prev_run.get("id") if prev_run else None
        ok = await self._dispatcher.add_comment(issue.id, comment)
        if not ok:
            log.warning("tier2 comment failed: %s", event.cooldown_key())
            self._status.mark_outcome(
                entry, outcome="dispatch_failed", detail="comment add failed",
            )
            return

        self._status.mark_dispatched(entry, issue_id=issue.id)
        self._status.add_in_flight(
            scope_key=event.scope_key(),
            trigger_type=event.trigger_type,
            target_role=event.target_role,
            stock_code=event.stock_code,
            stock_name=event.stock_name,
            started_at=event.detected_at,
            issue_id=issue.id,
        )

        task = asyncio.create_task(
            self._await_and_apply(event, entry, issue.id, prev_run_id, planner_result)
        )
        # Last-resort net. `_await_and_apply` handles its own failures, but an
        # exception raised *inside* that handler (or in the `finally`) would
        # otherwise only ever appear as asyncio's "Task exception was never
        # retrieved" during garbage collection, long after the fact and with
        # nothing tying it back to a trigger.
        task.add_done_callback(
            lambda finished, key=event.scope_key(): self._on_tier2_task_done(
                key, finished
            )
        )
        self._in_flight[event.scope_key()] = InFlightTask(
            scope_key=event.scope_key(),
            trigger=event,
            started_at=event.detected_at,
            issue_id=issue.id,
            task=task,
        )

    def _on_tier2_task_done(self, scope_key: str, task: asyncio.Task[Any]) -> None:
        """Retrieve a finished Tier-2 task's exception and free its slot.

        Runs synchronously in the event loop, so it cannot await — no Discord
        from here. Reaching this with an exception means ``_await_and_apply``'s
        own handler failed, which is a bug rather than an operational fault,
        so it is logged loudly and counted.
        """

        # Idempotent: the task's `finally` normally cleared these already.
        self._in_flight.pop(scope_key, None)
        self._status.remove_in_flight(scope_key)

        if task.cancelled():
            return  # shutdown; `_await_and_apply` already recorded the outcome
        exc = task.exception()
        if exc is None:
            return
        detail = self._record_failure(FAILURE_TIER2_TASK, exc)
        log.error(
            "tier2 task escaped its handler: %s — %s",
            scope_key,
            detail,
            exc_info=exc,
        )

    async def _ensure_issue_for(self, event: TriggerEvent):
        if event.target_role == ROLE_EVALUATOR:
            return await self._dispatcher.ensure_holding_issue(
                code=event.stock_code or "", name=event.stock_name or event.stock_code or ""
            )
        if event.target_role == ROLE_SCREENER:
            return await self._dispatcher.ensure_candidate_issue(
                code=event.stock_code or "", name=event.stock_name or event.stock_code or ""
            )
        if event.target_role == ROLE_PM:
            # Global PM triggers go to a dedicated per-day log issue so the
            # main daily issue stays readable. Stock-scoped PM triggers (if
            # any future trigger types add this scope) still use the per-stock
            # holding issue.
            if event.scope == "stock":
                return await self._dispatcher.ensure_holding_issue(
                    code=event.stock_code or "",
                    name=event.stock_name or event.stock_code or "",
                )
            return await self._dispatcher.ensure_pm_log_issue()
        if event.target_role == ROLE_RISK:
            return await self._dispatcher.ensure_risk_issue()
        return None

    def _build_trigger_comment(
        self,
        event: TriggerEvent,
        planner_result: dict[str, Any] | None = None,
    ) -> str:
        """Render a human-readable trigger payload for the agent.

        When ``planner_result`` is supplied, a portfolio summary block is
        prepended so the agent can pick an ACTION that matches actual
        portfolio state (e.g. picking ACKNOWLEDGE over TRIM when
        holdings=0). Comments are required every cycle.
        """

        stamp = event.detected_at.strftime("%H:%M:%S KST")
        header = f"**[{stamp}] [트리거: {event.trigger_type}]**"
        snapshot_json = json.dumps(event.snapshot, ensure_ascii=False, indent=2, default=str)

        action_options = {
            ROLE_EVALUATOR: "HOLD / TRIM / TAKE_PROFIT / CUT_LOSS / ROTATE",
            ROLE_SCREENER: "TIER1 / TIER2 / REJECT",
            ROLE_PM: "HOLD / TRIM / TAKE_PROFIT / CUT_LOSS / ROTATE / ACKNOWLEDGE",
            ROLE_RISK: "ACKNOWLEDGE / MITIGATE / ESCALATE",
        }.get(event.target_role, "ACKNOWLEDGE")

        target_line = ""
        if event.stock_code:
            target_line = f"종목: {event.stock_name or event.stock_code} ({event.stock_code})\n"

        portfolio_block = ""
        portfolio = (planner_result or {}).get("portfolio") or {}
        if portfolio:
            holdings_n = portfolio.get("holding_count") or 0
            open_orders_n = portfolio.get("open_order_count") or 0
            cash = portfolio.get("cash_available") or 0
            cash_d2 = portfolio.get("cash_d2") or 0
            assets = portfolio.get("estimated_assets") or 0
            cand_rows = (planner_result or {}).get("candidate_rows") or []
            candidates_n = len(cand_rows)
            holdings_list = (planner_result or {}).get("holdings") or []
            holdings_brief = ""
            if holdings_list:
                # These rows come from strategy._normalize_holding_rows, which
                # keys them stock_code/stock_name/profit_rate. Reading code/
                # name/return_pct here matched nothing, so every holding ever
                # rendered as "?(?) +0.00%" — and the fallback zero was the
                # damaging half: an unknown return is not a flat one. Agents
                # burned delegations on the phantom (SWO-900, SWO-925) and
                # were told a position was flat while it moved.
                items = [
                    f"{h.get('stock_name') or h.get('stock_code') or '?'}"
                    f"({h.get('stock_code') or '?'}) "
                    f"{_format_profit_rate(h.get('profit_rate'))}"
                    for h in holdings_list[:5]
                ]
                holdings_brief = " · " + ", ".join(items)
                if len(holdings_list) > 5:
                    holdings_brief += f" 외 {len(holdings_list) - 5}종목"
            # `cash` (entr) settles today; `assets` (prsm_dpst_aset_amt) and
            # `cash_d2` (d2_entra) settle D+2. Printing them as plain
            # "현금"/"총자산" made the gap between two settlement bases read
            # as a holding — the same phantom-position incident four times
            # (SWO-768/870/880/907), each an urgent dispatch chasing a
            # position that had already been sold. Name the basis, and when
            # nothing is held say outright what the gap is.
            cash_line = f"- 예수금(당일): {cash:,}원"
            if cash_d2:
                cash_line += f" · D+2 추정예수금: {cash_d2:,}원"
            cash_line += f" · 추정예탁자산(D+2): {assets:,}원"
            unsettled = (cash_d2 or assets) - cash
            if holdings_n == 0 and unsettled > 0:
                cash_line += (
                    f"\n  ⚠️ 차액 {unsettled:,}원은 **미정산 매도대금**이다"
                    "(D+2 정산 대기, 수수료·세금 차감 후). "
                    "보유 0종목이 맞으며 누락된 포지션이 아니다."
                )
            portfolio_block = (
                "## 포트폴리오 현황\n"
                f"- 보유: **{holdings_n}종목**{holdings_brief}\n"
                f"- 미체결: {open_orders_n}건\n"
                f"{cash_line}\n"
                f"- 후보 풀: {candidates_n}건\n\n"
            )
            # The sell-side rule only makes sense where selling is on the menu.
            # It used to be appended to every trigger, so a new_candidate went
            # to the screener saying "only ACKNOWLEDGE or HOLD are allowed" —
            # neither of which is a screener ACTION — while its skill asks for
            # TIER1/TIER2/REJECT. Contradictory instruction, and REJECT is the
            # only reading that satisfies both.
            if event.target_role in (ROLE_EVALUATOR, ROLE_PM):
                portfolio_block += (
                    "**ACTION 선택 규칙**\n"
                    "- 보유 0종목: `TRIM` / `TAKE_PROFIT` / `CUT_LOSS` / `ROTATE` 금지. "
                    "**`ACKNOWLEDGE` 또는 `HOLD`** 만 허용.\n"
                    "- 보유 ≥1종목: 매도 후보가 있을 때만 매도 계열 ACTION.\n\n"
                )
            elif event.target_role == ROLE_SCREENER:
                portfolio_block += (
                    f"**가능한 ACTION**: `{action_options}` "
                    "— 이 트리거는 신규 후보 판정이며 매도 계열 ACTION은 해당 없음.\n\n"
                )

        return (
            f"{header}\n\n"
            f"{target_line}"
            f"사유: {event.reason}\n\n"
            f"{portfolio_block}"
            f"```\n{snapshot_json}\n```\n\n"
            f"이 트리거에 대한 ACTION 결정을 **반드시 댓글로** 작성해 주세요. "
            "동일 결정의 반복이라도 매 사이클 ACTION 댓글이 필수입니다 — squad activity는 댓글 뒤 부수 기록.\n"
            f"옵션: {action_options}\n\n"
            f"마지막 줄에 `<!-- ACTION: XXX -->` 형식으로 명시해주세요. "
            "`XXX`는 위 옵션 중 실제 값으로 치환."
        )

    def _issue_type_for_event(self, event: TriggerEvent) -> str:
        if event.target_role == ROLE_EVALUATOR:
            return "holding"
        if event.target_role == ROLE_SCREENER:
            return "candidate"
        if event.target_role == ROLE_RISK:
            return "incident"
        if event.target_role == ROLE_PM and event.scope == "stock":
            return "holding"
        return "daily"

    async def _await_and_apply(
        self,
        event: TriggerEvent,
        entry: TriggerLogEntry,
        issue_id: str,
        prev_run_id: str | None,
        planner_result: dict[str, Any],
    ) -> None:
        """Wait for the agent's next run and apply the parsed ACTION.

        This runs as a detached ``asyncio`` task, so an escaping exception
        would only surface as asyncio's "Task exception was never retrieved"
        at garbage-collection time — the trigger would sit forever without an
        outcome and nobody would be paged (P1-2). Every operational failure is
        therefore caught here, attributed to the stage that raised it, counted,
        logged with a traceback and pushed to Discord. Cancellation is *not* a
        failure and unwinds normally.
        """

        # Which external dependency we are currently talking to. Used to
        # attribute a failure without guessing from the exception type.
        stage = FAILURE_MULTICA
        stage_label = "agent 응답 대기"
        try:
            response = await self._dispatcher.wait_for_new_action(
                issue_id,
                prev_run_id=prev_run_id,
                timeout_seconds=self._config.agent_timeout_seconds,
                poll_seconds=self._config.agent_poll_seconds,
            )
            if response is None:
                log.warning(
                    "tier2 timeout: %s (no agent response within %ss)",
                    event.cooldown_key(),
                    self._config.agent_timeout_seconds,
                )
                self._status.mark_outcome(
                    entry,
                    outcome="timeout",
                    detail=f"{self._config.agent_timeout_seconds}s 응답 없음",
                )
                await self._dispatcher.add_comment(
                    issue_id,
                    f"**[watcher]** {event.trigger_type} 응답이 "
                    f"{self._config.agent_timeout_seconds}초 내에 도착하지 않아 슬롯을 해제합니다.",
                )
                await self._notifier.warn(
                    f"Tier2 timeout · {event.trigger_type}",
                    f"{event.stock_name or event.target_role} "
                    f"({event.stock_code or '-'}) — agent 응답 없음",
                )
                return

            log.info(
                "tier2 action %s for %s — output_len=%d",
                response.action,
                event.cooldown_key(),
                len(response.output or ""),
            )

            stage, stage_label = FAILURE_MARKET, "stale 시세 조회"
            still_valid, _detail = await self._is_still_valid(event)
            if not still_valid:
                log.info("tier2 stale, dropping ACTION %s for %s", response.action, event.cooldown_key())
                self._status.mark_outcome(
                    entry,
                    outcome="stale",
                    action=response.action,
                    detail="시세/포지션 변동으로 ACTION 폐기",
                )
                await self._dispatcher.add_comment(
                    issue_id,
                    f"**[watcher]** ACTION={response.action} 폐기 — 트리거 이후 시세/포지션이 크게 변동.",
                )
                await self._notifier.warn(
                    f"Tier2 stale 폐기 · {event.trigger_type}",
                    f"{event.stock_name or event.target_role} "
                    f"({event.stock_code or '-'}) — ACTION={response.action} "
                    f"무시 (시세 이동)",
                )
                return

            stage, stage_label = FAILURE_MULTICA, "교차검토"
            peer_response = await self._request_peer_review(
                event,
                issue_id=issue_id,
                primary_response=response,
                planner_result=planner_result,
            )
            final_response = response
            arbitration_response = None
            if peer_response is not None and peer_response.action != response.action:
                arbitration_response = await self._request_arbitration(
                    event,
                    issue_id=issue_id,
                    primary_response=response,
                    peer_response=peer_response,
                    planner_result=planner_result,
                )
                if arbitration_response is not None:
                    final_response = arbitration_response
                elif event.target_role == ROLE_SCREENER and response.action in {"TIER1", "TIER2"}:
                    self._status.mark_outcome(
                        entry,
                        outcome="skipped",
                        action=response.action,
                        detail="매수 교차검토 불일치 — 중재 미확정으로 신규 매수 차단",
                    )
                    await self._safe_notify_error(
                        "신규 매수 검토 미확정",
                        f"{event.stock_code}: primary={response.action}, "
                        f"peer={peer_response.action} — 중재 없이 매수하지 않습니다.",
                    )
                    return

            stage, stage_label = FAILURE_MARKET, "최종 stale 시세 조회"
            # This is the fresher of the two checks and the last thing before
            # the order, so its book is what prices a protective sell.
            still_valid, detail_bundle = await self._is_still_valid(event)
            if not still_valid:
                log.info(
                    "tier2 stale after review, dropping ACTION %s for %s",
                    final_response.action,
                    event.cooldown_key(),
                )
                self._status.mark_outcome(
                    entry,
                    outcome="stale",
                    action=final_response.action,
                    detail="검토 완료 직전 시세/포지션 변동으로 ACTION 폐기",
                )
                await self._dispatcher.add_comment(
                    issue_id,
                    f"**[watcher]** ACTION={final_response.action} 폐기 — "
                    "검토 완료 직전 시세/포지션이 크게 변동.",
                )
                await self._notifier.warn(
                    f"Tier2 stale 폐기 · {event.trigger_type}",
                    f"{event.stock_name or event.target_role} "
                    f"({event.stock_code or '-'}) — ACTION={final_response.action} "
                    f"무시 (최종 적용 전 시세 이동)",
                )
                return

            stage, stage_label = FAILURE_ORDER, "ACTION 적용"
            apply_result = await self._apply_action(
                event, final_response.action, planner_result, detail=detail_bundle
            )
            # Record the applied holding ACTION (post-stale-check) so the
            # dedup gate can suppress repeat no-ops on an idling position.
            # The outcome rides along because "the evaluator said sell" and
            # "a sell is working at the broker" are different facts, and only
            # the second one justifies re-dispatching a flat position.
            if event.trigger_type == "holding_swing" and event.stock_code:
                self._last_holding_action[event.stock_code] = (
                    final_response.action,
                    event.snapshot.get("profit_rate"),
                    datetime.now(KST),
                    apply_result.state,
                )
            if event.trigger_type == "new_candidate" and event.stock_code:
                self._last_candidate_action[event.stock_code] = (
                    final_response.action,
                    event.snapshot.get("score"),
                    datetime.now(KST),
                )
            # The outcome is whatever the apply actually did. It used to be
            # `executed` for any evaluator/screener ACTION while orders were
            # enabled — including HOLD, REJECT, and rejected orders (P1-1).
            outcome = apply_result.state
            detail_parts: list[str] = []
            if arbitration_response is not None:
                detail_parts.append(
                    f"primary={response.action}; "
                    f"peer={peer_response.action if peer_response else '-'}; "
                    f"coordinator={arbitration_response.action}"
                )
            elif peer_response is not None:
                detail_parts.append(f"peer_review={peer_response.action}")
            if apply_result.reason:
                detail_parts.append(apply_result.reason)
            if apply_result.order_no:
                detail_parts.append(f"order_no={apply_result.order_no}")
            self._status.mark_outcome(
                entry,
                outcome=outcome,
                action=final_response.action,
                detail=" · ".join(detail_parts) or None,
            )
            if peer_response is not None and peer_response.action != response.action:
                await self._notifier.warn(
                    f"교차검토 불일치 · {event.trigger_type}",
                    f"{event.stock_name or event.target_role} "
                    f"({event.stock_code or '-'}) — primary={response.action}, "
                    f"peer={peer_response.action}, "
                    f"final={final_response.action}",
                )
            await self._notify_tier2_outcome(
                event, final_response.action, apply_result, peer_response
            )
        except asyncio.CancelledError:
            # Normal shutdown path (`_cancel_in_flight`) — or, rarely, someone
            # cancelling this one slot. Either way it is not a fault: record it
            # as its own outcome so the trigger log does not show a phantom
            # failure every time the watcher restarts, and let it unwind.
            shutting_down = self._stop_event.is_set()
            log_at = log.info if shutting_down else log.warning
            log_at(
                "tier2 cancelled during %s: %s (shutdown=%s)",
                stage_label,
                event.cooldown_key(),
                shutting_down,
            )
            self._mark_late_outcome(
                entry,
                outcome="cancelled",
                detail=(
                    f"{stage_label} 중 종료로 취소"
                    if shutting_down
                    else f"{stage_label} 중 취소됨"
                ),
                scope_key=event.scope_key(),
            )
            raise
        except Exception as exc:  # noqa: BLE001 - operational containment
            detail = self._record_failure(stage, exc)
            log.exception(
                "tier2 task failed during %s: %s (category=%s)",
                stage_label,
                event.cooldown_key(),
                stage,
            )
            self._mark_late_outcome(
                entry,
                outcome="failed",
                detail=f"{stage_label}: {detail}",
                scope_key=event.scope_key(),
            )
            await self._safe_notify_error(
                f"Tier2 처리 실패 · {event.trigger_type}",
                f"{event.stock_name or event.target_role} "
                f"({event.stock_code or '-'}) — {stage_label} 실패\n{detail}",
            )
        finally:
            # The slot must be released on every path — a leaked entry locks
            # this stock (or role) out of every future dispatch for the life
            # of the process.
            self._in_flight.pop(event.scope_key(), None)
            self._status.remove_in_flight(event.scope_key())

    async def _request_peer_review(
        self,
        event: TriggerEvent,
        *,
        issue_id: str,
        primary_response,
        planner_result: dict[str, Any] | None = None,
    ):
        if not self._config.agent_peer_review_enabled:
            return None
        review = getattr(self._dispatcher, "request_peer_review", None)
        if review is None:
            return None
        try:
            peer = await review(
                issue_id,
                issue_type=self._issue_type_for_event(event),
                trigger_comment=self._build_trigger_comment(event, planner_result),
                primary_response=primary_response,
                timeout_seconds=self._config.agent_peer_review_timeout_seconds,
                poll_seconds=self._config.agent_peer_review_poll_seconds,
            )
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001 - peer review is best-effort
            # Swallowed on purpose: a second opinion failing must not void the
            # primary ACTION. Counting it keeps a silently-degraded review
            # pipeline visible instead of looking like a healthy cycle.
            detail = self._record_failure(FAILURE_MULTICA, exc)
            log.warning(
                "peer review failed for %s: %s", event.cooldown_key(), detail
            )
            return None
        if peer is None:
            log.debug(
                "peer review not run for %s (squad-routed, no-op ACTION, or timeout)",
                event.cooldown_key(),
            )
        return peer

    async def _request_arbitration(
        self,
        event: TriggerEvent,
        *,
        issue_id: str,
        primary_response,
        peer_response,
        planner_result: dict[str, Any] | None = None,
    ):
        if not self._config.agent_arbitration_enabled:
            return None
        arbitrate = getattr(self._dispatcher, "request_action_arbitration", None)
        if arbitrate is None:
            return None
        try:
            result = await arbitrate(
                issue_id,
                issue_type=self._issue_type_for_event(event),
                trigger_comment=self._build_trigger_comment(event, planner_result),
                primary_response=primary_response,
                peer_response=peer_response,
                timeout_seconds=self._config.agent_arbitration_timeout_seconds,
                poll_seconds=self._config.agent_arbitration_poll_seconds,
            )
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001 - arbitration is best-effort
            detail = self._record_failure(FAILURE_MULTICA, exc)
            log.warning(
                "agent arbitration failed for %s: %s", event.cooldown_key(), detail
            )
            return None
        if result is None:
            log.info("agent arbitration unavailable/timeout for %s", event.cooldown_key())
        return result

    # -- stale check ---------------------------------------------------------

    async def _is_still_valid(
        self, event: TriggerEvent
    ) -> tuple[bool, dict[str, Any] | None]:
        """Is the ACTION still current, and the quote bundle that decided it.

        The bundle is returned rather than stored on ``self`` because
        ``_await_and_apply`` runs one background task per trigger and two
        stocks can be in flight at once -- a shared slot would price one
        stock's sell order off another stock's book. The caller passes it
        down explicitly instead.

        ``None`` for the bundle is ordinary, not an error: the early returns
        below never fetch one.
        """

        # We re-fetch the current quote for the trigger's stock and compare to
        # the snapshot price.
        if event.scope != "stock" or not event.stock_code:
            return True, None

        snap_price = event.snapshot.get("current_price")
        if not snap_price:
            return event.target_role != ROLE_SCREENER, None

        from . import market as market_service

        detail = await market_service.get_stock_detail_bundle(
            self._client,
            stock_code=event.stock_code,
            **({"bar_limit": max(5, self._config.ma_period)} if event.target_role == ROLE_SCREENER else {}),
        )
        cur_price = detail.get("quote", {}).get("cur_prc")
        try:
            cur_f = float(str(cur_price).replace("+", "").replace("-", ""))
        except (TypeError, ValueError):
            return event.target_role != ROLE_SCREENER, detail
        try:
            snap_f = float(snap_price)
        except (TypeError, ValueError):
            return event.target_role != ROLE_SCREENER, detail
        if not isfinite(cur_f) or not isfinite(snap_f) or cur_f <= 0 or snap_f <= 0:
            return event.target_role != ROLE_SCREENER, detail
        delta_pct = abs(cur_f - snap_f) / snap_f * 100
        return delta_pct <= self._config.stale_price_delta_pct, detail

    # -- ACTION → orders -----------------------------------------------------

    async def _apply_action(
        self,
        event: TriggerEvent,
        action: str,
        planner_result: dict[str, Any],
        *,
        detail: dict[str, Any] | None = None,
    ) -> OrderApplyResult:
        """Map the agent's ACTION tag to an actual order (or no-op).

        Always returns a result describing what happened — the caller records
        it verbatim, so a no-op or a rejected order can no longer be logged as
        a trade.
        """

        action = (action or "").upper()
        if self._superseded_by_protective_trigger(event):
            return OrderApplyResult.skipped(action, "보호주문 발생 이후 오래된 agent 판단 폐기")
        if not self._can_execute_orders():
            log.info(
                "tier2 dry-run (execute disabled): action=%s key=%s",
                action,
                event.cooldown_key(),
            )
            return OrderApplyResult.skipped(action, "execute_orders=False")

        if event.target_role == ROLE_EVALUATOR or (
            event.target_role == ROLE_PM and event.scope == "stock"
        ):
            return await self._apply_holding_action(event, action, detail=detail)
        if event.target_role == ROLE_SCREENER:
            return await self._apply_candidate_action(event, action, planner_result)
        # PM portfolio-level + risk responses are recorded as comments only
        # for v1 — auto-execution at portfolio level is too risky without
        # finer-grained ACTION semantics.
        log.info(
            "tier2 informational only: role=%s action=%s",
            event.target_role,
            action,
        )
        return OrderApplyResult.informational(
            action, f"{event.target_role} 역할은 기록만 (v1)"
        )

    async def _apply_holding_action(
        self,
        event: TriggerEvent,
        action: str,
        *,
        detail: dict[str, Any] | None = None,
    ) -> OrderApplyResult:
        """Sell-side actions per the evaluator's response."""

        qty = event.snapshot.get("quantity")
        if not qty:
            return OrderApplyResult.skipped(action, "보유 수량 없음")
        sell_qty: int | None = None
        exit_at_market = False
        if action == "HOLD":
            return OrderApplyResult.informational(action, "HOLD — 주문 없음")
        if action == "TRIM":
            sell_qty = max(int(qty) // 2, 1)
        elif action in ("TAKE_PROFIT", "ROTATE"):
            sell_qty = int(qty)
        elif action == "CUT_LOSS":
            sell_qty = int(qty)
            exit_at_market = True  # emergency: fill certainty over price
        else:
            return OrderApplyResult.informational(
                action, "매도 매핑 없는 ACTION — 주문 없음"
            )

        # Oversell guard. A re-firing exit must not sell shares an earlier
        # order is already working on. Never blocks outright when there is
        # anything left to sell — it clamps.
        code = str(event.stock_code or "")
        sellable = await self._sellable_quantity_now(code, int(qty))
        if self._superseded_by_protective_trigger(event):
            return OrderApplyResult.skipped(action, "보호주문 발생 이후 오래된 agent 매도 폐기")
        if sellable <= 0:
            log.info(
                "sell skipped: %s already fully covered by working sell orders",
                code,
            )
            return OrderApplyResult.skipped(
                action, "기존 매도 주문이 보유 수량을 이미 커버 — 중복 매도 차단"
            )
        if sell_qty > sellable:
            log.info(
                "sell clamped for %s: %d → %d (working sell orders)",
                code, sell_qty, sellable,
            )
            sell_qty = sellable

        # Price the order. trde_tp="0" is 보통 -- a plain limit -- and the
        # broker requires `ord_uv` for it; sending it empty is what rejected
        # every Tier-2 exit on 2026-08-31 (308003, 7 for 7, the first live
        # run of this path). The comment on that line said "limit at best
        # bid", which is the right idea and simply was not implemented.
        #
        # The bid comes from the order book `_is_still_valid` already
        # fetched moments ago, so this costs no extra call and the price is
        # a real book level -- tick-valid by construction, with no rounding
        # arithmetic to get wrong.
        if exit_at_market:
            order_type_code, ord_uv = "3", ""
        else:
            best_bid, no_bid_reason = _best_bid_from_detail(detail)
            if best_bid:
                order_type_code, ord_uv = "0", str(best_bid)
            else:
                # An exit that cannot be priced still has to happen -- the
                # fail-closed asymmetry runs the other way for protective
                # sells. Logged because a systematic book-fetch failure would
                # otherwise turn every exit into a market order in silence.
                order_type_code, ord_uv = "3", ""
                log.warning(
                    "sell price unavailable for %s (%s) — exiting at market",
                    code,
                    no_bid_reason,
                )

        intent, duplicate = await self._record_protective_intent(
            stock_code=code,
            side=order_ledger.SIDE_SELL,
            quantity=sell_qty,
            # Deliberately not `ord_uv`. The decision is "sell N of X because
            # ACTION", not "sell at price P" -- the price is in the decision
            # key, so a bid that ticks between re-fires would mint a fresh
            # decision every time and defeat the duplicate-sell guard.
            price=None,
            origin=event.trigger_type,
            decision_scope=action,
        )
        if duplicate is not None:
            return OrderApplyResult.skipped(action, duplicate)
        order_result = await order_service.place_stock_sell_order(
            self._client,
            stk_cd=event.stock_code or "",
            ord_qty=str(sell_qty),
            order_type_code=order_type_code,
            ord_uv=ord_uv,
        )
        result = OrderApplyResult.from_order_response(action, order_result)
        self._settle_intent(intent, result)
        return result

    async def _apply_candidate_action(
        self,
        event: TriggerEvent,
        action: str,
        planner_result: dict[str, Any],
    ) -> OrderApplyResult:
        """Buy-side actions per the screener's response."""

        if action == "REJECT" or action == "NO_TAG":
            return OrderApplyResult.informational(action, f"{action} — 매수 없음")
        if action not in ("TIER1", "TIER2"):
            return OrderApplyResult.informational(
                action, "매수 매핑 없는 ACTION — 주문 없음"
            )

        async with self._buy_lock:
            return await self._submit_candidate_buy(event, action, planner_result)

    async def _refresh_entry_portfolio(
        self, planner_result: dict[str, Any]
    ) -> dict[str, Any]:
        """Rebuild exposure and budget from a complete, current account read."""

        from . import account as account_service

        evaluation = await account_service.get_account_evaluation(self._client)
        if not evaluation.get("success") or evaluation.get("warning"):
            raise RuntimeError(
                f"매수 전 잔고 조회 불완전: {evaluation.get('warning') or evaluation.get('error') or evaluation.get('message')}"
            )
        records = evaluation.get("evaluation_data")
        if not isinstance(records, list) or not records:
            raise ValueError("매수 전 계좌 평가 데이터 없음")
        raw_holdings = []
        for record in records:
            if not isinstance(record, dict) or not isinstance(record.get("stk_acnt_evlt_prst"), list):
                raise ValueError("매수 전 보유종목 데이터 형식 오류")
            for row in record["stk_acnt_evlt_prst"]:
                if not isinstance(row, dict):
                    raise ValueError("매수 전 보유종목 행 형식 오류")
                quantity = int(str(row.get("rmnd_qty")).replace(",", ""))
                code = order_ledger.normalize_stock_code(row.get("stk_cd"))
                if quantity and (not code or not to_price(row.get("cur_prc"))):
                    raise ValueError("매수 전 보유 수량/평가금액 확인 불가")
                raw_holdings.append(row)
        summary = {**records[0], "stk_acnt_evlt_prst": raw_holdings}
        _, holdings = _normalize_holding_rows({"evaluation_data": [summary]})
        codes = [order_ledger.normalize_stock_code(row["stock_code"]) for row in holdings]
        if len(codes) != len(set(codes)):
            raise ValueError("매수 전 잔고에 중복 종목 행 존재 — 노출 확인 불가")
        old_portfolio = planner_result.get("portfolio") or {}
        fresh_budget = _safe_budget_amount(
            summary, position_budget_pct=self._config.position_budget_pct
        )
        portfolio = {
            **old_portfolio,
            "position_budget": min(int(old_portfolio.get("position_budget") or 0), fresh_budget),
            "max_positions": min(
                int(old_portfolio.get("max_positions") or self._config.max_positions),
                self._config.max_positions,
            ),
            "holding_count": len(holdings),
            "estimated_assets": summary.get("prsm_dpst_aset_amt") or summary.get("aset_evlt_amt"),
            "daily_pl_krw": summary.get("tdy_lspft"),
            "daily_pl_pct_broker": summary.get("tdy_lspft_rt"),
        }
        await self._update_entry_breaker(portfolio, now=self._market_session_status().observed_at)
        return {**planner_result, "portfolio": portfolio, "holdings": holdings}

    async def _submit_candidate_buy(
        self,
        event: TriggerEvent,
        action: str,
        planner_result: dict[str, Any],
    ) -> OrderApplyResult:
        """Check and submit one entry while holding the account-wide buy lock."""

        if not self._config.new_entries_enabled:
            return OrderApplyResult.skipped(action, "신규 매수 중지 모드 — 보호매도/취소만 허용")
        if not self._is_market_open(self._market_session_status().observed_at):
            return OrderApplyResult.skipped(action, "정규장 종료/불확실 — 신규 매수 차단")

        # Daily circuit breaker — the first gate on the only path that opens
        # new exposure. Deliberately not reachable from `_apply_holding_action`
        # or `_execute_tier1`: a breaker that could block an exit would turn a
        # bad day into an unbounded one.
        entry_decision = self._breaker.check_new_entry()
        if not entry_decision.allowed:
            log.warning(
                "candidate buy blocked by daily breaker (%s): %s",
                entry_decision.code,
                entry_decision.reason,
            )
            return OrderApplyResult.skipped(
                action, entry_decision.reason or "일일 서킷브레이커"
            )

        code = str(event.stock_code)

        # Order ledger — fail closed. Without a durable record of what we have
        # already sent, a restart or a lost response can re-buy a position we
        # already hold, which is the whole reason the ledger exists (P0-2).
        try:
            ledger = self._require_ledger()

            # Ask the BROKER, not just our own records, before opening
            # exposure. The per-tick pass can be a poll interval old and
            # skips executions, and — the case this gate exists for — an
            # empty ledger is not evidence that the broker is idle. See
            # `_broker_gate_for_new_buy`.
            blocked = await self._broker_gate_for_new_buy(code)
            if blocked is not None:
                log.warning("candidate buy blocked: %s", blocked)
                await self._safe_notify_error(
                    "🛑 신규 매수 차단",
                    f"{blocked}\n손절·익절·매도·주문취소는 계속 동작합니다.",
                )
                return OrderApplyResult.skipped(action, blocked)

            if ledger.has_unresolved(code, order_ledger.SIDE_BUY):
                pending = ledger.unresolved(
                    stock_code=code, side=order_ledger.SIDE_BUY
                )
                states = ", ".join(sorted({i.state for i in pending}))
                log.warning(
                    "candidate buy blocked: %d unresolved buy intent(s) for %s (%s)",
                    len(pending), code, states,
                )
                return OrderApplyResult.skipped(
                    action,
                    f"미종결 매수 intent {len(pending)}건 ({states}) — 중복 주문 차단",
                )
        except OrderLedgerError as exc:
            detail = self._record_failure(FAILURE_ORDER, exc)
            await self._alert_ledger_fault_once(detail)
            return OrderApplyResult.skipped(action, f"주문 원장 사용 불가: {detail}")

        try:
            planner_result = await self._refresh_entry_portfolio(planner_result)
        except Exception as exc:
            detail = self._record_failure(FAILURE_ACCOUNT, exc)
            return OrderApplyResult.skipped(action, f"최신 잔고 확인 불가: {detail}")
        try:
            event = await self._refresh_entry_candidate(event, planner_result)
        except Exception as exc:
            detail = self._record_failure(FAILURE_MARKET, exc)
            return OrderApplyResult.skipped(action, f"매수 조건 재검증 실패: {detail}")
        entry_decision = self._breaker.check_new_entry()
        if not entry_decision.allowed:
            return OrderApplyResult.skipped(action, entry_decision.reason or "일일 서킷브레이커")
        if self._superseded_by_protective_trigger(event):
            return OrderApplyResult.skipped(action, "보호주문 발생 이후 오래된 agent 매수 폐기")
        if not self._is_market_open(self._market_session_status().observed_at):
            return OrderApplyResult.skipped(action, "잔고 확인 중 정규장 종료 — 신규 매수 차단")

        snapshot = event.snapshot
        entry_price = snapshot.get("entry_price")
        try:
            entry_int = int(float(str(entry_price).replace("+", "")))
        except (TypeError, ValueError):
            return OrderApplyResult.skipped(action, "진입가 파싱 불가")
        if entry_int <= 0:
            return OrderApplyResult.skipped(action, "진입가 ≤ 0")

        budget = (planner_result.get("portfolio") or {}).get("position_budget") or 0
        try:
            budget = int(budget)
        except (TypeError, ValueError):
            budget = 0
        if budget <= 0:
            return OrderApplyResult.skipped(action, "position_budget ≤ 0")

        # Portfolio-exposure gates. The watcher routes candidate buys
        # directly (bypassing strategy.plan_intraday_momentum_strategy's
        # slot/budget gates), so without these it would buy `usable` every
        # time a candidate fires — no per-stock ceiling and no max-positions
        # cap. Real incidents: HS화성 was bought 5× on 5-min cooldowns to
        # 2.2× its budget (2026-06-11), and 6/9 held 4 distinct stocks with
        # max_positions=3. We re-derive both gates from planner_result here.
        portfolio = planner_result.get("portfolio") or {}
        holdings = planner_result.get("holdings") or []
        max_positions = portfolio.get("max_positions") or 0

        # Own in-flight exposure now comes from the ledger instead of the old
        # in-memory `_placed_orders` dict: same gates, but the record survives
        # a restart instead of evaporating with the process.
        pending_codes = ledger.unresolved_codes(order_ledger.SIDE_BUY)

        # `code` comes from the candidate row (bare six digits); holdings come
        # back A-prefixed. Compared raw, a held name is invisible here: gate 2
        # would not subtract its existing exposure and gate 1 would count it as
        # a new position. Masked today only because max_positions=1 blocks
        # anything new anyway — at 2+ the same name could take full budget
        # twice, which is what the 2026-06-11 gates exist to prevent.
        norm = order_ledger.normalize_stock_code
        code_key = norm(code)
        held = next(
            (h for h in holdings if norm(h.get("stock_code")) == code_key), None
        )
        held_codes = {norm(h.get("stock_code")) for h in holdings}

        # Gate 1 — max_positions: distinct codes across holdings ∪ own
        # in-flight (placed-but-not-yet-reflected). UNION, not a sum — a
        # filled order's code lives in both sets but counts once. A NEW stock
        # can't open once the union is at the cap.
        # `pending_codes` already arrives normalized from the ledger.
        distinct_codes = held_codes | pending_codes
        if (
            code_key not in distinct_codes
            and max_positions
            and len(distinct_codes) >= max_positions
        ):
            log.info(
                "candidate buy skipped: max_positions %d reached "
                "(held+placed distinct=%d, %s)",
                max_positions, len(distinct_codes), code,
            )
            return OrderApplyResult.skipped(
                action,
                f"max_positions {max_positions} 도달 "
                f"(보유+접수 distinct={len(distinct_codes)})",
            )

        # Gate 2 — per-stock cumulative budget: holdings value + own placed
        # value for this code, so repeat fires can't stack past `budget`
        # before the buy shows up in the account.
        already_value = 0
        if held is not None:
            try:
                held_qty = int(held.get("quantity") or 0)
                held_px = held.get("current_price") or entry_int
                held_px = int(float(str(held_px).replace("+", "")))
                already_value = held_qty * (held_px if held_px > 0 else entry_int)
            except (TypeError, ValueError):
                already_value = 0
        already_value += ledger.unresolved_notional(code, order_ledger.SIDE_BUY)
        remaining = budget - already_value
        if remaining < entry_int:  # can't afford even 1 share within budget
            log.info(
                "candidate buy skipped: per-stock budget exhausted "
                "(%s, held+placed≈%d / budget %d)",
                code, already_value, budget,
            )
            return OrderApplyResult.skipped(
                action,
                f"종목별 예산 소진 (보유+접수≈{already_value:,} / 예산 {budget:,})",
            )

        # TIER1 = full budget; TIER2 = half budget (smaller probe).
        # Cap by the remaining per-stock budget either way.
        usable = budget if action == "TIER1" else budget // 2
        usable = min(usable, remaining)
        quantity = floor(usable / entry_int)
        if quantity < 1:
            return OrderApplyResult.skipped(
                action, f"남은 예산 {usable:,}원으로 1주 미만"
            )

        # Commit the intent BEFORE the request leaves. A crash between here
        # and the API call leaves an INTENDED row that restart reconciliation
        # must resolve against the broker — far better than the old behaviour,
        # where the same crash left no trace at all.
        try:
            registration = ledger.record_intent(
                stock_code=code,
                side=order_ledger.SIDE_BUY,
                quantity=quantity,
                price=entry_int,
                origin=event.trigger_type,
                decision_scope=action,
            )
            if not registration.may_submit:
                # The identical decision is already in flight or already
                # concluded in this bucket. Reusing that row as grounds for a
                # second order would double the position and overwrite the
                # existing audit record.
                log.warning(
                    "candidate buy skipped (%s): %s",
                    registration.outcome,
                    registration.reason,
                )
                return OrderApplyResult.skipped(
                    action, registration.reason or "동일 결정 중복 — 주문 생략"
                )
            intent = registration.intent
        except OrderLedgerError as exc:
            detail = self._record_failure(FAILURE_ORDER, exc)
            await self._alert_ledger_fault_once(detail)
            return OrderApplyResult.skipped(action, f"주문 원장 기록 실패: {detail}")

        order_type_code = snapshot.get("entry_order_type_code") or "3"
        new_entry = code_key not in held_codes
        reserved_day = self._breaker.state.trading_day
        if new_entry:
            self._breaker.record_new_entry()
            if self._breaker.to_dict().get("state_error"):
                ledger.mark_state(
                    intent.intent_id, order_ledger.STATE_REJECTED,
                    reason="not submitted: daily entry reservation could not be persisted",
                )
                return OrderApplyResult.skipped(action, "일일 진입 예약 저장 실패 — 주문 미전송")
        order_result = await order_service.place_stock_buy_order(
            self._client,
            stk_cd=event.stock_code or "",
            ord_qty=str(quantity),
            order_type_code=str(order_type_code),
            ord_uv=str(entry_price) if entry_price else "",
        )
        result = OrderApplyResult.from_order_response(action, order_result)
        self._settle_intent(intent, result)
        # `submitted` for sure, and `unknown` too — a lost response might still
        # have booked the order, and treating it as nothing is how the same
        # stock gets bought twice. A `failed` order releases its slot: a
        # rejection is proof the broker holds nothing.
        if new_entry and not result.counts_as_exposure:
            try:
                settled = ledger.get(intent.intent_id)
            except OrderLedgerError as exc:
                self._record_failure(FAILURE_ORDER, exc)
                settled = None
            if settled is not None and settled.state == order_ledger.STATE_REJECTED and not settled.filled_quantity:
                self._breaker.release_new_entry(trading_day=reserved_day)
            else:
                return OrderApplyResult.for_state(
                    ORDER_STATE_UNKNOWN, action=action, order_no=result.order_no,
                    reason="REST 실패와 원장 상태 불일치 — 진입 예약 유지, 브로커 대사 필요",
                )
        return result

    async def _refresh_entry_candidate(
        self, event: TriggerEvent, planner_result: dict[str, Any]
    ) -> TriggerEvent:
        """Recheck the signal and price with uncached data immediately before buying."""

        valid, detail = await self._is_still_valid(event)
        if not valid or detail is None or detail.get("success") is False:
            raise ValueError("시세 누락 또는 트리거 이후 가격 변동 초과")
        if self._api_failure_count > 0:
            raise ValueError("최근 감시 사이클의 데이터 조회 실패 — 신규 진입 보류")
        regime = self._prev_regime or planner_result.get("regime") or {}
        if not regime or not regime.get("market_data_complete", True):
            raise ValueError("현재 시장 레짐 확인 불가")
        eligible, scored = _score_candidate(
            {"stock_code": event.stock_code, **event.snapshot},
            detail,
            regime,
            min_market_cap_krw=self._config.min_market_cap_krw,
            day_change_min=self._config.day_change_min,
            day_change_max=self._config.day_change_max,
            entry_mode=self._config.entry_mode,
            ma_period=self._config.ma_period,
        )
        if not eligible or scored["score"] < self._config.new_candidate_min_score:
            raise ValueError(
                f"현재 진입 조건 미달 (score={scored['score']}): {scored['reasons']}"
            )
        book = detail.get("orderbook") or {}
        bid, ask = to_price(book.get("buy_fpr_bid")), to_price(book.get("sel_fpr_bid"))
        if not bid or not ask or bid > ask:
            raise ValueError("현재 매수/매도 호가 확인 불가")
        return replace(event, snapshot={**event.snapshot, **scored})

    def _superseded_by_protective_trigger(self, event: TriggerEvent) -> bool:
        """A protective trigger invalidates earlier discretionary decisions for its stock."""

        code = order_ledger.normalize_stock_code(event.stock_code)
        observed_at = self._protective_trigger_at.get(code)
        return observed_at is not None and observed_at >= event.detected_at

    # -- state lifecycle -----------------------------------------------------

    async def _cancel_in_flight(self) -> None:
        """Cancel every pending Tier-2 dispatch and clear both slot registries.

        The slot list is snapshotted first: each task's ``finally`` pops itself
        from ``_in_flight`` as it unwinds, so iterating the live dict while
        awaiting them is a mutation-during-iteration hazard.
        """

        slots = list(self._in_flight.values())
        for slot in slots:
            slot.task.cancel()
        if slots:
            # `return_exceptions=True` also retrieves each task's exception,
            # which is what keeps shutdown from emitting "Task exception was
            # never retrieved" for anything still in flight.
            await asyncio.gather(
                *(slot.task for slot in slots), return_exceptions=True
            )
        for slot in slots:
            self._status.remove_in_flight(slot.scope_key)
        self._in_flight.clear()

    async def _sleep_with_stop(self, seconds: int) -> None:
        if seconds <= 0:
            return
        try:
            await asyncio.wait_for(self._stop_event.wait(), timeout=seconds)
        except asyncio.TimeoutError:
            return

    def _is_market_open(self, now: datetime | None = None) -> bool:
        return is_krx_regular_session_open(now)

    def _market_session_status(
        self, now: datetime | None = None
    ) -> KrxSessionStatus:
        return krx_regular_session_status(now)

    def _should_run_tick(self, now: datetime | None = None) -> bool:
        """Keep safety paths live when session metadata is uncertain."""

        return self._market_session_status(now).state != SESSION_CLOSED

    def _load_previous_state(self) -> dict[str, Any] | None:
        """The snapshot the previous process left on the PVC, or None.

        Best-effort like the writer: a missing, empty or corrupt file means
        there is no last session to show, never a failed start.
        """

        try:
            payload = json.loads(self._state_path.read_text())
        except (OSError, ValueError):
            return None
        if not isinstance(payload, dict) or not payload.get("last_tick_at"):
            return None
        return payload

    def _persist_state(self) -> None:
        """Best-effort snapshot for observability."""

        try:
            self._state_path.parent.mkdir(parents=True, exist_ok=True)
            snapshot = self._status.snapshot()
            payload = {
                "updated_at": datetime.now(KST).isoformat(),
                "cycle_count": self._cycle_count,
                "last_tick_at": self._last_tick_at.isoformat()
                if self._last_tick_at
                else None,
                "last_error": self._last_error,
                "in_flight": [
                    {
                        "scope_key": slot.scope_key,
                        "trigger_type": slot.trigger.trigger_type,
                        "stock_code": slot.trigger.stock_code,
                        "started_at": slot.started_at.isoformat(),
                    }
                    for slot in self._in_flight.values()
                ],
                "api_failure_count": self._api_failure_count,
                "failures": self._status.failure_summary(),
                "daily_entry_breaker": self._breaker.to_dict(),
                "order_ledger": self._ledger_snapshot(),
                "regime": self._prev_regime,
                # The dashboard shows these for the last session when the
                # current process has not ticked yet (off hours, or a
                # rollout before the open). Without them a restarted watcher
                # can report nothing about the day it just traded.
                "candidate_slots": snapshot.get("candidate_slots"),
                "candidates": snapshot.get("candidates"),
                "portfolio": snapshot.get("portfolio"),
            }
            self._state_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2)
            )
        except Exception:
            pass


__all__ = [
    "DEFAULT_STATE_PATH",
    "InFlightTask",
    "IntradayWatcher",
    "WatcherConfig",
]
