"""Integration-ish tests for IntradayWatcher's order routing.

We don't spin up the full async run loop. Instead we instantiate the
watcher with a stub Multica dispatcher and patched order primitives,
then drive its internal methods directly to verify the
ACTION-to-order mapping, the tier-1 fast path, the cooldown / in-flight
locks, and the stale-check behavior.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path

os.environ.setdefault("KIWOOM_APPKEY", "dummy-appkey")
os.environ.setdefault("KIWOOM_SECRETKEY", "dummy-secretkey")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402

from src.config import Settings  # noqa: E402
from src.services import market as market_module  # noqa: E402
from src.services import watcher as watcher_module  # noqa: E402
from src.services.daily_risk import (  # noqa: E402
    BLOCK_CALENDAR_UNCERTAIN,
    DailyEntryBreaker,
    DailyRiskLimits,
)
from src.services.order_ledger import (  # noqa: E402
    STORAGE_NETWORK,
    STATE_INTENDED,
    STATE_REJECTED,
    STATE_FILLED,
    STATE_PARTIAL,
    STATE_RELEASED,
    STATE_SUBMITTED,
    STATE_UNKNOWN,
    OrderLedger,
    OrderLedgerError,
)
from src.services.multica_dispatch import (  # noqa: E402
    ActionResponse,
    IssueRef,
    extract_action_tag,
)
from src.services.watcher import IntradayWatcher, WatcherConfig  # noqa: E402
from src.services.watcher_status import TriggerLogEntry  # noqa: E402
from src.services.watcher_triggers import (  # noqa: E402
    KST,
    ROLE_EVALUATOR,
    ROLE_PM,
    ROLE_SCREENER,
    ROLE_SELF,
    TriggerEvent,
)


def _entry_for(event: TriggerEvent) -> TriggerLogEntry:
    return TriggerLogEntry(
        detected_at=event.detected_at.isoformat(),
        trigger_type=event.trigger_type,
        tier=event.tier,
        scope=event.scope,
        target_role=event.target_role,
        stock_code=event.stock_code,
        stock_name=event.stock_name,
        reason=event.reason,
    )


# -- helpers --------------------------------------------------------------


class StubNotifier:
    """In-memory notifier used to keep tests off the network."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str]] = []

    async def info(self, title: str, description: str) -> None:
        self.calls.append(("info", title, description))

    async def success(self, title: str, description: str) -> None:
        self.calls.append(("success", title, description))

    async def warn(self, title: str, description: str) -> None:
        self.calls.append(("warn", title, description))

    async def error(self, title: str, description: str) -> None:
        self.calls.append(("error", title, description))


class StubDispatcher:
    """Minimal dispatcher; records calls for assertions."""

    def __init__(self, *, action: str | None = "HOLD", run_id: str = "run-1"):
        self.comments: list[tuple[str, str]] = []
        self.daily = IssueRef(id="daily-1", title="daily")
        self.holding = IssueRef(id="holding-1", title="holding")
        self.candidate = IssueRef(id="candidate-1", title="candidate")
        self.risk = IssueRef(id="risk-1", title="risk")
        self._action = action
        self._run_id = run_id

    async def ensure_daily_issue(self, *, now=None):
        return self.daily

    async def ensure_holding_issue(self, *, code, name, now=None):
        return self.holding

    async def ensure_candidate_issue(self, *, code, name, now=None):
        return self.candidate

    async def ensure_risk_issue(self, *, now=None):
        return self.risk

    async def ensure_pm_log_issue(self, *, now=None):
        # Global PM triggers (periodic_review) route here. Without it, any
        # test that drives a full `_tick` picks up an unrelated AttributeError.
        return self.daily

    async def add_comment(self, issue_id, content):
        self.comments.append((issue_id, content))
        return True

    async def latest_completed_run(self, issue_id):
        return None

    async def wait_for_new_action(
        self, issue_id, *, prev_run_id, timeout_seconds, poll_seconds=10
    ):
        if self._action is None:
            return None
        return ActionResponse(
            action=self._action,
            output=f"<!-- ACTION: {self._action} -->",
            run_id=self._run_id,
            completed_at=None,
        )


def _settings() -> Settings:
    return Settings(
        KIWOOM_USE_MOCK="true",
        KIWOOM_MOCK_APPKEY="mock-key",
        KIWOOM_MOCK_SECRETKEY="mock-secret",
    )


def _config(**overrides) -> WatcherConfig:
    cfg = WatcherConfig(
        execute_orders=True,
        cooldown_seconds=300,
        agent_timeout_seconds=1,
        agent_poll_seconds=1,
    )
    for k, v in overrides.items():
        setattr(cfg, k, v)
    return cfg


def _build_watcher(
    *, dispatcher=None, config=None, breaker=None, ledger=None
) -> IntradayWatcher:
    cfg = config or _config()
    watcher = IntradayWatcher(
        _settings(),
        cfg,
        dispatcher=dispatcher or StubDispatcher(),
        client=object(),  # never actually used in these tests
        notifier=StubNotifier(),  # type: ignore[arg-type]  # duck-typed
        # state_path=None keeps the breaker off the real filesystem; tests
        # that exercise restart durability pass their own tmp-path breaker.
        breaker=breaker
        or DailyEntryBreaker(
            DailyRiskLimits(
                max_daily_loss_pct=cfg.max_daily_loss_pct,
                max_daily_loss_krw=cfg.max_daily_loss_krw,
                max_daily_new_entries=cfg.max_daily_new_entries,
                loss_source_verified=cfg.daily_loss_source_verified,
            ),
            state_path=None,
        ),
        # An in-memory ledger per watcher: durable-restart behaviour is tested
        # explicitly with a tmp-path ledger, everything else just needs
        # isolation from the repo's real output/ file.
        ledger=ledger if ledger is not None else OrderLedger(None),
    )
    # Healthy-but-empty account queries by default. The client is a bare
    # object(), so without these every buy would fail closed on the pre-order
    # reconciliation and every exit would emit a refresh-failure alert.
    # `_fetch_open_orders` echoes the cache back so a test that seeds
    # `_last_open_orders` keeps its rows across a refresh; tests that want a
    # broken query override these with a raising stub.
    async def _stub_open_orders():
        return list(watcher._last_open_orders)

    async def _stub_executions():
        return []

    watcher._fetch_open_orders = _stub_open_orders  # type: ignore[assignment]
    watcher._fetch_executions = _stub_executions  # type: ignore[assignment]
    async def entry_portfolio(planner_result):
        return planner_result

    async def entry_candidate(event, planner_result):
        return event

    watcher._refresh_entry_portfolio = entry_portfolio
    watcher._refresh_entry_candidate = entry_candidate
    watcher._market_session_status = lambda now=None: watcher_module.krx_regular_session_status(
        datetime(2026, 9, 4, 10, tzinfo=KST)
    )
    return watcher


# -- ACTION tag extraction ------------------------------------------------


def test_extract_action_tag_basic():
    assert extract_action_tag("blah\n<!-- ACTION: HOLD -->") == "HOLD"
    assert extract_action_tag("<!-- ACTION: take_profit -->") == "TAKE_PROFIT"
    assert extract_action_tag("<!-- ACTION: TIER2 | score 15 -->") == "TIER2"
    assert extract_action_tag("Final ACTION: `TIER2`.") == "TIER2"
    assert extract_action_tag("최종 ACTION은 `HOLD`입니다.") == "HOLD"
    assert extract_action_tag("no tag here") == "NO_TAG"
    assert extract_action_tag("<!-- ACTION: WEIRD -->") == "WEIRD?"


# -- tier 1 routing -------------------------------------------------------


def test_tier1_stop_loss_places_market_sell(monkeypatch):
    sells: list[dict] = []

    async def fake_sell(client, **kwargs):
        sells.append(kwargs)
        return {"success": True}

    monkeypatch.setattr(watcher_module.order_service, "place_stock_sell_order", fake_sell)

    w = _build_watcher()
    event = TriggerEvent(
        trigger_type="stop_loss",
        tier=1,
        scope="stock",
        target_role=ROLE_SELF,
        stock_code="005930",
        stock_name="삼성전자",
        snapshot={"profit_rate": -3.5, "quantity": 10},
        detected_at=datetime.now(KST),
        reason="손절",
        suggested_action="sell_market",
    )
    asyncio.run(w._execute_tier1(event, _entry_for(event)))

    assert len(sells) == 1
    assert sells[0]["stk_cd"] == "005930"
    assert sells[0]["ord_qty"] == "10"
    assert sells[0]["order_type_code"] == "3"  # market


def test_tier1_skipped_when_execute_disabled(monkeypatch):
    sells: list[dict] = []

    async def fake_sell(client, **kwargs):
        sells.append(kwargs)
        return {"success": True}

    monkeypatch.setattr(watcher_module.order_service, "place_stock_sell_order", fake_sell)

    w = _build_watcher(config=_config(execute_orders=False))
    event = TriggerEvent(
        trigger_type="stop_loss",
        tier=1,
        scope="stock",
        target_role=ROLE_SELF,
        stock_code="005930",
        stock_name="삼성전자",
        snapshot={"quantity": 5},
        detected_at=datetime.now(KST),
        reason="손절",
        suggested_action="sell_market",
    )
    asyncio.run(w._execute_tier1(event, _entry_for(event)))
    assert sells == []


def test_tier1_cancel_routes_to_cancel_api(monkeypatch):
    cancels: list[dict] = []

    async def fake_cancel(client, **kwargs):
        cancels.append(kwargs)
        return {"success": True}

    monkeypatch.setattr(watcher_module.order_service, "cancel_stock_order", fake_cancel)

    w = _build_watcher()
    event = TriggerEvent(
        trigger_type="stale_unfilled_order",
        tier=1,
        scope="stock",
        target_role=ROLE_SELF,
        stock_code="005930",
        stock_name="삼성전자",
        snapshot={"qty": "10", "order_no": "OR-1"},
        detected_at=datetime.now(KST),
        reason="stale",
        suggested_action="cancel_order",
        metadata={"order_no": "OR-1"},
    )
    asyncio.run(w._execute_tier1(event, _entry_for(event)))

    assert len(cancels) == 1
    assert cancels[0]["orig_ord_no"] == "OR-1"
    assert cancels[0]["cncl_qty"] == "10"


# -- ACTION → orders (tier 2) --------------------------------------------


def test_holding_action_hold_does_nothing(monkeypatch):
    sells: list[dict] = []

    async def fake_sell(client, **kwargs):
        sells.append(kwargs)
        return {"success": True}

    monkeypatch.setattr(watcher_module.order_service, "place_stock_sell_order", fake_sell)

    w = _build_watcher()
    event = TriggerEvent(
        trigger_type="holding_swing",
        tier=2,
        scope="stock",
        target_role=ROLE_EVALUATOR,
        stock_code="005930",
        stock_name="삼성전자",
        snapshot={"quantity": 10},
        detected_at=datetime.now(KST),
        reason="swing",
    )
    asyncio.run(w._apply_action(event, "HOLD", {}))
    assert sells == []


def test_holding_action_trim_sells_half(monkeypatch):
    sells: list[dict] = []

    async def fake_sell(client, **kwargs):
        sells.append(kwargs)
        return {"success": True}

    monkeypatch.setattr(watcher_module.order_service, "place_stock_sell_order", fake_sell)

    w = _build_watcher()
    event = TriggerEvent(
        trigger_type="holding_swing",
        tier=2,
        scope="stock",
        target_role=ROLE_EVALUATOR,
        stock_code="005930",
        stock_name="삼성전자",
        snapshot={"quantity": 10},
        detected_at=datetime.now(KST),
        reason="swing",
    )
    asyncio.run(w._apply_action(event, "TRIM", {}))
    assert len(sells) == 1
    assert sells[0]["ord_qty"] == "5"


def test_holding_action_cut_loss_uses_market(monkeypatch):
    sells: list[dict] = []

    async def fake_sell(client, **kwargs):
        sells.append(kwargs)
        return {"success": True}

    monkeypatch.setattr(watcher_module.order_service, "place_stock_sell_order", fake_sell)

    w = _build_watcher()
    event = TriggerEvent(
        trigger_type="holding_swing",
        tier=2,
        scope="stock",
        target_role=ROLE_EVALUATOR,
        stock_code="005930",
        stock_name="삼성전자",
        snapshot={"quantity": 7},
        detected_at=datetime.now(KST),
        reason="swing",
    )
    asyncio.run(w._apply_action(event, "CUT_LOSS", {}))
    assert sells[0]["order_type_code"] == "3"
    assert sells[0]["ord_qty"] == "7"


def test_candidate_tier1_buys_full_budget(monkeypatch):
    buys: list[dict] = []

    async def fake_buy(client, **kwargs):
        buys.append(kwargs)
        return {"success": True}

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)

    w = _build_watcher()
    event = TriggerEvent(
        trigger_type="new_candidate",
        tier=2,
        scope="stock",
        target_role=ROLE_SCREENER,
        stock_code="123456",
        stock_name="채비",
        snapshot={"entry_price": "10000", "entry_order_type_code": "0"},
        detected_at=datetime.now(KST),
        reason="new",
    )
    planner = {"portfolio": {"position_budget": 100_000}}
    asyncio.run(w._apply_action(event, "TIER1", planner))

    assert len(buys) == 1
    assert buys[0]["stk_cd"] == "123456"
    # 100000 / 10000 = 10
    assert buys[0]["ord_qty"] == "10"


def test_candidate_tier2_buys_half_budget(monkeypatch):
    buys: list[dict] = []

    async def fake_buy(client, **kwargs):
        buys.append(kwargs)
        return {"success": True}

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)

    w = _build_watcher()
    event = TriggerEvent(
        trigger_type="new_candidate",
        tier=2,
        scope="stock",
        target_role=ROLE_SCREENER,
        stock_code="123456",
        stock_name="채비",
        snapshot={"entry_price": "10000", "entry_order_type_code": "0"},
        detected_at=datetime.now(KST),
        reason="new",
    )
    planner = {"portfolio": {"position_budget": 100_000}}
    asyncio.run(w._apply_action(event, "TIER2", planner))

    assert len(buys) == 1
    # half budget 50000 / 10000 = 5
    assert buys[0]["ord_qty"] == "5"


def test_candidate_reject_does_not_buy(monkeypatch):
    buys: list[dict] = []

    async def fake_buy(client, **kwargs):
        buys.append(kwargs)
        return {"success": True}

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)

    w = _build_watcher()
    event = TriggerEvent(
        trigger_type="new_candidate",
        tier=2,
        scope="stock",
        target_role=ROLE_SCREENER,
        stock_code="123456",
        stock_name="채비",
        snapshot={"entry_price": "10000", "entry_order_type_code": "0"},
        detected_at=datetime.now(KST),
        reason="new",
    )
    asyncio.run(
        w._apply_action(event, "REJECT", {"portfolio": {"position_budget": 100_000}})
    )
    assert buys == []


# -- order-apply result model (P1-1 / P1-4) -------------------------------
#
# `submitted` (the broker booked the request) must never be reported as a
# fill, and a no-op ACTION or a blocked gate must never be reported as a
# trade at all. These tests pin the whole result table down.


def _tier1_sell_event(quantity=10):
    return TriggerEvent(
        trigger_type="stop_loss",
        tier=1,
        scope="stock",
        target_role=ROLE_SELF,
        stock_code="005930",
        stock_name="삼성전자",
        snapshot={"profit_rate": -3.5, "quantity": quantity},
        detected_at=datetime.now(KST),
        reason="손절",
        suggested_action="sell_market",
    )


def _holding_event(code="005930", quantity=10):
    return TriggerEvent(
        trigger_type="holding_swing",
        tier=2,
        scope="stock",
        target_role=ROLE_EVALUATOR,
        stock_code=code,
        stock_name="삼성전자",
        snapshot={"quantity": quantity},
        detected_at=datetime.now(KST),
        reason="swing",
    )


def _ok_order(**extra):
    """Shape of a Kiwoom order response that was accepted, not filled."""

    payload = {"success": True, "return_code": 0, "return_msg": "정상처리"}
    payload.update(extra)
    return payload


def _rejected_order():
    return {
        "success": False,
        "return_code": 1902,
        "return_msg": "종목 정보가 없습니다",
        "error": "종목 정보가 없습니다",
    }


def _lost_response_order():
    """Transport blew up after the request went out — fate unknown."""

    return {
        "success": False,
        "error": "ReadTimeout",
        "message": "Stock buy order endpoint not yet implemented or failed to connect",
        "transport_state": "unknown",
    }


def test_tier1_accepted_order_is_submitted_not_executed(monkeypatch):
    async def fake_sell(client, **kwargs):
        return _ok_order(order_no="0001234")

    monkeypatch.setattr(watcher_module.order_service, "place_stock_sell_order", fake_sell)
    w = _build_watcher()
    event = _tier1_sell_event()
    entry = _entry_for(event)

    result = asyncio.run(w._execute_tier1(event, entry))

    assert result.state == "submitted"
    assert result.attempted is True
    assert result.submitted is True
    assert result.filled is False  # nothing has confirmed a fill
    assert result.success is True
    assert result.order_no == "1234"
    assert entry.outcome == "submitted"
    assert entry.outcome != "executed"


def test_tier1_rejected_order_records_failed(monkeypatch):
    async def fake_sell(client, **kwargs):
        return _rejected_order()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_sell_order", fake_sell)
    w = _build_watcher()
    event = _tier1_sell_event()
    entry = _entry_for(event)

    result = asyncio.run(w._execute_tier1(event, entry))

    assert result.state == "failed"
    assert result.attempted is True
    assert result.submitted is False
    assert result.success is False
    assert result.return_code == 1902
    assert entry.outcome == "failed"
    assert any(call[0] == "error" for call in w._notifier.calls)


def test_tier1_lost_response_records_unknown_and_warns_against_resubmit(monkeypatch):
    """A timed-out sell may already be live — it is not a clean failure."""

    async def fake_sell(client, **kwargs):
        return _lost_response_order()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_sell_order", fake_sell)
    w = _build_watcher()
    event = _tier1_sell_event()
    entry = _entry_for(event)

    result = asyncio.run(w._execute_tier1(event, entry))

    assert result.state == "unknown"
    assert result.attempted is True
    assert result.submitted is False
    assert result.success is False
    assert entry.outcome == "unknown"
    errors = [c for c in w._notifier.calls if c[0] == "error"]
    assert errors and "재주문 금지" in errors[0][2]


def test_tier1_dry_run_is_not_attempted(monkeypatch):
    async def fake_sell(client, **kwargs):
        raise AssertionError("must not order while execute_orders=False")

    monkeypatch.setattr(watcher_module.order_service, "place_stock_sell_order", fake_sell)
    w = _build_watcher(config=_config(execute_orders=False))
    event = _tier1_sell_event()
    entry = _entry_for(event)

    result = asyncio.run(w._execute_tier1(event, entry))

    assert result.state == "skipped"
    assert result.attempted is False
    assert result.success is False
    assert entry.outcome == "dry_run"


def test_tier1_missing_quantity_is_skipped_not_executed(monkeypatch):
    async def fake_sell(client, **kwargs):
        raise AssertionError("must not order without a quantity")

    monkeypatch.setattr(watcher_module.order_service, "place_stock_sell_order", fake_sell)
    w = _build_watcher()
    event = _tier1_sell_event(quantity=0)
    entry = _entry_for(event)

    result = asyncio.run(w._execute_tier1(event, entry))

    assert result.state == "skipped"
    assert result.attempted is False
    assert entry.outcome == "skipped"


def test_tier1_without_order_mapping_completes_as_informational():
    """A tier-1 trigger with no order to place must still complete.

    It previously returned early leaving `outcome=None` forever, so the
    trigger sat unfinished in `/recent`.
    """

    w = _build_watcher()
    event = TriggerEvent(
        trigger_type="position_overflow",
        tier=1,
        scope="stock",
        target_role=ROLE_SELF,
        stock_code="005930",
        stock_name="삼성전자",
        snapshot={"quantity": 10},
        detected_at=datetime.now(KST),
        reason="overflow",
        suggested_action=None,
    )
    entry = _entry_for(event)

    result = asyncio.run(w._execute_tier1(event, entry))

    assert result.state == "informational"
    assert result.attempted is False
    assert entry.outcome == "informational"


def test_holding_hold_is_informational_and_not_attempted(monkeypatch):
    async def fake_sell(client, **kwargs):
        raise AssertionError("HOLD must not place an order")

    monkeypatch.setattr(watcher_module.order_service, "place_stock_sell_order", fake_sell)
    w = _build_watcher()

    result = asyncio.run(w._apply_action(_holding_event(), "HOLD", {}))

    assert result.state == "informational"
    assert result.attempted is False
    assert result.submitted is False
    assert result.filled is False
    assert result.success is False


def test_holding_sell_failure_returns_failed(monkeypatch):
    async def fake_sell(client, **kwargs):
        return _rejected_order()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_sell_order", fake_sell)
    w = _build_watcher()

    result = asyncio.run(w._apply_action(_holding_event(), "CUT_LOSS", {}))

    assert result.state == "failed"
    assert result.success is False
    assert result.return_code == 1902


def test_holding_sell_accepted_is_submitted_not_filled(monkeypatch):
    async def fake_sell(client, **kwargs):
        return _ok_order(sell_order_result={"ord_no": "77"})

    monkeypatch.setattr(watcher_module.order_service, "place_stock_sell_order", fake_sell)
    w = _build_watcher()

    result = asyncio.run(w._apply_action(_holding_event(), "TRIM", {}))

    assert result.state == "submitted"
    assert result.submitted is True
    assert result.filled is False
    assert result.order_no == "77"


def test_holding_action_without_quantity_is_skipped(monkeypatch):
    async def fake_sell(client, **kwargs):
        raise AssertionError("no quantity to sell")

    monkeypatch.setattr(watcher_module.order_service, "place_stock_sell_order", fake_sell)
    w = _build_watcher()

    result = asyncio.run(w._apply_action(_holding_event(quantity=0), "TAKE_PROFIT", {}))

    assert result.state == "skipped"
    assert result.attempted is False


def test_tier2_dry_run_is_skipped_not_executed(monkeypatch):
    async def fake_sell(client, **kwargs):
        raise AssertionError("must not order while execute_orders=False")

    monkeypatch.setattr(watcher_module.order_service, "place_stock_sell_order", fake_sell)
    w = _build_watcher(config=_config(execute_orders=False))

    result = asyncio.run(w._apply_action(_holding_event(), "CUT_LOSS", {}))

    assert result.state == "skipped"
    assert result.attempted is False


def test_pm_portfolio_action_is_informational_only():
    w = _build_watcher()
    event = _pm_event("periodic_review")

    result = asyncio.run(w._apply_action(event, "TRIM", {}))

    assert result.state == "informational"
    assert result.attempted is False


def _candidate_event(code="123456"):
    return TriggerEvent(
        trigger_type="new_candidate",
        tier=2,
        scope="stock",
        target_role=ROLE_SCREENER,
        stock_code=code,
        stock_name="채비",
        snapshot={"entry_price": "10000", "entry_order_type_code": "0"},
        detected_at=datetime.now(KST),
        reason="new",
    )


def test_candidate_skips_new_stock_at_max_positions(monkeypatch):
    """Gate 1: a NEW stock can't open once max_positions is reached."""
    buys: list[dict] = []

    async def fake_buy(client, **kwargs):
        buys.append(kwargs)
        return {"success": True}

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)
    w = _build_watcher()
    planner = {
        "portfolio": {"position_budget": 100_000, "max_positions": 3},
        "holdings": [
            {"stock_code": "111", "quantity": 1, "current_price": 1000},
            {"stock_code": "222", "quantity": 1, "current_price": 1000},
            {"stock_code": "333", "quantity": 1, "current_price": 1000},
        ],
    }
    asyncio.run(w._apply_action(_candidate_event("999999"), "TIER1", planner))
    assert buys == []  # new stock blocked at cap


