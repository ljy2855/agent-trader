"""Live order service functions for Kiwoom OpenAPI.

A note on what ``success`` means here: it says the broker accepted the
*request*, not that anything was executed. Kiwoom answers ``return_code=0``
the moment an order is booked and reports the fill on a separate query, so
callers must classify these dicts through
``order_result.OrderApplyResult.from_order_response`` rather than treating
``success`` as a trade. Transport failures additionally carry
``transport_state`` so a lost response is never mistaken for a rejection.

Broker order numbers are best-effort: ``kiwoom_api_spec.md`` documents only
``dmst_stex_tp`` in the kt10000/kt10001 response body and only
``base_orig_ord_no`` for kt10002/kt10003, so ``order_no`` is populated when
the live payload happens to carry one and omitted otherwise.
"""

from __future__ import annotations

import asyncio
from typing import Any

import httpx

from .kiwoom_client import KiwoomClient
from .order_result import (
    ORDER_STATE_FAILED,
    classify_transport_error,
    extract_order_no,
)
from ..constants import APIInfo, ORDER_APIS


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


def _build_order_result(
    *,
    api_info: APIInfo,
    context: dict[str, Any],
    result_key: str,
    payload: Any,
    return_code: int | None = None,
    return_msg: str | None = None,
    error: str | None = None,
    status_code: int = 200,
    success_message: str,
) -> dict[str, Any]:
    """Create a normalized result payload for live order requests."""

    success = error is None
    result = {
        "success": success,
        "status_code": status_code,
        "api_id": api_info.api_id,
        "api_name": api_info.name,
        **context,
        result_key: payload,
    }

    if return_code is not None:
        result["return_code"] = return_code
    if return_msg is not None:
        result["return_msg"] = return_msg

    order_no = extract_order_no(payload)
    if order_no:
        result["order_no"] = order_no

    if success:
        result["message"] = return_msg or success_message
    else:
        result["error"] = error
        result["message"] = return_msg or error or "Kiwoom API returned a business error"

    return result


def _build_exception_result(
    *,
    api_info: APIInfo,
    context: dict[str, Any],
    result_key: str,
    message: str,
    error: Exception,
    transport_state: str | None = None,
) -> dict[str, Any]:
    """Create a consistent result for transport or runtime errors.

    ``transport_state`` separates "the broker definitively never saw this"
    (``failed``) from "the request went out and we lost the answer"
    (``unknown``). Only the first is safe to retry — see
    :func:`order_result.classify_transport_error`.
    """

    return {
        "success": False,
        "status_code": None,
        "api_id": api_info.api_id,
        "api_name": api_info.name,
        **context,
        result_key: None,
        "error": str(error),
        "message": message,
        "transport_state": transport_state or classify_transport_error(error),
        "note": "This requires proper Kiwoom API endpoint configuration",
    }


def _normalize_stock_code(value: Any) -> str:
    """Strip the KRX account-prefix form (e.g. ``A005930``) for order APIs.

    KRX tickers are 6 alphanumeric characters. Numeric-only codes are the
    common case; specialty securities (SPACs, certain REITs, M-class) embed
    one or two letters — e.g. ``메쥬`` is ``0088M0``. Kiwoom's account
    APIs return both forms with a leading ``A`` prefix; the order API
    requires the prefix removed regardless of letter content.

    2026-04-28 (SWO-180): the prior `[1:].isdigit()` guard rejected
    ``A0088M0`` and the prefix was kept, causing order API error 1902
    "종목 정보가 없습니다" and a stuck +36% live position on 메쥬.
    """

    code = str(value or "").strip().upper()
    if (
        len(code) == 7
        and code.startswith("A")
        and code[1:].isalnum()
    ):
        return code[1:]
    return code


async def _submit_order(
    client: KiwoomClient,
    *,
    api_info: APIInfo,
    request_data: dict[str, Any],
    context: dict[str, Any],
    result_key: str,
    success_message: str,
    exception_message: str,
) -> dict[str, Any]:
    """Submit a live order request to Kiwoom and normalize the response."""

    for attempt in range(3):
        try:
            response = await client.post(
                api_info.url,
                headers={"api-id": api_info.api_id, "cont-yn": "N"},
                json=request_data,
            )
            response_data = response.json()
            if not isinstance(response_data, dict):
                # HTTP 200 plus syntactically valid JSON is not proof that
                # Kiwoom accepted an order. A list/scalar body carries no
                # business verdict, so classify it through the conservative
                # transport-error path (`unknown`) rather than inventing a
                # successful submission. This also keeps protective-sell
                # liveness available instead of wedging a false SUBMITTED
                # intent forever.
                raise ValueError(
                    "order API response JSON must be an object, got "
                    f"{type(response_data).__name__}"
                )
            return_code, return_msg = _extract_business_status(response_data)

            if return_code not in (None, 0):
                return _build_order_result(
                    api_info=api_info,
                    context=context,
                    result_key=result_key,
                    payload=response_data,
                    return_code=return_code,
                    return_msg=return_msg,
                    error=return_msg or f"Kiwoom API returned return_code={return_code}",
                    success_message=success_message,
                )

            return _build_order_result(
                api_info=api_info,
                context=context,
                result_key=result_key,
                payload=response_data,
                return_code=return_code,
                return_msg=return_msg,
                success_message=success_message,
            )
        except httpx.HTTPStatusError as error:
            status_code = getattr(error.response, "status_code", None)
            if status_code == 429 and attempt < 2:
                await asyncio.sleep(1.2 * (attempt + 1))
                continue
            return _build_exception_result(
                api_info=api_info,
                context=context,
                result_key=result_key,
                message=exception_message,
                error=error,
            )
        except Exception as error:
            return _build_exception_result(
                api_info=api_info,
                context=context,
                result_key=result_key,
                message=exception_message,
                error=error,
            )

    # Defensive tail: every branch above returns, so this only fires if the
    # retry loop is ever restructured. Giving up after repeated 429s means the
    # broker rejected each attempt outright, so this is `failed`, not `unknown`.
    return _build_exception_result(
        api_info=api_info,
        context=context,
        result_key=result_key,
        message=exception_message,
        error=RuntimeError("Kiwoom order submission retries exhausted"),
        transport_state=ORDER_STATE_FAILED,
    )


