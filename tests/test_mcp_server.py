"""Smoke tests for the Kiwoom MCP server."""

from __future__ import annotations

import asyncio
import importlib
import os
import sys
from pathlib import Path

from fastmcp import Client
import pytest

os.environ.setdefault("KIWOOM_APPKEY", "dummy-appkey")
os.environ.setdefault("KIWOOM_SECRETKEY", "dummy-secretkey")
os.environ.setdefault("KIWOOM_USE_MOCK", "false")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

mcp_server_module = importlib.import_module("src.mcp_server")
account_module = importlib.import_module("src.services.account")
strategy_module = importlib.import_module("src.services.strategy")


@pytest.fixture(autouse=True)
def isolated_background_state(monkeypatch, tmp_path):
    engine_class = mcp_server_module.BackgroundTradeEngine
    monkeypatch.setattr(
        mcp_server_module, "BackgroundTradeEngine",
        lambda settings: engine_class(settings, state_path=tmp_path / "engine.json"),
    )


def _settings(**overrides):
    from src.config import Settings

    values = dict(
        _env_file=None, KIWOOM_USE_MOCK=False,
        KIWOOM_APPKEY="dummy", KIWOOM_SECRETKEY="dummy",
        KIWOOM_ALLOW_DIRECT_LIVE_ORDERS=False,
    )
    values.update(overrides)
    return Settings(**values)


def _list_tools(settings, monkeypatch) -> dict:
    monkeypatch.setattr(mcp_server_module, "get_settings", lambda: settings)

    async def run() -> dict:
        server = mcp_server_module.create_mcp_server()
        try:
            async with Client(server.mcp) as client:
                return {tool.name: tool for tool in await client.list_tools()}
        finally:
            await server.close()

    return asyncio.run(run())


ORDER_AND_ENGINE_TOOLS = {
    "place_stock_buy_order", "place_stock_sell_order",
    "modify_stock_order", "cancel_stock_order",
    "get_background_trade_engine_status", "update_background_trade_engine_config",
    "start_background_trade_engine", "pause_background_trade_engine",
    "resume_background_trade_engine", "stop_background_trade_engine",
}


def test_server_registers_expected_tools(monkeypatch) -> None:
    """A live process lists the read tools and nothing it would refuse."""

    tools = _list_tools(_settings(), monkeypatch)
    tool_names = set(tools)
    for name in (
        "get_account_current_status", "get_account_evaluation",
        "get_order_execution_status", "get_market_snapshot",
        "plan_intraday_momentum_strategy", "get_unexecuted_orders",
        # Added 2026-09-27 for the agents' own checks.
        "get_stock_quote", "get_stock_daily_bars", "get_order_ledger",
    ):
        assert name in tool_names, name

    # Unlisted, not merely refused: the agents read this list, and the
    # legacy engine's execute_orders=false was taken for the live system.
    assert not tool_names & ORDER_AND_ENGINE_TOOLS
    assert "run_mock_intraday_momentum_strategy" not in tool_names

    execution_tool = tools["get_execution_info"]
    assert execution_tool.input_schema["properties"]["sell_tp"]["enum"] == ["0", "1", "2"]
    assert execution_tool.description.startswith("API `ka10076`")

    # MA20 plus a 20-day volume average needs the latest bar and 20 before it.
    bars_limit = tools["get_stock_daily_bars"].input_schema["properties"]["limit"]
    assert bars_limit["minimum"] == 21

    # Strategy shaping arguments default to the deployment, so every
    # one of them has to be optional. Leaving any required would put
    # a code default back in front of the live config.
    schema = tools["plan_intraday_momentum_strategy"].input_schema
    props = schema["properties"]
    for name in ("entry_mode", "universe_mode", "min_market_cap_krw",
                 "auto_buy_min_score", "position_budget_pct",
                 "leaders_market_tp", "stop_loss_pct"):
        assert name in props, name
        assert name not in schema.get("required", []), name
        assert props[name].get("default", "unset") is None, name
    # The live budget has been 60 since 2026-09-10; a ceiling of
    # 50 meant the tool could not be asked to match the account.
    budget = props["position_budget_pct"]
    bounds = budget.get("anyOf") or [budget]
    maxima = [b["maximum"] for b in bounds if "maximum" in b]
    assert maxima == [100], maxima


def test_mock_server_lists_order_and_engine_tools(monkeypatch) -> None:
    tools = _list_tools(
        _settings(
            KIWOOM_USE_MOCK=True,
            KIWOOM_MOCK_APPKEY="dummy", KIWOOM_MOCK_SECRETKEY="dummy",
        ),
        monkeypatch,
    )

    assert ORDER_AND_ENGINE_TOOLS <= set(tools)
    buy_order_tool = tools["place_stock_buy_order"]
    assert buy_order_tool.input_schema["properties"]["confirm_live_order"]["const"] is True
    assert buy_order_tool.input_schema["properties"]["order_type_code"]["enum"][0] == "0"
    assert buy_order_tool.input_schema["properties"]["dmst_stex_tp"]["default"] == "KRX"
    assert buy_order_tool.description.startswith("ORDER SUBMISSION: API `kt10000`")

    strategy_tool = tools["run_mock_intraday_momentum_strategy"]
    schema = strategy_tool.input_schema
    assert schema["properties"]["confirm_mock_strategy_execution"]["const"] is True
    for name in ("entry_mode", "universe_mode", "position_budget_pct"):
        assert name not in schema.get("required", []), name
        assert schema["properties"][name].get("default", "unset") is None, name