def test_candidate_repeat_buy_blocked_when_budget_full(monkeypatch):
    """Gate 2: same-stock repeat buy is blocked once held value fills budget.

    This is the HS화성 case — held 35 @ 12000 ≈ 420k already exceeds the
    100k budget, so a further candidate fire must not stack more shares.
    """
    buys: list[dict] = []

    async def fake_buy(client, **kwargs):
        buys.append(kwargs)
        return {"success": True}

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)
    w = _build_watcher()
    planner = {
        "portfolio": {"position_budget": 100_000, "max_positions": 3},
        "holdings": [
            {"stock_code": "123456", "quantity": 35, "current_price": 12000},
        ],
    }
    asyncio.run(w._apply_action(_candidate_event("123456"), "TIER2", planner))
    assert buys == []  # budget already exhausted for this stock


def test_candidate_partial_budget_caps_quantity(monkeypatch):
    """Gate 2: with some held value, only the remaining budget is buyable."""
    buys: list[dict] = []

    async def fake_buy(client, **kwargs):
        buys.append(kwargs)
        return {"success": True}

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)
    w = _build_watcher()
    # budget 100k, already hold 3 @ 10000 = 30k → remaining 70k → 7 shares
    planner = {
        "portfolio": {"position_budget": 100_000, "max_positions": 3},
        "holdings": [
            {"stock_code": "123456", "quantity": 3, "current_price": 10000},
        ],
    }
    asyncio.run(w._apply_action(_candidate_event("123456"), "TIER1", planner))
    assert len(buys) == 1
    assert buys[0]["ord_qty"] == "7"  # 70000 / 10000


def test_placed_orders_block_race_across_stale_holdings(monkeypatch):
    """The real race: account holdings stay STALE (empty) while multiple
    buys fire within the poll lag. Gate must count the watcher's own placed
    orders (held ∪ placed), not just the lagged account — this is the 6/12
    fix (5 orders past max_positions=3). 2026-06-17.
    """
    buys: list[dict] = []

    async def fake_buy(client, **kwargs):
        buys.append(kwargs)
        return {"success": True}

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)
    w = _build_watcher()
    # holdings stays [] across all calls — buys not yet reflected in the poll.
    planner = {"portfolio": {"position_budget": 100_000, "max_positions": 3}, "holdings": []}

    # 3 distinct stocks open (each placed-order recorded, budget 100k → qty 10).
    for code in ["111111", "222222", "333333"]:
        asyncio.run(w._apply_action(_candidate_event(code), "TIER1", planner))
    assert len(buys) == 3

    # 4th distinct stock: blocked by Gate 1 union (placed distinct=3 = cap),
    # even though account holdings is still empty.
    asyncio.run(w._apply_action(_candidate_event("444444"), "TIER1", planner))
    assert len(buys) == 3  # blocked

    # Same stock repeat: blocked by Gate 2 (placed value 100k = budget).
    asyncio.run(w._apply_action(_candidate_event("111111"), "TIER1", planner))
    assert len(buys) == 3  # blocked


def test_placed_order_not_recorded_on_failed_buy(monkeypatch):
    """A rejected order must NOT be recorded — else it wedges the gate shut."""
    async def fake_buy_fail(client, **kwargs):
        return {"success": False, "error": "rejected"}

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy_fail)
    w = _build_watcher()
    planner = {"portfolio": {"position_budget": 100_000, "max_positions": 3}, "holdings": []}
    asyncio.run(w._apply_action(_candidate_event("111111"), "TIER1", planner))
    # The intent is recorded but terminates as REJECTED, so it holds no slot.
    assert w._ledger.unresolved() == []


def test_candidate_reject_is_informational_not_attempted(monkeypatch):
    async def fake_buy(client, **kwargs):
        raise AssertionError("REJECT must not buy")

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)
    w = _build_watcher()
    planner = {"portfolio": {"position_budget": 100_000, "max_positions": 3}}

    result = asyncio.run(w._apply_action(_candidate_event(), "REJECT", planner))

    assert result.state == "informational"
    assert result.attempted is False
    assert result.submitted is False
    assert result.success is False


def test_candidate_accepted_buy_is_submitted_not_filled(monkeypatch):
    async def fake_buy(client, **kwargs):
        return _ok_order(buy_order_result={"ord_no": "0000042"})

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)
    w = _build_watcher()
    planner = {"portfolio": {"position_budget": 100_000, "max_positions": 3}}

    result = asyncio.run(w._apply_action(_candidate_event(), "TIER1", planner))

    assert result.state == "submitted"
    assert result.submitted is True
    assert result.filled is False
    assert result.success is True
    assert result.order_no == "42"


def test_candidate_max_positions_skip_is_not_attempted(monkeypatch):
    async def fake_buy(client, **kwargs):
        raise AssertionError("cap reached — must not buy")

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)
    w = _build_watcher()
    planner = {
        "portfolio": {"position_budget": 100_000, "max_positions": 3},
        "holdings": [
            {"stock_code": "111", "quantity": 1, "current_price": 1000},
            {"stock_code": "222", "quantity": 1, "current_price": 1000},
            {"stock_code": "333", "quantity": 1, "current_price": 1000},
        ],
    }

    result = asyncio.run(w._apply_action(_candidate_event("999999"), "TIER1", planner))

    assert result.state == "skipped"
    assert result.attempted is False
    assert result.success is False
    assert "max_positions" in (result.reason or "")


def test_candidate_budget_skip_is_not_attempted(monkeypatch):
    async def fake_buy(client, **kwargs):
        raise AssertionError("budget exhausted — must not buy")

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)
    w = _build_watcher()
    planner = {
        "portfolio": {"position_budget": 100_000, "max_positions": 3},
        "holdings": [{"stock_code": "123456", "quantity": 35, "current_price": 12000}],
    }

    result = asyncio.run(w._apply_action(_candidate_event("123456"), "TIER2", planner))

    assert result.state == "skipped"
    assert result.attempted is False


def test_candidate_buy_failure_returns_failed(monkeypatch):
    async def fake_buy(client, **kwargs):
        return _rejected_order()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)
    w = _build_watcher()
    planner = {"portfolio": {"position_budget": 100_000, "max_positions": 3}}

    result = asyncio.run(w._apply_action(_candidate_event(), "TIER1", planner))

    assert result.state == "failed"
    assert result.attempted is True
    assert result.submitted is False
    assert result.success is False


def test_candidate_lost_response_counts_as_exposure(monkeypatch):
    """A buy whose response was lost may be live — hold the gate shut.

    Treating `unknown` as "nothing happened" would free the per-stock budget
    and let the very next candidate fire re-buy the same name. Until the
    intent ledger can resolve it against the open-order API, the conservative
    move is to count it as placed.
    """

    calls: list[dict] = []

    async def fake_buy(client, **kwargs):
        calls.append(kwargs)
        return _lost_response_order()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)
    w = _build_watcher()
    planner = {"portfolio": {"position_budget": 100_000, "max_positions": 1}, "holdings": []}

    result = asyncio.run(w._apply_action(_candidate_event("111111"), "TIER1", planner))

    assert result.state == "unknown"
    assert result.attempted is True
    assert result.submitted is False  # we never learned that it landed
    assert result.success is False
    assert result.counts_as_exposure is True
    # Recorded as UNKNOWN, which keeps holding the slot.
    pending = w._ledger.unresolved(stock_code="111111")
    assert [i.state for i in pending] == [STATE_UNKNOWN]

    # The same trigger firing again must not stack a second order.
    repeat = asyncio.run(w._apply_action(_candidate_event("111111"), "TIER1", planner))
    assert repeat.state == "skipped"
    assert len(calls) == 1


def test_await_and_apply_records_real_order_state(monkeypatch):
    """End to end: a rejected buy is logged `failed`, never `executed`."""

    async def fake_buy(client, **kwargs):
        return _rejected_order()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)
    w = _build_watcher(dispatcher=StubDispatcher(action="TIER1"))
    event = _candidate_event("123456")
    event.snapshot["current_price"] = 10_000
    async def quote(*args, **kwargs):
        return {"quote": {"cur_prc": "10000"}}

    monkeypatch.setattr(market_module, "get_stock_detail_bundle", quote)
    entry = _entry_for(event)
    planner = {"portfolio": {"position_budget": 100_000, "max_positions": 3}}

    asyncio.run(w._await_and_apply(event, entry, "candidate-1", None, planner))

    assert entry.action == "TIER1"
    assert entry.outcome == "failed"
    assert any(
        call[0] == "error" and "Tier2 주문 실패" in call[1] for call in w._notifier.calls
    )
    # The slot is always released regardless of order outcome.
    assert w._in_flight == {}


def test_await_and_apply_records_submitted_for_accepted_buy(monkeypatch):
    async def fake_buy(client, **kwargs):
        return _ok_order(buy_order_result={"ord_no": "55"})

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)
    w = _build_watcher(dispatcher=StubDispatcher(action="TIER1"))
    event = _candidate_event("123456")
    event.snapshot["current_price"] = 10_000
    async def quote(*args, **kwargs):
        return {"quote": {"cur_prc": "10000"}}

    monkeypatch.setattr(market_module, "get_stock_detail_bundle", quote)
    entry = _entry_for(event)
    planner = {"portfolio": {"position_budget": 100_000, "max_positions": 3}}

    asyncio.run(w._await_and_apply(event, entry, "candidate-1", None, planner))

    assert entry.outcome == "submitted"
    assert "order_no=55" in (entry.detail or "")
    assert any(
        call[0] == "success" and "Tier2 주문 접수" in call[1]
        for call in w._notifier.calls
    )


def _holding_swing_event(code="111111", profit_rate=1.0):
    return TriggerEvent(
        trigger_type="holding_swing",
        tier=2,
        scope="stock",
        target_role=ROLE_EVALUATOR,
        stock_code=code,
        stock_name="held",
        snapshot={"profit_rate": profit_rate, "quantity": 10, "current_price": 10000},
        detected_at=datetime.now(KST),
        reason="swing",
    )


def test_holding_swing_dedup_skips_repeat_noop():
    """Prior HOLD + profit barely moved → skip (the 엠앤씨솔루션 waste)."""
    w = _build_watcher()
    w._last_holding_action["111111"] = ("HOLD", 1.0, datetime.now(KST), "informational")
    # 1.0 → 1.5 = Δ0.5 < 1.5 threshold → skip
    assert w._should_skip_holding_swing(_holding_swing_event("111111", 1.5)) is True


def test_holding_swing_dedup_dispatches_on_profit_move():
    w = _build_watcher()
    w._last_holding_action["111111"] = ("HOLD", 1.0, datetime.now(KST), "informational")
    # 1.0 → 3.0 = Δ2.0 ≥ 1.5 → re-evaluate
    assert w._should_skip_holding_swing(_holding_swing_event("111111", 1.5 + 1.5)) is False


@pytest.mark.parametrize("state", ["submitted", "unknown", "filled"])
def test_holding_swing_dedup_never_skips_while_an_exit_is_working(state):
    """A sell the broker holds is worth re-checking even on a flat position."""

    w = _build_watcher()
    w._last_holding_action["111111"] = ("TRIM", 1.0, datetime.now(KST), state)
    assert w._should_skip_holding_swing(_holding_swing_event("111111", 1.0)) is False


@pytest.mark.parametrize("state", ["failed", "skipped"])
def test_holding_swing_dedup_treats_a_refused_sell_as_the_noop_it_was(state):
    """The 2026-08-31 amplifier: 7 dispatches, 48 comments, quota gone.

    Every exit was rejected 308003, so the position never moved and the next
    tick asked the identical question. The sell-action exemption is for
    watching an exit in progress; a refused order started none.
    """

    w = _build_watcher()
    w._last_holding_action["111111"] = ("TAKE_PROFIT", 1.0, datetime.now(KST), state)
    assert w._should_skip_holding_swing(_holding_swing_event("111111", 1.0)) is True


def test_refused_sell_still_re_dispatches_once_the_position_moves():
    """Suppression must not outlive the reason for it."""

    w = _build_watcher()
    w._last_holding_action["111111"] = ("TAKE_PROFIT", 1.0, datetime.now(KST), "failed")
    assert w._should_skip_holding_swing(_holding_swing_event("111111", 3.0)) is False


def test_rejected_exit_stops_re_dispatching_end_to_end(monkeypatch):
    """Drive the real path: the gate has to be *reached*, not just correct.

    Two ticks of the same flat position while the broker refuses every sell.
    Before this fix the second one dispatched again -- and in production that
    ran seven times, each agent run re-reading a thread that had grown to 48
    comments, which is what emptied the codex quota on 2026-08-31.
    """

    async def refused(client, **kwargs):
        return _rejected_order()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_sell_order", refused)
    w = _build_watcher(
        dispatcher=StubDispatcher(action="TAKE_PROFIT"),
        config=_config(cooldown_seconds=0),
    )

    async def tick():
        await w._handle_trigger(_holding_swing_event(profit_rate=1.0), planner_result={})
        for slot in list(w._in_flight.values()):
            await slot.task

    async def driver():
        await tick()
        await tick()

    asyncio.run(driver())

    # Each dispatch posts a trigger comment, so counting those counts agent
    # runs -- the resource that ran out.
    dispatched = [c for _issue, c in w._dispatcher.comments if "[트리거:" in c]
    assert len(dispatched) == 1, w._dispatcher.comments


def test_holding_swing_dedup_dispatches_first_time():
    w = _build_watcher()  # no prior action recorded
    assert w._should_skip_holding_swing(_holding_swing_event("111111", 1.0)) is False


def test_holding_swing_dedup_disabled_with_zero_delta():
    w = _build_watcher(config=_config(holding_dedup_profit_delta_pct=0.0))
    w._last_holding_action["111111"] = ("HOLD", 1.0, datetime.now(KST), "informational")
    assert w._should_skip_holding_swing(_holding_swing_event("111111", 1.0)) is False


class PeerReviewDispatcher(StubDispatcher):
    """Records the peer call and answers with a differing ACTION."""

    async def request_peer_review(
        self,
        issue_id,
        *,
        issue_type,
        trigger_comment,
        primary_response,
        timeout_seconds,
        poll_seconds=10,
    ):
        self.comments.append((issue_id, f"peer:{issue_type}:{primary_response.action}"))
        return ActionResponse(
            action="CUT_LOSS",
            output="<!-- ACTION: CUT_LOSS -->",
            run_id="peer-1",
            completed_at=None,
        )


def test_tier2_records_peer_review_mismatch(monkeypatch):
    async def fake_sell(client, **kwargs):
        return _ok_order()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_sell_order", fake_sell)
    dispatcher = PeerReviewDispatcher(action="TRIM")
    w = _build_watcher(dispatcher=dispatcher)
    event = _holding_event()
    entry = _entry_for(event)

    asyncio.run(w._await_and_apply(event, entry, "holding-1", None, {}))

    assert entry.action == "TRIM"
    assert "peer_review=CUT_LOSS" in (entry.detail or "")
    assert ("holding-1", "peer:holding:TRIM") in dispatcher.comments
    assert any(
        call[0] == "warn" and "교차검토 불일치" in call[1] for call in w._notifier.calls
    )


# -- cooldown / in-flight -------------------------------------------------


def test_cooldown_suppresses_repeat_within_window(monkeypatch):
    sells: list[dict] = []

    async def fake_sell(client, **kwargs):
        sells.append(kwargs)
        return {"success": True}

    monkeypatch.setattr(watcher_module.order_service, "place_stock_sell_order", fake_sell)

    w = _build_watcher()
    base_event = TriggerEvent(
        trigger_type="stop_loss",
        tier=1,
        scope="stock",
        target_role=ROLE_SELF,
        stock_code="005930",
        stock_name="삼성전자",
        snapshot={"quantity": 1},
        detected_at=datetime.now(KST),
        reason="x",
        suggested_action="sell_market",
    )
    asyncio.run(w._handle_trigger(base_event, planner_result={}))
    asyncio.run(w._handle_trigger(base_event, planner_result={}))
    # Second call should be suppressed by cooldown.
    assert len(sells) == 1


def test_regime_baseline_suppresses_until_stable():
    w = _build_watcher(config=_config(regime_stability_ticks=3))
    # First neutral observation — sets last_emitted but no fire.
    w._regime_history.append("neutral")
    assert w._build_regime_flip_baseline("neutral") is None
    w._regime_history.append("neutral")
    assert w._build_regime_flip_baseline("neutral") is None
    w._regime_history.append("neutral")
    # First time history is full; recorded as the baseline, no fire yet.
    assert w._build_regime_flip_baseline("neutral") is None
    assert w._last_emitted_regime == "neutral"
    # Switch to risk_off but only 2 of 3 recent — still suppressed.
    w._regime_history.append("risk_off")
    assert w._build_regime_flip_baseline("risk_off") is None
    w._regime_history.append("risk_off")
    assert w._build_regime_flip_baseline("risk_off") is None
    # Now full window of risk_off — eligible to flip.
    w._regime_history.append("risk_off")
    baseline = w._build_regime_flip_baseline("risk_off")
    assert baseline == {"regime": "neutral"}


def test_regime_baseline_does_not_re_emit_same_label():
    w = _build_watcher(config=_config(regime_stability_ticks=2))
    for _ in range(2):
        w._regime_history.append("risk_on")
        w._build_regime_flip_baseline("risk_on")
    assert w._last_emitted_regime == "risk_on"
    # Another stable risk_on tick should not emit again.
    w._regime_history.append("risk_on")
    assert w._build_regime_flip_baseline("risk_on") is None


def test_purge_expired_cooldowns_drops_old_entries():
    w = _build_watcher()
    now = datetime.now(KST)
    w._cooldowns = {
        "stock:001|stop_loss": now - timedelta(seconds=10),  # expired
        "stock:002|stop_loss": now + timedelta(seconds=300),  # alive
    }
    w._purge_expired_cooldowns()
    assert "stock:001|stop_loss" not in w._cooldowns
    assert "stock:002|stop_loss" in w._cooldowns


def test_pm_global_trigger_routes_to_pm_log_issue():
    """ROLE_PM with scope=global must use ensure_pm_log_issue, not daily."""

    captured = {"called": []}

    class CaptureDispatcher(StubDispatcher):
        async def ensure_daily_issue(self, *, now=None):
            captured["called"].append("daily")
            return await super().ensure_daily_issue(now=now)

        async def ensure_pm_log_issue(self, *, now=None):
            captured["called"].append("pm_log")
            return self.daily

    w = _build_watcher(dispatcher=CaptureDispatcher())
    event = TriggerEvent(
        trigger_type="periodic_review",
        tier=2,
        scope="global",
        target_role="pm",
        stock_code=None,
        stock_name=None,
        snapshot={"interval_minutes": 30},
        detected_at=datetime.now(KST),
        reason="test",
    )

    asyncio.run(w._ensure_issue_for(event))
    assert "pm_log" in captured["called"]
    assert "daily" not in captured["called"]  # pm_log internally chains to daily — ok


def test_in_flight_lock_per_stock_blocks_duplicate_dispatch():
    dispatcher = StubDispatcher(action=None)  # never resolves
    w = _build_watcher(dispatcher=dispatcher, config=_config(cooldown_seconds=0))

    event_a = TriggerEvent(
        trigger_type="holding_swing",
        tier=2,
        scope="stock",
        target_role=ROLE_EVALUATOR,
        stock_code="005930",
        stock_name="삼성전자",
        snapshot={"quantity": 1},
        detected_at=datetime.now(KST),
        reason="x",
    )
    event_b = TriggerEvent(
        trigger_type="holding_swing",
        tier=2,
        scope="stock",
        target_role=ROLE_EVALUATOR,
        stock_code="005930",
        stock_name="삼성전자",
        snapshot={"quantity": 1},
        detected_at=datetime.now(KST) + timedelta(seconds=1),
        reason="x2",
    )

    async def driver():
        await w._handle_trigger(event_a, planner_result={})
        await w._handle_trigger(event_b, planner_result={})
        # Cancel any leftover poll task
        for slot in list(w._in_flight.values()):
            slot.task.cancel()

    asyncio.run(driver())
    # Only one dispatch comment was posted because event_b hit the in-flight lock.
    assert len(dispatcher.comments) == 1


# -- Discord notification filter ----------------------------------------


def _pm_event(trigger_type: str) -> TriggerEvent:
    return TriggerEvent(
        trigger_type=trigger_type,
        tier=2,
        scope="global",
        target_role=ROLE_PM,
        stock_code=None,
        stock_name=None,
        snapshot={},
        detected_at=datetime.now(KST),
        reason="30분 정기 점검",
    )


def test_filter_suppresses_periodic_review_hold_by_default():
    w = _build_watcher()
    event = _pm_event("periodic_review")

    assert w._should_notify_tier2_action(event, "HOLD", "informational") is False
    assert w._should_notify_tier2_action(event, "ACKNOWLEDGE", "informational") is False


def test_filter_suppresses_regime_flip_hold_by_default():
    w = _build_watcher()
    event = _pm_event("regime_flip")
    assert w._should_notify_tier2_action(event, "HOLD", "informational") is False


def test_filter_keeps_actionable_pm_decisions():
    w = _build_watcher()
    event = _pm_event("periodic_review")
    # Real intent — should ping
    assert w._should_notify_tier2_action(event, "TRIM", "informational") is True
    assert w._should_notify_tier2_action(event, "ROTATE", "informational") is True


def test_filter_keeps_submitted_orders_even_if_hold():
    """Defensive: if an order actually went to the broker, always notify.

    `executed` used to be the marker here; it is gone from the watcher's
    vocabulary because it claimed fills the system never confirmed (P1-4).
    """

    w = _build_watcher()
    event = _pm_event("periodic_review")
    assert w._should_notify_tier2_action(event, "HOLD", "submitted") is True
    assert w._should_notify_tier2_action(event, "HOLD", "filled") is True
    # A no-op keeps being filtered out of the routine PM channel.
    assert w._should_notify_tier2_action(event, "HOLD", "informational") is False


def test_filter_keeps_stock_level_triggers():
    w = _build_watcher()
    holding_event = TriggerEvent(
        trigger_type="holding_swing",
        tier=2,
        scope="stock",
        target_role=ROLE_EVALUATOR,
        stock_code="005930",
        stock_name="삼성전자",
        snapshot={"profit_rate": 2.3},
        detected_at=datetime.now(KST),
        reason="2.3% swing",
    )
    assert w._should_notify_tier2_action(holding_event, "HOLD", "informational") is True


def test_filter_disabled_when_verbose_flag_set():
    w = _build_watcher(
        config=_config(notify_routine_pm_actions=True),
    )
    event = _pm_event("periodic_review")
    assert w._should_notify_tier2_action(event, "HOLD", "informational") is True


# -- Tier-2 background task exception handling (P1-2 / P1-3) --------------
#
# `_await_and_apply` runs detached via `asyncio.create_task`. Before this,
# an operational exception left the trigger with no outcome, no alert, and
# only asyncio's "Task exception was never retrieved" at GC time. Every
# stage of the pipeline is now caught, attributed and counted — and the
# per-stock lock is released no matter which stage blew up.


class BoomDispatcher(StubDispatcher):
    """Dispatcher whose agent-response poll always explodes."""

    async def wait_for_new_action(self, issue_id, *, prev_run_id, timeout_seconds, poll_seconds=10):
        raise RuntimeError("multica CLI exited 1")


def _failure_count(w, category: str) -> int:
    return w.status.failure_summary().get(category, {}).get("count", 0)


def test_dispatcher_exception_marks_failed_and_releases_lock():
    w = _build_watcher(dispatcher=BoomDispatcher())
    event = _holding_event()
    entry = _entry_for(event)
    w._in_flight[event.scope_key()] = object()  # type: ignore[assignment]
    w.status.add_in_flight(
        scope_key=event.scope_key(),
        trigger_type=event.trigger_type,
        target_role=event.target_role,
        stock_code=event.stock_code,
        stock_name=event.stock_name,
        started_at=event.detected_at,
        issue_id="holding-1",
    )

    asyncio.run(w._await_and_apply(event, entry, "holding-1", None, {}))

    assert entry.outcome == "failed"
    assert "multica CLI exited 1" in (entry.detail or "")
    assert _failure_count(w, "multica") == 1
    # The scope must be free again — a leaked slot locks this stock out of
    # every future dispatch for the life of the process.
    assert event.scope_key() not in w._in_flight
    assert w.status.snapshot()["in_flight"] == []
    assert any(call[0] == "error" for call in w._notifier.calls)


