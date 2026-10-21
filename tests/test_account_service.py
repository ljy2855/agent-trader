"""Tests for Kiwoom account service wrappers."""

from __future__ import annotations

import asyncio
import importlib
import os
import sys
from pathlib import Path
from typing import Any

import httpx

os.environ.setdefault("KIWOOM_APPKEY", "dummy-appkey")
os.environ.setdefault("KIWOOM_SECRETKEY", "dummy-secretkey")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

account_module = importlib.import_module("src.services.account")


class DummyResponse:
    """Simple response stub for service-layer tests."""

    def __init__(self, payload: Any, headers: dict[str, str] | None = None, status_code: int = 200):
        self._payload = payload
        self.headers = headers or {}
        self.status_code = status_code

    def json(self) -> Any:
        return self._payload


class DummyClient:
    """Simple client stub that records outbound POST calls."""

    def __init__(self, payload: Any, headers: dict[str, str] | None = None):
        self._payload = payload
        self._headers = headers or {}
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
        self.calls.append(
            {
                "path": path,
                "headers": headers or {},
                "params": params,
                "json": json,
                "data": data,
            }
        )
        return DummyResponse(self._payload, headers=self._headers)


class PagedDummyClient(DummyClient):
    """Fixture client that serves a finite sequence of paginated responses."""

    def __init__(self, pages: list[tuple[Any, dict[str, str]]]):
        super().__init__({})
        self._pages = list(pages)

    async def post(self, path: str, **kwargs: Any) -> DummyResponse:
        self.calls.append({"path": path, **kwargs})
        payload, headers = self._pages.pop(0)
        return DummyResponse(payload, headers=headers)


def test_business_error_is_not_reported_as_success() -> None:
    """Non-zero Kiwoom return codes should not be reported as successful."""

    client = DummyClient(
        {
            "return_code": 20,
            "return_msg": "[2000](571489:장이 열리지 않는 날입니다.)",
        }
    )

    result = asyncio.run(
        account_module.get_orderable_amount(
            client,
            stk_cd="005490",
            trde_tp="2",
            uv="343500",
        )
    )

    assert result["success"] is False
    assert result["return_code"] == 20
    assert "장이 열리지 않는 날입니다" in result["error"]
    assert result["orderable_amount_data"] == []


def test_execution_info_uses_filled_order_api() -> None:
    """Execution history wrapper should call the ka10076 endpoint contract."""

    client = DummyClient(
        {
            "cntr": [],
            "return_code": 0,
            "return_msg": "조회가 완료되었습니다.",
        }
    )

    result = asyncio.run(
        account_module.get_execution_info(
            client,
            qry_tp="0",
            sell_tp="0",
            stex_tp="0",
        )
    )

    assert result["success"] is True
    assert client.calls[0]["headers"]["api-id"] == "ka10076"
    assert client.calls[0]["json"] == {
        "qry_tp": "0",
        "sell_tp": "0",
        "stex_tp": "0",
    }


def test_unexecuted_orders_uses_complete_ka10075_contract() -> None:
    """Absence evidence must cover every stock, side and exchange venue.

    ``all_stk_tp`` is asserted present on purpose. It is absent from the
    ka10075 body table in `kiwoom_api_spec.md`, so it looks like dead weight,
    but the live broker rejects the call without it::

        입력 값 오류입니다[1511:필수 입력 값에 값이 존재하지 않습니다.
        필수입력 파라미터=all_stk_tp]

    That failure took down every open-order read on 2026-07-28. Do not "clean
    this up" to match the spec document.
    """

    client = DummyClient(
        {
            "oso": [],
            "return_code": 0,
            "return_msg": "조회가 완료되었습니다.",
        }
    )

    result = asyncio.run(
        account_module.get_unexecuted_orders(
            client,
            all_stk_tp="0",
            trde_tp="0",
            stex_tp="0",
        )
    )

    assert result["success"] is True
    assert client.calls[0]["headers"]["api-id"] == "ka10075"
    assert client.calls[0]["json"] == {
        "all_stk_tp": "0",
        "trde_tp": "0",
        "stex_tp": "0",
    }


def test_ka10075_and_ka10076_follow_pagination_to_a_complete_view() -> None:
    """A clean absence decision may use only a view whose final page arrived."""

    open_client = PagedDummyClient(
        [
            (
                {"oso": [{"ord_no": "1"}], "return_code": 0},
                {"cont-yn": "Y", "next-key": "open-page-2"},
            ),
            ({"oso": [{"ord_no": "2"}], "return_code": 0}, {}),
        ]
    )
    open_result = asyncio.run(
        account_module.get_unexecuted_orders(
            open_client, all_stk_tp="0", trde_tp="0", stex_tp="0"
        )
    )

    assert open_result["success"] is True
    assert open_result["total_requests"] == 2
    assert [row["ord_no"] for row in open_result["unexecuted_orders_data"]] == [
        "1",
        "2",
    ]
    assert open_client.calls[1]["headers"]["cont-yn"] == "Y"
    assert open_client.calls[1]["headers"]["next-key"] == "open-page-2"

    fill_client = PagedDummyClient(
        [
            (
                {"cntr": [{"ord_no": "3"}], "return_code": 0},
                {"cont-yn": "Y", "next-key": "fill-page-2"},
            ),
            ({"cntr": [{"ord_no": "4"}], "return_code": 0}, {}),
        ]
    )
    fill_result = asyncio.run(
        account_module.get_execution_info(
            fill_client, qry_tp="0", sell_tp="0", stex_tp="0"
        )
    )

    assert fill_result["success"] is True
    assert fill_result["total_requests"] == 2
    assert [row["ord_no"] for row in fill_result["execution_data"]] == ["3", "4"]
    assert fill_client.calls[1]["headers"]["cont-yn"] == "Y"
    assert fill_client.calls[1]["headers"]["next-key"] == "fill-page-2"