def test_live_opt_in_lists_order_tools_but_not_mock_strategy(monkeypatch) -> None:
    tools = _list_tools(_settings(KIWOOM_ALLOW_DIRECT_LIVE_ORDERS=True), monkeypatch)

    assert ORDER_AND_ENGINE_TOOLS <= set(tools)
    assert "run_mock_intraday_momentum_strategy" not in tools


def test_mcp_tool_call_returns_structured_data(monkeypatch) -> None:
    """A tool should be callable through the FastMCP client."""

    async def fake_get_account_current_status(client):
        return {"status": "ok", "source": "smoke-test"}

    monkeypatch.setattr(
        account_module,
        "get_account_current_status",
        fake_get_account_current_status,
    )

    async def run_test() -> None:
        server = mcp_server_module.create_mcp_server()
        try:
            async with Client(server.mcp) as client:
                result = await client.call_tool("get_account_current_status", {})
                assert result.is_error is False
                assert result.data == {"status": "ok", "source": "smoke-test"}
        finally:
            await server.close()

    asyncio.run(run_test())


def test_strategy_tool_is_callable(monkeypatch) -> None:
    """The strategy planning tool should be callable through the FastMCP client."""

    async def fake_plan_strategy(client, settings, **kwargs):
        return {"status": "ok", "strategy": "dry-run", "kwargs": kwargs}

    monkeypatch.setattr(
        strategy_module,
        "plan_intraday_momentum_strategy",
        fake_plan_strategy,
    )

    async def run_test() -> None:
        server = mcp_server_module.create_mcp_server()
        try:
            async with Client(server.mcp) as client:
                result = await client.call_tool(
                    "plan_intraday_momentum_strategy",
                    {
                        "leaders_limit": 8,
                        "candidate_limit": 4,
                        "max_positions": 3,
                        "max_new_positions": 1,
                        "position_budget_pct": 10,
                    },
                )
                assert result.is_error is False
                assert result.data["status"] == "ok"
                assert result.data["kwargs"]["leaders_limit"] == 8
        finally:
            await server.close()

    asyncio.run(run_test())


def test_dashboard_routes_are_registered() -> None:
    """The dashboard HTTP routes, including the agent endpoints, exist."""

    async def run_test() -> None:
        server = mcp_server_module.create_mcp_server()
        try:
            app = server.mcp.http_app()
            paths = {getattr(route, "path", None) for route in app.routes}
            assert "/api/dashboard" in paths
            assert "/api/agent_overview" in paths
            # Separate from the overview on purpose: its Multica comment fan-out
            # costs seconds and must not block the live status card.
            assert "/api/agent_timeline" in paths
        finally:
            await server.close()

    asyncio.run(run_test())


def test_agent_timeline_rejects_non_iso_dates() -> None:
    """The timeline keys Multica issue titles, so it takes ISO YYYY-MM-DD.

    Regression guard: it originally reused the Kiwoom YYYYMMDD validator, which
    rejected every date an <input type="date"> produces.
    """

    from starlette.testclient import TestClient

    async def run_test() -> None:
        server = mcp_server_module.create_mcp_server()
        try:
            with TestClient(server.mcp.http_app()) as client:
                assert client.get("/api/agent_timeline?date=20260813").status_code == 400
                assert client.get("/api/agent_timeline?date=nonsense").status_code == 400
                # A well-formed date must not be rejected by validation.
                resp = client.get("/api/agent_timeline?date=2026-08-13")
                assert resp.status_code != 400
        finally:
            await server.close()

    asyncio.run(run_test())


@pytest.mark.parametrize("tool_name,arguments", [
    ("place_stock_buy_order", {"stk_cd": "005930", "ord_qty": "1", "order_type_code": "3"}),
    ("place_stock_sell_order", {"stk_cd": "005930", "ord_qty": "1", "order_type_code": "3"}),
    ("modify_stock_order", {"stk_cd": "005930", "orig_ord_no": "123", "mdfy_qty": "1", "mdfy_uv": "10000"}),
    ("cancel_stock_order", {"stk_cd": "005930", "orig_ord_no": "123", "cncl_qty": "0"}),
])
def test_live_mcp_orders_cannot_be_called_even_with_tool_confirmation(
    monkeypatch, tool_name, arguments
):
    monkeypatch.setattr(mcp_server_module, "get_settings", lambda: _settings())
    submitted = []

    async def fake_order(*args, **kwargs):
        submitted.append((args, kwargs))
        return {"success": True}

    for name in ("place_stock_buy_order", "place_stock_sell_order",
                 "modify_stock_order", "cancel_stock_order"):
        monkeypatch.setattr(mcp_server_module.order, name, fake_order)

    async def run():
        server = mcp_server_module.create_mcp_server()
        try:
            async with Client(server.mcp) as client:
                result = await client.call_tool(
                    tool_name, {"confirm_live_order": True, **arguments}, raise_on_error=False,
                )
                assert result.is_error
        finally:
            await server.close()

    asyncio.run(run())
    assert submitted == []


