"""Account-related service functions for Kiwoom OpenAPI."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .kiwoom_client import KiwoomClient
from ..constants import ACCOUNT_APIS, APIInfo

RecordExtractor = Callable[[Any], list[Any]]


def _normalize_return_code(value: Any) -> int | None:
    """Normalize Kiwoom business return codes into integers when possible."""

    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    return None


def _extract_business_status(response_data: Any) -> tuple[int | None, str | None]:
    """Extract Kiwoom business status from a response payload."""

    if not isinstance(response_data, dict):
        return None, None
    return (
        _normalize_return_code(response_data.get("return_code")),
        response_data.get("return_msg"),
    )


def _list_from_key(key: str) -> RecordExtractor:
    """Extract a list payload from a named response field."""

    def extractor(response_data: Any) -> list[Any]:
        if isinstance(response_data, dict):
            value = response_data.get(key)
            if isinstance(value, list):
                return value
        if isinstance(response_data, list):
            return response_data
        return []

    return extractor


def _strict_list_from_key(key: str) -> RecordExtractor:
    """Extract a broker list while rejecting malformed "successful" payloads.

    For order reconciliation, a missing list is not equivalent to an empty
    list: only the latter is broker absence evidence.
    """

    def extractor(response_data: Any) -> list[Any]:
        if isinstance(response_data, dict):
            value = response_data.get(key)
            if isinstance(value, list):
                return value
        raise ValueError(f"Kiwoom response missing list field {key!r}")

    return extractor


def _wrap_dict_or_list(response_data: Any) -> list[Any]:
    """Preserve top-level dict responses while still accepting list payloads."""

    if isinstance(response_data, list):
        return response_data
    if isinstance(response_data, dict) and response_data:
        return [response_data]
    return []


def _build_result(
    *,
    api_info: APIInfo,
    context: dict[str, Any],
    result_key: str,
    records: list[Any],
    request_count: int,
    return_code: int | None = None,
    return_msg: str | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    """Create a normalized result payload for Kiwoom query wrappers."""

    success = error is None
    result = {
        "success": success,
        "status_code": 200,
        "api_id": api_info.api_id,
        "api_name": api_info.name,
        **context,
        "total_requests": request_count,
        "total_records": len(records),
        result_key: records,
    }

    if return_code is not None:
        result["return_code"] = return_code
    if return_msg is not None:
        result["return_msg"] = return_msg

    if success:
        result["message"] = f"Successfully retrieved {len(records)} records in {request_count} requests"
    else:
        result["error"] = error
        result["message"] = return_msg or "Kiwoom API returned a business error"

    return result


def _build_exception_result(
    *,
    api_info: APIInfo,
    context: dict[str, Any],
    result_key: str,
    message: str,
    error: Exception,
) -> dict[str, Any]:
    """Create a consistent result for unexpected transport or runtime errors."""

    return {
        "success": False,
        "status_code": None,
        "api_id": api_info.api_id,
        "api_name": api_info.name,
        **context,
        "total_requests": 0,
        "total_records": 0,
        result_key: [],
        "error": str(error),
        "message": message,
        "note": "This requires proper Kiwoom API endpoint configuration",
    }


async def _run_account_query(
    client: KiwoomClient,
    *,
    api_info: APIInfo,
    request_data: dict[str, Any],
    context: dict[str, Any],
    result_key: str,
    extractor: RecordExtractor,
    max_requests: int,
    exception_message: str,
) -> dict[str, Any]:
    """Execute a Kiwoom account query with pagination and business-code handling."""

    try:
        records: list[Any] = []
        cont_yn = "N"
        next_key: str | None = None
        request_count = 0
        return_code: int | None = None
        return_msg: str | None = None

        while request_count < max_requests:
            headers = {
                "api-id": api_info.api_id,
                "cont-yn": cont_yn,
            }
            if next_key:
                headers["next-key"] = next_key

            response = await client.post(api_info.url, json=request_data, headers=headers)
            request_count += 1

            response_data = response.json()
            return_code, return_msg = _extract_business_status(response_data)

            if return_code not in (None, 0):
                return _build_result(
                    api_info=api_info,
                    context=context,
                    result_key=result_key,
                    records=records,
                    request_count=request_count,
                    return_code=return_code,
                    return_msg=return_msg,
                    error=return_msg or f"Kiwoom API returned return_code={return_code}",
                )

            records.extend(extractor(response_data))

            response_cont_yn = response.headers.get("cont-yn", "N")
            response_next_key = response.headers.get("next-key")
            if response_cont_yn == "Y":
                if not response_next_key:
                    raise RuntimeError(
                        "pagination incomplete: cont-yn=Y without next-key"
                    )
                cont_yn = "Y"
                next_key = response_next_key
                continue
            break

        result = _build_result(
            api_info=api_info,
            context=context,
            result_key=result_key,
            records=records,
            request_count=request_count,
            return_code=return_code,
            return_msg=return_msg,
        )
        if request_count >= max_requests:
            result["warning"] = (
                f"Reached maximum request limit ({max_requests}). There may be more data available."
            )
        return result
    except Exception as error:
        return _build_exception_result(
            api_info=api_info,
            context=context,
            result_key=result_key,
            message=exception_message,
            error=error,
        )


async def get_daily_realized_profit_by_stock(
    client: KiwoomClient,
    stock_code: str,
    start_date: str,
    max_requests: int = 10,
) -> dict[str, Any]:
    """
    Get daily realized profit/loss by stock for a specific date with automatic pagination.

    Note:
        The live Kiwoom API accepts ``strt_dt`` and ignores extra keys. ``stock_code`` is
        retained in the wrapper signature for backward compatibility with the MCP tool.
    """

    return await _run_account_query(
        client,
        api_info=ACCOUNT_APIS.daily_realized_profit_by_stock,
        request_data={
            "stk_cd": stock_code,
            "strt_dt": start_date,
        },
        context={
            "stock_code": stock_code,
            "start_date": start_date,
        },
        result_key="realized_profit_data",
        extractor=_list_from_key("dt_stk_div_rlzt_pl"),
        max_requests=max_requests,
        exception_message="Daily realized profit by stock endpoint not yet implemented or failed to connect",
    )


async def get_account_evaluation(
    client: KiwoomClient,
    qry_tp: str = "0",
    dmst_stex_tp: str = "KRX",
    max_requests: int = 10,
) -> dict[str, Any]:
    """Get account evaluation status with automatic pagination."""

    return await _run_account_query(
        client,
        api_info=ACCOUNT_APIS.account_evaluation,
        request_data={
            "qry_tp": qry_tp,
            "dmst_stex_tp": dmst_stex_tp,
        },
        context={
            "qry_tp": qry_tp,
            "dmst_stex_tp": dmst_stex_tp,
        },
        result_key="evaluation_data",
        extractor=_wrap_dict_or_list,
        max_requests=max_requests,
        exception_message="Account evaluation endpoint not yet implemented or failed to connect",
    )


async def get_daily_estimated_asset(
    client: KiwoomClient,
    start_date: str,
    end_date: str,
    max_requests: int = 10,
) -> dict[str, Any]:
    """Get daily estimated deposit asset (kt00002) over a date range.

    Returns a row per day with ``dt`` and ``prsm_dpst_aset_amt`` — the
    server-side total-asset time series for the dashboard chart. Kiwoom
    keeps the history, so no local persistence is needed.
    """

    return await _run_account_query(
        client,
        api_info=ACCOUNT_APIS.daily_estimated_asset,
        request_data={
            "start_dt": start_date,
            "end_dt": end_date,
        },
        context={
            "start_date": start_date,
            "end_date": end_date,
        },
        result_key="daily_estimated_asset_data",
        extractor=_list_from_key("daly_prsm_dpst_aset_amt_prst"),
        max_requests=max_requests,
        exception_message="Daily estimated asset endpoint not yet implemented or failed to connect",
    )


async def get_account_current_status(
    client: KiwoomClient,
    max_requests: int = 10,
) -> dict[str, Any]:
    """Get account daily status with automatic pagination."""

    return await _run_account_query(
        client,
        api_info=ACCOUNT_APIS.account_current_status,
        request_data={},
        context={},
        result_key="daily_status_data",
        extractor=_wrap_dict_or_list,
        max_requests=max_requests,
        exception_message="Account daily status endpoint not yet implemented or failed to connect",
    )


async def get_daily_account_profit_detail(
    client: KiwoomClient,
    fr_dt: str,
    to_dt: str,
    max_requests: int = 10,
) -> dict[str, Any]:
    """Get daily account profit rate detailed status with automatic pagination."""

    return await _run_account_query(
        client,
        api_info=ACCOUNT_APIS.daily_account_profit_detail,
        request_data={
            "fr_dt": fr_dt,
            "to_dt": to_dt,
        },
        context={
            "fr_dt": fr_dt,
            "to_dt": to_dt,
        },
        result_key="profit_detail_data",
        extractor=_wrap_dict_or_list,
        max_requests=max_requests,
        exception_message="Daily account profit detail endpoint not yet implemented or failed to connect",
    )


async def get_orderable_amount(
    client: KiwoomClient,
    stk_cd: str,
    trde_tp: str,
    uv: str,
    io_amt: str = "",
    trde_qty: str = "",
    exp_buy_unp: str = "",
    max_requests: int = 10,
) -> dict[str, Any]:
    """Get orderable or withdrawable amount with automatic pagination."""

    request_data = {
        "stk_cd": stk_cd,
        "trde_tp": trde_tp,
        "uv": uv,
    }
    if io_amt:
        request_data["io_amt"] = io_amt
    if trde_qty:
        request_data["trde_qty"] = trde_qty
    if exp_buy_unp:
        request_data["exp_buy_unp"] = exp_buy_unp

    return await _run_account_query(
        client,
        api_info=ACCOUNT_APIS.orderable_amount,
        request_data=request_data,
        context={
            "stk_cd": stk_cd,
            "trde_tp": trde_tp,
            "uv": uv,
        },
        result_key="orderable_amount_data",
        extractor=_wrap_dict_or_list,
        max_requests=max_requests,
        exception_message="Orderable amount endpoint not yet implemented or failed to connect",
    )


async def get_execution_info(
    client: KiwoomClient,
    qry_tp: str,
    sell_tp: str,
    stex_tp: str,
    stk_cd: str = "",
    ord_no: str = "",
    max_requests: int = 10,
) -> dict[str, Any]:
    """Get execution history using Kiwoom's `ka10076` filled-order query."""

    request_data = {
        "qry_tp": qry_tp,
        "sell_tp": sell_tp,
        "stex_tp": stex_tp,
    }
    if stk_cd:
        request_data["stk_cd"] = stk_cd
    if ord_no:
        request_data["ord_no"] = ord_no

    return await _run_account_query(
        client,
        api_info=ACCOUNT_APIS["ka10076"],
        request_data=request_data,
        context={
            "qry_tp": qry_tp,
            "sell_tp": sell_tp,
            "stex_tp": stex_tp,
            "stk_cd": stk_cd,
            "ord_no": ord_no,
        },
        result_key="execution_data",
        extractor=_strict_list_from_key("cntr"),
        max_requests=max_requests,
        exception_message="Execution info endpoint not yet implemented or failed to connect",
    )


