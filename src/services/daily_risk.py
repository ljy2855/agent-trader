"""Daily circuit breaker for **new entries only**.

Per-stock stop-loss and ``position_budget_pct`` cap what one position can
lose; nothing capped what the *account* could lose in a day. A wrong signal
or a stale data feed could keep opening fresh positions in different names
all session, and the only brake was a human noticing a Discord message
(P0-1 of ``docs/ops/system-evaluation-2026-07-26.md``).

The invariant this module exists to protect:

    **The breaker only ever blocks opening new exposure. Selling, stop-loss,
    take-profit and order cancellation are never gated by it.**

A breaker that could block an exit would turn a bad day into an unbounded
one. Nothing here is reachable from the sell or cancel paths.

Two distinct kinds of block, deliberately not merged:

``latched trip``
    A configured threshold was breached (daily loss in KRW or %, or the
    day's new-entry count). Latches for the rest of the KST trading day and
    survives a restart — it does **not** clear when the loss recovers,
    because a threshold breach means the day's assumptions were wrong, not
    that the next tick is trustworthy. Clears only once the **next KRX
    trading day** is reached: a weekend or holiday is the same closed
    trading day, not a new one, so a Friday latch is still a latch on
    Saturday and ``/state`` keeps reporting it (see :func:`should_reset`).
``transient block``
    Something we depend on cannot be trusted right now, so we cannot prove
    we are inside the limits:

    * the KRX calendar year is unsupported, the date is an unverified special
      session, or today is a known close (``BLOCK_CALENDAR_UNCERTAIN`` /
      ``BLOCK_CALENDAR_CLOSED``). This gate is always active even when the
      optional loss/count thresholds are disabled,
    * the account snapshot is missing or unparseable
      (``BLOCK_ACCOUNT_DATA``),
    * the durable state could not be read or could not be written
      (``BLOCK_STATE_UNAVAILABLE``) — we may be sitting on a latch we failed
      to load, or holding one a restart would silently undo, or
    * a loss limit is armed but its data source has never been validated
      against a live account (``BLOCK_LOSS_SOURCE_UNVERIFIED``) — see
      "Loss-source verification" below.

    New buys fail closed while that lasts and resume when the condition
    clears. None of them latch — one bad poll or one bad disk write should
    not cost a session — and all are reported on ``/state``.

Calendar uncertainty never clears an existing latch. ``resets_on`` is
reported only when a definitely supported future trading day can be proved.
An uncertain special-session date is conservatively skipped to the next
definite trading day; crossing into an unsupported year reports
``resets_on=null`` and preserves the latch until the annual calendar update.
This is bounded by the supported-year table, so year-end cannot spin in a
search loop or invent a reset date.

## Loss-source verification (default: UNVERIFIED)

``max_daily_loss_krw`` and ``max_daily_loss_pct`` are **armed but not
enforceable** until an operator explicitly says the source has been checked.
Until then, arming either one blocks new entries outright rather than
comparing them against the threshold.

That is not belt-and-braces caution, it is the only sound reading of the
data. ``tdy_lspft`` parses as a clean number, but what it *counts* is
undocumented: realized-only or realized plus unrealized, gross or net of
commission and tax. If it turns out to exclude unrealized P&L, an account
sitting on a large open loss reports a flat day — and a breaker that trusted
it would wave through new entry after new entry precisely when it should be
stopping. "Below the threshold" from a source of unknown meaning is not
evidence of a safe account, so the breaker refuses to treat it as one.

``max_daily_new_entries`` is unaffected: it counts orders this process
placed and needs nothing from the broker's P&L, so a count-only
configuration is fully usable today.

**Enabling enforcement requires live-account semantic validation that this
codebase cannot perform.** An operator has to, on a real account:

1. Compare ``tdy_lspft`` against the day's realized P&L from the trading
   journal (``ka10170``) to see whether the two agree.
2. Hold an open position at a known unrealized loss and check whether
   ``tdy_lspft`` moves with it — that settles realized-only vs inclusive.
3. Confirm the sign convention and whether commission and tax are already
   deducted.

Only then pass ``--acknowledge-daily-loss-source-verified``. No production
code path sets that flag; it comes from a human on the command line. Tests
that exercise threshold mechanics opt in explicitly, exactly as an operator
would — the flag is never a default and never inferred.

All three limits default to ``0`` (disabled). The explicit calendar-confidence
gate remains active because an unsupported weekday is not evidence that new
exposure may be opened.

## Kiwoom daily P&L fields — what is actually documented

``kt00004`` (계좌평가현황요청) is the **only** account-level source of a daily
P&L figure, and ``strategy.plan_intraday_momentum_strategy`` already calls it
every tick, so the breaker costs no extra API traffic. Per
``kiwoom_api_spec.md``:

===================  ==========================================
``tdy_lspft``        당일투자손익 — today's P&L in KRW  ← used
``tdy_lspft_rt``     당일손익율 — today's P&L rate (%)
``tdy_lspft_amt``    당일투자**원금** — today's invested principal
``lspft``            누적투자손익 (cumulative, not daily)
``lspft2``           당월투자손익 (this month, not daily)
``lspft_ratio``      당월손익율 (this month's rate)
``lspft_rt``         누적손익율 (cumulative rate)
===================  ==========================================

``kt00017`` (계좌별당일현황요청) carries no P&L field at all — only deposits,
withdrawals, buy/sell amounts, commission and tax — so anything daily from
there would be a derivation, not a reading.

**Documented limits of this adapter:**

1. ``tdy_lspft``/``tdy_lspft_rt`` have never been read by this repository
   before (no fixture, no live sample). The field *names* come from the
   spec, not from an observed payload. Until an enabled breaker has been
   watched against a live account for a session, treat its numbers as
   unverified.
2. Whether ``tdy_lspft`` is realized-only or realized + unrealized, and
   whether it is net of commission and tax, is not stated in the spec. The
   breaker therefore treats it as an opaque "today's P&L" scalar and never
   tries to decompose it.
3. ``src/dashboard.py`` currently labels ``tdy_lspft_amt`` as today's P&L
   and prefers ``lspft_ratio`` (a *monthly* rate) for a daily figure. Per
   the table above both look wrong. That is out of scope here and was left
   alone — this module does not reuse the dashboard's mapping.
4. The percentage is computed against total account assets rather than the
   broker's own ``tdy_lspft_rt``; see :func:`AccountDailySnapshot.loss_pct`.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from .krx_calendar import (
    DAY_CLOSED,
    DAY_UNCERTAIN,
    SUPPORTED_KRX_CALENDAR_YEARS,
    KrxDayStatus,
    krx_day_status,
)

KST = ZoneInfo("Asia/Seoul")

log = logging.getLogger("kiwoom.watcher.daily_risk")

DEFAULT_STATE_PATH = (
    Path(__file__).resolve().parents[2] / "output" / "daily_risk_state.json"
)

# Machine-readable block codes, surfaced on `/state` and in the trigger log.
BLOCK_DAILY_LOSS_KRW = "daily_loss_krw"
BLOCK_DAILY_LOSS_PCT = "daily_loss_pct"
BLOCK_MAX_NEW_ENTRIES = "max_daily_new_entries"
BLOCK_ACCOUNT_DATA = "account_data_unavailable"
BLOCK_STATE_UNAVAILABLE = "breaker_state_unavailable"
BLOCK_LOSS_SOURCE_UNVERIFIED = "loss_source_unverified"
BLOCK_CALENDAR_CLOSED = "krx_calendar_closed"
BLOCK_CALENDAR_UNCERTAIN = "krx_calendar_uncertain"

# Trips that latch for the trading day. `BLOCK_ACCOUNT_DATA`,
# `BLOCK_STATE_UNAVAILABLE` and `BLOCK_LOSS_SOURCE_UNVERIFIED` are
# deliberately absent — they block while the underlying problem lasts, they
# do not burn the session.
LATCHING_BLOCKS = frozenset(
    {BLOCK_DAILY_LOSS_KRW, BLOCK_DAILY_LOSS_PCT, BLOCK_MAX_NEW_ENTRIES}
)


def current_trading_day(now: datetime | None = None) -> date:
    """The KST calendar day a decision belongs to."""

    current = now or datetime.now(KST)
    if current.tzinfo is None:
        current = current.replace(tzinfo=KST)
    return current.astimezone(KST).date()


@dataclass(frozen=True, slots=True)
class ResetSchedule:
    """Conservative next-reset date derived from the supported calendar."""

    resets_on: date | None
    exact: bool
    reason: str | None = None
    uncertain_dates: tuple[date, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "resets_on": self.resets_on.isoformat() if self.resets_on else None,
            "exact": self.exact,
            "reason": self.reason,
            "uncertain_dates": [day.isoformat() for day in self.uncertain_dates],
        }


def next_trading_day_status(day: date) -> ResetSchedule:
    """Find the next *definitely supported* KRX trading day.

    An uncertain special-session date is skipped in the conservative
    direction: a later definite trading day is a safe reset date regardless
    of whether the uncertain date traded.  Crossing into an unsupported year
    returns no date at all, preserving the latch until calendar data is
    reviewed rather than guessing or looping forever.
    """

    if day.year not in SUPPORTED_KRX_CALENDAR_YEARS:
        return ResetSchedule(
            resets_on=None,
            exact=False,
            reason=f"KRX calendar year {day.year} is unsupported",
        )

    candidate = day + timedelta(days=1)
    uncertain_dates: list[date] = []
    while candidate.year in SUPPORTED_KRX_CALENDAR_YEARS:
        status = krx_day_status(candidate)
        if status.is_trading_day:
            if uncertain_dates:
                listed = ", ".join(value.isoformat() for value in uncertain_dates)
                return ResetSchedule(
                    resets_on=candidate,
                    exact=False,
                    reason=(
                        "next session is uncertain; latch held through "
                        f"{listed} until a definitely supported trading day"
                    ),
                    uncertain_dates=tuple(uncertain_dates),
                )
            return ResetSchedule(resets_on=candidate, exact=True)
        if status.state == DAY_UNCERTAIN:
            uncertain_dates.append(candidate)
        candidate += timedelta(days=1)

    reason = (
        f"next calendar year {candidate.year} is unsupported; "
        "latch reset date cannot be proven"
    )
    if uncertain_dates:
        listed = ", ".join(value.isoformat() for value in uncertain_dates)
        reason = f"{reason}; uncertain dates encountered: {listed}"
    return ResetSchedule(
        resets_on=None,
        exact=False,
        reason=reason,
        uncertain_dates=tuple(uncertain_dates),
    )


def next_trading_day(day: date) -> date | None:
    """The next conservative KRX reset date, or ``None`` if unsupported."""

    return next_trading_day_status(day).resets_on


def should_reset(latched_day: date, today: date) -> bool:
    """Has the latch's trading day actually elapsed?

    Keyed on reaching the **next KRX trading day**, not on the calendar date
    changing. Those differ across every weekend and holiday: a latch set on
    Friday must still be a latch when the pod restarts on Saturday, because
    Saturday is not a new trading day — it is the same one, closed. Resetting
    on "the date changed" would drop Friday's latch overnight and, just as
    bad, make ``/state`` report a clean breaker all weekend when the account
    had in fact tripped.

    A latched day in the future (clock skew) never resets, which is the
    conservative direction.
    """

    reset_day = next_trading_day(latched_day)
    return reset_day is not None and today >= reset_day


def _parse_trading_day(value: Any) -> date | None:
    """Parse a stored ``trading_day``; ``None`` when it is not a usable date."""

    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        return None


def _to_int(value: Any) -> int | None:
    """Parse a Kiwoom numeric string (``"+1200"``, ``"-3,400"``) to int."""

    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    text = str(value).strip().replace(",", "").replace("+", "")
    if not text or text == "-":
        return None
    try:
        return int(float(text))
    except (TypeError, ValueError):
        return None


def _to_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(",", "").replace("+", "")
    if not text or text == "-":
        return None
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Limits
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class DailyRiskLimits:
    """Thresholds for the new-entry breaker. ``0`` disables a limit."""

    # Today's loss as a percentage of total account assets. Expressed as a
    # positive magnitude: 3.0 means "stop opening new positions once the
    # account is down 3% on the day".
    max_daily_loss_pct: float = 0.0
    # Today's loss in KRW, positive magnitude.
    max_daily_loss_krw: int = 0
    # How many new positions may be opened in one trading day.
    max_daily_new_entries: int = 0

    # Operator's explicit acknowledgement that the daily-loss source has been
    # validated against a live account (see `loss_source_unverified` below).
    # **Default False, and it must stay that way.** Nothing in this codebase
    # can set it — only a human passing the CLI flag, having done the
    # validation themselves.
    loss_source_verified: bool = False

    @property
    def enabled(self) -> bool:
        return (
            self.max_daily_loss_pct > 0
            or self.max_daily_loss_krw > 0
            or self.max_daily_new_entries > 0
        )

    @property
    def has_loss_limit(self) -> bool:
        """True when a limit is expressed in terms of the broker's daily P&L."""

        return self.max_daily_loss_pct > 0 or self.max_daily_loss_krw > 0

    @property
    def needs_account_data(self) -> bool:
        """True when a limit depends on the account snapshot being readable.

        A pure ``max_daily_new_entries`` setup counts its own orders and does
        not need the broker's P&L, so it must not fail closed when that
        figure is missing.
        """

        return self.has_loss_limit

    @property
    def loss_source_unverified(self) -> bool:
        """A loss limit is armed but its data source is not trusted yet.

        ``tdy_lspft`` parses cleanly and looks like a number, but nobody has
        established *what that number counts* — realized-only or realized
        plus unrealized, gross or net of commission and tax. The spec does
        not say and this repository has never read the field from a live
        account. A syntactically valid reading is therefore not a
        semantically valid one, and "the value is below the threshold" is not
        evidence that the account is safe: if the figure excludes unrealized
        P&L, an account deep in the red on open positions reads as a flat day
        and the breaker waves every new entry through.

        So an armed loss limit is treated as *not yet enforceable*: new
        entries are blocked outright rather than judged against a number we
        cannot interpret. Blocking is the only reading that is safe under
        either interpretation.
        """

        return self.has_loss_limit and not self.loss_source_verified

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_daily_loss_pct": self.max_daily_loss_pct,
            "max_daily_loss_krw": self.max_daily_loss_krw,
            "max_daily_new_entries": self.max_daily_new_entries,
            "loss_source_verified": self.loss_source_verified,
        }


