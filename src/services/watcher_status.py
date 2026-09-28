"""In-memory status registry for the intraday watcher.

The watcher publishes its lifecycle (cycle counter, regime label,
in-flight Tier-2 dispatches, recent triggers, last error) into a
``WatcherStatusRegistry`` instance. The status HTTP server reads from
the same instance and serves snapshots to the dashboard.

Why in-memory + thread-safe rather than a file:

* The HTTP server runs in the same event loop as the watcher, so a
  process-local registry avoids file I/O on every event.
* All mutation happens from the asyncio event loop; the lock is for
  the rare case the HTTP server (also async) overlaps with a tick.
* The watcher loop already persists a coarse snapshot to
  ``output/watcher_state.json`` for K8s observability — this registry
  layers on richer in-memory data that survives only as long as the
  process.
"""

from __future__ import annotations

import threading
from collections import deque
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Iterable
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")

# Hard cap on recent-trigger history kept in memory. Triggers fire at
# most a few times per minute even in heavy market action, so 200 covers
# multiple sessions without unbounded growth.
RECENT_TRIGGER_LIMIT = 200


def _now_iso() -> str:
    return datetime.now(KST).isoformat()


@dataclass(slots=True)
class TriggerLogEntry:
    """One trigger fire recorded for the dashboard activity feed."""

    detected_at: str
    trigger_type: str
    tier: int
    scope: str  # "stock" | "global"
    target_role: str
    stock_code: str | None
    stock_name: str | None
    reason: str
    # Lifecycle stamps populated as the watcher processes the trigger.
    dispatched: bool = False
    completed_at: str | None = None
    # Order-apply states from `order_result` — "informational", "skipped",
    # "submitted", "unknown", "failed", "filled" — plus watcher-only outcomes
    # "dry_run", "stale", "timeout", "dispatch_failed", "cancelled". Note
    # "submitted" means the broker accepted the request, NOT that it filled;
    # "filled" is reserved for executions confirmed against the account, and
    # "cancelled" is a clean shutdown, not a fault.
    outcome: str | None = None
    action: str | None = None  # ACTION tag for tier-2 outcomes
    detail: str | None = None  # short human-readable note

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class InFlightSnapshot:
    """Currently-pending Tier-2 dispatch awaiting agent response."""

    scope_key: str
    trigger_type: str
    target_role: str
    stock_code: str | None
    stock_name: str | None
    started_at: str
    issue_id: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class WatcherStatusRegistry:
    """Thread-safe registry of watcher runtime state.

    The watcher updates this from its own asyncio task; the status HTTP
    server reads via ``snapshot()``. All public methods take the lock
    so concurrent reads/writes stay coherent (especially the recent
    triggers deque).
    """

    def __init__(self, *, recent_limit: int = RECENT_TRIGGER_LIMIT):
        self._lock = threading.Lock()
        self._started_at: str | None = None
        self._stopped_at: str | None = None
        self._cycle_count: int = 0
        self._last_tick_at: str | None = None
        self._last_error: str | None = None
        self._regime: dict[str, Any] | None = None
        self._holding_count: int = 0
        self._open_order_count: int = 0
        self._candidate_count: int = 0
        self._api_failure_count: int = 0
        self._mode: str = "unknown"
        self._execute_orders: bool = False
        self._poll_interval_seconds: int = 0
        # The watcher's own effective config, reported at startup. Consumers must
        # render this instead of reconstructing thresholds from code defaults —
        # the live deployment overrides most of them via CLI args, and a dashboard
        # built from defaults printed confidently wrong numbers for months.
        self._config: dict[str, Any] = {}
        self._in_flight: dict[str, InFlightSnapshot] = {}
        self._recent: deque[TriggerLogEntry] = deque(maxlen=recent_limit)
        self._cooldowns: dict[str, str] = {}  # cooldown_key -> expires_at iso
        # category -> {"count", "last_at", "last_detail"}. Per-stage failure
        # attribution so an account/market/multica outage after a successful
        # planner call is visible instead of silently degrading the tick.
        self._failures: dict[str, dict[str, Any]] = {}
        # Latest new-entry circuit breaker snapshot; None until the first tick.
        self._daily_entry_breaker: dict[str, Any] | None = None
        # Today's tally of qualifying candidates met by a full portfolio.
        self._candidate_slots: dict[str, Any] = {
            "trading_day": None,
            "qualified_ticks": 0,
            "starved_ticks": 0,
            "best_starved_score": None,
            "best_starved_name": None,
        }
        # The last tick's candidate board — see ``summarize_candidates``.
        self._candidates: dict[str, Any] | None = None
        # What the previous process last persisted, loaded once at startup.
        # Everything above is in-memory and empty until the first tick, which
        # outside market hours never comes: after a holiday-morning rollout the
        # dashboard showed cycle 0 and a dash for every field, indistinguishable
        # from a dead watcher (2026-09-24). The persisted snapshot survives on
        # the PVC, so the last real session can still be shown — dated.
        self._last_session: dict[str, Any] | None = None

    # -- lifecycle ------------------------------------------------------------

    def mark_started(
        self,
        *,
        mode: str,
        execute_orders: bool,
        poll_interval_seconds: int,
        config: dict[str, Any] | None = None,
    ) -> None:
        with self._lock:
            self._started_at = _now_iso()
            self._stopped_at = None
            self._mode = mode
            self._execute_orders = execute_orders
            self._poll_interval_seconds = poll_interval_seconds
            self._config = dict(config or {})

    def mark_stopped(self) -> None:
        with self._lock:
            self._stopped_at = _now_iso()

    def mark_tick(
        self,
        *,
        regime: dict[str, Any] | None,
        holding_count: int,
        open_order_count: int,
        candidate_count: int,
        api_failure_count: int,
    ) -> None:
        with self._lock:
            self._cycle_count += 1
            self._last_tick_at = _now_iso()
            self._regime = regime
            self._holding_count = holding_count
            self._open_order_count = open_order_count
            self._candidate_count = candidate_count
            self._api_failure_count = api_failure_count
            self._last_error = None  # clear on successful tick

    def mark_tick_error(self, message: str) -> None:
        with self._lock:
            self._last_error = message

    # -- triggers -------------------------------------------------------------

    def record_trigger(
        self,
        *,
        trigger_type: str,
        tier: int,
        scope: str,
        target_role: str,
        stock_code: str | None,
        stock_name: str | None,
        reason: str,
        detected_at: datetime | None = None,
    ) -> TriggerLogEntry:
        entry = TriggerLogEntry(
            detected_at=(detected_at or datetime.now(KST)).isoformat(),
            trigger_type=trigger_type,
            tier=tier,
            scope=scope,
            target_role=target_role,
            stock_code=stock_code,
            stock_name=stock_name,
            reason=reason,
        )
        with self._lock:
            self._recent.appendleft(entry)
        return entry

    def mark_dispatched(self, entry: TriggerLogEntry, *, issue_id: str) -> None:
        with self._lock:
            entry.dispatched = True
            entry.detail = f"issue={issue_id}"

    def mark_outcome(
        self,
        entry: TriggerLogEntry,
        *,
        outcome: str,
        action: str | None = None,
        detail: str | None = None,
    ) -> None:
        with self._lock:
            entry.completed_at = _now_iso()
            entry.outcome = outcome
            if action is not None:
                entry.action = action
            if detail is not None:
                entry.detail = detail

    # -- in-flight ------------------------------------------------------------

    def add_in_flight(
        self,
        *,
        scope_key: str,
        trigger_type: str,
        target_role: str,
        stock_code: str | None,
        stock_name: str | None,
        started_at: datetime,
        issue_id: str,
    ) -> None:
        snapshot = InFlightSnapshot(
            scope_key=scope_key,
            trigger_type=trigger_type,
            target_role=target_role,
            stock_code=stock_code,
            stock_name=stock_name,
            started_at=started_at.isoformat(),
            issue_id=issue_id,
        )
        with self._lock:
            self._in_flight[scope_key] = snapshot

    def remove_in_flight(self, scope_key: str) -> None:
        with self._lock:
            self._in_flight.pop(scope_key, None)

    # -- cooldowns ------------------------------------------------------------

    def set_cooldowns(self, cooldowns: dict[str, datetime]) -> None:
        with self._lock:
            self._cooldowns = {k: v.isoformat() for k, v in cooldowns.items()}

    # -- failures -------------------------------------------------------------

    def record_failure(self, *, category: str, detail: str) -> None:
        """Count an operational failure against a pipeline stage.

        ``detail`` must already be sanitized — this registry is served over
        HTTP by the status server.
        """

        with self._lock:
            bucket = self._failures.setdefault(
                category, {"count": 0, "last_at": None, "last_detail": None}
            )
            bucket["count"] += 1
            bucket["last_at"] = _now_iso()
            bucket["last_detail"] = detail

    def failure_summary(self) -> dict[str, dict[str, Any]]:
        """Snapshot of per-category failure counts (empty when all healthy)."""

        with self._lock:
            return {k: dict(v) for k, v in self._failures.items()}

    # -- daily entry breaker --------------------------------------------------

    def record_candidate_slots(
        self,
        *,
        trading_day: str,
        available_slots: int,
        top_score: float | None = None,
        top_name: str | None = None,
    ) -> None:
        """Count ticks where a qualifying candidate met a full portfolio.

        `detect_tier2_new_candidates` returns `[]` when no slot is free, so
        the screener is never asked and the tick leaves no other trace. That
        silence hid the shape of a whole month: 78.7% of 2026-08-19..09-18
        snapshots held a gate-passing candidate while only 5 entries were
        made in 23 trading days, because a position was open 83% of the
        time. Counting it here puts the number next to everything else the
        digest already reads, instead of only in the journal on the PVC.

        ``top_score``/``top_name`` describe the best qualifying candidate on
        this tick, or None when nothing qualified. The best one seen while
        starved is kept for the day, because the tick count alone cannot
        separate "held a position through a quiet tape" from "let a better
        name go by": on 2026-09-21 the starvation rate was 99.2% and the
        wrap could not rule on a missed rotation, while the day's final
        snapshot had HMM at score 9 — over the rotation threshold — blocked
        with zero slots.

        Resets on a new trading day — the digest asks about today.
        """

        with self._lock:
            if self._candidate_slots.get("trading_day") != trading_day:
                self._candidate_slots = {
                    "trading_day": trading_day,
                    "qualified_ticks": 0,
                    "starved_ticks": 0,
                    "best_starved_score": None,
                    "best_starved_name": None,
                }
            if top_score is None:
                return
            self._candidate_slots["qualified_ticks"] += 1
            if available_slots > 0:
                return
            self._candidate_slots["starved_ticks"] += 1
            best = self._candidate_slots.get("best_starved_score")
            if best is None or top_score > best:
                self._candidate_slots["best_starved_score"] = top_score
                self._candidate_slots["best_starved_name"] = top_name

    def set_daily_entry_breaker(self, payload: dict[str, Any]) -> None:
        """Publish the new-entry circuit breaker's state (see daily_risk.py)."""

        with self._lock:
            self._daily_entry_breaker = dict(payload)

    def set_candidates(self, board: dict[str, Any] | None) -> None:
        """Publish the last tick's candidate board (``summarize_candidates``)."""

        with self._lock:
            self._candidates = dict(board) if board is not None else None

    def set_last_session(self, payload: dict[str, Any] | None) -> None:
        """Publish the previous process's persisted snapshot, as read."""

        with self._lock:
            self._last_session = dict(payload) if payload else None

    # -- snapshot -------------------------------------------------------------

    def snapshot(self) -> dict[str, Any]:
        """Return a JSON-serializable snapshot of all current state."""

        with self._lock:
            return {
                "now": _now_iso(),
                "started_at": self._started_at,
                "stopped_at": self._stopped_at,
                "mode": self._mode,
                "execute_orders": self._execute_orders,
                "poll_interval_seconds": self._poll_interval_seconds,
                "config": dict(self._config),
                "cycle_count": self._cycle_count,
                "last_tick_at": self._last_tick_at,
                "last_error": self._last_error,
                "regime": self._regime,
                "portfolio": {
                    "holding_count": self._holding_count,
                    "open_order_count": self._open_order_count,
                    "candidate_count": self._candidate_count,
                },
                "api_failure_count": self._api_failure_count,
                "failures": {k: dict(v) for k, v in self._failures.items()},
                "daily_entry_breaker": (
                    dict(self._daily_entry_breaker)
                    if self._daily_entry_breaker is not None
                    else None
                ),
                "candidate_slots": dict(self._candidate_slots),
                "candidates": (
                    dict(self._candidates) if self._candidates is not None else None
                ),
                "last_session": (
                    dict(self._last_session) if self._last_session else None
                ),
                "in_flight": [s.to_dict() for s in self._in_flight.values()],
                "cooldowns": dict(self._cooldowns),
            }

    def recent(self, limit: int | None = None) -> list[dict[str, Any]]:
        """Return up to ``limit`` most recent trigger entries (newest first)."""

        with self._lock:
            iterable: Iterable[TriggerLogEntry] = list(self._recent)
        if limit is not None:
            iterable = list(iterable)[:limit]
        return [e.to_dict() for e in iterable]