def test_order_absence_queries_reject_malformed_or_incomplete_success_payloads() -> None:
    missing_list = DummyClient({"return_code": 0, "return_msg": "정상"})
    execution = asyncio.run(
        account_module.get_execution_info(
            missing_list, qry_tp="0", sell_tp="0", stex_tp="0"
        )
    )
    assert execution["success"] is False
    assert "missing list field" in execution["error"]

    missing_cursor = DummyClient(
        {"oso": [], "return_code": 0},
        headers={"cont-yn": "Y"},
    )
    open_orders = asyncio.run(
        account_module.get_unexecuted_orders(
            missing_cursor, all_stk_tp="0", trde_tp="0", stex_tp="0"
        )
    )
    assert open_orders["success"] is False
    assert "pagination incomplete" in open_orders["error"]


def test_order_execution_status_uses_kt00009_contract() -> None:
    """Order/execution status wrapper should use the kt00009 request schema."""

    client = DummyClient(
        {
            "acnt_ord_cntr_prst_array": [],
            "return_code": 0,
            "return_msg": "조회가 완료되었습니다.",
        }
    )

    result = asyncio.run(
        account_module.get_order_execution_status(
            client,
            stk_bond_tp="1",
            mrkt_tp="0",
            sell_tp="0",
            qry_tp="0",
            dmst_stex_tp="KRX",
        )
    )

    assert result["success"] is True
    assert client.calls[0]["headers"]["api-id"] == "kt00009"
    assert client.calls[0]["json"] == {
        "stk_bond_tp": "1",
        "mrkt_tp": "0",
        "sell_tp": "0",
        "qry_tp": "0",
        "dmst_stex_tp": "KRX",
    }


def test_period_realized_profit_reads_ka10073_over_the_range() -> None:
    """ka10073 takes both dates; ka10072 answered for the start day only."""

    client = DummyClient(
        {
            "return_code": 0,
            "return_msg": "조회가 완료되었습니다.",
            "dt_stk_rlzt_pl": [
                {"dt": "20260306", "stk_nm": "삼성전자", "stk_cd": "005930", "cntr_qty": "1",
                 "buy_uv": "70000", "cntr_pric": "68000", "tdy_sel_pl": "-2196", "pl_rt": "-2.86",
                 "tdy_trde_cmsn": "60", "tdy_trde_tax": "136"},
            ],
        }
    )

    result = asyncio.run(account_module.get_period_realized_profit(client, "20260301", "20260331"))

    assert client.calls[0]["headers"]["api-id"] == "ka10073"
    # The body the live endpoint answered on 2026-10-14.
    assert client.calls[0]["json"] == {"strt_dt": "20260301", "end_dt": "20260331"}
    assert result["success"] is True
    assert result["realized_profit_data"][0]["tdy_sel_pl"] == "-2196"


def test_trade_history_reads_kt00015_trades() -> None:
    client = DummyClient(
        {
            "acnt_no": "",
            "return_code": 0,
            "return_msg": "조회가 완료되었습니다",
            "trst_ovrl_trde_prps_array": [
                {"trde_dt": "20260310", "cntr_dt": "20260306", "io_tp_nm": "매도", "trde_kind_nm": "매매",
                 "stk_cd": "A005930", "stk_nm": "삼성전자", "trde_qty_jwa_cnt": "1", "trde_unit": "68,000",
                 "trde_amt": "000000000068000", "tax_sum_cmsn": "000000000000166"},
            ],
        }
    )

    result = asyncio.run(account_module.get_trade_history(client, "20260301", "20260331"))

    assert client.calls[0]["headers"]["api-id"] == "kt00015"
    # The body the live endpoint answered on 2026-10-14; the spec table in the
    # repo lists `end_dt` but not `strt_dt`.
    assert client.calls[0]["json"] == {
        "strt_dt": "20260301",
        "end_dt": "20260331",
        "tp": "3",
        "stk_cd": "",
        "crnc_cd": "",
        "gds_tp": "1",
        "frgn_stex_code": "",
        "dmst_stex_tp": "%",
    }
    assert result["trade_history_data"][0]["cntr_dt"] == "20260306"


def test_trading_journal_sends_base_dt_only_when_given() -> None:
    """Today's call keeps the body it always had; a past day adds `base_dt`."""

    payload = {"return_code": 0, "return_msg": "조회가 완료되었습니다.", "tdy_trde_diary": []}
    today = DummyClient(payload)
    past = DummyClient(payload)

    asyncio.run(account_module.get_daily_trading_journal(today))
    asyncio.run(account_module.get_daily_trading_journal(past, base_dt="20260306"))

    assert today.calls[0]["json"] == {"ottks_tp": "2", "ch_crd_tp": "0"}
    assert past.calls[0]["json"] == {"ottks_tp": "2", "ch_crd_tp": "0", "base_dt": "20260306"}


class RaisingClient:
    """Client stub whose POST always raises the supplied exception."""

    def __init__(self, error: BaseException):
        self._error = error

    async def post(self, path: str, **kwargs: Any) -> DummyResponse:
        raise self._error


def test_transport_error_keeps_a_cause_when_its_message_is_empty() -> None:
    """httpx timeouts stringify to ""; the account read must still say why it failed."""

    result = asyncio.run(
        account_module.get_account_evaluation(RaisingClient(httpx.ReadTimeout("")))
    )

    assert result["success"] is False
    assert result["error"] == "ReadTimeout"
