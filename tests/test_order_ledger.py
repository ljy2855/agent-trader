"""Tests for the persistent order-intent ledger (P0-2).

The failure these guard against is duplicate live orders: a crash between
"decided to buy" and "sent the buy", or a transport timeout that hides
whether the broker booked anything. Every test below is one of those
sequences replayed against a real SQLite file.
"""

from __future__ import annotations

import hashlib
import os
import sqlite3
import sys
import threading
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

os.environ.setdefault("KIWOOM_APPKEY", "dummy-appkey")
os.environ.setdefault("KIWOOM_SECRETKEY", "dummy-secretkey")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402

from src.services.order_ledger import (  # noqa: E402
    KST,
    STORAGE_LOCAL,
    STORAGE_NETWORK,
    STORAGE_UNKNOWN,
    SIDE_BUY,
    SIDE_SELL,
    STATE_CANCELLED,
    STATE_FILLED,
    STATE_INTENDED,
    STATE_OPEN,
    STATE_PARTIAL,
    STATE_REJECTED,
    STATE_RELEASED,
    STATE_SUBMITTED,
    STATE_UNKNOWN,
    REGISTRATION_CREATED,
    REGISTRATION_EXISTING_OPEN,
    REGISTRATION_TERMINAL,
    IntentRegistration,
    OrderLedger,
    OrderLedgerError,
    UnsafeLedgerStorageError,
    classify_ledger_storage,
    make_attempt_id,
    make_decision_key,
    normalize_order_no,
    open_buy_quantity,
    open_sell_quantity,
    parse_linux_mountinfo,
    row_side,
)


def _at(hour: int = 10, minute: int = 0) -> datetime:
    return datetime(2026, 7, 27, hour, minute, tzinfo=KST)


def _ledger(tmp_path: Path) -> OrderLedger:
    return OrderLedger(tmp_path / "order_ledger.sqlite3")


def _mountinfo_row(
    mount_point: str,
    fs_type: str,
    *,
    source: str = "/dev/test",
    mount_id: int = 36,
) -> str:
    return (
        f"{mount_id} 25 0:32 / {mount_point} rw,relatime - "
        f"{fs_type} {source} rw\n"
    )


def _open_row(**over):
    """A broker row as it actually arrives — timestamp included.

    `ord_tmd` is derived from the wall clock rather than hard-coded so the
    row is never accidentally *earlier* than the intent the test creates,
    which the matcher would (correctly) refuse.
    """

    row = {
        "ord_no": "0000123",
        "stk_cd": "005930",
        "io_tp_nm": "매수",
        "ord_qty": "10",
        "ord_pric": "70000",
        "cntr_qty": "0",
        "oso_qty": "10",
        "ord_stt": "접수",
        "ord_tmd": datetime.now(KST).strftime("%Y%m%d%H%M%S"),
    }
    row.update(over)
    return row


def _new_intent(ledger, **kw):
    """Register a decision and return the freshly created attempt row."""

    reg = ledger.record_intent(**kw)
    assert reg.may_submit, f"expected a new attempt, got {reg.outcome}"
    return reg.intent


# -- intent identity -------------------------------------------------------


def test_same_decision_in_one_bucket_is_one_intent():
    kwargs = dict(
        trading_day="2026-07-27",
        stock_code="005930",
        side=SIDE_BUY,
        quantity=10,
        price=70000,
    )
    assert make_decision_key(**kwargs, now=_at(10, 0)) == make_decision_key(
        **kwargs, now=_at(10, 0)
    )


def test_different_decisions_get_different_intents():
    base = dict(
        trading_day="2026-07-27",
        stock_code="005930",
        side=SIDE_BUY,
        quantity=10,
        price=70000,
        now=_at(10, 0),
    )
    first = make_decision_key(**base)
    assert make_decision_key(**{**base, "quantity": 11}) != first
    assert make_decision_key(**{**base, "side": SIDE_SELL}) != first
    assert make_decision_key(**{**base, "stock_code": "000660"}) != first
    assert make_decision_key(**{**base, "trading_day": "2026-07-28"}) != first
    # A later bucket is a genuinely new decision.
    assert make_decision_key(**{**base, "now": _at(10, 5)}) != first


def test_replaying_a_decision_does_not_open_a_second_attempt(tmp_path):
    ledger = _ledger(tmp_path)
    first = ledger.record_intent(
        stock_code="005930", side=SIDE_BUY, quantity=10, price=70000
    )
    second = ledger.record_intent(
        stock_code="005930", side=SIDE_BUY, quantity=10, price=70000
    )

    assert first.may_submit is True
    assert second.may_submit is False  # caller must not submit again
    assert second.outcome == REGISTRATION_EXISTING_OPEN
    assert second.intent.intent_id == first.intent.intent_id
    assert len(ledger.unresolved()) == 1


def test_normalize_order_no_and_row_side():
    assert normalize_order_no("0000123") == "123"
    assert normalize_order_no("0") is None
    assert normalize_order_no(None) is None
    assert row_side({"io_tp_nm": "+매수"}) == SIDE_BUY
    assert row_side({"io_tp_nm": "현금매도"}) == SIDE_SELL
    assert row_side({"io_tp_nm": "무엇"}) is None


# -- crash before submit ---------------------------------------------------


def test_crash_before_submit_leaves_an_intended_row_that_blocks(tmp_path):
    """The old code left no trace at all here — restart just re-bought."""

    path = tmp_path / "order_ledger.sqlite3"
    first = OrderLedger(path)
    first.record_intent(
        stock_code="005930", side=SIDE_BUY, quantity=10, price=70000
    )
    first.close()  # process dies before the API call

    restarted = OrderLedger(path)
    pending = restarted.unresolved(stock_code="005930", side=SIDE_BUY)

    assert [i.state for i in pending] == [STATE_INTENDED]
    assert restarted.has_unresolved("005930", SIDE_BUY) is True


def test_crash_before_submit_resolves_when_the_order_did_land(tmp_path):
    """No order number to match on, so it falls back to a conservative match."""

    path = tmp_path / "order_ledger.sqlite3"
    first = OrderLedger(path)
    intent = _new_intent(first,
        stock_code="005930", side=SIDE_BUY, quantity=10, price=70000
    )
    first.close()

    restarted = OrderLedger(path)
    report = restarted.reconcile(open_orders=[_open_row()])

    assert report.adopted_order_no == 1
    row = restarted.get(intent.intent_id)
    assert row.state == STATE_OPEN
    assert row.order_no == "123"


def test_unmatchable_intent_stays_blocking(tmp_path):
    """The deliberate failure mode: we could not prove it did NOT land."""

    ledger = _ledger(tmp_path)
    intent = _new_intent(ledger,
        stock_code="005930", side=SIDE_BUY, quantity=10, price=70000
    )

    report = ledger.reconcile(open_orders=[], executions=[])

    assert report.still_unresolved == 1
    assert intent.intent_id in report.unmatched
    assert ledger.has_unresolved("005930", SIDE_BUY) is True


def test_conservative_match_requires_quantity_and_side_to_agree(tmp_path):
    ledger = _ledger(tmp_path)
    ledger.record_intent(
        stock_code="005930", side=SIDE_BUY, quantity=10, price=70000
    )

    ledger.reconcile(
        open_orders=[
            _open_row(ord_qty="7"),  # wrong quantity
            _open_row(io_tp_nm="매도"),  # wrong side
            _open_row(stk_cd="000660"),  # wrong stock
            _open_row(ord_pric="65000"),  # wrong price
        ]
    )

    assert ledger.has_unresolved("005930", SIDE_BUY) is True


# -- broker accepted, response lost ----------------------------------------


def test_lost_response_is_unknown_and_keeps_blocking(tmp_path):
    ledger = _ledger(tmp_path)
    intent = _new_intent(ledger,
        stock_code="005930", side=SIDE_BUY, quantity=10, price=70000
    )

    state = ledger.apply_order_result(
        intent.intent_id,
        submitted=False,
        unknown=True,
        order_no=None,
        reason="ReadTimeout",
    )

    assert state == STATE_UNKNOWN
    assert ledger.has_unresolved("005930", SIDE_BUY) is True


def test_lost_response_resolves_once_the_order_shows_up(tmp_path):
    """The broker HAD booked it. Reconciliation adopts the order number."""

    ledger = _ledger(tmp_path)
    intent = _new_intent(ledger,
        stock_code="005930", side=SIDE_BUY, quantity=10, price=70000
    )
    ledger.apply_order_result(
        intent.intent_id, submitted=False, unknown=True, order_no=None, reason="timeout"
    )

    ledger.reconcile(
        executions=[
            _open_row(cntr_qty="10", oso_qty="0", ord_stt="체결")
        ]
    )

    row = ledger.get(intent.intent_id)
    assert row.state == STATE_FILLED
    assert row.order_no == "123"
    assert ledger.unresolved() == []


def test_lost_response_survives_a_restart_as_unknown(tmp_path):
    path = tmp_path / "order_ledger.sqlite3"
    first = OrderLedger(path)
    intent = _new_intent(first,
        stock_code="005930", side=SIDE_BUY, quantity=10, price=70000
    )
    first.apply_order_result(
        intent.intent_id, submitted=False, unknown=True, order_no=None, reason="timeout"
    )
    first.close()

    restarted = OrderLedger(path)
    assert restarted.get(intent.intent_id).state == STATE_UNKNOWN
    assert restarted.has_unresolved("005930", SIDE_BUY) is True


