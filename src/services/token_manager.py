"""Token management for Kiwoom OpenAPI authentication."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Optional

from ..config import Settings, get_settings
from ..models import TokenIssueResponse


class TokenManager:
    """Manages Kiwoom OpenAPI tokens with automatic renewal."""

    def __init__(self, settings: Optional[Settings] = None):
        self._settings = settings or get_settings()
        self._token: Optional[str] = None
        self._token_type: Optional[str] = None
        self._expires_at: Optional[datetime] = None
        self._lock = asyncio.Lock()

    async def get_valid_token(self) -> str:
        """
        Get a valid access token, issuing a new one if needed.
        
        Returns:
            Valid access token string
            
        Raises:
            Exception: If token issuance fails
        """
        async with self._lock:
            if self._is_token_valid():
                return self._token

            # Token is expired or doesn't exist, get a new one
            await self._issue_new_token()
            return self._token

    def _is_token_valid(self) -> bool:
        """Check if current token is valid and not expired."""
        if not self._token or not self._expires_at:
            return False
        
        # Add 5 minute buffer before expiry
        buffer_time = timedelta(minutes=5)
        return datetime.now() + buffer_time < self._expires_at

    async def _issue_new_token(self) -> None:
        """Issue a new token from Kiwoom OpenAPI.

        Retries once on transient auth failures (return_code != 0): Kiwoom
        sometimes returns "인증에 실패했습니다" on the very first call
        after rotation, then succeeds on the immediate retry (SWO-183,
        2026-04-28). One retry covers that without masking persistent
        credential errors.
        """
        from .kiwoom_client import KiwoomClient

        last_error: str | None = None
        for attempt in (1, 2):
            client = KiwoomClient(self._settings)
            try:
                response = await client.request_access_token()
                if response.return_code != 0 or not response.token:
                    last_error = (
                        f"return_code={response.return_code} "
                        f"return_msg={response.return_msg!r}"
                    )
                    if attempt == 1:
                        # Brief backoff before retry — Kiwoom recovers within
                        # a couple hundred ms on transient auth failures.
                        await asyncio.sleep(0.5)
                        continue
                    raise Exception(f"Token issuance failed: {last_error}")

                self._token = response.token
                self._token_type = response.token_type
                # Parse expiration datetime (YYYYMMDDHHMMSS format)
                self._expires_at = datetime.strptime(
                    response.expires_dt, "%Y%m%d%H%M%S"
                )
                return
            finally:
                await client.close()

    async def force_refresh(self) -> str:
        """
        Force refresh the token regardless of current validity.
        
        Returns:
            New access token string
        """
        async with self._lock:
            await self._issue_new_token()
            return self._token

    async def invalidate(self) -> None:
        """Drop the currently cached token so the next call reissues it."""

        async with self._lock:
            self._token = None
            self._token_type = None
            self._expires_at = None

    def get_token_info(self) -> dict:
        """Get current token information for debugging."""
        return {
            "has_token": bool(self._token),
            "token_type": self._token_type,
            "expires_at": self._expires_at.isoformat() if self._expires_at else None,
            "is_valid": self._is_token_valid(),
            "expires_in_minutes": (
                (self._expires_at - datetime.now()).total_seconds() / 60 
                if self._expires_at and self._is_token_valid() 
                else 0
            ),
        }


# Global token manager instance
_token_manager: Optional[TokenManager] = None


def get_token_manager() -> TokenManager:
    """Get the global token manager instance."""
    global _token_manager
    if _token_manager is None:
        _token_manager = TokenManager()
    return _token_manager


__all__ = ["TokenManager", "get_token_manager"]
