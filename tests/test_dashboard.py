"""Tests for the dashboard web application."""

from __future__ import annotations

import asyncio
import importlib
import os
import sys
from pathlib import Path
from types import SimpleNamespace

from starlette.testclient import TestClient

os.environ.setdefault("KIWOOM_APPKEY", "dummy-appkey")
os.environ.setdefault("KIWOOM_SECRETKEY", "dummy-secretkey")
os.environ.setdefault("KIWOOM_USE_MOCK", "false")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

dashboard_module = importlib.import_module("src.dashboard")


def test_build_dashboard_snapshot_normalizes_nested_data(monkeypatch) -> None:
    """Dashboard payload should flatten nested Kiwoom responses."""

    async def fake_get_account_evaluation(client, qry_tp="0", dmst_stex_tp="KRX", max_requests=10):
        return {
            "success": True,
            "api_id": "kt00004",
            "return_code": 0,
            "return_msg": "ok",
            "total_records": 1,
            "evaluation_data": [
                {
                    "acnt_nm": "테스트계좌",
                    "brch_nm": "테스트지점",
                    "prsm_dpst_aset_amt": "1234500",
                    "aset_evlt_amt": "1200000",
                    "tot_est_amt": "142000",
                    "entr": "300000",
                    "d2_entra": "320000",
                    "tdy_lspft_amt": "15000",
                    "lspft_ratio": "1.25",
                    "stk_acnt_evlt_prst": [
                        {
                            "stk_cd": "005930",
                            "stk_nm": "삼성전자",
                            "rmnd_qty": "2",
                            "pur_uv": "70000",
                            "cur_prc": "71000",
                            "evlt_amt": "142000",
                            "lspft_amt": "2000",
                            "lspft_rt": "1.42",
                        }
                    ],
                }
            ],
        }

    async def fake_get_account_current_status(client, max_requests=10):
        return {
            "success": False,
            "api_id": "kt00017",
            "return_code": 20,
            "return_msg": "모의투자에서는 해당업무가 제공되지 않습니다.",
            "total_records": 0,
            "daily_status_data": [],
        }

    async def fake_get_daily_account_profit_detail(client, fr_dt, to_dt, max_requests=10):
        return {
            "success": True,
            "api_id": "kt00016",
            "return_code": 0,
            "return_msg": "ok",
            "total_records": 1,
            "profit_detail_data": [
                {
                    "dt": "20260324",
                    "tot_est_amt": "1234500",
                    "lspft_amt": "15000",
                    "lspft_ratio": "1.25",
                }
            ],
        }

    async def fake_get_daily_realized_profit_by_stock(client, stock_code, start_date, max_requests=10):
        return {
            "success": True,
            "api_id": "ka10072",
            "return_code": 0,
            "return_msg": "ok",
            "total_records": 1,
            "realized_profit_data": [
                {
                    "dt": "20260324",
                    "stk_cd": "005930",
                    "stk_nm": "삼성전자",
                    "qty": "1",
                    "rlzt_pl": "2500",
                    "rlzt_rt": "3.5",
                }
            ],
        }

    async def fake_get_execution_info(client, qry_tp, sell_tp, stex_tp, stk_cd="", ord_no="", max_requests=10):
        return {
            "success": True,
            "api_id": "ka10076",
            "return_code": 0,
            "return_msg": "ok",
            "total_records": 1,
            "execution_data": [
                {
                    "cntr_dt": "20260324",
                    "cntr_tm": "091501",
                    "stk_cd": "005930",
                    "stk_nm": "삼성전자",
                    "trde_tp_nm": "매수",
                    "cntr_qty": "1",
                    "cntr_uv": "71000",
                    "ord_no": "1234567",
                }
            ],
        }

    async def fake_get_order_execution_status(client, stk_bond_tp, mrkt_tp, sell_tp, qry_tp, dmst_stex_tp, stk_cd="", fr_ord_no="", max_requests=10):
        return {
            "success": True,
            "api_id": "kt00009",
            "return_code": 0,
            "return_msg": "ok",
            "total_records": 1,
            "order_execution_status_data": [
                {
                    "acnt_ord_cntr_prst_array": [
                        {
                            "ord_dt": "20260324",
                            "ord_tmd": "091500",
                            "stk_cd": "005930",
                            "stk_nm": "삼성전자",
                            "trde_tp_nm": "매수",
                            "ord_prst": "접수",
                            "ord_qty": "1",
                            "cntr_qty": "0",
                            "ord_uv": "70000",
                            "ord_no": "1234567",
                        }
                    ]
                }
            ],
        }

    async def fake_get_unexecuted_orders(client, all_stk_tp, trde_tp, stex_tp, stk_cd="", max_requests=10):
        return {
            "success": True,
            "api_id": "ka10075",
            "return_code": 0,
            "return_msg": "ok",
            "total_records": 1,
            "unexecuted_orders_data": [
                {
                    "ord_dt": "20260324",
                    "ord_tmd": "091500",
                    "stk_cd": "005930",
                    "stk_nm": "삼성전자",
                    "trde_tp_nm": "매수",
                    "ord_prst": "미체결",
                    "ord_qty": "1",
                    "cntr_qty": "0",
                    "ord_uv": "70000",
                    "ord_no": "1234567",
                }
            ],
        }

    async def fake_get_daily_estimated_asset(client, start_date, end_date, max_requests=10):
        return {
            "success": True,
            "api_id": "kt00002",
            "return_code": 0,
            "return_msg": "ok",
            "total_records": 3,
            "daily_estimated_asset_data": [
                {"dt": "20260322", "prsm_dpst_aset_amt": "1200000"},
                {"dt": "20260323", "prsm_dpst_aset_amt": "1220000"},
                {"dt": "20260324", "prsm_dpst_aset_amt": "1234500"},
            ],
        }

    monkeypatch.setattr(dashboard_module.account, "get_account_evaluation", fake_get_account_evaluation)
    monkeypatch.setattr(dashboard_module.account, "get_daily_estimated_asset", fake_get_daily_estimated_asset)
    monkeypatch.setattr(dashboard_module.account, "get_account_current_status", fake_get_account_current_status)
    monkeypatch.setattr(dashboard_module.account, "get_daily_account_profit_detail", fake_get_daily_account_profit_detail)
    monkeypatch.setattr(dashboard_module.account, "get_daily_realized_profit_by_stock", fake_get_daily_realized_profit_by_stock)
    monkeypatch.setattr(dashboard_module.account, "get_execution_info", fake_get_execution_info)
    monkeypatch.setattr(dashboard_module.account, "get_order_execution_status", fake_get_order_execution_status)
    monkeypatch.setattr(dashboard_module.account, "get_unexecuted_orders", fake_get_unexecuted_orders)

    payload = asyncio.run(
        dashboard_module.build_dashboard_snapshot(
            client=object(),
            settings=SimpleNamespace(use_mock=True, active_base_url="https://mockapi.kiwoom.com/"),
            start_date="20260301",
            end_date="20260324",
        )
    )

    assert payload["environment"]["mode"] == "mock"
    assert payload["identity"]["account_name"] == "테스트계좌"
    # First card is the new explicit "예수금 + 보유평가" combined total.
    assert payload["summary"][0]["label"] == "총 자산 (예수금+보유평가)"
    assert payload["summary"][0]["highlight"] is True
    # Cash (entr=300000) + holdings evaluation (evlt_amt=142000) = 442000.
    assert payload["summary"][0]["value"] == "442000"
    assert payload["summary"][0]["detail"] == "예수금 300,000원 + 보유 평가 142,000원"
    # Kiwoom-reported total assets is now further down the list.
    assert any(
        card["label"] == "총 추정자산 (Kiwoom)" and card["value"] == "1234500"
        for card in payload["summary"]
    )
    assert payload["tables"]["holdings"]["rows"][0]["stock_name"] == "삼성전자"
    assert payload["tables"]["order_status"]["rows"][0]["status"] == "접수"
    assert payload["tables"]["executions"]["rows"][0]["filled_price"] == "71000"
    # Total-asset time series (kt00002): sorted points + range delta.
    series = payload["asset_series"]
    assert [p["date"] for p in series["points"]] == ["2026-03-22", "2026-03-23", "2026-03-24"]
    assert series["points"][0]["value"] == 1200000
    assert series["start_value"] == 1200000 and series["end_value"] == 1234500
    assert series["change"] == 34500
    assert payload["sources"][1]["status"] == "unsupported"


