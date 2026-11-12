"""Tests for Kiwoom client authentication retry behavior."""

from __future__ import annotations

import asyncio
import importlib
import os
import sys
from pathlib import Path
from typing import Any

import httpx
import pytest

os.environ.setdefault("KIWOOM_APPKEY", "dummy-appkey")
os.environ.setdefault("KIWOOM_SECRETKEY", "dummy-secretkey")
os.environ.setdefault("KIWOOM_USE_MOCK", "false")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

config_module = importlib.import_module("src.config")
client_module = importlib.import_module("src.services.kiwoom_client")

Settings = config_module.Settings
KiwoomClient = client_module.KiwoomClient


class FakeTokenManager:
    """Minimal token manager stub for client retry tests."""

    def __init__(self) -> None:
        self.current_token = "stale-token"
        self.invalidate_calls = 0
        self.force_refresh_calls = 0

    async def get_valid_token(self) -> str:
        return self.current_token

    async def invalidate(self) -> None:
        self.invalidate_calls += 1

    async def force_refresh(self) -> str:
        self.force_refresh_calls += 1
        self.current_token = f"fresh-token-{self.force_refresh_calls}"
        return self.current_token


def test_client_retries_once_when_kiwoom_reports_invalid_token(monkeypatch) -> None:
    """Business-level token failures should trigger one refresh and retry."""

    monkeypatch.setenv("KIWOOM_USE_MOCK", "true")
    monkeypatch.setenv("KIWOOM_MOCK_APPKEY", "mock-appkey")
    monkeypatch.setenv("KIWOOM_MOCK_SECRETKEY", "mock-secret")
    settings = Settings(_env_file=None)

    recorded_tokens: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        recorded_tokens.append(request.headers["authorization"])
        if request.headers["authorization"] == "Bearer stale-token":
            return httpx.Response(
                200,
                json={
                    "return_code": 8005,
                    "return_msg": "인증에 실패했습니다[8005:Token이 유효하지 않습니다]",
                },
            )
        return httpx.Response(
            200,
            json={
                "return_code": 0,
                "return_msg": "정상적으로 처리되었습니다",
            },
        )

    token_manager = FakeTokenManager()
    http_client = httpx.AsyncClient(
        base_url=settings.active_base_url,
        transport=httpx.MockTransport(handler),
    )
    client = KiwoomClient(
        settings,
        token_manager=token_manager,
        http_client=http_client,
    )

    async def run_test() -> dict[str, Any]:
        response = await client.post(
            "/uapi/domestic-stock/v1/trading/inquire-balance",
            headers={"api-id": "kt00004"},
            json={"qry_tp": "0"},
        )
        await http_client.aclose()
        return response.json()

    payload = asyncio.run(run_test())

    assert payload["return_code"] == 0
    assert token_manager.invalidate_calls == 1
    assert token_manager.force_refresh_calls == 1
    assert recorded_tokens == ["Bearer stale-token", "Bearer fresh-token-1"]


# --- Auth-expiry classification ---------------------------------------------
#
# Kiwoom reports the specific code either at the top level or embedded in the
# message as `[8005:...]`. We knew only top-level 8005 and otherwise matched
# Korean message text, so the embedded form -- which the mock endpoint
# actually returns -- fell through to the fallbacks or was missed entirely.
# Code table sourced from Kiwoom's official API repository and re-expressed
# in `kiwoom_client`; see the comment there on why it is not imported.


@pytest.mark.parametrize(
    "payload",
    [
        {"return_code": 8005, "return_msg": "Token이 유효하지 않습니다"},
        {"return_code": 3, "return_msg": "인증에 실패했습니다[8005:Token이 유효하지 않습니다]"},
        {"return_code": 3, "return_msg": "인증에 실패했습니다[8003:토큰이 만료되었습니다]"},
        {"return_code": 8016, "return_msg": ""},
    ],
    ids=["top-level", "embedded", "embedded-8003", "another-expiry-code"],
)
def test_expired_token_is_detected_by_code(payload):
    assert client_module._is_token_invalid_payload(payload) is True


