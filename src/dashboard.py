"""Dashboard web application for Kiwoom account and trade activity."""

from __future__ import annotations

import asyncio
import calendar
import json
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta
from typing import Any, Awaitable, Callable
from zoneinfo import ZoneInfo

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, Response
from starlette.routing import Route

from .agent_overview import build_agent_overview
from .config import Settings, get_settings
from .dashboard_template import DASHBOARD_HTML
from .services import account, benchmark, etf_allocation, krx_calendar, market, market_context
from .services.kiwoom_client import KiwoomClient

KST = ZoneInfo("Asia/Seoul")

TableColumn = dict[str, str]
DashboardLoader = Callable[[KiwoomClient, Settings, str, str], Awaitable[dict[str, Any]]]


def _today_ymd() -> str:
    """Return the current date in Korea as YYYYMMDD."""

    return datetime.now(KST).strftime("%Y%m%d")


def _default_start_date(days: int = 30) -> str:
    """Return a default start date in Korea as YYYYMMDD."""

    return (datetime.now(KST) - timedelta(days=days)).strftime("%Y%m%d")


def _validate_ymd(value: str, field_name: str) -> str:
    """Validate that a string is a YYYYMMDD date."""

    if len(value) != 8 or not value.isdigit():
        raise ValueError(f"{field_name} must be YYYYMMDD")
    return value


def _pick_first(record: dict[str, Any], *keys: str) -> Any:
    """Return the first non-empty value for the given keys."""

    for key in keys:
        value = record.get(key)
        if value not in (None, ""):
            return value
    return ""


def _to_int(value: Any) -> int | None:
    """Convert a Kiwoom numeric field to an int when possible."""

    if isinstance(value, int):
        return value
    if value in (None, ""):
        return None
    text = str(value).replace(",", "").strip()
    if not text:
        return None
    if text.startswith(("+", "-")):
        sign = -1 if text[0] == "-" else 1
        text = text[1:]
    else:
        sign = 1
    if not text.isdigit():
        return None
    return sign * int(text)


def _sort_executions_desc(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sort execution rows newest-first.

    Uses (trade_date, trade_time) when populated; falls back to numeric
    order_no descending so mock-mode rows (which omit date/time) still come
    out in plausibly chronological order.
    """

    def key(row: dict[str, Any]):
        date = str(row.get("trade_date") or "").strip()
        time = str(row.get("trade_time") or "").strip().zfill(6)
        order_no_raw = str(row.get("order_no") or "").strip()
        order_no_int = int(order_no_raw) if order_no_raw.isdigit() else 0
        # Larger key = more recent. Negate order_no so higher numbers sort first
        # when date/time are equal/empty.
        return (date, time, order_no_int)

    return sorted(rows, key=key, reverse=True)


def _tone_for_value(value: Any) -> str:
    """Classify a numeric value for UI styling."""

    number = _to_int(value)
    if number is None:
        return "neutral"
    if number > 0:
        return "positive"
    if number < 0:
        return "negative"
    return "neutral"


def _records(result: dict[str, Any], key: str) -> list[dict[str, Any]]:
    """Return list-like rows from a normalized service result."""

    value = result.get(key, [])
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, dict)]


def _first_record(result: dict[str, Any], key: str) -> dict[str, Any]:
    """Return the first record from a result payload."""

    rows = _records(result, key)
    return rows[0] if rows else {}


def _nested_rows(rows: list[dict[str, Any]], nested_key: str) -> list[dict[str, Any]]:
    """Flatten nested list rows when Kiwoom returns summary + detail arrays."""

    flattened: list[dict[str, Any]] = []
    for row in rows:
        nested = row.get(nested_key)
        if isinstance(nested, list):
            flattened.extend(item for item in nested if isinstance(item, dict))
    return flattened


def _normalize_rows(rows: list[dict[str, Any]], column_aliases: dict[str, list[str]]) -> list[dict[str, Any]]:
    """Normalize raw Kiwoom records into a stable table shape."""

    normalized: list[dict[str, Any]] = []
    for row in rows:
        normalized.append(
            {
                key: _pick_first(row, *aliases)
                for key, aliases in column_aliases.items()
            }
        )
    return normalized


def _source_status(result: dict[str, Any]) -> tuple[str, str]:
    """Convert a Kiwoom response into a dashboard status."""

    message = str(result.get("return_msg") or result.get("message") or "")
    if "관련자료가없습니다" in message or "조회 내역이 없습니다" in message or "해당조회내역이 없습니다" in message:
        return "empty", "빈 결과"
    if not result.get("success", False):
        if "제공되지 않습니다" in message:
            return "unsupported", "모의 미지원"
        return "error", "오류"
    if result.get("total_records", 0) == 0:
        return "empty", "빈 결과"
    return "ok", "정상"


def _table_payload(
    *,
    title: str,
    columns: list[TableColumn],
    rows: list[dict[str, Any]],
    raw_rows: list[dict[str, Any]],
    empty_message: str,
) -> dict[str, Any]:
    """Build a table descriptor for the dashboard UI."""

    return {
        "title": title,
        "columns": columns,
        "rows": rows,
        "raw_rows": raw_rows,
        "row_count": len(raw_rows),
        "empty_message": empty_message,
    }


def _prefer_nonzero(primary: Any, fallback: Any) -> Any:
    """Use fallback when the primary value is empty or zero-like."""

    primary_number = _to_int(primary)
    if primary in ("", None) or primary_number == 0:
        return fallback
    return primary


def _build_asset_series(asset_series_result: dict[str, Any]) -> dict[str, Any]:
    """Normalize kt00002 daily estimated-asset rows into a chart series.

    Each point: {date: 'YYYY-MM-DD', value: <total asset KRW>}. The value
    is `prsm_dpst_aset_amt` (추정예탁자산 = D+2 현금 + 유가평가), the same
    total-asset figure the summary uses. Note: this tracks total ASSET, which
    includes external cash flows (deposits/withdrawals) — it is NOT pure
    trading P&L. See `performance.cumulative_realized_pl` for trade-only P&L.

    `cash` carries `entr` from the same row so the benchmark can tell how
    much of the account was actually invested. Without it an account sitting
    in cash reads as a losing strategy whenever the index rises.
    """

    rows = _records(asset_series_result, "daily_estimated_asset_data")
    points: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        dt = str(row.get("dt") or "").strip()
        amt = _to_int(_pick_first(row, "prsm_dpst_aset_amt"))
        if len(dt) != 8 or amt is None:
            continue
        point: dict[str, Any] = {"date": f"{dt[:4]}-{dt[4:6]}-{dt[6:]}", "value": amt}
        cash = _to_int(_pick_first(row, "entr"))
        if cash is not None:
            point["cash"] = cash
        points.append(point)
    points.sort(key=lambda p: p["date"])
    first = points[0]["value"] if points else None
    last = points[-1]["value"] if points else None
    return {
        "points": points,
        "start_value": first,
        "end_value": last,
        "change": (last - first) if (first is not None and last is not None) else None,
        # total-asset change includes deposits/withdrawals, so don't label it P&L
        "note": "총자산 추이 (입출금 포함 — 매매손익 아님)",
    }


def _annotate_asset_sessions(
    points: list[dict[str, Any]],
    index_bars: list[dict[str, Any]],
    excluded_days: list[dict[str, Any]],
) -> None:
    """Mark trading days and each one's change from the previous session.

    kt00002 returns every calendar day, so weekends and holidays sit in the
    series as copies of the last close: 60 days held about 40 sessions and
    the chart read as a flat line with a few steps. The index bars fetched
    for the benchmark are exactly the exchange's sessions, so they decide
    which points count. Outside the bars' range (today before the index row
    exists, or no index data at all) a weekday stands in.

    `flow_suspect` carries the benchmark's excluded days -- moves too large
    for the trades to explain, which on this account means a deposit or a
    withdrawal -- so the chart can show them apart from trading days.
    """

    sessions = set(benchmark.index_series(index_bars))
    first_session = min(sessions) if sessions else None
    last_session = max(sessions) if sessions else None
    flows = {
        str(row.get("date"))
        for row in excluded_days or []
        if isinstance(row, dict) and row.get("date")
    }
    previous: int | None = None
    for point in points:
        day = point["date"]
        if first_session is not None and first_session <= day <= last_session:
            trading = day in sessions
        else:
            trading = datetime.strptime(day, "%Y-%m-%d").weekday() < 5
        point["trading_day"] = trading
        if not trading:
            continue
        if previous is not None:
            change = point["value"] - previous
            point["day_change"] = change
            point["day_change_pct"] = round(change / previous * 100, 2) if previous else None
        if day in flows:
            point["flow_suspect"] = True
        previous = point["value"]


# kt00015 books a trade on its settlement day, two sessions after the fill,
# in a batch around 01:10 KST. The last three sessions up to today are read
# from the day journal (ka10170) instead -- three, not two, so T-2 is covered
# before that batch has run.
RECENT_JOURNAL_SESSIONS = 3


def _ymd(day: date) -> str:
    return day.strftime("%Y%m%d")


def _parse_ymd(value: str) -> date:
    return datetime.strptime(value, "%Y%m%d").date()


def _code6(value: Any) -> str:
    """`A005930` (kt00004, kt00015) and `005930` (ka10073, ka10170) alike."""

    text = str(value or "").strip()
    if len(text) == 7 and text[0] == "A" and text[1:].isdigit():
        return text[1:]
    return text


def _stock_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Drop the all-empty row ka10170 sends for a day without trades."""

    return [row for row in rows if _code6(row.get("stk_cd")) or str(row.get("stk_nm") or "").strip()]


