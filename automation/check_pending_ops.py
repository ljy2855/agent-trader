#!/usr/bin/env python3
"""SessionStart hook — surface open `[점검 필요]` ops-handoff issues.

The daily ops digest (cloud CronJob) creates `[점검 필요]` multica issues
when it detects operational anomalies it cannot fix on its own. This hook
surfaces any open ones when the operator opens Claude Code locally, so the
cloud→local handoff is visible without polling Discord.

Fast + fail-safe: any error (multica missing, network, parse) exits 0
silently so it never blocks or slows a session beyond the multica call.

Query shape matters here. A single unfiltered `issue list` is *not* a
complete view: the API caps results at 100 regardless of `--limit`, and the
default `position` sort is manual kanban order, unrelated to recency.

Filter by status, not by date. The digest can sort `created_at desc`
because it is always today-scoped, but this hook's predicate is itself a
status predicate — "not done, not cancelled" — and querying that axis
directly bounds the result by the *open* set, which stays small however
much the project churns. Any date- or position-ordered page is a window
whose reach shrinks as issues accumulate, so it can only ever be lucky.

Seen 2026-08-28: SWO-687 (`[점검 필요]`, todo, high, created 08-12) was
invisible to this hook for 16 days. ~100 issues of routine churn had
pushed it out of the position-ordered page, and the newest-100 page
reached back only to 08-13 — but that boundary is a fact about current
volume, not about the bug.
"""

from __future__ import annotations

import concurrent.futures
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Statuses that mean "still needs a human". Queried explicitly rather than
# derived by excluding terminal ones, because an unfiltered list can't be
# trusted to be complete (see module docstring). `blocked` is here because
# the drift probe below found it on the first run — the list is only as
# good as the workspace it was written against, which is why the probe stays.
OPEN_STATUSES = ("todo", "in_progress", "in_review", "blocked")
TERMINAL_STATUSES = ("done", "cancelled")


def _project_id() -> str | None:
    v = os.environ.get("MULTICA_PROJECT")
    if v:
        return v
    # Fall back to parsing trading_env.sh next to this script (the hook runs
    # in a fresh shell where trading_env.sh hasn't been sourced).
    env = Path(__file__).resolve().parent / "trading_env.sh"
    try:
        for line in env.read_text().splitlines():
            m = re.match(r"\s*export\s+MULTICA_PROJECT=([^\s#]+)", line)
            if m:
                return m.group(1).strip().strip('"').strip("'")
    except OSError:
        pass
    return None


def _list_issues(binary: str, pid: str, *extra: str) -> list[dict]:
    """One `issue list` call. Any failure yields [] — never raises."""
    try:
        out = subprocess.run(
            [binary, "issue", "list", "--project", pid,
             "--limit", "100", "--output", "json", *extra],
            capture_output=True, text=True, timeout=10, check=False,
        ).stdout
        items = json.loads(out).get("issues", [])
    except Exception:
        return []
    return [it for it in items if isinstance(it, dict)]


def collect_pending(binary: str, pid: str) -> tuple[list[dict], set[str]]:
    """Open `[점검 필요]` issues, plus any status values we don't enumerate.

    Runs one query per open status plus a recency-sorted probe, unioned by
    issue id. The probe is what makes status drift visible: if multica ever
    renames or adds a status, the filtered queries would quietly return
    nothing and this hook would go silent again — the exact failure it
    exists to prevent. Queries run concurrently so the hook still costs
    about one round-trip.
    """

    queries: list[tuple[str, ...]] = [("--status", s) for s in OPEN_STATUSES]
    queries.append(("--sort", "created_at", "--direction", "desc"))

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(queries)) as pool:
        results = list(pool.map(lambda q: _list_issues(binary, pid, *q), queries))

    known = set(OPEN_STATUSES) | set(TERMINAL_STATUSES)
    unknown: set[str] = set()
    merged: dict[str, dict] = {}
    for items in results:
        for it in items:
            status = str(it.get("status") or "")
            if status and status not in known:
                unknown.add(status)
            key = str(it.get("id") or it.get("identifier") or "")
            if key:
                merged[key] = it

    pending = [
        it for it in merged.values()
        if str(it.get("title", "")).startswith("[점검 필요]")
        and it.get("status") not in TERMINAL_STATUSES
    ]
    pending.sort(key=lambda it: str(it.get("created_at") or ""))
    return pending, unknown


def main() -> int:
    pid = _project_id()
    if not pid:
        return 0
    binary = os.environ.get("MULTICA_BIN") or shutil.which("multica") \
        or "/opt/homebrew/bin/multica"
    try:
        pend, unknown = collect_pending(binary, pid)
    except Exception:
        return 0

    if unknown:
        print(
            "ℹ️ multica에 모르는 이슈 상태가 있습니다: "
            f"{', '.join(sorted(unknown))} — check_pending_ops.py의 "
            "OPEN_STATUSES 갱신 필요 여부 확인"
        )
    if not pend:
        return 0

    print(f"⚠️ 미처리 운영 점검 {len(pend)}건 (daily ops digest 핸드오프):")
    for it in pend[:10]:
        # Print the issue key, not a truncated UUID: multica 0.4.9 rejects
        # short prefixes ("short prefixes are no longer supported"), so the
        # `issue status` line below used to fail exactly as printed.
        ref = it.get("identifier") or it.get("id")
        print(f"  - {it.get('title')} [{it.get('status')}] {ref}")
    print("처리: 조사 후 수정 적용 → `multica issue status <key> done` 으로 닫기")
    return 0


if __name__ == "__main__":
    sys.exit(main())