def test_call_time_guard_still_refuses_live_orders(monkeypatch):
    """Unlisting is the outer layer; the per-call check stays underneath."""

    monkeypatch.setattr(mcp_server_module, "get_settings", lambda: _settings())

    async def run():
        server = mcp_server_module.create_mcp_server()
        try:
            with pytest.raises(ValueError, match="Direct live orders are disabled"):
                server._require_direct_order_permission()
        finally:
            await server.close()

    asyncio.run(run())


SAMPLE_QUOTE = {
    "stk_nm": "삼성전자", "stk_cd": "005930", "date": "20260923", "tm": "153000",
    "pred_close_pric": "276500", "upl_pric": "+359000", "lst_pric": "-194000",
    "flo_stkcnt": "5846279", "cur_prc": "+286500", "flu_rt": "+3.62", "pred_rt": "+114.91",
    "open_pric": "+284500", "high_pric": "+286500", "low_pric": "+281000",
    "trde_qty": "20864376", "trde_prica": "5926487",
    "sel_1bid": "+286500", "sel_2bid": "+287000", "buy_1bid": "+286000", "buy_2bid": "+285500",
    "sel_1bid_req": "97775", "sel_2bid_req": "99296",
    "buy_1bid_req": "42115", "buy_2bid_req": "72633",
    "tot_buy_req": "443260", "tot_sel_req": "489605",
}


def test_get_stock_quote_tool_returns_the_summary(monkeypatch):
    market_module = importlib.import_module("src.services.market")

    async def fake_quote(client, *, stock_code):
        return {"success": True, "quote": SAMPLE_QUOTE}

    monkeypatch.setattr(market_module, "get_stock_quote", fake_quote)
    monkeypatch.setattr(mcp_server_module, "get_settings", lambda: _settings())

    async def run():
        server = mcp_server_module.create_mcp_server()
        try:
            async with Client(server.mcp) as client:
                result = await client.call_tool("get_stock_quote", {"stock_code": "005930"})
                data = result.data
                assert data["success"] is True
                assert data["price"] == 286500
                assert data["upper_limit"] == 359000
                assert data["orderbook_ratio"] == round(443260 / 489605, 2)
                assert data["bids"][0] == {"price": 286000, "quantity": 42115}
        finally:
            await server.close()

    asyncio.run(run())


def test_get_stock_quote_tool_reports_broker_failure(monkeypatch):
    market_module = importlib.import_module("src.services.market")

    async def failing_quote(client, *, stock_code):
        return {"success": False, "error": "1511:필수입력 파라미터", "message": "x"}

    monkeypatch.setattr(market_module, "get_stock_quote", failing_quote)
    monkeypatch.setattr(mcp_server_module, "get_settings", lambda: _settings())

    async def run():
        server = mcp_server_module.create_mcp_server()
        try:
            async with Client(server.mcp) as client:
                result = await client.call_tool("get_stock_quote", {"stock_code": "005930"})
                assert result.data["success"] is False
                assert "1511" in result.data["error"]
        finally:
            await server.close()

    asyncio.run(run())


def test_get_order_ledger_tool_passes_filters_to_the_watcher(monkeypatch):
    seen = {}

    async def fake_fetch(*, limit, trading_day):
        seen.update(limit=limit, trading_day=trading_day)
        return {"available": True, "unresolved": [], "recent": []}

    monkeypatch.setattr(mcp_server_module, "fetch_watcher_ledger", fake_fetch)
    monkeypatch.setattr(mcp_server_module, "get_settings", lambda: _settings())

    async def run():
        server = mcp_server_module.create_mcp_server()
        try:
            async with Client(server.mcp) as client:
                result = await client.call_tool(
                    "get_order_ledger", {"limit": 10, "trading_day": "2026-09-23"}
                )
                assert result.data["available"] is True
                bad = await client.call_tool(
                    "get_order_ledger", {"trading_day": "20260923"}, raise_on_error=False
                )
                assert bad.is_error
        finally:
            await server.close()

    asyncio.run(run())
    assert seen == {"limit": 10, "trading_day": "2026-09-23"}


def test_live_background_execution_cannot_bypass_watcher_gate(tmp_path):
    from src.config import Settings
    from src.trade_engine import BackgroundTradeEngine

    settings = Settings(
        _env_file=None, KIWOOM_USE_MOCK=False,
        KIWOOM_APPKEY="dummy", KIWOOM_SECRETKEY="dummy",
        KIWOOM_ALLOW_DIRECT_LIVE_ORDERS=False,
    )
    engine = BackgroundTradeEngine(settings, state_path=tmp_path / "engine.json")

    async def run():
        started = await engine.start(execute_orders=True, confirm_live_execution=True)
        updated = await engine.update_config(execute_orders=True)
        assert not started["success"]
        assert not updated["success"]
        assert engine._task is None
        assert not engine._config.execute_orders

    asyncio.run(run())
