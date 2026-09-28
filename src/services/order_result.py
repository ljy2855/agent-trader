"""Structured outcome of applying a trading decision.

``order.py`` hands back raw Kiwoom response dicts whose ``success`` flag only
means "the request produced a clean business response". That is *not* a fill,
and on a transport error it does not even separate "we never reached the
broker" from "the broker may have booked the order and we lost the answer".
Every apply path therefore returns an ``OrderApplyResult`` instead of ``None``
or a bare dict, so the status registry, Discord, the operations digest and the
order-intent ledger that follows all read the same vocabulary.

State vocabulary (P1-1 / P1-4 of ``docs/ops/system-evaluation-2026-07-26.md``):

``informational``
    The decision intentionally maps to no order — ``HOLD``, ``REJECT``, or a
    portfolio-level ACTION the watcher only records. Nothing was attempted.
``skipped``
    An order *would* have gone out but a gate stopped it: ``execute_orders``
    off, missing quantity, per-stock budget exhausted, ``max_positions``
    reached. Nothing was attempted.
``submitted``
    The broker accepted the request. **Not a fill.** Kiwoom answers
    ``return_code=0`` the moment an order is booked; the execution shows up
    later on a separate query.
``unknown``
    The request left us but we never learned whether the broker booked it —
    read timeout, connection reset mid-response, 5xx, unparseable body. Treat
    it as *possible* exposure: never resubmit off this state, resolve it
    against the open-order / execution APIs first.
``failed``
    The broker rejected the request, or it never reached the broker at all.
``filled``
    Execution confirmed against the account. Nothing here produces it yet —
    the reconciliation ledger will. It exists so no caller is tempted to
    reuse ``submitted`` to mean a fill.

``success`` is deliberately narrow: it is true only when an order actually
reached the broker (``submitted``/``filled``). A ``HOLD`` did not "succeed" —
it never had an order to succeed with, and ``attempted=False`` says so. Any
caller that reads ``if result.success`` gets "an order went out", which is the
fail-safe reading.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import httpx

ORDER_STATE_INFORMATIONAL = "informational"
ORDER_STATE_SKIPPED = "skipped"
ORDER_STATE_SUBMITTED = "submitted"
ORDER_STATE_UNKNOWN = "unknown"
ORDER_STATE_FAILED = "failed"
ORDER_STATE_FILLED = "filled"

ORDER_STATES = frozenset(
    {
        ORDER_STATE_INFORMATIONAL,
        ORDER_STATE_SKIPPED,
        ORDER_STATE_SUBMITTED,
        ORDER_STATE_UNKNOWN,
        ORDER_STATE_FAILED,
        ORDER_STATE_FILLED,
    }
)

# States meaning "the broker may be holding an order for us". Exposure
# tracking (the position gates today, the intent ledger next) must count
# ``unknown`` alongside ``submitted``: assuming a timed-out order never landed
# is exactly how the same stock gets bought twice.
EXPOSURE_STATES = frozenset(
    {ORDER_STATE_SUBMITTED, ORDER_STATE_UNKNOWN, ORDER_STATE_FILLED}
)

# state -> (attempted, submitted, filled, success)
_STATE_FLAGS: dict[str, tuple[bool, bool, bool, bool]] = {
    ORDER_STATE_INFORMATIONAL: (False, False, False, False),
    ORDER_STATE_SKIPPED: (False, False, False, False),
    ORDER_STATE_SUBMITTED: (True, True, False, True),
    ORDER_STATE_FILLED: (True, True, True, True),
    ORDER_STATE_UNKNOWN: (True, False, False, False),
    ORDER_STATE_FAILED: (True, False, False, False),
}

# Keys that have carried a broker order number. The kt10000/kt10001 response
# schema in ``kiwoom_api_spec.md`` documents only ``dmst_stex_tp``, and
# kt10002/kt10003 only ``base_orig_ord_no`` — so an order number is
# best-effort here, never assumed. See the module note in ``order.py``.
_ORDER_NO_KEYS = ("ord_no", "order_no", "odr_no", "base_orig_ord_no")

# ``order.py`` nests the raw Kiwoom body under an API-specific key.
_NESTED_RESULT_KEYS = (
    "buy_order_result",
    "sell_order_result",
    "modify_order_result",
    "cancel_order_result",
)


def normalize_order_no(value: Any) -> str | None:
    """Return a comparable broker order number, or ``None`` when absent.

    Kiwoom returns order numbers as strings, sometimes zero-padded and
    sometimes not, and uses an all-zero string as "no order number". Later
    reconciliation compares numbers coming from the order API against ones
    from the open-order/execution APIs, so both sides need the same shape:
    digit-only values drop their leading zeroes.
    """

    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.isdigit():
        stripped = text.lstrip("0")
        return stripped or None
    return text


def extract_order_no(payload: Any) -> str | None:
    """Best-effort pull of the broker order number out of an order response.

    Accepts either the raw Kiwoom body or the wrapper dict ``order.py``
    builds (which nests the body under ``*_order_result``).
    """

    if not isinstance(payload, dict):
        return None
    for key in _ORDER_NO_KEYS:
        order_no = normalize_order_no(payload.get(key))
        if order_no:
            return order_no
    for key in _NESTED_RESULT_KEYS:
        nested = payload.get(key)
        if isinstance(nested, dict):
            for inner in _ORDER_NO_KEYS:
                order_no = normalize_order_no(nested.get(inner))
                if order_no:
                    return order_no
    return None


def classify_transport_error(error: BaseException) -> str:
    """Decide whether a failed order request could still have been booked.

    This distinction is the entire point of the ``unknown`` state. A connect
    timeout never reached Kiwoom, so the order definitively does not exist. A
    *read* timeout means the request was already on the wire — the broker may
    well have booked it and only the answer was lost. Resubmitting the second
    case is how an account ends up long twice.

    Anything we cannot positively prove never reached the broker classifies as
    ``unknown``. The cost of a false ``unknown`` is one blocked new entry until
    the caller resolves it; the cost of a false ``failed`` is a duplicate live
    order.
    """

    if isinstance(error, httpx.HTTPStatusError):
        status = getattr(getattr(error, "response", None), "status_code", None)
        # 5xx: the broker received the request. Whether it booked the order
        # before failing is unknowable from this side.
        if isinstance(status, int) and status >= 500:
            return ORDER_STATE_UNKNOWN
        # 4xx (including the 429 we give up on) is an explicit rejection.
        return ORDER_STATE_FAILED
    # Connection never established -> the request was never delivered.
    # Checked before the broader NetworkError/TransportError families below,
    # which these subclass.
    if isinstance(
        error,
        (
            httpx.ConnectError,
            httpx.ConnectTimeout,
            httpx.ProxyError,
            httpx.UnsupportedProtocol,
            httpx.InvalidURL,
        ),
    ):
        return ORDER_STATE_FAILED
    return ORDER_STATE_UNKNOWN


def _coerce_return_code(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


@dataclass(slots=True)
class OrderApplyResult:
    """What actually happened when a decision was applied.

    Flags are derived from ``state`` so they can never disagree — build one
    through :meth:`for_state`, :meth:`informational`, :meth:`skipped` or
    :meth:`from_order_response` rather than setting fields by hand.
    """

    action: str
    attempted: bool = False
    submitted: bool = False
    filled: bool = False
    success: bool = False
    state: str = ORDER_STATE_INFORMATIONAL
    order_no: str | None = None
    return_code: int | None = None
    reason: str | None = None

    # -- constructors ---------------------------------------------------------

    @classmethod
    def for_state(
        cls,
        state: str,
        *,
        action: str,
        order_no: str | None = None,
        return_code: int | None = None,
        reason: str | None = None,
    ) -> "OrderApplyResult":
        if state not in _STATE_FLAGS:
            raise ValueError(f"unknown order state: {state!r}")
        attempted, submitted, filled, success = _STATE_FLAGS[state]
        return cls(
            action=action,
            attempted=attempted,
            submitted=submitted,
            filled=filled,
            success=success,
            state=state,
            order_no=order_no,
            return_code=return_code,
            reason=reason,
        )

    @classmethod
    def informational(cls, action: str, reason: str | None = None) -> "OrderApplyResult":
        """A decision that maps to no order by design (HOLD, REJECT, ...)."""

        return cls.for_state(
            ORDER_STATE_INFORMATIONAL, action=action, reason=reason
        )

    @classmethod
    def skipped(cls, action: str, reason: str) -> "OrderApplyResult":
        """A gate stopped an order that would otherwise have been placed."""

        return cls.for_state(ORDER_STATE_SKIPPED, action=action, reason=reason)

    @classmethod
    def from_order_response(
        cls,
        action: str,
        response: Any,
        *,
        reason: str | None = None,
    ) -> "OrderApplyResult":
        """Classify a normalized ``order.py`` response dict.

        ``success=True`` on the wrapper means the broker *accepted the
        request* — that maps to ``submitted``, never to a fill. A rejection is
        ``failed``, and a transport error is whatever
        :func:`classify_transport_error` recorded on the way out.
        """

        if not isinstance(response, dict):
            # Our own wrapper misbehaved; we cannot show the order never
            # landed, so fail closed.
            return cls.for_state(
                ORDER_STATE_UNKNOWN,
                action=action,
                reason=reason or "주문 API가 dict 응답을 반환하지 않음",
            )

        order_no = extract_order_no(response)
        return_code = _coerce_return_code(response.get("return_code"))
        message = (
            response.get("return_msg")
            or response.get("error")
            or response.get("message")
        )

        if response.get("success"):
            state = ORDER_STATE_SUBMITTED
        elif response.get("transport_state") == ORDER_STATE_UNKNOWN:
            state = ORDER_STATE_UNKNOWN
        else:
            state = ORDER_STATE_FAILED

        return cls.for_state(
            state,
            action=action,
            order_no=order_no,
            return_code=return_code,
            reason=reason or (str(message) if message else None),
        )

    # -- helpers --------------------------------------------------------------

    @property
    def counts_as_exposure(self) -> bool:
        """True when the broker may be holding an order because of this apply."""

        return self.state in EXPOSURE_STATES

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


__all__ = [
    "EXPOSURE_STATES",
    "ORDER_STATES",
    "ORDER_STATE_FAILED",
    "ORDER_STATE_FILLED",
    "ORDER_STATE_INFORMATIONAL",
    "ORDER_STATE_SKIPPED",
    "ORDER_STATE_SUBMITTED",
    "ORDER_STATE_UNKNOWN",
    "OrderApplyResult",
    "classify_transport_error",
    "extract_order_no",
    "normalize_order_no",
]
