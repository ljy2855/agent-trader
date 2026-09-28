"""Live trade ledger tests — normalization, idempotent append, stats gating."""

import importlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "automation"))
ltj = importlib.import_module("live_trade_journal")


@pytest.fixture(autouse=True)
def _tmp_ledger(tmp_path, monkeypatch):
    monkeypatch.setattr(ltj, "LEDGER_PATH", tmp_path / "live_trades.jsonl")
    return ltj.LEDGER_PATH


# --- normalization --------------------------------------------------------


def test_row_with_realized_sell_becomes_a_record():
    row = {
        "stk_cd": "005930", "stk_nm": "삼성전자",
        "buy_qty": "5", "buy_avg_pric": "70000",
        "sell_qty": "5", "sel_avg_pric": "72000",
        "prft_rt": "2.62", "pl_amt": "9200", "cmsn_alm_tax": "800",
    }
    rec = ltj.normalize_journal_row(row, "2026-07-24")
    assert rec is not None
    assert rec["stock_code"] == "005930"
    assert rec["net_pct"] == 2.62
    assert rec["net_pct_source"] == "broker_prft_rt"  # broker figure wins
    assert rec["profit_loss_krw"] == 9200


def test_open_position_without_sell_is_skipped():
    # Unrealized holdings must not enter the ledger — they'd bias
    # expectancy toward whatever happens to be held right now.
    row = {"stk_cd": "005930", "buy_qty": "5", "buy_avg_pric": "70000", "sell_qty": "0"}
    assert ltj.normalize_journal_row(row, "2026-07-24") is None


def test_net_pct_derived_when_broker_rate_missing():
    row = {
        "stk_cd": "000660", "buy_qty": "1", "buy_avg_pric": "100000",
        "sell_qty": "1", "sel_avg_pric": "110000",
    }
    rec = ltj.normalize_journal_row(row, "2026-07-24")
    assert rec["net_pct_source"] == "derived_from_avg_prices"
    # +10% gross minus the 0.23% assumed round-trip cost
    assert rec["net_pct"] == pytest.approx(10.0 - ltj.FALLBACK_COST_PCT, abs=1e-6)


def test_row_without_usable_prices_is_skipped():
    assert ltj.normalize_journal_row({"stk_cd": "X", "sell_qty": "3"}, "2026-07-24") is None


def test_negative_profit_rate_parses():
    row = {"stk_cd": "A", "sell_qty": "1", "buy_avg_pric": "100",
           "sel_avg_pric": "95", "prft_rt": "-5.12"}
    assert ltj.normalize_journal_row(row, "2026-07-24")["net_pct"] == -5.12


# --- append / idempotency -------------------------------------------------


def _rec(date, code, net):
    return {"trade_date": date, "stock_code": code, "net_pct": net}


def test_append_writes_and_reloads():
    assert ltj.append_records([_rec("2026-07-24", "005930", 1.0)]) == 1
    rows = ltj.load_ledger()
    assert len(rows) == 1 and rows[0]["stock_code"] == "005930"


def test_append_is_idempotent_per_date_and_code():
    ltj.append_records([_rec("2026-07-24", "005930", 1.0)])
    added = ltj.append_records([_rec("2026-07-24", "005930", 1.0)])
    assert added == 0
    assert len(ltj.load_ledger()) == 1


def test_same_code_on_a_different_day_is_a_new_record():
    ltj.append_records([_rec("2026-07-24", "005930", 1.0)])
    assert ltj.append_records([_rec("2026-07-25", "005930", 2.0)]) == 1
    assert len(ltj.load_ledger()) == 2


def test_load_ledger_tolerates_a_torn_final_line():
    ltj.append_records([_rec("2026-07-24", "005930", 1.0)])
    with ltj.LEDGER_PATH.open("a") as fh:
        fh.write('{"trade_date": "2026-07-25", "stock_c')  # interrupted write
    rows = ltj.load_ledger()
    assert len(rows) == 1  # good row survives, partial one dropped


def test_load_ledger_empty_when_missing():
    assert ltj.load_ledger() == []


# --- stats output ---------------------------------------------------------


def test_stats_refuses_to_conclude_below_30_trades(capsys):
    ltj.append_records([
        {"trade_date": "2026-07-24", "stock_code": f"{i:06d}", "net_pct": 5.0}
        for i in range(4)
    ])
    ltj._print_stats()
    out = capsys.readouterr().out
    assert "n=4" in out
    assert "결론도 내릴 수 없다" in out  # no edge claim on a tiny sample


def test_stats_reports_ci_and_totals(capsys):
    ltj.append_records([
        {"trade_date": "2026-07-24", "stock_code": f"{i:06d}",
         "net_pct": 1.0 if i % 2 else -1.0,
         "profit_loss_krw": 1000, "commission_tax_krw": 50}
        for i in range(40)
    ])
    ltj._print_stats()
    out = capsys.readouterr().out
    assert "95% CI" in out
    assert "거래 40건" in out
    assert "수수료/세금" in out


def test_stats_handles_empty_ledger(capsys):
    ltj._print_stats()
    assert "원장 비어 있음" in capsys.readouterr().out
