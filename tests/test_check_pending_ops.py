"""Ops-handoff hook tests — the query shape that made an open issue invisible.

The hook is only as good as the page it asks for. multica caps `issue list`
at 100 rows whatever `--limit` says, so any single query is a *window*, not
the workspace. On 2026-08-28 SWO-687 (`[점검 필요]`, todo, created 08-12)
had been outside that window for 16 days and the hook printed nothing.
"""

import importlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "automation"))
hook = importlib.import_module("check_pending_ops")

PENDING = {
    "id": "fa870a69",
    "identifier": "SWO-687",
    "title": "[점검 필요] 2026-08-12 운영 이상",
    "status": "todo",
    "created_at": "2026-08-12T07:00:16Z",
}


def _issue(n, status="done"):
    return {
        "id": f"id-{n}",
        "identifier": f"SWO-{n}",
        "title": f"[Wrap] 2026-08-{n % 28 + 1} 장마감 리포트",
        "status": status,
        "created_at": f"2026-08-{n % 28 + 1:02d}T06:40:16Z",
    }


class _FakeCLI:
    """Stands in for `multica issue list`, capped at 100 rows like the API.

    ``recent`` is the workspace ordered newest-first; the capped page is the
    first 100 of it, which is exactly what pushed the pending issue out.
    """

    def __init__(self, recent, by_status=None):
        self.recent = recent
        self.by_status = by_status or {}
        self.calls = []

    def __call__(self, argv, **kwargs):
        self.calls.append(argv)
        status = None
        if "--status" in argv:
            status = argv[argv.index("--status") + 1]
        rows = self.by_status.get(status, []) if status else self.recent
        return type("R", (), {"stdout": json.dumps({"issues": rows[:100]})})()


def _run(monkeypatch, fake):
    monkeypatch.setattr(hook.subprocess, "run", fake)
    return hook.collect_pending("multica", "proj")


def test_pending_issue_outside_the_capped_page_is_still_found(monkeypatch):
    """The regression: 100 newer issues hide an old open one.

    A recency-sorted query cannot reach it either — sorting is the wrong
    axis when the issue may be arbitrarily old — so the status filter is
    what has to find it.
    """

    fake = _FakeCLI(
        recent=[_issue(n) for n in range(789, 689, -1)],
        by_status={"todo": [PENDING]},
    )
    pending, unknown = _run(monkeypatch, fake)

    assert [it["identifier"] for it in pending] == ["SWO-687"]
    assert unknown == set()


def test_recency_query_alone_would_miss_it(monkeypatch):
    """Guards the reason the status filter exists, not just its result."""

    fake = _FakeCLI(recent=[_issue(n) for n in range(789, 689, -1)])
    pending, _ = _run(monkeypatch, fake)  # no by_status → filters return []

    assert pending == []


def test_every_open_status_is_queried(monkeypatch):
    fake = _FakeCLI(recent=[])
    _run(monkeypatch, fake)

    asked = {
        argv[argv.index("--status") + 1]
        for argv in fake.calls
        if "--status" in argv
    }
    assert asked == set(hook.OPEN_STATUSES)
    assert any("--sort" in argv for argv in fake.calls), "recency probe missing"


def test_issue_found_by_two_queries_is_reported_once(monkeypatch):
    fake = _FakeCLI(recent=[PENDING], by_status={"todo": [PENDING]})
    pending, _ = _run(monkeypatch, fake)

    assert len(pending) == 1


def test_terminal_status_is_not_pending(monkeypatch):
    closed = dict(PENDING, status="done")
    fake = _FakeCLI(recent=[closed], by_status={"todo": [closed]})
    pending, _ = _run(monkeypatch, fake)

    assert pending == []


def test_unenumerated_status_is_reported_as_drift(monkeypatch):
    """`blocked` was live in the workspace and absent from OPEN_STATUSES.

    Without the probe the filtered queries would just come back empty and
    the hook would go silent again — the failure it exists to prevent.
    """

    fake = _FakeCLI(recent=[_issue(700, status="archived_v2")])
    _, unknown = _run(monkeypatch, fake)

    assert unknown == {"archived_v2"}


def test_blocked_is_enumerated():
    """It is a real open status here; an old blocked handoff must surface."""

    assert "blocked" in hook.OPEN_STATUSES


def test_cli_failure_is_silent(monkeypatch):
    """Fail-safe: the hook must never break or slow a session start."""

    def boom(*a, **k):
        raise OSError("multica missing")

    monkeypatch.setattr(hook.subprocess, "run", boom)
    assert hook.collect_pending("multica", "proj") == ([], set())