def test_stale_quote_exception_marks_failed_and_places_no_order(monkeypatch):
    """A market-data failure must never fall through into an order."""

    async def boom_valid(event):
        raise ConnectionError("quote endpoint unreachable")

    async def fake_sell(client, **kwargs):
        raise AssertionError("must not order after a stale-check failure")

    monkeypatch.setattr(watcher_module.order_service, "place_stock_sell_order", fake_sell)
    w = _build_watcher(dispatcher=StubDispatcher(action="CUT_LOSS"))
    monkeypatch.setattr(w, "_is_still_valid", boom_valid)
    event = _holding_event()
    entry = _entry_for(event)

    asyncio.run(w._await_and_apply(event, entry, "holding-1", None, {}))

    assert entry.outcome == "failed"
    assert _failure_count(w, "market") == 1
    assert "stale 시세 조회" in (entry.detail or "")
    assert w._in_flight == {}


def test_peer_review_exception_does_not_kill_the_trigger(monkeypatch):
    """A second opinion failing must not void the primary ACTION."""

    class PeerBoomDispatcher(StubDispatcher):
        async def request_peer_review(self, issue_id, **kwargs):
            raise TimeoutError("peer backend down")

    sells: list[dict] = []

    async def fake_sell(client, **kwargs):
        sells.append(kwargs)
        return _ok_order()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_sell_order", fake_sell)
    w = _build_watcher(dispatcher=PeerBoomDispatcher(action="CUT_LOSS"))
    event = _holding_event()
    entry = _entry_for(event)

    asyncio.run(w._await_and_apply(event, entry, "holding-1", None, {}))

    # Primary ACTION still applied; only the review degraded.
    assert entry.outcome == "submitted"
    assert len(sells) == 1
    # ...and the degradation is visible rather than silent.
    assert _failure_count(w, "multica") == 1
    assert w._in_flight == {}


def test_order_apply_exception_marks_failed_and_releases_lock(monkeypatch):
    async def boom_sell(client, **kwargs):
        raise RuntimeError("order client closed")

    monkeypatch.setattr(watcher_module.order_service, "place_stock_sell_order", boom_sell)
    w = _build_watcher(dispatcher=StubDispatcher(action="CUT_LOSS"))
    event = _holding_event()
    entry = _entry_for(event)

    asyncio.run(w._await_and_apply(event, entry, "holding-1", None, {}))

    assert entry.outcome == "failed"
    assert _failure_count(w, "order") == 1
    assert "ACTION 적용" in (entry.detail or "")
    assert w._in_flight == {}


def test_same_scope_dispatches_again_after_a_failure():
    """A failed trigger must not wedge its stock shut permanently."""

    w = _build_watcher(dispatcher=BoomDispatcher(), config=_config(cooldown_seconds=0))
    event = _holding_event()

    asyncio.run(w._await_and_apply(event, _entry_for(event), "holding-1", None, {}))
    assert w._in_flight == {}

    # The scope is free, so the very next fire dispatches normally.
    async def driver():
        w._dispatcher = StubDispatcher(action="HOLD")
        await w._handle_trigger(_holding_event(), planner_result={})
        for slot in list(w._in_flight.values()):
            await slot.task

    asyncio.run(driver())
    assert w._in_flight == {}


def test_cancellation_is_recorded_separately_from_failure():
    """Shutdown cancels in-flight tasks; that is not a fault."""

    class HangingDispatcher(StubDispatcher):
        async def wait_for_new_action(self, issue_id, *, prev_run_id, timeout_seconds, poll_seconds=10):
            await asyncio.sleep(3600)

    w = _build_watcher(dispatcher=HangingDispatcher())
    event = _holding_event()
    entry = _entry_for(event)

    async def driver():
        w.stop()  # simulate shutdown having been requested
        task = asyncio.create_task(
            w._await_and_apply(event, entry, "holding-1", None, {})
        )
        await asyncio.sleep(0)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(driver())

    assert entry.outcome == "cancelled"
    assert entry.outcome != "failed"
    # A cancellation is not counted against any dependency.
    assert w.status.failure_summary() == {}
    assert w._in_flight == {}
    assert not any(call[0] == "error" for call in w._notifier.calls)


def test_cancel_in_flight_retrieves_exceptions_and_clears_slots():
    """Shutdown must not leave an unretrieved task exception behind."""

    class HangingDispatcher(StubDispatcher):
        async def wait_for_new_action(self, issue_id, *, prev_run_id, timeout_seconds, poll_seconds=10):
            await asyncio.sleep(3600)

    dispatcher = HangingDispatcher()
    w = _build_watcher(dispatcher=dispatcher)
    event = _holding_event()

    async def driver():
        await w._handle_trigger(event, planner_result={})
        assert w._in_flight  # dispatched and waiting
        w.stop()
        await w._cancel_in_flight()

    asyncio.run(driver())

    assert w._in_flight == {}
    assert w.status.snapshot()["in_flight"] == []


def test_done_callback_reports_an_exception_that_escaped_the_handler():
    """Net for a fault inside the handler itself — no silent GC-time warning."""

    w = _build_watcher()

    async def driver():
        async def boom():
            raise RuntimeError("escaped handler")

        task = asyncio.create_task(boom())
        task.add_done_callback(
            lambda finished: w._on_tier2_task_done("stock:005930|x", finished)
        )
        await asyncio.gather(task, return_exceptions=True)
        await asyncio.sleep(0)  # let the callback run

    asyncio.run(driver())

    assert _failure_count(w, "tier2_task") == 1
    assert "escaped handler" in (w._last_error or "")


def test_done_callback_ignores_cancellation():
    w = _build_watcher()

    async def driver():
        async def hang():
            await asyncio.sleep(3600)

        task = asyncio.create_task(hang())
        task.add_done_callback(
            lambda finished: w._on_tier2_task_done("stock:005930|x", finished)
        )
        await asyncio.sleep(0)
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        await asyncio.sleep(0)

    asyncio.run(driver())

    assert w.status.failure_summary() == {}


def test_trigger_dispatch_failure_does_not_abort_the_remaining_triggers():
    """One multica outage must not skip the Tier-1 stop-loss queued behind it."""

    class IssueBoomDispatcher(StubDispatcher):
        async def ensure_holding_issue(self, *, code, name, now=None):
            raise RuntimeError("multica unreachable")

    w = _build_watcher(dispatcher=IssueBoomDispatcher(), config=_config(cooldown_seconds=0))

    async def driver():
        # Two triggers in the order a tick would hand them over: the first
        # blows up inside multica, the second must still be processed.
        await w._handle_trigger(_holding_event("111111"), planner_result={})
        await w._handle_trigger(_holding_event("222222"), planner_result={})

    asyncio.run(driver())  # must not raise

    assert _failure_count(w, "multica") == 2  # both contained, both counted
    assert w._in_flight == {}
    assert sum(1 for call in w._notifier.calls if call[0] == "error") == 2


def test_tier1_trigger_failure_is_contained_and_counted(monkeypatch):
    async def boom_sell(client, **kwargs):
        raise RuntimeError("order endpoint down")

    monkeypatch.setattr(watcher_module.order_service, "place_stock_sell_order", boom_sell)
    w = _build_watcher()

    asyncio.run(w._handle_trigger(_tier1_sell_event(), planner_result={}))

    assert _failure_count(w, "order") == 1
    assert any(call[0] == "error" for call in w._notifier.calls)


# -- failure attribution / sanitization -----------------------------------


def test_open_order_fetch_failure_degrades_instead_of_aborting_the_tick(monkeypatch):
    """Losing this query costs stale-cancel detection, not the whole tick."""

    w = _build_watcher()

    async def boom_fetch():
        raise ConnectionError("account endpoint timed out")

    async def fake_plan(*args, **kwargs):
        return {
            "success": True,
            "holdings": [],
            "regime": {"regime": "neutral"},
            "candidate_rows": [],
            "portfolio": {"open_order_count": 3},
        }

    monkeypatch.setattr(w, "_fetch_open_orders", boom_fetch)
    monkeypatch.setattr(watcher_module, "plan_intraday_momentum_strategy", fake_plan)

    asyncio.run(w._tick())  # must not raise

    assert _failure_count(w, "account") == 1
    assert w._api_failure_count == 1
    assert w.status.snapshot()["cycle_count"] == 1  # the tick still completed


def test_planner_failure_is_attributed_to_the_planner(monkeypatch):
    w = _build_watcher()

    async def boom_plan(*args, **kwargs):
        raise RuntimeError("planner blew up")

    monkeypatch.setattr(watcher_module, "plan_intraday_momentum_strategy", boom_plan)

    with pytest.raises(RuntimeError):
        asyncio.run(w._tick())

    assert _failure_count(w, "planner") == 1
    assert w._api_failure_count == 1


def test_sanitize_error_detail_redacts_credentials():
    sanitize = watcher_module.sanitize_error_detail

    assert "sk-live-abcdef123" not in sanitize(
        RuntimeError("auth failed: Bearer sk-live-abcdef123")
    )
    assert "hunter2" not in sanitize(RuntimeError("multica --token=hunter2 failed"))
    assert "s3cr3t" not in sanitize(RuntimeError('{"secretkey": "s3cr3t"}'))
    # The exception type survives so the log stays diagnosable.
    assert sanitize(ConnectionError("boom")).startswith("ConnectionError: ")


def test_sanitize_error_detail_flattens_and_truncates():
    sanitize = watcher_module.sanitize_error_detail

    flattened = sanitize(RuntimeError("line one\n  line two\n\tline three"))
    assert "\n" not in flattened
    assert flattened == "RuntimeError: line one line two line three"

    long = sanitize(RuntimeError("x" * 5000))
    assert len(long) <= 300
    assert long.endswith("…")


def test_failure_counts_are_exposed_on_state():
    w = _build_watcher()
    w._record_failure("market", ConnectionError("quote down"))
    w._record_failure("market", ConnectionError("quote down again"))

    failures = w.status.snapshot()["failures"]
    assert failures["market"]["count"] == 2
    assert "quote down again" in failures["market"]["last_detail"]
    assert failures["market"]["last_at"]


def test_escaping_tier2_task_is_retrieved_not_left_for_gc():
    """The literal P1-2 requirement: no "Task exception was never retrieved".

    Simulates the worst case — the handler inside `_await_and_apply` itself
    failing — so only the done-callback can retrieve the exception. If it
    didn't, asyncio would report it through the loop exception handler when
    the task is garbage collected.
    """

    import gc

    w = _build_watcher()
    loop_errors: list[dict] = []

    async def escaping(*args, **kwargs):
        raise RuntimeError("handler itself failed")

    async def driver():
        asyncio.get_running_loop().set_exception_handler(
            lambda loop, context: loop_errors.append(context)
        )
        w._await_and_apply = escaping  # type: ignore[assignment]
        await w._handle_trigger(_holding_event(), planner_result={})
        tasks = [slot.task for slot in w._in_flight.values()]
        assert tasks, "dispatch should have created a task"
        await asyncio.gather(*tasks, return_exceptions=True)
        await asyncio.sleep(0)  # let the done-callback run
        del tasks
        gc.collect()
        await asyncio.sleep(0)

    asyncio.run(driver())

    assert loop_errors == []  # nothing was left for asyncio to complain about
    assert _failure_count(w, "tier2_task") == 1
    # The callback also frees the slot the escaped body never cleaned up.
    assert w._in_flight == {}
    assert w.status.snapshot()["in_flight"] == []


def test_a_submitted_order_is_never_relabelled_failed(monkeypatch):
    """A fault *after* the order landed must not report it as dead.

    The order state is the operator's ground truth for whether they have a
    live position; a Discord push failing afterwards is a notification bug,
    not an order failure.
    """

    class ExplodingNotifier(StubNotifier):
        async def success(self, title, description):
            raise RuntimeError("discord exploded")

    async def fake_sell(client, **kwargs):
        return _ok_order(order_no="99")

    monkeypatch.setattr(watcher_module.order_service, "place_stock_sell_order", fake_sell)
    w = _build_watcher(dispatcher=StubDispatcher(action="CUT_LOSS"))
    w._notifier = ExplodingNotifier()  # type: ignore[assignment]
    event = _holding_event()
    entry = _entry_for(event)

    asyncio.run(w._await_and_apply(event, entry, "holding-1", None, {}))

    assert entry.outcome == "submitted"  # not "failed"
    # The fault is still counted (stage attribution is coarse — the apply
    # stage owns everything after `_apply_action`), it just doesn't get to
    # overwrite the order's real outcome.
    assert _failure_count(w, "order") == 1
    assert w._in_flight == {}


# -- consecutive-failure counter semantics --------------------------------
#
# `_api_failure_count` gates the risk-manager health trigger, so it has to
# mean "consecutive broken cycles". Resetting it the instant the planner
# succeeded made a permanently-failing account query bump it 0 → 1 on every
# single tick — the threshold was unreachable and the alarm never armed.


def _healthy_planner_result(open_order_count: int = 2) -> dict:
    return {
        "success": True,
        "holdings": [],
        "regime": {"regime": "neutral"},
        "candidate_rows": [],
        "portfolio": {"open_order_count": open_order_count},
    }


def test_persistent_open_order_failure_reaches_the_api_failure_threshold(monkeypatch):
    w = _build_watcher(config=_config(api_failure_threshold=3))

    async def boom_fetch():
        raise ConnectionError("account endpoint timed out")

    async def fake_plan(*args, **kwargs):
        return _healthy_planner_result()

    monkeypatch.setattr(w, "_fetch_open_orders", boom_fetch)
    monkeypatch.setattr(watcher_module, "plan_intraday_momentum_strategy", fake_plan)

    async def driver():
        counts = []
        for _ in range(3):
            await w._tick()
            counts.append(w._api_failure_count)
        await w._cancel_in_flight()
        return counts

    counts = asyncio.run(driver())

    assert counts == [1, 2, 3]  # accumulates instead of pinning at 1 forever
    assert _failure_count(w, "account") == 3
    # Reaching the threshold is the whole point: the risk-manager health
    # trigger finally fires.
    assert any(
        entry["trigger_type"] == "api_failures" for entry in w.status.recent()
    )


def test_healthy_cycle_resets_the_consecutive_counter(monkeypatch):
    w = _build_watcher(config=_config(api_failure_threshold=3))
    broken = {"account": True}

    async def maybe_boom_fetch():
        if broken["account"]:
            raise ConnectionError("account endpoint timed out")
        return []

    async def fake_plan(*args, **kwargs):
        return _healthy_planner_result()

    monkeypatch.setattr(w, "_fetch_open_orders", maybe_boom_fetch)
    monkeypatch.setattr(watcher_module, "plan_intraday_momentum_strategy", fake_plan)

    async def driver():
        for _ in range(2):
            await w._tick()
        assert w._api_failure_count == 2
        broken["account"] = False
        await w._tick()  # every required path healthy again
        await w._cancel_in_flight()

    asyncio.run(driver())

    assert w._api_failure_count == 0
    # The cumulative category counter is history — a recovery does not erase it.
    assert _failure_count(w, "account") == 2


def test_multiple_broken_paths_in_one_cycle_count_once(monkeypatch):
    """The counter measures consecutive broken *cycles*, not failures."""

    w = _build_watcher()

    async def boom_fetch():
        raise ConnectionError("account down")

    async def failing_plan(*args, **kwargs):
        result = _healthy_planner_result()
        result["success"] = False
        result["message"] = "planner degraded"
        return result

    monkeypatch.setattr(w, "_fetch_open_orders", boom_fetch)
    monkeypatch.setattr(watcher_module, "plan_intraday_momentum_strategy", failing_plan)

    async def driver():
        await w._tick()
        await w._cancel_in_flight()

    asyncio.run(driver())

    assert w._api_failure_count == 1  # one cycle, one increment — not two
    # ...while both broken paths stay individually attributed.
    assert _failure_count(w, "planner") == 1
    assert _failure_count(w, "account") == 1


# -- daily new-entry circuit breaker (P0-1) -------------------------------
#
# THE invariant: the breaker blocks opening new exposure and nothing else.
# A breaker that could block an exit would turn a bad day into an unbounded
# one, so the sell/stop/take/cancel paths are asserted explicitly here.


def _tripped_breaker(**limits) -> DailyEntryBreaker:
    """A breaker already latched on a KRW loss, with no filesystem state."""

    breaker = DailyEntryBreaker(
        DailyRiskLimits(loss_source_verified=True, max_daily_loss_krw=50_000, **limits), state_path=None
    )
    breaker.observe(
        watcher_module.read_account_daily_snapshot(
            {"daily_pl_krw": -60_000, "estimated_assets": 1_000_000}
        )
    )
    assert breaker.tripped is True
    return breaker


def test_breaker_blocks_a_new_buy(monkeypatch):
    async def fake_buy(client, **kwargs):
        raise AssertionError("breaker is tripped — must not buy")

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)
    w = _build_watcher(breaker=_tripped_breaker())
    planner = {"portfolio": {"position_budget": 100_000, "max_positions": 3}}

    result = asyncio.run(w._apply_action(_candidate_event(), "TIER1", planner))

    assert result.state == "skipped"
    assert result.attempted is False
    assert "서킷브레이커" in (result.reason or "")


def test_breaker_never_blocks_a_tier1_stop_loss(monkeypatch):
    """The whole point: protective exits keep working while entries are shut."""

    sells: list[dict] = []

    async def fake_sell(client, **kwargs):
        sells.append(kwargs)
        return _ok_order()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_sell_order", fake_sell)
    w = _build_watcher(breaker=_tripped_breaker())
    event = _tier1_sell_event()

    result = asyncio.run(w._execute_tier1(event, _entry_for(event)))

    assert result.state == "submitted"
    assert len(sells) == 1


def test_breaker_never_blocks_a_tier1_stale_order_cancel(monkeypatch):
    cancels: list[dict] = []

    async def fake_cancel(client, **kwargs):
        cancels.append(kwargs)
        return _ok_order()

    monkeypatch.setattr(watcher_module.order_service, "cancel_stock_order", fake_cancel)
    w = _build_watcher(breaker=_tripped_breaker())
    event = TriggerEvent(
        trigger_type="stale_unfilled_order",
        tier=1,
        scope="stock",
        target_role=ROLE_SELF,
        stock_code="005930",
        stock_name="삼성전자",
        snapshot={"qty": "10", "order_no": "OR-1"},
        detected_at=datetime.now(KST),
        reason="stale",
        suggested_action="cancel_order",
        metadata={"order_no": "OR-1"},
    )

    result = asyncio.run(w._execute_tier1(event, _entry_for(event)))

    assert result.state == "submitted"
    assert len(cancels) == 1


def test_breaker_never_blocks_agent_sell_actions(monkeypatch):
    sells: list[dict] = []

    async def fake_sell(client, **kwargs):
        sells.append(kwargs)
        return _ok_order()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_sell_order", fake_sell)
    w = _build_watcher(breaker=_tripped_breaker())

    # One stock per action. Reusing a single 10-share holding for all four
    # would run into oversell protection — a separate mechanism, tested on its
    # own — and would say nothing about whether the breaker gates exits.
    for code, action in zip(
        ("111111", "222222", "333333", "444444"),
        ("TRIM", "TAKE_PROFIT", "CUT_LOSS", "ROTATE"),
    ):
        result = asyncio.run(w._apply_action(_holding_event(code), action, {}))
        assert result.state == "submitted", action

    assert len(sells) == 4


def test_buy_allowed_before_the_threshold_and_blocked_after(monkeypatch):
    """Drive it the way a session does: through `_tick`'s account observation."""

    buys: list[dict] = []

    async def fake_buy(client, **kwargs):
        buys.append(kwargs)
        return _ok_order()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)

    daily_pl = {"value": -10_000}  # 1% of a 1M account

    async def fake_plan(*args, **kwargs):
        return {
            "success": True,
            "holdings": [],
            "regime": {"regime": "neutral"},
            "candidate_rows": [],
            "portfolio": {
                "open_order_count": 0,
                "estimated_assets": 1_000_000,
                "daily_pl_krw": daily_pl["value"],
                "position_budget": 100_000,
                "max_positions": 3,
            },
        }

    monkeypatch.setattr(watcher_module, "plan_intraday_momentum_strategy", fake_plan)
    w = _build_watcher(
        breaker=DailyEntryBreaker(
            DailyRiskLimits(loss_source_verified=True, max_daily_loss_pct=3.0), state_path=None
        )
    )
    planner = {"portfolio": {"position_budget": 100_000, "max_positions": 3}}

    async def driver():
        await w._tick(now=datetime(2026, 7, 27, 10, 0, tzinfo=KST))
        # -1.0% — under the limit
        before = await w._apply_action(_candidate_event("111111"), "TIER1", planner)

        daily_pl["value"] = -35_000  # -3.5% — over the limit
        await w._tick(now=datetime(2026, 7, 27, 11, 0, tzinfo=KST))
        after = await w._apply_action(_candidate_event("222222"), "TIER1", planner)

        await w._cancel_in_flight()
        return before, after

    before, after = asyncio.run(driver())

    assert before.state == "submitted"
    assert after.state == "skipped"
    assert len(buys) == 1
    assert w._breaker.tripped is True
    # The operator gets told, and told what still works.
    assert any(
        "서킷브레이커" in call[1] and call[0] == "error" for call in w._notifier.calls
    )


def test_missing_account_data_blocks_buys_but_not_sells(monkeypatch):
    """Fail closed on entries; protective exits are never data-gated."""

    sells: list[dict] = []

    async def fake_buy(client, **kwargs):
        raise AssertionError("no account data — must not buy")

    async def fake_sell(client, **kwargs):
        sells.append(kwargs)
        return _ok_order()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)
    monkeypatch.setattr(watcher_module.order_service, "place_stock_sell_order", fake_sell)

    async def fake_plan(*args, **kwargs):
        return {
            "success": True,
            "holdings": [],
            "regime": {"regime": "neutral"},
            "candidate_rows": [],
            # No `daily_pl_krw` at all — the field the breaker needs is gone.
            "portfolio": {"open_order_count": 0, "estimated_assets": 1_000_000},
        }

    monkeypatch.setattr(watcher_module, "plan_intraday_momentum_strategy", fake_plan)
    w = _build_watcher(
        breaker=DailyEntryBreaker(
            DailyRiskLimits(loss_source_verified=True, max_daily_loss_pct=3.0), state_path=None
        )
    )

    async def driver():
        await w._tick(now=datetime(2026, 7, 27, 10, 0, tzinfo=KST))
        buy = await w._apply_action(
            _candidate_event(), "TIER1",
            {"portfolio": {"position_budget": 100_000, "max_positions": 3}},
        )
        sell = await w._apply_action(_holding_event(), "CUT_LOSS", {})
        await w._cancel_in_flight()
        return buy, sell

    buy, sell = asyncio.run(driver())

    assert buy.state == "skipped"
    assert "매도/취소는 허용" in (buy.reason or "")
    assert sell.state == "submitted"  # the exit went through
    assert len(sells) == 1
    # A bad poll is transient — it must not latch the whole session.
    assert w._breaker.tripped is False


def test_new_entry_budget_counts_submitted_and_unknown_orders(monkeypatch):
    """An order whose fate we don't know may well be a real position."""

    responses = [_ok_order(), _lost_response_order()]

    async def fake_buy(client, **kwargs):
        return responses.pop(0)

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)
    w = _build_watcher(
        breaker=DailyEntryBreaker(
            DailyRiskLimits(max_daily_new_entries=2), state_path=None
        )
    )
    planner = {
        "portfolio": {"position_budget": 100_000, "max_positions": 5},
        "holdings": [],
    }

    first = asyncio.run(w._apply_action(_candidate_event("111111"), "TIER1", planner))
    second = asyncio.run(w._apply_action(_candidate_event("222222"), "TIER1", planner))
    third = asyncio.run(w._apply_action(_candidate_event("333333"), "TIER1", planner))

    assert first.state == "submitted"
    assert second.state == "unknown"  # counted anyway
    assert w._breaker.state.new_entries == 2
    assert third.state == "skipped"
    assert "신규 진입" in (third.reason or "")