@pytest.mark.parametrize(
    "payload",
    [
        {"return_code": 3, "return_msg": "인증에 실패했습니다[8001:App Key와 Secret Key 검증에 실패했습니다]"},
        {"return_code": 3, "return_msg": "인증에 실패했습니다[8031:모의투자 미신청 계좌입니다]"},
        {"return_code": 0, "return_msg": "정상처리"},
        {"return_code": 2000, "return_msg": "[2000](308003:주문단가를 입력하십시요)"},
    ],
    ids=["bad-credentials", "mode-mismatch", "success", "order-rejection"],
)
def test_non_expiry_failures_do_not_trigger_a_token_retry(payload):
    """Reissuing cannot fix wrong keys or the wrong mode.

    Retrying those just doubles the failed calls, and on the order path every
    extra call is another chance to double-submit. The 8001 case is real: the
    mock endpoint returned exactly that shape on 2026-08-31.
    """

    assert client_module._is_token_invalid_payload(payload) is False


def test_embedded_code_parser_reads_only_the_bracket_colon_form():
    """`[8005:...]` is the shape Kiwoom uses for an embedded auth code.

    An order rejection reads `[2000](308003:...)` -- bracket then paren --
    and must not parse, or a refused order would look like an expired token
    and get retried.
    """

    assert client_module.embedded_return_code("인증에 실패했습니다[8005:x]") == 8005
    assert client_module.embedded_return_code("[2000](308003:주문단가)") is None
    assert client_module.embedded_return_code("no code here") is None
    assert client_module.embedded_return_code(None) is None


def test_websocket_embeds_its_code_differently_than_rest():
    """`CODE=8005` is the realtime form; only `[8005:...]` was matched.

    The socket's rejection therefore looked like an unknown failure, so the
    expired token was never reissued and the same one was replayed every 30
    seconds for a weekend (2026-09-05).
    """

    ws = (
        "토큰 인증에 실패했습니다. 접속을 종료합니다 "
        "[CODE=8005, MESSAGE=Token이 유효하지 않습니다]"
    )

    assert client_module.embedded_return_code(ws) == 8005
    assert client_module.is_auth_expiry_code(805004, ws) is True


def test_auth_expiry_verdict_is_shared_and_narrow():
    assert client_module.is_auth_expiry_code(8005, "") is True
    assert client_module.is_auth_expiry_code(805004, "[CODE=8001, MESSAGE=x]") is False
    assert client_module.is_auth_expiry_code(0, "정상처리") is False


# -- once-a-second account queries ---------------------------------------------


class _Clock:
    """Time that moves only when the client sleeps, so spacing is exact."""

    def __init__(self) -> None:
        self.now = 1000.0
        self.slept: list[float] = []

    def __call__(self) -> float:
        return self.now

    async def sleep(self, seconds: float) -> None:
        self.slept.append(round(seconds, 3))
        self.now += seconds


class _OncePerSecond:
    """Kiwoom's gate as its 2026-11-09 notice states it: each listed query
    once a second, refused with 429 (the status its rate limit has always
    answered with) when asked again sooner."""

    def __init__(self, clock: _Clock, *, others_sent_at: dict[str, float] | None = None) -> None:
        self.clock = clock
        self.last = dict(others_sent_at or {})  # sends by another process on the key
        self.seen: list[tuple[str, float, int]] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        api_id = request.headers["api-id"]
        limited = api_id in client_module.ONE_PER_SECOND_API_IDS
        last = self.last.get(api_id)
        refused = limited and last is not None and self.clock() - last < 1.0
        self.last[api_id] = self.clock()
        self.seen.append((api_id, round(self.clock() - 1000.0, 3), 429 if refused else 200))
        if refused:
            return httpx.Response(429, text="Too Many Requests")
        return httpx.Response(200, json={"return_code": 0, "return_msg": "정상적으로 처리되었습니다"})


@pytest.fixture
def paced(monkeypatch):
    """A real client in front of the once-a-second gate, on a clock we hold."""

    monkeypatch.setenv("KIWOOM_USE_MOCK", "true")
    monkeypatch.setenv("KIWOOM_MOCK_APPKEY", "mock-appkey")
    monkeypatch.setenv("KIWOOM_MOCK_SECRETKEY", "mock-secret")
    clock = _Clock()
    monkeypatch.setattr(client_module, "_clock", clock)
    monkeypatch.setattr(client_module, "_sleep", clock.sleep)

    def build(**gate_kwargs):
        gate = _OncePerSecond(clock, **gate_kwargs)
        settings = Settings(_env_file=None)
        http_client = httpx.AsyncClient(
            base_url=settings.active_base_url, transport=httpx.MockTransport(gate)
        )
        token_manager = FakeTokenManager()
        token_manager.current_token = "fresh-token"
        return KiwoomClient(settings, token_manager=token_manager, http_client=http_client), gate, clock

    return build


