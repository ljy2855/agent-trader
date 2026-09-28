"""Tests for the intraday strategy planner."""

from __future__ import annotations

import asyncio
import importlib
import os
import sys
from pathlib import Path

from src.config import Settings

os.environ.setdefault("KIWOOM_APPKEY", "dummy-appkey")
os.environ.setdefault("KIWOOM_SECRETKEY", "dummy-secretkey")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

strategy_module = importlib.import_module("src.services.strategy")


def test_normalize_holdings_includes_all_pages_and_keeps_first_summary():
    summary = {
        "prsm_dpst_aset_amt": "1000000",
        "stk_acnt_evlt_prst": [{"stk_cd": "005930", "rmnd_qty": "10", "cur_prc": "10000"}],
    }
    record, holdings = strategy_module._normalize_holding_rows({
        "evaluation_data": [summary, {
            "stk_acnt_evlt_prst": [{"stk_cd": "000660", "rmnd_qty": "5", "cur_prc": "20000"}],
        }],
    })
    assert record == summary
    assert [holding["stock_code"] for holding in holdings] == ["005930", "000660"]
    assert [holding["quantity"] for holding in holdings] == [10, 5]


async def fake_account_evaluation(client):
    return {
        "success": True,
        "evaluation_data": [
            {
                "prsm_dpst_aset_amt": "1000000",
                "aset_evlt_amt": "1000000",
                "tot_est_amt": "0",
                "entr": "500000",
                "stk_acnt_evlt_prst": [],
            }
        ],
    }


async def fake_unexecuted_orders(client, all_stk_tp, trde_tp, stex_tp, stk_cd=""):
    return {
        "success": True,
        "unexecuted_orders_data": [],
    }


async def fake_market_snapshot(
    client,
    *,
    watchlist=None,
    leaders_limit=10,
    stock_detail_cache_ttl_seconds=0.0,
    leaders_market_tp="000",
):
    return {
        "success": True,
        "indices": {
            "kospi": {"flu_rt": "+1.20", "rising": "600", "fall": "300"},
            "kosdaq": {"flu_rt": "+1.00", "rising": "700", "fall": "350"},
        },
        "leaders": {
            "gainers": [{"stk_cd": "005930", "stk_nm": "삼성전자"}],
            "volume": [{"stk_cd": "005930", "stk_nm": "삼성전자"}],
            "value": [{"stk_cd": "005930", "stk_nm": "삼성전자"}],
        },
        "sector_rows": [{"stk_cd": "001", "stk_nm": "종합(KOSPI)"}],
        "watchlist_details": [],
    }


async def fake_stock_detail_bundle(
    client,
    *,
    stock_code,
    bar_limit=5,
    cache_ttl_seconds=0.0,
):
    return {
        "success": True,
        "stock_code": stock_code,
        "quote": {
            "stk_cd": stock_code,
            "stk_nm": "삼성전자",
            "cur_prc": "+70000",
            "flu_rt": "+2.94",
            "open_pric": "+69000",
            "high_pric": "+70500",
            "pred_close_pric": "68000",
        },
        "orderbook": {
            "sel_fpr_bid": "+70000",
            "buy_fpr_bid": "+69900",
            "tot_sel_req": "10000",
            "tot_buy_req": "18000",
        },
        "daily_bars": [
            {"date": "20260325", "close_pric": "+70000"},
            {"date": "20260324", "high_pric": "+69000", "close_pric": "+68000"},
        ],
    }


async def fake_place_stock_buy_order(client, **kwargs):
    return {
        "success": True,
        "message": "mock buy submitted",
        "kwargs": kwargs,
    }


def test_strategy_planner_generates_buy_action(monkeypatch) -> None:
    """Risk-on conditions with a strong candidate should yield a buy plan."""

    monkeypatch.setattr(strategy_module.account, "get_account_evaluation", fake_account_evaluation)
    monkeypatch.setattr(strategy_module.account, "get_unexecuted_orders", fake_unexecuted_orders)
    monkeypatch.setattr(strategy_module.market, "get_market_snapshot", fake_market_snapshot)
    monkeypatch.setattr(strategy_module.market, "get_stock_detail_bundle", fake_stock_detail_bundle)

    result = asyncio.run(
        strategy_module.plan_intraday_momentum_strategy(
            client=object(),
            settings=Settings(KIWOOM_APPKEY="dummy-appkey", KIWOOM_SECRETKEY="dummy-secretkey"),
            watchlist=["005930"],
            leaders_limit=5,
            candidate_limit=3,
            max_positions=3,
            max_new_positions=1,
            position_budget_pct=10,
        )
    )

    assert result["success"] is True
    assert result["regime"]["risk_on"] is True
    assert result["planned_actions"][0]["action"] == "buy"
    assert result["planned_actions"][0]["stock_code"] == "005930"
    assert result["planned_actions"][0]["quantity"] >= 1


