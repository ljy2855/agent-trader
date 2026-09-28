"""Lightweight Discord webhook notifier for the watcher.

The webhook URL is sourced (in priority order) from:

1. The constructor argument ``webhook_url``
2. ``$DISCORD_WEBHOOK_URL`` environment variable
3. ``automation/discord_webhook_url`` file contents (matching the
   convention used by ``automation/send_discord_summary.sh``)

If none of these resolve, the notifier becomes a no-op so the watcher
can run in environments without Discord without crashing. All HTTP work
is offloaded to a worker thread via ``asyncio.to_thread`` so the main
loop stays responsive.

Severity colors mirror ``automation/send_discord_summary.sh`` so the
visual language is consistent across the existing scheduled tasks and
the new continuous watcher.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger("kiwoom.watcher.discord")


COLOR_INFO = 3447003     # blue
COLOR_SUCCESS = 3066993  # green
COLOR_WARN = 16705372    # yellow
COLOR_ERROR = 15158332   # red


@dataclass(slots=True)
class _Embed:
    title: str
    description: str
    color: int


def _read_webhook_url_file() -> str | None:
    """Read ``automation/discord_webhook_url`` if present."""

    candidate = (
        Path(__file__).resolve().parents[2] / "automation" / "discord_webhook_url"
    )
    try:
        if candidate.is_file():
            text = candidate.read_text(encoding="utf-8").strip()
            return text or None
    except OSError:
        return None
    return None


def _resolve_webhook_url(explicit: str | None) -> str | None:
    if explicit:
        return explicit
    env_value = os.environ.get("DISCORD_WEBHOOK_URL")
    if env_value:
        return env_value
    return _read_webhook_url_file()


class DiscordNotifier:
    """Async-friendly Discord webhook sender. No-op when unconfigured."""

    def __init__(
        self,
        *,
        webhook_url: str | None = None,
        username: str = "Kiwoom Watcher",
        prefix: str = "",
    ):
        self._webhook_url = _resolve_webhook_url(webhook_url)
        self._username = username
        self._prefix = prefix or ""

    @property
    def enabled(self) -> bool:
        return bool(self._webhook_url)

    async def info(self, title: str, description: str) -> None:
        await self._send(_Embed(title, description, COLOR_INFO))

    async def success(self, title: str, description: str) -> None:
        await self._send(_Embed(title, description, COLOR_SUCCESS))

    async def warn(self, title: str, description: str) -> None:
        await self._send(_Embed(title, description, COLOR_WARN))

    async def error(self, title: str, description: str) -> None:
        await self._send(_Embed(title, description, COLOR_ERROR))

    # -- internals ------------------------------------------------------------

    async def _send(self, embed: _Embed) -> None:
        if not self._webhook_url:
            return
        full_title = f"{self._prefix}{embed.title}" if self._prefix else embed.title
        # Discord embed description hard cap is 4096; keep some headroom.
        description = embed.description or ""
        if len(description) > 3900:
            description = description[:3897] + "..."
        payload = {
            "username": self._username,
            "embeds": [
                {
                    "title": full_title,
                    "description": description,
                    "color": embed.color,
                }
            ],
        }
        try:
            await asyncio.to_thread(self._post_sync, payload)
        except Exception as exc:
            # Notifier failures must never break the watcher loop.
            log.warning("discord notify failed: %s", exc)

    def _post_sync(self, payload: dict) -> None:
        url = self._webhook_url or ""
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != "https" or "discord.com/api/webhooks/" not in url:
            log.warning("discord webhook URL is not a discord.com URL — skipping")
            return
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "User-Agent": "kiwoom-watcher/1.0",
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status not in (200, 204):
                    log.warning(
                        "discord webhook returned status %s", response.status
                    )
        except urllib.error.HTTPError as exc:
            log.warning("discord HTTP error %s", exc.code)
        except urllib.error.URLError as exc:
            log.warning("discord network error: %s", exc)


__all__ = [
    "COLOR_ERROR",
    "COLOR_INFO",
    "COLOR_SUCCESS",
    "COLOR_WARN",
    "DiscordNotifier",
]
