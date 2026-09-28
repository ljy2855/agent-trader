"""Kiwoom realtime 주문체결(00) → broker rows the ledger already understands.

Why this exists
---------------
Order state reaches us only by polling ka10075/ka10076 today, and polling has
a blind spot the ledger cannot close on its own: an order that fills between
two ticks is never *open*, so it appears in neither view at the moment we
look. On 2026-08-26 an immediately-filled buy sat at ``SUBMITTED`` for a full
session and emitted 708 unresolved-intent warnings. The realtime stream
pushes the transition instead, including the rejection reason (FID 919) that
would have named the 308003 outage on 2026-08-31 as it happened.

What it deliberately is not
---------------------------
Not a replacement for the polled reconciliation. A socket can drop, and every
event delivered while it was down is simply gone -- the stream carries no
replay. REST stays the source of truth and keeps running on its own schedule;
this only lets the ledger hear about a transition sooner. That is why the
translation targets the existing ``reconcile()`` row contract rather than
introducing a second path into the state machine: one matcher, one set of
ownership rules, one place where a mistake can be made.

Splitting the pure translation out from the socket is what makes the
protocol testable without a broker.
"""

from __future__ import annotations

from typing import Any

# Realtime type code for 주문체결 (order/execution). Kiwoom's realtime types
# are two characters, unrelated to the ka*/kt* REST ids.
REALTIME_TYPE_ORDER_EXECUTION = "00"

# FID -> the ka10075/ka10076 field carrying the same fact. Only the fields
# reconciliation actually reads are mapped; everything else on the wire is
# ignored rather than guessed at.
#
# Verified against the response tables in Kiwoom's published spec (see
# src/constants/vendor/README.md) -- both queries expose exactly these names.
_FID_TO_ROW_FIELD = {
    "9203": "ord_no",     # 주문번호
    "9001": "stk_cd",     # 종목코드
    "913": "ord_stt",     # 주문상태
    "900": "ord_qty",     # 주문수량
    "901": "ord_pric",    # 주문가격
    "902": "oso_qty",     # 미체결수량
    "911": "cntr_qty",    # 체결량
    "905": "io_tp_nm",    # 주문구분 ("+매수" / "현금매도") -- row_side reads this
    "908": "ord_tm",      # 주문/체결시간 (HHMMSS) -- parse_broker_time reads this
}

# 919 거부사유. Not part of the row: rejection is not a ledger state that
# reconciliation infers from a broker view, and inventing a field the REST
# rows never carry would put the two paths out of step. Surfaced separately so
# an operator hears about it.
_FID_REJECT_REASON = "919"

# Values 919 carries when there is nothing to report. Kiwoom sends "0" rather
# than an empty string on a perfectly good fill, so presence alone is not
# rejection -- reading it that way alerted four times on two orders that both
# filled (2026-09-02). The spec documents no sentinel, so this is what the
# live feed was observed to send.
_NO_REJECTION_SENTINELS = {"", "0"}

# 913 주문상태. Spec-documented values: 접수, 체결, 확인, 취소, 거부.
_FID_ORDER_STATUS = "913"
_STATUS_REJECTED = "거부"


def is_order_execution_message(message: Any) -> bool:
    """True for a REAL frame carrying at least one 주문체결 entry."""

    if not isinstance(message, dict):
        return False
    if str(message.get("trnm", "")).upper() != "REAL":
        return False
    data = message.get("data")
    if not isinstance(data, list):
        return False
    return any(
        isinstance(entry, dict)
        and str(entry.get("type", "")) == REALTIME_TYPE_ORDER_EXECUTION
        for entry in data
    )


def row_from_values(values: Any) -> dict[str, Any] | None:
    """Translate one entry's FID ``values`` into a broker row.

    ``None`` when the entry carries no order number: reconciliation can match
    an unnumbered row only by identity and timing, and those rules were
    written for a same-day REST query. Feeding a numberless realtime frame
    through them would widen that matcher with a case it was never designed
    for, so it is dropped and the polled path handles the order instead.
    """

    if not isinstance(values, dict):
        return None
    row: dict[str, Any] = {}
    for fid, field in _FID_TO_ROW_FIELD.items():
        if fid in values:
            text = str(values[fid]).strip()
            if text:
                row[field] = text
    if not row.get("ord_no"):
        return None
    return row