def test_strategy_executor_submits_mock_buy_orders(monkeypatch) -> None:
    """Execution mode should submit mock buy orders when allowed."""

    monkeypatch.setattr(strategy_module.account, "get_account_evaluation", fake_account_evaluation)
    monkeypatch.setattr(strategy_module.account, "get_unexecuted_orders", fake_unexecuted_orders)
    monkeypatch.setattr(strategy_module.market, "get_market_snapshot", fake_market_snapshot)
    monkeypatch.setattr(strategy_module.market, "get_stock_detail_bundle", fake_stock_detail_bundle)
    monkeypatch.setattr(strategy_module.order, "place_stock_buy_order", fake_place_stock_buy_order)

    result = asyncio.run(
        strategy_module.plan_intraday_momentum_strategy(
            client=object(),
            settings=Settings(
                KIWOOM_USE_MOCK="true",
                KIWOOM_MOCK_APPKEY="dummy-mock-appkey",
                KIWOOM_MOCK_SECRETKEY="dummy-mock-secretkey",
            ),
            watchlist=["005930"],
            execute_orders=True,
            confirm_mock_orders=True,
        )
    )

    assert result["environment"]["execution_allowed"] is True
    assert len(result["executed_orders"]) == 1
    assert result["executed_orders"][0]["order_result"]["success"] is True
    assert result["executed_orders"][0]["action"]["stock_code"] == "005930"
    # SWO-122 RC2: execution_summary disambiguates empty executed_orders
    summary = result["execution_summary"]
    assert summary["execution_requested"] is True
    assert summary["execution_allowed"] is True
    assert summary["orders_planned"] == 1
    assert summary["orders_succeeded"] == 1
    assert summary["orders_failed"] == 0


def test_auto_buy_min_score_blocks_low_score_candidates(monkeypatch) -> None:
    """SWO-122/135/156: candidates below auto_buy_min_score must NOT auto-buy.

    Eligible candidates with score lower than the gate should still appear in
    candidate_rows for human review, but must not generate a planned_action
    or be executed.
    """
    monkeypatch.setattr(strategy_module.account, "get_account_evaluation", fake_account_evaluation)
    monkeypatch.setattr(strategy_module.account, "get_unexecuted_orders", fake_unexecuted_orders)
    monkeypatch.setattr(strategy_module.market, "get_market_snapshot", fake_market_snapshot)
    monkeypatch.setattr(strategy_module.market, "get_stock_detail_bundle", fake_stock_detail_bundle)
    monkeypatch.setattr(strategy_module.order, "place_stock_buy_order", fake_place_stock_buy_order)

    # Set auto_buy_min_score impossibly high so even a strong candidate is
    # blocked. With the fixture above, score is well above 7 but always below
    # 999.
    result = asyncio.run(
        strategy_module.plan_intraday_momentum_strategy(
            client=object(),
            settings=Settings(
                KIWOOM_USE_MOCK="true",
                KIWOOM_MOCK_APPKEY="dummy-mock-appkey",
                KIWOOM_MOCK_SECRETKEY="dummy-mock-secretkey",
            ),
            watchlist=["005930"],
            execute_orders=True,
            confirm_mock_orders=True,
            auto_buy_min_score=999,
        )
    )

    # Candidate is still scored & eligible…
    eligible_rows = [r for r in result["candidate_rows"] if r.get("eligible")]
    assert len(eligible_rows) >= 1
    assert all("auto_buy_blocked_reason" in r for r in eligible_rows)
    # …but NO buy was planned or executed.
    buy_actions = [a for a in result["planned_actions"] if a.get("action") == "buy"]
    assert buy_actions == []
    assert result["executed_orders"] == []
    assert result["execution_summary"]["orders_planned"] == 0
    assert result["execution_summary"]["orders_succeeded"] == 0