# Rows kept on the board. The roster is 30 names; the dashboard needs the
# ones that decide something — the qualifiers and the nearest misses.
CANDIDATE_BOARD_LIMIT = 8


def summarize_candidates(
    rows: Iterable[dict[str, Any]],
    *,
    min_score: float,
    available_slots: int,
    at: str | None,
    in_band: Any = None,
    limit: int = CANDIDATE_BOARD_LIMIT,
) -> dict[str, Any]:
    """Condense one tick's candidate rows into what a person can read.

    The planner returns every scanned name with a score and a list of veto
    reasons. The question an observer asks is narrower — how many got how
    far, and what stopped the best of them — so the board is a funnel
    (scanned → in the MA band → eligible → at the gate) plus the top rows
    with their *first* blocking reason. The first reason is the one that
    decided; the rest are noise on a phone screen.

    ``available_slots`` rides along because at zero nothing below the gate
    matters: the screener is never called (`detect_tier2_new_candidates`
    returns before building an event). Without it a board full of 9s reads
    as the system ignoring them.

    ``in_band`` is the journal's band predicate, passed in rather than
    re-derived so the dashboard and the journal cannot disagree about which
    names were in the dip band.
    """

    clean = [r for r in rows if isinstance(r, dict)]

    def _qualified(row: dict[str, Any]) -> bool:
        return bool(row.get("eligible")) and (row.get("score") or 0) >= min_score

    ranked = sorted(
        clean,
        key=lambda r: (_qualified(r), r.get("score") or 0),
        reverse=True,
    )
    top = []
    for row in ranked[:limit]:
        reasons = [x for x in (row.get("reasons") or []) if x]
        top.append(
            {
                "stock_code": row.get("stock_code"),
                "stock_name": row.get("stock_name"),
                "score": row.get("score"),
                "eligible": bool(row.get("eligible")),
                "qualified": _qualified(row),
                "ma_dip_pct": row.get("ma_dip_pct"),
                "day_change_pct": row.get("day_change_pct"),
                "blocked_by": reasons[0] if reasons else None,
            }
        )
    return {
        "at": at,
        "min_score": min_score,
        "available_slots": available_slots,
        "scanned": len(clean),
        "in_band": (
            sum(1 for r in clean if in_band(r)) if callable(in_band) else None
        ),
        "eligible": sum(1 for r in clean if r.get("eligible")),
        "qualified": sum(1 for r in clean if _qualified(r)),
        "top": top,
    }


__all__ = [
    "CANDIDATE_BOARD_LIMIT",
    "summarize_candidates",
    "InFlightSnapshot",
    "RECENT_TRIGGER_LIMIT",
    "TriggerLogEntry",
    "WatcherStatusRegistry",
]