def test_submitted_intent_survives_a_restart(tmp_path):
    path = tmp_path / "order_ledger.sqlite3"
    first = OrderLedger(path)
    intent = _new_intent(first,
        stock_code="005930", side=SIDE_BUY, quantity=10, price=70000
    )
    first.apply_order_result(
        intent.intent_id, submitted=True, unknown=False, order_no="0000123", reason="ok"
    )
    first.close()

    restarted = OrderLedger(path)
    row = restarted.get(intent.intent_id)
    assert row.state == STATE_SUBMITTED
    assert row.order_no == "123"
    assert restarted.has_unresolved("005930", SIDE_BUY) is True


# -- partial fills ---------------------------------------------------------


def test_partial_fill_is_tracked_and_stays_unresolved(tmp_path):
    ledger = _ledger(tmp_path)
    intent = _new_intent(ledger,
        stock_code="005930", side=SIDE_BUY, quantity=10, price=70000
    )
    ledger.apply_order_result(
        intent.intent_id, submitted=True, unknown=False, order_no="123", reason="ok"
    )

    ledger.reconcile(open_orders=[_open_row(cntr_qty="4", oso_qty="6")])

    row = ledger.get(intent.intent_id)
    assert row.state == STATE_PARTIAL
    assert row.filled_quantity == 4
    assert row.remaining_quantity == 6
    # Only the unfilled remainder still counts as committed budget.
    assert ledger.unresolved_notional("005930") == 6 * 70000


def test_partial_then_complete_fill_resolves(tmp_path):
    ledger = _ledger(tmp_path)
    intent = _new_intent(ledger,
        stock_code="005930", side=SIDE_BUY, quantity=10, price=70000
    )
    ledger.apply_order_result(
        intent.intent_id, submitted=True, unknown=False, order_no="123", reason="ok"
    )
    ledger.reconcile(open_orders=[_open_row(cntr_qty="4", oso_qty="6")])
    ledger.reconcile(
        executions=[_open_row(cntr_qty="10", oso_qty="0", ord_stt="체결")]
    )

    assert ledger.get(intent.intent_id).state == STATE_FILLED
    assert ledger.unresolved() == []


def test_cancelled_and_rejected_rows_are_terminal(tmp_path):
    ledger = _ledger(tmp_path)
    cancelled = _new_intent(ledger,
        stock_code="005930", side=SIDE_BUY, quantity=10, price=70000
    )
    ledger.apply_order_result(
        cancelled.intent_id, submitted=True, unknown=False, order_no="123", reason="ok"
    )
    ledger.reconcile(open_orders=[_open_row(ord_stt="취소확인", oso_qty="0")])
    assert ledger.get(cancelled.intent_id).state == STATE_CANCELLED

    rejected = _new_intent(ledger,
        stock_code="000660", side=SIDE_BUY, quantity=5, price=100, now=_at(11)
    )
    ledger.apply_order_result(
        rejected.intent_id,
        submitted=True,
        unknown=False,
        order_no="999",
        reason="ok",
    )
    ledger.reconcile(
        open_orders=[
            # Stamped on the intent's own trading day — a broker row from a
            # different session can no longer bind to it (7-digit order
            # numbers are a daily sequence).
            _row_at(
                _dt(11, 0, 5), ord_no="999", stk_cd="000660", ord_qty="5",
                ord_stt="거부",
            )
        ]
    )
    assert ledger.get(rejected.intent_id).state == STATE_REJECTED
    assert ledger.unresolved() == []


# -- rejected orders may be retried ----------------------------------------


def test_rejected_order_releases_the_slot(tmp_path):
    """A rejection is proof the broker holds nothing, so retrying is safe."""

    ledger = _ledger(tmp_path)
    intent = _new_intent(ledger,
        stock_code="005930", side=SIDE_BUY, quantity=10, price=70000
    )

    state = ledger.apply_order_result(
        intent.intent_id,
        submitted=False,
        unknown=False,
        order_no=None,
        reason="종목 정보가 없습니다",
    )

    assert state == STATE_REJECTED
    assert ledger.has_unresolved("005930", SIDE_BUY) is False
    assert ledger.unresolved_notional("005930") == 0


# -- oversell protection ---------------------------------------------------


def test_open_sell_quantity_counts_only_working_sells():
    rows = [
        {"stk_cd": "005930", "io_tp_nm": "매도", "ord_qty": "10", "oso_qty": "6"},
        {"stk_cd": "005930", "io_tp_nm": "매수", "ord_qty": "5", "oso_qty": "5"},
        {"stk_cd": "000660", "io_tp_nm": "매도", "ord_qty": "3", "oso_qty": "3"},
    ]

    assert open_sell_quantity(rows, "005930") == 6
    assert open_sell_quantity(rows, "A005930") == 6  # account-style prefix
    assert open_sell_quantity(rows, "000660") == 3
    assert open_sell_quantity(rows, "123456") == 0


def test_open_sell_quantity_assumes_the_whole_order_when_remaining_is_absent():
    rows = [{"stk_cd": "005930", "io_tp_nm": "매도", "ord_qty": "10"}]

    assert open_sell_quantity(rows, "005930") == 10


def test_unresolved_sell_quantity_tracks_our_own_exits(tmp_path):
    ledger = _ledger(tmp_path)
    intent = _new_intent(ledger,
        stock_code="005930", side=SIDE_SELL, quantity=10, price=None
    )
    ledger.apply_order_result(
        intent.intent_id, submitted=True, unknown=False, order_no="123", reason="ok"
    )

    assert ledger.unresolved_sell_quantity("005930") == 10

    ledger.reconcile(
        open_orders=[_open_row(io_tp_nm="매도", cntr_qty="4", oso_qty="6")]
    )
    assert ledger.unresolved_sell_quantity("005930") == 6


# -- bounded UNKNOWN protective-sell release -------------------------------


def _unknown_sell(ledger, *, at, code="005930", qty=10):
    intent = _new_intent(
        ledger,
        stock_code=code,
        side=SIDE_SELL,
        quantity=qty,
        price=None,
        now=at,
    )
    ledger.apply_order_result(
        intent.intent_id,
        submitted=False,
        unknown=True,
        order_no=None,
        reason="ReadTimeout",
        now=at,
    )
    return intent


def test_unknown_sell_releases_only_after_grace_and_three_spaced_absences(tmp_path):
    ledger = _ledger(tmp_path)
    started = _dt(10)
    intent = _unknown_sell(ledger, at=started)

    # Before the 120-second grace: a complete empty pair is not evidence yet.
    ledger.reconcile(
        open_orders=[],
        executions=[],
        broker_views_complete=True,
        now=started + timedelta(seconds=119),
    )
    assert ledger.get(intent.intent_id).absence_observation_count == 0

    first = started + timedelta(seconds=120)
    ledger.reconcile(
        open_orders=[],
        executions=[],
        broker_views_complete=True,
        now=first,
    )
    # A too-soon poll cannot manufacture another independent observation.
    ledger.reconcile(
        open_orders=[],
        executions=[],
        broker_views_complete=True,
        now=first + timedelta(seconds=29),
    )
    assert ledger.get(intent.intent_id).absence_observation_count == 1

    ledger.reconcile(
        open_orders=[],
        executions=[],
        broker_views_complete=True,
        now=first + timedelta(seconds=30),
    )
    report = ledger.reconcile(
        open_orders=[],
        executions=[],
        broker_views_complete=True,
        now=first + timedelta(seconds=60),
    )

    row = ledger.get(intent.intent_id)
    assert row.state == STATE_RELEASED
    assert row.absence_observation_count == 3
    assert row.absence_first_observed_at == first.isoformat()
    assert row.absence_last_observed_at == (first + timedelta(seconds=60)).isoformat()
    assert row.released_at == row.absence_last_observed_at
    assert "broker non-acceptance is not proven" in (row.reason or "")
    assert ledger.unresolved_sell_quantity("005930") == 0
    assert report.released == 1
    assert report.resolved == 1
    assert [e["event_type"] for e in ledger.audit_events(intent.intent_id)] == [
        "RELEASED",
        "ABSENCE_OBSERVED",
        "ABSENCE_OBSERVED",
    ]


def test_complete_absence_never_releases_an_unknown_buy(tmp_path):
    ledger = _ledger(tmp_path)
    started = _dt(10)
    intent = _unknown_intent(
        ledger, at=started, side=SIDE_BUY, price=70000
    )

    for seconds in (120, 150, 180, 600):
        ledger.reconcile(
            open_orders=[],
            executions=[],
            broker_views_complete=True,
            now=started + timedelta(seconds=seconds),
        )

    row = ledger.get(intent.intent_id)
    assert row.state == STATE_UNKNOWN
    assert row.absence_observation_count == 0
    assert ledger.has_unresolved("005930", SIDE_BUY) is True
    assert ledger.audit_events(intent.intent_id) == []
    with pytest.raises(ValueError, match="protective-sell"):
        ledger.mark_state(intent.intent_id, STATE_RELEASED)


def test_incomplete_view_resets_the_unknown_sell_absence_streak(tmp_path):
    ledger = _ledger(tmp_path)
    started = _dt(10)
    intent = _unknown_sell(ledger, at=started)

    for seconds in (120, 150):
        ledger.reconcile(
            open_orders=[],
            executions=[],
            broker_views_complete=True,
            now=started + timedelta(seconds=seconds),
        )
    assert ledger.get(intent.intent_id).absence_observation_count == 2

    report = ledger.reconcile(
        open_orders=[],
        executions=[],
        broker_views_complete=False,
        now=started + timedelta(seconds=180),
    )

    row = ledger.get(intent.intent_id)
    assert row.state == STATE_UNKNOWN
    assert row.absence_observation_count == 0
    assert row.absence_first_observed_at is None
    assert row.absence_last_observed_at is None
    assert report.absence_resets == 1
    event = ledger.audit_events(intent.intent_id)[0]
    assert event["event_type"] == "ABSENCE_RESET"
    assert event["observation_count"] == 2
    assert "incomplete" in event["reason"]

    # The next clean view starts over at one; it is not the third observation.
    ledger.reconcile(
        open_orders=[],
        executions=[],
        broker_views_complete=True,
        now=started + timedelta(seconds=210),
    )
    assert ledger.get(intent.intent_id).absence_observation_count == 1