def test_score_tier_rewards_strong_momentum(monkeypatch) -> None:
    """2026-04-29 retrospective: strong momentum (+15~25%) should outscore
    weak gainers (+1~5%). The pre-fix tiering inverted this — +1~10% got
    +2 while +10~25% got +1, so 대원전선 +24% never reached the auto-buy
    gate. New tiering: 1~5%→+1, 5~15%→+2, 15~25%→+3, 25~29.5%→+1.
    """

    monkeypatch.setattr(strategy_module.account, "get_account_evaluation", fake_account_evaluation)
    monkeypatch.setattr(strategy_module.account, "get_unexecuted_orders", fake_unexecuted_orders)

    base_regime = {"regime": "neutral", "extreme_risk_off": False}

    def make_candidate(day_change, source="gainers"):
        prev_close = 10000
        cur = int(prev_close * (1 + day_change / 100))
        return {
            "stock_code": "001234",
            "stock_name": "TestCo",
            "sources": [source],
            "ranks": {source: 1},
            "seed_row": {},
        }, {
            "quote": {
                "stk_nm": "TestCo",
                "cur_prc": str(cur),
                "flu_rt": f"+{day_change:.2f}",
                "open_pric": str(int(cur * 0.99)),
                "high_pric": str(int(cur * 1.005)),
                "pred_close_pric": str(prev_close),
            },
            "orderbook": {
                "buy_fpr_bid": str(cur - 10),
                "sel_fpr_bid": str(cur),
                "tot_buy_req": "20000",
                "tot_sel_req": "12000",
            },
            "daily_bars": [
                {"date": "20260428", "close_pric": str(cur)},
                {"date": "20260427", "high_pric": str(int(cur * 0.95)), "close_pric": str(prev_close)},
            ],
        }

    weak_cand, weak_detail = make_candidate(3.0)        # +3%
    medium_cand, medium_detail = make_candidate(10.0)   # +10%
    strong_cand, strong_detail = make_candidate(20.0)   # +20%
    late_cand, late_detail = make_candidate(28.0)       # +28%

    _, weak = strategy_module._score_candidate(weak_cand, weak_detail, base_regime)
    _, medium = strategy_module._score_candidate(medium_cand, medium_detail, base_regime)
    _, strong = strategy_module._score_candidate(strong_cand, strong_detail, base_regime)
    _, late = strategy_module._score_candidate(late_cand, late_detail, base_regime)

    # Strong momentum must outscore weak — the bug we are fixing.
    assert strong["score"] > weak["score"], (
        f"strong({strong['score']}) should beat weak({weak['score']}) — "
        "old formula inverted this"
    )
    # Mid-tier sits between weak and strong.
    assert weak["score"] <= medium["score"] <= strong["score"]
    # Late stage (25~29.5%) must NOT beat the prime 15~25% range — chase
    # discount applies.
    assert late["score"] < strong["score"]


def test_pullback_tolerance_widened_to_8pct(monkeypatch) -> None:
    """A 6% pullback from intraday high used to fail eligibility (5% gate);
    healthy pullbacks should now pass. 2026-04-29 retrospective."""

    monkeypatch.setattr(strategy_module.account, "get_account_evaluation", fake_account_evaluation)
    monkeypatch.setattr(strategy_module.account, "get_unexecuted_orders", fake_unexecuted_orders)

    candidate = {
        "stock_code": "001234",
        "stock_name": "Pullback",
        "sources": ["gainers"],
        "ranks": {"gainers": 1},
        "seed_row": {},
    }
    detail = {
        "quote": {
            "stk_nm": "Pullback",
            "cur_prc": "10000",   # current
            "flu_rt": "+10.00",
            "open_pric": "9900",
            "high_pric": "10600",  # 6% above current — within new 8% tolerance
            "pred_close_pric": "9090",
        },
        "orderbook": {
            "buy_fpr_bid": "9990",
            "sel_fpr_bid": "10000",
            "tot_buy_req": "20000",
            "tot_sel_req": "12000",
        },
        "daily_bars": [
            {"date": "20260428", "close_pric": "10000"},
            {"date": "20260427", "high_pric": "9500", "close_pric": "9090"},
        ],
    }

    eligible, scored = strategy_module._score_candidate(
        candidate, detail, {"regime": "neutral", "extreme_risk_off": False}
    )
    assert eligible is True, scored.get("reasons")
    assert "고가 대비" not in " ".join(scored.get("reasons", []))


def _largecap_detail(flo_stkcnt: str | None) -> tuple[dict, dict]:
    """Eligible candidate (passes all legacy gates); only flo_stkcnt varies.

    market_cap = cur_prc(10000) × flo_stkcnt(천주) × 1000.
    flo_stkcnt='200000' → 2조 (large-cap); '50000' → 5000억 (small-cap).
    """
    candidate = {
        "stock_code": "005930",
        "stock_name": "BigCap",
        "sources": ["gainers"],
        "ranks": {"gainers": 1},
        "seed_row": {},
    }
    quote = {
        "stk_nm": "BigCap",
        "cur_prc": "10000",
        "flu_rt": "+10.00",
        "open_pric": "9900",
        "high_pric": "10100",
        "pred_close_pric": "9090",
    }
    if flo_stkcnt is not None:
        quote["flo_stkcnt"] = flo_stkcnt
    detail = {
        "quote": quote,
        "orderbook": {
            "buy_fpr_bid": "9990", "sel_fpr_bid": "10000",
            "tot_buy_req": "20000", "tot_sel_req": "12000",
        },
        "daily_bars": [
            {"date": "20260612", "close_pric": "10000"},
            {"date": "20260611", "high_pric": "9500", "close_pric": "9090"},
        ],
    }
    return candidate, detail


_NEUTRAL = {"regime": "neutral", "extreme_risk_off": False}
_ONE_TRILLION = 1_0000_0000_0000


def test_market_cap_filter_keeps_large_cap() -> None:
    cand, detail = _largecap_detail("200000")  # 2조
    eligible, scored = strategy_module._score_candidate(
        cand, detail, _NEUTRAL, min_market_cap_krw=_ONE_TRILLION
    )
    assert eligible is True, scored.get("reasons")
    assert "시총" not in " ".join(scored.get("reasons", []))


