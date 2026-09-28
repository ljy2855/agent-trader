"""Realtime 주문체결 → ledger, and the socket lifecycle around it.

The protocol translation is pure, so these run without a broker. The value
being protected is the 2026-08-26 blind spot: an order that fills between two
polls appears in neither the open-order nor the execution view at the moment
we look, and its intent sat at SUBMITTED for a session while emitting 708
warnings.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import Settings  # noqa: E402
from src.services import realtime_orders as rt  # noqa: E402
from src.services.order_ledger import SIDE_BUY, OrderLedger  # noqa: E402
from src.services.realtime_stream import (  # noqa: E402
    RealtimeOrderStream,
    websocket_uri,
)

KST = ZoneInfo("Asia/Seoul")


@pytest.fixture
def settings() -> Settings:
    return Settings(
        KIWOOM_USE_MOCK="true",
        KIWOOM_MOCK_APPKEY="mock-key",
        KIWOOM_MOCK_SECRETKEY="mock-secret",
    )

FILL_VALUES = {
    "9203": "0108634",   # 주문번호
    "9001": "A105560",   # 종목코드
    "913": "체결",        # 주문상태
    "900": "1",          # 주문수량
    "901": "165300",     # 주문가격
    "902": "0",          # 미체결수량
    "911": "1",          # 체결량
    "905": "+매수",       # 주문구분
    "908": "091547",     # 주문/체결시간
}


def _real(values, type_="00"):
    return {"trnm": "REAL", "data": [{"type": type_, "item": "", "values": values}]}


# -- translation -------------------------------------------------------------


def test_fill_frame_becomes_a_broker_row():
    (row,) = rt.extract_order_rows(_real(FILL_VALUES))

    assert row == {
        "ord_no": "0108634",
        "stk_cd": "A105560",
        "ord_stt": "체결",
        "ord_qty": "1",
        "ord_pric": "165300",
        "oso_qty": "0",
        "cntr_qty": "1",
        "io_tp_nm": "+매수",
        "ord_tm": "091547",
    }


def test_other_realtime_types_are_ignored():
    """We subscribe to one type; a shared socket could carry others."""

    assert rt.extract_order_rows(_real({"10": "70000"}, type_="0B")) == []
    assert rt.extract_order_rows({"trnm": "PING"}) == []
    assert rt.extract_order_rows("PING") == []


def test_frame_without_an_order_number_is_dropped():
    """Unnumbered matching is time-and-identity based and REST-shaped.

    Widening it with a stream frame would change rules written for a
    same-day query, so the polled path handles those orders instead.
    """

    assert rt.extract_order_rows(_real({k: v for k, v in FILL_VALUES.items()
                                        if k != "9203"})) == []


def test_blank_fids_do_not_become_empty_fields():
    """An absent value must be absent, not "" -- parsers read presence."""

    row, = rt.extract_order_rows(_real({**FILL_VALUES, "908": "   "}))
    assert "ord_tm" not in row


def test_rejection_reason_is_extracted_separately():
    """FID 919 is not a row field: no REST view carries it."""

    frame = _real({**FILL_VALUES, "913": "거부",
                   "919": "308003:주문단가를 입력하십시요"})

    assert rt.extract_rejections(frame) == [
        ("0108634", "308003:주문단가를 입력하십시요")
    ]
    assert "919" not in rt.extract_order_rows(frame)[0]


@pytest.mark.parametrize(
    "values",
    [
        FILL_VALUES,                         # 체결, no 919 at all
        {**FILL_VALUES, "919": "0"},         # 체결 with the live sentinel
        {**FILL_VALUES, "913": "접수", "919": "0"},
    ],
    ids=["fill-no-919", "fill-sentinel-919", "accepted-sentinel-919"],
)
def test_a_healthy_order_never_reads_as_rejected(values):
    """919 is populated as "0" on good fills, so presence is not rejection.

    Reading it that way alerted four times on 2026-09-02 for two orders
    that both filled -- the first live session with the stream on.
    """

    assert rt.extract_rejections(_real(values)) == []


def test_rejection_without_a_stated_reason_still_alerts():
    """Silence would be worse: the order was refused either way."""

    frame = _real({**FILL_VALUES, "913": "거부", "919": "0"})

    assert rt.extract_rejections(frame) == [("0108634", "사유 미상")]


# -- ledger integration ------------------------------------------------------


def test_realtime_fill_settles_what_polling_could_not(tmp_path):
    """The 2026-08-26 regression, end to end.

    An immediately-filled buy is in neither broker view, so reconciliation
    leaves it SUBMITTED however often it runs. One pushed frame settles it.
    """

    led = OrderLedger(str(tmp_path / "l.sqlite3"))
    now = datetime(2026, 8, 26, 9, 15, 47, tzinfo=KST)
    reg = led.record_intent(
        stock_code="105560", side=SIDE_BUY, quantity=1, price=165300,
        origin="new_candidate", decision_scope="TIER2", now=now,
    )
    led.mark_state(reg.intent.intent_id, "SUBMITTED", order_no="108634", now=now)

    led.reconcile(open_orders=[], executions=[], broker_views_complete=True,
                  now=datetime(2026, 8, 26, 9, 20, tzinfo=KST))
    assert [i.state for i in led.unresolved()] == ["SUBMITTED"]

    report = led.reconcile(
        executions=rt.extract_order_rows(_real(FILL_VALUES)),
        broker_views_complete=False,
        now=datetime(2026, 8, 26, 9, 15, 50, tzinfo=KST),
    )

    assert report.resolved == 1
    assert led.unresolved() == []


# -- packets -----------------------------------------------------------------


def test_registration_subscribes_to_the_account_not_a_symbol():
    packet = rt.build_register_packet()

    assert packet["trnm"] == "REG"
    assert packet["data"][0]["type"] == ["00"]
    assert packet["refresh"] == "1", "must not drop an existing registration"


def test_login_failure_is_reported_and_success_is_not():
    assert rt.login_error({"trnm": "LOGIN", "return_code": 0}) is None
    assert rt.login_error({"trnm": "LOGIN", "return_code": "0"}) is None
    assert rt.login_error({"trnm": "LOGIN", "return_code": 8005,
                           "return_msg": "만료"}) == (8005, "만료")
    assert rt.login_error({"trnm": "REAL"}) is None


def test_ping_detection_covers_both_encodings():
    assert rt.is_ping("PING") is True
    assert rt.is_ping({"trnm": "PING"}) is True
    assert rt.is_ping(_real(FILL_VALUES)) is False


# -- socket lifecycle --------------------------------------------------------


class FakeSocket:
    """Replays a scripted server; records what the client sent."""

    def __init__(self, script):
        self._script = list(script)
        self.sent: list = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def send(self, raw):
        self.sent.append(json.loads(raw))

    async def recv(self):
        if not self._script:
            raise ConnectionError("server closed")
        return json.dumps(self._script.pop(0))


def _stream(script, settings, **kwargs):
    socket = FakeSocket(script)
    stream = RealtimeOrderStream(
        settings,
        token_provider=_token,
        on_rows=kwargs.pop("on_rows", _noop_rows),
        connect=lambda uri: socket,
        **kwargs,
    )
    return stream, socket


async def _token():
    return "tok"


async def _noop_rows(rows):
    return None


def test_session_logs_in_registers_then_delivers_rows(settings):
    seen: list = []

    async def collect(rows):
        seen.extend(rows)

    stream, socket = _stream(
        [{"trnm": "LOGIN", "return_code": 0}, _real(FILL_VALUES)],
        settings,
        on_rows=collect,
    )

    with pytest.raises(ConnectionError):
        asyncio.run(stream._session())

    assert [p["trnm"] for p in socket.sent] == ["LOGIN", "REG"]
    assert socket.sent[0]["token"] == "tok"
    assert len(seen) == 1


def test_ping_is_echoed_back(settings):
    stream, socket = _stream(
        [{"trnm": "LOGIN", "return_code": 0}, {"trnm": "PING", "n": 1}],
        settings,
    )

    with pytest.raises(ConnectionError):
        asyncio.run(stream._session())

    assert {"trnm": "PING", "n": 1} in socket.sent


def test_login_rejection_aborts_the_session(settings):
    stream, socket = _stream(
        [{"trnm": "LOGIN", "return_code": 8005, "return_msg": "만료"}], settings
    )

    with pytest.raises(RuntimeError, match="8005"):
        asyncio.run(stream._session())

    assert [p["trnm"] for p in socket.sent] == ["LOGIN"], "must not subscribe"


def test_a_failing_handler_does_not_kill_the_stream(settings):
    """Dropping the socket would silently fall back to polling-only."""

    calls = []

    async def boom(rows):
        calls.append(rows)
        raise RuntimeError("ledger fault")

    stream, _socket = _stream(
        [{"trnm": "LOGIN", "return_code": 0},
         _real(FILL_VALUES), _real(FILL_VALUES)],
        settings,
        on_rows=boom,
    )

    with pytest.raises(ConnectionError):
        asyncio.run(stream._session())

    assert len(calls) == 2, "second event must still be delivered"


def test_uri_targets_the_realtime_port(settings):
    uri = websocket_uri(settings)

    assert uri.startswith("wss://")
    assert uri.endswith(":10000/api/dostk/websocket")


# -- watcher wiring ----------------------------------------------------------
#
# The predicate being right is not the same as the watcher reaching it.


def test_watcher_leaves_the_stream_off_by_default(tmp_path):
    from tests.test_watcher import _build_watcher

    w = _build_watcher()
    w._start_realtime_orders()

    assert w._realtime is None


def test_watcher_starts_the_stream_when_enabled(tmp_path, monkeypatch):
    from tests.test_watcher import _build_watcher, _config

    started: list = []

    class Spy:
        def __init__(self, *a, **k):
            self.args = (a, k)

        def start(self):
            started.append(self)

    class TokenStub:
        async def get_valid_token(self):
            return "tok"

        async def force_refresh(self):
            return "tok2"

    class ClientStub:
        token_manager = TokenStub()

    monkeypatch.setattr(
        "src.services.watcher.RealtimeOrderStream", Spy
    )
    w = _build_watcher(config=_config(enable_realtime_orders=True))
    w._ledger = object()  # a ledger must exist for the stream to be useful
    w._client = ClientStub()
    w._start_realtime_orders()

    assert len(started) == 1


def test_stream_is_not_started_without_a_ledger(monkeypatch):
    """Nothing to reconcile into means nothing to subscribe for."""

    from tests.test_watcher import _build_watcher, _config

    monkeypatch.setattr(
        "src.services.watcher.RealtimeOrderStream",
        lambda *a, **k: pytest.fail("must not construct a stream"),
    )
    w = _build_watcher(config=_config(enable_realtime_orders=True))
    w._ledger = None

    w._start_realtime_orders()


def test_watcher_reconciles_pushed_rows_without_claiming_complete_views(tmp_path):
    """`broker_views_complete` must stay False on this path.

    That flag licenses the UNKNOWN protective-sell release, which requires a
    fully paginated sweep of both views. A single pushed event is not that.
    """

    from tests.test_watcher import _build_watcher

    seen: dict = {}

    class LedgerSpy:
        def reconcile(self, **kwargs):
            seen.update(kwargs)

            class R:
                resolved = 1
                adopted_order_no = 0

                @staticmethod
                def to_dict():
                    return {}

            return R()

    w = _build_watcher()
    w._ledger = LedgerSpy()

    asyncio.run(w._on_realtime_rows(rt.extract_order_rows(_real(FILL_VALUES))))

    assert seen["broker_views_complete"] is False
    assert "open_orders" not in seen, "absence must not be inferred from a push"
    assert seen["executions"][0]["ord_no"] == "0108634"


# --- token expiry on the socket ---------------------------------------------
#
# 2026-09-05: the stream spent a weekend retrying one stale token, 977 times.
# REST refreshes on an expiry verdict and recovers; the socket did not, and
# off-hours is exactly when it bites — polling stops, so nothing else renews
# the cache and the socket is the only thing still authenticating.

WS_EXPIRED = (
    "토큰 인증에 실패했습니다. 접속을 종료합니다 "
    "[CODE=8005, MESSAGE=Token이 유효하지 않습니다]"
)


def _stream_with_refresh(settings, script, refreshed):
    async def refresh():
        refreshed.append(1)

    socket = FakeSocket(script)
    return RealtimeOrderStream(
        settings,
        token_provider=_token,
        on_rows=_noop_rows,
        refresh_token=refresh,
        connect=lambda uri: socket,
    )


def test_an_expired_token_is_reissued_by_the_reconnect_loop(settings):
    """Drives run(), not the helper: the loop has to reach the refresh.

    A test that calls _maybe_refresh_token directly passes even when the
    reconnect loop never calls it — which is precisely the code path that
    spent a weekend replaying one dead token.
    """

    refreshed: list = []
    tokens_used: list = []

    async def token():
        tokens_used.append(len(refreshed))
        return f"tok{len(refreshed)}"

    async def refresh():
        refreshed.append(1)

    socket = FakeSocket(
        [{"trnm": "LOGIN", "return_code": 805004, "return_msg": WS_EXPIRED}] * 6
    )
    stream = RealtimeOrderStream(
        settings,
        token_provider=token,
        on_rows=_noop_rows,
        refresh_token=refresh,
        connect=lambda uri: socket,
    )

    async def drive():
        task = asyncio.create_task(stream.run())
        for _ in range(200):          # let a couple of reconnect cycles land
            await asyncio.sleep(0)
            if refreshed:
                break
        await stream.stop()
        with contextlib.suppress(asyncio.CancelledError):
            await task

    asyncio.run(drive())

    assert refreshed, "the reconnect loop must reissue the token"
    assert tokens_used[0] == 0, "first attempt uses the cached token"


@pytest.mark.parametrize(
    "code,msg",
    [
        (805004, "[CODE=8001, MESSAGE=App Key와 Secret Key 검증에 실패했습니다]"),
        (805004, "[CODE=8031, MESSAGE=모의투자 미신청]"),
    ],
    ids=["bad-credentials", "mode-mismatch"],
)
def test_a_misconfiguration_does_not_hammer_the_token_endpoint(settings, code, msg):
    """Reissuing cannot fix these; retrying them just multiplies failures."""

    refreshed: list = []
    stream = _stream_with_refresh(
        settings, [{"trnm": "LOGIN", "return_code": code, "return_msg": msg}], refreshed
    )

    async def one_cycle():
        try:
            await stream._session()
        except Exception as exc:
            await stream._maybe_refresh_token(exc)

    asyncio.run(one_cycle())

    assert refreshed == []


def test_a_transport_drop_does_not_touch_the_token(settings):
    """Only a login verdict says anything about the token."""

    refreshed: list = []
    stream = _stream_with_refresh(settings, [], refreshed)

    async def one_cycle():
        try:
            await stream._session()
        except Exception as exc:
            await stream._maybe_refresh_token(exc)

    asyncio.run(one_cycle())

    assert refreshed == []