def _recent_sessions(today: str, start: str, end: str) -> list[str]:
    """The last sessions up to ``today`` that fall inside [start, end].

    A weekday the calendar cannot rule out (an unsupported year) counts as
    a session: asking the journal for a closed day only returns an empty row.
    """

    day = _parse_ymd(today)
    found: list[str] = []
    for _ in range(15):  # enough to cross the longest holiday run
        if len(found) == RECENT_JOURNAL_SESSIONS:
            break
        if krx_calendar.krx_day_status(day).state != krx_calendar.DAY_CLOSED:
            found.append(_ymd(day))
        day -= timedelta(days=1)
    return [d for d in found if start <= d <= end]


def _realized_window_start(start: str, end: str) -> str:
    """Clamp ``start`` to the three months ka10073 answers before ``end``."""

    last = _parse_ymd(end)
    year, month = (last.year, last.month - 3) if last.month > 3 else (last.year - 1, last.month + 9)
    floor = date(year, month, min(last.day, calendar.monthrange(year, month)[1])) + timedelta(days=1)
    return max(start, _ymd(floor))


def _build_trade_history(
    settled_rows: list[dict[str, Any]],
    journals: dict[str, list[dict[str, Any]]],
    realized_rows: list[dict[str, Any]],
    start: str,
    end: str,
) -> list[dict[str, Any]]:
    """Buys and sells by execution day, newest first.

    Until 2026-10-14 the dashboard's trade list was ka10076, which only
    knows today's fills, so a month of trading showed as an empty table.
    Settled trades come from kt00015 by `cntr_dt`. The days in ``journals``
    (recent sessions kt00015 may not have booked yet) come from ka10170 and
    replace whatever kt00015 holds for them. Sells carry the realized P&L
    ka10073 reports for the same day and stock, which nets the whole round
    trip's costs; the journal's own `pl_amt` leaves out the buy commission.
    """

    realized: dict[tuple[str, str], tuple[int, Any]] = {}
    for row in realized_rows:
        key = (str(row.get("dt") or ""), _code6(row.get("stk_cd")))
        pl = _to_int(row.get("tdy_sel_pl"))
        if pl is None:
            continue
        previous = realized.get(key)
        realized[key] = ((previous[0] if previous else 0) + pl, row.get("pl_rt") or "")

    trades: list[dict[str, Any]] = []

    def add(day: str, side: str, row: dict[str, Any], quantity: Any, price: Any,
            amount: Any, fee: Any, profit: Any = None, rate: Any = "") -> None:
        code = _code6(row.get("stk_cd"))
        if side == "매도" and (day, code) in realized:
            profit, rate = realized[(day, code)]
        trades.append({
            "trade_date": day,
            "side": side,
            "stock_name": str(row.get("stk_nm") or "").strip(),
            "stock_code": code,
            "quantity": _to_int(quantity),
            "price": _to_int(price),
            "amount": _to_int(amount),
            "fee_tax": _to_int(fee),
            "profit_loss": _to_int(profit) if side == "매도" else None,
            "profit_rate": rate if side == "매도" else "",
        })

    for row in settled_rows:
        day = str(row.get("cntr_dt") or row.get("trde_dt") or "")
        side = str(row.get("io_tp_nm") or "").strip()
        if not (start <= day <= end) or day in journals or side not in ("매수", "매도"):
            continue
        add(day, side, row, row.get("trde_qty_jwa_cnt"), row.get("trde_unit"),
            row.get("trde_amt"), row.get("tax_sum_cmsn"))

    for day, rows in journals.items():
        for row in _stock_rows(rows):
            bought = _to_int(row.get("buy_qty")) or 0
            sold = _to_int(row.get("sell_qty")) or 0
            # One fee per stock-day; with both legs it goes to the sell,
            # which carries the tax.
            fee = row.get("cmsn_alm_tax")
            if bought > 0:
                add(day, "매수", row, bought, row.get("buy_avg_pric"), row.get("buy_amt"),
                    None if sold > 0 else fee)
            if sold > 0:
                add(day, "매도", row, sold, row.get("sel_avg_pric"), row.get("sell_amt"), fee,
                    row.get("pl_amt"), row.get("prft_rt") or "")

    # Neither source has a fill time. Buys list above sells within a day:
    # closing-auction entries are usually the day's last fill.
    trades.sort(key=lambda t: (t["trade_date"], t["side"] == "매수"), reverse=True)
    return trades