def test_market_cap_filter_rejects_small_cap() -> None:
    cand, detail = _largecap_detail("50000")  # 5000억 < 1조
    eligible, scored = strategy_module._score_candidate(
        cand, detail, _NEUTRAL, min_market_cap_krw=_ONE_TRILLION
    )
    assert eligible is False
    assert any("시총 미달" in r for r in scored.get("reasons", []))


def test_market_cap_filter_rejects_missing_shares() -> None:
    """No flo_stkcnt → can't verify cap → conservative reject."""
    cand, detail = _largecap_detail(None)
    eligible, scored = strategy_module._score_candidate(
        cand, detail, _NEUTRAL, min_market_cap_krw=_ONE_TRILLION
    )
    assert eligible is False
    assert any("시총 미달" in r for r in scored.get("reasons", []))


def test_market_cap_filter_off_by_default() -> None:
    """min_market_cap_krw=0 (default) → small-cap still eligible (no regression)."""
    cand, detail = _largecap_detail("50000")  # small-cap
    eligible, scored = strategy_module._score_candidate(cand, detail, _NEUTRAL)
    assert eligible is True, scored.get("reasons")
    assert "시총" not in " ".join(scored.get("reasons", []))


def _below_ma_detail(cur: int, ma_closes: list[int]):
    """Candidate whose daily_bars give a known MA; cur_prc set for dip control."""
    cand = {"stock_code": "005930", "stock_name": "Dip", "sources": ["value"], "ranks": {}, "seed_row": {}}
    detail = {
        "quote": {
            "stk_nm": "Dip", "cur_prc": str(cur), "flu_rt": "-1.0",
            "open_pric": str(cur - 5), "high_pric": str(cur + 50),
            "pred_close_pric": str(cur + 10),
        },
        "orderbook": {
            "buy_fpr_bid": str(cur - 10), "sel_fpr_bid": str(cur),
            "tot_buy_req": "20000", "tot_sel_req": "12000",
        },
        # bars[0] = latest; MA uses closes. Make 20 bars all = ma_closes value.
        "daily_bars": [{"date": f"2026{i:04d}", "close_pric": str(v), "high_pric": str(v)} for i, v in enumerate(ma_closes)],
    }
    return cand, detail


def test_below_ma_admits_shallow_dip() -> None:
    """below_ma: close just under MA (1% dip) → eligible, dip scored."""
    cand, detail = _below_ma_detail(9900, [10000] * 20)  # MA=10000, cur 9900 = 1% dip
    eligible, scored = strategy_module._score_candidate(
        cand, detail, _NEUTRAL, entry_mode="below_ma", ma_period=20
    )
    assert eligible is True, scored.get("reasons")


def test_below_ma_rejects_above_ma() -> None:
    """Above the MA = not cheap → rejected."""
    cand, detail = _below_ma_detail(10100, [10000] * 20)  # above MA
    eligible, scored = strategy_module._score_candidate(
        cand, detail, _NEUTRAL, entry_mode="below_ma", ma_period=20
    )
    assert eligible is False
    assert any("이평 위" in r for r in scored.get("reasons", []))


def test_below_ma_rejects_deep_dip_falling_knife() -> None:
    """>5% below MA = trend broken → rejected (falling knife)."""
    cand, detail = _below_ma_detail(9000, [10000] * 20)  # 10% dip
    eligible, scored = strategy_module._score_candidate(
        cand, detail, _NEUTRAL, entry_mode="below_ma", ma_period=20
    )
    assert eligible is False
    assert any("추세 하락" in r for r in scored.get("reasons", []))


def test_below_ma_ignores_day_change_band() -> None:
    """below_ma mode must NOT apply the momentum day_change gate (a -1% day
    would fail momentum's 1% min, but below_ma cares only about the dip)."""
    cand, detail = _below_ma_detail(9900, [10000] * 20)
    eligible, _ = strategy_module._score_candidate(
        cand, detail, _NEUTRAL, entry_mode="below_ma", ma_period=20,
        day_change_min=1.0, day_change_max=10.0,
    )
    assert eligible is True  # -1% day_change doesn't block below_ma


def test_universe_includes_carryover_codes() -> None:
    """Codes in the carryover list should appear in the merged universe even
    when they are not on any current leaderboard."""

    snapshot = {
        "leaders": {
            "gainers": [
                {"stk_cd": "111111", "stk_nm": "Today1"},
            ],
            "volume": [],
            "value": [],
        }
    }
    universe = strategy_module._merge_leaderboards(
        snapshot, carryover_codes=["222222", "333333"]
    )
    codes = {row["stock_code"] for row in universe}
    assert "111111" in codes
    assert "222222" in codes
    assert "333333" in codes
    # Carryover-only entry tags its source so scoring/audit can see it.
    only_carry = next(r for r in universe if r["stock_code"] == "222222")
    assert only_carry["sources"] == ["carryover"]
    # Live leaderboard entry retains its original source intact.
    live_entry = next(r for r in universe if r["stock_code"] == "111111")
    assert live_entry["sources"] == ["gainers"]