def test_adding_to_a_held_position_is_not_a_new_entry(monkeypatch):
    """The budget is on *new positions*, not on order count."""

    async def fake_buy(client, **kwargs):
        return _ok_order()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)
    w = _build_watcher(
        breaker=DailyEntryBreaker(
            DailyRiskLimits(max_daily_new_entries=1), state_path=None
        )
    )
    planner = {
        "portfolio": {"position_budget": 100_000, "max_positions": 3},
        "holdings": [{"stock_code": "123456", "quantity": 1, "current_price": 10000}],
    }

    result = asyncio.run(w._apply_action(_candidate_event("123456"), "TIER1", planner))

    assert result.state == "submitted"
    assert w._breaker.state.new_entries == 0  # topped up, not opened


def test_disabled_breaker_leaves_the_buy_path_untouched(monkeypatch):
    """Default config must behave exactly as it did before this feature."""

    buys: list[dict] = []

    async def fake_buy(client, **kwargs):
        buys.append(kwargs)
        return _ok_order()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)
    w = _build_watcher()  # all limits 0
    planner = {"portfolio": {"position_budget": 100_000, "max_positions": 3}}

    assert w._breaker.enabled is False
    result = asyncio.run(w._apply_action(_candidate_event(), "TIER1", planner))

    assert result.state == "submitted"
    assert len(buys) == 1


def test_breaker_state_is_published_on_state(monkeypatch):
    async def fake_plan(*args, **kwargs):
        return {
            "success": True,
            "holdings": [],
            "regime": {"regime": "neutral"},
            "candidate_rows": [],
            "portfolio": {
                "open_order_count": 0,
                "estimated_assets": 1_000_000,
                "daily_pl_krw": -40_000,
                "daily_pl_pct_broker": -9.9,
            },
        }

    monkeypatch.setattr(watcher_module, "plan_intraday_momentum_strategy", fake_plan)
    w = _build_watcher(
        breaker=DailyEntryBreaker(
            DailyRiskLimits(loss_source_verified=True, max_daily_loss_pct=3.0), state_path=None
        )
    )

    async def driver():
        await w._tick(now=datetime(2026, 7, 27, 10, 0, tzinfo=KST))
        await w._cancel_in_flight()

    asyncio.run(driver())

    published = w.status.snapshot()["daily_entry_breaker"]
    assert published["enabled"] is True
    assert published["tripped"] is True
    assert published["trip_code"] == "daily_loss_pct"
    assert published["limit_value"] == 3.0
    assert published["observed_value"] == 4.0
    assert published["tripped_at"]
    assert published["resets_on"]
    assert published["account"]["broker_daily_pl_pct"] == -9.9


def test_unusable_breaker_state_blocks_buys_but_not_sells(monkeypatch, tmp_path):
    """Review correction: a state we cannot trust fails NEW ENTRIES closed.

    We may be sitting on a latch we failed to read, so buying again would
    silently undo a trip. Exits are never gated by it.
    """

    sells: list[dict] = []

    async def fake_buy(client, **kwargs):
        raise AssertionError("breaker state unusable — must not buy")

    async def fake_sell(client, **kwargs):
        sells.append(kwargs)
        return _ok_order()

    async def fake_cancel(client, **kwargs):
        return _ok_order()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)
    monkeypatch.setattr(watcher_module.order_service, "place_stock_sell_order", fake_sell)
    monkeypatch.setattr(watcher_module.order_service, "cancel_stock_order", fake_cancel)

    corrupt = tmp_path / "daily_risk_state.json"
    corrupt.write_text("{not json", encoding="utf-8")
    w = _build_watcher(
        breaker=DailyEntryBreaker(
            DailyRiskLimits(max_daily_new_entries=5), state_path=corrupt
        )
    )

    buy = asyncio.run(
        w._apply_action(
            _candidate_event(), "TIER1",
            {"portfolio": {"position_budget": 100_000, "max_positions": 3}},
        )
    )
    assert buy.state == "skipped"
    assert buy.attempted is False
    assert "매도/취소는 허용" in (buy.reason or "")

    # Every protective path still goes through. Distinct codes, so the
    # oversell guard (a separate mechanism, tested below) stays out of it.
    sell = asyncio.run(w._apply_action(_holding_event("111111"), "CUT_LOSS", {}))
    assert sell.state == "submitted"

    stop_event = _tier1_sell_event()
    stop = asyncio.run(w._execute_tier1(stop_event, _entry_for(stop_event)))
    assert stop.state == "submitted"

    cancel_event = TriggerEvent(
        trigger_type="stale_unfilled_order",
        tier=1,
        scope="stock",
        target_role=ROLE_SELF,
        stock_code="005930",
        stock_name="삼성전자",
        snapshot={"qty": "10", "order_no": "OR-1"},
        detected_at=datetime.now(KST),
        reason="stale",
        suggested_action="cancel_order",
        metadata={"order_no": "OR-1"},
    )
    cancel = asyncio.run(w._execute_tier1(cancel_event, _entry_for(cancel_event)))
    assert cancel.state == "submitted"
    assert len(sells) == 2  # agent CUT_LOSS + tier-1 stop


def test_unsupported_calendar_blocks_buy_but_all_protective_paths_continue(
    monkeypatch,
):
    """Calendar fail-closed is entry-only, even when risk limits are disabled."""

    sells: list[dict] = []
    cancels: list[dict] = []

    async def fake_buy(client, **kwargs):
        raise AssertionError("unsupported calendar must not submit a buy")

    async def fake_sell(client, **kwargs):
        sells.append(kwargs)
        return _ok_order()

    async def fake_cancel(client, **kwargs):
        cancels.append(kwargs)
        return _ok_order()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)
    monkeypatch.setattr(watcher_module.order_service, "place_stock_sell_order", fake_sell)
    monkeypatch.setattr(watcher_module.order_service, "cancel_stock_order", fake_cancel)

    breaker = DailyEntryBreaker(
        DailyRiskLimits(),
        state_path=None,
        now=datetime(2027, 1, 4, 10, 0, tzinfo=KST),
    )
    w = _build_watcher(breaker=breaker)

    buy = asyncio.run(
        w._apply_action(
            _candidate_event(),
            "TIER1",
            {"portfolio": {"position_budget": 100_000, "max_positions": 3}},
        )
    )
    assert buy.state == "skipped"
    assert breaker.check_new_entry().code == BLOCK_CALENDAR_UNCERTAIN

    agent_sell = asyncio.run(
        w._apply_action(_holding_event("111111"), "CUT_LOSS", {})
    )
    assert agent_sell.state == "submitted"

    stop_event = _tier1_sell_event()
    stop = asyncio.run(w._execute_tier1(stop_event, _entry_for(stop_event)))
    assert stop.state == "submitted"

    cancel_event = TriggerEvent(
        trigger_type="stale_unfilled_order",
        tier=1,
        scope="stock",
        target_role=ROLE_SELF,
        stock_code="333333",
        stock_name="보호취소",
        snapshot={"qty": "10", "order_no": "OR-CALENDAR"},
        detected_at=datetime(2027, 1, 4, 10, 0, tzinfo=KST),
        reason="stale",
        suggested_action="cancel_order",
        metadata={"order_no": "OR-CALENDAR"},
    )
    cancel = asyncio.run(w._execute_tier1(cancel_event, _entry_for(cancel_event)))
    assert cancel.state == "submitted"
    assert len(sells) == 2
    assert len(cancels) == 1


def test_unusable_breaker_state_is_alerted_once(monkeypatch, tmp_path):
    async def fake_plan(*args, **kwargs):
        return {
            "success": True,
            "holdings": [],
            "regime": {"regime": "neutral"},
            "candidate_rows": [],
            "portfolio": {
                "open_order_count": 0,
                "estimated_assets": 1_000_000,
                "daily_pl_krw": -100,
            },
        }

    monkeypatch.setattr(watcher_module, "plan_intraday_momentum_strategy", fake_plan)
    corrupt = tmp_path / "daily_risk_state.json"
    corrupt.write_text("{not json", encoding="utf-8")
    w = _build_watcher(
        breaker=DailyEntryBreaker(
            DailyRiskLimits(loss_source_verified=True, max_daily_loss_krw=50_000), state_path=corrupt
        )
    )

    async def driver():
        await w._tick()
        await w._tick()
        await w._cancel_in_flight()

    asyncio.run(driver())

    alerts = [
        c for c in w._notifier.calls
        if c[0] == "error" and "상태 신뢰 불가" in c[1]
    ]
    assert len(alerts) == 1  # persistent fault, one page
    assert w.status.snapshot()["daily_entry_breaker"]["state_error"]


def test_weekend_restart_keeps_the_breaker_shut_for_new_buys(monkeypatch, tmp_path):
    """End to end for the calendar fix: Friday's latch still blocks buys
    after a Saturday pod restart, while exits keep working."""

    async def fake_buy(client, **kwargs):
        raise AssertionError("Friday's latch must survive the weekend")

    async def fake_sell(client, **kwargs):
        return _ok_order()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)
    monkeypatch.setattr(watcher_module.order_service, "place_stock_sell_order", fake_sell)

    state_path = tmp_path / "daily_risk_state.json"
    limits = DailyRiskLimits(loss_source_verified=True, max_daily_loss_krw=50_000)

    friday = DailyEntryBreaker(
        limits, state_path=state_path,
        now=datetime(2026, 7, 31, 14, 0, tzinfo=KST),
    )
    friday.observe(
        watcher_module.read_account_daily_snapshot(
            {"daily_pl_krw": -60_000, "estimated_assets": 1_000_000}
        )
    )

    # Pod restarts on Saturday and rebuilds the watcher from the same volume.
    w = _build_watcher(
        breaker=DailyEntryBreaker(
            limits, state_path=state_path,
            now=datetime(2026, 8, 1, 10, 0, tzinfo=KST),
        )
    )

    buy = asyncio.run(
        w._apply_action(
            _candidate_event(), "TIER1",
            {"portfolio": {"position_budget": 100_000, "max_positions": 3}},
        )
    )
    sell = asyncio.run(w._apply_action(_holding_event(), "CUT_LOSS", {}))

    assert buy.state == "skipped"
    assert sell.state == "submitted"
    assert w._breaker.state.trading_day == "2026-07-31"


# -- loss-source verification, through the real order routing --------------


def _unverified_loss_watcher(**limits):
    """Watcher whose loss limit is armed but NOT acknowledged (the default)."""

    return _build_watcher(
        breaker=DailyEntryBreaker(
            DailyRiskLimits(max_daily_loss_krw=50_000, **limits), state_path=None
        )
    )


def test_unverified_loss_limit_blocks_buys_but_not_exits(monkeypatch):
    """Below-threshold, cleanly-parsed loss data still blocks new entries.

    A number whose meaning is unestablished cannot show the account is safe,
    so we refuse to open exposure on it — while every protective path stays
    completely unrestricted.
    """

    sells: list[dict] = []

    async def fake_buy(client, **kwargs):
        raise AssertionError("loss source unverified — must not buy")

    async def fake_sell(client, **kwargs):
        sells.append(kwargs)
        return _ok_order()

    async def fake_cancel(client, **kwargs):
        return _ok_order()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)
    monkeypatch.setattr(watcher_module.order_service, "place_stock_sell_order", fake_sell)
    monkeypatch.setattr(watcher_module.order_service, "cancel_stock_order", fake_cancel)

    w = _unverified_loss_watcher()
    # A healthy, well-under-threshold account reading.
    w._breaker.observe(
        watcher_module.read_account_daily_snapshot(
            {"daily_pl_krw": -1_000, "estimated_assets": 1_000_000}
        )
    )

    buy = asyncio.run(
        w._apply_action(
            _candidate_event(), "TIER1",
            {"portfolio": {"position_budget": 100_000, "max_positions": 3}},
        )
    )
    assert buy.state == "skipped"
    assert buy.attempted is False
    assert "검증되지 않음" in (buy.reason or "")

    # Agent sell, tier-1 stop-loss and tier-1 stale cancel all go through.
    # Distinct codes so the oversell guard is not what is being measured.
    assert asyncio.run(
        w._apply_action(_holding_event("111111"), "CUT_LOSS", {})
    ).state == "submitted"

    stop_event = _tier1_sell_event()
    assert asyncio.run(
        w._execute_tier1(stop_event, _entry_for(stop_event))
    ).state == "submitted"

    cancel_event = TriggerEvent(
        trigger_type="stale_unfilled_order",
        tier=1,
        scope="stock",
        target_role=ROLE_SELF,
        stock_code="005930",
        stock_name="삼성전자",
        snapshot={"qty": "10", "order_no": "OR-1"},
        detected_at=datetime.now(KST),
        reason="stale",
        suggested_action="cancel_order",
        metadata={"order_no": "OR-1"},
    )
    assert asyncio.run(
        w._execute_tier1(cancel_event, _entry_for(cancel_event))
    ).state == "submitted"
    assert len(sells) == 2


def test_count_only_limit_still_buys_while_loss_source_unverified(monkeypatch):
    """A count-only configuration needs no broker P&L, so it works today."""

    buys: list[dict] = []

    async def fake_buy(client, **kwargs):
        buys.append(kwargs)
        return _ok_order()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)
    w = _build_watcher(
        breaker=DailyEntryBreaker(
            DailyRiskLimits(max_daily_new_entries=2), state_path=None
        )
    )
    planner = {
        "portfolio": {"position_budget": 100_000, "max_positions": 5},
        "holdings": [],
    }

    first = asyncio.run(w._apply_action(_candidate_event("111111"), "TIER1", planner))
    second = asyncio.run(w._apply_action(_candidate_event("222222"), "TIER1", planner))
    third = asyncio.run(w._apply_action(_candidate_event("333333"), "TIER1", planner))

    assert first.state == "submitted"
    assert second.state == "submitted"
    assert third.state == "skipped"  # its own count limit, not the metadata gate
    assert "신규 진입" in (third.reason or "")
    assert len(buys) == 2


def test_verified_acknowledgement_restores_threshold_buying(monkeypatch):
    async def fake_buy(client, **kwargs):
        return _ok_order()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)
    w = _build_watcher(
        breaker=DailyEntryBreaker(
            DailyRiskLimits(max_daily_loss_krw=50_000, loss_source_verified=True),
            state_path=None,
        )
    )
    w._breaker.observe(
        watcher_module.read_account_daily_snapshot(
            {"daily_pl_krw": -1_000, "estimated_assets": 1_000_000}
        )
    )
    planner = {"portfolio": {"position_budget": 100_000, "max_positions": 3}}

    assert asyncio.run(
        w._apply_action(_candidate_event(), "TIER1", planner)
    ).state == "submitted"


def test_unverified_loss_source_is_alerted_once(monkeypatch):
    """Otherwise the operator just sees the watcher never entering anything."""

    async def fake_plan(*args, **kwargs):
        return {
            "success": True,
            "holdings": [],
            "regime": {"regime": "neutral"},
            "candidate_rows": [],
            "portfolio": {
                "open_order_count": 0,
                "estimated_assets": 1_000_000,
                "daily_pl_krw": -1_000,
            },
        }

    monkeypatch.setattr(watcher_module, "plan_intraday_momentum_strategy", fake_plan)
    w = _unverified_loss_watcher()

    async def driver():
        await w._tick()
        await w._tick()
        await w._cancel_in_flight()

    asyncio.run(driver())

    alerts = [c for c in w._notifier.calls if c[0] == "error" and "미검증" in c[1]]
    assert len(alerts) == 1
    published = w.status.snapshot()["daily_entry_breaker"]
    assert published["loss_source_status"] == "unverified"
    assert published["loss_limits_enforced"] is False


def test_watcher_config_defaults_to_unverified():
    w = _build_watcher()
    assert w._config.daily_loss_source_verified is False
    assert w._breaker.limits.loss_source_verified is False


# -- order-intent ledger, through the real order routing (P0-2) ------------
#
# The scenarios that made a duplicate live order possible: a crash between
# deciding and sending, a broker that booked an order whose response we lost,
# a partial fill, and a stop-loss re-firing while an earlier exit is working.



def _seed_intent(ledger, **kw):
    """Seed a ledger row directly and return the created attempt."""

    reg = ledger.record_intent(**kw)
    assert reg.may_submit, reg.outcome
    return reg.intent


def _ledger_watcher(tmp_path=None, **kwargs):
    ledger = OrderLedger(tmp_path / "order_ledger.sqlite3" if tmp_path else None)
    return _build_watcher(ledger=ledger, **kwargs), ledger


def test_ledger_view_narrows_recent_to_one_day_but_keeps_every_unresolved():
    """What `/ledger` serves the agents in place of `kubectl exec` + SQLite."""

    w, ledger = _ledger_watcher()
    earlier = _seed_intent(
        ledger, stock_code="005930", side="buy", quantity=1, price=100_000,
        trading_day="2026-09-22",
    )
    today = _seed_intent(
        ledger, stock_code="000660", side="buy", quantity=1, price=200_000,
        trading_day="2026-09-23",
    )

    view = w.ledger_view(limit=500, trading_day="2026-09-23")

    assert view["available"] is True
    assert view["trading_day"] == "2026-09-23"
    assert [row["intent_id"] for row in view["recent"]] == [today.intent_id]
    # An unresolved intent blocks the next buy whatever day it came from.
    assert {row["intent_id"] for row in view["unresolved"]} == {
        earlier.intent_id, today.intent_id,
    }


def test_ledger_view_without_a_ledger_says_so():
    w = _build_watcher()
    w._ledger = None

    view = w.ledger_view()

    assert view["available"] is False


def test_buy_commits_an_intent_before_the_order_goes_out(monkeypatch):
    seen: list[list] = []

    async def fake_buy(client, **kwargs):
        # Whatever the API sees, the intent must already be on disk.
        seen.append(w._ledger.unresolved(stock_code="123456"))
        return _ok_order(buy_order_result={"ord_no": "0000042"})

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)
    w, ledger = _ledger_watcher()
    planner = {"portfolio": {"position_budget": 100_000, "max_positions": 3}}

    result = asyncio.run(w._apply_action(_candidate_event(), "TIER1", planner))

    assert [i.state for i in seen[0]] == ["INTENDED"]
    assert result.state == "submitted"
    row = ledger.unresolved(stock_code="123456")[0]
    assert row.state == STATE_SUBMITTED
    assert row.order_no == "42"


def test_unresolved_intent_blocks_a_duplicate_buy(monkeypatch):
    calls: list[dict] = []

    async def fake_buy(client, **kwargs):
        calls.append(kwargs)
        return _ok_order()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)
    w, _ = _ledger_watcher()
    planner = {"portfolio": {"position_budget": 100_000, "max_positions": 3}}

    first = asyncio.run(w._apply_action(_candidate_event(), "TIER1", planner))
    second = asyncio.run(w._apply_action(_candidate_event(), "TIER1", planner))

    assert first.state == "submitted"
    assert second.state == "skipped"
    assert "미종결 매수 intent" in (second.reason or "")
    assert len(calls) == 1


def test_restart_still_blocks_a_buy_recorded_by_the_previous_process(
    monkeypatch, tmp_path
):
    """The core P0-2 fix: exposure now outlives the process."""

    calls: list[dict] = []

    async def fake_buy(client, **kwargs):
        calls.append(kwargs)
        return _ok_order(buy_order_result={"ord_no": "42"})

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)
    planner = {"portfolio": {"position_budget": 100_000, "max_positions": 3}}

    before, ledger = _ledger_watcher(tmp_path)
    assert asyncio.run(
        before._apply_action(_candidate_event(), "TIER1", planner)
    ).state == "submitted"
    ledger.close()  # pod dies

    after, _ = _ledger_watcher(tmp_path)
    result = asyncio.run(after._apply_action(_candidate_event(), "TIER1", planner))

    assert result.state == "skipped"
    assert len(calls) == 1  # not re-bought


def test_lost_response_blocks_the_next_buy_and_is_not_resubmitted(monkeypatch):
    calls: list[dict] = []

    async def fake_buy(client, **kwargs):
        calls.append(kwargs)
        return _lost_response_order()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)
    w, ledger = _ledger_watcher()
    planner = {"portfolio": {"position_budget": 100_000, "max_positions": 3}}

    first = asyncio.run(w._apply_action(_candidate_event(), "TIER1", planner))
    second = asyncio.run(w._apply_action(_candidate_event(), "TIER1", planner))

    assert first.state == "unknown"
    assert ledger.unresolved(stock_code="123456")[0].state == STATE_UNKNOWN
    assert second.state == "skipped"
    assert len(calls) == 1  # never resubmitted off an unknown


def test_rejected_buy_may_be_retried(monkeypatch):
    """A rejection proves the broker holds nothing, so the slot reopens."""

    calls: list[dict] = []
    responses = [_rejected_order(), _ok_order()]

    async def fake_buy(client, **kwargs):
        calls.append(kwargs)
        return responses.pop(0)

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)
    w, _ = _ledger_watcher()
    planner = {"portfolio": {"position_budget": 100_000, "max_positions": 3}}

    first = asyncio.run(w._apply_action(_candidate_event(), "TIER1", planner))
    second = asyncio.run(w._apply_action(_candidate_event(), "TIER1", planner))

    assert first.state == "failed"
    assert second.state == "submitted"
    assert len(calls) == 2


def test_partial_fill_only_commits_the_remainder_to_the_budget(monkeypatch):
    async def fake_buy(client, **kwargs):
        return _ok_order(buy_order_result={"ord_no": "42"})

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)
    w, ledger = _ledger_watcher()
    planner = {"portfolio": {"position_budget": 100_000, "max_positions": 3}}

    asyncio.run(w._apply_action(_candidate_event(), "TIER1", planner))  # 10 @ 10000
    ledger.reconcile(
        open_orders=[
            {
                "ord_no": "42", "stk_cd": "123456", "io_tp_nm": "매수",
                "ord_qty": "10", "ord_pric": "10000",
                "cntr_qty": "4", "oso_qty": "6", "ord_stt": "접수",
            }
        ]
    )

    row = ledger.unresolved(stock_code="123456")[0]
    assert row.state == STATE_PARTIAL
    assert row.filled_quantity == 4
    assert ledger.unresolved_notional("123456") == 60_000


def test_ledger_failure_fails_buys_closed_but_not_exits(monkeypatch):
    sells: list[dict] = []

    async def fake_buy(client, **kwargs):
        raise AssertionError("ledger is down — must not buy")

    async def fake_sell(client, **kwargs):
        sells.append(kwargs)
        return _ok_order()

    async def fake_cancel(client, **kwargs):
        return _ok_order()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)
    monkeypatch.setattr(watcher_module.order_service, "place_stock_sell_order", fake_sell)
    monkeypatch.setattr(watcher_module.order_service, "cancel_stock_order", fake_cancel)

    w, ledger = _ledger_watcher()
    ledger.close()  # storage gone mid-session

    buy = asyncio.run(
        w._apply_action(
            _candidate_event(), "TIER1",
            {"portfolio": {"position_budget": 100_000, "max_positions": 3}},
        )
    )
    assert buy.state == "skipped"
    assert buy.attempted is False
    assert "원장" in (buy.reason or "")
    # The operator is paged, and the message names the cause (title or body).
    assert any(
        c[0] == "error" and "원장" in (c[1] + c[2]) for c in w._notifier.calls
    )

    # A ledger fault must never trap the account in a position.
    assert asyncio.run(
        w._apply_action(_holding_event("111111"), "CUT_LOSS", {})
    ).state == "submitted"

    stop_event = _tier1_sell_event()
    assert asyncio.run(
        w._execute_tier1(stop_event, _entry_for(stop_event))
    ).state == "submitted"
    assert len(sells) == 2


def test_unopenable_ledger_at_construction_fails_buys_closed(monkeypatch, tmp_path):
    blocked = tmp_path / "order_ledger.sqlite3"
    blocked.mkdir()

    async def fake_buy(client, **kwargs):
        raise AssertionError("ledger unavailable — must not buy")

    async def fake_sell(client, **kwargs):
        return _ok_order()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)
    monkeypatch.setattr(watcher_module.order_service, "place_stock_sell_order", fake_sell)
    monkeypatch.setattr(watcher_module, "DEFAULT_STATE_PATH", tmp_path / "state.json")
    monkeypatch.setattr(
        watcher_module.OrderLedger, "__init__",
        lambda self, *a, **k: (_ for _ in ()).throw(OrderLedgerError("boom")),
    )

    w = IntradayWatcher(
        _settings(),
        _config(),
        dispatcher=StubDispatcher(),
        client=object(),
        notifier=StubNotifier(),  # type: ignore[arg-type]
        breaker=DailyEntryBreaker(DailyRiskLimits(), state_path=None),
    )

    assert w._ledger is None
    buy = asyncio.run(
        w._apply_action(
            _candidate_event(), "TIER1",
            {"portfolio": {"position_budget": 100_000, "max_positions": 3}},
        )
    )
    assert buy.state == "skipped"
    # Exits keep working with no ledger at all.
    assert asyncio.run(
        w._apply_action(_holding_event(), "CUT_LOSS", {})
    ).state == "submitted"