def _ask(client, api_id: str):
    return client.post("/api/dostk/acnt", headers={"api-id": api_id, "cont-yn": "N"}, json={})


def test_the_buy_gates_account_read_waits_out_the_planners(paced):
    """One tick reads the account twice: the planner first, the buy gate a
    few hundred milliseconds later. Since 2026-11-12 18:00 Kiwoom refuses the
    second, and a refused account read blocks the buy."""

    client, gate, clock = paced()

    async def tick():
        await _ask(client, "kt00004")  # planner
        clock.now += 0.4               # the market snapshot in between
        await _ask(client, "kt00004")  # buy gate, first ETF
        await _ask(client, "kt00004")  # buy gate, second ETF

    asyncio.run(tick())

    assert [status for _, _, status in gate.seen] == [200, 200, 200]
    assert [at for _, at, _ in gate.seen] == [0.0, 1.2, 2.4]
    assert clock.slept == [0.8, 1.2]


def test_without_the_spacing_the_gate_refuses_the_second_read(paced, monkeypatch):
    """What the fixture's gate does to the old behaviour — the reason the
    spacing exists."""

    monkeypatch.setattr(client_module, "ACCOUNT_QUERY_SPACING_SECONDS", 0.0)
    client, gate, _ = paced()

    async def tick():
        await _ask(client, "kt00004")
        await _ask(client, "kt00004")

    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(tick())
    assert [status for _, _, status in gate.seen] == [200, 429, 429]


def test_other_queries_are_not_held_back(paced):
    """The limit is per query: the unfilled-orders read that follows the
    account read in every tick is a different one, and not on the list."""

    client, gate, clock = paced()

    async def tick():
        await _ask(client, "kt00004")
        await _ask(client, "ka10075")
        await _ask(client, "ka10075")
        await _ask(client, "kt00017")

    asyncio.run(tick())

    assert clock.slept == []
    assert [status for _, _, status in gate.seen] == [200, 200, 200, 200]


def test_queries_that_arrive_together_leave_one_spacing_apart(paced):
    """Two dashboard loads at once ask for the same query in the same instant."""

    client, gate, _ = paced()

    async def together():
        await asyncio.gather(*(_ask(client, "kt00015") for _ in range(3)))

    asyncio.run(together())

    assert [(at, status) for _, at, status in gate.seen] == [(0.0, 200), (1.2, 200), (2.4, 200)]


def test_a_refusal_caused_by_another_process_is_asked_again_once(paced):
    """The watcher and the dashboard run as separate processes on one app
    key. When the other one sent the same query a moment ago, ours is
    refused however well it paces itself; it asks again a spacing later."""

    client, gate, clock = paced(others_sent_at={"kt00004": 999.7})

    asyncio.run(_ask(client, "kt00004"))

    assert [(at, status) for _, at, status in gate.seen] == [(0.0, 429), (1.2, 200)]
    assert clock.slept == [1.2]


def test_a_query_refused_twice_is_reported_not_repeated_forever(paced):
    client, _, clock = paced()

    def always_refused(request: httpx.Request) -> httpx.Response:
        calls.append(request.headers["api-id"])
        return httpx.Response(429, text="Too Many Requests")

    calls: list[str] = []
    client._client = httpx.AsyncClient(
        base_url="https://example.invalid", transport=httpx.MockTransport(always_refused)
    )

    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(_ask(client, "kt00004"))
    assert calls == ["kt00004", "kt00004"]


def test_a_refused_query_off_the_list_is_left_to_its_caller(paced):
    """Market queries have their own three-attempt retry; an order must never
    be sent twice from here."""

    client, _, clock = paced()
    calls: list[str] = []

    def always_refused(request: httpx.Request) -> httpx.Response:
        calls.append(request.headers["api-id"])
        return httpx.Response(429, text="Too Many Requests")

    client._client = httpx.AsyncClient(
        base_url="https://example.invalid", transport=httpx.MockTransport(always_refused)
    )

    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(_ask(client, "kt10000"))
    assert calls == ["kt10000"] and clock.slept == []


def test_the_listed_queries_are_the_nineteen_of_the_notice():
    assert len(client_module.ONE_PER_SECOND_API_IDS) == 19
    # The two the watcher's order path depends on: the account read is
    # limited, the unfilled-orders read beside it is not.
    assert "kt00004" in client_module.ONE_PER_SECOND_API_IDS
    assert "ka10075" not in client_module.ONE_PER_SECOND_API_IDS
