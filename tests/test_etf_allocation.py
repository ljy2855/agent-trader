"""Allocation properties: cash reserve, whole shares, timing and bad data."""
from datetime import datetime
from zoneinfo import ZoneInfo
import asyncio
import math
import httpx
import pytest

from src.services.etf_allocation import allocation_orders, plan_etf_allocation, verified_assets
from src.services.krx_ticks import floor_to_etf_tick

KST = ZoneInfo("Asia/Seoul")
PRICES = {"069500": 100_000, "133690": 180_000}


def plan(holdings=(), day=5, assets=1_200_000, prices=None):
    return allocation_orders(assets=assets, holdings=list(holdings), prices=prices or PRICES,
                             now=datetime(2026, 10, day, 15, 20, tzinfo=KST))


def held(code, quantity):
    return {"stock_code": code, "stock_name": code, "quantity": quantity, "current_price": 100_000}


def test_seed_whole_shares_with_reserve_even_outside_monthly_window():
    p = plan(day=15)
    assert [(r["stock_code"], r["quantity"]) for r in p["buys"]] == [("069500", 5), ("133690", 3)]
    assert sum(r["quantity"] * r["current_price"] for r in p["buys"]) <= 1_200_000 * .94


def test_restart_or_small_price_drift_does_not_top_up_or_churn():
    assert plan([held("A069500", 5), held("133690", 3)]) == {"buys": [], "sells": []}


def test_held_positions_rebalance_only_in_monthly_window_and_outside_band():
    holdings = [held("069500", 8), held("133690", 1)]
    assert plan(holdings, day=15) == {"buys": [], "sells": []}
    p = plan(holdings)
    assert [(r["stock_code"], r["quantity"]) for r in p["sells"]] == [("069500", 3)]
    assert [(r["stock_code"], r["quantity"]) for r in p["buys"]] == [("133690", 2)]


def test_legacy_positions_are_explicit_migration_sells():
    p = plan([held("A005930", 1)], day=15)
    assert p["sells"][0]["stock_code"] == "005930"
    assert p["sells"][0]["quantity"] == 1


@pytest.mark.parametrize("assets", [0, -1, float("nan"), float("inf")])
def test_invalid_nav_blocks_allocation(assets):
    with pytest.raises(ValueError):
        plan(assets=assets)


def test_missing_quote_duplicate_holdings_and_fractional_quantities_block():
    with pytest.raises(ValueError):
        plan(prices={"069500": 100_000})
    with pytest.raises(ValueError):
        plan([held("069500", 1), held("A069500", 1)])
    with pytest.raises(ValueError):
        plan([held("069500", .5)])


def test_etf_price_units_are_not_stock_price_units():
    assert floor_to_etf_tick(105_658.9) == 105_655
    assert floor_to_etf_tick(1999.9) == 1999
    assert floor_to_etf_tick(2002) == 2000
    with pytest.raises(ValueError):
        floor_to_etf_tick(math.inf)


@pytest.mark.parametrize("value", [None, "", "-1200000", "0", "nan", "1.5"])
def test_broker_nav_cannot_be_missing_negative_or_coerced_from_invalid_data(value):
    with pytest.raises(ValueError):
        verified_assets({"prsm_dpst_aset_amt": value})


def test_broker_nav_accepts_zero_padding_and_separators():
    assert verified_assets({"prsm_dpst_aset_amt": "000001200000"}) == 1_200_000
    assert verified_assets({"prsm_dpst_aset_amt": "1,200,000"}) == 1_200_000


def stub_plan_sources(monkeypatch, *, holdings=None, orders=None, market_success=True):
    from src.services import account, market

    async def evaluation(*args, **kwargs):
        return {"success": True, "evaluation_data": [{
            "prsm_dpst_aset_amt": "000001200000", "d2_entra": "000001000000",
            "stk_acnt_evlt_prst": holdings if holdings is not None else [{
                "stk_cd": "A005930", "stk_nm": "legacy", "rmnd_qty": "000000000001",
                "cur_prc": "000000100000", "avg_prc": "000000099000",
            }],
        }]}

    async def unfilled(*args, **kwargs):
        return orders if orders is not None else {"success": True, "unexecuted_orders_data": []}

    async def snapshot(*args, **kwargs):
        return {"success": market_success,
                "indices": {m: {"rising": "500", "fall": "500", "flu_rt": "0"}
                            for m in ("kospi", "kosdaq")},
                "watchlist_details": [{"stock_code": code, "success": True,
                                       "quote": {"cur_prc": str(price)}}
                                      for code, price in PRICES.items()]}

    monkeypatch.setattr(account, "get_account_evaluation", evaluation)
    monkeypatch.setattr(account, "get_unexecuted_orders", unfilled)
    monkeypatch.setattr(market, "get_market_snapshot", snapshot)