def test_dashboard_routes_render_with_loader_override() -> None:
    """Dashboard routes should render HTML and JSON payloads."""

    captured: dict[str, str] = {}

    async def fake_loader(client, settings, start_date, end_date):
        captured["start_date"] = start_date
        captured["end_date"] = end_date
        return {
            "generated_at": "2026-03-24T09:15:00+09:00",
            "environment": {
                "mode": "mock",
                "label": "Mock Investment",
                "base_url": "https://mockapi.kiwoom.com/",
            },
            "filters": {
                "start_date": start_date,
                "end_date": end_date,
            },
            "identity": {
                "account_name": "테스트계좌",
                "branch_name": "테스트지점",
            },
            "summary": [],
            "sources": [],
            "tables": {
                "holdings": {"row_count": 0, "rows": [], "raw_rows": [], "columns": [], "empty_message": "empty"},
                "unexecuted_orders": {"row_count": 0, "rows": [], "raw_rows": [], "columns": [], "empty_message": "empty"},
                "order_status": {"row_count": 0, "rows": [], "raw_rows": [], "columns": [], "empty_message": "empty"},
                "executions": {"row_count": 0, "rows": [], "raw_rows": [], "columns": [], "empty_message": "empty"},
                "realized_profit": {"row_count": 0, "rows": [], "raw_rows": [], "columns": [], "empty_message": "empty"},
                "daily_profit_detail": {"row_count": 0, "rows": [], "raw_rows": [], "columns": [], "empty_message": "empty"},
            },
        }

    app = dashboard_module.create_dashboard_app(data_loader=fake_loader)

    with TestClient(app) as client:
        html_response = client.get("/")
        assert html_response.status_code == 200
        assert "Trading Dashboard" in html_response.text

        api_response = client.get("/api/dashboard?start_date=20260301&end_date=20260324")
        assert api_response.status_code == 200
        assert api_response.json()["environment"]["mode"] == "mock"

    assert captured == {"start_date": "20260301", "end_date": "20260324"}