async def get_order_execution_status(
    client: KiwoomClient,
    stk_bond_tp: str,
    mrkt_tp: str,
    sell_tp: str,
    qry_tp: str,
    dmst_stex_tp: str,
    stk_cd: str = "",
    fr_ord_no: str = "",
    max_requests: int = 10,
) -> dict[str, Any]:
    """Get account order/execution status using Kiwoom's `kt00009` query."""

    request_data = {
        "stk_bond_tp": stk_bond_tp,
        "mrkt_tp": mrkt_tp,
        "sell_tp": sell_tp,
        "qry_tp": qry_tp,
        "dmst_stex_tp": dmst_stex_tp,
    }
    if stk_cd:
        request_data["stk_cd"] = stk_cd
    if fr_ord_no:
        request_data["fr_ord_no"] = fr_ord_no

    return await _run_account_query(
        client,
        api_info=ACCOUNT_APIS.order_execution_status,
        request_data=request_data,
        context={
            "stk_bond_tp": stk_bond_tp,
            "mrkt_tp": mrkt_tp,
            "sell_tp": sell_tp,
            "qry_tp": qry_tp,
            "dmst_stex_tp": dmst_stex_tp,
            "stk_cd": stk_cd,
            "fr_ord_no": fr_ord_no,
        },
        result_key="order_execution_status_data",
        extractor=_wrap_dict_or_list,
        max_requests=max_requests,
        exception_message="Order execution status endpoint not yet implemented or failed to connect",
    )


