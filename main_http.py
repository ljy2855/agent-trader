"""HTTP server entrypoint for running the Kiwoom MCP server."""

import asyncio
import os

from src.mcp_server import mcp_server


def _env_bool(name: str, default: bool = False) -> bool:
    """Parse a boolean environment variable."""

    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


async def _serve() -> None:
    """Start the HTTP server and optionally auto-start the trade engine."""

    host = os.getenv("KIWOOM_HTTP_HOST", "0.0.0.0")
    port = int(os.getenv("KIWOOM_HTTP_PORT", "8000"))

    if _env_bool("KIWOOM_BACKGROUND_AUTO_START", False):
        await mcp_server.start_background_engine(
            execute_orders=_env_bool("KIWOOM_BACKGROUND_EXECUTE_ORDERS", False),
            confirm_live_execution=_env_bool("KIWOOM_BACKGROUND_CONFIRM_LIVE_TRADING", False),
        )

    await mcp_server.mcp.run_http_async(
        host=host,
        port=port,
        path="/mcp",
        transport="streamable-http",
    )


def main() -> None:
    """Start the MCP server as HTTP server."""
    asyncio.run(_serve())


if __name__ == "__main__":
    main()
