#!/usr/bin/env python3
"""Forward today's autopilot-generated brief/wrap output to Discord.

The Multica autopilot creates an issue and triggers the PM agent. This
script polls that issue's latest completed run, extracts the agent
output (with the expected ACTION tag), and posts it to Discord.

Issue lookup strategies (preferred → fallback):

1. ``--autopilot <uuid>`` — query the autopilot's run history directly,
   pick today's completed run, follow ``run.issue_id``. This is the
   precise pairing and works even when Multica creates the issue with
   ``project_id=null`` (an orphan; the legacy ``--project`` filter
   misses those entirely).
2. ``--title-prefix "[Pre-open]"`` — list issues, match prefix +
   today's date. Used when ``--autopilot`` is omitted, or as a fallback
   if the autopilot's run history doesn't contain today's entry yet.

Usage::

    forward_autopilot_brief.py --autopilot <uuid> \\
        --required-action BRIEF_DONE \\
        --discord-title "Pre-Open Brief" --discord-emoji "🌅" \\
        --title-prefix "[Pre-open]"

Environment (set by the K8s CronJob via the kiwoom-watcher-env secret):

* ``MULTICA_BIN``           — path to multica CLI (default ``multica`` on PATH)
* ``KIWOOM_TRADING_MODE``   — "mock" | "live" (label only, doesn't switch)
* ``TRADING_MODE_LABEL``    — display label (e.g. ``🔴 LIVE``)
* ``DISCORD_WEBHOOK_URL``   — Discord webhook to POST into
* ``MULTICA_PROJECT``       — optional, used only by the title-prefix
  fallback path. The ``--autopilot`` path ignores it.

Exit codes:
* 0 — Discord message sent (with the agent output, even if ACTION tag missing)
* 0 — Discord message sent with a fallback warning when no issue/run found
* 0 — never raises in normal operation; logs failures to stderr

The script is best-effort by design — Discord errors must never page
oncall by crashing the CronJob.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))
# Digit-aware: TIER1/TIER2 carry a trailing digit, so `[A-Z_]+` would
# truncate them to "TIER". Used for both Discord forwarding and the
# end-of-day in_review cleanup.
ACTION_RE = re.compile(r"<!--\s*ACTION:\s*([A-Z0-9_]+)", re.IGNORECASE)

# Terminal ACTION tags that mark an issue as operationally resolved. An
# in_review issue from a past trading day carrying one of these can be
# auto-closed (status=done) — see `_close_resolved_issues`.
VALID_ACTIONS = frozenset(
    {
        "HOLD", "TRIM", "TAKE_PROFIT", "CUT_LOSS", "ROTATE", "ACKNOWLEDGE",
        "ESCALATE", "MITIGATE", "TIER1", "TIER2", "REJECT",
        "WRAP_DONE", "BRIEF_DONE",
    }
)

MULTICA_BIN = os.environ.get("MULTICA_BIN", "multica")
PROJECT = os.environ.get("MULTICA_PROJECT", "")
DAILY_LABEL = os.environ.get("TRADING_MODE_LABEL", "")
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")


def _today_kst() -> str:
    return datetime.now(KST).strftime("%Y-%m-%d")


def _err(msg: str) -> None:
    print(f"[forward_autopilot_brief] {msg}", file=sys.stderr)


def _run(args: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(
        [MULTICA_BIN, *args], capture_output=True, text=True, check=False
    )
    return proc.returncode, proc.stdout, proc.stderr


def _list_today_issues(title_prefix: str) -> list[dict]:
    """Find issues created today whose title starts with the given prefix.

    No ``--project`` filter — autopilot-created issues sometimes land
    with ``project_id=null`` (Multica CLI's ``autopilot update --project``
    doesn't seem to persist), and we want them found anyway.
    """

    today = _today_kst()
    # Sort by recency, not the default "position" (manual kanban order): the
    # API caps results at 100 regardless of --limit, so a position-ordered
    # page can miss today's issues entirely and the forwarder silently posts
    # nothing. Same defect the digest hit on 2026-07-24 (SWO-614). This call
    # is workspace-wide on purpose (see docstring), so its page is the most
    # crowded of any issue-list site here.
    rc, out, err = _run(
        [
            "issue",
            "list",
            "--output",
            "json",
            "--limit",
            "100",
            "--sort",
            "created_at",
            "--direction",
            "desc",
        ]
    )
    if rc != 0:
        _err(f"issue list failed: {err.strip()}")
        return []
    try:
        data = json.loads(out)
    except json.JSONDecodeError as exc:
        _err(f"issue list parse failed: {exc}")
        return []
    items = data if isinstance(data, list) else (data or {}).get("issues", [])
    matched: list[dict] = []
    for issue in items:
        title = issue.get("title") or ""
        created = issue.get("createdAt") or issue.get("created_at") or ""
        if not title.startswith(title_prefix):
            continue
        # Match either the title contains today's date OR the issue was
        # created today (autopilot template might not substitute date).
        if today in title or str(created).startswith(today):
            matched.append(issue)
    matched.sort(
        key=lambda i: i.get("createdAt") or i.get("created_at") or "",
        reverse=True,
    )
    return matched


def _autopilot_today_issue_id(autopilot_id: str) -> str | None:
    """Find the issue created by today's autopilot run.

    Queries ``multica autopilot runs <id>`` and picks the run whose
    ``triggered_at`` falls on today's KST date. Returns its ``issue_id``
    or ``None`` if no run fired today yet.
    """

    today = _today_kst()
    rc, out, err = _run(
        ["autopilot", "runs", autopilot_id, "--output", "json", "--limit", "20"]
    )
    if rc != 0:
        _err(f"autopilot runs {autopilot_id} failed: {err.strip()}")
        return None
    try:
        data = json.loads(out)
    except json.JSONDecodeError as exc:
        _err(f"autopilot runs parse failed: {exc}")
        return None
    runs = data if isinstance(data, list) else (data or {}).get("runs", [])
    # Convert UTC triggered_at to KST date and pick today's run (latest).
    candidates: list[tuple[str, dict]] = []
    for run in runs:
        if not isinstance(run, dict):
            continue
        triggered = run.get("triggered_at") or run.get("created_at") or ""
        if not triggered:
            continue
        try:
            dt = datetime.fromisoformat(triggered.replace("Z", "+00:00"))
        except ValueError:
            continue
        kst_date = dt.astimezone(KST).strftime("%Y-%m-%d")
        if kst_date == today:
            candidates.append((triggered, run))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1].get("issue_id")


def _fetch_issue_meta(issue_id: str) -> dict | None:
    rc, out, err = _run(["issue", "get", issue_id, "--output", "json"])
    if rc != 0:
        _err(f"issue get {issue_id} failed: {err.strip()}")
        return None
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return None
    # CLI returns the issue object at the top level for `issue get`.
    return data if isinstance(data, dict) else None


def _backfill_project(issue_id: str, project_id: str) -> bool:
    """Bind an autopilot-created orphan issue to the real-stock project.

    Autopilot's ``--project`` flag is silently dropped by the multica
    server (verified on 0.3.1), so every brief/wrap issue lands with
    ``project_id=null``. We patch it post-hoc so the issue is visible
    in the project's issue queue alongside watcher cycle traces.
    """

    rc, _out, err = _run(["issue", "update", issue_id, "--project", project_id, "--output", "json"])
    if rc != 0:
        _err(f"issue project backfill {issue_id} failed: {err.strip()}")
        return False
    return True


def _latest_completed_run(issue_id: str) -> dict | None:
    rc, out, err = _run(["issue", "runs", issue_id, "--output", "json"])
    if rc != 0:
        _err(f"issue runs {issue_id} failed: {err.strip()}")
        return None
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return None
    runs = data if isinstance(data, list) else (data or {}).get("runs", [])
    completed = [r for r in runs if isinstance(r, dict) and r.get("status") == "completed"]
    if not completed:
        return None
    completed.sort(key=lambda r: r.get("completed_at") or "", reverse=True)
    return completed[0]


def _latest_agent_comment(issue_id: str, *, agent_id: str | None, since: str | None) -> str | None:
    """Return the latest agent-authored comment body posted after the run started.

    The daily-wrap / pre-open-brief PM agent posts the actual content as an
    issue comment, not in run.result.output (output only contains narration
    + "Posted the daily-wrap comment..."). Fetch comments and prefer the
    one written by the assigned agent during this run.
    """

    rc, out, err = _run(
        ["issue", "comment", "list", issue_id, "--output", "json"]
    )
    if rc != 0:
        _err(f"issue comment list {issue_id} failed: {err.strip()}")
        return None
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return None
    items = data if isinstance(data, list) else (data or {}).get("comments", [])
    candidates: list[dict] = []
    for c in items:
        if not isinstance(c, dict):
            continue
        if agent_id and c.get("author_id") != agent_id:
            continue
        if since:
            created = c.get("created_at") or ""
            if created and created < since:
                continue
        candidates.append(c)
    if not candidates:
        return None
    candidates.sort(key=lambda c: c.get("created_at") or "", reverse=True)
    body = candidates[0].get("content") or candidates[0].get("body")
    return body if isinstance(body, str) and body.strip() else None


def _wait_for_run(issue_id: str, *, timeout_seconds: int, poll_seconds: int) -> dict | None:
    """Poll until a completed run exists or the timeout elapses."""

    deadline = time.time() + max(timeout_seconds, 1)
    while time.time() < deadline:
        run = _latest_completed_run(issue_id)
        if run is not None:
            return run
        time.sleep(poll_seconds)
    return _latest_completed_run(issue_id)


def _extract_action(text: str | None) -> str:
    if not text:
        return "NO_TAG"
    m = ACTION_RE.search(text)
    if not m:
        return "NO_TAG"
    return m.group(1).upper()


def _post_discord(title: str, description: str, *, color: int) -> None:
    if not WEBHOOK_URL:
        _err("DISCORD_WEBHOOK_URL not set — printing payload instead")
        print(f"[discord {title}]\n{description}")
        return
    if len(description) > 3900:
        description = description[:3897] + "..."
    payload = {
        "username": f"Kiwoom Brief {DAILY_LABEL}".strip(),
        "embeds": [
            {
                "title": title,
                "description": description,
                "color": color,
            }
        ],
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        WEBHOOK_URL,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            # Discord/Cloudflare returns 403 (error 1010) on the default
            # Python-urllib user-agent. Match send_discord_webhook.py.
            "User-Agent": "kiwoom-brief-forwarder/1.0",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status not in (200, 204):
                _err(f"discord status {resp.status}")
    except urllib.error.HTTPError as exc:
        _err(f"discord HTTP error {exc.code}: {exc.read()[:200]!r}")
    except urllib.error.URLError as exc:
        _err(f"discord network error: {exc}")


COLOR_INFO = 3447003
COLOR_SUCCESS = 3066993
COLOR_WARN = 16705372
COLOR_ERROR = 15158332


def _fmt_title(emoji: str, label: str) -> str:
    today = _today_kst()
    parts = [emoji, today]
    if DAILY_LABEL:
        parts.append(DAILY_LABEL)
    parts.append(label)
    return " ".join(p for p in parts if p)


def _issue_has_valid_action(issue_id: str) -> bool:
    """True if any comment on the issue carries a VALID_ACTIONS tag."""

    rc, out, _err = _run(
        ["issue", "comment", "list", issue_id, "--output", "json"]
    )
    if rc != 0:
        return False
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return False
    comments = data if isinstance(data, list) else data.get("comments", [])
    for c in comments:
        if not isinstance(c, dict):
            continue
        body = c.get("content") or c.get("body") or ""
        m = ACTION_RE.search(body)
        if m and m.group(1).upper() in VALID_ACTIONS:
            return True
    return False


def _close_resolved_issues() -> int:
    """Move resolved in_review issues from past trading days to done.

    Agents finish their run and post an ACTION comment but leave the issue
    in ``in_review``; without this they pile up indefinitely. We close only
    issues that are (a) created before today KST and (b) carry a terminal
    ACTION tag — today's issues stay open since their cycle may still be
    live. Idempotent: re-running closes nothing new.
    """

    if not PROJECT:
        _err("close-resolved skipped: MULTICA_PROJECT unset")
        return 0
    today = _today_kst()
    rc, out, err = _run(
        [
            "issue", "list", "--project", PROJECT,
            "--status", "in_review", "--limit", "200", "--output", "json",
        ]
    )
    if rc != 0:
        _err(f"close-resolved list failed: {err.strip()}")
        return 0
    try:
        issues = json.loads(out).get("issues", [])
    except (json.JSONDecodeError, AttributeError):
        return 0

    closed = 0
    for it in issues:
        created = it.get("created_at") or ""
        try:
            cdate = datetime.fromisoformat(
                created.replace("Z", "+00:00")
            ).astimezone(KST).strftime("%Y-%m-%d")
        except ValueError:
            cdate = created[:10]
        if cdate >= today:
            continue  # today's issues may still be active
        if not _issue_has_valid_action(it["id"]):
            continue  # unresolved — leave for manual review
        crc, _o, cerr = _run(["issue", "status", it["id"], "done"])
        if crc == 0:
            closed += 1
        else:
            _err(f"close-resolved status failed {it['id']}: {cerr.strip()}")
    if closed:
        _err(f"close-resolved: moved {closed} issue(s) to done")
    return closed


def _finish(args: argparse.Namespace, code: int = 0) -> int:
    """Run the optional end-of-day cleanup, then return ``code``.

    Cleanup runs regardless of whether forwarding succeeded so a wrap-agent
    timeout does not also block the inbox cleanup.
    """

    if getattr(args, "close_resolved", False):
        try:
            _close_resolved_issues()
        except Exception as exc:  # cleanup must never break the forwarder
            _err(f"close-resolved error: {exc}")
    return code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--autopilot",
        help=(
            "Autopilot UUID. Preferred lookup: query its run history and "
            "follow today's run.issue_id directly. Works even when the "
            "autopilot creates orphan (project_id=null) issues."
        ),
    )
    parser.add_argument(
        "--title-prefix",
        required=True,
        help=(
            "Issue title prefix (e.g. '[Pre-open]'). Used as fallback "
            "when --autopilot is not set or has no run today."
        ),
    )
    parser.add_argument(
        "--required-action",
        required=True,
        help="Expected ACTION tag (e.g. BRIEF_DONE)",
    )
    parser.add_argument("--discord-title", required=True)
    parser.add_argument("--discord-emoji", default="📝")
    parser.add_argument("--timeout-seconds", type=int, default=420)
    parser.add_argument("--poll-seconds", type=int, default=20)
    parser.add_argument(
        "--close-resolved",
        action="store_true",
        help=(
            "After forwarding, move resolved in_review issues from past "
            "trading days (with a terminal ACTION tag) to done. Intended "
            "for the post-market run so the issue inbox stays clean."
        ),
    )
    args = parser.parse_args()

    issue_id: str | None = None
    issue_title: str = "?"

    if args.autopilot:
        issue_id = _autopilot_today_issue_id(args.autopilot)
        if issue_id:
            meta = _fetch_issue_meta(issue_id)
            if meta:
                issue_title = meta.get("title") or issue_id

    if issue_id is None:
        # Fallback: title-prefix search (legacy path)
        issues = _list_today_issues(args.title_prefix)
        if not issues:
            _post_discord(
                _fmt_title(args.discord_emoji, args.discord_title),
                (
                    f"⚠️ 오늘 `{args.title_prefix}` 이슈를 찾지 못했습니다. "
                    f"Multica autopilot이 발화하지 않았거나 PM agent 트리거 실패입니다."
                ),
                color=COLOR_ERROR,
            )
            return _finish(args)
        issue = issues[0]
        issue_id = issue["id"]
        issue_title = issue.get("title") or issue_id
    run = _wait_for_run(
        issue_id,
        timeout_seconds=args.timeout_seconds,
        poll_seconds=args.poll_seconds,
    )
    if run is None:
        _post_discord(
            _fmt_title(args.discord_emoji, args.discord_title),
            (
                f"⚠️ PM agent 응답이 {args.timeout_seconds}초 내에 도착하지 않았습니다.\n"
                f"이슈: `{issue_title}` ({issue_id})"
            ),
            color=COLOR_WARN,
        )
        return _finish(args)

    run_output = (run.get("result") or {}).get("output") or ""
    # Prefer the agent's issue comment as the Discord body — the daily-wrap /
    # pre-open-brief PM posts the real content there and leaves only narration
    # in run.output. Fall back to run.output if no comment is available.
    meta = _fetch_issue_meta(issue_id) or {}
    assignee_id = meta.get("assignee_id") or meta.get("assigneeId")
    # Backfill project binding for orphan autopilot issues.
    if PROJECT and not (meta.get("project_id") or meta.get("projectId")):
        _backfill_project(issue_id, PROJECT)
    comment_body = _latest_agent_comment(
        issue_id,
        agent_id=str(assignee_id) if assignee_id else None,
        since=str(run.get("started_at") or "") or None,
    )
    output = comment_body if comment_body else run_output
    tag = _extract_action(output)

    if tag == args.required_action:
        color = COLOR_SUCCESS
    elif tag == "NO_TAG":
        color = COLOR_WARN
        output += "\n\n_(ACTION 태그 누락 — 그대로 전달함)_"
    else:
        color = COLOR_INFO
        output += f"\n\n_(예상 태그={args.required_action}, 도착={tag})_"

    _post_discord(
        _fmt_title(args.discord_emoji, args.discord_title),
        output,
        color=color,
    )
    return _finish(args)


if __name__ == "__main__":
    sys.exit(main())