def test_eventual_broker_presence_prevents_release_and_tracks_partial_fill(tmp_path):
    ledger = _ledger(tmp_path)
    started = _dt(10)
    intent = _unknown_sell(ledger, at=started)
    for seconds in (120, 150):
        ledger.reconcile(
            open_orders=[],
            executions=[],
            broker_views_complete=True,
            now=started + timedelta(seconds=seconds),
        )

    # The response was merely delayed: on the next view the order appears,
    # already partially filled. It must win over the local absence policy.
    row = _row_at(
        started + timedelta(seconds=175),
        io_tp_nm="매도",
        cntr_qty="4",
        oso_qty="6",
    )
    report = ledger.reconcile(
        open_orders=[row],
        executions=[],
        broker_views_complete=True,
        now=started + timedelta(seconds=180),
    )

    reconciled = ledger.get(intent.intent_id)
    assert reconciled.state == STATE_PARTIAL
    assert reconciled.filled_quantity == 4
    assert reconciled.remaining_quantity == 6
    assert ledger.unresolved_sell_quantity("005930") == 6
    assert report.released == 0
    assert report.absence_resets == 1
    assert ledger.audit_events(intent.intent_id)[0]["event_type"] == "ABSENCE_RESET"


def test_unmatchable_broker_row_resets_absence_instead_of_looking_absent(tmp_path):
    """No timestamp means no adoption, but it is still not a clean absence."""

    ledger = _ledger(tmp_path)
    started = _dt(10)
    intent = _unknown_sell(ledger, at=started)
    for seconds in (120, 150):
        ledger.reconcile(
            open_orders=[],
            executions=[],
            broker_views_complete=True,
            now=started + timedelta(seconds=seconds),
        )

    untimed = _open_row(io_tp_nm="매도")
    untimed.pop("ord_tmd")
    report = ledger.reconcile(
        open_orders=[untimed],
        executions=[],
        broker_views_complete=True,
        now=started + timedelta(seconds=180),
    )

    row = ledger.get(intent.intent_id)
    assert row.state == STATE_UNKNOWN  # never guessed OPEN from an untimed row
    assert row.absence_observation_count == 0  # but never called it absent
    assert report.released == 0
    assert report.absence_resets == 1


def test_unknown_sell_absence_streak_survives_restart(tmp_path):
    path = tmp_path / "order_ledger.sqlite3"
    started = _dt(10)
    first = OrderLedger(path)
    intent = _unknown_sell(first, at=started)
    for seconds in (120, 150):
        first.reconcile(
            open_orders=[],
            executions=[],
            broker_views_complete=True,
            now=started + timedelta(seconds=seconds),
        )
    first.close()

    restarted = OrderLedger(path)
    before = restarted.get(intent.intent_id)
    assert before.absence_observation_count == 2
    report = restarted.reconcile(
        open_orders=[],
        executions=[],
        broker_views_complete=True,
        now=started + timedelta(seconds=180),
    )

    assert report.released == 1
    assert restarted.get(intent.intent_id).state == STATE_RELEASED
    assert len(restarted.audit_events(intent.intent_id)) == 3


def test_released_sell_allows_a_new_attempt_without_rewriting_audit(tmp_path):
    started = _dt(10)
    ledger = OrderLedger(
        tmp_path / "order_ledger.sqlite3", bucket_seconds=3600
    )
    intent = _unknown_sell(ledger, at=started)
    for seconds in (120, 150, 180):
        ledger.reconcile(
            open_orders=[],
            executions=[],
            broker_views_complete=True,
            now=started + timedelta(seconds=seconds),
        )
    released_before = ledger.get(intent.intent_id).to_dict()

    retry = ledger.record_intent(
        stock_code="005930",
        side=SIDE_SELL,
        quantity=10,
        price=None,
        now=started + timedelta(seconds=180),
    )

    assert retry.may_submit is True
    assert retry.intent.attempt == 2
    assert retry.intent.intent_id != intent.intent_id
    assert ledger.get(intent.intent_id).to_dict() == released_before


# -- exposure accounting (the `_placed_orders` replacement) ----------------


def test_unresolved_codes_and_notional_feed_the_position_gates(tmp_path):
    ledger = _ledger(tmp_path)
    ledger.record_intent(
        stock_code="005930", side=SIDE_BUY, quantity=10, price=70000
    )
    ledger.record_intent(
        stock_code="000660", side=SIDE_BUY, quantity=5, price=100_000, now=_at(11)
    )

    assert ledger.unresolved_codes(SIDE_BUY) == {"005930", "000660"}
    assert ledger.unresolved_notional("005930") == 700_000
    assert ledger.unresolved_notional("000660") == 500_000


def test_exposure_survives_a_restart(tmp_path):
    """The whole point: the old in-memory dict evaporated with the process."""

    path = tmp_path / "order_ledger.sqlite3"
    first = OrderLedger(path)
    intent = _new_intent(first,
        stock_code="005930", side=SIDE_BUY, quantity=10, price=70000
    )
    first.apply_order_result(
        intent.intent_id, submitted=True, unknown=False, order_no="123", reason="ok"
    )
    first.close()

    restarted = OrderLedger(path)
    assert restarted.unresolved_codes(SIDE_BUY) == {"005930"}
    assert restarted.unresolved_notional("005930") == 700_000


# -- storage faults --------------------------------------------------------


def test_mountinfo_parser_decodes_escaped_paths_and_sources():
    mounts = parse_linux_mountinfo(
        _mountinfo_row(
            r"/srv/order\040ledger",
            "nfs4",
            source=r"server:/exports/order\040ledger",
        )
    )

    assert len(mounts) == 1
    assert mounts[0].mount_point == Path("/srv/order ledger")
    assert mounts[0].source == "server:/exports/order ledger"
    safety = classify_ledger_storage(
        "/srv/order ledger/current/order_ledger.sqlite3",
        _mountinfo_row(r"/srv/order\040ledger", "nfs4"),
    )
    assert safety.state == STORAGE_NETWORK


def test_storage_classification_uses_longest_mount_prefix():
    mountinfo = (
        _mountinfo_row("/", "ext4", mount_id=1)
        + _mountinfo_row("/srv", "nfs4", source="server:/srv", mount_id=2)
        + _mountinfo_row(
            "/srv/local-ledger", "xfs", source="/dev/nvme0n1", mount_id=3
        )
    )

    assert (
        classify_ledger_storage("/srv/shared/ledger.sqlite3", mountinfo).state
        == STORAGE_NETWORK
    )
    local = classify_ledger_storage(
        "/srv/local-ledger/ledger.sqlite3", mountinfo
    )
    assert local.state == STORAGE_LOCAL
    assert local.mount_point == "/srv/local-ledger"


@pytest.mark.parametrize(
    "fs_type",
    ["nfs", "nfs4", "cifs", "smbfs", "sshfs", "fuse.sshfs"],
)
def test_known_network_filesystems_are_blocked(fs_type):
    safety = classify_ledger_storage(
        "/ledger/order_ledger.sqlite3",
        _mountinfo_row("/ledger", fs_type, source="server:/ledger"),
    )

    assert safety.state == STORAGE_NETWORK
    assert safety.blocks_new_entries is True


def test_confirmed_network_storage_refuses_before_opening_database(tmp_path):
    path = tmp_path / "remote" / "order_ledger.sqlite3"
    mountinfo = _mountinfo_row(
        str(tmp_path / "remote"),
        "nfs4",
        source="server:/ledger",
    )

    with pytest.raises(UnsafeLedgerStorageError) as caught:
        OrderLedger(path, mountinfo_reader=lambda: mountinfo)

    assert caught.value.safety.state == STORAGE_NETWORK
    assert "WAL+synchronous=FULL" in str(caught.value)
    assert not path.exists()


def test_unreadable_mount_metadata_does_not_block_local_development(tmp_path):
    def unreadable() -> str:
        raise PermissionError("mountinfo denied")

    ledger = OrderLedger(
        tmp_path / "order_ledger.sqlite3",
        mountinfo_reader=unreadable,
    )

    assert ledger.storage_safety.state == STORAGE_UNKNOWN
    assert ledger.storage_safety.metadata_available is False
    assert ledger._conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
    assert ledger._conn.execute("PRAGMA synchronous").fetchone()[0] == 2
    ledger.close()


def test_unclassified_filesystem_is_visible_but_not_blocking(tmp_path):
    path = tmp_path / "order_ledger.sqlite3"
    mountinfo = _mountinfo_row(str(tmp_path), "futurefs")

    ledger = OrderLedger(path, mountinfo_reader=lambda: mountinfo)

    assert ledger.storage_safety.state == STORAGE_UNKNOWN
    assert ledger.storage_safety.blocks_new_entries is False
    assert path.exists()
    ledger.close()


def test_unopenable_ledger_raises(tmp_path):
    # A directory where the database file should be.
    blocked = tmp_path / "order_ledger.sqlite3"
    blocked.mkdir()

    with pytest.raises(OrderLedgerError):
        OrderLedger(blocked)


def test_corrupt_database_raises_on_read(tmp_path):
    path = tmp_path / "order_ledger.sqlite3"
    ledger = _ledger(tmp_path)
    ledger.record_intent(
        stock_code="005930", side=SIDE_BUY, quantity=1, price=1000
    )
    ledger.close()
    path.write_bytes(b"this is not a sqlite database at all" * 20)

    with pytest.raises(OrderLedgerError):
        OrderLedger(path).unresolved()