# ---------------------------------------------------------------------------
# Account adapter
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class AccountDailySnapshot:
    """Today's P&L as read out of a kt00004 account-evaluation record."""

    daily_pl_krw: int | None = None
    total_assets_krw: int | None = None
    # The broker's own 당일손익율. Carried for cross-checking on `/state`;
    # never used for a threshold decision — see `loss_pct`.
    broker_daily_pl_pct: float | None = None
    valid: bool = False
    reason: str | None = None

    @property
    def loss_pct(self) -> float | None:
        """Today's loss as a positive % of total account assets.

        Computed here rather than taken from the broker's ``tdy_lspft_rt``:
        that rate's denominator is 당일투자원금 (today's invested principal),
        which for a partially-deployed account is far smaller than the
        account itself, so the same "3%" would trip at wildly different real
        drawdowns depending on how much happened to be in the market. A
        denominator we compute from a documented field keeps the threshold
        meaning the thing an operator thinks it means.

        Returns ``None`` when it cannot be computed, and ``0.0`` when the day
        is flat or profitable (a gain is not a loss).
        """

        if self.daily_pl_krw is None or not self.total_assets_krw:
            return None
        if self.total_assets_krw <= 0:
            return None
        if self.daily_pl_krw >= 0:
            return 0.0
        return abs(self.daily_pl_krw) / self.total_assets_krw * 100

    @property
    def loss_krw(self) -> int | None:
        """Today's loss as a positive KRW magnitude (0 when not losing)."""

        if self.daily_pl_krw is None:
            return None
        return abs(self.daily_pl_krw) if self.daily_pl_krw < 0 else 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "daily_pl_krw": self.daily_pl_krw,
            "total_assets_krw": self.total_assets_krw,
            "broker_daily_pl_pct": self.broker_daily_pl_pct,
            "loss_pct": self.loss_pct,
            "valid": self.valid,
            "reason": self.reason,
        }


