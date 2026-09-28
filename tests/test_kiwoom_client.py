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
