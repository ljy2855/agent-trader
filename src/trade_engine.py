"""Background trading engine for continuous strategy execution."""

from __future__ import annotations

import asyncio
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from .config import Settings
from .services.kiwoom_client import KiwoomClient
from .services.krx_calendar import (
    SESSION_CLOSED,
    SESSION_UNCERTAIN,
    is_krx_regular_session_open,
    krx_regular_session_status,
)
from .services.strategy import plan_intraday_momentum_strategy

KST = ZoneInfo("Asia/Seoul")
DEFAULT_STATE_PATH = Path(__file__).resolve().parents[1] / "output" / "background_trade_engine.json"


def _now_iso() -> str:
    """Return the current KST timestamp as ISO-8601 text."""

    return datetime.now(KST).isoformat()


def _normalize_watchlist(watchlist: list[str] | None) -> list[str]:
    """Normalize watchlist values into unique 6-digit stock codes."""

    normalized: list[str] = []
    for raw_code in watchlist or []:
        code = str(raw_code).strip()
        if not code:
            continue
        if len(code) != 6 or not code.isdigit():
            raise ValueError(f"Invalid stock code: {code}")
        if code not in normalized:
            normalized.append(code)
    return normalized


def _is_market_open(now: datetime | None = None) -> bool:
    """Return True when the KRX regular session is open."""

    return is_krx_regular_session_open(now)


CALENDAR_WAIT = "wait"
CALENDAR_FULL = "full"
CALENDAR_PROTECTIVE_ONLY = "protective_only"


def _calendar_cycle_mode(now: datetime | None = None) -> str:
    """Whether a cycle may include buys, exits only, or no market work."""

    state = krx_regular_session_status(now).state
    if state == SESSION_CLOSED:
        return CALENDAR_WAIT
    if state == SESSION_UNCERTAIN:
        return CALENDAR_PROTECTIVE_ONLY
    return CALENDAR_FULL