def test_closed_ledger_raises_rather_than_silently_allowing(tmp_path):
    ledger = _ledger(tmp_path)
    ledger.close()

    with pytest.raises(OrderLedgerError):
        ledger.unresolved()
    with pytest.raises(OrderLedgerError):
        ledger.record_intent(
            stock_code="005930", side=SIDE_BUY, quantity=1, price=1000
        )


class _FailingConnection:
    """Stands in for a connection whose disk has gone away mid-session."""

    def execute(self, *args, **kwargs):
        raise sqlite3.OperationalError("disk I/O error")

    def commit(self):  # pragma: no cover - never reached
        raise sqlite3.OperationalError("disk I/O error")


def test_write_failure_raises(tmp_path):
    ledger = _ledger(tmp_path)
    ledger._conn = _FailingConnection()  # type: ignore[assignment]

    with pytest.raises(OrderLedgerError):
        ledger.record_intent(
            stock_code="005930", side=SIDE_BUY, quantity=1, price=1000
        )
    with pytest.raises(OrderLedgerError):
        ledger.unresolved()


# -- reconciliation bookkeeping --------------------------------------------


def test_reconcile_does_not_steal_another_intents_order(tmp_path):
    """A numbered intent's row must not be adopted by an unnumbered one."""

    ledger = _ledger(tmp_path)
    numbered = _new_intent(ledger,
        stock_code="005930", side=SIDE_BUY, quantity=10, price=70000
    )
    ledger.apply_order_result(
        numbered.intent_id, submitted=True, unknown=False, order_no="123", reason="ok"
    )
    unnumbered = _new_intent(ledger,
        stock_code="005930",
        side=SIDE_BUY,
        quantity=10,
        price=70000,
        now=_at(11),
    )

    ledger.reconcile(open_orders=[_open_row()])

    assert ledger.get(numbered.intent_id).state == STATE_OPEN
    # The only broker row was already claimed, so this one stays blocking.
    assert ledger.get(unnumbered.intent_id).state == STATE_INTENDED


def test_reconcile_report_counts(tmp_path):
    ledger = _ledger(tmp_path)
    filled = _new_intent(ledger,
        stock_code="005930", side=SIDE_BUY, quantity=10, price=70000
    )
    ledger.apply_order_result(
        filled.intent_id, submitted=True, unknown=False, order_no="123", reason="ok"
    )
    ledger.record_intent(
        stock_code="000660", side=SIDE_BUY, quantity=5, price=100, now=_at(11)
    )

    report = ledger.reconcile(
        executions=[_open_row(cntr_qty="10", oso_qty="0", ord_stt="체결")]
    )

    assert report.checked == 2
    assert report.resolved == 1
    assert report.still_unresolved == 1


def test_reconcile_is_a_no_op_without_pending_intents(tmp_path):
    ledger = _ledger(tmp_path)

    report = ledger.reconcile(open_orders=[_open_row()])

    assert report.to_dict() == {
        "checked": 0,
        "resolved": 0,
        "still_unresolved": 0,
        "adopted_order_no": 0,
        "released": 0,
        "absence_observed": 0,
        "absence_resets": 0,
        "unmatched": [],
        "ambiguous": [],
    }


# -- broker-only open buys (second Task 4 review correction) ---------------


def test_open_buy_quantity_mirrors_the_sell_side():
    rows = [
        {"stk_cd": "005930", "io_tp_nm": "매수", "ord_qty": "10", "oso_qty": "6"},
        {"stk_cd": "005930", "io_tp_nm": "매도", "ord_qty": "4", "oso_qty": "4"},
        {"stk_cd": "000660", "io_tp_nm": "+매수", "ord_qty": "3", "oso_qty": "3"},
    ]

    assert open_buy_quantity(rows, "005930") == 6
    assert open_buy_quantity(rows, "A005930") == 6  # account-style prefix
    assert open_buy_quantity(rows, "000660") == 3
    assert open_buy_quantity(rows, "123456") == 0
    # The two sides stay independent.
    assert open_sell_quantity(rows, "005930") == 4


def test_open_buy_quantity_ignores_fully_filled_rows():
    rows = [{"stk_cd": "005930", "io_tp_nm": "매수", "ord_qty": "10", "oso_qty": "0"}]

    assert open_buy_quantity(rows, "005930") == 0


def test_open_buy_quantity_can_count_unclassifiable_rows():
    """The buy gate opts in: a working row we cannot read might be a buy."""

    rows = [{"stk_cd": "005930", "ord_qty": "10", "oso_qty": "7"}]

    assert open_buy_quantity(rows, "005930") == 0  # strict by default
    assert open_buy_quantity(rows, "005930", include_unclassified=True) == 7
    # A readable sell is still a sell, even with the flag on.
    sell_rows = [{"stk_cd": "005930", "io_tp_nm": "매도", "ord_qty": "9", "oso_qty": "9"}]
    assert open_buy_quantity(sell_rows, "005930", include_unclassified=True) == 0


def test_open_buy_quantity_assumes_the_whole_order_when_remaining_is_absent():
    rows = [{"stk_cd": "005930", "io_tp_nm": "매수", "ord_qty": "10"}]

    assert open_buy_quantity(rows, "005930") == 10


# -- unnumbered matching must be time-aware -------------------------------
#
# Identity (code/side/qty/price) is not an order's fingerprint: a 09:00 fill
# and a 14:00 lost-response intent for the same stock and size are
# indistinguishable by identity alone. Adopting the former marked the latter
# FILLED off somebody else's trade and released the duplicate-order block.


def _dt(h, m=0, s=0) -> datetime:
    return datetime(2026, 7, 27, h, m, s, tzinfo=KST)


def _row_at(when: datetime, **over):
    """A broker row stamped with a full YYYYMMDDHHMMSS time."""

    return _open_row(ord_tmd=when.strftime("%Y%m%d%H%M%S"), **over)


def _unknown_intent(ledger, *, at, code="005930", qty=10, price=70000, side=SIDE_BUY):
    intent = _new_intent(ledger,
        stock_code=code, side=side, quantity=qty, price=price, now=at
    )
    ledger.apply_order_result(
        intent.intent_id, submitted=False, unknown=True, order_no=None,
        reason="ReadTimeout", now=at,
    )
    return intent


def test_earlier_fill_does_not_settle_a_later_unknown_intent(tmp_path):
    """THE regression: 09:00 execution, 14:00 UNKNOWN, identical identity."""

    ledger = _ledger(tmp_path)
    intent = _unknown_intent(ledger, at=_dt(14))

    report = ledger.reconcile(
        executions=[_row_at(_dt(9), cntr_qty="10", oso_qty="0", ord_stt="체결")],
        now=_dt(14, 0, 5),
    )

    row = ledger.get(intent.intent_id)
    assert row.state == STATE_UNKNOWN  # NOT filled
    assert row.order_no is None  # the morning order was not adopted
    assert report.adopted_order_no == 0
    assert intent.intent_id in report.unmatched
    # ...and it therefore keeps blocking new buys.
    assert ledger.has_unresolved("005930", SIDE_BUY) is True


def test_a_later_event_does_match(tmp_path):
    """The guard must not break the case it exists to protect."""

    ledger = _ledger(tmp_path)
    intent = _unknown_intent(ledger, at=_dt(14))

    ledger.reconcile(
        executions=[_row_at(_dt(14, 0, 3), cntr_qty="10", oso_qty="0", ord_stt="체결")],
        now=_dt(14, 1),
    )

    row = ledger.get(intent.intent_id)
    assert row.state == STATE_FILLED
    assert row.order_no == "123"


def test_a_slightly_backdated_event_still_matches(tmp_path):
    """Second-granularity broker clocks and modest skew must not block."""

    ledger = _ledger(tmp_path)
    intent = _unknown_intent(ledger, at=_dt(14, 0, 30))

    ledger.reconcile(
        executions=[_row_at(_dt(14, 0, 25), cntr_qty="10", oso_qty="0", ord_stt="체결")],
        now=_dt(14, 1),
    )

    assert ledger.get(intent.intent_id).state == STATE_FILLED


def test_an_event_from_another_trading_day_does_not_match(tmp_path):
    ledger = _ledger(tmp_path)
    intent = _unknown_intent(ledger, at=_dt(14))

    ledger.reconcile(
        executions=[
            _open_row(
                ord_tmd=datetime(2026, 7, 28, 14, 0, tzinfo=KST).strftime("%Y%m%d%H%M%S"),
                cntr_qty="10", oso_qty="0", ord_stt="체결",
            )
        ],
        now=_dt(14, 1),
    )

    assert ledger.get(intent.intent_id).state == STATE_UNKNOWN


def test_a_row_without_a_timestamp_does_not_match(tmp_path):
    """No time, no match — we cannot place it relative to the intent."""

    ledger = _ledger(tmp_path)
    intent = _unknown_intent(ledger, at=_dt(14))
    row = _open_row(cntr_qty="10", oso_qty="0", ord_stt="체결")
    row.pop("ord_tmd")

    report = ledger.reconcile(executions=[row], now=_dt(14, 1))

    assert ledger.get(intent.intent_id).state == STATE_UNKNOWN
    assert report.adopted_order_no == 0


def test_an_unparseable_timestamp_does_not_match(tmp_path):
    ledger = _ledger(tmp_path)
    intent = _unknown_intent(ledger, at=_dt(14))

    ledger.reconcile(
        executions=[
            _open_row(ord_tmd="", tm="정오쯤", cntr_qty="10", oso_qty="0", ord_stt="체결")
        ],
        now=_dt(14, 1),
    )

    assert ledger.get(intent.intent_id).state == STATE_UNKNOWN