def read_account_daily_snapshot(portfolio: Any) -> AccountDailySnapshot:
    """Build a snapshot from the planner's ``portfolio`` block.

    Deliberately strict: an absent or unparseable daily P&L yields
    ``valid=False`` rather than a zero, because a silent zero reads as "flat
    day, keep trading" — the exact failure this breaker exists to prevent.
    """

    if not isinstance(portfolio, dict):
        return AccountDailySnapshot(
            valid=False, reason="portfolio 데이터 없음"
        )

    daily_pl = _to_int(portfolio.get("daily_pl_krw"))
    total_assets = _to_int(portfolio.get("estimated_assets"))
    broker_pct = _to_float(portfolio.get("daily_pl_pct_broker"))

    if daily_pl is None:
        return AccountDailySnapshot(
            daily_pl_krw=None,
            total_assets_krw=total_assets,
            broker_daily_pl_pct=broker_pct,
            valid=False,
            reason="당일손익(tdy_lspft) 값을 읽을 수 없음",
        )
    if not total_assets or total_assets <= 0:
        # KRW limits still work without it, so keep the P&L and let the
        # breaker decide: only a pct limit actually needs the denominator.
        return AccountDailySnapshot(
            daily_pl_krw=daily_pl,
            total_assets_krw=None,
            broker_daily_pl_pct=broker_pct,
            valid=False,
            reason="총자산(prsm_dpst_aset_amt) 값을 읽을 수 없음",
        )
    return AccountDailySnapshot(
        daily_pl_krw=daily_pl,
        total_assets_krw=total_assets,
        broker_daily_pl_pct=broker_pct,
        valid=True,
    )


