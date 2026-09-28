"""Application configuration and settings management."""

from functools import lru_cache

from pydantic import Field, HttpUrl, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables or .env files."""

    appkey: str | None = Field(
        None,
        alias="KIWOOM_APPKEY",
        description="Kiwoom OpenAPI app key for the live trading environment",
    )
    secretkey: str | None = Field(
        None,
        alias="KIWOOM_SECRETKEY",
        description="Kiwoom OpenAPI secret key for the live trading environment",
    )
    mock_appkey: str | None = Field(
        None,
        alias="KIWOOM_MOCK_APPKEY",
        description="Kiwoom OpenAPI app key for the mock trading environment",
    )
    mock_secretkey: str | None = Field(
        None,
        alias="KIWOOM_MOCK_SECRETKEY",
        description="Kiwoom OpenAPI secret key for the mock trading environment",
    )
    base_url: HttpUrl = Field(
        "https://api.kiwoom.com",
        alias="KIWOOM_BASE_URL",
        description="Base URL for Kiwoom OpenAPI REST endpoints (production)",
    )
    mock_base_url: HttpUrl = Field(
        "https://mockapi.kiwoom.com",
        alias="KIWOOM_MOCK_BASE_URL",
        description="Base URL for Kiwoom OpenAPI mock endpoints (KRX only)",
    )
    token_endpoint: str = Field(
        "/oauth2/token",
        alias="KIWOOM_TOKEN_ENDPOINT",
        description="Relative path for token issuance",
    )
    use_mock: bool = Field(
        False,
        alias="KIWOOM_USE_MOCK",
        description="Whether to use mock API endpoint (for KRX testing)",
    )
    timeout_seconds: float = Field(10.0, description="HTTP client timeout in seconds")
    allow_direct_live_orders: bool = Field(
        False,
        alias="KIWOOM_ALLOW_DIRECT_LIVE_ORDERS",
        description="Allow live MCP/manual and legacy background orders outside the watcher risk gates",
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @model_validator(mode="after")
    def validate_selected_credentials(self) -> "Settings":
        """Ensure the active environment has the credentials it needs."""

        if self.use_mock:
            if not self.mock_appkey or not self.mock_secretkey:
                raise ValueError(
                    "KIWOOM_MOCK_APPKEY and KIWOOM_MOCK_SECRETKEY are required when KIWOOM_USE_MOCK=true"
                )
            return self

        if not self.appkey or not self.secretkey:
            raise ValueError(
                "KIWOOM_APPKEY and KIWOOM_SECRETKEY are required when KIWOOM_USE_MOCK=false"
            )

        return self

    @property
    def active_appkey(self) -> str:
        """Return the app key for the selected Kiwoom environment."""

        return self.mock_appkey if self.use_mock else self.appkey  # type: ignore[return-value]

    @property
    def active_secretkey(self) -> str:
        """Return the secret key for the selected Kiwoom environment."""

        return self.mock_secretkey if self.use_mock else self.secretkey  # type: ignore[return-value]

    @property
    def active_base_url(self) -> str:
        """Return the base URL for the selected Kiwoom environment."""

        return str(self.mock_base_url if self.use_mock else self.base_url)


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings instance."""

    return Settings()


__all__ = ["Settings", "get_settings"]