async def get_unexecuted_orders(
    client: KiwoomClient,
    all_stk_tp: str,
    trde_tp: str,
    stex_tp: str,
    stk_cd: str = "",
    max_requests: int = 10,
) -> dict[str, Any]:
    """Get ka10075 unexecuted orders with automatic pagination.

    ``all_stk_tp`` MUST stay in the request body. `kiwoom_api_spec.md` omits it
    from the ka10075 body table, and Phase 0 briefly dropped it on that basis --
    but the live endpoint rejects the request outright::

        입력 값 오류입니다[1511:필수 입력 값에 값이 존재하지 않습니다.
        필수입력 파라미터=all_stk_tp]

    Observed 2026-07-28 against https://api.kiwoom.com. The vendored spec is
    incomplete here; the broker is the authority. Dropping this field breaks
    every open-order read, which silently degrades the oversell guard, the
    stale-unfilled cancel path and the UNKNOWN protective-sell release.
    """

    request_data = {
        "all_stk_tp": all_stk_tp,
        "trde_tp": trde_tp,
        "stex_tp": stex_tp,
    }
    if stk_cd:
        request_data["stk_cd"] = stk_cd

    return await _run_account_query(
        client,
        api_info=ACCOUNT_APIS.unexecuted_orders,
        request_data=request_data,
        context={
            "all_stk_tp": all_stk_tp,
            "trde_tp": trde_tp,
            "stex_tp": stex_tp,
            "stk_cd": stk_cd,
        },
        result_key="unexecuted_orders_data",
        extractor=_strict_list_from_key("oso"),
        max_requests=max_requests,
        exception_message="Unexecuted orders endpoint not yet implemented or failed to connect",
    )