def test_network_ledger_blocks_buys_once_but_routes_sell_and_cancel(
    monkeypatch, tmp_path, caplog
):
    buys: list[dict] = []
    sells: list[dict] = []
    cancels: list[dict] = []

    async def fake_buy(client, **kwargs):
        buys.append(kwargs)
        return _ok_order()

    async def fake_sell(client, **kwargs):
        sells.append(kwargs)
        return _ok_order()

    async def fake_cancel(client, **kwargs):
        cancels.append(kwargs)
        return _ok_order()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)
    monkeypatch.setattr(
        watcher_module.order_service, "place_stock_sell_order", fake_sell
    )
    monkeypatch.setattr(watcher_module.order_service, "cancel_stock_order", fake_cancel)
    mountinfo = "36 25 0:32 / / rw,relatime - nfs4 server:/ledger rw\n"

    with caplog.at_level("ERROR"):
        w = IntradayWatcher(
            _settings(),
            _config(),
            dispatcher=StubDispatcher(),
            client=object(),
            notifier=StubNotifier(),  # type: ignore[arg-type]
            state_path=tmp_path / "state.json",
            breaker=DailyEntryBreaker(DailyRiskLimits(), state_path=None),
            ledger_mountinfo_reader=lambda: mountinfo,
        )

    async def no_open_orders():
        return []

    async def no_executions():
        return []

    w._fetch_open_orders = no_open_orders  # type: ignore[assignment]
    w._fetch_executions = no_executions  # type: ignore[assignment]
    planner = {"portfolio": {"position_budget": 100_000, "max_positions": 3}}

    first_buy = asyncio.run(
        w._apply_action(_candidate_event(), "TIER1", planner)
    )
    second_buy = asyncio.run(
        w._apply_action(_candidate_event(), "TIER1", planner)
    )
    sell = asyncio.run(w._apply_action(_holding_event(), "CUT_LOSS", {}))
    cancel_event = TriggerEvent(
        trigger_type="stale_unfilled_order",
        tier=1,
        scope="stock",
        target_role=ROLE_SELF,
        stock_code="005930",
        stock_name="삼성전자",
        snapshot={"qty": "10", "order_no": "OR-1"},
        detected_at=datetime.now(KST),
        reason="stale",
        suggested_action="cancel_order",
        metadata={"order_no": "OR-1"},
    )
    cancel = asyncio.run(w._execute_tier1(cancel_event, _entry_for(cancel_event)))

    assert first_buy.state == second_buy.state == "skipped"
    assert buys == []
    assert sell.state == "submitted"
    assert cancel.state == "submitted"
    assert len(sells) == 1
    assert len(cancels) == 1
    alerts = [call for call in w._notifier.calls if call[0] == "error"]
    assert len(alerts) == 1
    assert "네트워크 파일시스템" in alerts[0][1]
    assert "local block filesystem" in alerts[0][2]
    snapshot = w._ledger_snapshot()
    assert snapshot["available"] is False
    assert snapshot["storage_safety"]["state"] == STORAGE_NETWORK
    assert snapshot["storage_safety"]["blocks_new_entries"] is True
    assert any("network filesystem nfs4" in record.message for record in caplog.records)


# -- oversell protection ---------------------------------------------------


def test_stop_loss_refire_does_not_oversell_over_a_working_sell(monkeypatch):
    """The exact scenario: an earlier exit is still live at the broker."""

    sells: list[dict] = []

    async def fake_sell(client, **kwargs):
        sells.append(kwargs)
        return _ok_order()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_sell_order", fake_sell)
    w, _ = _ledger_watcher()
    # The broker already has all 10 shares working as a sell.
    w._last_open_orders = [
        {"stk_cd": "005930", "io_tp_nm": "매도", "ord_qty": "10", "oso_qty": "10"}
    ]

    event = _tier1_sell_event(quantity=10)
    result = asyncio.run(w._execute_tier1(event, _entry_for(event)))

    assert result.state == "skipped"
    assert "중복 매도" in (result.reason or "")
    assert sells == []


def test_sell_is_clamped_to_the_uncovered_remainder(monkeypatch):
    sells: list[dict] = []

    async def fake_sell(client, **kwargs):
        sells.append(kwargs)
        return _ok_order()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_sell_order", fake_sell)
    w, _ = _ledger_watcher()
    # 4 of the 10 held shares are already working.
    w._last_open_orders = [
        {"stk_cd": "005930", "io_tp_nm": "매도", "ord_qty": "4", "oso_qty": "4"}
    ]

    event = _tier1_sell_event(quantity=10)
    result = asyncio.run(w._execute_tier1(event, _entry_for(event)))

    assert result.state == "submitted"
    assert sells[0]["ord_qty"] == "6"  # not 10


def test_agent_sell_after_our_own_exit_does_not_double_up(monkeypatch):
    """Our own unresolved sell intent counts even before the broker shows it."""

    sells: list[dict] = []

    async def fake_sell(client, **kwargs):
        sells.append(kwargs)
        return _ok_order()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_sell_order", fake_sell)
    w, _ = _ledger_watcher()

    first = asyncio.run(w._apply_action(_holding_event(quantity=10), "TAKE_PROFIT", {}))
    second = asyncio.run(w._apply_action(_holding_event(quantity=10), "CUT_LOSS", {}))

    assert first.state == "submitted"
    assert sells[0]["ord_qty"] == "10"
    assert second.state == "skipped"  # all 10 already spoken for
    assert len(sells) == 1


def test_open_sell_and_ledger_intent_are_not_double_counted(monkeypatch):
    """Right after submit the same order sits in both views; `max`, not sum."""

    sells: list[dict] = []

    async def fake_sell(client, **kwargs):
        sells.append(kwargs)
        return _ok_order()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_sell_order", fake_sell)
    w, _ = _ledger_watcher()

    asyncio.run(w._apply_action(_holding_event(quantity=10), "TRIM", {}))  # sells 5
    # The broker now reports that same 5-share order as working.
    w._last_open_orders = [
        {"stk_cd": "005930", "io_tp_nm": "매도", "ord_qty": "5", "oso_qty": "5"}
    ]

    # 5 of 10 are covered, so a full exit may still sell the other 5.
    second = asyncio.run(w._apply_action(_holding_event(quantity=10), "CUT_LOSS", {}))

    assert second.state == "submitted"
    assert sells[1]["ord_qty"] == "5"


# -- reconciliation wiring -------------------------------------------------


def test_tick_reconciles_against_the_open_orders_it_already_fetched(monkeypatch):
    w, ledger = _ledger_watcher()
    intent = _seed_intent(ledger,
        stock_code="005930", side="buy", quantity=10, price=70000
    )
    ledger.apply_order_result(
        intent.intent_id, submitted=True, unknown=False, order_no="123", reason="ok"
    )

    async def fake_plan(*args, **kwargs):
        return {
            "success": True,
            "holdings": [],
            "regime": {"regime": "neutral"},
            "candidate_rows": [],
            "portfolio": {"open_order_count": 1},
        }

    async def fake_open_orders():
        return [
            {
                "ord_no": "123", "stk_cd": "005930", "io_tp_nm": "매수",
                "ord_qty": "10", "cntr_qty": "10", "oso_qty": "0",
                "ord_stt": "체결",
            }
        ]

    monkeypatch.setattr(watcher_module, "plan_intraday_momentum_strategy", fake_plan)
    monkeypatch.setattr(w, "_fetch_open_orders", fake_open_orders)

    async def driver():
        await w._tick()
        await w._cancel_in_flight()

    asyncio.run(driver())

    assert ledger.get(intent.intent_id).state == STATE_FILLED
    assert w._last_open_orders  # cached for the oversell guard


def test_startup_reconciliation_settles_a_pre_restart_intent(monkeypatch):
    w, ledger = _ledger_watcher()
    intent = _seed_intent(ledger,
        stock_code="005930", side="buy", quantity=10, price=70000
    )
    ledger.apply_order_result(
        intent.intent_id, submitted=False, unknown=True, order_no=None, reason="timeout"
    )

    async def fake_executions():
        return [
            {
                "ord_no": "777", "stk_cd": "005930", "io_tp_nm": "매수",
                "ord_qty": "10", "ord_pric": "70000",
                "cntr_qty": "10", "oso_qty": "0", "ord_stt": "체결",
                "ord_tmd": _broker_now(),
            }
        ]

    monkeypatch.setattr(w, "_fetch_executions", fake_executions)

    asyncio.run(w._reconcile_ledger(fetch_executions=True))

    row = ledger.get(intent.intent_id)
    assert row.state == STATE_FILLED
    assert row.order_no == "777"  # adopted from the broker


def test_state_exposes_the_ledger(monkeypatch):
    w, ledger = _ledger_watcher()
    ledger.record_intent(
        stock_code="005930", side="buy", quantity=10, price=70000
    )

    snapshot = w._ledger_snapshot()

    assert snapshot["available"] is True
    assert snapshot["unresolved_count"] == 1
    assert snapshot["unresolved"][0]["state"] == "INTENDED"


# -- broker reconciliation wiring (Task 4 review correction) ---------------
#
# The ledger's own unit tests can only prove the bookkeeping. These prove the
# watcher actually asks the broker at the moments that matter: before it may
# open exposure, and before it sizes an exit.


def _broker_now() -> str:
    """`ord_tmd` for a row that just happened (YYYYMMDDHHMMSS, KST)."""

    return datetime.now(KST).strftime("%Y%m%d%H%M%S")


def _filled_row(ord_no="123", code="005930", side="매수", qty="10", price="70000"):
    return {
        "ord_no": ord_no, "stk_cd": code, "io_tp_nm": side,
        "ord_qty": qty, "ord_pric": price,
        "cntr_qty": qty, "oso_qty": "0", "ord_stt": "체결",
        "ord_tmd": _broker_now(),
    }


def test_startup_fetches_both_open_orders_and_executions(monkeypatch):
    """An order left working shows up in the open-order query and nowhere
    else — startup used to look only at executions."""

    calls: list[str] = []
    w, ledger = _ledger_watcher()
    ledger.record_intent(
        stock_code="005930", side="buy", quantity=10, price=70000
    )

    async def fake_open_orders():
        calls.append("open_orders")
        return [
            {
                "ord_no": "555", "stk_cd": "005930", "io_tp_nm": "매수",
                "ord_qty": "10", "ord_pric": "70000",
                "cntr_qty": "0", "oso_qty": "10", "ord_stt": "접수",
                "ord_tmd": _broker_now(),
            }
        ]

    async def fake_executions():
        calls.append("executions")
        return []

    monkeypatch.setattr(w, "_fetch_open_orders", fake_open_orders)
    monkeypatch.setattr(w, "_fetch_executions", fake_executions)
    monkeypatch.setattr(w, "_is_market_open", lambda *a, **k: False)
    monkeypatch.setattr(w, "_persist_state", lambda: None)

    async def driver():
        w.stop()  # run() does the startup reconcile, then exits immediately
        await w.run()

    asyncio.run(driver())

    assert calls == ["open_orders", "executions"]
    # The still-working order was adopted rather than left unmatched.
    row = ledger.unresolved(stock_code="005930")[0]
    assert row.order_no == "555"
    assert row.state == "OPEN"


def test_new_buy_reconciles_against_a_fresh_broker_view_first(monkeypatch):
    """A stale intent the broker has already filled must not block forever."""

    buys: list[dict] = []
    calls: list[str] = []

    async def fake_buy(client, **kwargs):
        buys.append(kwargs)
        return _ok_order()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)
    w, ledger = _ledger_watcher()
    # Left over from a previous process, already filled at the broker.
    intent = _seed_intent(ledger,
        stock_code="123456", side="buy", quantity=10, price=10000
    )
    ledger.apply_order_result(
        intent.intent_id, submitted=True, unknown=False, order_no="900", reason="ok"
    )

    async def fake_open_orders():
        calls.append("open_orders")
        return []

    async def fake_executions():
        calls.append("executions")
        return [_filled_row(ord_no="900", code="123456", qty="10", price="10000")]

    monkeypatch.setattr(w, "_fetch_open_orders", fake_open_orders)
    monkeypatch.setattr(w, "_fetch_executions", fake_executions)

    planner = {
        "portfolio": {"position_budget": 100_000, "max_positions": 3},
        "holdings": [{"stock_code": "123456", "quantity": 10, "current_price": 1}],
    }
    result = asyncio.run(w._apply_action(_candidate_event(), "TIER1", planner))

    # Both queries ran before the decision, and the fill released the block.
    assert calls == ["open_orders", "executions"]
    assert ledger.get(intent.intent_id).state == STATE_FILLED
    assert result.state == "submitted"
    assert len(buys) == 1


def test_new_buy_stays_blocked_when_the_broker_still_shows_it_working(monkeypatch):
    async def fake_buy(client, **kwargs):
        raise AssertionError("intent is still open at the broker — must not buy")

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)
    w, ledger = _ledger_watcher()
    intent = _seed_intent(ledger,
        stock_code="123456", side="buy", quantity=10, price=10000
    )
    ledger.apply_order_result(
        intent.intent_id, submitted=True, unknown=False, order_no="900", reason="ok"
    )

    async def fake_open_orders():
        return [
            {
                "ord_no": "900", "stk_cd": "123456", "io_tp_nm": "매수",
                "ord_qty": "10", "ord_pric": "10000",
                "cntr_qty": "0", "oso_qty": "10", "ord_stt": "접수",
            }
        ]

    monkeypatch.setattr(w, "_fetch_open_orders", fake_open_orders)

    result = asyncio.run(
        w._apply_action(
            _candidate_event(), "TIER1",
            {"portfolio": {"position_budget": 100_000, "max_positions": 3}},
        )
    )

    # Blocked either as our own unresolved intent or as a working broker
    # order — both are true here, and either reason is a correct refusal.
    assert result.state == "skipped"
    assert result.attempted is False


def test_new_buy_fails_closed_when_the_open_order_query_fails(monkeypatch):
    """"We could not check" must never read as "clear"."""

    async def fake_buy(client, **kwargs):
        raise AssertionError("reconciliation failed — must not buy")

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)
    w, ledger = _ledger_watcher()
    ledger.record_intent(
        stock_code="999999", side="buy", quantity=1, price=1000
    )

    async def boom_open_orders():
        raise ConnectionError("account endpoint down")

    monkeypatch.setattr(w, "_fetch_open_orders", boom_open_orders)

    result = asyncio.run(
        w._apply_action(
            _candidate_event(), "TIER1",
            {"portfolio": {"position_budget": 100_000, "max_positions": 3}},
        )
    )

    assert result.state == "skipped"
    assert result.attempted is False
    assert "조회 실패" in (result.reason or "")
    assert any(c[0] == "error" and "매수 차단" in c[1] for c in w._notifier.calls)


def test_new_buy_fails_closed_when_the_execution_query_fails(monkeypatch):
    async def fake_buy(client, **kwargs):
        raise AssertionError("reconciliation failed — must not buy")

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)
    w, ledger = _ledger_watcher()
    ledger.record_intent(
        stock_code="999999", side="buy", quantity=1, price=1000
    )

    async def boom_executions():
        raise ConnectionError("execution endpoint down")

    monkeypatch.setattr(w, "_fetch_executions", boom_executions)

    result = asyncio.run(
        w._apply_action(
            _candidate_event(), "TIER1",
            {"portfolio": {"position_budget": 100_000, "max_positions": 3}},
        )
    )

    assert result.state == "skipped"
    assert "조회 실패" in (result.reason or "")


def test_tick_reconciles_even_when_the_planner_reports_no_open_orders(monkeypatch):
    """`open_order_count=0` says nothing about a lost-response intent."""

    w, ledger = _ledger_watcher()
    intent = _seed_intent(ledger,
        stock_code="005930", side="buy", quantity=10, price=70000
    )
    ledger.apply_order_result(
        intent.intent_id, submitted=True, unknown=False, order_no="123", reason="ok"
    )

    fetched: list[str] = []

    async def fake_plan(*args, **kwargs):
        return {
            "success": True,
            "holdings": [],
            "regime": {"regime": "neutral"},
            "candidate_rows": [],
            "portfolio": {"open_order_count": 0},  # planner sees nothing
        }

    async def fake_open_orders():
        fetched.append("open_orders")
        return [_filled_row()]

    monkeypatch.setattr(watcher_module, "plan_intraday_momentum_strategy", fake_plan)
    monkeypatch.setattr(w, "_fetch_open_orders", fake_open_orders)

    async def driver():
        await w._tick()
        await w._cancel_in_flight()

    asyncio.run(driver())

    assert fetched == ["open_orders"]  # fetched for the ledger's sake
    assert ledger.get(intent.intent_id).state == STATE_FILLED


def test_tick_skips_the_open_order_query_when_nothing_needs_it(monkeypatch):
    """No unresolved intents and no stale-cancel rule: no wasted round trip."""

    w, _ = _ledger_watcher(config=_config(stale_unfilled_minutes=0))
    fetched: list[str] = []

    async def fake_plan(*args, **kwargs):
        return {
            "success": True,
            "holdings": [],
            "regime": {"regime": "neutral"},
            "candidate_rows": [],
            "portfolio": {"open_order_count": 3},
        }

    async def fake_open_orders():
        fetched.append("open_orders")
        return []

    monkeypatch.setattr(watcher_module, "plan_intraday_momentum_strategy", fake_plan)
    monkeypatch.setattr(w, "_fetch_open_orders", fake_open_orders)

    async def driver():
        await w._tick()
        await w._cancel_in_flight()

    asyncio.run(driver())

    assert fetched == []


def test_protective_sell_sees_a_pre_existing_broker_sell_with_stale_cancel_off(
    monkeypatch,
):
    """With `stale_unfilled_minutes=0` the tick never fetched open orders, so
    the oversell guard was blind to an order placed outside this process."""

    sells: list[dict] = []

    async def fake_sell(client, **kwargs):
        sells.append(kwargs)
        return _ok_order()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_sell_order", fake_sell)
    w, _ = _ledger_watcher(config=_config(stale_unfilled_minutes=0))
    assert w._last_open_orders == []  # nothing cached, as in the bug

    async def fake_open_orders():
        return [
            {"stk_cd": "005930", "io_tp_nm": "매도", "ord_qty": "7", "oso_qty": "7"}
        ]

    monkeypatch.setattr(w, "_fetch_open_orders", fake_open_orders)

    event = _tier1_sell_event(quantity=10)
    result = asyncio.run(w._execute_tier1(event, _entry_for(event)))

    assert result.state == "submitted"
    assert sells[0]["ord_qty"] == "3"  # 10 held − 7 already working


def test_protective_sell_proceeds_when_the_refresh_fails(monkeypatch):
    """A blocked exit is the worse outcome, so we size off cache + ledger."""

    sells: list[dict] = []

    async def fake_sell(client, **kwargs):
        sells.append(kwargs)
        return _ok_order()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_sell_order", fake_sell)
    w, _ = _ledger_watcher()
    w._last_open_orders = [
        {"stk_cd": "005930", "io_tp_nm": "매도", "ord_qty": "2", "oso_qty": "2"}
    ]

    async def boom_open_orders():
        raise ConnectionError("account endpoint down")

    monkeypatch.setattr(w, "_fetch_open_orders", boom_open_orders)

    event = _tier1_sell_event(quantity=10)
    result = asyncio.run(w._execute_tier1(event, _entry_for(event)))

    assert result.state == "submitted"
    assert sells[0]["ord_qty"] == "8"  # cached view still applied: 10 − 2
    assert any(
            c[0] == "error" and "미체결 조회 실패" in c[1] for c in w._notifier.calls
        )


def test_failed_open_order_refresh_does_not_wipe_the_cache(monkeypatch):
    """Replacing a good view with [] would blind the guard exactly when it
    matters most."""

    w, _ = _ledger_watcher()
    cached = [{"stk_cd": "005930", "io_tp_nm": "매도", "ord_qty": "4", "oso_qty": "4"}]
    w._last_open_orders = list(cached)

    async def boom_open_orders():
        raise ConnectionError("down")

    monkeypatch.setattr(w, "_fetch_open_orders", boom_open_orders)

    assert asyncio.run(w._refresh_open_orders()) is False
    assert w._last_open_orders == cached


def test_open_order_query_business_error_is_a_failure_not_an_empty_list(monkeypatch):
    """`account._run_account_query` swallows errors into a result dict, so a
    bare `.get()` would report "no open orders" for a broken query."""

    from src.services import account as account_module

    w, _ = _ledger_watcher()

    async def failing_unexecuted(client, *args, **kwargs):
        return {
            "success": False, "message": "endpoint down",
            "unexecuted_orders_data": None,
        }

    async def failing_executions(client, *args, **kwargs):
        return {"success": False, "message": "endpoint down", "execution_data": None}

    monkeypatch.setattr(
        account_module, "get_unexecuted_orders", failing_unexecuted
    )
    monkeypatch.setattr(account_module, "get_execution_info", failing_executions)

    # Bypass the test helper's stubs and exercise the real methods.
    with pytest.raises(RuntimeError):
        asyncio.run(IntradayWatcher._fetch_open_orders(w))
    with pytest.raises(RuntimeError):
        asyncio.run(IntradayWatcher._fetch_executions(w))


def test_pagination_cap_warning_is_not_complete_absence_evidence(monkeypatch):
    """A successful-but-truncated page set must reset, never advance, release."""

    from src.services import account as account_module

    w, _ = _ledger_watcher()

    async def capped_unexecuted(client, *args, **kwargs):
        return {
            "success": True,
            "warning": "Reached maximum request limit (10).",
            "unexecuted_orders_data": [],
        }

    async def capped_executions(client, *args, **kwargs):
        return {
            "success": True,
            "warning": "Reached maximum request limit (10).",
            "execution_data": [],
        }

    monkeypatch.setattr(
        account_module, "get_unexecuted_orders", capped_unexecuted
    )
    monkeypatch.setattr(account_module, "get_execution_info", capped_executions)

    with pytest.raises(RuntimeError, match="incomplete"):
        asyncio.run(IntradayWatcher._fetch_open_orders(w))
    with pytest.raises(RuntimeError, match="incomplete"):
        asyncio.run(IntradayWatcher._fetch_executions(w))


# -- broker-only open orders (second Task 4 review correction) -------------
#
# An empty ledger is not evidence that the broker is idle. It says only that
# *we* have no record — exactly the state left by a fresh install, a wiped
# volume, an older build, or an order placed by hand. The pre-buy gate
# therefore queries unconditionally and inspects the broker view directly.


def _buy_row(code="123456", qty="10", remaining="10", side="매수"):
    return {
        "ord_no": "8001", "stk_cd": code, "io_tp_nm": side,
        "ord_qty": qty, "ord_pric": "10000",
        "cntr_qty": "0", "oso_qty": remaining, "ord_stt": "접수",
    }


def test_pre_buy_queries_both_apis_even_with_an_empty_ledger(monkeypatch):
    """The short-circuit this correction removes: no pending, no lookup."""

    calls: list[str] = []

    async def fake_buy(client, **kwargs):
        return _ok_order()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)
    w, ledger = _ledger_watcher()
    assert ledger.unresolved() == []  # clean ledger

    async def fake_open_orders():
        calls.append("open_orders")
        return []

    async def fake_executions():
        calls.append("executions")
        return []

    monkeypatch.setattr(w, "_fetch_open_orders", fake_open_orders)
    monkeypatch.setattr(w, "_fetch_executions", fake_executions)

    result = asyncio.run(
        w._apply_action(
            _candidate_event(), "TIER1",
            {"portfolio": {"position_budget": 100_000, "max_positions": 3}},
        )
    )

    assert calls == ["open_orders", "executions"]
    assert result.state == "submitted"  # clean views allow the buy


