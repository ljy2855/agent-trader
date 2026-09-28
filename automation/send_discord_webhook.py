#!/usr/bin/env python3
"""Send a message to Discord via webhook."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Send Discord webhook messages from terminal workflows."
    )
    parser.add_argument("--webhook-url", help="Discord webhook URL. Defaults to DISCORD_WEBHOOK_URL.")
    parser.add_argument("--content", help="Message body text.")
    parser.add_argument("--content-file", help="Read message body from a file.")
    parser.add_argument("--username", help="Override webhook username.")
    parser.add_argument("--avatar-url", help="Override webhook avatar URL.")
    parser.add_argument("--tts", action="store_true", help="Enable text-to-speech.")
    parser.add_argument("--embed-title", help="Embed title.")
    parser.add_argument("--embed-description", help="Embed description.")
    parser.add_argument(
        "--embed-color",
        type=int,
        help="Embed color as decimal integer (e.g., 3066993).",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print payload and skip sending.")
    return parser


def resolve_content(args: argparse.Namespace) -> str | None:
    if args.content and args.content_file:
        raise ValueError("Use only one of --content or --content-file.")

    if args.content:
        return args.content

    if args.content_file:
        with open(args.content_file, "r", encoding="utf-8") as f:
            return f.read().strip()

    if not sys.stdin.isatty():
        return sys.stdin.read().strip()

    return None


def build_payload(args: argparse.Namespace, content: str | None) -> dict:
    payload: dict[str, object] = {}

    if content:
        payload["content"] = content
    if args.username:
        payload["username"] = args.username
    if args.avatar_url:
        payload["avatar_url"] = args.avatar_url
    if args.tts:
        payload["tts"] = True

    if args.embed_title or args.embed_description or args.embed_color is not None:
        embed: dict[str, object] = {}
        if args.embed_title:
            embed["title"] = args.embed_title
        if args.embed_description:
            embed["description"] = args.embed_description
        if args.embed_color is not None:
            embed["color"] = args.embed_color
        payload["embeds"] = [embed]

    if not payload:
        raise ValueError("No message content found. Provide --content, --content-file, or stdin.")

    return payload


def send(webhook_url: str, payload: dict) -> tuple[int, str]:
    parsed = urllib.parse.urlparse(webhook_url)
    if parsed.scheme != "https" or "discord.com/api/webhooks/" not in parsed.geturl():
        raise ValueError("Invalid Discord webhook URL.")

    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "User-Agent": "discord-message-sender/1.0",
            "Accept": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            text = response.read().decode("utf-8", errors="replace")
            return response.status, text
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Discord API error {e.code}: {detail}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Network error: {e}") from e


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    webhook_url = args.webhook_url or os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        parser.error("Provide --webhook-url or set DISCORD_WEBHOOK_URL.")

    try:
        content = resolve_content(args)
        payload = build_payload(args, content)
    except (OSError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2

    if args.dry_run:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    try:
        status, response_text = send(webhook_url, payload)
    except (RuntimeError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if status in (200, 204):
        print(f"Sent Discord message successfully (HTTP {status}).")
        if response_text.strip():
            print(response_text)
        return 0

    print(f"Unexpected status code: {status}", file=sys.stderr)
    if response_text.strip():
        print(response_text, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
