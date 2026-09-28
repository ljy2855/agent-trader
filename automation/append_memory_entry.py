#!/usr/bin/env python3
"""Append a timestamped run summary to the KRX Paper Trader memory file.

Memory is split per trading mode (2026-04-28, SWO-178): cross-mode memory
pollution caused the live cycle to compare today's real account against
yesterday's mock holdings, triggering a false "포지션 대변화" alarm. Each
mode now writes to its own file:

  - mock → automation/memory_mock.md
  - live → automation/memory_live.md

The legacy ``memory.md`` is kept as a symlink target so older runs and
human-read history still resolve. Override with ``--memory-file`` if you
need to write somewhere specific.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

AUTOMATION_DIR = Path(__file__).resolve().parent
KST = ZoneInfo("Asia/Seoul")


def _default_memory_path() -> Path:
    """Pick the right memory file for the current trading mode.

    Falls back to the legacy ``memory.md`` when KIWOOM_TRADING_MODE is unset
    so callers that haven't sourced ``trading_env.sh`` still work.
    """

    mode = (os.environ.get("KIWOOM_TRADING_MODE") or "").strip().lower()
    if mode == "live":
        return AUTOMATION_DIR / "memory_live.md"
    if mode == "mock":
        return AUTOMATION_DIR / "memory_mock.md"
    return AUTOMATION_DIR / "memory.md"


DEFAULT_MEMORY_PATH = _default_memory_path()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Append a run summary to automation memory.")
    parser.add_argument(
        "--memory-file",
        default=None,
        help=(
            "Target memory file path. Defaults to memory_{mode}.md based on "
            "KIWOOM_TRADING_MODE (live/mock), or legacy memory.md if unset."
        ),
    )
    parser.add_argument(
        "--timestamp",
        help="Optional preformatted timestamp header, e.g. '2026-03-31 10:05:00 KST'.",
    )
    return parser


def read_summary() -> str:
    if sys.stdin.isatty():
        raise SystemExit("Provide the run summary via stdin.")
    summary = sys.stdin.read().strip()
    if not summary:
        raise SystemExit("Run summary is empty.")
    return summary


def ensure_header(path: Path) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# KRX Paper Trader Memory\n", encoding="utf-8")


def append_entry(path: Path, summary: str, timestamp: str) -> None:
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    chunk = f"\n\n## {timestamp}\n{summary.rstrip()}\n"
    if not existing:
        path.write_text(f"# KRX Paper Trader Memory{chunk}", encoding="utf-8")
        return
    with path.open("a", encoding="utf-8") as handle:
        handle.write(chunk)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    memory_path = Path(args.memory_file).expanduser() if args.memory_file else _default_memory_path()
    summary = read_summary()
    timestamp = args.timestamp or datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S KST")

    ensure_header(memory_path)
    append_entry(memory_path, summary, timestamp)
    print(f"Appended run summary to {memory_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