async def get_daily_trading_journal(
    client: KiwoomClient,
    ottks_tp: str = "2",
    ch_crd_tp: str = "0",
    max_requests: int = 10,
) -> dict[str, Any]:
    """Get today's trading journal (당일매매일지) using Kiwoom's `ka10170`.

    Args:
        ottks_tp: 단주구분. 1=당일매수에 대한 당일매도, 2=당일매도 전체
        ch_crd_tp: 현금신용구분. 0=전체, 1=현금매매만, 2=신용매매만
    """

    return await _run_account_query(
        client,
        api_info=ACCOUNT_APIS.daily_trading_journal,
        request_data={"ottks_tp": ottks_tp, "ch_crd_tp": ch_crd_tp},
        context={"ottks_tp": ottks_tp, "ch_crd_tp": ch_crd_tp},
        result_key="trading_journal_data",
        extractor=_list_from_key("tdy_trde_diary"),
        max_requests=max_requests,
        exception_message="Daily trading journal endpoint not yet implemented or failed to connect",
    )


__all__ = [
    "get_daily_realized_profit_by_stock",
    "get_daily_trading_journal",
    "get_account_evaluation",
    "get_daily_estimated_asset",
    "get_account_current_status",
    "get_daily_account_profit_detail",
    "get_orderable_amount",
    "get_execution_info",
    "get_order_execution_status",
    "get_unexecuted_orders",
]
