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
                    "tdy_lspft_amt": "500000",
                    "tdy_lspft": "15000",
                    "tdy_lspft_rt": "1.04",
                    "lspft": "-30000",
                    "lspft_ratio": "1.25",
                    "lspft_rt": "-2.37",
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

    async def fake_get_period_realized_profit(client, start_date, end_date, max_requests=10):
        # ka10073's own keys. This fixture used `qty`/`rlzt_pl`/`rlzt_rt`,
        # the keys the parser looked for, and so kept a table of blanks green.
        return {
            "success": True,
            "api_id": "ka10073",
            "return_code": 0,
            "return_msg": "ok",
            "total_records": 1,
            "realized_profit_data": [
                {
                    "dt": "20260324",
                    "tdy_htssel_cmsn": "현금",
                    "stk_nm": "삼성전자",
                    "cntr_qty": "1",
                    "buy_uv": "68000",
                    "cntr_pric": "71000",
                    "tdy_sel_pl": "2838",
                    "pl_rt": "+4.17",
                    "stk_cd": "005930",
                    "tdy_trde_cmsn": "20",
                    "tdy_trde_tax": "142",
                    "wthd_alowa": "0",
                    "loan_dt": "",
                    "crd_tp": "현금잔고",
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
    monkeypatch.setattr(dashboard_module.account, "get_period_realized_profit", fake_get_period_realized_profit)
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
    # First card is the explicit "D+2 예수금 + 보유평가" combined total.
    assert payload["summary"][0]["label"] == "총 자산 (D+2 예수금+보유평가)"
    assert payload["summary"][0]["highlight"] is True
    # D+2 cash (d2_entra=320000) + holdings evaluation (evlt_amt=142000);
    # today's `entr` (300000) has not seen fills that are still settling.
    assert payload["summary"][0]["value"] == "462000"
    assert payload["summary"][0]["detail"] == "D+2 예수금 320,000원 + 보유 평가 142,000원"
    summary_cards = {card["label"]: card for card in payload["summary"]}
    # 당일투자손익, not 당일투자원금 (`tdy_lspft_amt`).
    assert summary_cards["당일 손익 (Kiwoom)"]["value"] == "15000"
    assert summary_cards["당일 손익 (Kiwoom)"]["detail"] == "당일손익율 1.04%"
    # 누적손익율, not 당월손익율 (`lspft_ratio`).
    assert summary_cards["누적 손익률 (Kiwoom)"]["value"] == "-2.37"
    assert summary_cards["누적 손익률 (Kiwoom)"]["tone"] == "negative"
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
    realized = payload["tables"]["realized_profit"]["rows"][0]
    assert (realized["buy_price"], realized["sell_price"], realized["profit_loss"]) == (68000, 71000, 2838)
    assert realized["fee_tax"] == 162
    cards = {card["label"]: card for card in payload["performance"]}
    assert cards["실현 손익 (기간)"]["value"] == "2838"
    assert cards["거래 통계"]["value"] == "1승 0패"


def test_asset_sessions_follow_index_bars() -> None:
    """Holidays drop out, and each session changes from the previous one."""

    # 10/9 (Fri) was Hangul Day and 10/10-11 a weekend: kt00002 still sends
    # rows for them, the index does not.
    points = [
        {"date": "2026-10-08", "value": 1_000_000, "cash": 600_000},
        {"date": "2026-10-09", "value": 1_000_000, "cash": 600_000},
        {"date": "2026-10-10", "value": 1_000_000, "cash": 600_000},
        {"date": "2026-10-11", "value": 1_001_500, "cash": 601_500},
        {"date": "2026-10-12", "value": 994_000, "cash": 601_500},
        {"date": "2026-10-13", "value": 794_000, "cash": 401_500},
        {"date": "2026-10-14", "value": 795_000, "cash": 401_500},
    ]
    index_bars = [
        {"dt": "20261013", "cur_prc": "600000"},
        {"dt": "20261012", "cur_prc": "630000"},
        {"dt": "20261008", "cur_prc": "640000"},
    ]
    excluded = [{"date": "2026-10-13", "change_pct": -20.12, "reason": "매매로 설명 불가한 급변 — 입출금 추정"}]

    dashboard_module._annotate_asset_sessions(points, index_bars, excluded)

    by_day = {p["date"]: p for p in points}
    assert [p["date"] for p in points if p["trading_day"]] == [
        "2026-10-08", "2026-10-12", "2026-10-13", "2026-10-14",
    ]
    assert "day_change" not in by_day["2026-10-08"]
    # Measured from the 10/8 session, not the Sunday row in between.
    assert by_day["2026-10-12"]["day_change"] == -6_000
    assert by_day["2026-10-12"]["day_change_pct"] == -0.6
    assert by_day["2026-10-13"]["flow_suspect"] is True
    assert "flow_suspect" not in by_day["2026-10-12"]
    # Today, past the last index bar, counts by weekday.
    assert by_day["2026-10-14"]["day_change"] == 1_000
    assert "day_change" not in by_day["2026-10-11"]


def test_recent_sessions_and_realized_window() -> None:
    # 10/9 (Fri) was Hangul Day and 10/10-11 a weekend.
    assert dashboard_module._recent_sessions("20261012", "20261001", "20261031") == [
        "20261012", "20261008", "20261007",
    ]
    assert dashboard_module._recent_sessions("20261012", "20261008", "20261031") == ["20261012", "20261008"]
    # ka10073 answers three months back from the end date.
    assert dashboard_module._realized_window_start("20260101", "20261009") == "20260710"
    assert dashboard_module._realized_window_start("20260801", "20261009") == "20260801"
    assert dashboard_module._realized_window_start("20260101", "20260531") == "20260301"


def _ok(api_id: str, key: str, rows: list[dict]) -> dict:
    return {"success": True, "api_id": api_id, "return_code": 0, "return_msg": "ok",
            "total_records": len(rows), key: rows}


def _journal_row(**fields: str) -> dict:
    """A ka10170 row; the blank one is what a day without trades returns."""

    row = {key: "" for key in ("stk_nm", "buy_avg_pric", "buy_qty", "sel_avg_pric", "sell_qty",
                               "cmsn_alm_tax", "pl_amt", "sell_amt", "buy_amt", "prft_rt", "stk_cd")}
    row.update(fields)
    return row


def test_trade_history_spans_the_period(monkeypatch) -> None:
    """Settled trades from kt00015, the last sessions from the day journal."""

    def empty(api_id: str, key: str):
        async def fake(*_args, **_kwargs):
            return _ok(api_id, key, [])
        return fake

    for name, api_id, key in (
        ("get_account_evaluation", "kt00004", "evaluation_data"),
        ("get_account_current_status", "kt00017", "daily_status_data"),
        ("get_daily_account_profit_detail", "kt00016", "profit_detail_data"),
        ("get_execution_info", "ka10076", "execution_data"),
        ("get_order_execution_status", "kt00009", "order_execution_status_data"),
        ("get_unexecuted_orders", "ka10075", "unexecuted_orders_data"),
        ("get_daily_estimated_asset", "kt00002", "daily_estimated_asset_data"),
    ):
        monkeypatch.setattr(dashboard_module.account, name, empty(api_id, key))
    monkeypatch.setattr(dashboard_module.market, "get_index_daily_bars", empty("ka20006", "index_daily_bars"))
    monkeypatch.setattr(dashboard_module, "_today_ymd", lambda: "20261012")

    calls: dict[str, list] = {"kt00015": [], "ka10073": [], "ka10170": []}

    def settled(cntr_dt: str, side: str, code: str, name: str, qty: str, unit: str, amount: str, fee: str) -> dict:
        return {"trde_dt": "", "cntr_dt": cntr_dt, "io_tp_nm": side, "trde_kind_nm": "매매",
                "rmrk_nm": f"장내{side}", "stk_cd": code, "stk_nm": name, "trde_qty_jwa_cnt": qty,
                "trde_unit": unit, "trde_amt": amount, "tax_sum_cmsn": fee}

    async def fake_trade_history(client, start_date, end_date, tp="3", gds_tp="1", max_requests=10):
        calls["kt00015"].append((start_date, end_date))
        return _ok("kt00015", "trade_history_data", [
            settled("20260930", "매수", "A000270", "기아", "2", "99,000", "000000000198000", "000000000000030"),
            settled("20261002", "매수", "A000270", "기아", "2", "100,000", "000000000200000", "000000000000030"),
            settled("20261006", "매도", "A000270", "기아", "2", "105,000", "000000000210000", "000000000000450"),
            # Booked for a day the journal also covers: the journal wins.
            settled("20261007", "매수", "A005930", "삼성전자", "9", "70,000", "000000000630000", "000000000000090"),
        ])

    async def fake_realized(client, start_date, end_date, max_requests=10):
        calls["ka10073"].append((start_date, end_date))
        return _ok("ka10073", "realized_profit_data", [
            {"dt": "20261008", "stk_nm": "삼성전자", "stk_cd": "005930", "cntr_qty": "1", "buy_uv": "70000",
             "cntr_pric": "68000", "tdy_sel_pl": "-2196", "pl_rt": "-3.14", "tdy_trde_cmsn": "60", "tdy_trde_tax": "136"},
            {"dt": "20261006", "stk_nm": "기아", "stk_cd": "000270", "cntr_qty": "2", "buy_uv": "100000",
             "cntr_pric": "105000", "tdy_sel_pl": "9520", "pl_rt": "+4.76", "tdy_trde_cmsn": "60", "tdy_trde_tax": "420"},
        ])

    journals = {
        "": [_journal_row(stk_nm="셀트리온", stk_cd="068270", buy_qty="1", buy_avg_pric="180000",
                          buy_amt="180000", sell_qty="1", sel_avg_pric="181000", sell_amt="181000",
                          cmsn_alm_tax="420", pl_amt="580", prft_rt="0.32")],
        "20261008": [_journal_row(stk_nm="삼성전자", stk_cd="005930", buy_qty="0", buy_avg_pric="0",
                                  sell_qty="1", sel_avg_pric="68000", sell_amt="68000", cmsn_alm_tax="166",
                                  pl_amt="-2166", prft_rt="-3.09")],
        "20261007": [_journal_row(stk_nm="삼성전자", stk_cd="005930", buy_qty="1", buy_avg_pric="70000",
                                  buy_amt="70000", sell_qty="0", sel_avg_pric="0", cmsn_alm_tax="10")],
    }

    async def fake_journal(client, ottks_tp="2", ch_crd_tp="0", max_requests=10, base_dt=""):
        calls["ka10170"].append(base_dt)
        return _ok("ka10170", "trading_journal_data", journals.get(base_dt) or [_journal_row()])

    monkeypatch.setattr(dashboard_module.account, "get_trade_history", fake_trade_history)
    monkeypatch.setattr(dashboard_module.account, "get_period_realized_profit", fake_realized)
    monkeypatch.setattr(dashboard_module.account, "get_daily_trading_journal", fake_journal)

    payload = asyncio.run(
        dashboard_module.build_dashboard_snapshot(
            client=object(),
            settings=SimpleNamespace(use_mock=False, active_base_url="https://api.kiwoom.com/"),
            start_date="20261001",
            end_date="20261012",
        )
    )

    # Today's journal is the one call without `base_dt`; 10/9 and the weekend
    # are skipped on the way back to three sessions.
    assert sorted(calls["ka10170"]) == ["", "20261007", "20261008"]
    assert calls["kt00015"] == [("20261001", "20261012")]
    assert calls["ka10073"] == [("20261001", "20261012")]

    rows = payload["tables"]["trade_history"]["rows"]
    assert [(r["trade_date"], r["side"], r["stock_name"]) for r in rows] == [
        ("20261012", "매수", "셀트리온"),
        ("20261012", "매도", "셀트리온"),
        ("20261008", "매도", "삼성전자"),
        ("20261007", "매수", "삼성전자"),
        ("20261006", "매도", "기아"),
        ("20261002", "매수", "기아"),
    ]
    by_key = {(r["trade_date"], r["side"]): r for r in rows}
    # Same-day round trip: one fee for the stock-day, on the sell leg.
    assert by_key[("20261012", "매수")]["fee_tax"] is None
    assert by_key[("20261012", "매도")]["fee_tax"] == 420
    # No ka10073 row for it yet: the journal's own P&L stands in.
    assert by_key[("20261012", "매도")]["profit_loss"] == 580
    # ka10073 nets the round trip and wins over the journal's -2,166.
    assert by_key[("20261008", "매도")]["profit_loss"] == -2196
    assert by_key[("20261007", "매수")]["quantity"] == 1
    assert by_key[("20261006", "매도")]["profit_loss"] == 9520
    assert by_key[("20261006", "매도")]["stock_code"] == "000270"
    assert by_key[("20261002", "매수")]["price"] == 100000
    assert by_key[("20261002", "매수")]["profit_loss"] is None
    assert payload["overview"]["trade_history_count"] == 6

    # The blank row of a day without trades never reaches a table.
    assert payload["tables"]["trading_journal"]["row_count"] == 1
    cards = {card["label"]: card for card in payload["performance"]}
    assert cards["실현 손익 (기간)"]["value"] == str(-2196 + 9520)
    assert cards["실현 손익 (기간)"]["detail"] == "매도 2건 · 수수료·세금 676원"

    # A longer period is cut to the three months ka10073 answers, for both
    # tables, and says so.
    long_run = asyncio.run(
        dashboard_module.build_dashboard_snapshot(
            client=object(),
            settings=SimpleNamespace(use_mock=False, active_base_url="https://api.kiwoom.com/"),
            start_date="20260101",
            end_date="20261012",
        )
    )
    assert calls["ka10073"][-1] == ("20260713", "20261012")
    assert calls["kt00015"][-1] == ("20260713", "20261012")
    assert long_run["tables"]["realized_profit"]["note"] == "07/13부터 (최근 3개월)"
    assert long_run["tables"]["trade_history"]["note"].startswith("07/13부터 (최근 3개월) · ")
    long_cards = {card["label"]: card for card in long_run["performance"]}
    assert long_cards["종합 손익"]["detail"].startswith("기간 실현 +7,324(07/13부터) + 보유 평가 +0")


def _period_cards(monkeypatch, kt00016_record: dict, evaluation_record: dict | None = None) -> dict[str, dict]:
    """Snapshot performance cards with every account call empty except kt00016."""

    def empty(api_id: str, key: str):
        async def fake(*_args, **_kwargs):
            return {"success": True, "api_id": api_id, "return_code": 0,
                    "return_msg": "ok", "total_records": 0, key: []}
        return fake

    for name, api_id, key in (
        ("get_account_evaluation", "kt00004", "evaluation_data"),
        ("get_account_current_status", "kt00017", "daily_status_data"),
        ("get_period_realized_profit", "ka10073", "realized_profit_data"),
        ("get_trade_history", "kt00015", "trade_history_data"),
        ("get_daily_trading_journal", "ka10170", "trading_journal_data"),
        ("get_execution_info", "ka10076", "execution_data"),
        ("get_order_execution_status", "kt00009", "order_execution_status_data"),
        ("get_unexecuted_orders", "ka10075", "unexecuted_orders_data"),
        ("get_daily_estimated_asset", "kt00002", "daily_estimated_asset_data"),
    ):
        monkeypatch.setattr(dashboard_module.account, name, empty(api_id, key))
    monkeypatch.setattr(dashboard_module.market, "get_index_daily_bars", empty("ka20006", "index_daily_bars"))

    if evaluation_record is not None:
        async def fake_evaluation(*_args, **_kwargs):
            return {"success": True, "api_id": "kt00004", "return_code": 0, "return_msg": "ok",
                    "total_records": 1, "evaluation_data": [evaluation_record]}

        monkeypatch.setattr(dashboard_module.account, "get_account_evaluation", fake_evaluation)

    async def fake_profit_detail(client, fr_dt, to_dt, max_requests=10):
        return {"success": True, "api_id": "kt00016", "return_code": 0, "return_msg": "ok",
                "total_records": 1, "profit_detail_data": [kt00016_record]}

    monkeypatch.setattr(dashboard_module.account, "get_daily_account_profit_detail", fake_profit_detail)
    payload = asyncio.run(
        dashboard_module.build_dashboard_snapshot(
            client=object(),
            settings=SimpleNamespace(use_mock=False, active_base_url="https://api.kiwoom.com/"),
            start_date="20260401",
            end_date="20261009",
        )
    )
    return {card["label"]: card for card in payload["performance"]}


def test_period_profit_excludes_withdrawals(monkeypatch) -> None:
    """A withdrawal is not a loss: use kt00016's own flow-netted profit.

    Keys and formats are the live kt00016 response's (2026-10-09); the values
    are illustrative. End minus start reads -600,000원 (-30%) because
    700,000원 left the account; Kiwoom's `evltv_prft` is +100,000원.
    """

    cards = _period_cards(monkeypatch, {
        "tot_amt_fr": "000002000000", "tot_amt_to": "000001400000",
        "invt_bsamt": "000001700000", "evltv_prft": "000000100000",
        "prft_rt": "5.88", "tern_rt": "626.16",
        "termin_tot_trns": "000000001000", "termin_tot_pymn": "000000700000",
    })

    assert cards["기간 손익 (Kiwoom)"]["value"] == 100000
    assert cards["기간 손익 (Kiwoom)"]["tone"] == "positive"
    assert cards["기간 손익 (Kiwoom)"]["detail"] == "입금 1,000원 · 출금 700,000원 제외"
    assert cards["기간 수익률 (Kiwoom)"]["value"] == 5.88
    assert cards["기간 시작 자산"]["value"] == "000002000000"


def test_period_profit_negative_month_without_flows(monkeypatch) -> None:
    """Kiwoom sends a negative profit zero-padded after the sign (live 2026-09)."""

    cards = _period_cards(monkeypatch, {
        "tot_amt_fr": "000001000000", "tot_amt_to": "000000980000",
        "invt_bsamt": "000001000000", "evltv_prft": "-00000020000",
        "prft_rt": "-2.00", "tern_rt": "137.37",
        "termin_tot_trns": "000000000000", "termin_tot_pymn": "000000000000",
    })

    assert cards["기간 손익 (Kiwoom)"]["value"] == -20000
    assert cards["기간 손익 (Kiwoom)"]["tone"] == "negative"
    assert cards["기간 손익 (Kiwoom)"]["detail"] == ""
    assert cards["기간 수익률 (Kiwoom)"]["value"] == -2.0


def test_period_profit_before_the_end_date_closes(monkeypatch) -> None:
    """kt00016 for a period ending today: every `*_to` field is 0.

    Its `evltv_prft` is then minus the starting assets (-100%). The card
    nets the flows by hand on today's estimated assets instead.
    """

    cards = _period_cards(
        monkeypatch,
        {
            "tot_amt_fr": "000002000000", "tot_amt_to": "000000000000",
            "entr_to": "000000000000", "scrt_evlt_amt_to": "000000000000",
            "invt_bsamt": "000001800000", "evltv_prft": "-00002000000",
            "prft_rt": "-100.00", "tern_rt": "128.77",
            "termin_tot_trns": "000000000000", "termin_tot_pymn": "000000500000",
        },
        evaluation_record={"prsm_dpst_aset_amt": "000001530000"},
    )

    # 1,530,000 - 2,000,000 + 500,000 withdrawn
    assert cards["기간 손익 (Kiwoom)"]["value"] == 30000
    assert cards["기간 수익률 (Kiwoom)"]["value"] == round(30000 / 1800000 * 100, 2)
    assert cards["기간 손익 (Kiwoom)"]["detail"] == (
        "입금 0원 · 출금 500,000원 제외 · 키움 기간 집계 전 — 현재 추정자산 기준"
    )
    assert cards["현재 기준 자산"]["value"] == "000001530000"


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