def test_merge_leaderboards_value_first_sort() -> None:
    """Large-cap mode (value_first=True) ranks 거래대금(value) leaders ahead of
    등락률(gainers) — the KOSPI universe leans on value, not gainers. 2026-06-24."""

    snapshot = {
        "leaders": {
            # GAIN is gainers-rank 1 but absent from value; VAL is value-rank 1.
            "gainers": [{"stk_cd": "GAIN00", "stk_nm": "Gainer"}],
            "volume": [],
            "value": [{"stk_cd": "VAL000", "stk_nm": "ValueLeader"}],
        }
    }
    # Default (small-cap momentum): gainers wins the top slot.
    default_order = strategy_module._merge_leaderboards(snapshot)
    assert default_order[0]["stock_code"] == "GAIN00"

    # value_first: the 거래대금 leader takes the top slot.
    value_order = strategy_module._merge_leaderboards(snapshot, value_first=True)
    assert value_order[0]["stock_code"] == "VAL000"


def test_day_change_band_parameterized() -> None:
    """Large-cap band (0.5~10%) admits a +6% move that the old 1~29.5% band
    also admits, but a +6% name must be rejected once max is lowered to 5%,
    and a +0.7% name (below small-cap min 1.0) must pass the large-cap min."""

    monkeypatch_regime = {"regime": "neutral", "extreme_risk_off": False}

    def detail_at(change_pct: float, cur: int = 10000):
        # Build a candidate that passes every other eligibility gate.
        prev = round(cur / (1 + change_pct / 100))
        return {
            "quote": {
                "stk_nm": "Big", "cur_prc": str(cur), "flu_rt": f"+{change_pct:.2f}",
                "open_pric": str(prev), "high_pric": str(cur),
                "pred_close_pric": str(prev), "flo_stkcnt": "200000",  # 2조
            },
            "orderbook": {
                "buy_fpr_bid": str(cur - 10), "sel_fpr_bid": str(cur),
                "tot_buy_req": "20000", "tot_sel_req": "12000",
            },
            "daily_bars": [
                {"date": "20260625", "close_pric": str(cur)},
                {"date": "20260624", "high_pric": str(prev), "close_pric": str(prev)},
            ],
        }

    cand = {"stock_code": "005930", "stock_name": "Big", "sources": ["value"], "ranks": {}, "seed_row": {}}

    # +0.7% : below default min(1.0) → rejected by default, but large-cap min(0.5) admits.
    elig_def, _ = strategy_module._score_candidate(cand, detail_at(0.7), monkeypatch_regime)
    assert elig_def is False  # default 1~29.5 rejects +0.7
    elig_lc, _ = strategy_module._score_candidate(
        cand, detail_at(0.7), monkeypatch_regime, day_change_min=0.5, day_change_max=10
    )
    assert elig_lc is True, "large-cap band 0.5~10 should admit +0.7%"

    # +6% : large-cap max=5 must reject it (overheated for big-cap).
    _, scored6 = strategy_module._score_candidate(
        cand, detail_at(6.0), monkeypatch_regime, day_change_min=0.5, day_change_max=5
    )
    assert any("상승률" in r for r in scored6.get("reasons", []))


def test_degraded_sources_names_the_failing_reads() -> None:
    """A degraded cycle must say which upstream read broke, not just that one did.

    Market legs swallow transport errors into `success=False` instead of
    raising, so if the plan does not carry the breakdown there is no trace
    anywhere. A DNS fault on 2026-07-29 degraded ~10% of cycles and the only
    record was a counter whose detail read "Built intraday strategy plan".
    """

    snapshot = {
        "success": False,
        "sources": {
            "value": {"success": True},
            "gainers": {
                "success": False,
                "api_id": "ka10027",
                "error": "[Errno -3] Temporary failure in name resolution",
            },
            "kospi": {
                "success": False,
                "api_id": "ka20001",
                "return_code": 3,
                "return_msg": "조회가 실패했습니다",
            },
        },
    }
    degraded = strategy_module._degraded_sources({"success": True}, snapshot)

    names = [entry["source"] for entry in degraded]
    assert names == ["gainers", "kospi"], "only failing legs, deterministically ordered"
    assert degraded[0]["error"].startswith("[Errno -3]")
    assert degraded[0]["api_id"] == "ka10027"
    assert degraded[1]["return_msg"] == "조회가 실패했습니다"


def test_degraded_sources_includes_a_failed_account_read() -> None:
    """`success` ANDs the account evaluation in, so it must be nameable too."""

    degraded = strategy_module._degraded_sources(
        {"success": False, "error": "read timeout"},
        {"success": True, "sources": {"value": {"success": True}}},
    )
    assert [e["source"] for e in degraded] == ["account_evaluation"]
    assert degraded[0]["error"] == "read timeout"


def test_degraded_sources_is_empty_on_a_clean_cycle() -> None:
    degraded = strategy_module._degraded_sources(
        {"success": True}, {"success": True, "sources": {"value": {"success": True}}}
    )
    assert degraded == []


def test_degraded_sources_still_reports_a_snapshot_without_a_breakdown() -> None:
    """A stubbed/older snapshot has no `sources`; the failure must not vanish."""

    degraded = strategy_module._degraded_sources({"success": True}, {"success": False})
    assert [e["source"] for e in degraded] == ["market_snapshot"]