def test_broker_only_open_buy_blocks_a_new_buy(monkeypatch):
    """A manual / older-build / other-process order we have no intent for."""

    async def fake_buy(client, **kwargs):
        raise AssertionError("broker already has a working buy — must not duplicate")

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)
    w, ledger = _ledger_watcher()

    async def fake_open_orders():
        return [_buy_row(code="123456")]

    monkeypatch.setattr(w, "_fetch_open_orders", fake_open_orders)

    result = asyncio.run(
        w._apply_action(
            _candidate_event("123456"), "TIER1",
            {"portfolio": {"position_budget": 100_000, "max_positions": 3}},
        )
    )

    assert result.state == "skipped"
    assert result.attempted is False
    assert "미체결 매수" in (result.reason or "")
    # Blocking is enough — the external order is never adopted into our books.
    assert ledger.unresolved() == []


def test_fully_filled_broker_buy_row_does_not_block(monkeypatch):
    """Nothing remaining means nothing working."""

    buys: list[dict] = []

    async def fake_buy(client, **kwargs):
        buys.append(kwargs)
        return _ok_order()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)
    w, _ = _ledger_watcher()

    async def fake_open_orders():
        return [_buy_row(code="123456", remaining="0")]

    monkeypatch.setattr(w, "_fetch_open_orders", fake_open_orders)

    result = asyncio.run(
        w._apply_action(
            _candidate_event("123456"), "TIER1",
            {"portfolio": {"position_budget": 100_000, "max_positions": 3}},
        )
    )

    assert result.state == "submitted"
    assert len(buys) == 1


def test_other_stocks_and_sell_rows_do_not_falsely_block(monkeypatch):
    """The gate must be specific, or it would stop the strategy dead."""

    buys: list[dict] = []

    async def fake_buy(client, **kwargs):
        buys.append(kwargs)
        return _ok_order()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)
    w, _ = _ledger_watcher()

    async def fake_open_orders():
        return [
            _buy_row(code="999999"),  # a different stock
            _buy_row(code="123456", side="매도"),  # our stock, but a SELL
        ]

    monkeypatch.setattr(w, "_fetch_open_orders", fake_open_orders)

    result = asyncio.run(
        w._apply_action(
            _candidate_event("123456"), "TIER1",
            {"portfolio": {"position_budget": 100_000, "max_positions": 3}},
        )
    )

    assert result.state == "submitted"
    assert len(buys) == 1


def test_unreadable_side_on_our_stock_blocks_conservatively(monkeypatch):
    """A working row we cannot classify might be a buy; blocking is cheap."""

    async def fake_buy(client, **kwargs):
        raise AssertionError("unclassifiable working row — must not buy")

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)
    w, _ = _ledger_watcher()

    async def fake_open_orders():
        return [
            {"ord_no": "8100", "stk_cd": "123456", "ord_qty": "10", "oso_qty": "10"}
        ]

    monkeypatch.setattr(w, "_fetch_open_orders", fake_open_orders)

    result = asyncio.run(
        w._apply_action(
            _candidate_event("123456"), "TIER1",
            {"portfolio": {"position_budget": 100_000, "max_positions": 3}},
        )
    )

    assert result.state == "skipped"


def test_pre_buy_query_failure_fails_closed_with_an_empty_ledger(monkeypatch):
    """The zero-pending path must fail closed too, not sail through."""

    async def fake_buy(client, **kwargs):
        raise AssertionError("query failed — must not buy")

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)
    w, ledger = _ledger_watcher()
    assert ledger.unresolved() == []

    async def boom_open_orders():
        raise ConnectionError("account endpoint down")

    monkeypatch.setattr(w, "_fetch_open_orders", boom_open_orders)

    result = asyncio.run(
        w._apply_action(
            _candidate_event(), "TIER1",
            {"portfolio": {"position_budget": 100_000, "max_positions": 3}},
        )
    )

    assert result.state == "skipped"
    assert "조회 실패" in (result.reason or "")


def test_pre_buy_execution_failure_fails_closed_with_an_empty_ledger(monkeypatch):
    async def fake_buy(client, **kwargs):
        raise AssertionError("query failed — must not buy")

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)
    w, _ = _ledger_watcher()

    async def boom_executions():
        raise ConnectionError("execution endpoint down")

    monkeypatch.setattr(w, "_fetch_executions", boom_executions)

    result = asyncio.run(
        w._apply_action(
            _candidate_event(), "TIER1",
            {"portfolio": {"position_budget": 100_000, "max_positions": 3}},
        )
    )

    assert result.state == "skipped"
    assert "조회 실패" in (result.reason or "")


def test_a_later_clean_view_recovers_after_a_failed_pre_buy(monkeypatch):
    """A transient outage must not latch the buy path shut."""

    buys: list[dict] = []
    broken = {"value": True}

    async def fake_buy(client, **kwargs):
        buys.append(kwargs)
        return _ok_order()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)
    w, _ = _ledger_watcher()

    async def flaky_open_orders():
        if broken["value"]:
            raise ConnectionError("down")
        return []

    monkeypatch.setattr(w, "_fetch_open_orders", flaky_open_orders)
    planner = {"portfolio": {"position_budget": 100_000, "max_positions": 3}}

    first = asyncio.run(w._apply_action(_candidate_event(), "TIER1", planner))
    broken["value"] = False
    second = asyncio.run(w._apply_action(_candidate_event(), "TIER1", planner))

    assert first.state == "skipped"
    assert second.state == "submitted"
    assert len(buys) == 1


def test_startup_queries_both_views_even_with_an_empty_ledger(monkeypatch):
    calls: list[str] = []
    w, ledger = _ledger_watcher()
    assert ledger.unresolved() == []

    async def fake_open_orders():
        calls.append("open_orders")
        return []

    async def fake_executions():
        calls.append("executions")
        return []

    monkeypatch.setattr(w, "_fetch_open_orders", fake_open_orders)
    monkeypatch.setattr(w, "_fetch_executions", fake_executions)
    monkeypatch.setattr(w, "_is_market_open", lambda *a, **k: False)
    monkeypatch.setattr(w, "_persist_state", lambda: None)

    async def driver():
        w.stop()
        await w.run()

    asyncio.run(driver())

    assert calls == ["open_orders", "executions"]


def test_broker_only_open_buy_never_blocks_a_protective_exit(monkeypatch):
    """The buy gate is buy-only; exits stay unrestricted."""

    sells: list[dict] = []

    async def fake_sell(client, **kwargs):
        sells.append(kwargs)
        return _ok_order()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_sell_order", fake_sell)
    w, _ = _ledger_watcher()

    async def fake_open_orders():
        return [_buy_row(code="005930")]  # a working BUY on the held stock

    monkeypatch.setattr(w, "_fetch_open_orders", fake_open_orders)

    event = _tier1_sell_event(quantity=10)
    result = asyncio.run(w._execute_tier1(event, _entry_for(event)))

    assert result.state == "submitted"
    assert sells[0]["ord_qty"] == "10"  # a buy row does not reduce sellable


def test_ambiguous_intent_keeps_new_buys_closed_but_not_exits(monkeypatch):
    """Invariant: while reconciliation cannot decide, entries stop and exits
    do not. Two identical-looking broker orders match one lost-response
    intent, so it stays unresolved rather than being settled arbitrarily."""

    sells: list[dict] = []

    async def fake_buy(client, **kwargs):
        raise AssertionError("ambiguous ledger state — must not buy")

    async def fake_sell(client, **kwargs):
        sells.append(kwargs)
        return _ok_order()

    async def fake_cancel(client, **kwargs):
        return _ok_order()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)
    monkeypatch.setattr(watcher_module.order_service, "place_stock_sell_order", fake_sell)
    monkeypatch.setattr(watcher_module.order_service, "cancel_stock_order", fake_cancel)

    w, ledger = _ledger_watcher()
    intent = _seed_intent(ledger,
        stock_code="123456", side="buy", quantity=10, price=10000
    )
    ledger.apply_order_result(
        intent.intent_id, submitted=False, unknown=True, order_no=None,
        reason="ReadTimeout",
    )

    stamp = _broker_now()
    twins = [
        {
            "ord_no": no, "stk_cd": "123456", "io_tp_nm": "매수",
            "ord_qty": "10", "ord_pric": "10000",
            "cntr_qty": "0", "oso_qty": "10", "ord_stt": "접수",
            "ord_tmd": stamp,
        }
        for no in ("7001", "7002")
    ]

    async def fake_open_orders():
        return twins

    monkeypatch.setattr(w, "_fetch_open_orders", fake_open_orders)

    buy = asyncio.run(
        w._apply_action(
            _candidate_event("123456"), "TIER1",
            {"portfolio": {"position_budget": 100_000, "max_positions": 3}},
        )
    )
    assert buy.state == "skipped"
    assert buy.attempted is False
    # Unresolved, and no order number was guessed at.
    row = ledger.get(intent.intent_id)
    assert row.state == STATE_UNKNOWN
    assert row.order_no is None

    # Protective paths are untouched by the ambiguity.
    assert asyncio.run(
        w._apply_action(_holding_event("111111"), "CUT_LOSS", {})
    ).state == "submitted"
    stop_event = _tier1_sell_event()
    assert asyncio.run(
        w._execute_tier1(stop_event, _entry_for(stop_event))
    ).state == "submitted"
    assert len(sells) == 2


def test_stale_morning_fill_does_not_release_the_afternoon_block(monkeypatch):
    """End to end: the defect allowed a duplicate buy after an unrelated fill."""

    calls: list[dict] = []
    afternoon = datetime(2026, 7, 28, 15, 0, tzinfo=KST)
    real_ledger_now = watcher_module.order_ledger._now
    monkeypatch.setattr(
        watcher_module.order_ledger,
        "_now",
        lambda now=None: real_ledger_now(now or afternoon),
    )

    async def fake_buy(client, **kwargs):
        calls.append(kwargs)
        return _lost_response_order()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)
    w, ledger = _ledger_watcher()
    planner = {"portfolio": {"position_budget": 100_000, "max_positions": 3}}

    # A lost-response buy: 10 @ 10000, now UNKNOWN and blocking.
    first = asyncio.run(w._apply_action(_candidate_event("123456"), "TIER1", planner))
    assert first.state == "unknown"

    # An unrelated fill from earlier in the session, identical in every
    # identity field, appears in the execution view.
    morning = afternoon.replace(hour=9)

    async def fake_executions():
        return [
            {
                "ord_no": "5555", "stk_cd": "123456", "io_tp_nm": "매수",
                "ord_qty": "10", "ord_pric": "10000",
                "cntr_qty": "10", "oso_qty": "0", "ord_stt": "체결",
                "ord_tmd": morning.strftime("%Y%m%d%H%M%S"),
            }
        ]

    monkeypatch.setattr(w, "_fetch_executions", fake_executions)

    second = asyncio.run(w._apply_action(_candidate_event("123456"), "TIER1", planner))

    assert second.state == "skipped"  # still blocked
    assert len(calls) == 1  # no duplicate order
    row = ledger.get(
        ledger.unresolved(stock_code="123456")[0].intent_id
    )
    assert row.state == STATE_UNKNOWN
    assert row.order_no is None  # the morning order was never adopted


# -- decision replay must not re-submit (Task 1 review correction) ---------
#
# Each of these counts *order API calls* and inspects the ledger's attempt
# history, because the defect was invisible in the final state: the watcher
# sent a second order and then overwrote the row that proved the first one.


def test_same_bucket_replay_of_a_working_buy_sends_one_order(monkeypatch):
    calls: list[dict] = []

    async def fake_buy(client, **kwargs):
        calls.append(kwargs)
        return _ok_order(buy_order_result={"ord_no": "1234567"})

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)
    w, ledger = _ledger_watcher()
    planner = {"portfolio": {"position_budget": 100_000, "max_positions": 3}}

    first = asyncio.run(w._apply_action(_candidate_event(), "TIER1", planner))
    second = asyncio.run(w._apply_action(_candidate_event(), "TIER1", planner))

    assert first.state == "submitted"
    assert second.state == "skipped"
    assert len(calls) == 1
    history = ledger.attempts_for(
        ledger.unresolved(stock_code="123456")[0].decision_key
    )
    assert [(i.attempt, i.state) for i in history] == [(1, STATE_SUBMITTED)]


def test_crash_before_submit_replay_sends_one_order(monkeypatch, tmp_path):
    """The INTENDED row from the dead process must suppress the retry."""

    calls: list[dict] = []

    async def fake_buy(client, **kwargs):
        calls.append(kwargs)
        return _ok_order()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)
    path = tmp_path / "order_ledger.sqlite3"
    planner = {"portfolio": {"position_budget": 100_000, "max_positions": 3}}

    # Process A commits INTENDED and dies before the API call.
    dying = OrderLedger(path)
    seeded = _seed_intent(
        dying, stock_code="123456", side="buy", quantity=10, price=10000,
        decision_scope="TIER1",
    )
    assert seeded.state == STATE_INTENDED
    dying.close()

    # Process B replays the identical decision inside the same bucket.
    w, ledger = _ledger_watcher(tmp_path)
    result = asyncio.run(w._apply_action(_candidate_event(), "TIER1", planner))

    assert result.state == "skipped"
    assert calls == []  # no order at all
    assert len(ledger.attempts_for(seeded.decision_key)) == 1


def test_lost_response_replay_sends_one_order(monkeypatch):
    calls: list[dict] = []

    async def fake_buy(client, **kwargs):
        calls.append(kwargs)
        return _lost_response_order()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)
    w, ledger = _ledger_watcher()
    planner = {"portfolio": {"position_budget": 100_000, "max_positions": 3}}

    first = asyncio.run(w._apply_action(_candidate_event(), "TIER1", planner))
    second = asyncio.run(w._apply_action(_candidate_event(), "TIER1", planner))

    assert first.state == "unknown"
    assert second.state == "skipped"
    assert len(calls) == 1  # never resubmitted off UNKNOWN
    row = ledger.unresolved(stock_code="123456")[0]
    assert [(i.attempt, i.state) for i in ledger.attempts_for(row.decision_key)] == [
        (1, STATE_UNKNOWN)
    ]


def test_filled_decision_replay_sends_no_order_and_keeps_the_row(monkeypatch):
    """The headline defect: a settled decision replayed in the same bucket
    used to produce a second order and overwrite its own audit row."""

    calls: list[dict] = []

    async def fake_buy(client, **kwargs):
        calls.append(kwargs)
        return _ok_order(buy_order_result={"ord_no": "1234567"})

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)
    w, ledger = _ledger_watcher()
    planner = {"portfolio": {"position_budget": 100_000, "max_positions": 3}}

    first = asyncio.run(w._apply_action(_candidate_event(), "TIER1", planner))
    assert first.state == "submitted"
    intent_id = ledger.unresolved(stock_code="123456")[0].intent_id
    decision_key = ledger.get(intent_id).decision_key
    # The order fills.
    ledger.mark_state(intent_id, STATE_FILLED, filled_quantity=10)
    settled = ledger.get(intent_id).to_dict()

    second = asyncio.run(w._apply_action(_candidate_event(), "TIER1", planner))

    assert second.state == "skipped"
    assert len(calls) == 1  # no duplicate buy
    assert ledger.get(intent_id).to_dict() == settled  # audit row intact
    assert len(ledger.attempts_for(decision_key)) == 1


def test_rejected_buy_retry_records_a_second_attempt(monkeypatch):
    calls: list[dict] = []
    responses = [_rejected_order(), _ok_order(buy_order_result={"ord_no": "999"})]

    async def fake_buy(client, **kwargs):
        calls.append(kwargs)
        return responses.pop(0)

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", fake_buy)
    w, ledger = _ledger_watcher()
    planner = {"portfolio": {"position_budget": 100_000, "max_positions": 3}}

    first = asyncio.run(w._apply_action(_candidate_event(), "TIER1", planner))
    second = asyncio.run(w._apply_action(_candidate_event(), "TIER1", planner))

    assert first.state == "failed"
    assert second.state == "submitted"
    assert len(calls) == 2  # a rejection is safe to retry
    key = ledger.unresolved(stock_code="123456")[0].decision_key
    history = ledger.attempts_for(key)
    assert [(i.attempt, i.state) for i in history] == [
        (1, STATE_REJECTED), (2, STATE_SUBMITTED)
    ]
    assert history[0].reason == "종목 정보가 없습니다"  # rejection preserved


def test_same_bucket_replay_of_a_protective_sell_sends_one_order(monkeypatch):
    """A replayed exit is a double, not an exit."""

    sells: list[dict] = []

    async def fake_sell(client, **kwargs):
        sells.append(kwargs)
        return _ok_order()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_sell_order", fake_sell)
    w, ledger = _ledger_watcher()

    first = asyncio.run(w._apply_action(_holding_event(quantity=10), "CUT_LOSS", {}))
    second = asyncio.run(w._apply_action(_holding_event(quantity=10), "CUT_LOSS", {}))

    assert first.state == "submitted"
    assert second.state == "skipped"
    assert len(sells) == 1
    key = ledger.unresolved(stock_code="005930", side="sell")[0].decision_key
    assert len(ledger.attempts_for(key)) == 1


def test_a_different_exit_instruction_of_the_same_size_still_goes_out(monkeypatch):
    """TRIM 5 then CUT_LOSS 5 on 10 shares is a full exit, not a replay."""

    sells: list[dict] = []

    async def fake_sell(client, **kwargs):
        sells.append(kwargs)
        return _ok_order()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_sell_order", fake_sell)
    w, _ = _ledger_watcher()

    trim = asyncio.run(w._apply_action(_holding_event(quantity=10), "TRIM", {}))
    # 5 are now working, so a full exit clamps to the remaining 5 — the same
    # size as the TRIM, but a different instruction.
    cut = asyncio.run(w._apply_action(_holding_event(quantity=10), "CUT_LOSS", {}))

    assert trim.state == "submitted"
    assert cut.state == "submitted"
    assert [s["ord_qty"] for s in sells] == ["5", "5"]


def test_tier1_stop_loss_replay_sends_one_order(monkeypatch):
    sells: list[dict] = []

    async def fake_sell(client, **kwargs):
        sells.append(kwargs)
        return _ok_order()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_sell_order", fake_sell)
    w, _ = _ledger_watcher()

    e1 = _tier1_sell_event(quantity=10)
    first = asyncio.run(w._execute_tier1(e1, _entry_for(e1)))
    e2 = _tier1_sell_event(quantity=10)
    second = asyncio.run(w._execute_tier1(e2, _entry_for(e2)))

    assert first.state == "submitted"
    assert second.state == "skipped"
    assert len(sells) == 1


def test_ledger_fault_still_lets_a_protective_exit_through(monkeypatch):
    """Policy preserved: a ledger *fault* is not a duplicate refusal."""

    sells: list[dict] = []

    async def fake_sell(client, **kwargs):
        sells.append(kwargs)
        return _ok_order()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_sell_order", fake_sell)
    w, ledger = _ledger_watcher()
    ledger.close()  # storage gone

    result = asyncio.run(w._apply_action(_holding_event(quantity=10), "CUT_LOSS", {}))

    assert result.state == "submitted"
    assert len(sells) == 1
    assert any(c[0] == "error" and "원장" in (c[1] + c[2]) for c in w._notifier.calls)


def test_lost_response_sell_eventually_releases_without_unbounded_stop_lock(
    monkeypatch,
):
    """The regression: UNKNOWN sell used to subtract all holdings forever."""

    clock = {"now": datetime(2026, 7, 27, 10, 0, tzinfo=KST)}

    def fake_now(now=None):
        value = now or clock["now"]
        return value.astimezone(KST)

    monkeypatch.setattr(watcher_module.order_ledger, "_now", fake_now)

    sells: list[dict] = []

    async def fake_sell(client, **kwargs):
        sells.append(kwargs)
        return _lost_response_order() if len(sells) == 1 else _ok_order()

    async def no_open_orders():
        return []

    async def no_executions():
        return []

    monkeypatch.setattr(
        watcher_module.order_service, "place_stock_sell_order", fake_sell
    )
    w, ledger = _ledger_watcher()
    monkeypatch.setattr(w, "_fetch_open_orders", no_open_orders)
    monkeypatch.setattr(w, "_fetch_executions", no_executions)

    first_event = _tier1_sell_event(quantity=10)
    first = asyncio.run(w._execute_tier1(first_event, _entry_for(first_event)))
    assert first.state == "unknown"
    assert len(sells) == 1
    old_intent = ledger.unresolved(stock_code="005930", side="sell")[0]
    assert old_intent.state == STATE_UNKNOWN

    # Three independent, complete empty view-pairs. Until the third, the
    # prior sell still covers all holdings and the stop-loss is suppressed.
    outcomes = []
    for seconds in (120, 150, 180):
        clock["now"] = datetime(2026, 7, 27, 10, 0, tzinfo=KST) + timedelta(
            seconds=seconds
        )
        event = _tier1_sell_event(quantity=10)
        outcomes.append(
            asyncio.run(w._execute_tier1(event, _entry_for(event)))
        )

    assert [result.state for result in outcomes] == [
        "skipped",
        "skipped",
        "submitted",
    ]
    assert len(sells) == 2
    assert sells[1]["ord_qty"] == "10"
    released = ledger.get(old_intent.intent_id)
    assert released.state == STATE_RELEASED
    assert released.absence_observation_count == 3
    # A new attempt is recorded instead of mutating/reusing the released row.
    assert ledger.get(old_intent.intent_id).state == STATE_RELEASED
    assert [
        row.state
        for row in ledger.recent()
        if row.stock_code == "005930" and row.side == "sell"
    ] == [STATE_SUBMITTED, STATE_RELEASED]
    snapshot = w._ledger_snapshot()
    assert any(row["state"] == STATE_RELEASED for row in snapshot["recent"])
    assert snapshot["recent_audit"][0]["event_type"] == "RELEASED"


def test_unknown_sell_query_failure_resets_evidence_but_never_blocks_exit_fault_policy(
    monkeypatch,
):
    """Account failure resets RELEASED evidence; ledger faults still don't gate."""

    started = datetime(2026, 7, 27, 10, 0, tzinfo=KST)
    clock = {"now": started}

    def fake_now(now=None):
        return (now or clock["now"]).astimezone(KST)

    monkeypatch.setattr(watcher_module.order_ledger, "_now", fake_now)
    w, ledger = _ledger_watcher()
    intent = _seed_intent(
        ledger,
        stock_code="005930",
        side="sell",
        quantity=10,
        price=None,
        now=started,
    )
    ledger.apply_order_result(
        intent.intent_id,
        submitted=False,
        unknown=True,
        order_no=None,
        reason="ReadTimeout",
        now=started,
    )

    async def no_open_orders():
        return []

    async def no_executions():
        return []

    monkeypatch.setattr(w, "_fetch_open_orders", no_open_orders)
    monkeypatch.setattr(w, "_fetch_executions", no_executions)
    for seconds in (120, 150):
        clock["now"] = started + timedelta(seconds=seconds)
        asyncio.run(w._sellable_quantity_now("005930", 10))
    assert ledger.get(intent.intent_id).absence_observation_count == 2

    async def executions_down():
        raise ConnectionError("ka10076 down")

    monkeypatch.setattr(w, "_fetch_executions", executions_down)
    clock["now"] = started + timedelta(seconds=180)
    # Still blocked by the UNKNOWN quantity, but the protective route returns
    # normally and reports the degraded query rather than raising.
    assert asyncio.run(w._sellable_quantity_now("005930", 10)) == 0
    assert ledger.get(intent.intent_id).absence_observation_count == 0
    assert any(
        call[0] == "error" and "주문은 그대로 집행" in call[1]
        for call in w._notifier.calls
    )