def _realized_table_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """ka10073 rows in the realized-P&L table's shape, newest first."""

    table: list[dict[str, Any]] = []
    for row in rows:
        commission = _to_int(row.get("tdy_trde_cmsn"))
        tax = _to_int(row.get("tdy_trde_tax"))
        table.append({
            "trade_date": str(row.get("dt") or ""),
            "stock_name": str(row.get("stk_nm") or "").strip(),
            "stock_code": _code6(row.get("stk_cd")),
            "quantity": _to_int(row.get("cntr_qty")),
            "buy_price": _to_int(row.get("buy_uv")),
            "sell_price": _to_int(row.get("cntr_pric")),
            "fee_tax": None if commission is None and tax is None else (commission or 0) + (tax or 0),
            "profit_loss": _to_int(row.get("tdy_sel_pl")),
            "profit_rate": row.get("pl_rt") or "",
        })
    table.sort(key=lambda r: r["trade_date"], reverse=True)
    return table



def _target_allocation_card(comparison: dict[str, Any]) -> dict[str, Any]:
    """Performance card: the account against the allocation it should hold."""

    card: dict[str, Any] = {"label": "목표 배분 대비", "kind": "ratio", "tone": "neutral", "value": ""}
    if not comparison.get("available"):
        card["detail"] = comparison.get("reason") or ""
        return card
    gap = comparison.get("alpha_pct")
    card["value"] = gap
    if isinstance(gap, (int, float)):
        card["tone"] = "positive" if gap > 0 else ("negative" if gap < 0 else "neutral")
    card["detail"] = (
        f"계좌 {comparison.get('account_return_pct'):+.2f}% · 목표 배분 "
        f"{comparison.get('index_return_pct'):+.2f}% · {comparison.get('compared_days')}거래일 "
        f"({comparison.get('start_date')}~{comparison.get('end_date')}, %p 차이)"
    )
    return card


async def _target_allocation_closes() -> dict[str, Any]:
    """Daily KRX closes of the allocation's ETFs, shaped like a source result."""

    symbols = {code: f"{code}.KS" for code in etf_allocation.TARGETS}
    api_id = "yahoo:" + ",".join(symbols.values())
    try:
        closes = await market_context.fetch_daily_closes(symbols)
    except Exception as exc:  # noqa: BLE001 - a benchmark leg must not break the page
        return {"success": False, "api_id": api_id, "message": f"{type(exc).__name__}: {exc}"[:200]}
    return {
        "success": True,
        "api_id": api_id,
        "message": "Yahoo 일봉 (비공식)",
        "closes": closes,
        "total_records": sum(len(days) for days in closes.values()),
    }


def _target_allocation_comparison(
    account_points: list[dict[str, Any]], closes_result: dict[str, Any]
) -> dict[str, Any]:
    if not closes_result.get("success"):
        return {
            "available": False,
            "reason": f"목표 배분 ETF 일봉 조회 실패: {closes_result.get('message')}",
        }
    weights = {code: etf_allocation.TARGET_PCT / 100 for code in etf_allocation.TARGETS}
    return benchmark.build_allocation_comparison(
        account_points,
        closes_result["closes"],
        weights,
        names=etf_allocation.TARGETS,
        source="Yahoo 일봉 — KRX 15:30 종가 (비공식)",
    )


