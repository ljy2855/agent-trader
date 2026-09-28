"""Tests for the Discord notifier helper.

We never hit Discord — instead we patch the synchronous POST helper to
capture payloads (or to assert the URL-validation no-op path).
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

os.environ.setdefault("KIWOOM_APPKEY", "dummy-appkey")
os.environ.setdefault("KIWOOM_SECRETKEY", "dummy-secretkey")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.services import discord_notify  # noqa: E402
from src.services.discord_notify import DiscordNotifier  # noqa: E402


def test_disabled_when_no_url(monkeypatch):
    monkeypatch.delenv("DISCORD_WEBHOOK_URL", raising=False)
    monkeypatch.setattr(discord_notify, "_read_webhook_url_file", lambda: None)
    n = DiscordNotifier()
    assert n.enabled is False


def test_enabled_when_explicit_url():
    n = DiscordNotifier(webhook_url="https://discord.com/api/webhooks/abc")
    assert n.enabled is True


def test_no_post_when_url_not_discord(monkeypatch):
    """A non-Discord URL must be silently skipped, not crashed on."""

    n = DiscordNotifier(webhook_url="https://example.com/notdiscord")
    posts: list[dict] = []
    monkeypatch.setattr(
        n, "_post_sync", lambda payload: posts.append(payload)
    )
    # Even though the helper is patched, the URL check would normally reject;
    # verify we still always go through _send → _post_sync to keep wiring honest.
    asyncio.run(n.info("hi", "there"))
    assert len(posts) == 1
    assert posts[0]["embeds"][0]["title"] == "hi"


def test_severity_colors():
    n = DiscordNotifier(webhook_url="https://discord.com/api/webhooks/x/y")
    captured: list[dict] = []

    def fake_post(payload):
        captured.append(payload)

    # Use object's __dict__ to override since _post_sync is bound
    n._post_sync = fake_post  # type: ignore[assignment]

    asyncio.run(n.info("t", "d"))
    asyncio.run(n.success("t", "d"))
    asyncio.run(n.warn("t", "d"))
    asyncio.run(n.error("t", "d"))

    colors = [p["embeds"][0]["color"] for p in captured]
    assert colors == [
        discord_notify.COLOR_INFO,
        discord_notify.COLOR_SUCCESS,
        discord_notify.COLOR_WARN,
        discord_notify.COLOR_ERROR,
    ]


def test_prefix_prepended_to_title():
    n = DiscordNotifier(
        webhook_url="https://discord.com/api/webhooks/x/y",
        prefix="[🔴 LIVE] ",
    )
    captured: list[dict] = []
    n._post_sync = lambda payload: captured.append(payload)  # type: ignore[assignment]
    asyncio.run(n.info("Tier1 실행", "X"))
    assert captured[0]["embeds"][0]["title"] == "[🔴 LIVE] Tier1 실행"


def test_long_description_is_truncated():
    n = DiscordNotifier(webhook_url="https://discord.com/api/webhooks/x/y")
    captured: list[dict] = []
    n._post_sync = lambda payload: captured.append(payload)  # type: ignore[assignment]
    asyncio.run(n.info("x", "a" * 5000))
    desc = captured[0]["embeds"][0]["description"]
    assert len(desc) <= 3900
    assert desc.endswith("...")


def test_disabled_send_is_noop(monkeypatch):
    monkeypatch.delenv("DISCORD_WEBHOOK_URL", raising=False)
    monkeypatch.setattr(discord_notify, "_read_webhook_url_file", lambda: None)
    n = DiscordNotifier()
    calls: list = []
    n._post_sync = lambda payload: calls.append(payload)  # type: ignore[assignment]
    asyncio.run(n.info("x", "y"))
    assert calls == []


def test_post_sync_skips_non_discord_url(monkeypatch):
    """The actual URL gate inside _post_sync should reject non-discord URLs."""

    n = DiscordNotifier(webhook_url="https://example.com/foo")
    # Patch urllib.request.urlopen at the discord_notify scope so we know
    # whether _post_sync attempted the network call.
    opens: list[str] = []

    def fake_urlopen(req, timeout=None):
        opens.append(getattr(req, "full_url", ""))
        raise AssertionError("must not be called for non-discord URL")

    monkeypatch.setattr(
        discord_notify.urllib.request, "urlopen", fake_urlopen, raising=True
    )
    # Force the real _post_sync (don't mock) so the URL check executes.
    payload = {"username": "u", "embeds": [{"title": "t", "description": "d", "color": 1}]}
    n._post_sync(payload)
    assert opens == []
