"""Tests for Kiwoom live order service wrappers."""

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

order_module = importlib.import_module("src.services.order")
order_result_module = importlib.import_module("src.services.order_result")

OrderApplyResult = order_result_module.OrderApplyResult
classify_transport_error = order_result_module.classify_transport_error
extract_order_no = order_result_module.extract_order_no
normalize_order_no = order_result_module.normalize_order_no


class DummyResponse:
    """Simple response stub for order service tests."""

    def __init__(self, payload: Any, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code
        self.headers: dict[str, str] = {}

    def json(self) -> Any:
        return self._payload


class DummyClient:
    """Client stub that records outbound POST calls."""

    def __init__(self, payload: Any):
        self._payload = payload
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
        return DummyResponse(self._payload)


class RetryClient:
    """Client stub that fails once with 429 before succeeding."""

    def __init__(self, payload: Any):
        self._payload = payload
        self.calls: list[dict[str, Any]] = []
        self._attempt = 0

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
        self._attempt += 1
        if self._attempt == 1:
            request = httpx.Request("POST", "https://example.test/order")
            response = httpx.Response(429, request=request)
            raise httpx.HTTPStatusError("rate limited", request=request, response=response)
        return DummyResponse(self._payload)


def test_buy_order_uses_kt10000_contract() -> None:
    """Buy orders should map to the live kt10000 request schema."""

    client = DummyClient({"dmst_stex_tp": "KRX"})

    result = asyncio.run(
        order_module.place_stock_buy_order(
            client,
            stk_cd="005930",
            ord_qty="1",
            order_type_code="0",
            ord_uv="70000",
        )
    )

    assert result["success"] is True
    assert client.calls[0]["headers"]["api-id"] == "kt10000"
    assert client.calls[0]["json"] == {
        "stk_cd": "005930",
        "ord_qty": "1",
        "trde_tp": "0",
        "dmst_stex_tp": "KRX",
        "ord_uv": "70000",
    }


def test_sell_order_normalizes_account_style_stock_code() -> None:
    """Order submission should strip the leading account-style A prefix."""

    client = DummyClient({"return_code": 0, "return_msg": "ok"})

    result = asyncio.run(
        order_module.place_stock_sell_order(
            client,
            stk_cd="A005930",
            ord_qty="2",
            order_type_code="0",
            ord_uv="70000",
        )
    )

    assert result["success"] is True
    assert client.calls[0]["json"]["stk_cd"] == "005930"
    assert result["stk_cd"] == "005930"


def test_sell_order_strips_A_prefix_from_alphanumeric_ticker() -> None:
    """Specialty tickers (SPACs, M-class etc.) embed letters but still need
    the leading A prefix stripped before order submission.

    Regression for SWO-180 (2026-04-28): 메쥬 ticker A0088M0 was rejected
    by Kiwoom order API with "1902 종목 정보가 없습니다" because the prior
    normalize guard required all-digit suffix.
    """

    client = DummyClient({"return_code": 0, "return_msg": "ok"})

    result = asyncio.run(
        order_module.place_stock_sell_order(
            client,
            stk_cd="A0088M0",
            ord_qty="1",
            order_type_code="3",
            ord_uv="",
        )
    )

    assert result["success"] is True
    assert client.calls[0]["json"]["stk_cd"] == "0088M0"
    assert result["stk_cd"] == "0088M0"


def test_sell_order_retries_once_after_429_rate_limit() -> None:
    """Transient 429s should be retried before reporting failure."""

    client = RetryClient({"return_code": 0, "return_msg": "ok"})

    result = asyncio.run(
        order_module.place_stock_sell_order(
            client,
            stk_cd="005930",
            ord_qty="2",
            order_type_code="3",
        )
    )

    assert result["success"] is True
    assert len(client.calls) == 2


def test_cancel_order_business_error_is_reported() -> None:
    """Business errors from live order endpoints should not be reported as success."""

    client = DummyClient(
        {
            "return_code": 2,
            "return_msg": "입력 값 오류입니다.",
        }
    )

    result = asyncio.run(
        order_module.cancel_stock_order(
            client,
            orig_ord_no="1234567",
            stk_cd="005930",
            cncl_qty="0",
        )
    )

    assert result["success"] is False
    assert result["return_code"] == 2
    assert result["message"] == "입력 값 오류입니다."
    assert result["cancel_order_result"]["return_msg"] == "입력 값 오류입니다."
    assert client.calls[0]["json"]["dmst_stex_tp"] == "KRX"


# -- transport classification (P1-4) --------------------------------------
#
# `success=False` alone cannot tell "the broker rejected this" from "the
# request went out and we lost the answer". Only the first is safe to retry,
# so every exception path stamps a `transport_state`.


class RaisingClient:
    """Client stub whose POST always raises the supplied exception."""

    def __init__(self, error: BaseException):
        self._error = error
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
        self.calls.append({"path": path, "json": json})
        raise self._error


class UnparsableResponse(DummyResponse):
    """The broker answered, but the body is not JSON we can read."""

    def json(self) -> Any:
        raise ValueError("Expecting value: line 1 column 1 (char 0)")


class UnparsableClient(DummyClient):
    async def post(self, path: str, **kwargs: Any) -> DummyResponse:
        self.calls.append({"path": path, **kwargs})
        return UnparsableResponse(None)


def _http_status_error(status: int) -> httpx.HTTPStatusError:
    request = httpx.Request("POST", "https://example.test/order")
    response = httpx.Response(status, request=request)
    return httpx.HTTPStatusError(f"status {status}", request=request, response=response)


def test_read_timeout_is_unknown_not_failed() -> None:
    """A read timeout means the order may already be booked at the broker."""

    client = RaisingClient(httpx.ReadTimeout("timed out"))

    result = asyncio.run(
        order_module.place_stock_buy_order(
            client, stk_cd="005930", ord_qty="1", order_type_code="3"
        )
    )

    assert result["success"] is False
    assert result["transport_state"] == "unknown"
    applied = OrderApplyResult.from_order_response("TIER1", result)
    assert applied.state == "unknown"
    assert applied.attempted is True
    assert applied.submitted is False
    assert applied.success is False
    assert applied.counts_as_exposure is True


def test_connect_error_is_failed_not_unknown() -> None:
    """The connection never opened, so the order definitively does not exist."""

    client = RaisingClient(httpx.ConnectError("connection refused"))

    result = asyncio.run(
        order_module.place_stock_buy_order(
            client, stk_cd="005930", ord_qty="1", order_type_code="3"
        )
    )

    assert result["transport_state"] == "failed"
    applied = OrderApplyResult.from_order_response("TIER1", result)
    assert applied.state == "failed"
    assert applied.counts_as_exposure is False


def test_server_error_is_unknown() -> None:
    client = RaisingClient(_http_status_error(503))

    result = asyncio.run(
        order_module.place_stock_sell_order(
            client, stk_cd="005930", ord_qty="1", order_type_code="3"
        )
    )

    assert result["transport_state"] == "unknown"


def test_client_error_is_failed() -> None:
    client = RaisingClient(_http_status_error(400))

    result = asyncio.run(
        order_module.place_stock_sell_order(
            client, stk_cd="005930", ord_qty="1", order_type_code="3"
        )
    )

    assert result["transport_state"] == "failed"


def test_exhausted_429_retries_are_failed() -> None:
    """Giving up after repeated rate limits is a rejection, not a lost answer."""

    client = RaisingClient(_http_status_error(429))

    result = asyncio.run(
        order_module.place_stock_sell_order(
            client, stk_cd="005930", ord_qty="1", order_type_code="3"
        )
    )

    assert result["transport_state"] == "failed"
    assert len(client.calls) == 3  # two retries then give up


def test_unreadable_response_body_is_unknown() -> None:
    """The broker answered — we just can't tell what it said."""

    client = UnparsableClient(None)

    result = asyncio.run(
        order_module.place_stock_buy_order(
            client, stk_cd="005930", ord_qty="1", order_type_code="3"
        )
    )

    assert result["transport_state"] == "unknown"


def test_parseable_non_object_response_is_unknown_not_submitted() -> None:
    """Valid JSON without a business object cannot prove broker acceptance."""

    client = DummyClient(["unexpected", "response"])

    result = asyncio.run(
        order_module.place_stock_buy_order(
            client, stk_cd="005930", ord_qty="1", order_type_code="3"
        )
    )

    assert result["success"] is False
    assert result["transport_state"] == "unknown"
    applied = OrderApplyResult.from_order_response("TIER1", result)
    assert applied.state == "unknown"
    assert applied.counts_as_exposure is True


def test_classify_transport_error_prefers_specific_connect_failures() -> None:
    # ConnectTimeout subclasses TimeoutException; ConnectError subclasses
    # NetworkError. Both must classify as `failed`, not fall through to the
    # conservative `unknown` default for their parent families.
    assert classify_transport_error(httpx.ConnectTimeout("x")) == "failed"
    assert classify_transport_error(httpx.ConnectError("x")) == "failed"
    assert classify_transport_error(httpx.ReadTimeout("x")) == "unknown"
    assert classify_transport_error(httpx.RemoteProtocolError("x")) == "unknown"
    # Anything we cannot prove never reached the broker stays conservative.
    assert classify_transport_error(RuntimeError("boom")) == "unknown"


# -- order number normalization (P1-4) ------------------------------------


def test_normalize_order_no_strips_padding_and_placeholders() -> None:
    assert normalize_order_no("0001234") == "1234"
    assert normalize_order_no("1234") == "1234"
    assert normalize_order_no(" 42 ") == "42"
    assert normalize_order_no(1234) == "1234"
    assert normalize_order_no("0000000") is None  # placeholder, not an order
    assert normalize_order_no("") is None
    assert normalize_order_no(None) is None


def test_extract_order_no_reads_nested_order_payload() -> None:
    assert extract_order_no({"ord_no": "0000055"}) == "55"
    assert extract_order_no({"buy_order_result": {"ord_no": "55"}}) == "55"
    assert extract_order_no({"cancel_order_result": {"base_orig_ord_no": "7"}}) == "7"
    assert extract_order_no({"dmst_stex_tp": "KRX"}) is None
    assert extract_order_no(None) is None


def test_order_response_surfaces_order_no_when_broker_sends_one() -> None:
    client = DummyClient({"return_code": 0, "return_msg": "ok", "ord_no": "0000123"})

    result = asyncio.run(
        order_module.place_stock_buy_order(
            client, stk_cd="005930", ord_qty="1", order_type_code="3"
        )
    )

    assert result["order_no"] == "123"


def test_order_response_omits_order_no_when_broker_sends_none() -> None:
    """kt10000's documented response body carries no order number at all."""

    client = DummyClient({"dmst_stex_tp": "KRX"})

    result = asyncio.run(
        order_module.place_stock_buy_order(
            client, stk_cd="005930", ord_qty="1", order_type_code="3"
        )
    )

    assert "order_no" not in result
    applied = OrderApplyResult.from_order_response("TIER1", result)
    assert applied.state == "submitted"
    assert applied.order_no is None


# -- OrderApplyResult model ------------------------------------------------


def test_accepted_request_is_submitted_never_filled() -> None:
    result = OrderApplyResult.from_order_response(
        "TIER1", {"success": True, "return_code": 0, "return_msg": "정상처리"}
    )

    assert result.state == "submitted"
    assert result.submitted is True
    assert result.filled is False  # a booking is not an execution
    assert result.success is True
    assert result.return_code == 0


def test_business_rejection_is_failed() -> None:
    result = OrderApplyResult.from_order_response(
        "CUT_LOSS",
        {"success": False, "return_code": 1902, "return_msg": "종목 정보가 없습니다"},
    )

    assert result.state == "failed"
    assert result.attempted is True
    assert result.submitted is False
    assert result.success is False
    assert result.return_code == 1902
    assert result.reason == "종목 정보가 없습니다"


def test_non_dict_response_fails_closed_to_unknown() -> None:
    """If our own wrapper misbehaves we cannot prove the order never landed."""

    result = OrderApplyResult.from_order_response("TIER1", None)

    assert result.state == "unknown"
    assert result.counts_as_exposure is True


def test_no_op_results_are_not_attempted() -> None:
    informational = OrderApplyResult.informational("HOLD", "HOLD — 주문 없음")
    skipped = OrderApplyResult.skipped("TIER1", "예산 소진")

    for result in (informational, skipped):
        assert result.attempted is False
        assert result.submitted is False
        assert result.filled is False
        assert result.success is False
        assert result.counts_as_exposure is False


def test_state_flags_stay_consistent_across_the_vocabulary() -> None:
    """Flags are derived from `state`, so they can never contradict it."""

    for state in order_result_module.ORDER_STATES:
        result = OrderApplyResult.for_state(state, action="X")
        assert result.state == state
        assert result.success == (state in ("submitted", "filled"))
        assert result.submitted == (state in ("submitted", "filled"))
        assert result.attempted == (
            state in ("submitted", "filled", "unknown", "failed")
        )
        assert result.filled == (state == "filled")
        # `filled` implies `submitted`; nothing can fill without being booked.
        assert not (result.filled and not result.submitted)

    try:
        OrderApplyResult.for_state("executed", action="X")
    except ValueError:
        pass
    else:  # pragma: no cover - the retired vocabulary must stay retired
        raise AssertionError("`executed` must not be a valid order state")