# ---------------------------------------------------------------------------
# Breaker
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class EntryDecision:
    """Whether one new entry may proceed."""

    allowed: bool
    code: str | None = None
    reason: str | None = None


@dataclass(slots=True)
class BreakerState:
    """Everything that has to survive a same-day restart."""

    trading_day: str
    tripped: bool = False
    trip_code: str | None = None
    trip_reason: str | None = None
    limit_value: float | None = None
    observed_value: float | None = None
    tripped_at: str | None = None
    new_entries: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "trading_day": self.trading_day,
            "tripped": self.tripped,
            "trip_code": self.trip_code,
            "trip_reason": self.trip_reason,
            "limit_value": self.limit_value,
            "observed_value": self.observed_value,
            "tripped_at": self.tripped_at,
            "new_entries": self.new_entries,
        }

    @classmethod
    def restore(cls, payload: dict[str, Any], *, latched_day: date) -> "BreakerState":
        """Rebuild a still-current state, keeping its original trading day.

        ``latched_day`` stays as stored rather than being rewritten to today:
        over a weekend the latch belongs to Friday, and reporting it as
        Saturday's would both misstate ``/state`` and compute the wrong
        ``resets_on``.
        """

        return cls(
            trading_day=latched_day.isoformat(),
            tripped=bool(payload.get("tripped")),
            trip_code=payload.get("trip_code"),
            trip_reason=payload.get("trip_reason"),
            limit_value=payload.get("limit_value"),
            observed_value=payload.get("observed_value"),
            tripped_at=payload.get("tripped_at"),
            new_entries=int(payload.get("new_entries") or 0),
        )