async def build_dashboard_snapshot(
    client: KiwoomClient,
    settings: Settings,
    start_date: str,
    end_date: str,
) -> dict[str, Any]:
    """Collect and normalize dashboard data from Kiwoom APIs."""

    # Total-asset chart spans a wider window than the trade tables.
    asset_series_start = _default_start_date(60)
    today = _today_ymd()
    trades_end = min(end_date, today)
    # Both trade tables cover at most the three months ka10073 answers. For
    # kt00015 the cap is about volume: it pages 20 rows at a time, April had
    # 100+ fills on one settlement day, and back-to-back pages draw 429
    # (2026-10-14, 4/1~10/14).
    trades_start = _realized_window_start(start_date, trades_end)
    # Fills up to `end_date` settle (and reach kt00015) up to a few days later.
    history_end = min(today, _ymd(_parse_ymd(end_date) + timedelta(days=10)))
    recent_sessions = _recent_sessions(today, trades_start, end_date)
    journal_days = [day for day in recent_sessions if day != today]

    (
        evaluation_result,
        current_status_result,
        profit_detail_result,
        realized_profit_result,
        trading_journal_result,
        execution_result,
        order_status_result,
        unexecuted_result,
        asset_series_result,
        index_bars_result,
        allocation_closes_result,
        trade_history_result,
        *journal_results,
    ) = await asyncio.gather(
        account.get_account_evaluation(client),
        account.get_account_current_status(client),
        account.get_daily_account_profit_detail(client, start_date, end_date),
        account.get_period_realized_profit(client, trades_start, trades_end),
        account.get_daily_trading_journal(client),
        account.get_execution_info(client, "0", "0", "1"),
        account.get_order_execution_status(client, "1", "0", "0", "0", "KRX"),
        account.get_unexecuted_orders(client, "0", "0", "1"),
        account.get_daily_estimated_asset(client, asset_series_start, end_date),
        # Benchmark leg. One call returns ~600 daily bars, so the window the
        # comparison needs never paginates. `inds_cd` is required — omitting
        # it is answered with 1511, the same shape as the ka10075 outage.
        market.get_index_daily_bars(client, inds_cd="001", base_date=end_date),
        # Second benchmark leg: the target ETF allocation. From Yahoo, not
        # Kiwoom — it spares the app key's rate limit, and its .KS closes are
        # KRX's 15:30 closes where Kiwoom's daily bars end near 20:00.
        _target_allocation_closes(),
        account.get_trade_history(client, trades_start, history_end),
        *(account.get_daily_trading_journal(client, base_dt=day) for day in journal_days),
    )

    evaluation_record = _first_record(evaluation_result, "evaluation_data")
    current_status_record = _first_record(current_status_result, "daily_status_data")
    profit_detail_record = _first_record(profit_detail_result, "profit_detail_data")
    profit_detail_rows = _records(profit_detail_result, "profit_detail_data")
    execution_rows = _records(execution_result, "execution_data")
    realized_profit_rows = _stock_rows(_records(realized_profit_result, "realized_profit_data"))
    trading_journal_rows = _stock_rows(_records(trading_journal_result, "trading_journal_data"))
    unexecuted_rows = _records(unexecuted_result, "unexecuted_orders_data")

    # A journal day replaces kt00015's rows for that day, so only a journal
    # that answered may do so; otherwise kt00015 keeps the day.
    journals = {
        day: _records(result, "trading_journal_data")
        for day, result in zip(journal_days, journal_results)
        if result.get("success")
    }
    if today in recent_sessions and trading_journal_result.get("success"):
        journals[today] = _records(trading_journal_result, "trading_journal_data")
    trade_history = _build_trade_history(
        _records(trade_history_result, "trade_history_data"),
        journals,
        realized_profit_rows,
        trades_start,
        end_date,
    )

    asset_series = _build_asset_series(asset_series_result)
    index_bars = _records(index_bars_result, "index_daily_bars")
    # Same points the chart draws, measured against the index over the same
    # days. Until 2026-09-21 nothing here compared the account to anything.
    benchmark_summary = benchmark.build_comparison(
        asset_series.get("points") or [],
        index_bars,
    )
    _annotate_asset_sessions(
        asset_series.get("points") or [],
        index_bars,
        benchmark_summary.get("excluded_days") or [],
    )
    benchmark_summary["target_allocation"] = _target_allocation_comparison(
        asset_series.get("points") or [],
        allocation_closes_result,
    )

    holdings_rows: list[dict[str, Any]] = []
    if isinstance(evaluation_record.get("stk_acnt_evlt_prst"), list):
        holdings_rows = [
            row for row in evaluation_record["stk_acnt_evlt_prst"]
            if isinstance(row, dict)
        ]

    order_status_summary_rows = _records(order_status_result, "order_execution_status_data")
    order_status_rows = _nested_rows(order_status_summary_rows, "acnt_ord_cntr_prst_array")

    if not order_status_rows:
        order_status_rows = order_status_summary_rows

    # Compute "현금 + 보유 종목 평가금액" explicitly so the user always sees
    # one consolidated figure regardless of Kiwoom's settlement-state quirks
    # in `prsm_dpst_aset_amt` / `aset_evlt_amt`.
    cash_value = _pick_first(
        current_status_record, "entr", "d2_est_dpst", "dpsit", "entr_amt"
    ) or _pick_first(evaluation_record, "entr")
    cash_int = _to_int(cash_value) or 0
    holdings_eval_int = 0
    for row in holdings_rows:
        amount = _pick_first(row, "evlt_amt", "aset_evlt_amt")
        n = _to_int(amount)
        if n is not None:
            holdings_eval_int += n
    # The cash leg is D+2 추정예수금, not today's 예수금 `entr`: `entr` has not
    # seen fills that are still settling, so for two sessions after a sale
    # the proceeds were missing from the total (about a fifth of the account
    # on 2026-10-14) and after a buy the cost was counted twice.
    settled_cash_int = _to_int(
        _pick_first(current_status_record, "d2_entra", "d2_est_dpst")
        or _pick_first(evaluation_record, "d2_entra")
    )
    cash_label = "D+2 예수금"
    if settled_cash_int is None:
        settled_cash_int, cash_label = cash_int, "예수금"
    total_combined = settled_cash_int + holdings_eval_int

    summary = [
        {
            "label": "총 자산 (D+2 예수금+보유평가)",
            "value": str(total_combined) if (settled_cash_int or holdings_eval_int) else "",
            "kind": "currency",
            "tone": "neutral",
            "highlight": True,
            "detail": (
                f"{cash_label} {settled_cash_int:,}원 + 보유 평가 {holdings_eval_int:,}원"
                if (settled_cash_int or holdings_eval_int) else ""
            ),
        },
        {
            "label": "예수금",
            "value": str(cash_int) if cash_int else _pick_first(
                current_status_record, "entr", "d2_est_dpst", "dpsit", "entr_amt", "entr"
            ),
            "fallback": _pick_first(evaluation_record, "entr"),
            "kind": "currency",
            "tone": "neutral",
        },
        {
            "label": "보유 종목 평가금액",
            "value": str(holdings_eval_int) if holdings_eval_int else "",
            "kind": "currency",
            "tone": "neutral",
        },
        {
            "label": "총 추정자산 (Kiwoom)",
            "value": _pick_first(evaluation_record, "prsm_dpst_aset_amt", "aset_evlt_amt"),
            "kind": "currency",
            "tone": "neutral",
        },
        {
            "label": "D+2 예수금",
            "value": _pick_first(current_status_record, "d2_entra", "d2_est_dpst"),
            "fallback": _pick_first(evaluation_record, "d2_entra"),
            "kind": "currency",
            "tone": "neutral",
        },
        # kt00004's own P&L fields, by their spec names (daily_risk.py has
        # the table). These cards read `tdy_lspft_amt` (당일투자원금, a
        # principal) as today's P&L and `lspft_ratio` (당월손익율) as the
        # total rate. What `tdy_lspft` counts is still unverified.
        {
            "label": "당일 손익 (Kiwoom)",
            "value": _pick_first(evaluation_record, "tdy_lspft"),
            "kind": "currency",
            "tone": _tone_for_value(_pick_first(evaluation_record, "tdy_lspft")),
            "detail": (
                f"당일손익율 {_pick_first(evaluation_record, 'tdy_lspft_rt')}%"
                if _pick_first(evaluation_record, "tdy_lspft_rt") else ""
            ),
        },
        {
            "label": "누적 손익률 (Kiwoom)",
            "value": _pick_first(evaluation_record, "lspft_rt"),
            "kind": "ratio",
            "tone": _tone_for_value(_pick_first(evaluation_record, "lspft")),
            "detail": (
                f"누적 투자손익 {_to_int(_pick_first(evaluation_record, 'lspft')):,}원"
                if _to_int(_pick_first(evaluation_record, "lspft")) is not None else ""
            ),
        },
    ]

    for item in summary:
        if item.get("value") in ("", None) and item.get("fallback") not in ("", None):
            item["value"] = item["fallback"]
        item.pop("fallback", None)

    sources = []
    for title, result in [
        ("계좌 평가", evaluation_result),
        ("당일 계좌 현황", current_status_result),
        ("기간별 수익률", profit_detail_result),
        ("실현손익", realized_profit_result),
        ("당일매매일지", trading_journal_result),
        ("체결 내역", execution_result),
        ("주문 체결 현황", order_status_result),
        ("미체결 주문", unexecuted_result),
        # A silent index failure would make the benchmark quietly vanish
        # rather than say why, so it gets a source row like every other leg.
        ("KOSPI 일봉 (벤치마크)", index_bars_result),
        ("목표 배분 ETF 일봉 (Yahoo, 벤치마크)", allocation_closes_result),
        ("매매 이력 (결제분)", trade_history_result),
        *((f"매매일지 {day[4:6]}/{day[6:]}", result) for day, result in zip(journal_days, journal_results)),
    ]:
        status, status_label = _source_status(result)
        sources.append(
            {
                "title": title,
                "api_id": result.get("api_id"),
                "status": status,
                "status_label": status_label,
                "message": result.get("return_msg") or result.get("message"),
                "record_count": result.get("total_records", 0),
            }
        )

    holdings_columns = [
        {"key": "stock_name", "label": "종목"},
        {"key": "stock_code", "label": "코드"},
        {"key": "quantity", "label": "수량"},
        {"key": "avg_price", "label": "평균단가"},
        {"key": "current_price", "label": "현재가"},
        {"key": "evaluation_amount", "label": "평가금액"},
        {"key": "profit_loss", "label": "손익"},
        {"key": "profit_rate", "label": "수익률"},
    ]
    holdings_aliases = {
        "stock_name": ["stk_nm", "item_nm", "name"],
        "stock_code": ["stk_cd", "code"],
        "quantity": ["rmnd_qty", "qty", "hold_qty", "bal_qty"],
        "avg_price": ["avg_prc", "pur_uv", "buy_uv", "avg_uv"],
        "current_price": ["cur_prc", "now_prc", "close_pric"],
        "evaluation_amount": ["evlt_amt", "aset_evlt_amt"],
        "profit_loss": ["lspft_amt", "pl_amt", "evlt_pl"],
        "profit_rate": ["lspft_rt", "lspft_ratio", "pl_rt"],
    }

    order_columns = [
        {"key": "trade_date", "label": "일자"},
        {"key": "trade_time", "label": "시간"},
        {"key": "stock_name", "label": "종목"},
        {"key": "stock_code", "label": "코드"},
        {"key": "side", "label": "구분"},
        {"key": "status", "label": "상태"},
        {"key": "order_qty", "label": "주문수량"},
        {"key": "filled_qty", "label": "체결수량"},
        {"key": "order_price", "label": "주문가"},
        {"key": "filled_price", "label": "체결가"},
        {"key": "order_no", "label": "주문번호"},
    ]
    order_aliases = {
        "trade_date": ["ord_dt", "cntr_dt", "trde_dt", "dt"],
        "trade_time": ["ord_tmd", "ord_tm", "cntr_tm", "tm"],
        "stock_name": ["stk_nm", "item_nm", "name"],
        "stock_code": ["stk_cd", "code"],
        "side": ["trde_tp_nm", "sell_tp_nm", "trde_tp", "sell_tp"],
        "status": ["ord_prst", "cntr_prst", "prst", "stts"],
        "order_qty": ["ord_qty", "qty"],
        "filled_qty": ["cntr_qty", "exec_qty", "engg_qty"],
        "order_price": ["ord_uv", "uv"],
        "filled_price": ["cntr_uv", "exec_uv"],
        "order_no": ["ord_no", "orig_ord_no", "orgn_ord_no"],
    }

    execution_columns = [
        {"key": "trade_date", "label": "일자"},
        {"key": "trade_time", "label": "시간"},
        {"key": "stock_name", "label": "종목"},
        {"key": "stock_code", "label": "코드"},
        {"key": "side", "label": "구분"},
        {"key": "filled_qty", "label": "체결수량"},
        {"key": "filled_price", "label": "체결가"},
        {"key": "amount", "label": "체결금액"},
        {"key": "order_no", "label": "주문번호"},
    ]
    execution_aliases = {
        "trade_date": ["cntr_dt", "ord_dt", "dt"],
        "trade_time": ["cntr_tm", "ord_tmd", "tm"],
        "stock_name": ["stk_nm", "item_nm", "name"],
        "stock_code": ["stk_cd", "code"],
        "side": ["trde_tp_nm", "sell_tp_nm", "sell_tp"],
        "filled_qty": ["cntr_qty", "exec_qty"],
        "filled_price": ["cntr_uv", "exec_uv"],
        "amount": ["cntr_amt", "amt", "engg_amt"],
        "order_no": ["ord_no", "orig_ord_no"],
    }

    trade_history_columns = [
        {"key": "trade_date", "label": "체결일"},
        {"key": "side", "label": "구분"},
        {"key": "stock_name", "label": "종목"},
        {"key": "stock_code", "label": "코드"},
        {"key": "quantity", "label": "수량"},
        {"key": "price", "label": "단가"},
        {"key": "amount", "label": "금액"},
        {"key": "fee_tax", "label": "수수료·세금"},
        {"key": "profit_loss", "label": "실현손익"},
        {"key": "profit_rate", "label": "수익률"},
    ]

    realized_columns = [
        {"key": "trade_date", "label": "매도일"},
        {"key": "stock_name", "label": "종목"},
        {"key": "stock_code", "label": "코드"},
        {"key": "quantity", "label": "수량"},
        {"key": "buy_price", "label": "매입단가"},
        {"key": "sell_price", "label": "매도가"},
        {"key": "fee_tax", "label": "수수료·세금"},
        {"key": "profit_loss", "label": "실현손익"},
        {"key": "profit_rate", "label": "수익률"},
    ]
    trades_since = (
        f"{trades_start[4:6]}/{trades_start[6:]}부터" if trades_start > start_date else ""
    )
    trades_note = f"{trades_since} (최근 3개월)" if trades_since else ""

    trading_journal_columns = [
        {"key": "stock_name", "label": "종목"},
        {"key": "stock_code", "label": "코드"},
        {"key": "buy_qty", "label": "매수수량"},
        {"key": "buy_avg_price", "label": "매수평균가"},
        {"key": "sell_qty", "label": "매도수량"},
        {"key": "sell_avg_price", "label": "매도평균가"},
        {"key": "profit_loss", "label": "손익금액"},
        {"key": "profit_rate", "label": "수익률"},
        {"key": "commission_tax", "label": "수수료/세금"},
    ]
    trading_journal_aliases = {
        "stock_name": ["stk_nm", "item_nm", "name"],
        "stock_code": ["stk_cd", "code"],
        "buy_qty": ["buy_qty", "qty"],
        "buy_avg_price": ["buy_avg_pric", "buy_uv"],
        "sell_qty": ["sell_qty", "sel_qty"],
        "sell_avg_price": ["sel_avg_pric", "sell_uv"],
        "profit_loss": ["pl_amt", "tdy_sel_pl", "lspft_amt"],
        "profit_rate": ["prft_rt", "pl_rt", "lspft_rt"],
        "commission_tax": ["cmsn_alm_tax", "tdy_trde_cmsn"],
    }

    daily_profit_columns = [
        {"key": "trade_date", "label": "일자"},
        {"key": "deposit", "label": "예수금"},
        {"key": "estimated_assets", "label": "추정자산"},
        {"key": "evaluation_amount", "label": "평가금액"},
        {"key": "profit_loss", "label": "손익"},
        {"key": "profit_rate", "label": "수익률"},
    ]
    daily_profit_aliases = {
        "trade_date": ["dt", "base_dt", "trde_dt"],
        "deposit": ["entr_to", "entr_fr", "entr", "dpsit", "d2_entra"],
        "estimated_assets": ["tot_amt_to", "tot_amt_fr", "prsm_dpst_aset_amt", "aset_evlt_amt"],
        "evaluation_amount": ["scrt_evlt_amt_to", "scrt_evlt_amt_fr", "aset_evlt_amt", "evlt_amt"],
        "profit_loss": ["evltv_prft", "lspft_amt", "tdy_lspft_amt"],
        "profit_rate": ["prft_rt", "tern_rt", "lspft_ratio", "lspft_rt"],
    }

    sources_with_issues = [
        source for source in sources if source["status"] in {"unsupported", "error"}
    ]
    empty_sources = [
        source for source in sources if source["status"] == "empty"
    ]
    overview = {
        "holdings_count": len(holdings_rows),
        "active_orders_count": len(unexecuted_rows),
        "order_status_count": len(order_status_rows),
        "executions_count": len(execution_rows),
        "trade_history_count": len(trade_history),
        "realized_trades_count": len(realized_profit_rows),
        "issues_count": len(sources_with_issues),
        "empty_sources_count": len(empty_sources),
    }
    period_start_raw = _pick_first(profit_detail_record, "tot_amt_fr", "invt_bsamt")
    period_current_raw = _prefer_nonzero(
        _pick_first(profit_detail_record, "tot_amt_to"),
        _pick_first(evaluation_record, "prsm_dpst_aset_amt", "aset_evlt_amt"),
    )
    period_start_value = _to_int(period_start_raw)
    period_current_value = _to_int(period_current_raw)
    # kt00016 nets deposits and withdrawals out of `evltv_prft` and rates it
    # on the average invested principal (`prft_rt`). The end-minus-start
    # asset difference counts a withdrawal as a loss: a half year with one
    # large withdrawal read as a deep loss where Kiwoom reported a gain (10/9).
    broker_profit = _to_int(_pick_first(profit_detail_record, "evltv_prft"))
    try:
        broker_rate: float | None = round(
            float(str(_pick_first(profit_detail_record, "prft_rt")).replace(",", "")), 2
        )
    except ValueError:
        broker_rate = None
    # Until the end date has closed, kt00016 has no row for it: every `*_to`
    # field reads 0 and `evltv_prft` is minus the starting assets, -100%.
    # With the default end date of today that was the dashboard's state for
    # the whole day (2026-10-14). The flow totals are still filled in then.
    broker_closed = bool(_to_int(_pick_first(profit_detail_record, "tot_amt_to")))
    deposits = _to_int(_pick_first(profit_detail_record, "termin_tot_trns")) or 0
    withdrawals = _to_int(_pick_first(profit_detail_record, "termin_tot_pymn")) or 0
    flow_note = (
        f"입금 {deposits:,}원 · 출금 {withdrawals:,}원 제외" if (deposits or withdrawals) else ""
    )
    period_flow_detail = flow_note
    if broker_closed and broker_profit is not None and broker_rate is not None:
        period_profit_value: Any = broker_profit
        period_rate_value: Any = broker_rate
    elif period_start_value is not None and period_current_value is not None:
        # The same netting by hand, on today's estimated assets (kt00004).
        period_profit_value = period_current_value - period_start_value - (deposits - withdrawals)
        rate_base = _to_int(_pick_first(profit_detail_record, "invt_bsamt")) or period_start_value
        period_rate_value = round(period_profit_value / rate_base * 100, 2) if rate_base else 0
        if profit_detail_record and not broker_closed:
            period_flow_detail = " · ".join(
                part for part in (flow_note, "키움 기간 집계 전 — 현재 추정자산 기준") if part
            )
    elif broker_closed:
        # `tern_rt` is turnover (626% over the same window), not a return.
        period_profit_value = _pick_first(profit_detail_record, "evltv_prft", "lspft_amt")
        period_rate_value = _pick_first(profit_detail_record, "prft_rt")
    else:
        period_profit_value = ""
        period_rate_value = ""

    # Derived performance — works in mock where kt00016 (period profit) is
    # unsupported. Period sells (ka10073) + holdings unrealized P&L for a
    # picture of "what happened this period". This read today's journal
    # (ka10170) until 2026-10-14, so the card was empty on any day without
    # a sell, whatever the period.
    realized_pl_int = 0
    commission_int = 0
    win_count = 0
    loss_count = 0
    closed_trade_count = 0
    biggest_winner = None  # (gain_int, name)
    biggest_loser = None
    for row in realized_profit_rows:
        pl_int = _to_int(row.get("tdy_sel_pl"))
        if pl_int is None:
            continue
        closed_trade_count += 1
        realized_pl_int += pl_int
        commission_int += (_to_int(row.get("tdy_trde_cmsn")) or 0) + (_to_int(row.get("tdy_trde_tax")) or 0)
        if pl_int > 0:
            win_count += 1
            if biggest_winner is None or pl_int > biggest_winner[0]:
                biggest_winner = (pl_int, _pick_first(row, "stk_nm", "item_nm", "name") or "?")
        elif pl_int < 0:
            loss_count += 1
            if biggest_loser is None or pl_int < biggest_loser[0]:
                biggest_loser = (pl_int, _pick_first(row, "stk_nm", "item_nm", "name") or "?")

    unrealized_pl_int = 0
    for row in holdings_rows:
        upl = _to_int(
            _pick_first(row, "lspft_amt", "pl_amt", "evlt_pl", "evltv_prft")
        )
        if upl is not None:
            unrealized_pl_int += upl

    total_pl_int = realized_pl_int + unrealized_pl_int
    realized_ok = bool(realized_profit_result.get("success"))
    win_rate_value: Any = ""
    if win_count + loss_count > 0:
        win_rate_value = round(win_count / (win_count + loss_count) * 100, 1)

    # The period's own starting assets (kt00016) first; cash+holdings is a
    # today figure and, inside the T+2 window, counts a trade twice or not
    # at all (roadmap), so it is only the fallback.
    pl_rate_value: Any = ""
    asset_base = period_start_value or total_combined or 0
    if asset_base:
        pl_rate_value = round(total_pl_int / asset_base * 100, 2)

    performance = [
        {
            "label": "기간 시작 자산",
            "value": period_start_raw,
            "kind": "currency",
            "tone": "neutral",
        },
        {
            "label": "현재 기준 자산",
            "value": period_current_raw,
            "kind": "currency",
            "tone": "neutral",
        },
        {
            "label": "기간 손익 (Kiwoom)",
            "value": period_profit_value,
            "kind": "currency",
            "tone": _tone_for_value(period_profit_value),
            "detail": period_flow_detail,
        },
        {
            "label": "기간 수익률 (Kiwoom)",
            "value": period_rate_value,
            "kind": "ratio",
            "tone": _tone_for_value(period_profit_value),
        },
        {
            "label": "실현 손익 (기간)",
            # A period without a sell is 0, not missing; only a failed read is.
            "value": str(realized_pl_int) if realized_ok else "",
            "kind": "currency",
            "tone": _tone_for_value(realized_pl_int),
            "detail": " · ".join(
                part for part in (
                    f"매도 {closed_trade_count}건 · 수수료·세금 {commission_int:,}원"
                    if closed_trade_count else "기간 중 매도 없음",
                    trades_note,
                ) if part
            ) if realized_ok else "",
        },
        {
            "label": "미실현 손익 (보유 평가)",
            "value": str(unrealized_pl_int) if holdings_rows else "",
            "kind": "currency",
            "tone": _tone_for_value(unrealized_pl_int),
            "detail": f"보유 {len(holdings_rows)}종목" if holdings_rows else "",
        },
        {
            "label": "종합 손익",
            "value": str(total_pl_int) if (realized_ok or holdings_rows) else "",
            "kind": "currency",
            "tone": _tone_for_value(total_pl_int),
            "highlight": True,
            "detail": (
                f"기간 실현 {realized_pl_int:+,}{f'({trades_since})' if trades_since else ''} "
                f"+ 보유 평가 {unrealized_pl_int:+,} (매매손익만 — 입출금 무관)"
                if (realized_ok or holdings_rows) else ""
            ),
        },
        {
            "label": "종합 수익률",
            "value": pl_rate_value,
            "kind": "ratio",
            "tone": _tone_for_value(total_pl_int),
            "detail": (
                f"기준자산 {asset_base:,}원 대비" if asset_base else ""
            ),
        },
        _target_allocation_card(benchmark_summary.get("target_allocation") or {}),
        {
            "label": "거래 통계",
            "value": (
                f"{win_count}승 {loss_count}패"
                if (win_count or loss_count) else ""
            ),
            "kind": "text",
            "tone": (
                "positive" if win_count > loss_count
                else "negative" if loss_count > win_count
                else "neutral"
            ),
            "detail": (
                f"승률 {win_rate_value}%" if win_rate_value != "" else ""
            ),
        },
        {
            "label": "최고 수익 종목",
            "value": (
                f"{biggest_winner[1]} {biggest_winner[0]:+,}원"
                if biggest_winner else ""
            ),
            "kind": "text",
            "tone": "positive" if biggest_winner else "neutral",
        },
        {
            "label": "최대 손실 종목",
            "value": (
                f"{biggest_loser[1]} {biggest_loser[0]:+,}원"
                if biggest_loser else ""
            ),
            "kind": "text",
            "tone": "negative" if biggest_loser else "neutral",
        },
    ]

    return {
        "generated_at": datetime.now(KST).isoformat(),
        "environment": {
            "mode": "mock" if settings.use_mock else "live",
            "label": "Mock Investment" if settings.use_mock else "Live Trading",
            "base_url": settings.active_base_url,
        },
        "filters": {
            "start_date": start_date,
            "end_date": end_date,
        },
        "identity": {
            "account_name": _pick_first(evaluation_record, "acnt_nm") or "계좌명 없음",
            "branch_name": _pick_first(evaluation_record, "brch_nm") or "지점 정보 없음",
        },
        "overview": overview,
        "performance": performance,
        "summary": summary,
        "asset_series": asset_series,
        "benchmark": benchmark_summary,
        "sources": sources,
        "tables": {
            "holdings": _table_payload(
                title="보유 종목",
                columns=holdings_columns,
                rows=_normalize_rows(holdings_rows, holdings_aliases),
                raw_rows=holdings_rows,
                empty_message="현재 보유 종목이 없습니다.",
            ),
            "unexecuted_orders": _table_payload(
                title="미체결 주문",
                columns=order_columns,
                rows=_normalize_rows(unexecuted_rows, order_aliases),
                raw_rows=unexecuted_rows,
                empty_message="현재 미체결 주문이 없습니다.",
            ),
            "order_status": _table_payload(
                title="주문 체결 현황",
                columns=order_columns,
                rows=_normalize_rows(order_status_rows, order_aliases),
                raw_rows=order_status_rows,
                empty_message="조회 가능한 주문 현황이 없습니다.",
            ),
            "executions": _table_payload(
                title="체결 이력",
                columns=execution_columns,
                rows=_sort_executions_desc(
                    _normalize_rows(execution_rows, execution_aliases)
                ),
                raw_rows=execution_rows,
                empty_message="체결 이력이 없습니다.",
            ),
            "trade_history": {
                **_table_payload(
                    title="매매 이력",
                    columns=trade_history_columns,
                    rows=trade_history,
                    raw_rows=trade_history,
                    empty_message="선택 기간의 매매 내역이 없습니다.",
                ),
                "note": " · ".join(
                    part for part in (trades_note, "최근 3거래일은 당일매매일지, 그 전은 결제 내역 기준") if part
                ),
            },
            "realized_profit": {
                **_table_payload(
                    title="실현손익",
                    columns=realized_columns,
                    rows=_realized_table_rows(realized_profit_rows),
                    raw_rows=realized_profit_rows,
                    empty_message="선택 기간의 실현손익이 없습니다.",
                ),
                "note": trades_note,
            },
            "trading_journal": _table_payload(
                title="당일매매일지",
                columns=trading_journal_columns,
                rows=_normalize_rows(trading_journal_rows, trading_journal_aliases),
                raw_rows=trading_journal_rows,
                empty_message="당일 매매 내역이 없습니다.",
            ),
            "daily_profit_detail": _table_payload(
                title="기간별 수익률",
                columns=daily_profit_columns,
                rows=_normalize_rows(profit_detail_rows, daily_profit_aliases),
                raw_rows=profit_detail_rows,
                empty_message="선택 기간의 수익률 상세 데이터가 없습니다.",
            ),
        },
    }