def test_degraded_detail_names_sources_instead_of_the_fixed_plan_message() -> None:
    """The failure detail must carry the cause, not the plan's success string.

    `plan_intraday_momentum_strategy` returns the same `message` whether or not
    the cycle succeeded, so recording it produced a `/state` counter that read
    "Built intraday strategy plan" 140 times while DNS was failing.
    """

    detail = watcher_module._describe_degraded_sources(
        {
            "success": False,
            "message": "Built intraday strategy plan",
            "degraded_sources": [
                {"source": "gainers", "api_id": "ka10027", "error": "name resolution"},
                {"source": "kospi", "return_msg": "조회가 실패했습니다"},
            ],
        }
    )

    assert "Built intraday strategy plan" not in detail
    assert "gainers: name resolution" in detail
    assert "kospi: 조회가 실패했습니다" in detail


def test_degraded_detail_truncates_when_every_leg_breaks() -> None:
    """A DNS fault degrades all legs at once; the detail still goes to Discord."""

    detail = watcher_module._describe_degraded_sources(
        {
            "success": False,
            "degraded_sources": [
                {"source": f"leg{i}", "error": "timeout"} for i in range(7)
            ],
        }
    )

    assert "leg0: timeout" in detail
    assert "leg6" not in detail
    assert "(+3 more)" in detail


def test_degraded_detail_is_explicit_when_no_breakdown_is_present() -> None:
    """An older plan payload must not silently look like a clean cycle."""

    detail = watcher_module._describe_degraded_sources(
        {"success": False, "message": "Built intraday strategy plan"}
    )

    assert detail == "planner success=false (no source breakdown)"
    assert "Built intraday strategy plan" not in detail


def _regime_plan(regime: dict):
    async def fake_plan(*args, **kwargs):
        return {
            "success": True,
            "holdings": [],
            "regime": regime,
            "candidate_rows": [],
            "portfolio": {"open_order_count": 0},
        }

    return fake_plan


def test_degraded_regime_stays_out_of_the_flip_debounce_window(monkeypatch):
    """A zeroed index read classifies as risk_off; it must not become stable.

    An outage lasting the stability window would otherwise install
    "risk_off" as the baseline and fabricate a "risk_off -> risk_on" flip
    the moment the read recovers — a second false page chasing the first.
    """

    w = _build_watcher(config=_config(regime_stability_ticks=3))
    monkeypatch.setattr(
        watcher_module,
        "plan_intraday_momentum_strategy",
        _regime_plan(
            {
                "regime": "risk_off",
                "extreme_risk_off": True,
                "market_data_complete": False,
            }
        ),
    )

    for _ in range(4):
        asyncio.run(w._tick())

    assert list(w._regime_history) == []


def test_complete_regime_still_feeds_the_debounce_window(monkeypatch):
    """Positive control: the guard must not starve normal debouncing."""

    w = _build_watcher(config=_config(regime_stability_ticks=3))
    monkeypatch.setattr(
        watcher_module,
        "plan_intraday_momentum_strategy",
        _regime_plan({"regime": "risk_on", "market_data_complete": True}),
    )

    for _ in range(3):
        asyncio.run(w._tick())

    assert list(w._regime_history) == ["risk_on", "risk_on", "risk_on"]


def test_degraded_tick_does_not_consume_a_pending_flip_announcement(monkeypatch):
    """`_last_emitted_regime` records what we actually announced.

    The detector suppresses a degraded tick's flip, so advancing the
    announcement here would retire a trigger that was never sent — and the
    recovered tick, seeing "already announced", would stay silent for good.
    """

    w = _build_watcher(config=_config(regime_stability_ticks=3))
    w._last_emitted_regime = "risk_on"
    for _ in range(3):
        w._regime_history.append("risk_off")

    monkeypatch.setattr(
        watcher_module,
        "plan_intraday_momentum_strategy",
        _regime_plan(
            {
                "regime": "risk_off",
                "extreme_risk_off": True,
                "market_data_complete": False,
            }
        ),
    )
    asyncio.run(w._tick())
    assert w._last_emitted_regime == "risk_on", "degraded tick must not announce"

    monkeypatch.setattr(
        watcher_module,
        "plan_intraday_momentum_strategy",
        _regime_plan({"regime": "risk_off", "market_data_complete": True}),
    )
    asyncio.run(w._tick())
    assert w._last_emitted_regime == "risk_off", "recovered tick must still fire"


def _candidate_row(code, *, score, eligible, name=None):
    return {
        "stock_code": code,
        "stock_name": name or f"종목{code}",
        "score": score,
        "eligible": eligible,
        "ma_dip_pct": 2.0,
        "reasons": [] if eligible else ["극단적 시장 약세 (진입 불가)"],
        "entry_price": 10000,
        "sources": ["roster"],
    }


def _plan_with_candidates(rows):
    async def fake_plan(*args, **kwargs):
        return {
            "success": True,
            "holdings": [],
            "regime": {"regime": "neutral", "market_data_complete": True},
            "candidate_rows": rows,
            "portfolio": {"open_order_count": 0},
        }

    return fake_plan


def test_a_scanned_but_unqualified_name_can_still_fire_later(monkeypatch):
    """Scanning a code must not permanently mark it "not new".

    The movers leaderboards churned, so tracking what was *scanned* was a
    fair proxy for novelty. A fixed roster scores the same codes every tick,
    so that proxy marked all of them un-new after tick 1 and new_candidate
    stopped firing altogether — 2026-08-19/20 held 186 snapshots with an
    eligible, past-the-gate candidate and dispatched none of them.
    """

    w = _build_watcher(config=_config(new_candidate_min_score=8, max_positions=1))
    code = "005930"

    # Tick 1: scanned, but vetoed — must not be remembered as qualified.
    monkeypatch.setattr(
        watcher_module,
        "plan_intraday_momentum_strategy",
        _plan_with_candidates([_candidate_row(code, score=9, eligible=False)]),
    )
    asyncio.run(w._tick())
    assert w._prev_qualified_codes == set()

    # Tick 2: the same code now qualifies — this is the dispatch we lost.
    monkeypatch.setattr(
        watcher_module,
        "plan_intraday_momentum_strategy",
        _plan_with_candidates([_candidate_row(code, score=9, eligible=True)]),
    )
    asyncio.run(w._tick())

    fired = [e for e in w.status.recent() if e["trigger_type"] == "new_candidate"]
    assert fired, "newly-qualified roster name must dispatch"
    assert fired[0]["stock_code"] == code
    assert w._prev_qualified_codes == {code}


def test_a_name_below_the_gate_is_not_remembered_as_qualified(monkeypatch):
    """Eligible but short of the score gate is not a dispatch."""

    w = _build_watcher(config=_config(new_candidate_min_score=8))
    monkeypatch.setattr(
        watcher_module,
        "plan_intraday_momentum_strategy",
        _plan_with_candidates([_candidate_row("000660", score=7, eligible=True)]),
    )
    asyncio.run(w._tick())
    assert w._prev_qualified_codes == set()
    assert not [e for e in w.status.recent() if e["trigger_type"] == "new_candidate"]


def _dedup_candidate_event(code="068270", *, score):
    return TriggerEvent(
        trigger_type="new_candidate",
        tier=2,
        scope="stock",
        target_role=ROLE_SCREENER,
        stock_code=code,
        stock_name="셀트리온",
        snapshot={"score": score},
        detected_at=datetime.now(KST),
        reason=f"신규 강한 후보 (score={score})",
    )


def test_rejected_candidate_is_not_re_dispatched_at_the_same_score():
    """2026-08-25: 113 screener calls on 7 names, every one REJECT.

    Scores drift across the gate, so a rejected name that slips a point and
    re-qualifies looks new again every cooldown. It drained the agent
    backend's quota mid-session.
    """

    w = _build_watcher(config=_config(candidate_dedup_score_delta=1.0))
    w._last_candidate_action["068270"] = ("REJECT", 8.0, datetime.now(KST))

    assert w._should_skip_new_candidate(_dedup_candidate_event(score=8))
    assert w._should_skip_new_candidate(_dedup_candidate_event(score=7)), (
        "a weaker score is not new information"
    )


def test_a_materially_better_score_reopens_a_rejected_candidate():
    w = _build_watcher(config=_config(candidate_dedup_score_delta=1.0))
    w._last_candidate_action["068270"] = ("REJECT", 8.0, datetime.now(KST))
    assert not w._should_skip_new_candidate(_dedup_candidate_event(score=9))


def test_an_approved_candidate_is_never_suppressed():
    """An approval has to reach the buy path."""

    w = _build_watcher(config=_config(candidate_dedup_score_delta=1.0))
    for action in ("TIER1", "TIER2"):
        w._last_candidate_action["068270"] = (action, 8.0, datetime.now(KST))
        assert not w._should_skip_new_candidate(_dedup_candidate_event(score=8))


def test_yesterdays_rejection_does_not_mute_today():
    w = _build_watcher(config=_config(candidate_dedup_score_delta=1.0))
    w._last_candidate_action["068270"] = (
        "REJECT", 8.0, datetime.now(KST) - timedelta(days=1)
    )
    assert not w._should_skip_new_candidate(_dedup_candidate_event(score=8))


def test_candidate_dedup_disabled_by_zero_delta():
    w = _build_watcher(config=_config(candidate_dedup_score_delta=0))
    w._last_candidate_action["068270"] = ("REJECT", 8.0, datetime.now(KST))
    assert not w._should_skip_new_candidate(_dedup_candidate_event(score=8))


def test_candidate_dedup_does_not_touch_other_triggers():
    """Only new_candidate — a holding or Tier-1 event must pass through."""

    w = _build_watcher(config=_config(candidate_dedup_score_delta=1.0))
    w._last_candidate_action["068270"] = ("REJECT", 8.0, datetime.now(KST))
    event = _dedup_candidate_event(score=8)
    event.trigger_type = "holding_swing"
    assert not w._should_skip_new_candidate(event)


def test_missing_score_dispatches_rather_than_suppressing():
    w = _build_watcher(config=_config(candidate_dedup_score_delta=1.0))
    w._last_candidate_action["068270"] = ("REJECT", None, datetime.now(KST))
    assert not w._should_skip_new_candidate(_dedup_candidate_event(score=8))


def test_rejected_candidate_is_gated_out_of_the_dispatch_path():
    """Wiring check: the predicate must actually be consulted by the handler.

    Testing `_should_skip_new_candidate` alone passes even when the gate is
    not called at all, which is exactly how a dedup can exist in the code and
    still burn the quota in production.
    """

    w = _build_watcher(config=_config(candidate_dedup_score_delta=1.0))
    w._last_candidate_action["068270"] = ("REJECT", 8.0, datetime.now(KST))

    asyncio.run(w._handle_trigger(_dedup_candidate_event(score=8), planner_result={}))
    assert not w.status.recent(), "suppressed trigger must not reach the dispatcher"

    # A stronger score must still get through the same path.
    asyncio.run(w._handle_trigger(_dedup_candidate_event(score=9), planner_result={}))
    assert [e["trigger_type"] for e in w.status.recent()] == ["new_candidate"]


def _planner_for_comment():
    return {
        "portfolio": {
            "holding_count": 0, "open_order_count": 0,
            "cash_available": 1_256_640, "estimated_assets": 1_256_640,
        },
        "candidate_rows": [{"stock_code": "068270"}],
        "holdings": [],
    }


def test_screener_comment_offers_screener_actions_not_sell_rules():
    """A candidate trigger was told only ACKNOWLEDGE/HOLD were allowed.

    Neither is a screener ACTION — its skill asks for TIER1/TIER2/REJECT —
    so the instruction contradicted itself and REJECT was the only reading
    that satisfied both. Every one of 2026-08-25's 113 dispatches came back
    REJECT.
    """

    w = _build_watcher()
    body = w._build_trigger_comment(
        _dedup_candidate_event(score=8), _planner_for_comment()
    )
    assert "TIER1 / TIER2 / REJECT" in body
    assert "`TRIM`" not in body
    assert "만 허용" not in body


def test_evaluator_comment_keeps_the_sell_side_rule():
    """The rule is right where selling is actually on the menu."""

    w = _build_watcher()
    event = _dedup_candidate_event(score=8)
    event.trigger_type = "holding_swing"
    event.target_role = ROLE_EVALUATOR
    body = w._build_trigger_comment(event, _planner_for_comment())
    assert "ACTION 선택 규칙" in body
    assert "`TRIM`" in body


def _planner_after_a_sale():
    """2026-09-14 10:00, measured. 기아 2주 sold at 09:04:13.

    entr still shows this morning's deposit; prsm_dpst_aset_amt and d2_entra
    already carry the proceeds. 246,800 gross - 30 fee - 493 tax = 246,277,
    which is exactly the gap.
    """

    return {
        "portfolio": {
            "holding_count": 0, "open_order_count": 0,
            "cash_available": 1_018_699,
            "cash_d2": 1_264_976,
            "estimated_assets": 1_264_976,
        },
        "candidate_rows": [],
        "holdings": [],
    }


def test_unsettled_sale_proceeds_are_named_not_left_as_a_bare_gap():
    """Four incidents read this gap as a position that had already been sold.

    SWO-768 / 870 / 880 / 907 — the last one an urgent ESCALATE. The trigger
    said "현금 1,018,699원 · 총자산 1,264,976원" with 보유 0종목, and the
    246,277원 between two settlement bases is indistinguishable from a
    holding unless the basis is named.
    """

    w = _build_watcher()
    event = _dedup_candidate_event(score=8)
    event.trigger_type = "periodic_review"
    event.target_role = ROLE_PM
    body = w._build_trigger_comment(event, _planner_after_a_sale())

    assert "246,277원" in body
    assert "미정산 매도대금" in body
    assert "누락된 포지션이 아니다" in body
    # The unlabelled pairing is what did the damage.
    assert "- 현금:" not in body
    assert "예수금(당일)" in body and "D+2" in body


def test_holdings_line_uses_the_keys_the_planner_actually_emits():
    """Every holding rendered as "?(?) +0.00%" — the keys never matched.

    strategy._normalize_holding_rows emits stock_code/stock_name/profit_rate;
    this block read code/name/return_pct. Two delegations were spent chasing
    the phantom (SWO-900 "보유 종목 식별 불가", SWO-925 "식별 불가 보유 1종목"),
    and the wrap logged it running to the close.
    """

    w = _build_watcher()
    planner = _planner_after_a_sale()
    planner["portfolio"]["holding_count"] = 1
    planner["holdings"] = [
        # Exactly the shape strategy.py builds — not this test's invention.
        {
            "stock_code": "051910", "stock_name": "LG화학", "quantity": 2,
            "avg_price": 270_750, "current_price": 271_500,
            "profit_loss": 255, "profit_rate": -3.42,
        }
    ]

    event = _dedup_candidate_event(score=8)
    event.trigger_type = "periodic_review"
    event.target_role = ROLE_PM
    body = w._build_trigger_comment(event, planner)

    assert "LG화학(051910)" in body
    assert "-3.42%" in body
    assert "?(?)" not in body
    # The flat-looking zero is the half that actually misleads.
    assert "+0.00%" not in body


def test_unknown_return_is_not_rendered_as_flat():
    """A missing rate must not read as 0.00% — flat invites HOLD."""

    w = _build_watcher()
    planner = _planner_after_a_sale()
    planner["portfolio"]["holding_count"] = 1
    planner["holdings"] = [
        {"stock_code": "051910", "stock_name": "LG화학", "profit_rate": None}
    ]

    event = _dedup_candidate_event(score=8)
    event.trigger_type = "periodic_review"
    event.target_role = ROLE_PM
    body = w._build_trigger_comment(event, planner)

    assert "LG화학(051910)" in body
    assert "수익률 미상" in body
    assert "+0.00%" not in body


def test_a_real_holding_is_not_relabelled_as_unsettled_proceeds():
    """The note must not fire while a position is actually held.

    Here the same arithmetic gap *is* the position, and claiming otherwise
    would talk an evaluator out of a live exit.
    """

    w = _build_watcher()
    planner = _planner_after_a_sale()
    planner["portfolio"]["holding_count"] = 1
    planner["portfolio"]["cash_d2"] = 1_018_699
    # The keys strategy._normalize_holding_rows actually emits. Writing this
    # fixture against what the renderer happened to read is how the "?(?)"
    # bug survived — the same trap as the ka10075 fixture.
    planner["holdings"] = [
        {"stock_code": "000270", "stock_name": "기아", "profit_rate": -2.28}
    ]

    event = _dedup_candidate_event(score=8)
    event.trigger_type = "holding_swing"
    event.target_role = ROLE_EVALUATOR
    body = w._build_trigger_comment(event, planner)

    assert "미정산 매도대금" not in body
    assert "기아" in body


def test_a_buy_that_never_rested_on_the_book_still_reconciles(monkeypatch):
    """A marketable buy fills on submission and never appears as an open order.

    Executions used to be fetched only for the UNKNOWN-sell release, so the
    one view that could confirm such a fill was never requested and the
    intent sat at SUBMITTED forever — 2026-08-26 held KB금융 all session
    while its intent stayed unresolved, warning 708 times and blocking
    further buys of that code.
    """

    w = _build_watcher()
    calls = {"executions": 0}

    async def fake_executions():
        calls["executions"] += 1
        return []

    async def fake_open_orders():
        return []

    monkeypatch.setattr(w, "_fetch_executions", fake_executions)
    monkeypatch.setattr(w, "_fetch_open_orders", fake_open_orders)
    # An unresolved BUY — no UNKNOWN sell anywhere.
    monkeypatch.setattr(w, "_has_unresolved_intents", lambda: True)
    monkeypatch.setattr(w, "_has_unknown_sell_intents", lambda: False)
    monkeypatch.setattr(
        watcher_module,
        "plan_intraday_momentum_strategy",
        _plan_with_candidates([]),
    )

    asyncio.run(w._tick())

    assert calls["executions"] == 1, (
        "reconciliation must see the execution view for a buy, not just sells"
    )


def test_executions_are_not_fetched_when_nothing_is_unresolved(monkeypatch):
    """The extra call is bounded to ticks that actually have work pending."""

    w = _build_watcher()
    calls = {"executions": 0}

    async def fake_executions():
        calls["executions"] += 1
        return []

    monkeypatch.setattr(w, "_fetch_executions", fake_executions)
    monkeypatch.setattr(w, "_has_unresolved_intents", lambda: False)
    monkeypatch.setattr(w, "_has_unknown_sell_intents", lambda: False)
    monkeypatch.setattr(
        watcher_module,
        "plan_intraday_momentum_strategy",
        _plan_with_candidates([]),
    )

    asyncio.run(w._tick())
    assert calls["executions"] == 0


def _holding_row(code, *, qty=1, price=165200, cur=168100):
    return {
        "stock_code": code, "stock_name": "KB금융", "quantity": qty,
        "avg_price": price, "current_price": cur,
        "profit_loss": 0, "profit_rate": 1.5,
    }


def test_buy_gate_subtracts_an_a_prefixed_holding_from_the_budget(monkeypatch):
    """Account holdings are A-prefixed; the roster is bare six digits.

    Compared raw, a held name is invisible to gate 2, so its existing
    exposure is not subtracted and the full budget is offered again — the
    failure the 2026-06-11 gates exist to prevent (HS화성, 예산 2.2배).
    Masked while max_positions=1 blocks anything new; this drives 2.
    """

    seen = {}

    async def fake_buy(client, **kwargs):
        seen.update(kwargs)
        return _rejected_order()

    monkeypatch.setattr(
        watcher_module.order_service, "place_stock_buy_order", fake_buy
    )
    w = _build_watcher(config=_config(max_positions=2))
    planner = {
        "portfolio": {"position_budget": 500_000, "max_positions": 2},
        "holdings": [_holding_row("A105560", qty=1, cur=168_100)],
    }
    event = TriggerEvent(
        trigger_type="new_candidate", tier=2, scope="stock",
        target_role=ROLE_SCREENER, stock_code="105560",
        stock_name="KB금융", snapshot={"score": 9, "entry_price": 168_100},
        detected_at=datetime.now(KST), reason="test",
    )

    asyncio.run(w._apply_candidate_action(event, "TIER1", planner))

    # 500,000 budget less the 168,100 already held leaves room for one more
    # share. Without normalisation the holding is not found, nothing is
    # subtracted, and the full budget buys two.
    assert int(seen.get("ord_qty")) == 1, seen


def test_normalize_stock_code_unifies_the_two_broker_spellings():
    from src.services.order_ledger import normalize_stock_code

    assert normalize_stock_code("A105560") == normalize_stock_code("105560")
    assert normalize_stock_code(" a105560 ") == "105560"
    assert normalize_stock_code(None) == ""


# --- Tier-2 sell pricing ----------------------------------------------------
#
# 2026-08-31: every Tier-2 exit was rejected 308003 (주문단가를 입력하십시요).
# The code sent trde_tp="0" -- 보통, a plain limit -- with an empty `ord_uv`,
# under a comment claiming "limit at best bid". The comment described what it
# should do; nothing implemented it. Latent since the watcher's first commit
# because the sell path had never run live until that day.


def _seen_sell(monkeypatch):
    """Capture the kwargs the watcher hands to the sell API."""

    seen: dict = {}

    async def fake_sell(client, **kwargs):
        seen.update(kwargs)
        return _ok_order(sell_order_result={"ord_no": "77"})

    monkeypatch.setattr(watcher_module.order_service, "place_stock_sell_order", fake_sell)
    return seen


def _book(bid):
    return {"orderbook": {"buy_fpr_bid": bid}}


@pytest.mark.parametrize("action", ["TAKE_PROFIT", "TRIM", "ROTATE"])
def test_discretionary_exit_prices_a_limit_at_the_best_bid(monkeypatch, action):
    seen = _seen_sell(monkeypatch)
    w = _build_watcher()

    result = asyncio.run(
        w._apply_action(_holding_event(), action, {}, detail=_book("+173300"))
    )

    assert result.state == "submitted"
    assert seen["order_type_code"] == "0"   # 보통 — requires a price
    assert seen["ord_uv"] == "173300"       # ...and now carries one


def test_price_comes_from_the_book_not_the_snapshot(monkeypatch):
    """A book level is tick-valid by construction; a derived one may not be."""

    seen = _seen_sell(monkeypatch)
    w = _build_watcher()
    event = _holding_event()
    event.snapshot["current_price"] = 173880  # off-tick, and not the bid

    asyncio.run(w._apply_action(event, "TAKE_PROFIT", {}, detail=_book("173500")))

    assert seen["ord_uv"] == "173500"


@pytest.mark.parametrize(
    "detail",
    [None, {}, {"orderbook": {}}, {"orderbook": {"buy_fpr_bid": "0"}}],
    ids=["no-bundle", "empty-bundle", "book-fetch-failed", "no-bid"],
)
def test_unpriceable_exit_still_goes_out_at_market(monkeypatch, detail):
    """A protective sell that cannot be priced must not be skipped.

    The fail-closed asymmetry runs the other way here: a blocked exit is
    worse than an unpriced one.
    """

    seen = _seen_sell(monkeypatch)
    w = _build_watcher()

    result = asyncio.run(
        w._apply_action(_holding_event(), "TAKE_PROFIT", {}, detail=detail)
    )

    assert result.state == "submitted"
    assert seen["order_type_code"] == "3"
    assert not seen.get("ord_uv")


def test_falling_back_to_market_is_logged(monkeypatch, caplog):
    """Otherwise a systematic book outage silently marketises every exit."""

    _seen_sell(monkeypatch)
    w = _build_watcher()

    with caplog.at_level(logging.WARNING, logger="kiwoom.watcher"):
        asyncio.run(w._apply_action(_holding_event(), "TAKE_PROFIT", {}, detail=None))

    assert any("exiting at market" in r.message for r in caplog.records)


def test_cut_loss_still_exits_at_market(monkeypatch):
    """An emergency exit must not rest in the book waiting for a fill."""

    seen = _seen_sell(monkeypatch)
    w = _build_watcher()

    asyncio.run(
        w._apply_action(_holding_event(), "CUT_LOSS", {}, detail=_book("173300"))
    )

    assert seen["order_type_code"] == "3"
    assert not seen.get("ord_uv")


