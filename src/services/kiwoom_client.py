"""HTTP client wrapper around the Kiwoom OpenAPI."""

from __future__ import annotations

import re
import uuid
from typing import Any

import httpx

from ..config import Settings
from ..models import TokenIssueResponse
from ..constants import OAUTH_APIS
from .token_manager import TokenManager, get_token_manager


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


# Kiwoom reports auth failures two ways: a specific top-level `return_code`,
# or a generic one (3, 5, ..., 805004) with the real code embedded in the
# message. The embedding differs by transport:
#
#   REST      `인증에 실패했습니다[8005:Token이 유효하지 않습니다]`
#   WebSocket `... [CODE=8005, MESSAGE=Token이 유효하지 않습니다]`
#
# Both forms are live. Only the REST one was matched until 2026-09-05, when
# the realtime socket spent a weekend retrying a stale token 977 times: its
# rejection carries `CODE=8005`, so the expiry went unrecognised and the same
# cached token was replayed every 30 seconds.
_EMBEDDED_RETURN_CODE_RE = re.compile(r"\[(\d{3,5}):|CODE=(\d{3,5})")

# Codes that mean "this token is no longer usable", where reissuing and
# retrying once is the right move. Sourced from the code tables published in
# Kiwoom's official API repository (Kiwoom-Securities/Kiwoom-REST-API,
# kiwoom/core/errors.py) and re-expressed here rather than imported: that
# package is licensed for use with the service but not for modification or
# redistribution, and this image is redistributed to the cluster.
#
# We previously knew only 8005 and otherwise matched Korean message text,
# which missed the embedded form entirely and would break silently if Kiwoom
# reworded anything.
_TOKEN_EXPIRED_CODES = frozenset({8003, 8005, 8006, 8009, 8015, 8016})

# Deliberately *not* retried: the credentials are wrong (8001/8002/8011/8012)
# or the account is in the wrong mode (8030/8031). Reissuing cannot fix
# either, so a retry just doubles the failed calls -- and on the order path
# every extra call is another chance to double-submit.


def embedded_return_code(return_msg: Any) -> int | None:
    """The specific code Kiwoom embeds in a message, when there is one."""

    match = _EMBEDDED_RETURN_CODE_RE.search(str(return_msg or ""))
    if match is None:
        return None
    return int(match.group(1) or match.group(2))


def is_auth_expiry_code(return_code: Any, return_msg: Any = "") -> bool:
    """Does this failure mean "reissue the token and try again"?

    Shared with the realtime WebSocket, which authenticates outside the HTTP
    client but fails the same way and needs the same verdict.
    """

    code = _normalize_return_code(return_code)
    if code in _TOKEN_EXPIRED_CODES:
        return True
    return embedded_return_code(return_msg) in _TOKEN_EXPIRED_CODES


def _is_token_invalid_payload(payload: Any) -> bool:
    """Detect Kiwoom business-level token invalid responses."""

    if not isinstance(payload, dict):
        return False

    return_code = _normalize_return_code(payload.get("return_code"))
    return_msg = str(payload.get("return_msg") or payload.get("msg") or "")
    if return_code in _TOKEN_EXPIRED_CODES:
        return True
    if embedded_return_code(return_msg) in _TOKEN_EXPIRED_CODES:
        return True
    # Message fallbacks, kept for shapes that carry neither code.
    if "Token이 유효하지 않습니다" in return_msg:
        return True
    return "인증에 실패했습니다" in return_msg and "Token" in return_msg


def _response_has_invalid_token(response: httpx.Response) -> bool:
    """Detect invalid-token responses from either HTTP or business status."""

    if response.status_code in {401, 403}:
        return True
    try:
        payload = response.json()
    except ValueError:
        return False
    return _is_token_invalid_payload(payload)