def test_an_intended_row_without_a_timestamp_stays_intended(tmp_path):
    """Crash-before-submit path gets the same treatment as UNKNOWN."""

    ledger = _ledger(tmp_path)
    intent = _new_intent(ledger,
        stock_code="005930", side=SIDE_BUY, quantity=10, price=70000, now=_dt(14)
    )
    row = _open_row()
    row.pop("ord_tmd")

    ledger.reconcile(open_orders=[row], now=_dt(14, 1))

    assert ledger.get(intent.intent_id).state == STATE_INTENDED
    assert ledger.has_unresolved("005930", SIDE_BUY) is True


# -- ambiguity -------------------------------------------------------------


def test_two_plausible_candidates_leave_the_intent_unresolved(tmp_path):
    """Never pick arbitrarily between two orders that both fit."""

    ledger = _ledger(tmp_path)
    intent = _unknown_intent(ledger, at=_dt(14))

    report = ledger.reconcile(
        open_orders=[
            _row_at(_dt(14, 0, 2), ord_no="900"),
            _row_at(_dt(14, 0, 4), ord_no="901"),
        ],
        now=_dt(14, 1),
    )

    row = ledger.get(intent.intent_id)
    assert row.state == STATE_UNKNOWN
    assert row.order_no is None
    assert intent.intent_id in report.ambiguous
    assert report.adopted_order_no == 0
    assert ledger.has_unresolved("005930", SIDE_BUY) is True


def test_ambiguity_resolves_once_only_one_candidate_remains(tmp_path):
    """A clearer later view settles it; ambiguity is not a latch."""

    ledger = _ledger(tmp_path)
    intent = _unknown_intent(ledger, at=_dt(14))
    ledger.reconcile(
        open_orders=[
            _row_at(_dt(14, 0, 2), ord_no="900"),
            _row_at(_dt(14, 0, 4), ord_no="901"),
        ],
        now=_dt(14, 1),
    )
    assert ledger.get(intent.intent_id).state == STATE_UNKNOWN

    # One of them turns out to belong elsewhere / is gone from the view.
    ledger.reconcile(
        open_orders=[_row_at(_dt(14, 0, 2), ord_no="900")], now=_dt(14, 2)
    )

    row = ledger.get(intent.intent_id)
    assert row.state == STATE_OPEN
    assert row.order_no == "900"


def test_one_order_in_both_views_is_not_two_candidates(tmp_path):
    """The same broker order routinely appears in open-orders AND executions."""

    ledger = _ledger(tmp_path)
    intent = _unknown_intent(ledger, at=_dt(14))

    report = ledger.reconcile(
        open_orders=[_row_at(_dt(14, 0, 2), ord_no="900", cntr_qty="4", oso_qty="6")],
        executions=[
            _row_at(_dt(14, 0, 2), ord_no="900", cntr_qty="10", oso_qty="0",
                    ord_stt="체결")
        ],
        now=_dt(14, 1),
    )

    assert report.ambiguous == []
    row = ledger.get(intent.intent_id)
    assert row.state == STATE_FILLED  # the more advanced view won
    assert row.filled_quantity == 10


def test_duplicate_views_merge_regardless_of_argument_order(tmp_path):
    """A settled order must not regress to OPEN because of list ordering."""

    ledger = _ledger(tmp_path)
    intent = _unknown_intent(ledger, at=_dt(14))

    ledger.reconcile(
        # Deliberately reversed: the *filled* view arrives as `open_orders`.
        open_orders=[
            _row_at(_dt(14, 0, 2), ord_no="900", cntr_qty="10", oso_qty="0",
                    ord_stt="체결")
        ],
        executions=[_row_at(_dt(14, 0, 2), ord_no="900", cntr_qty="4", oso_qty="6")],
        now=_dt(14, 1),
    )

    assert ledger.get(intent.intent_id).state == STATE_FILLED


# -- order-number ownership across the whole ledger ------------------------


def test_a_terminal_rows_order_number_cannot_be_reused(tmp_path):
    """Claimed numbers used to be collected from unresolved rows only, so a
    settled FILLED row's number was fair game — and the thief inherited its
    fill."""

    ledger = _ledger(tmp_path)
    settled = _new_intent(ledger,
        stock_code="005930", side=SIDE_BUY, quantity=10, price=70000, now=_dt(9)
    )
    ledger.apply_order_result(
        settled.intent_id, submitted=True, unknown=False, order_no="123",
        reason="ok", now=_dt(9),
    )
    ledger.reconcile(
        executions=[_row_at(_dt(9, 0, 5), cntr_qty="10", oso_qty="0", ord_stt="체결")],
        now=_dt(9, 1),
    )
    assert ledger.get(settled.intent_id).state == STATE_FILLED

    # A later, identical-looking intent must not adopt order 123.
    later = _unknown_intent(ledger, at=_dt(14))
    report = ledger.reconcile(
        executions=[_row_at(_dt(14, 0, 2), cntr_qty="10", oso_qty="0", ord_stt="체결")],
        now=_dt(14, 1),
    )

    row = ledger.get(later.intent_id)
    assert row.state == STATE_UNKNOWN
    assert row.order_no is None
    assert report.adopted_order_no == 0
    assert ledger.claimed_order_numbers() == {"123"}


def test_claimed_order_numbers_includes_every_state(tmp_path):
    ledger = _ledger(tmp_path)
    for i, (no, submitted) in enumerate([("11", True), ("22", False)]):
        intent = _new_intent(ledger,
            stock_code="00593%d" % i, side=SIDE_BUY, quantity=1, price=10,
            now=_dt(9 + i),
        )
        ledger.apply_order_result(
            intent.intent_id, submitted=submitted, unknown=False, order_no=no,
            reason="x", now=_dt(9 + i),
        )

    # One SUBMITTED (unresolved) and one REJECTED (terminal) — both own theirs.
    assert ledger.claimed_order_numbers() == {"11", "22"}


def test_a_numbered_intent_still_reconciles_against_its_own_order(tmp_path):
    """Ownership must not lock an intent out of its own broker row."""

    ledger = _ledger(tmp_path)
    intent = _new_intent(ledger,
        stock_code="005930", side=SIDE_BUY, quantity=10, price=70000, now=_dt(14)
    )
    ledger.apply_order_result(
        intent.intent_id, submitted=True, unknown=False, order_no="123",
        reason="ok", now=_dt(14),
    )

    ledger.reconcile(
        executions=[_row_at(_dt(14, 0, 3), cntr_qty="10", oso_qty="0", ord_stt="체결")],
        now=_dt(14, 1),
    )

    assert ledger.get(intent.intent_id).state == STATE_FILLED


# -- timestamp normalization ----------------------------------------------


def test_parse_broker_time_accepts_the_documented_encodings():
    from src.services.order_ledger import parse_broker_time

    day = date(2026, 7, 27)
    # `ord_tmd` carries its own date and outranks everything.
    at, d = parse_broker_time({"ord_tmd": "20260728093015"}, reference_day=day)
    assert (at.hour, at.minute, at.second) == (9, 30, 15)
    assert d == date(2026, 7, 28)
    # ka10076 주문시간 / ka10075 시간 are time-of-day, dated to the query day.
    for key in ("ord_tm", "tm", "cntr_tm"):
        at, d = parse_broker_time({key: "093015"}, reference_day=day)
        assert (at.hour, at.minute, at.second, d) == (9, 30, 15, day), key
    at, d = parse_broker_time({"tm": "09:30:15"}, reference_day=day)
    assert (at.hour, at.minute, d) == (9, 30, day)
    at, d = parse_broker_time({"tm": "0930"}, reference_day=day)
    assert (at.hour, at.minute, d) == (9, 30, day)
    assert at.tzinfo is not None


def test_parse_broker_time_rejects_what_it_cannot_read():
    from src.services.order_ledger import parse_broker_time

    day = date(2026, 7, 27)
    for row in ({}, {"tm": ""}, {"tm": "정오"}, {"tm": "99"},
                {"ord_tmd": "notadate12345x"}, {"tm": "996100"}):
        assert parse_broker_time(row, reference_day=day) == (None, None), row


# -- order-number ownership is per trading day -----------------------------
#
# Kiwoom order numbers are 7 digits and the spec guarantees no uniqueness
# beyond a session — they behave as a daily sequence. Owning them globally
# was safe but decayed: every terminal row ever written would forbid that
# number forever, so reconciliation liveness degraded as the ledger grew.


def _settled_buy(ledger, *, at, order_no, code="005930", qty=10, price=70000):
    """A FILLED intent that owns `order_no` on `at`'s trading day."""

    intent = _new_intent(ledger,
        stock_code=code, side=SIDE_BUY, quantity=qty, price=price, now=at
    )
    ledger.apply_order_result(
        intent.intent_id, submitted=True, unknown=False, order_no=order_no,
        reason="ok", now=at,
    )
    ledger.reconcile(
        executions=[
            _row_at(
                at + timedelta(seconds=5), ord_no=order_no, stk_cd=code,
                ord_qty=str(qty), ord_pric=str(price),
                cntr_qty=str(qty), oso_qty="0", ord_stt="체결",
            )
        ],
        now=at + timedelta(minutes=1),
    )
    assert ledger.get(intent.intent_id).state == STATE_FILLED
    return intent


def test_claim_is_scoped_to_the_trading_day(tmp_path):
    ledger = _ledger(tmp_path)
    _settled_buy(ledger, at=_dt(9), order_no="1234567")

    assert ledger.claimed_order_numbers(trading_day="2026-07-27") == {"1234567"}
    assert ledger.claimed_order_numbers(trading_day="2026-07-28") == set()
    # The unscoped form is observability only, and still sees everything.
    assert ledger.claimed_order_numbers() == {"1234567"}