async def place_stock_buy_order(
    client: KiwoomClient,
    stk_cd: str,
    ord_qty: str,
    order_type_code: str,
    dmst_stex_tp: str = "KRX",
    ord_uv: str = "",
    cond_uv: str = "",
) -> dict[str, Any]:
    """Submit a live stock buy order to Kiwoom."""

    normalized_stock_code = _normalize_stock_code(stk_cd)
    request_data = {
        "stk_cd": normalized_stock_code,
        "ord_qty": ord_qty,
        "trde_tp": order_type_code,
        "dmst_stex_tp": dmst_stex_tp,
    }
    if ord_uv:
        request_data["ord_uv"] = ord_uv
    if cond_uv:
        request_data["cond_uv"] = cond_uv

    return await _submit_order(
        client,
        api_info=ORDER_APIS.buy_order,
        request_data=request_data,
        context={
            "stk_cd": normalized_stock_code,
            "ord_qty": ord_qty,
            "order_type_code": order_type_code,
            "dmst_stex_tp": dmst_stex_tp,
            "ord_uv": ord_uv,
            "cond_uv": cond_uv,
        },
        result_key="buy_order_result",
        success_message="Live stock buy order request submitted",
        exception_message="Stock buy order endpoint not yet implemented or failed to connect",
    )


async def place_stock_sell_order(
    client: KiwoomClient,
    stk_cd: str,
    ord_qty: str,
    order_type_code: str,
    dmst_stex_tp: str = "KRX",
    ord_uv: str = "",
    cond_uv: str = "",
) -> dict[str, Any]:
    """Submit a live stock sell order to Kiwoom."""

    normalized_stock_code = _normalize_stock_code(stk_cd)
    request_data = {
        "stk_cd": normalized_stock_code,
        "ord_qty": ord_qty,
        "trde_tp": order_type_code,
        "dmst_stex_tp": dmst_stex_tp,
    }
    if ord_uv:
        request_data["ord_uv"] = ord_uv
    if cond_uv:
        request_data["cond_uv"] = cond_uv

    return await _submit_order(
        client,
        api_info=ORDER_APIS.sell_order,
        request_data=request_data,
        context={
            "stk_cd": normalized_stock_code,
            "ord_qty": ord_qty,
            "order_type_code": order_type_code,
            "dmst_stex_tp": dmst_stex_tp,
            "ord_uv": ord_uv,
            "cond_uv": cond_uv,
        },
        result_key="sell_order_result",
        success_message="Live stock sell order request submitted",
        exception_message="Stock sell order endpoint not yet implemented or failed to connect",
    )


async def modify_stock_order(
    client: KiwoomClient,
    orig_ord_no: str,
    stk_cd: str,
    mdfy_qty: str,
    mdfy_uv: str,
    dmst_stex_tp: str = "KRX",
    mdfy_cond_uv: str = "",
) -> dict[str, Any]:
    """Submit a live stock modify order to Kiwoom."""

    normalized_stock_code = _normalize_stock_code(stk_cd)
    request_data = {
        "orig_ord_no": orig_ord_no,
        "stk_cd": normalized_stock_code,
        "mdfy_qty": mdfy_qty,
        "mdfy_uv": mdfy_uv,
        "dmst_stex_tp": dmst_stex_tp,
    }
    if mdfy_cond_uv:
        request_data["mdfy_cond_uv"] = mdfy_cond_uv

    return await _submit_order(
        client,
        api_info=ORDER_APIS.modify_order,
        request_data=request_data,
        context={
            "orig_ord_no": orig_ord_no,
            "stk_cd": normalized_stock_code,
            "mdfy_qty": mdfy_qty,
            "mdfy_uv": mdfy_uv,
            "dmst_stex_tp": dmst_stex_tp,
            "mdfy_cond_uv": mdfy_cond_uv,
        },
        result_key="modify_order_result",
        success_message="Live stock modify order request submitted",
        exception_message="Stock modify order endpoint not yet implemented or failed to connect",
    )


async def cancel_stock_order(
    client: KiwoomClient,
    orig_ord_no: str,
    stk_cd: str,
    cncl_qty: str,
    dmst_stex_tp: str = "KRX",
) -> dict[str, Any]:
    """Submit a live stock cancel order to Kiwoom."""

    normalized_stock_code = _normalize_stock_code(stk_cd)
    return await _submit_order(
        client,
        api_info=ORDER_APIS.cancel_order,
        request_data={
            "orig_ord_no": orig_ord_no,
            "stk_cd": normalized_stock_code,
            "cncl_qty": cncl_qty,
            "dmst_stex_tp": dmst_stex_tp,
        },
        context={
            "orig_ord_no": orig_ord_no,
            "stk_cd": normalized_stock_code,
            "cncl_qty": cncl_qty,
            "dmst_stex_tp": dmst_stex_tp,
        },
        result_key="cancel_order_result",
        success_message="Live stock cancel order request submitted",
        exception_message="Stock cancel order endpoint not yet implemented or failed to connect",
    )


__all__ = [
    "place_stock_buy_order",
    "place_stock_sell_order",
    "modify_stock_order",
    "cancel_stock_order",
]