def _index_leg(*, rising: int, falling: int, change: str) -> dict:
    return {"rising": str(rising), "fall": str(falling), "flu_rt": change}


def _snapshot(*, kospi_ok: bool = True, kosdaq_ok: bool = True) -> dict:
    """A calm, clearly non-crash market, with per-leg success switchable."""

    return {
        "success": kospi_ok and kosdaq_ok,
        "indices": {
            "kospi": _index_leg(rising=500, falling=300, change="+0.80")
            if kospi_ok
            else {},
            "kosdaq": _index_leg(rising=600, falling=400, change="+0.90")
            if kosdaq_ok
            else {},
        },
        "sources": {
            "kospi": {"success": kospi_ok},
            "kosdaq": {"success": kosdaq_ok},
            "gainers": {"success": True},
        },
    }


def test_regime_is_complete_and_calm_on_a_clean_read() -> None:
    regime = strategy_module._build_market_regime(_snapshot())
    assert regime["market_data_complete"] is True
    assert regime["extreme_risk_off"] is False


def test_regime_marks_a_failed_index_leg_incomplete() -> None:
    """Both legs down zero every figure — the 2026-07-29/30 signature."""

    regime = strategy_module._build_market_regime(
        _snapshot(kospi_ok=False, kosdaq_ok=False)
    )
    assert regime["market_data_complete"] is False
    assert regime["breadth_score"] == 0.0
    assert regime["average_change_pct"] == 0.0
    # Still vetoes new entries — the veto is the safe direction on no data.
    assert regime["extreme_risk_off"] is True


def test_regime_vetoes_entries_when_only_one_leg_fails() -> None:
    """The hole a pure threshold missed.

    One good leg plus one zeroed leg leaves breadth at 0.5 — comfortably
    above the 0.2 crash threshold — so the entry gate would have opened on
    half-read data. Completeness, not the number, has to drive the veto.
    """

    regime = strategy_module._build_market_regime(_snapshot(kosdaq_ok=False))
    assert regime["breadth_score"] > 0.2
    assert regime["market_data_complete"] is False
    assert regime["extreme_risk_off"] is True


def test_regime_treats_a_successful_but_empty_read_as_incomplete() -> None:
    """The open, before the first tick has printed.

    Both legs answer 200 with every count zeroed, so the transport check
    called the read complete — while breadth, 0/max(0,1), came out at 0.0 and
    tripped the 0.2 crash threshold. Numerically identical to a crash, and
    unlike a failed read it stayed dispatchable, so the PM squad was woken by
    a phantom extreme_risk_off at 09:00 on 2026-09-10 (SWO-884) and again on
    2026-09-17 (SWO-938).
    """

    snapshot = _snapshot()
    snapshot["indices"]["kospi"] = _index_leg(rising=0, falling=0, change="0.00")
    snapshot["indices"]["kosdaq"] = _index_leg(rising=0, falling=0, change="0.00")

    regime = strategy_module._build_market_regime(snapshot)

    assert regime["market_data_complete"] is False
    # The entry veto still stands — no data is not permission to buy.
    assert regime["extreme_risk_off"] is True


def test_regime_marks_one_empty_leg_incomplete_too() -> None:
    """A single silent leg still halves breadth, so it cannot be trusted."""

    snapshot = _snapshot()
    snapshot["indices"]["kosdaq"] = _index_leg(rising=0, falling=0, change="0.00")

    regime = strategy_module._build_market_regime(snapshot)

    assert regime["market_data_complete"] is False
    assert regime["extreme_risk_off"] is True


def test_a_thin_but_real_tape_stays_complete() -> None:
    """Only all-zero means no tick. A quiet market must remain dispatchable.

    Otherwise this guard would suppress the very crash it sits next to.
    """

    snapshot = _snapshot()
    snapshot["indices"]["kospi"] = _index_leg(rising=1, falling=0, change="+0.01")
    snapshot["indices"]["kosdaq"] = _index_leg(rising=0, falling=1, change="-0.01")

    regime = strategy_module._build_market_regime(snapshot)

    assert regime["market_data_complete"] is True


def test_regime_defaults_to_complete_without_a_sources_breakdown() -> None:
    """Older/stubbed snapshots must not be read as a permanent outage."""

    regime = strategy_module._build_market_regime(
        {
            "success": True,
            "indices": {
                "kospi": _index_leg(rising=500, falling=300, change="+0.80"),
                "kosdaq": _index_leg(rising=600, falling=400, change="+0.90"),
            },
        }
    )
    assert regime["market_data_complete"] is True
    assert regime["extreme_risk_off"] is False


def test_regime_still_flags_a_genuine_crash_as_complete() -> None:
    """A real crash must stay dispatchable, not be mistaken for an outage."""

    snapshot = _snapshot()
    snapshot["indices"]["kospi"] = _index_leg(rising=20, falling=880, change="-6.20")
    snapshot["indices"]["kosdaq"] = _index_leg(rising=15, falling=900, change="-7.10")
    regime = strategy_module._build_market_regime(snapshot)
    assert regime["market_data_complete"] is True
    assert regime["extreme_risk_off"] is True