def test_planner_reads_broker_shaped_rows_and_preserves_protective_observation(monkeypatch):
    observed = []
    stub_plan_sources(monkeypatch)

    async def observe(rows):
        observed.extend(rows)

    result = asyncio.run(plan_etf_allocation(None, None, holding_observer=observe))
    assert result["success"] is True
    assert result["portfolio"]["estimated_assets"] == 1_200_000
    assert result["allocation"]["sells"][0]["stock_code"] == "005930"
    assert observed[0]["quantity"] == 1


@pytest.mark.parametrize("orders, market_success, named", [
    ({"success": False, "unexecuted_orders_data": []}, True, "unexecuted_orders"),
    ({"success": True}, True, "unexecuted_orders"),
    ({"success": True, "unexecuted_orders_data": [], "warning": "pagination incomplete"}, True, "unexecuted_orders"),
    ({"success": True, "unexecuted_orders_data": []}, False, "market_snapshot"),
])
def test_incomplete_market_or_orders_blocks_routine_migration_but_observes_holdings(monkeypatch, orders, market_success, named):
    observed = []
    stub_plan_sources(monkeypatch, orders=orders, market_success=market_success)

    async def observe(rows):
        observed.extend(rows)

    result = asyncio.run(plan_etf_allocation(None, None, holding_observer=observe))
    assert result["success"] is False
    assert result["allocation"] == {"sells": [], "buys": []}
    assert observed[0]["quantity"] == 1
    # The plan names the read that held it back; the watcher's failure
    # detail is built from this and said "no source breakdown" without it.
    assert [entry["source"] for entry in result["degraded_sources"]] == [named]


def test_a_healthy_plan_names_no_degraded_source(monkeypatch):
    stub_plan_sources(monkeypatch)

    result = asyncio.run(plan_etf_allocation(None, None))

    assert result["success"] is True and result["degraded_sources"] == []


def test_the_watcher_failure_detail_names_the_etf_plans_failed_read(monkeypatch):
    from src.services.watcher import _describe_degraded_sources

    stub_plan_sources(monkeypatch, orders={
        "success": True, "unexecuted_orders_data": [], "warning": "pagination incomplete",
    })

    result = asyncio.run(plan_etf_allocation(None, None))

    assert _describe_degraded_sources(result) == (
        "planner degraded — unexecuted_orders: pagination incomplete"
    )


class _Kiwoom:
    """A client whose every request ends the way `outcome` says: an httpx
    error raised, or a body answered. The reads under test are the real ones,
    so the failure reaches the planner in the shape production gives it."""

    def __init__(self, outcome):
        self.outcome = outcome

    async def post(self, *args, **kwargs):
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return httpx.Response(200, json=self.outcome)


@pytest.mark.parametrize("outcome, named", [
    (httpx.ReadTimeout(""), "ReadTimeout"),  # httpx timeouts stringify to ""
    (httpx.RemoteProtocolError("Server disconnected without sending a response."), "Server disconnected"),
    ({"return_code": 3, "return_msg": "인증에 실패했습니다[8001:App Key와 Secret Key 검증에 실패했습니다]"},
     "인증에 실패했습니다[8001"),
])
def test_a_failed_account_read_says_why(outcome, named):
    """Three single ticks stopped here on 2026-11-12 with "계좌 조회 불완전" and
    nothing else: the log could not tell a timeout from a dropped connection
    from a broker error, because the read's own reason was left behind."""

    with pytest.raises(ValueError, match="계좌 조회 불완전 — ") as raised:
        asyncio.run(plan_etf_allocation(_Kiwoom(outcome), None))

    assert named in str(raised.value)


def test_a_failed_etf_quote_names_the_etf_and_the_reason(monkeypatch):
    from src.services import market

    stub_plan_sources(monkeypatch, holdings=[])

    async def snapshot(client, **kwargs):
        # The second ETF's quote, orderbook and daily bars all time out.
        failed = await market.get_stock_detail_bundle(_Kiwoom(httpx.ReadTimeout("")), stock_code="133690")
        return {"success": False, "indices": {}, "watchlist_details": [
            {"stock_code": "069500", "success": True, "quote": {"cur_prc": "100000"}}, failed,
        ]}

    monkeypatch.setattr(market, "get_market_snapshot", snapshot)

    with pytest.raises(ValueError, match=r"ETF 시세 조회 불완전\(133690\) — ReadTimeout"):
        asyncio.run(plan_etf_allocation(None, None))


@pytest.mark.parametrize("holdings", [
    [{"stk_cd": "A005930", "rmnd_qty": "-1"}],
    [{"stk_cd": "", "rmnd_qty": "1"}],
    ["invalid row"],
])
def test_malformed_broker_holdings_never_produce_allocation_orders(monkeypatch, holdings):
    stub_plan_sources(monkeypatch, holdings=holdings)
    with pytest.raises(ValueError):
        asyncio.run(plan_etf_allocation(None, None))