@dataclass(slots=True)
class TradeEngineConfig:
    """Mutable strategy configuration used by the background engine."""

    watchlist: list[str] = field(default_factory=list)
    leaders_limit: int = 10
    candidate_limit: int = 5
    max_positions: int = 3
    max_new_positions: int = 1
    position_budget_pct: int = 10
    cycle_interval_seconds: int = 60
    off_hours_interval_seconds: int = 300
    execute_orders: bool = False

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> "TradeEngineConfig":
        """Build config from persisted JSON data."""

        data = payload or {}
        return cls(
            watchlist=_normalize_watchlist(data.get("watchlist")),
            leaders_limit=int(data.get("leaders_limit", 10)),
            candidate_limit=int(data.get("candidate_limit", 5)),
            max_positions=int(data.get("max_positions", 3)),
            max_new_positions=int(data.get("max_new_positions", 1)),
            position_budget_pct=int(data.get("position_budget_pct", 10)),
            cycle_interval_seconds=max(int(data.get("cycle_interval_seconds", 60)), 5),
            off_hours_interval_seconds=max(int(data.get("off_hours_interval_seconds", 300)), 10),
            execute_orders=bool(data.get("execute_orders", False)),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize config for status payloads and persistence."""

        return asdict(self)


@dataclass(slots=True)
class TradeEngineRuntime:
    """Live runtime state for the background engine."""

    running: bool = False
    paused: bool = False
    current_phase: str = "stopped"
    cycle_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    last_started_at: str | None = None
    last_stopped_at: str | None = None
    last_cycle_started_at: str | None = None
    last_cycle_completed_at: str | None = None
    last_error: str | None = None
    last_message: str | None = None
    last_result_summary: dict[str, Any] = field(default_factory=dict)
    calendar: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize runtime state."""

        return asdict(self)


def _summarize_cycle_result(result: dict[str, Any]) -> dict[str, Any]:
    """Extract a compact summary from the strategy result."""

    executed_orders = result.get("executed_orders", [])
    successful_orders = 0
    failed_orders = 0
    if isinstance(executed_orders, list):
        for item in executed_orders:
            order_result = item.get("order_result", {}) if isinstance(item, dict) else {}
            if order_result.get("success", False):
                successful_orders += 1
            else:
                failed_orders += 1

    return {
        "success": result.get("success", False),
        "message": result.get("message"),
        "regime": result.get("regime", {}).get("regime"),
        "planned_action_count": len(result.get("planned_actions", [])),
        "executed_order_count": len(executed_orders) if isinstance(executed_orders, list) else 0,
        "successful_order_count": successful_orders,
        "failed_order_count": failed_orders,
        "holding_count": result.get("portfolio", {}).get("holding_count"),
        "open_order_count": result.get("portfolio", {}).get("open_order_count"),
    }


class BackgroundTradeEngine:
    """Continuous strategy runner controlled by the MCP server."""

    def __init__(self, settings: Settings, *, state_path: Path = DEFAULT_STATE_PATH):
        self._settings = settings
        self._state_path = state_path
        self._config = self._load_config()
        self._runtime = TradeEngineRuntime()
        self._task: asyncio.Task[None] | None = None
        self._stop_event = asyncio.Event()
        self._lock = asyncio.Lock()
        self._live_execution_confirmed = False

    def _load_config(self) -> TradeEngineConfig:
        """Load persisted config or fall back to defaults."""

        if not self._state_path.exists():
            return TradeEngineConfig()
        try:
            payload = json.loads(self._state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return TradeEngineConfig()
        config_payload = payload.get("config") if isinstance(payload, dict) else None
        try:
            return TradeEngineConfig.from_dict(config_payload)
        except (TypeError, ValueError):
            return TradeEngineConfig()

    def _persist_state(self) -> None:
        """Persist config plus the latest runtime snapshot to disk."""

        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "config": self._config.to_dict(),
            "runtime": self._runtime.to_dict(),
            "updated_at": _now_iso(),
        }
        self._state_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _reload_config_from_disk(self) -> None:
        """Refresh config from disk so external control writers are picked up."""

        self._config = self._load_config()

    async def _sleep_with_stop(self, seconds: int) -> None:
        """Sleep in short slices so stop/pause/config changes are responsive."""

        remaining = max(seconds, 1)
        while remaining > 0 and not self._stop_event.is_set():
            step = min(remaining, 5)
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=step)
                return
            except TimeoutError:
                remaining -= step

    def status(self) -> dict[str, Any]:
        """Return a structured engine status payload."""

        return {
            "success": True,
            "message": self._runtime.last_message or "Background trade engine status",
            "environment": "mock" if self._settings.use_mock else "live",
            "state_path": str(self._state_path),
            "config": self._config.to_dict(),
            "runtime": self._runtime.to_dict(),
        }

    async def update_config(self, **updates: Any) -> dict[str, Any]:
        """Update config values while preserving unspecified fields."""

        async with self._lock:
            if (
                updates.get("execute_orders")
                and not self._settings.use_mock
                and not self._settings.allow_direct_live_orders
            ):
                return {"success": False, "message": "Direct live background orders are disabled; use the watcher"}
            for key, value in updates.items():
                if value is None:
                    continue
                if key == "watchlist":
                    self._config.watchlist = _normalize_watchlist(value)
                    continue
                if key in {"leaders_limit", "candidate_limit", "max_positions", "max_new_positions", "position_budget_pct"}:
                    setattr(self._config, key, int(value))
                    continue
                if key == "cycle_interval_seconds":
                    self._config.cycle_interval_seconds = max(int(value), 5)
                    continue
                if key == "off_hours_interval_seconds":
                    self._config.off_hours_interval_seconds = max(int(value), 10)
                    continue
                if key == "execute_orders":
                    self._config.execute_orders = bool(value)
            self._runtime.last_message = "Background trade engine config updated"
            self._persist_state()
            return self.status()

    async def start(
        self,
        *,
        execute_orders: bool | None = None,
        confirm_live_execution: bool = False,
    ) -> dict[str, Any]:
        """Start the background engine if it is not already running."""

        async with self._lock:
            requested_execution = self._config.execute_orders if execute_orders is None else bool(execute_orders)
            if requested_execution and not self._settings.use_mock and not self._settings.allow_direct_live_orders:
                return {"success": False, "message": "Direct live background orders are disabled; use the watcher"}
            if requested_execution and not self._settings.use_mock and not confirm_live_execution:
                return {
                    "success": False,
                    "message": "Live background trading requires explicit confirmation",
                    "config": self._config.to_dict(),
                    "runtime": self._runtime.to_dict(),
                }
            self._config.execute_orders = requested_execution
            self._live_execution_confirmed = confirm_live_execution
            if self._task and not self._task.done():
                self._runtime.paused = False
                self._runtime.last_message = "Background trade engine is already running"
                self._persist_state()
                return self.status()

            self._stop_event = asyncio.Event()
            self._runtime.running = True
            self._runtime.paused = False
            self._runtime.current_phase = "starting"
            self._runtime.last_started_at = _now_iso()
            self._runtime.last_stopped_at = None
            self._runtime.last_error = None
            self._runtime.last_message = "Background trade engine started"
            self._task = asyncio.create_task(self._run_loop(), name="background-trade-engine")
            self._persist_state()
            return self.status()

    async def pause(self) -> dict[str, Any]:
        """Pause execution without destroying the engine task."""

        async with self._lock:
            if not self._task or self._task.done():
                return {
                    "success": False,
                    "message": "Background trade engine is not running",
                    "config": self._config.to_dict(),
                    "runtime": self._runtime.to_dict(),
                }
            self._runtime.paused = True
            self._runtime.current_phase = "paused"
            self._runtime.last_message = "Background trade engine paused"
            self._persist_state()
            return self.status()

    async def resume(self) -> dict[str, Any]:
        """Resume a paused engine."""

        async with self._lock:
            if not self._task or self._task.done():
                return {
                    "success": False,
                    "message": "Background trade engine is not running",
                    "config": self._config.to_dict(),
                    "runtime": self._runtime.to_dict(),
                }
            self._runtime.paused = False
            self._runtime.current_phase = "idle"
            self._runtime.last_message = "Background trade engine resumed"
            self._persist_state()
            return self.status()

    async def stop(self) -> dict[str, Any]:
        """Stop the background engine and wait for the task to exit."""

        async with self._lock:
            task = self._task
            if not task or task.done():
                self._runtime.running = False
                self._runtime.current_phase = "stopped"
                self._runtime.last_message = "Background trade engine is already stopped"
                self._persist_state()
                return self.status()
            self._runtime.last_message = "Stopping background trade engine"
            self._runtime.current_phase = "stopping"
            self._stop_event.set()

        await task

        async with self._lock:
            self._task = None
            self._runtime.running = False
            self._runtime.paused = False
            self._runtime.current_phase = "stopped"
            self._runtime.last_stopped_at = _now_iso()
            self._runtime.last_message = "Background trade engine stopped"
            self._persist_state()
            return self.status()

    async def close(self) -> None:
        """Shutdown helper for server teardown."""

        await self.stop()

    async def _run_loop(self) -> None:
        """Continuously evaluate and optionally execute the configured strategy."""

        client = KiwoomClient(self._settings)
        try:
            while not self._stop_event.is_set():
                self._reload_config_from_disk()
                config = TradeEngineConfig.from_dict(self._config.to_dict())

                if self._runtime.paused:
                    self._runtime.current_phase = "paused"
                    self._persist_state()
                    await self._sleep_with_stop(5)
                    continue

                session = krx_regular_session_status()
                calendar_mode = _calendar_cycle_mode(session.observed_at)
                self._runtime.calendar = session.to_dict()
                if calendar_mode == CALENDAR_WAIT:
                    self._runtime.current_phase = "waiting_market_open"
                    self._runtime.last_message = "Market is closed; waiting for next session"
                    self._persist_state()
                    await self._sleep_with_stop(config.off_hours_interval_seconds)
                    continue

                protective_only = calendar_mode == CALENDAR_PROTECTIVE_ONLY
                self._runtime.current_phase = (
                    "running_protective_only_calendar_uncertain"
                    if protective_only
                    else "running_cycle"
                )
                self._runtime.last_cycle_started_at = _now_iso()
                self._runtime.last_error = None
                if protective_only:
                    self._runtime.last_message = (
                        "Calendar uncertain; new buys blocked, protective sells allowed"
                    )
                self._persist_state()

                try:
                    result = await plan_intraday_momentum_strategy(
                        client,
                        self._settings,
                        watchlist=config.watchlist or None,
                        leaders_limit=config.leaders_limit,
                        candidate_limit=config.candidate_limit,
                        max_positions=config.max_positions,
                        max_new_positions=(
                            0 if protective_only else config.max_new_positions
                        ),
                        position_budget_pct=config.position_budget_pct,
                        execute_orders=config.execute_orders and (
                            self._settings.use_mock or self._settings.allow_direct_live_orders
                        ),
                        confirm_mock_orders=config.execute_orders and self._settings.use_mock,
                        confirm_live_orders=config.execute_orders
                        and (not self._settings.use_mock)
                        and self._live_execution_confirmed,
                    )
                    self._runtime.cycle_count += 1
                    self._runtime.last_cycle_completed_at = _now_iso()
                    self._runtime.last_result_summary = _summarize_cycle_result(result)
                    self._runtime.last_message = result.get("message")
                    if result.get("success", False):
                        self._runtime.success_count += 1
                    else:
                        self._runtime.failure_count += 1
                        self._runtime.last_error = result.get("error") or result.get("message")
                except Exception as error:  # pragma: no cover - network/runtime safeguard
                    self._runtime.cycle_count += 1
                    self._runtime.failure_count += 1
                    self._runtime.last_cycle_completed_at = _now_iso()
                    self._runtime.last_error = str(error)
                    self._runtime.last_message = "Background trade cycle failed"
                    self._runtime.last_result_summary = {
                        "success": False,
                        "message": str(error),
                    }

                self._runtime.current_phase = "sleeping"
                self._persist_state()
                await self._sleep_with_stop(config.cycle_interval_seconds)
        finally:
            await client.close()
            self._runtime.running = False
            self._runtime.current_phase = "stopped"
            self._runtime.last_stopped_at = _now_iso()
            self._persist_state()


__all__ = [
    "BackgroundTradeEngine",
    "DEFAULT_STATE_PATH",
    "TradeEngineConfig",
    "TradeEngineRuntime",
]