def _two_market_snapshot(kospi: dict, kosdaq: dict) -> dict:
    return {
        "success": True,
        "indices": {"kospi": kospi, "kosdaq": kosdaq},
        "sources": {"kospi": {"success": True}, "kosdaq": {"success": True}},
    }


def test_regime_names_the_traded_market() -> None:
    regime = strategy_module._build_market_regime(
        _two_market_snapshot(
            _index_leg(rising=490, falling=381, change="-4.58"),
            _index_leg(rising=736, falling=893, change="+0.26"),
        ),
        leaders_market_tp="001",
    )
    assert regime["primary_market"] == "kospi"
    assert regime["primary_change_pct"] == -4.58
    assert regime["primary_breadth"] == 1.29


def test_regime_vetoes_a_traded_market_crash_the_average_dilutes() -> None:
    """The 2026-08-06 shape, deepened past the threshold.

    KOSPI crashes while KOSDAQ holds up, so the two-market average lands at
    -2.0% — nowhere near -5.0 — even though every candidate comes from the
    KOSPI that just fell 6%.
    """

    snapshot = _two_market_snapshot(
        _index_leg(rising=100, falling=800, change="-6.0"),
        _index_leg(rising=700, falling=500, change="+2.0"),
    )
    diluted = strategy_module._build_market_regime(snapshot)
    assert diluted["average_change_pct"] == -2.0
    assert diluted["extreme_risk_off"] is False, "the hole this closes"

    scoped = strategy_module._build_market_regime(snapshot, leaders_market_tp="001")
    assert scoped["extreme_risk_off"] is True


def test_regime_vetoes_a_mega_cap_breadth_collapse() -> None:
    """Equal-weighted breadth averages away a concentrated large-cap panic."""

    snapshot = _two_market_snapshot(
        _index_leg(rising=40, falling=850, change="-3.0"),
        _index_leg(rising=900, falling=450, change="+1.0"),
    )
    assert strategy_module._build_market_regime(snapshot)["extreme_risk_off"] is False
    scoped = strategy_module._build_market_regime(snapshot, leaders_market_tp="001")
    assert scoped["primary_breadth"] < 0.2
    assert scoped["extreme_risk_off"] is True


def test_regime_scoping_never_loosens_the_veto() -> None:
    """The per-market legs are OR-ed on; a healthy KOSPI cannot clear a
    crash the average already caught."""

    snapshot = _two_market_snapshot(
        _index_leg(rising=700, falling=500, change="+1.0"),
        _index_leg(rising=30, falling=900, change="-11.0"),
    )
    assert strategy_module._build_market_regime(snapshot)["extreme_risk_off"] is True
    scoped = strategy_module._build_market_regime(snapshot, leaders_market_tp="001")
    assert scoped["primary_change_pct"] == 1.0, "traded market itself is fine"
    assert scoped["extreme_risk_off"] is True, "average leg must still hold"


def test_regime_without_a_primary_market_keeps_average_only() -> None:
    """leaders_market_tp='000' scans both, so no single index governs."""

    regime = strategy_module._build_market_regime(
        _two_market_snapshot(
            _index_leg(rising=100, falling=800, change="-6.0"),
            _index_leg(rising=700, falling=500, change="+2.0"),
        ),
        leaders_market_tp="000",
    )
    assert regime["primary_market"] is None
    assert regime["primary_change_pct"] is None
    assert regime["extreme_risk_off"] is False


def _leader_snapshot() -> dict:
    """A movers snapshot with no overlap with the large-cap roster."""

    return {
        "success": True,
        "leaders": {
            "value": [{"stk_cd": "900001", "stk_nm": "무버A"}],
            "gainers": [{"stk_cd": "900002", "stk_nm": "무버B"}],
            "volume": [{"stk_cd": "900003", "stk_nm": "무버C"}],
        },
    }


def test_universe_defaults_to_leaders_only() -> None:
    """Existing callers must see exactly the movers universe they had."""

    rows = strategy_module._merge_leaderboards(_leader_snapshot())
    codes = [r["stock_code"] for r in rows]
    assert set(codes) == {"900001", "900002", "900003"}
    assert codes[0] == "900002", "default sort still leads with gainers"
    assert all("roster" not in r["sources"] for r in rows)


def test_roster_mode_replaces_the_movers_universe() -> None:
    from src.constants.universe import ROSTER_CODES

    rows = strategy_module._merge_leaderboards(
        _leader_snapshot(), roster_codes=ROSTER_CODES, include_leaders=False
    )
    codes = [r["stock_code"] for r in rows]
    assert codes == list(ROSTER_CODES), "roster order preserved, movers dropped"
    assert all(r["sources"] == ["roster"] for r in rows)


