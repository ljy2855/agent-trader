"""Every `multica issue list` call: the page it asks for, and what is on it.

Captured 2026-11-14 against the live server, with the CLI the image carried
(0.4.9) and the one the agent host had just moved to (0.9.0):

* One answer holds at most 100 rows. 0.4.9 passed a larger `--limit` on and
  got 100 back; 0.9.0 refuses it before asking, with LIMIT_REFUSAL. Four call
  sites asked for 200, so each would have read "no issues" from the new CLI.
* Without `--sort` the rows come in board order: by `position`, ascending, and
  each status numbers its own column. The closed issues stood at -454 and up,
  the two open ones at -29 and -28 — behind every one of them. The watcher's
  own lookup did not sort, so the issue it had made that morning was on no
  page it asked for, whichever CLI it used.
"""

from __future__ import annotations

import asyncio
import importlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "automation"))

from src import agent_overview  # noqa: E402
from src.services import multica_dispatch as md  # noqa: E402

digest = importlib.import_module("daily_ops_digest")
fab = importlib.import_module("forward_autopilot_brief")

LIMIT_REFUSAL = (
    "--limit must be between 1 and 100 (the server returns at most 100 issues per request); "
    "use --offset to page through more"
)
KST = timezone(timedelta(hours=9))
NOW = datetime(2026, 11, 16, 10, 0, tzinfo=KST)
TODAY = "2026-11-16"
DAILY_TITLE = f"{TODAY} {md.DEFAULT_DAILY_SUFFIX}"
RISK_TITLE = f"[리스크] {TODAY} 리스크 알림"
OPS_TITLE = f"[점검 필요] {TODAY} 운영 이상"


def _row(number, title, *, status, position, created_at, assignee=None, parent=None):
    """One `issue list` row, with the keys of the server's that callers read."""

    return {
        "id": f"id-{number}", "identifier": f"SWO-{number}", "number": number, "title": title,
        "status": status, "position": position, "created_at": created_at,
        "assignee_type": "agent" if assignee else None, "assignee_id": assignee,
        "parent_issue_id": parent, "project_id": "project-1",
    }


def _board():
    """A project like the live one: 120 closed issues, then today's open ones."""

    first = datetime(2026, 7, 1, 6, 40, tzinfo=timezone.utc)
    closed = [
        _row(1000 + n, f"[Wrap] {(first + timedelta(days=n)):%Y-%m-%d} 장마감 리포트", status="done",
             position=-454 + n, created_at=f"{(first + timedelta(days=n)):%Y-%m-%dT%H:%M:%SZ}")
        for n in range(120)
    ]
    return closed + [
        _row(2000, DAILY_TITLE, status="todo", position=-28, created_at="2026-11-16T00:00:06Z"),
        _row(2001, RISK_TITLE, status="todo", position=-29, created_at="2026-11-16T00:31:10Z",
             assignee="agent-risk", parent="id-2000"),
        _row(2002, OPS_TITLE, status="todo", position=-30, created_at="2026-11-16T07:00:21Z"),
        _row(1999, "[Wrap] 2026-11-13 ETF 배분·주문 대사 및 장마감 회고", status="in_review",
             position=-29, created_at="2026-11-13T06:40:08Z", assignee="agent-pm"),
    ]


def answer_issue_list(args, board):
    """(rc, stdout, stderr) of one `issue list` call, as multica 0.9.0 gives it."""

    def flag(name, default=None):
        return args[args.index(name) + 1] if name in args else default

    limit = int(flag("--limit", 50))
    if not 1 <= limit <= 100:
        return 1, "", LIMIT_REFUSAL
    rows = [r for r in board if flag("--status") in (None, r["status"])]
    if flag("--sort") == "created_at":
        rows.sort(key=lambda r: r["created_at"], reverse=flag("--direction") == "desc")
    else:
        rows.sort(key=lambda r: r["position"])
    offset = int(flag("--offset", 0))
    page = rows[offset:offset + limit]
    body = {"issues": page, "total": len(rows), "limit": limit, "offset": offset,
            "has_more": offset + len(page) < len(rows)}
    return 0, json.dumps(body, ensure_ascii=False), ""