def test_next_trading_day_may_reuse_the_same_seven_digit_number(tmp_path):
    """The liveness fix: a recycled daily sequence number is free again."""

    ledger = _ledger(tmp_path)
    _settled_buy(ledger, at=_dt(9), order_no="1234567")

    tomorrow = datetime(2026, 7, 28, 14, 0, tzinfo=KST)
    later = _new_intent(ledger,
        stock_code="005930", side=SIDE_BUY, quantity=10, price=70000, now=tomorrow
    )
    ledger.apply_order_result(
        later.intent_id, submitted=False, unknown=True, order_no=None,
        reason="ReadTimeout", now=tomorrow,
    )

    report = ledger.reconcile(
        executions=[
            _row_at(
                tomorrow + timedelta(seconds=3), ord_no="1234567",
                cntr_qty="10", oso_qty="0", ord_stt="체결",
            )
        ],
        now=tomorrow + timedelta(minutes=1),
    )

    row = ledger.get(later.intent_id)
    assert row.state == STATE_FILLED
    assert row.order_no == "1234567"
    assert report.adopted_order_no == 1
    # Yesterday's owner is untouched.
    assert ledger.claimed_order_numbers(trading_day="2026-07-27") == {"1234567"}
    assert ledger.claimed_order_numbers(trading_day="2026-07-28") == {"1234567"}


def test_same_day_terminal_number_is_still_untouchable(tmp_path):
    """Task 1's stale-fill defence must survive the day scoping."""

    ledger = _ledger(tmp_path)
    _settled_buy(ledger, at=_dt(9), order_no="1234567")

    # Same trading day, identical identity, later in the session.
    later = _unknown_intent(ledger, at=_dt(14))
    report = ledger.reconcile(
        executions=[
            _row_at(_dt(14, 0, 3), ord_no="1234567", cntr_qty="10", oso_qty="0",
                    ord_stt="체결")
        ],
        now=_dt(14, 1),
    )

    row = ledger.get(later.intent_id)
    assert row.state == STATE_UNKNOWN
    assert row.order_no is None
    assert report.adopted_order_no == 0


def test_a_previous_day_row_is_rejected_even_with_a_matching_number(tmp_path):
    """Day agreement on the broker event stays mandatory."""

    ledger = _ledger(tmp_path)
    tomorrow = datetime(2026, 7, 28, 14, 0, tzinfo=KST)
    later = _new_intent(ledger,
        stock_code="005930", side=SIDE_BUY, quantity=10, price=70000, now=tomorrow
    )
    ledger.apply_order_result(
        later.intent_id, submitted=False, unknown=True, order_no=None,
        reason="timeout", now=tomorrow,
    )

    # A row numbered identically but stamped on the PREVIOUS session.
    ledger.reconcile(
        executions=[
            _row_at(_dt(14), ord_no="1234567", cntr_qty="10", oso_qty="0",
                    ord_stt="체결")
        ],
        now=tomorrow + timedelta(minutes=1),
    )

    assert ledger.get(later.intent_id).state == STATE_UNKNOWN


def test_a_numbered_intent_does_not_bind_to_a_recycled_number_next_day(tmp_path):
    """A stale SUBMITTED row must not adopt today's state off a reused number."""

    ledger = _ledger(tmp_path)
    stale = _new_intent(ledger,
        stock_code="005930", side=SIDE_BUY, quantity=10, price=70000, now=_dt(14)
    )
    ledger.apply_order_result(
        stale.intent_id, submitted=True, unknown=False, order_no="1234567",
        reason="ok", now=_dt(14),
    )

    # Next session: somebody else's order carries the recycled number.
    tomorrow = datetime(2026, 7, 28, 10, 0, tzinfo=KST)
    ledger.reconcile(
        executions=[
            _row_at(tomorrow, ord_no="1234567", cntr_qty="10", oso_qty="0",
                    ord_stt="체결")
        ],
        now=tomorrow + timedelta(minutes=1),
    )

    # Still SUBMITTED — not filled off a different session's trade.
    assert ledger.get(stale.intent_id).state == STATE_SUBMITTED


def test_a_numbered_intent_still_binds_within_its_own_day(tmp_path):
    """The day check must not lock a same-session intent out of its order."""

    ledger = _ledger(tmp_path)
    intent = _new_intent(ledger,
        stock_code="005930", side=SIDE_BUY, quantity=10, price=70000, now=_dt(14)
    )
    ledger.apply_order_result(
        intent.intent_id, submitted=True, unknown=False, order_no="1234567",
        reason="ok", now=_dt(14),
    )

    ledger.reconcile(
        executions=[
            _row_at(_dt(14, 0, 3), ord_no="1234567", cntr_qty="10", oso_qty="0",
                    ord_stt="체결")
        ],
        now=_dt(14, 1),
    )

    assert ledger.get(intent.intent_id).state == STATE_FILLED


def test_a_numbered_intent_binds_to_an_untimed_row_on_its_own_day(tmp_path):
    """Untimed rows come from a same-day query, so they belong to today."""

    ledger = _ledger(tmp_path)
    today = datetime.now(KST)
    intent = _new_intent(ledger,
        stock_code="005930", side=SIDE_BUY, quantity=10, price=70000, now=today
    )
    ledger.apply_order_result(
        intent.intent_id, submitted=True, unknown=False, order_no="1234567",
        reason="ok", now=today,
    )
    row = _open_row(ord_no="1234567", cntr_qty="10", oso_qty="0", ord_stt="체결")
    row.pop("ord_tmd")

    ledger.reconcile(executions=[row], now=today)

    assert ledger.get(intent.intent_id).state == STATE_FILLED


def test_claim_comparison_uses_normalized_numbers(tmp_path):
    """Zero-padding must not let the same order look like two."""

    ledger = _ledger(tmp_path)
    # The broker reports it padded; we store it normalized.
    _settled_buy(ledger, at=_dt(9), order_no="0001234")
    assert ledger.claimed_order_numbers(trading_day="2026-07-27") == {"1234"}

    later = _unknown_intent(ledger, at=_dt(14))
    ledger.reconcile(
        # Same order, this time unpadded — must still read as claimed.
        executions=[
            _row_at(_dt(14, 0, 3), ord_no="1234", cntr_qty="10", oso_qty="0",
                    ord_stt="체결")
        ],
        now=_dt(14, 1),
    )

    assert ledger.get(later.intent_id).state == STATE_UNKNOWN
    assert ledger.get(later.intent_id).order_no is None


def test_claim_sets_do_not_mix_across_days_in_one_pass(tmp_path):
    """Two pending intents on different days, reconciled together."""

    ledger = _ledger(tmp_path)
    # Day 1 owns 1234567 via a settled row.
    _settled_buy(ledger, at=_dt(9), order_no="1234567")
    day1 = _unknown_intent(ledger, at=_dt(14))

    tomorrow = datetime(2026, 7, 28, 14, 0, tzinfo=KST)
    day2 = _new_intent(ledger,
        stock_code="000660", side=SIDE_BUY, quantity=5, price=50_000, now=tomorrow
    )
    ledger.apply_order_result(
        day2.intent_id, submitted=False, unknown=True, order_no=None,
        reason="timeout", now=tomorrow,
    )

    ledger.reconcile(
        executions=[
            # Day-1 candidate reusing day 1's owned number → refused.
            _row_at(_dt(14, 0, 3), ord_no="1234567", cntr_qty="10", oso_qty="0",
                    ord_stt="체결"),
            # Day-2 candidate reusing the SAME number on a different day → ok.
            _row_at(
                tomorrow + timedelta(seconds=3), ord_no="1234567",
                stk_cd="000660", ord_qty="5", ord_pric="50000",
                cntr_qty="5", oso_qty="0", ord_stt="체결",
            ),
        ],
        now=tomorrow + timedelta(minutes=1),
    )

    assert ledger.get(day1.intent_id).state == STATE_UNKNOWN  # blocked
    assert ledger.get(day2.intent_id).state == STATE_FILLED  # free
    assert ledger.get(day2.intent_id).order_no == "1234567"


# -- decision key vs attempt identity -------------------------------------
#
# One decision, N attempts. Collapsing the two let a same-bucket replay hand
# back an already-settled row, which the caller then submitted against and
# overwrote — a duplicate trade and a destroyed audit record in one move.


def _register(ledger, *, qty=10, price=70000, scope=None, now=None, code="005930",
              side=SIDE_BUY):
    return ledger.record_intent(
        stock_code=code, side=side, quantity=qty, price=price,
        decision_scope=scope, now=now,
    )


def test_a_fresh_decision_creates_attempt_one(tmp_path):
    reg = _register(_ledger(tmp_path))

    assert reg.outcome == REGISTRATION_CREATED
    assert reg.may_submit is True
    assert reg.intent.attempt == 1
    # Attempt 1 keeps the bare decision key, so pre-attempt ids stay valid.
    assert reg.intent.intent_id == reg.intent.decision_key


def test_unresolved_states_never_authorize_a_second_submit(tmp_path):
    for state in (STATE_INTENDED, STATE_SUBMITTED, STATE_UNKNOWN,
                  STATE_OPEN, STATE_PARTIAL):
        ledger = OrderLedger(None)
        first = _register(ledger)
        ledger.mark_state(first.intent.intent_id, state)

        replay = _register(ledger)

        assert replay.outcome == REGISTRATION_EXISTING_OPEN, state
        assert replay.may_submit is False, state
        assert replay.intent.intent_id == first.intent.intent_id, state
        # The existing row is handed back untouched, not re-opened.
        assert ledger.get(first.intent.intent_id).state == state
        assert len(ledger.attempts_for(first.intent.decision_key)) == 1