def _render_dashboard_page(initial_config: dict[str, Any]) -> str:
    """Return the dashboard shell HTML."""

    initial_json = json.dumps(initial_config, ensure_ascii=False)
    return DASHBOARD_HTML.replace("__INITIAL_CONFIG__", initial_json)


async def _homepage(request: Request) -> HTMLResponse:
    """Serve the dashboard shell."""

    default_start = _default_start_date()
    default_end = _today_ymd()
    return HTMLResponse(
        _render_dashboard_page(
            {
                "start_date": default_start,
                "end_date": default_end,
            }
        )
    )


async def _favicon(_: Request) -> Response:
    """Return an empty favicon response to avoid noisy 404s."""

    return Response(status_code=204)


def create_dashboard_app(
    *,
    data_loader: DashboardLoader | None = None,
) -> Starlette:
    """Create the dashboard ASGI application."""

    settings = get_settings()
    loader = data_loader or build_dashboard_snapshot

    @asynccontextmanager
    async def lifespan(app: Starlette):
        app.state.settings = settings
        app.state.kiwoom_client = KiwoomClient(settings)
        try:
            yield
        finally:
            await app.state.kiwoom_client.close()

    async def dashboard_api(request: Request) -> JSONResponse:
        start_date = request.query_params.get("start_date", _default_start_date())
        end_date = request.query_params.get("end_date", _today_ymd())

        try:
            start_date = _validate_ymd(start_date, "start_date")
            end_date = _validate_ymd(end_date, "end_date")
        except ValueError as exc:
            return JSONResponse({"success": False, "error": str(exc)}, status_code=400)

        payload = await loader(
            request.app.state.kiwoom_client,
            request.app.state.settings,
            start_date,
            end_date,
        )
        return JSONResponse(payload)

    async def agent_overview_api(request: Request) -> JSONResponse:
        try:
            payload = await build_agent_overview(request.app.state.kiwoom_client)
            return JSONResponse(payload)
        except Exception as exc:
            return JSONResponse(
                {"success": False, "error": f"agent_overview build 실패: {exc}"},
                status_code=500,
            )

    routes = [
        Route("/", endpoint=_homepage),
        Route("/favicon.ico", endpoint=_favicon),
        Route("/api/dashboard", endpoint=dashboard_api),
        Route("/api/agent_overview", endpoint=agent_overview_api),
    ]
    return Starlette(routes=routes, lifespan=lifespan)


app = create_dashboard_app()


__all__ = ["app", "build_dashboard_snapshot", "create_dashboard_app"]
