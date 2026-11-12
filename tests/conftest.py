"""Suite-wide guards.

`market_context` is the one module that reaches outside Kiwoom (Yahoo, Cboe,
ECOS). The dashboard snapshot and the agent overview both call it, so without
a guard every test of those would open real connections. The suite's promise
is "no network": here every such request is refused, and a test that wants
data installs its own transport.
"""

from __future__ import annotations

import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.services import kiwoom_client, market_context  # noqa: E402


def _refuse(request: httpx.Request) -> httpx.Response:
    raise httpx.ConnectError("network is disabled in tests", request=request)


@pytest.fixture(autouse=True)
def _offline_market_context(monkeypatch):
    market_context.clear_cache()
    monkeypatch.setattr(
        market_context,
        "_http_client",
        lambda: httpx.AsyncClient(transport=httpx.MockTransport(_refuse)),
    )
    yield
    market_context.clear_cache()


@pytest.fixture(autouse=True)
def _fresh_account_query_pacing():
    """The spacing between account queries is kept per process. Left over
    from one test it would make the next one's first query wait."""

    kiwoom_client._next_send.clear()
    yield
    kiwoom_client._next_send.clear()