def test_both_mode_puts_roster_ahead_of_movers() -> None:
    """The caller scores only `scan_limit` rows, so ordering decides whether
    a roster name is ever looked at."""

    roster = ("005930", "000660")
    rows = strategy_module._merge_leaderboards(
        _leader_snapshot(), roster_codes=roster, include_leaders=True
    )
    codes = [r["stock_code"] for r in rows]
    assert codes[:2] == list(roster)
    assert set(codes[2:]) == {"900001", "900002", "900003"}


def test_roster_ordering_survives_value_first_sort() -> None:
    """value_first exists for the large-cap leaderboard sort; it must not
    push rankless roster rows behind the movers."""

    roster = ("005930", "000660")
    rows = strategy_module._merge_leaderboards(
        _leader_snapshot(),
        roster_codes=roster,
        include_leaders=True,
        value_first=True,
    )
    assert [r["stock_code"] for r in rows][:2] == list(roster)


def test_roster_entry_that_also_leads_keeps_its_leaderboard_row() -> None:
    """A roster name topping a board must not lose its seed row."""

    snap = {
        "success": True,
        "leaders": {"value": [{"stk_cd": "005930", "stk_nm": "삼성전자"}]},
    }
    rows = strategy_module._merge_leaderboards(
        snap, roster_codes=("005930",), include_leaders=True
    )
    assert len(rows) == 1
    assert rows[0]["stock_name"] == "삼성전자"
    assert rows[0]["seed_row"]["stk_cd"] == "005930"
    assert set(rows[0]["sources"]) == {"roster", "value"}


# --- extreme_risk_off hysteresis band ---------------------------------------
#
# Dispatch needs a band so a metric hugging the threshold stops paging the PM
# squad every tick (2026-09-02: primary_breadth 0.19 vs a 0.20 line, 8 rising
# edges in one session). The entry veto must NOT get that band — it has to
# react on the tick the market crosses, and loosening a safety gate to save
# API calls would be the wrong trade.


def _kospi_breadth_snapshot(*, rising: int, falling: int, change: str) -> dict:
    """KOSPI-only crash shaping; KOSDAQ held calm so `primary_*` decides."""

    return {
        "success": True,
        "indices": {
            "kospi": _index_leg(rising=rising, falling=falling, change=change),
            "kosdaq": _index_leg(rising=600, falling=400, change="+0.90"),
        },
        "sources": {
            "kospi": {"success": True},
            "kosdaq": {"success": True},
            "gainers": {"success": True},
        },
    }


def test_breadth_below_entry_threshold_is_extreme_by_both_flags() -> None:
    """0.19 breadth — the reading actually observed on 2026-09-02."""

    regime = strategy_module._build_market_regime(
        _kospi_breadth_snapshot(rising=190, falling=1000, change="-3.99"),
        leaders_market_tp="001",
    )

    assert regime["primary_breadth"] < 0.20
    assert regime["extreme_risk_off"] is True
    assert regime["extreme_risk_off_sticky"] is True


def test_breadth_inside_the_band_clears_entry_but_stays_sticky() -> None:
    """0.21: past the entry line, short of the exit line.

    This is the tick that used to re-arm the rising edge. The veto lifts —
    the market really is above the crash threshold — while dispatch treats it
    as a continuation.
    """

    regime = strategy_module._build_market_regime(
        _kospi_breadth_snapshot(rising=210, falling=1000, change="-3.99"),
        leaders_market_tp="001",
    )

    assert 0.20 <= regime["primary_breadth"] < 0.22
    assert regime["extreme_risk_off"] is False
    assert regime["extreme_risk_off_sticky"] is True


def test_breadth_clear_of_the_exit_band_is_no_longer_sticky() -> None:
    regime = strategy_module._build_market_regime(
        _kospi_breadth_snapshot(rising=300, falling=1000, change="-3.99"),
        leaders_market_tp="001",
    )

    assert regime["extreme_risk_off"] is False
    assert regime["extreme_risk_off_sticky"] is False


def test_the_entry_veto_never_widens_with_the_band() -> None:
    """The safety property: a reading inside the band still allows entry.

    `extreme_risk_off` is what `_review_holding`/`_score_candidate` gate on,
    and it must track the entry thresholds exactly — otherwise this change
    would have quietly extended a new-entry block by a tenth of a point.
    """

    in_band = strategy_module._build_market_regime(
        _kospi_breadth_snapshot(rising=210, falling=1000, change="-3.99"),
        leaders_market_tp="001",
    )
    below = strategy_module._build_market_regime(
        _kospi_breadth_snapshot(rising=190, falling=1000, change="-3.99"),
        leaders_market_tp="001",
    )

    assert below["extreme_risk_off"] is True     # veto on
    assert in_band["extreme_risk_off"] is False  # veto off, sticky still True


def test_an_incomplete_read_is_sticky_too() -> None:
    """A data outage must not look like a fresh crash when it recovers."""

    regime = strategy_module._build_market_regime(_snapshot(kospi_ok=False))

    assert regime["market_data_complete"] is False
    assert regime["extreme_risk_off"] is True
    assert regime["extreme_risk_off_sticky"] is True
