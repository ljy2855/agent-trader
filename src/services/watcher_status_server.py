"""Read-only HTTP endpoints exposing the watcher's runtime state.

Mounted alongside the watcher loop in ``main_watcher.py`` when
``--status-port`` is set. The dashboard polls these endpoints to render
the agent overview panel.

Endpoints (all GET, JSON):

* ``/state``   — current snapshot (cycle, regime, in_flight, mode, errors)
* ``/recent``  — recent trigger fire history (newest first)
* ``/ledger``  — order-intent ledger: unresolved + recent intents + audit
* ``/health``  — cheap liveness probe ({"ok": true})

This service is ClusterIP only. `/ledger` reaches the agents through the MCP
server's `get_order_ledger` tool, not through a public `/api/*` route — the
dashboard host is reachable from the internet.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from .watcher_status import WatcherStatusRegistry

LedgerView = Callable[..., dict[str, Any]]


def build_status_app(
    registry: WatcherStatusRegistry, *, ledger_view: LedgerView | None = None
) -> Starlette:
    """Build a small Starlette app reading from the given registry."""

    async def state(_: Request) -> JSONResponse:
        return JSONResponse(registry.snapshot())

    async def recent(request: Request) -> JSONResponse:
        try:
            limit = int(request.query_params.get("limit", "100"))
        except ValueError:
            limit = 100
        limit = max(1, min(limit, 500))
        return JSONResponse({"items": registry.recent(limit=limit)})

    async def health(_: Request) -> JSONResponse:
        return JSONResponse({"ok": True})

    async def ledger(request: Request) -> JSONResponse:
        if ledger_view is None:
            return JSONResponse(
                {"available": False, "error": "ledger view not wired"}, status_code=503
            )
        try:
            limit = int(request.query_params.get("limit", "50"))
        except ValueError:
            limit = 50
        trading_day = request.query_params.get("trading_day") or None
        return JSONResponse(ledger_view(limit=limit, trading_day=trading_day))

    return Starlette(
        routes=[
            Route("/state", endpoint=state),
            Route("/recent", endpoint=recent),
            Route("/ledger", endpoint=ledger),
            Route("/health", endpoint=health),
        ]
    )


__all__ = ["build_status_app"]