def _numbers(rows):
    return [r["identifier"] for r in rows]


def test_the_page_nobody_sorted_holds_no_open_issue():
    # The two facts above, as the stand-in gives them. The watcher's lookup
    # used to send exactly the first call; four other sites sent the second.
    rc, out, _ = answer_issue_list(["issue", "list", "--project", "project-1", "--limit", "100"], _board())
    assert rc == 0 and {r["status"] for r in json.loads(out)["issues"]} == {"done"}

    assert answer_issue_list(["issue", "list", "--limit", "200"], _board()) == (1, "", LIMIT_REFUSAL)


class _Restarted(md.MulticaDispatcher):
    """A watcher that has just come up: nothing remembered, the board as it stands."""

    def __init__(self, board):
        super().__init__(project="project-1", binary="/bin/false")
        self.board, self.created = board, []

    async def _run_async(self, args, stdin=None):  # type: ignore[override]
        if args[:2] == ["issue", "list"]:
            return answer_issue_list(args, self.board)
        if args[:2] == ["issue", "create"]:
            self.created.append(args[args.index("--title") + 1])
            return 0, json.dumps({"id": f"new-{len(self.created)}", "assignee_id": None}), ""
        raise AssertionError(f"unexpected multica call {args}")


def test_a_restarted_watcher_finds_the_issue_it_made_this_morning():
    watcher = _Restarted(_board())

    ref = asyncio.run(watcher.ensure_risk_issue(now=NOW))

    assert watcher.created == [], "a second issue with the same title"
    assert (ref.id, ref.parent_id, ref.assigned) == ("id-2001", "id-2000", True)


def test_the_overview_reads_todays_issues_newest_first(monkeypatch):
    def cli(argv, **_kwargs):
        rc, out, err = answer_issue_list(argv[1:], _board())
        return type("Done", (), {"returncode": rc, "stdout": out, "stderr": err})()

    monkeypatch.setattr(agent_overview.subprocess, "run", cli)
    ctx = agent_overview._MulticaContext(binary="multica", project="project-1")

    assert _numbers(agent_overview._fetch_issues_for_date(ctx, TODAY)) == ["SWO-2002", "SWO-2001", "SWO-2000"]


def _digest_cli(monkeypatch, board):
    created = []

    def run(args):
        if args[:2] == ["issue", "list"]:
            return answer_issue_list(args, board)
        if args[:2] == ["issue", "create"]:
            created.append(args[args.index("--title") + 1])
            return 0, json.dumps({"id": "new-1"}), ""
        raise AssertionError(f"unexpected multica call {args}")

    monkeypatch.setattr(digest, "_run", run)
    monkeypatch.setattr(digest, "PROJECT", "project-1")
    monkeypatch.setattr(digest, "_today_kst", lambda: TODAY)
    return created


def test_the_digest_reads_todays_issues(monkeypatch):
    _digest_cli(monkeypatch, _board())

    assert _numbers(digest._today_issues()) == ["SWO-2002", "SWO-2001", "SWO-2000"]


def test_the_digest_does_not_queue_a_second_handoff_issue(monkeypatch):
    # A refused list reads as "none queued today", and the digest files another.
    created = _digest_cli(monkeypatch, _board())

    digest._ensure_ops_issue(TODAY, ["watcher 재시작"], [])

    assert created == []


def test_the_digest_queues_the_handoff_issue_when_there_is_none(monkeypatch):
    board = [r for r in _board() if r["title"] != OPS_TITLE]
    created = _digest_cli(monkeypatch, board)

    digest._ensure_ops_issue(TODAY, ["watcher 재시작"], [])

    assert created == [OPS_TITLE]


def test_the_cleanup_reads_the_issues_waiting_in_review(monkeypatch):
    monkeypatch.setattr(fab, "_run", lambda args: answer_issue_list(args, _board()))
    monkeypatch.setattr(fab, "PROJECT", "project-1")

    assert _numbers(fab._list_by_status("in_review")) == ["SWO-1999"]