def test_filled_decision_is_refused_and_left_alone(tmp_path):
    ledger = _ledger(tmp_path)
    first = _register(ledger)
    ledger.mark_state(
        first.intent.intent_id, STATE_FILLED, order_no="1234567",
        filled_quantity=10,
    )
    before = ledger.get(first.intent.intent_id).to_dict()

    replay = _register(ledger)

    assert replay.outcome == REGISTRATION_TERMINAL
    assert replay.may_submit is False
    # No new attempt, and the settled row is byte-for-byte unchanged.
    assert len(ledger.attempts_for(first.intent.decision_key)) == 1
    assert ledger.get(first.intent.intent_id).to_dict() == before


def test_cancelled_decision_is_refused_and_left_alone(tmp_path):
    ledger = _ledger(tmp_path)
    first = _register(ledger)
    ledger.mark_state(first.intent.intent_id, STATE_CANCELLED, order_no="1234567")
    before = ledger.get(first.intent.intent_id).to_dict()

    replay = _register(ledger)

    assert replay.outcome == REGISTRATION_TERMINAL
    assert replay.may_submit is False
    assert ledger.get(first.intent.intent_id).to_dict() == before


def test_rejected_decision_retries_as_a_new_attempt_preserving_history(tmp_path):
    ledger = _ledger(tmp_path)
    first = _register(ledger)
    ledger.apply_order_result(
        first.intent.intent_id, submitted=False, unknown=False, order_no=None,
        reason="종목 정보가 없습니다",
    )

    retry = _register(ledger)

    assert retry.outcome == REGISTRATION_CREATED
    assert retry.may_submit is True
    assert retry.intent.attempt == 2
    assert retry.intent.intent_id != first.intent.intent_id
    assert retry.intent.decision_key == first.intent.decision_key
    # The rejection stays as history rather than being overwritten.
    history = ledger.attempts_for(first.intent.decision_key)
    assert [(i.attempt, i.state) for i in history] == [
        (1, STATE_REJECTED), (2, STATE_INTENDED)
    ]
    assert ledger.get(first.intent.intent_id).reason == "종목 정보가 없습니다"


def test_repeated_rejections_keep_stacking_attempts(tmp_path):
    ledger = _ledger(tmp_path)
    key = None
    for expected in (1, 2, 3):
        reg = _register(ledger)
        assert reg.intent.attempt == expected
        key = reg.intent.decision_key
        ledger.apply_order_result(
            reg.intent.intent_id, submitted=False, unknown=False,
            order_no=None, reason="거부",
        )

    assert [i.attempt for i in ledger.attempts_for(key)] == [1, 2, 3]


def test_a_different_instruction_of_the_same_size_is_a_different_decision(tmp_path):
    """TRIM 5 then CUT_LOSS 5 on 10 shares is a full exit, not a replay."""

    ledger = _ledger(tmp_path)
    trim = _register(ledger, qty=5, price=None, scope="TRIM", side=SIDE_SELL)
    cut = _register(ledger, qty=5, price=None, scope="CUT_LOSS", side=SIDE_SELL)

    assert trim.may_submit is True
    assert cut.may_submit is True
    assert trim.intent.decision_key != cut.intent.decision_key


def test_the_same_instruction_and_size_is_one_decision(tmp_path):
    ledger = _ledger(tmp_path)
    first = _register(ledger, qty=5, price=None, scope="TRIM", side=SIDE_SELL)
    again = _register(ledger, qty=5, price=None, scope="TRIM", side=SIDE_SELL)

    assert first.may_submit is True
    assert again.may_submit is False


def test_a_later_bucket_is_a_new_decision(tmp_path):
    ledger = _ledger(tmp_path)
    first = _register(ledger, now=_dt(14, 0, 0))
    ledger.mark_state(first.intent.intent_id, STATE_FILLED, filled_quantity=10)

    later = _register(ledger, now=_dt(14, 5, 0))

    assert later.may_submit is True
    assert later.intent.decision_key != first.intent.decision_key


# -- non-destructive migration --------------------------------------------


def test_pre_attempt_database_migrates_without_losing_rows(tmp_path):
    """An older ledger file must open, keep every row, and keep its ids."""

    path = tmp_path / "order_ledger.sqlite3"
    legacy = sqlite3.connect(str(path))
    legacy.executescript(
        """
        CREATE TABLE order_intents (
            intent_id       TEXT PRIMARY KEY,
            trading_day     TEXT NOT NULL,
            stock_code      TEXT NOT NULL,
            side            TEXT NOT NULL,
            quantity        INTEGER NOT NULL,
            price           INTEGER,
            state           TEXT NOT NULL,
            order_no        TEXT,
            filled_quantity INTEGER NOT NULL DEFAULT 0,
            reason          TEXT,
            origin          TEXT,
            created_at      TEXT NOT NULL,
            updated_at      TEXT NOT NULL
        );
        """
    )
    legacy.execute(
        "INSERT INTO order_intents VALUES "
        "('legacykey0001','2026-07-27','005930','buy',10,70000,'FILLED',"
        "'1234567',10,'reconciled','new_candidate',"
        "'2026-07-27T09:00:00+09:00','2026-07-27T09:01:00+09:00')"
    )
    legacy.commit()
    legacy.close()

    ledger = OrderLedger(path)
    row = ledger.get("legacykey0001")

    assert row is not None
    assert row.state == STATE_FILLED
    assert row.order_no == "1234567"
    # Backfilled as attempt 1 of its own decision, so the old id stays valid.
    assert row.decision_key == "legacykey0001"
    assert row.attempt == 1
    assert ledger.attempts_for("legacykey0001")[0].intent_id == "legacykey0001"
    # Ownership queries still see it.
    assert ledger.claimed_order_numbers(trading_day="2026-07-27") == {"1234567"}


def test_migration_is_idempotent(tmp_path):
    path = tmp_path / "order_ledger.sqlite3"
    first = _ledger(tmp_path)
    reg = _register(first)
    first.close()

    for _ in range(3):
        again = OrderLedger(path)
        assert again.get(reg.intent.intent_id) is not None
        again.close()


# -- legacy dedup bridge (Task 2 review correction A) ----------------------
#
# The pre-scope hash was day|code|side|qty|price|bucket. Today's includes the
# instruction scope, so an exact-key lookup misses a legacy row entirely and a
# replay of a legacy UNKNOWN/FILLED order was authorized to submit again. The
# earlier migration test only proved the file opened, which is why it missed
# this — these drive the real replay.

_LEGACY_COLUMNS = (
    "intent_id, trading_day, stock_code, side, quantity, price, state, "
    "order_no, filled_quantity, reason, origin, created_at, updated_at"
)


def _legacy_decision_key(
    *, trading_day, stock_code, side, quantity, price, stamp, bucket_seconds=60
):
    """The pre-scope algorithm, reproduced verbatim.

    Deliberately a literal copy rather than a call into the module: the point
    is to build a row exactly as the *old* code would have, so that if
    `make_decision_key` changes again this fixture still represents history.
    """

    bucket = int(stamp.timestamp()) // bucket_seconds
    raw = (
        f"{trading_day}|{stock_code}|{side}|{quantity}"
        f"|{price if price is not None else '-'}|{bucket}"
    )
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:20]


def _write_legacy_db(path: Path, *, state: str, stamp: datetime, order_no="1234567"):
    """A pre-attempt, pre-scope database holding exactly one row."""

    key = _legacy_decision_key(
        trading_day="2026-07-27", stock_code="005930", side=SIDE_BUY,
        quantity=10, price=70000, stamp=stamp,
    )
    conn = sqlite3.connect(str(path))
    conn.executescript(
        """
        CREATE TABLE order_intents (
            intent_id       TEXT PRIMARY KEY,
            trading_day     TEXT NOT NULL,
            stock_code      TEXT NOT NULL,
            side            TEXT NOT NULL,
            quantity        INTEGER NOT NULL,
            price           INTEGER,
            state           TEXT NOT NULL,
            order_no        TEXT,
            filled_quantity INTEGER NOT NULL DEFAULT 0,
            reason          TEXT,
            origin          TEXT,
            created_at      TEXT NOT NULL,
            updated_at      TEXT NOT NULL
        );
        """
    )
    conn.execute(
        f"INSERT INTO order_intents ({_LEGACY_COLUMNS}) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            key, "2026-07-27", "005930", SIDE_BUY, 10, 70000, state, order_no,
            10 if state == STATE_FILLED else 0, "legacy history",
            "new_candidate", stamp.isoformat(), stamp.isoformat(),
        ),
    )
    conn.commit()
    conn.close()
    return key


def _replay(ledger, stamp, scope="TIER1"):
    """The same decision the legacy row recorded, under today's algorithm."""

    return ledger.record_intent(
        stock_code="005930", side=SIDE_BUY, quantity=10, price=70000,
        decision_scope=scope, now=stamp,
    )


def test_legacy_unresolved_states_block_the_replay(tmp_path):
    stamp = _dt(14)
    for state in (STATE_INTENDED, STATE_SUBMITTED, STATE_UNKNOWN,
                  STATE_OPEN, STATE_PARTIAL):
        path = tmp_path / f"legacy_{state}.sqlite3"
        legacy_key = _write_legacy_db(path, state=state, stamp=stamp)
        ledger = OrderLedger(path)

        reg = _replay(ledger, stamp)

        assert reg.may_submit is False, state
        assert reg.outcome == REGISTRATION_EXISTING_OPEN, state
        assert reg.intent.intent_id == legacy_key, state
        assert reg.intent.is_legacy is True, state
        assert "legacy row" in (reg.reason or ""), state
        # No second row was opened.
        assert len(list(ledger._query("SELECT intent_id FROM order_intents"))) == 1
        ledger.close()


