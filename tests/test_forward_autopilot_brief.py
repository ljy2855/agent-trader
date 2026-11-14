"""Brief/wrap forwarder — the KRX holiday gate and the end-of-day cleanup."""

import importlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "automation"))
fab = importlib.import_module("forward_autopilot_brief")

KST = timezone(timedelta(hours=9))

PRE_OPEN_ARGS = [
    "forward_autopilot_brief",
    "--autopilot=autopilot-1",
    "--title-prefix=[Pre-open]",
    "--required-action=BRIEF_DONE",
    "--discord-title=Pre-Open Brief",
]


def _pin(monkeypatch, *parts):
    """Make the module's clock read the given KST time."""

    class Pinned(datetime):
        @classmethod
        def now(cls, tz=None):
            at = datetime(*parts, tzinfo=KST)
            return at.astimezone(tz) if tz else at

    monkeypatch.setattr(fab, "datetime", Pinned)


def test_closure_comes_from_the_krx_calendar(monkeypatch):
    _pin(monkeypatch, 2026, 10, 5, 8, 50)
    assert fab._krx_closure_today() == "개천절 대체공휴일"
    _pin(monkeypatch, 2026, 10, 6, 8, 50)
    assert fab._krx_closure_today() is None
    # An unverified special session is uncertain, not closed: it may trade.
    _pin(monkeypatch, 2026, 11, 19, 8, 50)
    assert fab._krx_closure_today() is None


def test_holiday_run_neither_forwards_nor_cleans_up(monkeypatch):
    _pin(monkeypatch, 2026, 10, 5, 15, 55)
    calls = []
    monkeypatch.setattr(fab, "_run", lambda args: calls.append(args) or (0, "{}", ""))
    monkeypatch.setattr(fab, "_post_discord", lambda *a, **k: calls.append(("discord", a)))
    monkeypatch.setattr(sys, "argv", [*PRE_OPEN_ARGS, "--close-resolved"])

    assert fab.main() == 0
    assert calls == []


def test_trading_day_still_pages_when_the_brief_is_missing(monkeypatch):
    _pin(monkeypatch, 2026, 10, 6, 8, 50)
    looked, posts = [], []
    monkeypatch.setattr(fab, "_autopilot_today_issue_id", lambda ap: looked.append(ap))
    monkeypatch.setattr(fab, "_list_today_issues", lambda prefix: [])
    monkeypatch.setattr(fab, "_post_discord", lambda title, desc, **k: posts.append(desc))
    monkeypatch.setattr(sys, "argv", PRE_OPEN_ARGS)

    assert fab.main() == 0
    assert looked == ["autopilot-1"]
    assert posts and "찾지 못했습니다" in posts[0]


# --- end-of-day cleanup (--close-resolved) -----------------------------------
# Issues as `multica issue list --output json` returns them (the keys the
# cleanup reads), taken from the 2026-11-05 session. Created-at is UTC.

DAILY_1105 = {
    "id": "daily-1105", "identifier": "SWO-1164", "title": "2026-11-05 장중 실거래",
    "status": "in_review", "created_at": "2026-11-05T00:00:06Z",
    "assignee_type": None, "assignee_id": None, "parent_issue_id": None,
}
PM_1105 = {
    "id": "pm-1105", "identifier": "SWO-1165", "title": "[PM 코멘트] 2026-11-05 사이클 점검",
    "status": "in_review", "created_at": "2026-11-05T00:00:08Z",
    "assignee_type": "squad", "assignee_id": "squad-pm", "parent_issue_id": "daily-1105",
}
HOLDING_1105 = {
    "id": "kb-1105", "identifier": "SWO-1166", "title": "[KB금융] (A105560) 2026-11-05 보유 분석",
    "status": "in_review", "created_at": "2026-11-05T00:00:42Z",
    "assignee_type": "agent", "assignee_id": "agent-evaluator", "parent_issue_id": "daily-1105",
}
# 08:40 KST is the previous evening in UTC: the date must be read in KST.
BRIEF_1105 = {
    "id": "brief-1105", "identifier": "SWO-1163", "title": "[Pre-open] 2026-11-05 실거래 개장 전 브리프",
    "status": "in_review", "created_at": "2026-11-04T23:40:07Z",
    "assignee_type": "agent", "assignee_id": "agent-pm", "parent_issue_id": None,
}
OPS_ALERT = {
    "id": "ops-1105", "identifier": "SWO-1170", "title": "[점검 필요] 2026-11-05 운영 이상",
    "status": "todo", "created_at": "2026-11-05T07:00:21Z",
    "assignee_type": None, "assignee_id": None, "parent_issue_id": None,
}