class DailyEntryBreaker:
    """Latching, restart-durable gate on opening new positions.

    Never consulted by a sell, stop-loss, take-profit or cancel path.
    """

    def __init__(
        self,
        limits: DailyRiskLimits,
        *,
        state_path: Path | None = DEFAULT_STATE_PATH,
        now: datetime | None = None,
    ):
        self._limits = limits
        self._state_path = state_path
        # Set when the durable state cannot be trusted — an unreadable or
        # corrupt file, or a failed latch write. While set (and while a limit
        # is armed) new buys fail closed; exits are never affected.
        self._state_error: str | None = None
        day = current_trading_day(now)
        # ``None`` means the internal buy path has not observed a clock yet.
        # Production calls ``roll_day`` at the start of every tick. Keeping
        # the unobserved state distinct avoids pretending that construction
        # time itself was an audited calendar observation.
        self._calendar_status: KrxDayStatus | None = None
        self._calendar_observed_at: str | None = None
        if now is not None:
            self._observe_calendar(now)
        self._state = self._load(day)
        # Latest account read; None until the first `observe`.
        self._snapshot: AccountDailySnapshot | None = None

    # -- properties -----------------------------------------------------------

    @property
    def limits(self) -> DailyRiskLimits:
        return self._limits

    @property
    def enabled(self) -> bool:
        return self._limits.enabled

    @property
    def tripped(self) -> bool:
        return self._state.tripped

    @property
    def state(self) -> BreakerState:
        return self._state

    # -- persistence ----------------------------------------------------------

    def _fail_state(self, message: str) -> None:
        """Mark the durable state untrustworthy — new buys fail closed."""

        self._state_error = message
        if self._limits.enabled:
            log.error("daily risk state unusable — 신규 매수 차단: %s", message)
        else:
            log.warning("daily risk state unusable (breaker disabled): %s", message)

    def _load(self, day: date) -> BreakerState:
        iso = day.isoformat()
        if self._state_path is None:
            return BreakerState(trading_day=iso)
        try:
            raw = json.loads(self._state_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            # First run on this volume — normal, not an error.
            return BreakerState(trading_day=iso)
        except (OSError, ValueError) as exc:
            # We cannot tell whether this file was holding a latch, so we
            # must not assume it wasn't. Fail closed for new entries until a
            # successful write replaces it (which `roll_day` does on the next
            # trading day, by which point any latch would have expired anyway).
            self._fail_state(f"상태 파일을 읽을 수 없음: {exc}")
            return BreakerState(trading_day=iso)

        if not isinstance(raw, dict):
            self._fail_state("상태 파일 형식이 dict가 아님")
            return BreakerState(trading_day=iso)

        latched_day = _parse_trading_day(raw.get("trading_day"))
        if latched_day is None:
            # A state blob whose day we cannot read is a state we cannot age
            # out — same fail-closed treatment as an unreadable file.
            self._fail_state("상태 파일의 trading_day를 해석할 수 없음")
            return BreakerState(trading_day=iso)

        if should_reset(latched_day, day):
            log.info(
                "daily entry breaker state from %s has aged out (today %s)",
                latched_day.isoformat(),
                iso,
            )
            return BreakerState(trading_day=iso)

        state = BreakerState.restore(raw, latched_day=latched_day)
        if state.tripped:
            log.warning(
                "daily entry breaker restored as TRIPPED for %s (today %s): %s",
                state.trading_day,
                iso,
                state.trip_reason,
            )
        return state

    def _persist(self) -> None:
        """Write the latch through immediately.

        Not best-effort like the watcher's observability snapshot: if the
        process dies right after tripping, the latch has to still be there on
        restart. A write failure therefore fails new entries closed — an
        un-durable latch is a latch that a pod restart would silently undo.
        Exits are untouched.
        """

        if self._state_path is None:
            return
        if not self._limits.enabled:
            # Nothing to make durable: a disabled breaker never latches, and
            # writing a file per buy for a feature nobody turned on is noise.
            return
        try:
            self._state_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self._state_path.with_suffix(".tmp")
            tmp.write_text(
                json.dumps(self._state.to_dict(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            tmp.replace(self._state_path)  # atomic; never a half-written latch
        except OSError as exc:
            self._fail_state(f"상태 저장 실패: {exc}")
            return
        # A good write means we own a trustworthy file again.
        self._state_error = None

    # -- lifecycle ------------------------------------------------------------

    def _observe_calendar(self, now: datetime | None = None) -> KrxDayStatus:
        current = now or datetime.now(KST)
        if current.tzinfo is None:
            current = current.replace(tzinfo=KST)
        current = current.astimezone(KST)
        self._calendar_status = krx_day_status(current)
        self._calendar_observed_at = current.isoformat()
        return self._calendar_status

    def roll_day(self, now: datetime | None = None) -> bool:
        """Reset the latch once the **next KRX trading day** has been reached.

        Returns True when a reset happened. A weekend or holiday is not a new
        trading day, so a Friday latch survives Saturday and Sunday untouched.
        An unsupported year or uncertain special session also preserves the
        latch; only a later definitely supported trading day can reset it.
        """

        today = self._observe_calendar(now).day
        latched_day = _parse_trading_day(self._state.trading_day)
        if latched_day is None:
            # Should be unreachable — every constructor path writes an ISO
            # date — but a corrupt in-memory day must not wedge the roll.
            self._fail_state("메모리 상태의 trading_day가 손상됨")
            self._state = BreakerState(trading_day=today.isoformat())
            self._snapshot = None
            self._persist()
            return True
        if not should_reset(latched_day, today):
            return False
        log.info(
            "daily entry breaker reset for new trading day %s (was %s, tripped=%s)",
            today.isoformat(),
            self._state.trading_day,
            self._state.tripped,
        )
        self._state = BreakerState(trading_day=today.isoformat())
        self._snapshot = None
        self._persist()
        return True

    def observe(
        self,
        snapshot: AccountDailySnapshot,
        *,
        now: datetime | None = None,
    ) -> EntryDecision | None:
        """Feed a fresh account read in. Returns the trip if one just fired."""

        self._snapshot = snapshot
        if not self._limits.enabled or self._state.tripped:
            return None
        if (
            self._calendar_status is not None
            and not self._calendar_status.is_trading_day
        ):
            # Keep the account reading observable, but do not manufacture a
            # new "daily" latch on a known close or a date whose trading-day
            # semantics are not verified. The calendar gate already blocks
            # new entries while protective paths continue.
            return None

        if self._limits.loss_source_unverified:
            # Keep the reading on `/state` — that is the raw material an
            # operator needs to do the semantic validation — but do not act
            # on it. Latching "you lost 3%" off a number whose meaning is
            # unestablished would record a reason we cannot stand behind;
            # `check_new_entry` blocks entries for the honest reason instead.
            return None

        loss_krw = snapshot.loss_krw
        if (
            self._limits.max_daily_loss_krw > 0
            and loss_krw is not None
            and loss_krw >= self._limits.max_daily_loss_krw
        ):
            return self._trip(
                BLOCK_DAILY_LOSS_KRW,
                limit=float(self._limits.max_daily_loss_krw),
                observed=float(loss_krw),
                reason=(
                    f"당일 손실 {loss_krw:,}원 ≥ 한도 "
                    f"{self._limits.max_daily_loss_krw:,}원"
                ),
                now=now,
            )

        loss_pct = snapshot.loss_pct
        if (
            self._limits.max_daily_loss_pct > 0
            and loss_pct is not None
            and loss_pct >= self._limits.max_daily_loss_pct
        ):
            return self._trip(
                BLOCK_DAILY_LOSS_PCT,
                limit=self._limits.max_daily_loss_pct,
                observed=loss_pct,
                reason=(
                    f"당일 손실 {loss_pct:.2f}% ≥ 한도 "
                    f"{self._limits.max_daily_loss_pct:.2f}% "
                    f"(총자산 {snapshot.total_assets_krw:,}원 기준)"
                ),
                now=now,
            )
        return None

    def _trip(
        self,
        code: str,
        *,
        limit: float,
        observed: float,
        reason: str,
        now: datetime | None = None,
    ) -> EntryDecision:
        stamp = (now or datetime.now(KST)).isoformat()
        self._state.tripped = True
        self._state.trip_code = code
        self._state.trip_reason = reason
        self._state.limit_value = limit
        self._state.observed_value = observed
        self._state.tripped_at = stamp
        self._persist()
        log.warning("daily entry breaker TRIPPED (%s): %s", code, reason)
        return EntryDecision(allowed=False, code=code, reason=reason)

    # -- the gate -------------------------------------------------------------

    def check_new_entry(self) -> EntryDecision:
        """May a *new* position be opened right now?

        Only ever called from the buy path. Exits are not gated.
        """

        # Calendar confidence is an always-on entry gate, independent of the
        # optional daily-risk thresholds. The watcher keeps its protective
        # cycle alive during uncertainty, but no buy may interpret an
        # unsupported year or unverified special session as permission.
        if self._calendar_status is not None:
            if self._calendar_status.state == DAY_UNCERTAIN:
                return EntryDecision(
                    allowed=False,
                    code=BLOCK_CALENDAR_UNCERTAIN,
                    reason=(
                        f"KRX 캘린더 불확실 ({self._calendar_status.reason}) — "
                        "신규 매수 보류 (매도/취소는 허용; 보호매도·손절 포함)"
                    ),
                )
            if self._calendar_status.state == DAY_CLOSED:
                return EntryDecision(
                    allowed=False,
                    code=BLOCK_CALENDAR_CLOSED,
                    reason=(
                        f"KRX 비거래일 ({self._calendar_status.reason}) — "
                        "신규 매수 보류 (매도/취소는 허용; 보호매도·손절 포함)"
                    ),
                )

        if not self._limits.enabled:
            return EntryDecision(allowed=True)

        if self._state.tripped:
            return EntryDecision(
                allowed=False,
                code=self._state.trip_code,
                reason=(
                    f"일일 서킷브레이커 발동 중 — {self._state.trip_reason} "
                    f"(발동 {self._state.tripped_at})"
                ),
            )

        # Durable state we cannot trust. We may be sitting on a latch we
        # failed to read, or holding one we failed to write; either way a
        # restart could silently resume buying. Block entries, never exits.
        if self._state_error is not None:
            return EntryDecision(
                allowed=False,
                code=BLOCK_STATE_UNAVAILABLE,
                reason=(
                    f"서킷브레이커 상태 신뢰 불가 ({self._state_error}) — "
                    "신규 매수 보류 (매도/취소는 허용)"
                ),
            )

        if (
            self._limits.max_daily_new_entries > 0
            and self._state.new_entries >= self._limits.max_daily_new_entries
        ):
            # Latch it so the reason is durable and identical on restart.
            return self._trip(
                BLOCK_MAX_NEW_ENTRIES,
                limit=float(self._limits.max_daily_new_entries),
                observed=float(self._state.new_entries),
                reason=(
                    f"당일 신규 진입 {self._state.new_entries}건 ≥ 한도 "
                    f"{self._limits.max_daily_new_entries}건"
                ),
            )

        # An armed loss limit whose data source has never been validated
        # against a live account. Checked AFTER the count limit so a mixed
        # setup still latches its entry budget normally, and before the
        # account-data checks because "we cannot interpret this number" is
        # the more fundamental problem than "this number is missing".
        #
        # Note this fires even when the snapshot parses cleanly and sits well
        # below the threshold — that is the entire point. A below-threshold
        # reading from a source that might exclude unrealized P&L is not
        # evidence of a safe account.
        if self._limits.loss_source_unverified:
            return EntryDecision(
                allowed=False,
                code=BLOCK_LOSS_SOURCE_UNVERIFIED,
                reason=(
                    "일일 손실 한도가 설정됐으나 손익 데이터 소스(tdy_lspft)가 "
                    "실계좌 검증되지 않음 — 신규 매수 보류 (매도/취소는 허용). "
                    "검증 후 --acknowledge-daily-loss-source-verified 로 활성화"
                ),
            )

        # Fail closed when a loss limit is armed but we cannot see the account.
        if self._limits.needs_account_data:
            if self._snapshot is None:
                return EntryDecision(
                    allowed=False,
                    code=BLOCK_ACCOUNT_DATA,
                    reason="계좌 손익 스냅샷 미수신 — 신규 매수 보류 (매도/취소는 허용)",
                )
            if not self._snapshot.valid:
                needs_pct = self._limits.max_daily_loss_pct > 0
                needs_krw = self._limits.max_daily_loss_krw > 0
                # A missing denominator only blocks the pct limit; if a KRW
                # limit is armed and the P&L itself parsed, we can still judge.
                krw_usable = needs_krw and self._snapshot.loss_krw is not None
                if needs_pct or not krw_usable:
                    return EntryDecision(
                        allowed=False,
                        code=BLOCK_ACCOUNT_DATA,
                        reason=(
                            f"계좌 손익 데이터 불량 ({self._snapshot.reason}) — "
                            "신규 매수 보류 (매도/취소는 허용)"
                        ),
                    )

        return EntryDecision(allowed=True)

    def record_new_entry(self, *, now: datetime | None = None) -> int:
        """Reserve an entry durably before submission; uncertainty keeps the reservation."""

        self._state.new_entries += 1
        self._persist()
        return self._state.new_entries

    def release_new_entry(self, *, trading_day: str) -> None:
        """Release a reservation only after a definitive failure on the same day."""

        if self._state.trading_day != trading_day:
            return
        self._state.new_entries = max(self._state.new_entries - 1, 0)
        self._persist()

    # -- observability --------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Shape published on ``/state`` and in the persisted watcher state."""

        payload: dict[str, Any] = {
            "enabled": self._limits.enabled,
            "limits": self._limits.to_dict(),
            **self._state.to_dict(),
            "state_error": self._state_error,
            # Verification state of the daily-loss data source. `unverified`
            # means the KRW/PCT limits are armed but NOT enforceable, and new
            # entries are being blocked outright because of it.
            "loss_source_status": (
                "n/a"
                if not self._limits.has_loss_limit
                else ("verified" if self._limits.loss_source_verified else "unverified")
            ),
            "loss_limits_enforced": (
                self._limits.has_loss_limit and self._limits.loss_source_verified
            ),
            "account": self._snapshot.to_dict() if self._snapshot else None,
            "calendar": (
                {
                    **self._calendar_status.to_dict(),
                    "observed_at": self._calendar_observed_at,
                    "entry_gate_active": self._calendar_status.state
                    in {DAY_CLOSED, DAY_UNCERTAIN},
                }
                if self._calendar_status is not None
                else {
                    "state": "unobserved",
                    "supported": None,
                    "reason": "calendar clock not observed yet",
                    "observed_at": None,
                    "entry_gate_active": False,
                }
            ),
        }
        latched_day = _parse_trading_day(self._state.trading_day)
        if self._state.tripped and latched_day is not None:
            # Reported even on a weekend, when `trading_day` is still the
            # (closed) day the latch belongs to rather than today.
            schedule = next_trading_day_status(latched_day)
            payload["resets_on"] = (
                schedule.resets_on.isoformat() if schedule.resets_on else None
            )
            payload["reset_schedule"] = schedule.to_dict()
        return payload


__all__ = [
    "BLOCK_ACCOUNT_DATA",
    "BLOCK_CALENDAR_CLOSED",
    "BLOCK_CALENDAR_UNCERTAIN",
    "BLOCK_DAILY_LOSS_KRW",
    "BLOCK_DAILY_LOSS_PCT",
    "BLOCK_LOSS_SOURCE_UNVERIFIED",
    "BLOCK_MAX_NEW_ENTRIES",
    "BLOCK_STATE_UNAVAILABLE",
    "DEFAULT_STATE_PATH",
    "LATCHING_BLOCKS",
    "AccountDailySnapshot",
    "BreakerState",
    "DailyEntryBreaker",
    "DailyRiskLimits",
    "EntryDecision",
    "ResetSchedule",
    "current_trading_day",
    "next_trading_day",
    "next_trading_day_status",
    "read_account_daily_snapshot",
    "should_reset",
]