class KiwoomClient:
    """Thin client responsible for talking to the Kiwoom OpenAPI endpoints."""

    def __init__(
        self,
        settings: Settings,
        *,
        token_manager: TokenManager | None = None,
        http_client: httpx.AsyncClient | None = None,
    ):
        self._settings = settings
        self._token_manager = token_manager or get_token_manager()
        self._owns_client = http_client is None
        self._client = http_client or httpx.AsyncClient(
            base_url=settings.active_base_url,
            timeout=settings.timeout_seconds,
            headers={"User-Agent": f"kiwoom-mcp/{uuid.uuid4()}"},
        )

    async def close(self) -> None:
        """Close the underlying HTTP session."""

        if self._owns_client:
            await self._client.aclose()

    async def request_access_token(
        self,
        *,
        grant_type: str = "client_credentials",
    ) -> TokenIssueResponse:
        """Issue an OAuth token using the configured appkey and secretkey."""

        payload = {
            "grant_type": grant_type,
            "appkey": self._settings.active_appkey,
            "secretkey": self._settings.active_secretkey,
        }

        # Get token issuance API info
        token_api = OAUTH_APIS["TOKEN_ISSUE"]
        
        # Kiwoom API requires specific headers
        headers = {
            "api-id": token_api.api_id,
            "Content-Type": "application/json; charset=UTF-8",
        }

        response = await self._client.post(
            token_api.url,
            json=payload,
            headers=headers,
        )
        response.raise_for_status()
        return TokenIssueResponse.model_validate(response.json())

    async def revoke_token(self, *, token: str, token_type_hint: str | None = None) -> None:
        """Revoke a previously issued token (placeholder - Kiwoom API may not support this)."""

        # Note: Kiwoom API documentation doesn't show a revoke endpoint
        # This is a placeholder for potential future implementation
        payload: dict[str, Any] = {"token": token}
        if token_type_hint:
            payload["token_type_hint"] = token_type_hint

        # For now, just raise an error indicating this feature is not available
        raise NotImplementedError("Token revocation is not yet implemented for Kiwoom OpenAPI")

    def _build_auth_headers(
        self,
        token: str,
        additional_headers: dict[str, str] | None = None,
    ) -> dict[str, str]:
        """Compose the request headers for an authenticated Kiwoom call."""

        headers = {
            "Content-Type": "application/json; charset=UTF-8",
            "authorization": f"Bearer {token}",
        }

        if additional_headers:
            headers.update(additional_headers)

        return headers

    async def _request_with_auth_retry(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Send an authenticated request and retry once after token invalidation."""

        token = await self._token_manager.get_valid_token()
        auth_headers = self._build_auth_headers(token, headers)
        response = await self._client.request(
            method,
            path,
            headers=auth_headers,
            params=params,
            json=json,
            data=data,
        )

        if _response_has_invalid_token(response):
            await self._token_manager.invalidate()
            refreshed_token = await self._token_manager.force_refresh()
            retry_headers = self._build_auth_headers(refreshed_token, headers)
            response = await self._client.request(
                method,
                path,
                headers=retry_headers,
                params=params,
                json=json,
                data=data,
            )

        response.raise_for_status()
        return response

    async def get(self, path: str, *, headers: dict[str, str] | None = None, params: dict[str, Any] | None = None) -> httpx.Response:
        """Perform a GET request against the Kiwoom OpenAPI with automatic authentication."""

        return await self._request_with_auth_retry(
            "GET",
            path,
            headers=headers,
            params=params,
        )

    @property
    def token_manager(self) -> TokenManager:
        """The token source, for callers that authenticate outside HTTP.

        The realtime WebSocket sends the access token in its LOGIN frame, so
        it needs the same managed token this client uses rather than issuing
        one of its own.
        """

        return self._token_manager

    async def post(
        self,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Perform a POST request against the Kiwoom OpenAPI with automatic authentication."""

        return await self._request_with_auth_retry(
            "POST",
            path,
            headers=headers,
            params=params,
            json=json,
            data=data,
        )


__all__ = ["KiwoomClient"]