def test_legacy_terminal_states_block_the_replay_and_stay_byte_identical(tmp_path):
    stamp = _dt(14)
    for state in (STATE_FILLED, STATE_CANCELLED):
        path = tmp_path / f"legacy_{state}.sqlite3"
        legacy_key = _write_legacy_db(path, state=state, stamp=stamp)
        ledger = OrderLedger(path)
        before = ledger.get(legacy_key).to_dict()

        reg = _replay(ledger, stamp)

        assert reg.may_submit is False, state
        assert reg.outcome == REGISTRATION_TERMINAL, state
        # The audit row is untouched, field for field.
        assert ledger.get(legacy_key).to_dict() == before, state
        assert len(list(ledger._query("SELECT intent_id FROM order_intents"))) == 1
        ledger.close()


def test_legacy_rejected_allows_a_new_attempt_and_preserves_the_old_row(tmp_path):
    stamp = _dt(14)
    path = tmp_path / "legacy_rejected.sqlite3"
    legacy_key = _write_legacy_db(path, state=STATE_REJECTED, stamp=stamp)
    ledger = OrderLedger(path)
    before = ledger.get(legacy_key).to_dict()

    reg = _replay(ledger, stamp)

    assert reg.may_submit is True
    assert reg.outcome == REGISTRATION_CREATED
    # A brand-new row, not a rewrite of the legacy one.
    assert reg.intent.intent_id != legacy_key
    assert reg.intent.attempt == 2  # numbering continues across the bridge
    assert ledger.get(legacy_key).to_dict() == before
    assert len(list(ledger._query("SELECT intent_id FROM order_intents"))) == 2
    # The lineage spans both keys, which is what the bridge buys us.
    lineage = ledger.decision_history(
        stock_code="005930", side=SIDE_BUY, quantity=10, price=70000,
        decision_scope="TIER1", now=stamp,
    )
    assert [(i.attempt, i.state, i.is_legacy) for i in lineage] == [
        (1, STATE_REJECTED, True), (2, STATE_INTENDED, False)
    ]
    # And the second attempt itself now blocks a further replay.
    assert _replay(ledger, stamp).may_submit is False


def test_the_bridge_only_catches_pre_scope_rows(tmp_path):
    """New rows keep being separated by instruction, so TRIM != CUT_LOSS."""

    stamp = _dt(14)
    ledger = _ledger(tmp_path)
    trim = ledger.record_intent(
        stock_code="005930", side=SIDE_SELL, quantity=5, price=None,
        decision_scope="TRIM", now=stamp,
    )
    cut = ledger.record_intent(
        stock_code="005930", side=SIDE_SELL, quantity=5, price=None,
        decision_scope="CUT_LOSS", now=stamp,
    )

    assert trim.may_submit is True
    assert cut.may_submit is True  # not bridged into one decision
    assert trim.intent.is_legacy is False
    assert cut.intent.is_legacy is False


def test_the_bridge_respects_the_canonical_tuple(tmp_path):
    """A legacy row for a different decision must not block an unrelated one."""

    stamp = _dt(14)
    path = tmp_path / "legacy.sqlite3"
    _write_legacy_db(path, state=STATE_FILLED, stamp=stamp)
    ledger = OrderLedger(path)

    # Different quantity, different stock, different bucket — all free.
    assert ledger.record_intent(
        stock_code="005930", side=SIDE_BUY, quantity=7, price=70000,
        decision_scope="TIER1", now=stamp,
    ).may_submit is True
    assert ledger.record_intent(
        stock_code="000660", side=SIDE_BUY, quantity=10, price=70000,
        decision_scope="TIER1", now=stamp,
    ).may_submit is True
    assert ledger.record_intent(
        stock_code="005930", side=SIDE_BUY, quantity=10, price=70000,
        decision_scope="TIER1", now=_dt(14, 5),
    ).may_submit is True
    # Opposite side is a different decision too.
    assert ledger.record_intent(
        stock_code="005930", side=SIDE_SELL, quantity=10, price=70000,
        decision_scope="TIER1", now=stamp,
    ).may_submit is True


def test_legacy_bridge_survives_a_reopen(tmp_path):
    """The backfilled bucket is persisted, not recomputed per session."""

    stamp = _dt(14)
    path = tmp_path / "legacy.sqlite3"
    legacy_key = _write_legacy_db(path, state=STATE_UNKNOWN, stamp=stamp)
    first = OrderLedger(path)
    assert first.get(legacy_key).decision_bucket is not None
    first.close()

    reopened = OrderLedger(path)
    assert _replay(reopened, stamp).may_submit is False


def test_a_legacy_row_with_an_unreadable_created_at_is_left_unbridged(tmp_path):
    """Conservative: an unparseable timestamp yields NULL, not a wrong bucket."""

    path = tmp_path / "legacy.sqlite3"
    _write_legacy_db(path, state=STATE_FILLED, stamp=_dt(14))
    conn = sqlite3.connect(str(path))
    conn.execute("UPDATE order_intents SET created_at = 'not a timestamp'")
    conn.commit()
    conn.close()

    ledger = OrderLedger(path)  # must still open

    assert ledger.get(
        list(ledger._query("SELECT intent_id FROM order_intents"))[0][0]
    ).decision_bucket is None


# -- registration atomicity (Task 2 review correction B) ------------------


def test_two_connections_racing_one_decision_authorize_exactly_one(tmp_path):
    """Two watchers on one ledger file, released from a barrier together.

    Pre-fix the loser raised a UNIQUE-constraint `OrderLedgerError`, which the
    protective-order path treats as a ledger *fault* and therefore submits
    anyway — turning the race into a real double sell.
    """

    path = tmp_path / "race.sqlite3"
    OrderLedger(path).close()  # create the schema up front
    stamp = _dt(14)
    barrier = threading.Barrier(2)
    results: dict[str, Any] = {}

    def worker(name: str) -> None:
        # Its own connection, created in its own thread — as a second process
        # would have.
        ledger = OrderLedger(path)
        try:
            barrier.wait(timeout=5)
            results[name] = ledger.record_intent(
                stock_code="005930", side=SIDE_BUY, quantity=10, price=70000,
                decision_scope="TIER1", now=stamp,
            )
        except OrderLedgerError as exc:  # pragma: no cover - the defect
            results[name] = exc
        finally:
            ledger.close()

    threads = [threading.Thread(target=worker, args=(n,)) for n in ("A", "B")]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=15)

    assert set(results) == {"A", "B"}
    # A uniqueness race is duplicate detection, never a storage fault.
    assert not any(isinstance(r, OrderLedgerError) for r in results.values())
    authorized = [r for r in results.values() if r.may_submit]
    refused = [r for r in results.values() if not r.may_submit]
    assert len(authorized) == 1
    assert len(refused) == 1
    assert refused[0].outcome == REGISTRATION_EXISTING_OPEN

    survivor = OrderLedger(path)
    assert len(list(survivor._query("SELECT intent_id FROM order_intents"))) == 1
    survivor.close()


def test_racing_a_rejected_retry_allocates_one_attempt(tmp_path):
    """Attempt numbering must be race-safe too, or two rows claim attempt 2."""

    path = tmp_path / "race_retry.sqlite3"
    seed = OrderLedger(path)
    first = _register(seed, scope="TIER1", now=_dt(14))
    seed.apply_order_result(
        first.intent.intent_id, submitted=False, unknown=False, order_no=None,
        reason="거부", now=_dt(14),
    )
    seed.close()

    stamp = _dt(14)
    barrier = threading.Barrier(3)
    results: dict[str, Any] = {}

    def worker(name: str) -> None:
        ledger = OrderLedger(path)
        try:
            barrier.wait(timeout=5)
            results[name] = ledger.record_intent(
                stock_code="005930", side=SIDE_BUY, quantity=10, price=70000,
                decision_scope="TIER1", now=stamp,
            )
        except OrderLedgerError as exc:  # pragma: no cover - the defect
            results[name] = exc
        finally:
            ledger.close()

    threads = [threading.Thread(target=worker, args=(n,)) for n in ("A", "B", "C")]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=15)

    assert not any(isinstance(r, OrderLedgerError) for r in results.values())
    assert len([r for r in results.values() if r.may_submit]) == 1

    survivor = OrderLedger(path)
    history = survivor.attempts_for(first.intent.decision_key)
    assert [i.attempt for i in history] == [1, 2]  # exactly one retry row
    survivor.close()


def test_a_real_storage_fault_is_still_an_exception(tmp_path):
    """Requirement: uniqueness races are duplicates, disks are faults."""

    ledger = _ledger(tmp_path)
    ledger.close()

    with pytest.raises(OrderLedgerError):
        _register(ledger)


@pytest.mark.parametrize("state", [STATE_FILLED, STATE_PARTIAL, STATE_OPEN, STATE_CANCELLED, STATE_REJECTED])
@pytest.mark.parametrize("submitted,unknown", [(True, False), (False, True), (False, False)])
def test_late_rest_response_does_not_overwrite_broker_event(state, submitted, unknown):
    ledger = OrderLedger(None)
    intent = _new_intent(ledger, stock_code="005930", side=SIDE_BUY, quantity=10, price=10000)
    ledger.mark_state(intent.intent_id, state, order_no="123", filled_quantity=5, reason="realtime")
    before = ledger.get(intent.intent_id).to_dict()
    result = ledger.apply_order_result(
        intent.intent_id, submitted=submitted, unknown=unknown, order_no="123", reason="REST",
    )
    assert result == state
    assert ledger.get(intent.intent_id).to_dict() == before
    ledger.close()
