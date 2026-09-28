"""Authentication-related request and response models for Kiwoom OpenAPI."""

from pydantic import BaseModel, Field


class TokenIssueRequest(BaseModel):
    """Request payload for Kiwoom OAuth token issuance."""

    grant_type: str = Field(
        "client_credentials",
        description="OAuth grant type - must be 'client_credentials'",
    )
    appkey: str = Field(description="Kiwoom OpenAPI app key")
    secretkey: str = Field(description="Kiwoom OpenAPI secret key")


class TokenIssueResponse(BaseModel):
    """Response from Kiwoom OAuth token issuance API.

    On the success path Kiwoom returns return_code=0 plus expires_dt /
    token_type / token. On auth failures (e.g. transient
    "인증에 실패했습니다", return_code=3) those three credential fields
    are absent — making them required would crash pydantic validation
    before the caller can read return_msg, masking the real error
    behind a confusing ValidationError (SWO-183, 2026-04-28).
    """

    expires_dt: str = Field(
        default="", description="Token expiration datetime (YYYYMMDDHHMMSS format)"
    )
    token_type: str = Field(default="", description="Token type, typically 'bearer'")
    token: str = Field(default="", description="Access token for API calls")
    return_code: int = Field(description="Return code from Kiwoom API (0 for success)")
    return_msg: str = Field(description="Return message from Kiwoom API")


class TokenRevokeRequest(BaseModel):
    """Request payload for token revocation (placeholder for future implementation)."""

    token: str = Field(description="Previously issued token to revoke")
    token_type_hint: str | None = Field(
        default=None,
        description="Optional hint (e.g. 'access_token' or 'refresh_token')",
    )
