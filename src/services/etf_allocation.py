"""Low-turnover index allocation, independent of the legacy entry score.

This is market exposure, not a claim of monthly alpha. Orders still belong to
the watcher's ledger/reconciliation path. No order API is imported here.
"""
from __future__ import annotations

from datetime import datetime
from math import floor, isfinite
from typing import Any
from zoneinfo import ZoneInfo

MODE = "etf_allocation"
TARGETS = {"069500": "KODEX 200", "133690": "TIGER 미국나스닥100"}
TARGET_PCT = 47
BAND_PCT = 10
KST = ZoneInfo("Asia/Seoul")


def normalized_code(value: Any) -> str:
    code = str(value or "").strip()
    return code[1:] if len(code) == 7 and code.startswith("A") else code


def verified_assets(summary: dict) -> int:
    """Account NAV has a real sign, unlike signed Kiwoom quote prices."""
    try:
        assets = int(str(summary.get("prsm_dpst_aset_amt")).replace(",", ""))
    except (TypeError, ValueError):
        raise ValueError("결제 기준 총 추정자산 확인 불가") from None
    if assets <= 0:
        raise ValueError("결제 기준 총 추정자산은 양수여야 함")
    return assets


def allocation_orders(
    *, assets: float, holdings: list[dict], prices: dict[str, float], now: datetime,
) -> dict[str, list[dict]]:
    """Integer-share target deltas. Seed missing ETFs; rebalance in days 1–7.

    A held ETF is adjusted only outside a ten-percentage-point band. Shares
    remaining in that band are left alone, including after a restart. Legacy
    securities are a migration, not an invitation to exceed the two slots.
    """
    if not isfinite(assets) or assets <= 0:
        raise ValueError("ETF allocation requires verified positive account assets")
    if any(not isfinite(prices.get(c, 0)) or prices.get(c, 0) <= 0 for c in TARGETS):
        raise ValueError("ETF allocation requires both current ETF prices")
    owned = {}
    for h in holdings:
        code = normalized_code(h.get("stock_code"))
        qty = h.get("quantity")
        if not code or not isinstance(qty, int) or qty < 0 or code in owned:
            raise ValueError("invalid/duplicate allocation holding")
        if qty:
            owned[code] = h
    sells, buys = [], []
    for code, h in owned.items():
        if code not in TARGETS:
            sells.append({**h, "stock_code": code, "reason": "ETF 배분으로 전환"})
    monthly_window = now.astimezone(KST).day <= 7
    for code, name in TARGETS.items():
        price = prices[code]
        quantity = owned.get(code, {}).get("quantity", 0)
        current_pct = quantity * price / assets * 100
        target_quantity = floor(assets * TARGET_PCT / 100 / price)
        if quantity and (not monthly_window or abs(current_pct - TARGET_PCT) < BAND_PCT):
            continue
        delta = target_quantity - quantity
        item = {
            "stock_code": code, "stock_name": name, "quantity": abs(delta),
            "current_price": price, "target_quantity": target_quantity,
            "reason": "초기 ETF 배분" if not quantity else "월초 ETF 비중 조정",
        }
        if delta > 0:
            buys.append(item)
        elif delta < 0:
            sells.append(item)
    return {"sells": sells, "buys": buys}


async def plan_etf_allocation(client, settings, *, holding_observer=None,
                              position_budget_pct=TARGET_PCT, max_positions=2,
                              stock_detail_cache_ttl_seconds=75, now=None, **_):
    """Publish a read-only plan in the shape consumed by IntradayWatcher."""
    from . import account, market
    from .strategy import _normalize_holding_rows, _build_market_regime, _to_price, _extract_open_order_codes

    if position_budget_pct != TARGET_PCT or max_positions != 2:
        raise ValueError("etf_allocation requires position_budget_pct=47 and max_positions=2")
    now = now or datetime.now(KST)
    evaluation = await account.get_account_evaluation(client)
    summary, holdings = _normalize_holding_rows(evaluation)
    if holding_observer is not None and evaluation.get("success"):
        await holding_observer(holdings)
    if not evaluation.get("success") or evaluation.get("warning"):
        raise ValueError("ETF 배분을 위한 계좌 조회 불완전")
    raw = evaluation.get("evaluation_data")
    if (not isinstance(raw, list) or len(raw) != 1 or not isinstance(raw[0], dict)
            or not isinstance(raw[0].get("stk_acnt_evlt_prst"), list)):
        raise ValueError("ETF 배분을 위한 계좌 원본 형식 불완전")
    # Normalization must not silently drop a malformed, nonzero position.
    source_positions = []
    for row in raw[0]["stk_acnt_evlt_prst"]:
        if not isinstance(row, dict):
            raise ValueError("ETF 배분 보유종목 행 형식 오류")
        quantity = int(str(row.get("rmnd_qty")).replace(",", ""))
        if quantity < 0:
            raise ValueError("ETF 배분 보유 수량은 음수일 수 없음")
        if quantity:
            source_positions.append(row)
    if len(source_positions) != len(holdings):
        raise ValueError("ETF 배분 보유종목 누락")
    assets = verified_assets(summary)
    orders = await account.get_unexecuted_orders(client, "0", "0", "1")
    snapshot = await market.get_market_snapshot(
        client, watchlist=list(TARGETS), leaders_limit=1,
        stock_detail_cache_ttl_seconds=stock_detail_cache_ttl_seconds,
        leaders_market_tp="001",
    )
    regime = _build_market_regime(snapshot, leaders_market_tp="001")
    details = {normalized_code(d.get("stock_code")): d for d in snapshot.get("watchlist_details", [])}
    prices = {c: _to_price((details.get(c, {}).get("quote") or {}).get("cur_prc")) or 0 for c in TARGETS}
    if any(details.get(c, {}).get("success") is not True for c in TARGETS):
        raise ValueError("ETF 시세 조회 불완전")
    deltas = allocation_orders(assets=assets, holdings=holdings, prices=prices, now=now)
    healthy = bool(
        snapshot.get("success") and orders.get("success") and not orders.get("warning")
        and isinstance(orders.get("unexecuted_orders_data"), list)
        and regime.get("market_data_complete")
    )
    if not healthy:
        deltas = {"buys": [], "sells": []}  # routine rebalancing waits; hard exits ran above
    return {
        "success": healthy, "strategy_name": MODE, "regime": regime,
        "portfolio": {
            "estimated_assets": assets, "position_budget": floor(assets * TARGET_PCT / 100),
            "max_positions": 2, "max_new_positions": 2, "holding_count": len(holdings),
            "open_order_count": len(_extract_open_order_codes(orders)),
            "cash_d2": _to_price(summary.get("d2_entra")),
            "daily_pl_krw": summary.get("tdy_lspft"),
        },
        "holdings": holdings, "allocation": deltas, "allocation_prices": prices,
        "candidate_rows": [
            {**r, "eligible": not regime.get("extreme_risk_off"), "score": 100,
             "entry_price": str(int(r["current_price"])), "entry_order_type_code": "0"}
            for r in deltas["buys"]
        ],
    }