TRIGGER = "**[09:00:04 KST] [트리거: periodic_review]**\n<!-- ACTION: XXX -->"
VERDICT = "KB금융(105560) HOLD\n\n<!-- ACTION: HOLD -->"


def _cleanup_cli(monkeypatch, *, by_status, comments):
    """Answer the cleanup's multica calls; return the issues it closed."""

    closed, asked = [], []

    def run(args):
        if args[:2] == ["issue", "list"]:
            rows = by_status.get(args[args.index("--status") + 1], [])
            limit = int(args[args.index("--limit") + 1])
            page = {"issues": rows, "total": len(rows), "limit": limit, "offset": 0, "has_more": False}
            return 0, json.dumps(page, ensure_ascii=False), ""
        if args[:3] == ["issue", "comment", "list"]:
            asked.append(args[3])
            rows = [{"content": c, "author_type": "agent"} for c in comments.get(args[3], [])]
            return 0, json.dumps(rows, ensure_ascii=False), ""
        if args[:2] == ["issue", "status"]:
            closed.append((args[2], args[3]))
            return 0, f"Issue {args[2]} status changed to {args[3]}.", ""
        raise AssertionError(f"unexpected multica call {args}")

    monkeypatch.setattr(fab, "_run", run)
    monkeypatch.setattr(fab, "PROJECT", "project-1")
    return closed, asked


def test_cleanup_closes_a_past_days_parent_that_has_no_comments(monkeypatch):
    # Since 11/04 the day's parent is never assigned, so nobody comments on
    # it. The wrap moved SWO-1164 to in_review with zero comments; the
    # ACTION check alone left it there for good.
    _pin(monkeypatch, 2026, 11, 6, 15, 55)
    closed, _asked = _cleanup_cli(
        monkeypatch,
        by_status={"in_review": [DAILY_1105, PM_1105, HOLDING_1105, BRIEF_1105]},
        comments={
            "pm-1105": [TRIGGER, VERDICT],
            "kb-1105": [TRIGGER, VERDICT],
            "brief-1105": ["개장 전 브리프\n<!-- ACTION: BRIEF_DONE -->"],
        },
    )

    assert fab._close_resolved_issues() == 4
    assert sorted(i for i, _ in closed) == ["brief-1105", "daily-1105", "kb-1105", "pm-1105"]
    assert {s for _, s in closed} == {"done"}


def test_cleanup_leaves_todays_parent_and_unanswered_children(monkeypatch):
    _pin(monkeypatch, 2026, 11, 5, 15, 55)
    closed, _asked = _cleanup_cli(
        monkeypatch,
        by_status={"in_review": [DAILY_1105, PM_1105, BRIEF_1105]},
        comments={"pm-1105": [TRIGGER, VERDICT]},
    )
    assert fab._close_resolved_issues() == 0
    assert closed == []

    # A day later the parent goes, but a child whose agent never answered
    # (only the trigger's ACTION: XXX placeholder) stays for a person to see.
    _pin(monkeypatch, 2026, 11, 6, 15, 55)
    closed, _asked = _cleanup_cli(
        monkeypatch,
        by_status={"in_review": [DAILY_1105, HOLDING_1105]},
        comments={"kb-1105": [TRIGGER]},
    )
    assert fab._close_resolved_issues() == 1
    assert closed == [("daily-1105", "done")]


def test_cleanup_closes_a_parent_the_failed_wrap_left_in_todo(monkeypatch):
    # 11/04: the wrap failed on the quota, so nothing moved the parent out of
    # todo. Nothing else in todo is touched — an ops alert waits for a person.
    _pin(monkeypatch, 2026, 11, 6, 15, 55)
    in_todo = {**DAILY_1105, "status": "todo"}
    closed, asked = _cleanup_cli(
        monkeypatch,
        by_status={"in_review": [], "todo": [in_todo, OPS_ALERT]},
        comments={"ops-1105": ["<!-- ACTION: ACKNOWLEDGE -->"]},
    )

    assert fab._close_resolved_issues() == 1
    assert closed == [("daily-1105", "done")]
    assert asked == []


def test_only_an_unassigned_dated_title_is_the_days_container():
    assert fab._is_daily_container(DAILY_1105)
    # Before 11/04 the parent was assigned to the PM squad; that one answered
    # with ACTION comments and goes through the ordinary check.
    assert not fab._is_daily_container({**DAILY_1105, "assignee_type": "squad", "assignee_id": "squad-pm"})
    assert not fab._is_daily_container(OPS_ALERT)
    assert not fab._is_daily_container({**DAILY_1105, "title": "2026-11-05 장중 실거래 메모"})
