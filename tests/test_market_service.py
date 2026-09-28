"""Tests for Kiwoom market-data service wrappers."""

from __future__ import annotations

import asyncio
import importlib
import os
import sys
from pathlib import Path
from typing import Any

os.environ.setdefault("KIWOOM_APPKEY", "dummy-appkey")
os.environ.setdefault("KIWOOM_SECRETKEY", "dummy-secretkey")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

market_module = importlib.import_module("src.services.market")


class DummyResponse:
    """Simple response stub for market service tests."""

    def __init__(self, payload: Any, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code
        self.headers: dict[str, str] = {}

    def json(self) -> Any:
        return self._payload


class DummyClient:
    """Client stub that dispatches payloads based on api-id and request body."""

    def __init__(self):
        self.calls: list[dict[str, Any]] = []

    async def post(
        self,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> DummyResponse:
        call = {
            "path": path,
            "headers": headers or {},
            "params": params,
            "json": json or {},
            "data": data,
        }
        self.calls.append(call)

        api_id = call["headers"].get("api-id")
        request = call["json"]

        if api_id == "ka10027":
            return DummyResponse(
                {
                    "pred_pre_flu_rt_upper": [
                        {"stk_cd": "005930", "stk_nm": "삼성전자"},
                        {"stk_cd": "000660", "stk_nm": "SK하이닉스"},
                    ],
                    "return_code": 0,
                    "return_msg": "정상적으로 처리되었습니다",
                }
            )
        if api_id == "ka20001" and request.get("inds_cd") == "001":
            return DummyResponse(
                {
                    "cur_prc": "+2600.00",
                    "flu_rt": "+1.20",
                    "rising": "500",
                    "fall": "300",
                    "inds_cur_prc_tm": [{"tm_n": "100000", "cur_prc_n": "+2600.00"}],
                    "return_code": 0,
                    "return_msg": "정상적으로 처리되었습니다",
                }
            )
        if api_id == "ka20001" and request.get("inds_cd") == "101":
            return DummyResponse(
                {
                    "cur_prc": "+900.00",
                    "flu_rt": "+0.80",
                    "rising": "700",
                    "fall": "400",
                    "inds_cur_prc_tm": [{"tm_n": "100000", "cur_prc_n": "+900.00"}],
                    "return_code": 0,
                    "return_msg": "정상적으로 처리되었습니다",
                }
            )
        if api_id == "ka20003":
            return DummyResponse(
                {
                    "all_inds_idex": [
                        {"stk_cd": "001", "stk_nm": "종합(KOSPI)"},
                        {"stk_cd": "002", "stk_nm": "대형주"},
                    ],
                    "return_code": 0,
                    "return_msg": "정상적으로 처리되었습니다",
                }
            )
        if api_id == "ka10030":
            return DummyResponse(
                {
                    "tdy_trde_qty_upper": [
                        {"stk_cd": "005930", "stk_nm": "삼성전자"},
                    ],
                    "return_code": 0,
                    "return_msg": "정상적으로 처리되었습니다",
                }
            )
        if api_id == "ka10032":
            return DummyResponse(
                {
                    "trde_prica_upper": [
                        {"stk_cd": "005930", "stk_nm": "삼성전자"},
                    ],
                    "return_code": 0,
                    "return_msg": "정상적으로 처리되었습니다",
                }
            )
        if api_id == "ka10007":
            return DummyResponse(
                {
                    "stk_cd": "005930",
                    "stk_nm": "삼성전자",
                    "cur_prc": "+70000",
                    "flu_rt": "+2.30",
                    "open_pric": "+69000",
                    "high_pric": "+70500",
                    "pred_close_pric": "68000",
                    "return_code": 0,
                    "return_msg": "정상적으로 처리되었습니다",
                }
            )
        if api_id == "ka10004":
            return DummyResponse(
                {
                    "sel_fpr_bid": "+70000",
                    "buy_fpr_bid": "+69900",
                    "tot_sel_req": "10000",
                    "tot_buy_req": "15000",
                    "return_code": 0,
                    "return_msg": "정상적으로 처리되었습니다",
                }
            )
        if api_id == "ka10005":
            return DummyResponse(
                {
                    "stk_ddwkmm": [
                        {"date": "20260325", "close_pric": "+70000"},
                        {"date": "20260324", "high_pric": "+69000", "close_pric": "+68000"},
                    ],
                    "return_code": 0,
                    "return_msg": "정상적으로 처리되었습니다",
                }
            )

        raise AssertionError(f"Unexpected api-id in test client: {api_id}")


def test_top_gainers_uses_documented_override_payload() -> None:
    """Top gainers should send the mrkt_tp and ETF exclusion fields."""

    client = DummyClient()

    result = asyncio.run(
        market_module.get_top_gainers(
            client,
            mrkt_tp="000",
            limit=2,
        )
    )

    assert result["success"] is True
    assert client.calls[0]["headers"]["api-id"] == "ka10027"
    assert client.calls[0]["json"]["mrkt_tp"] == "000"
    assert client.calls[0]["json"]["stk_cnd"] == "16"
    assert len(result["gainer_rows"]) == 2


def test_market_snapshot_aggregates_indices_leaders_and_watchlist() -> None:
    """The aggregated market snapshot should include leaders and watchlist details."""

    client = DummyClient()

    result = asyncio.run(
        market_module.get_market_snapshot(
            client,
            watchlist=["005930"],
            leaders_limit=3,
            sector_limit=2,
        )
    )

    assert result["success"] is True
    assert result["indices"]["kospi"]["cur_prc"] == "+2600.00"
    assert result["indices"]["kosdaq"]["cur_prc"] == "+900.00"
    assert len(result["leaders"]["gainers"]) == 2
    assert result["watchlist_details"][0]["quote"]["stk_nm"] == "삼성전자"
    assert result["watchlist_details"][0]["orderbook"]["tot_buy_req"] == "15000"


def test_stock_detail_bundle_can_reuse_ttl_cache() -> None:
    """Repeated detail reads should avoid quote/orderbook/daily API churn."""

    market_module._STOCK_DETAIL_CACHE.clear()
    client = DummyClient()

    first = asyncio.run(
        market_module.get_stock_detail_bundle(
            client,
            stock_code="005930",
            cache_ttl_seconds=60,
        )
    )
    second = asyncio.run(
        market_module.get_stock_detail_bundle(
            client,
            stock_code="005930",
            cache_ttl_seconds=60,
        )
    )

    assert first["success"] is True
    assert second["success"] is True
    assert second["cache_hit"] is True
    assert [call["headers"]["api-id"] for call in client.calls] == [
        "ka10007",
        "ka10004",
        "ka10005",
    ]
