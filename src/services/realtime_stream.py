"""Long-lived Kiwoom realtime socket feeding order events to the ledger.

Owns the connection lifecycle only; the protocol itself is pure functions in
``realtime_orders`` so it can be tested without a broker. See that module for
why this exists and, more importantly, for what it deliberately is not: the
polled reconciliation stays authoritative, because a socket that was down
missed events and Kiwoom offers no replay. This narrows the window in which
the ledger is out of date with the broker; it does not close it.

Failure posture matches the rest of the order path. Anything that goes wrong
here is logged and retried, never raised into the trading loop: a realtime
outage must not stop Tier-1 exits, and it cannot block new entries either,
since the polled path already gates those on its own freshness checks.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from typing import Any, Awaitable, Callable

import websockets

from ..config import Settings
from .kiwoom_client import is_auth_expiry_code
from .realtime_orders import (
    build_login_packet,
    build_register_packet,
    extract_order_rows,
    extract_rejections,
    is_ping,
    login_error,
)

log = logging.getLogger("kiwoom.watcher.realtime")


class RealtimeLoginRejected(RuntimeError):
    """The broker refused the LOGIN frame, with its return code kept intact."""

    def __init__(self, code: int, message: str):
        super().__init__(f"realtime login rejected ({code}): {message}")
        self.code = code
        self.return_msg = message

# Kiwoom serves realtime on a dedicated port rather than the REST host.
_WS_PORT = 10000
_WS_PATH = "/api/dostk/websocket"

# Reconnect backoff. Capped low: the value of this stream is timeliness, and a
# long sleep after a blip would leave the ledger polling-only for no reason.
_BACKOFF_START = 1.0
_BACKOFF_MAX = 30.0


def websocket_uri(settings: Settings) -> str:
    """``wss://…:10000/api/dostk/websocket`` for the configured environment."""

    host = str(settings.active_base_url).split("://", 1)[-1].strip("/")
    return f"wss://{host}:{_WS_PORT}{_WS_PATH}"


class RealtimeOrderStream:
    """Subscribes to 주문체결 and hands each order row to a callback.

    The callback is expected to be cheap and non-raising; it runs inline with
    the receive loop, so anything slow there delays the next event.
    """

    def __init__(
        self,
        settings: Settings,
        token_provider: Callable[[], Awaitable[str]],
        on_rows: Callable[[list[dict[str, Any]]], Awaitable[None]],
        *,
        on_rejection: Callable[[str, str], Awaitable[None]] | None = None,
        refresh_token: Callable[[], Awaitable[Any]] | None = None,
        connect: Callable[..., Any] | None = None,
    ):
        self._settings = settings
        self._token_provider = token_provider
        self._refresh_token = refresh_token
        self._on_rows = on_rows
        self._on_rejection = on_rejection
        self._connect = connect or websockets.connect
        self._stop = asyncio.Event()
        self._task: asyncio.Task | None = None
        self.connected = False
        self.events_received = 0
        self.last_event_at: float | None = None

    # -- lifecycle -----------------------------------------------------------

    def start(self) -> None:
        if self._task is None or self._task.done():
            self._stop.clear()
            self._task = asyncio.create_task(self.run())

    async def stop(self) -> None:
        self._stop.set()
        if self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    async def run(self) -> None:
        """Connect, subscribe, consume — forever, with backoff on failure."""

        backoff = _BACKOFF_START
        while not self._stop.is_set():
            try:
                await self._session()
                backoff = _BACKOFF_START  # a clean session resets the ramp
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001 — must never escape
                self.connected = False
                await self._maybe_refresh_token(exc)
                log.warning("realtime stream error (%s); reconnecting in %.0fs",
                            exc, backoff)
            if self._stop.is_set():
                break
            with contextlib.suppress(asyncio.TimeoutError):
                await asyncio.wait_for(self._stop.wait(), timeout=backoff)
            backoff = min(backoff * 2, _BACKOFF_MAX)

    # -- one connection ------------------------------------------------------

    async def _session(self) -> None:
        uri = websocket_uri(self._settings)
        async with self._connect(uri) as socket:
            await self._send(socket, build_login_packet(await self._token_provider()))
            await self._await_login_ack(socket)
            await self._send(socket, build_register_packet())
            self.connected = True
            log.info("realtime order stream connected")
            await self._consume(socket)

    async def _maybe_refresh_token(self, exc: BaseException) -> None:
        """Reissue the access token when the broker says it has expired.

        The REST client has always done this; the socket did not, so it
        replayed one stale token every 30 seconds for a whole weekend (977
        attempts, 2026-09-05). Off-hours is exactly when it bites: REST stops
        polling, so nothing else refreshes the cache, and the socket is the
        only thing still authenticating.

        Refreshing only on an expiry verdict matters. Wrong credentials and a
        mode mismatch fail the same way to a caller but cannot be fixed by
        reissuing, and hammering the token endpoint on those would turn a
        misconfiguration into rate-limited noise.
        """

        if self._refresh_token is None:
            return
        if not isinstance(exc, RealtimeLoginRejected):
            return
        if not is_auth_expiry_code(exc.code, exc.return_msg):
            return
        try:
            await self._refresh_token()
            log.info("realtime access token reissued after an expiry rejection")
        except Exception as refresh_exc:  # noqa: BLE001 — best effort
            log.warning("realtime token refresh failed: %s", refresh_exc)

    async def _send(self, socket: Any, payload: dict[str, Any]) -> None:
        await socket.send(json.dumps(payload))

    async def _await_login_ack(self, socket: Any) -> None:
        while True:
            message = await self._receive(socket)
            if is_ping(message):
                await self._send(socket, message)
                continue
            failure = login_error(message)
            if failure is not None:
                code, msg = failure
                raise RealtimeLoginRejected(code, msg)
            if isinstance(message, dict) and str(message.get("trnm", "")).upper() == "LOGIN":
                return
            # Anything else before the ack means the handshake is not what we
            # think it is; tearing down is safer than subscribing blind.
            raise RuntimeError(f"unexpected frame before login ack: {message!r}")

    async def _consume(self, socket: Any) -> None:
        while not self._stop.is_set():
            message = await self._receive(socket)
            if is_ping(message):
                await self._send(socket, message)
                continue
            await self._handle(message)

    async def _receive(self, socket: Any) -> Any:
        raw = await socket.recv()
        if isinstance(raw, (bytes, bytearray)):
            raw = raw.decode("utf-8", "replace")
        try:
            return json.loads(raw)
        except (TypeError, ValueError):
            return raw  # PING arrives as a bare string on some builds

    async def _handle(self, message: Any) -> None:
        rows = extract_order_rows(message)
        if rows:
            self.events_received += len(rows)
            self.last_event_at = asyncio.get_running_loop().time()
            try:
                await self._on_rows(rows)
            except Exception as exc:  # noqa: BLE001
                # A ledger fault must not kill the socket: dropping the stream
                # would silently return us to polling-only.
                log.warning("realtime row handler failed: %s", exc)
        if self._on_rejection is not None:
            for ident, reason in extract_rejections(message):
                with contextlib.suppress(Exception):
                    await self._on_rejection(ident, reason)