def rejection_from_values(values: Any) -> str | None:
    """The broker's stated reason for refusing an order, when it refused one.

    Two independent signals have to agree, because neither is sufficient on
    its own. 주문상태(913) names 거부 as one of its five states, which is the
    authoritative fact; 919 carries the text but is populated as ``"0"`` on
    ordinary fills, so treating any value there as a rejection raises an
    alarm on every successful order -- as it did four times on 2026-09-02
    for two orders that both filled.

    Returning the reason for a 거부 whose 919 is a sentinel still beats
    silence: the operator needs to know the order was refused even when the
    broker declines to say why.
    """

    if not isinstance(values, dict):
        return None
    if str(values.get(_FID_ORDER_STATUS, "")).strip() != _STATUS_REJECTED:
        return None
    reason = str(values.get(_FID_REJECT_REASON, "")).strip()
    if reason in _NO_REJECTION_SENTINELS:
        return "사유 미상"
    return reason


def extract_order_rows(message: Any) -> list[dict[str, Any]]:
    """Every 주문체결 entry in a REAL frame, as broker rows."""

    if not is_order_execution_message(message):
        return []
    rows: list[dict[str, Any]] = []
    for entry in message.get("data") or []:
        if not isinstance(entry, dict):
            continue
        if str(entry.get("type", "")) != REALTIME_TYPE_ORDER_EXECUTION:
            continue
        row = row_from_values(entry.get("values"))
        if row is not None:
            rows.append(row)
    return rows


def extract_rejections(message: Any) -> list[tuple[str, str]]:
    """``(order_no_or_code, reason)`` for entries the broker refused."""

    if not is_order_execution_message(message):
        return []
    out: list[tuple[str, str]] = []
    for entry in message.get("data") or []:
        if not isinstance(entry, dict):
            continue
        if str(entry.get("type", "")) != REALTIME_TYPE_ORDER_EXECUTION:
            continue
        values = entry.get("values")
        reason = rejection_from_values(values)
        if not reason:
            continue
        ident = ""
        if isinstance(values, dict):
            ident = str(values.get("9203") or values.get("9001") or "").strip()
        out.append((ident or "?", reason))
    return out


def build_login_packet(token: str) -> dict[str, Any]:
    """The first frame on a new socket; the server acks with ``trnm=LOGIN``."""

    return {"trnm": "LOGIN", "token": token}


def build_register_packet(*, group_no: str = "1") -> dict[str, Any]:
    """Subscribe to 주문체결.

    ``item`` is empty because this type is account-scoped rather than
    per-symbol -- it reports every order on the authenticated account.
    ``refresh="1"`` keeps any existing registration rather than replacing it.
    """

    return {
        "trnm": "REG",
        "grp_no": group_no,
        "refresh": "1",
        "data": [{"item": [""], "type": [REALTIME_TYPE_ORDER_EXECUTION]}],
    }


def is_ping(message: Any) -> bool:
    """Kiwoom's keepalive. The server expects the same frame echoed back."""

    if isinstance(message, str):
        return message.strip().upper() == "PING"
    return isinstance(message, dict) and str(message.get("trnm", "")).upper() == "PING"


def login_error(message: Any) -> tuple[int, str] | None:
    """``(return_code, return_msg)`` when a LOGIN ack reports failure."""

    if not isinstance(message, dict):
        return None
    if str(message.get("trnm", "")).upper() != "LOGIN":
        return None
    raw = message.get("return_code")
    try:
        code = int(str(raw).strip())
    except (TypeError, ValueError):
        code = 0 if raw in (None, "") else -1
    if code == 0:
        return None
    return code, str(message.get("return_msg") or "unknown error")