def test_concurrent_exits_each_use_their_own_book(monkeypatch):
    """Two stocks in flight must not cross their prices.

    Drives the real sequence `_await_and_apply` uses -- fetch the bundle
    via `_is_still_valid`, then apply with it -- and makes the book fetch
    the point where the two tasks interleave. That is what a bundle parked
    on the watcher would get wrong: the second fetch overwrites the first,
    and both orders price off the same book. A wrong-price live order that
    looks correct in every log.
    """

    books = {
        "005930": {"quote": {"cur_prc": "70000"}, "orderbook": {"buy_fpr_bid": "70000"}},
        "105560": {"quote": {"cur_prc": "173300"}, "orderbook": {"buy_fpr_bid": "173300"}},
    }
    # Hold both fetches open until both have arrived, so neither task can
    # place its order before the other has fetched. A single shared slot is
    # then guaranteed to hold the loser's book when the winner prices.
    arrived = 0
    both_in = asyncio.Event()

    async def fake_bundle(client, *, stock_code, **kwargs):
        nonlocal arrived
        arrived += 1
        if arrived == 2:
            both_in.set()
        await both_in.wait()
        return books[stock_code]

    orders: list[dict] = []

    async def fake_sell(client, **kwargs):
        orders.append(kwargs)
        return _ok_order(sell_order_result={"ord_no": "77"})

    monkeypatch.setattr(market_module, "get_stock_detail_bundle", fake_bundle)
    monkeypatch.setattr(watcher_module.order_service, "place_stock_sell_order", fake_sell)
    w = _build_watcher()

    # In production this refreshes the broker's open orders over the network,
    # so it suspends between fetching the book and pricing the order -- which
    # is the window the two tasks interleave in. Model that; without a real
    # suspension point here the tasks run start-to-finish and no shared slot
    # could ever be observed being overwritten.
    real_sellable = w._sellable_quantity_now

    async def yielding_sellable(stock_code, held_quantity):
        await asyncio.sleep(0)
        return await real_sellable(stock_code, held_quantity)

    monkeypatch.setattr(w, "_sellable_quantity_now", yielding_sellable)

    async def exit_one(code, price):
        event = _holding_event(code=code)
        event.snapshot["current_price"] = price
        _valid, detail = await w._is_still_valid(event)
        await w._apply_action(event, "TAKE_PROFIT", {}, detail=detail)

    async def both():
        await asyncio.wait_for(
            asyncio.gather(exit_one("005930", 70000), exit_one("105560", 173300)),
            timeout=5,
        )

    asyncio.run(both())

    priced = {o["stk_cd"]: o["ord_uv"] for o in orders}
    assert priced == {"005930": "70000", "105560": "173300"}


def test_rejected_protective_sell_is_logged(monkeypatch, caplog):
    """The rejection reached Discord and the ledger and nowhere else.

    Seven failed exits in one session left the log silent, so grepping it
    for the outage found nothing.
    """

    async def fake_sell(client, **kwargs):
        return _rejected_order()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_sell_order", fake_sell)
    w = _build_watcher()
    event = _holding_event()

    with caplog.at_level(logging.WARNING, logger="kiwoom.watcher"):
        result = asyncio.run(
            w._apply_action(event, "TAKE_PROFIT", {}, detail=_book("173300"))
        )
        asyncio.run(w._notify_tier2_outcome(event, "TAKE_PROFIT", result, None))

    assert result.state == "failed"
    assert any("rejected" in r.message for r in caplog.records)


def _entry_account_rows(*holdings):
    return {
        "success": True,
        "evaluation_data": [{
            "prsm_dpst_aset_amt": "1000000",
            "entr": "500000",
            "tdy_lspft": "0",
            "stk_acnt_evlt_prst": list(holdings),
        }],
    }


def _use_real_entry_portfolio(watcher, monkeypatch, payload):
    from src.services import account

    async def account_read(client):
        return payload

    monkeypatch.setattr(account, "get_account_evaluation", account_read)
    watcher._refresh_entry_portfolio = IntradayWatcher._refresh_entry_portfolio.__get__(watcher)


def test_filled_buy_still_consumes_slot_from_fresh_holdings(monkeypatch):
    watcher = _build_watcher(config=_config(max_positions=1))
    intent = _seed_intent(watcher._ledger, stock_code="005930", side="buy", quantity=10, price=10000)
    watcher._ledger.mark_state(intent.intent_id, STATE_FILLED, filled_quantity=10)
    _use_real_entry_portfolio(watcher, monkeypatch, _entry_account_rows(
        {"stk_cd": "A005930", "rmnd_qty": "10", "cur_prc": "10000"}
    ))
    result = asyncio.run(watcher._apply_action(
        _candidate_event("000660"), "TIER1",
        {"holdings": [], "portfolio": {"position_budget": 100000, "max_positions": 1}},
    ))
    assert result.state == "skipped"
    assert "max_positions" in result.reason
    assert watcher._ledger.unresolved() == []


@pytest.mark.parametrize("payload", [
    {"success": False},
    {"success": True, "evaluation_data": []},
    {**_entry_account_rows(), "warning": "pagination truncated"},
    _entry_account_rows({"stk_cd": "005930", "rmnd_qty": "bad", "cur_prc": "10000"}),
    _entry_account_rows({"stk_cd": "005930", "rmnd_qty": "10", "cur_prc": ""}),
])
def test_new_buy_blocks_on_incomplete_fresh_account(monkeypatch, payload):
    watcher = _build_watcher()
    _use_real_entry_portfolio(watcher, monkeypatch, payload)
    result = asyncio.run(watcher._apply_action(
        _candidate_event(), "TIER1", {"portfolio": {"position_budget": 100000}},
    ))
    assert result.state == "skipped"
    assert "최신 잔고" in result.reason
    assert watcher._ledger.recent() == []


def test_entry_account_reads_holdings_on_later_pages(monkeypatch):
    watcher = _build_watcher(config=_config(max_positions=1))
    payload = _entry_account_rows()
    payload["evaluation_data"].append({"stk_acnt_evlt_prst": [
        {"stk_cd": "A005930", "rmnd_qty": "1", "cur_prc": "10000"},
    ]})
    _use_real_entry_portfolio(watcher, monkeypatch, payload)
    result = asyncio.run(watcher._apply_action(
        _candidate_event("000660"), "TIER1",
        {"portfolio": {"position_budget": 100000, "max_positions": 1}},
    ))
    assert result.state == "skipped"
    assert "max_positions" in result.reason


def test_concurrent_candidate_buys_cannot_exceed_daily_limit(monkeypatch):
    watcher = _build_watcher(config=_config(max_daily_new_entries=3))
    watcher._breaker.record_new_entry()
    watcher._breaker.record_new_entry()
    calls = []

    async def buy(client, **kwargs):
        calls.append(kwargs)
        await asyncio.sleep(0)
        return _ok_order()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", buy)

    async def run():
        return await asyncio.gather(*[
            watcher._apply_action(_candidate_event(code), "TIER1", {
                "portfolio": {"position_budget": 100000, "max_positions": 3},
            }) for code in ("005930", "000660")
        ])

    results = asyncio.run(run())
    assert sorted(result.state for result in results) == ["skipped", "submitted"]
    assert len(calls) == 1
    assert watcher._breaker.state.new_entries == 3


def test_new_buy_rechecks_session_after_account_read():
    watcher = _build_watcher()

    async def account_read(planner):
        watcher._market_session_status = lambda now=None: watcher_module.krx_regular_session_status(
            datetime(2026, 9, 4, 16, tzinfo=KST)
        )
        return planner

    watcher._refresh_entry_portfolio = account_read
    result = asyncio.run(watcher._apply_action(
        _candidate_event(), "TIER1", {"portfolio": {"position_budget": 100000}},
    ))
    assert result.state == "skipped"
    assert "정규장 종료" in result.reason
    assert watcher._ledger.recent() == []


@pytest.mark.parametrize("price", [None, "", "bad", "NaN", "Infinity", "0"])
def test_candidate_stale_check_fails_closed_on_invalid_quote(monkeypatch, price):
    async def quote(*args, **kwargs):
        return {"quote": {"cur_prc": price}}

    monkeypatch.setattr(market_module, "get_stock_detail_bundle", quote)
    watcher = _build_watcher()
    event = _candidate_event()
    event.snapshot["current_price"] = 10000
    valid, _ = asyncio.run(watcher._is_still_valid(event))
    assert valid is False


def test_candidate_peer_rejection_without_arbitration_blocks_buy(monkeypatch):
    class RejectingPeer(StubDispatcher):
        async def request_peer_review(self, *args, **kwargs):
            return ActionResponse(action="REJECT", output="REJECT", run_id="peer", completed_at=None)

        async def request_action_arbitration(self, *args, **kwargs):
            return None

    async def quote(*args, **kwargs):
        return {"quote": {"cur_prc": "10000"}}

    monkeypatch.setattr(market_module, "get_stock_detail_bundle", quote)
    watcher = _build_watcher(dispatcher=RejectingPeer(action="TIER1"))
    event = _candidate_event()
    event.snapshot["current_price"] = 10000
    entry = _entry_for(event)
    asyncio.run(watcher._await_and_apply(event, entry, "candidate-1", None, {}))
    assert entry.outcome == "skipped"
    assert "중재 미확정" in entry.detail
    assert watcher._ledger.recent() == []


def _fresh_dip_detail(price=9900):
    return {
        "quote": {
            "cur_prc": str(price), "open_pric": "9890", "high_pric": "10000",
            "pred_close_pric": "10000", "flu_rt": "-1",
        },
        "orderbook": {
            "buy_fpr_bid": str(price - 10), "sel_fpr_bid": str(price),
            "tot_buy_req": "20000", "tot_sel_req": "12000",
        },
        "daily_bars": [{"cur_prc": "10000"} for _ in range(20)],
    }


def test_entry_signal_is_rechecked_and_repriced_before_buy(monkeypatch):
    seen = []

    async def quote(*args, **kwargs):
        seen.append(kwargs)
        return _fresh_dip_detail()

    monkeypatch.setattr(market_module, "get_stock_detail_bundle", quote)
    watcher = _build_watcher(config=_config(entry_mode="below_ma", new_candidate_min_score=8))
    event = _candidate_event()
    event.snapshot.update(current_price=9900, entry_price="9890", sources=["value"])
    result = asyncio.run(IntradayWatcher._refresh_entry_candidate(watcher, event, {
        "regime": {"regime": "neutral", "market_data_complete": True},
    }))
    assert result.snapshot["entry_price"] == "9900"
    assert event.snapshot["entry_price"] == "9890"
    assert seen[0]["bar_limit"] >= 20


@pytest.mark.parametrize("regime,price", [
    ({"regime": "neutral", "market_data_complete": True}, 10010),
    ({"regime": "risk_off", "extreme_risk_off": True}, 9900),
    ({"regime": "neutral", "market_data_complete": False}, 9900),
])
def test_old_approval_cannot_override_changed_entry_conditions(monkeypatch, regime, price):
    async def quote(*args, **kwargs):
        return _fresh_dip_detail(price)

    monkeypatch.setattr(market_module, "get_stock_detail_bundle", quote)
    watcher = _build_watcher(config=_config(entry_mode="below_ma", new_candidate_min_score=8))
    watcher._prev_regime = regime
    event = _candidate_event()
    event.snapshot.update(current_price=9900, sources=["value"])
    with pytest.raises(ValueError):
        asyncio.run(IntradayWatcher._refresh_entry_candidate(watcher, event, {
            "regime": {"regime": "neutral", "market_data_complete": True},
        }))


def test_daily_entry_reservation_survives_response_loss_and_restart(monkeypatch, tmp_path):
    state_path = tmp_path / "risk.json"
    observed_at = datetime(2026, 9, 4, 10, tzinfo=KST)
    limits = DailyRiskLimits(max_daily_new_entries=1)
    watcher = _build_watcher(breaker=DailyEntryBreaker(limits, state_path=state_path, now=observed_at))

    async def interrupted_buy(client, **kwargs):
        restored = DailyEntryBreaker(limits, state_path=state_path, now=observed_at)
        assert restored.state.new_entries == 1
        raise asyncio.CancelledError()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", interrupted_buy)
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(watcher._apply_action(_candidate_event(), "TIER1", {
            "portfolio": {"position_budget": 100000, "max_positions": 3},
        }))
    restored = DailyEntryBreaker(limits, state_path=state_path, now=observed_at)
    assert not restored.check_new_entry().allowed


def test_definitive_buy_rejection_releases_daily_reservation(monkeypatch):
    watcher = _build_watcher(config=_config(max_daily_new_entries=1))

    async def rejected(client, **kwargs):
        assert watcher._breaker.state.new_entries == 1
        return _rejected_order()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", rejected)
    result = asyncio.run(watcher._apply_action(_candidate_event(), "TIER1", {
        "portfolio": {"position_budget": 100000, "max_positions": 3},
    }))
    assert result.state == "failed"
    assert watcher._breaker.state.new_entries == 0
    assert watcher._breaker.check_new_entry().allowed


def test_daily_reservation_write_failure_prevents_submission(monkeypatch, tmp_path):
    state_path = tmp_path / "risk.json"
    watcher = _build_watcher(breaker=DailyEntryBreaker(
        DailyRiskLimits(max_daily_new_entries=3), state_path=state_path,
    ))
    state_path.mkdir()

    async def forbidden(client, **kwargs):
        pytest.fail("must not submit an entry without a durable risk reservation")

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", forbidden)
    result = asyncio.run(watcher._apply_action(_candidate_event(), "TIER1", {
        "portfolio": {"position_budget": 100000, "max_positions": 3},
    }))
    assert result.state == "skipped"
    assert "저장 실패" in result.reason
    assert watcher._ledger.recent()[0].state == STATE_REJECTED


@pytest.mark.parametrize("broker_state", [STATE_FILLED, STATE_PARTIAL])
def test_late_rest_failure_cannot_release_broker_confirmed_entry(monkeypatch, broker_state):
    watcher = _build_watcher(config=_config(max_daily_new_entries=1))

    async def filled_then_rejected(client, **kwargs):
        intent = watcher._ledger.recent()[0]
        watcher._ledger.mark_state(intent.intent_id, broker_state, filled_quantity=1)
        return _rejected_order()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", filled_then_rejected)
    result = asyncio.run(watcher._apply_action(_candidate_event(), "TIER1", {
        "portfolio": {"position_budget": 100000, "max_positions": 3},
    }))
    assert result.state == "unknown"
    assert watcher._ledger.recent()[0].state == broker_state
    assert watcher._breaker.state.new_entries == 1
    assert not watcher._breaker.check_new_entry().allowed


def test_exit_only_mode_blocks_buys_but_preserves_stop_loss(monkeypatch):
    watcher = _build_watcher(config=_config(new_entries_enabled=False))
    calls = []

    async def sell(client, **kwargs):
        calls.append(kwargs)
        return _ok_order()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_sell_order", sell)
    buy = asyncio.run(watcher._apply_action(_candidate_event(), "TIER1", {}))
    event = _tier1_sell_event()
    stop = asyncio.run(watcher._execute_tier1(event, _entry_for(event)))
    assert buy.state == "skipped"
    assert stop.state == "submitted"
    assert len(calls) == 1


def test_two_approved_candidates_with_instant_fill_respect_single_position(monkeypatch):
    from src.services import account

    watcher = _build_watcher(config=_config(
        max_positions=1, position_budget_pct=40, max_daily_new_entries=3,
        entry_mode="below_ma", new_candidate_min_score=8,
    ))
    watcher._refresh_entry_portfolio = IntradayWatcher._refresh_entry_portfolio.__get__(watcher)
    watcher._refresh_entry_candidate = IntradayWatcher._refresh_entry_candidate.__get__(watcher)
    held = []
    calls = []

    async def account_read(client):
        return _entry_account_rows(*held)

    async def quote(*args, **kwargs):
        assert kwargs["bar_limit"] >= 20
        return _fresh_dip_detail()

    async def buy(client, **kwargs):
        calls.append(kwargs)
        held.append({"stk_cd": kwargs["stk_cd"], "rmnd_qty": kwargs["ord_qty"], "cur_prc": "9900"})
        await watcher._on_realtime_rows([{
            "stk_cd": kwargs["stk_cd"], "ord_no": "123", "io_tp_nm": "매수",
            "ord_qty": kwargs["ord_qty"], "ord_pric": "9900",
            "cntr_qty": kwargs["ord_qty"], "oso_qty": "0", "ord_stt": "체결",
            "ord_tmd": datetime.now(KST).strftime("%Y%m%d%H%M%S"),
        }])
        return _ok_order(buy_order_result={"ord_no": "123"})

    monkeypatch.setattr(account, "get_account_evaluation", account_read)
    monkeypatch.setattr(market_module, "get_stock_detail_bundle", quote)
    monkeypatch.setattr(watcher_module.order_service, "place_stock_buy_order", buy)

    async def run():
        events = [_candidate_event(code) for code in ("005930", "000660")]
        for event in events:
            event.snapshot.update(current_price=9900, sources=["value"])
        planner = {
            "holdings": [],
            "portfolio": {"position_budget": 100000, "max_positions": 1},
            "regime": {"regime": "neutral", "market_data_complete": True},
        }
        return await asyncio.gather(*[
            watcher._apply_action(event, "TIER1", planner) for event in events
        ])

    results = asyncio.run(run())
    assert sorted(result.state for result in results) == ["skipped", "submitted"]
    assert len(calls) == 1
    assert watcher._ledger.recent()[0].state == STATE_FILLED
    assert watcher._breaker.state.new_entries == 1


def test_stop_loss_preempts_agent_wait_and_invalidates_older_action(monkeypatch):
    watcher = _build_watcher()
    event = _holding_event("005930")
    calls = []

    async def sell(client, **kwargs):
        calls.append(kwargs)
        return _ok_order()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_sell_order", sell)
    watcher._in_flight[event.scope_key()] = object()
    stop = _tier1_sell_event()
    asyncio.run(watcher._handle_trigger(stop, planner_result={}))
    late = asyncio.run(watcher._apply_action(event, "TRIM", {}))
    assert len(calls) == 1
    assert late.state == "skipped"
    assert "오래된 agent" in late.reason


def test_tier1_retry_is_not_delayed_by_five_minute_agent_cooldown():
    watcher = _build_watcher(config=_config(cooldown_seconds=300, poll_interval_seconds=30))
    event = _tier1_sell_event()
    watcher._set_cooldown(event)
    remaining = (watcher._cooldowns[event.cooldown_key()] - datetime.now(KST)).total_seconds()
    assert 0 < remaining <= 30


@pytest.mark.parametrize("holding_page", [0, 1])
def test_hard_exit_runs_before_market_planner_failure(monkeypatch, holding_page):
    from src.services import account, strategy

    watcher = _build_watcher()
    calls = []

    async def account_read(client):
        result = _entry_account_rows({
            "stk_cd": "005930", "rmnd_qty": "10", "cur_prc": "9500",
            "avg_prc": "10000", "lspft_rt": "-5",
        })
        if holding_page:
            result["evaluation_data"].insert(0, {"stk_acnt_evlt_prst": []})
        return result

    async def unexecuted(*args, **kwargs):
        assert calls == ["protective_sell"]
        return {"success": True, "unexecuted_orders_data": []}

    async def failed_market(*args, **kwargs):
        assert calls == ["protective_sell"]
        raise RuntimeError("discretionary scanner down")

    async def sell(client, **kwargs):
        calls.append("protective_sell")
        return _ok_order()

    monkeypatch.setattr(account, "get_account_evaluation", account_read)
    monkeypatch.setattr(account, "get_unexecuted_orders", unexecuted)
    monkeypatch.setattr(market_module, "get_market_snapshot", failed_market)
    monkeypatch.setattr(watcher_module.order_service, "place_stock_sell_order", sell)
    monkeypatch.setattr(watcher_module, "plan_intraday_momentum_strategy", strategy.plan_intraday_momentum_strategy)
    with pytest.raises(RuntimeError, match="discretionary scanner down"):
        asyncio.run(watcher._tick())
    assert calls == ["protective_sell"]


def test_early_protective_rules_are_not_replayed_on_the_same_stale_snapshot(monkeypatch):
    watcher = _build_watcher()
    events = []
    holdings = [{"stock_code": "005930", "quantity": 10, "current_price": 9500, "profit_rate": -5}]

    async def planner(*args, holding_observer, **kwargs):
        await holding_observer(holdings)
        return {
            "success": True, "holdings": holdings, "candidate_rows": [],
            "portfolio": {"open_order_count": 0}, "regime": {},
        }

    async def handle(event, **kwargs):
        events.append(event)

    monkeypatch.setattr(watcher_module, "plan_intraday_momentum_strategy", planner)
    monkeypatch.setattr(watcher, "_handle_trigger", handle)
    asyncio.run(watcher._tick())
    assert len([event for event in events if event.trigger_type == "stop_loss"]) == 1


# --- protective triggers vs. older agent decisions ---------------------------
#
# A Tier-1 action that liquidates the position makes an in-flight agent
# decision obsolete: the code already sold. A cancel is Tier 1 and protective
# too, but it withdraws an *order*, not the holding — and it frees the shares,
# so an exit formed just before it is more executable afterwards, not less.
# Treating both alike let a stale-order cancel swallow a CUT_LOSS.
#
# Newly reachable: the stale-unfilled cancel had never fired in production
# until the ka10075 timestamp fix (2026-09-05).


def _tier1_event(action, code="005930"):
    return TriggerEvent(
        trigger_type="stale_unfilled_order" if action == "cancel_order" else "stop_loss",
        tier=1,
        scope="stock",
        target_role=ROLE_SELF,
        stock_code=code,
        stock_name="삼성전자",
        snapshot={"quantity": 1, "order_no": "419694"},
        detected_at=datetime.now(KST),
        reason="x",
        suggested_action=action,
    )


def _stale_decision(code="005930"):
    """An agent decision formed 90s ago — i.e. before whatever just happened."""

    return replace(
        _holding_event(code=code), detected_at=datetime.now(KST) - timedelta(seconds=90)
    )


def test_cancelling_an_order_does_not_discard_a_pending_exit(monkeypatch):
    """The cancel frees the shares; the exit is now more executable, not less."""

    sells: list = []

    async def fake_sell(client, **kwargs):
        sells.append(kwargs)
        return _ok_order()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_sell_order", fake_sell)
    w = _build_watcher()
    w._protective_trigger_at["005930"] = datetime.now(KST) - timedelta(seconds=30)

    # Only a liquidation registers, so a cancel leaves the registry untouched.
    w._protective_trigger_at.clear()
    result = asyncio.run(
        w._apply_action(_stale_decision(), "CUT_LOSS", {}, detail=_book("70000"))
    )

    assert result.state == "submitted"
    assert len(sells) == 1


def test_a_liquidation_still_discards_an_older_decision(monkeypatch):
    """The position is already gone; acting on the stale view would re-sell."""

    async def fake_sell(client, **kwargs):
        raise AssertionError("must not sell after the position was liquidated")

    monkeypatch.setattr(watcher_module.order_service, "place_stock_sell_order", fake_sell)
    w = _build_watcher()
    w._protective_trigger_at["005930"] = datetime.now(KST) - timedelta(seconds=30)

    result = asyncio.run(
        w._apply_action(_stale_decision(), "CUT_LOSS", {}, detail=_book("70000"))
    )

    assert result.state == "skipped"


def test_a_decision_formed_after_the_liquidation_is_honoured(monkeypatch):
    """Suppression is about staleness, not about the stock being touched."""

    sells: list = []

    async def fake_sell(client, **kwargs):
        sells.append(kwargs)
        return _ok_order()

    monkeypatch.setattr(watcher_module.order_service, "place_stock_sell_order", fake_sell)
    w = _build_watcher()
    w._protective_trigger_at["005930"] = datetime.now(KST) - timedelta(seconds=90)

    result = asyncio.run(
        w._apply_action(_holding_event(), "CUT_LOSS", {}, detail=_book("70000"))
    )

    assert result.state == "submitted"
    assert len(sells) == 1


@pytest.mark.parametrize(
    "action,registers",
    [("sell_market", True), ("cancel_order", False)],
    ids=["liquidation", "cancel"],
)
def test_only_a_liquidation_registers_as_superseding(action, registers):
    """Drives _handle_trigger: the predicate has to be fed the right events."""

    w = _build_watcher(config=_config(execute_orders=False, cooldown_seconds=0))

    asyncio.run(w._handle_trigger(_tier1_event(action), planner_result={}))

    assert ("005930" in w._protective_trigger_at) is registers
