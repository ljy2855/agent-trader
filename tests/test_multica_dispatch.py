"""Unit tests for MulticaDispatcher.wait_for_new_action.

These verify the bug-fix landed 2026-05-21: when the first new completed
run lacks an ACTION tag (e.g. agent emitted a thinking/status stub), the
dispatcher must keep polling for either a follow-up run with a VALID
action or a delayed ACTION comment, up to the timeout — instead of
giving up immediately as the previous implementation did.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("KIWOOM_APPKEY", "dummy-appkey")
os.environ.setdefault("KIWOOM_SECRETKEY", "dummy-secretkey")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402

from src.services import multica_dispatch as md  # noqa: E402
from src.services.multica_dispatch import MulticaDispatcher  # noqa: E402


class _StubDispatcher(MulticaDispatcher):
    """Override the two CLI-touching helpers with scripted responses."""

    def __init__(self, runs_seq, comments_seq):
        super().__init__(project="test-project", binary="/bin/false")
        self._runs_seq = list(runs_seq)
        self._comments_seq = list(comments_seq)
        self.run_calls = 0
        self.comment_calls = 0

    async def latest_completed_run(self, issue_id):  # type: ignore[override]
        if self._runs_seq:
            v = self._runs_seq.pop(0)
        else:
            v = None
        self.run_calls += 1
        return v

    async def list_comments(self, issue_id):  # type: ignore[override]
        if self._comments_seq:
            v = self._comments_seq.pop(0)
        else:
            v = []
        self.comment_calls += 1
        return v


def _run(run_id, output, started_at="2026-05-21T00:02:11Z", completed_at="2026-05-21T00:02:21Z"):
    return {
        "id": run_id,
        "status": "completed",
        "started_at": started_at,
        "completed_at": completed_at,
        "result": {"output": output},
    }


def _comment(content, created_at):
    return {"content": content, "created_at": created_at}


def test_first_new_run_with_valid_action_returns_immediately():
    disp = _StubDispatcher(
        runs_seq=[_run("r1", "<!-- ACTION: ACKNOWLEDGE -->")],
        comments_seq=[],
    )
    resp = asyncio.run(
        disp.wait_for_new_action(
            "issue-1", prev_run_id="r0", timeout_seconds=1, poll_seconds=0.01
        )
    )
    assert resp is not None
    assert resp.action == "ACKNOWLEDGE"
    assert resp.run_id == "r1"
    # Should NOT have polled comments — early return on valid action.
    assert disp.comment_calls == 0


def test_first_run_no_tag_then_second_run_valid_returns_valid():
    """NO_TAG stub run followed by a real ACTION run within timeout."""
    disp = _StubDispatcher(
        runs_seq=[
            _run("r1", "Processing regime flip..."),
            _run("r2", "<!-- ACTION: ACKNOWLEDGE -->"),
        ],
        comments_seq=[[], []],
    )
    resp = asyncio.run(
        disp.wait_for_new_action(
            "issue-1", prev_run_id="r0", timeout_seconds=1, poll_seconds=0.01
        )
    )
    assert resp is not None
    assert resp.action == "ACKNOWLEDGE"
    assert resp.run_id == "r2"


def test_first_run_no_tag_then_action_comment_returns_action():
    """5/21 09:02 regime_flip scenario: stub run + delayed ACTION comment."""
    disp = _StubDispatcher(
        runs_seq=[_run("r1", "Processing regime flip...")],
        comments_seq=[
            [],
            [_comment("최종 결정.\n<!-- ACTION: ACKNOWLEDGE -->", "2026-05-21T00:03:02Z")],
        ],
    )
    resp = asyncio.run(
        disp.wait_for_new_action(
            "issue-1", prev_run_id="r0", timeout_seconds=1, poll_seconds=0.01
        )
    )
    assert resp is not None
    assert resp.action == "ACKNOWLEDGE"
    # Run id is the NO_TAG run's id; we surface the comment's content.
    assert resp.run_id == "r1"
    assert "ACKNOWLEDGE" in resp.output


def test_no_tag_run_no_comment_returns_no_tag_at_timeout():
    """Agent never decides — return the NO_TAG ActionResponse, not None."""
    disp = _StubDispatcher(
        runs_seq=[_run("r1", "Still thinking...")],
        comments_seq=[[]] * 50,
    )
    resp = asyncio.run(
        disp.wait_for_new_action(
            "issue-1", prev_run_id="r0", timeout_seconds=0.1, poll_seconds=0.02
        )
    )
    assert resp is not None
    assert resp.action == "NO_TAG"
    assert resp.run_id == "r1"


def test_no_new_run_returns_none():
    """No agent run completes before deadline → None."""
    disp = _StubDispatcher(runs_seq=[], comments_seq=[])
    resp = asyncio.run(
        disp.wait_for_new_action(
            "issue-1", prev_run_id="r0", timeout_seconds=0.1, poll_seconds=0.02
        )
    )
    assert resp is None


def test_trigger_template_xxx_in_comment_is_not_treated_as_valid_action():
    """The watcher's own trigger comment carries `<!-- ACTION: XXX -->` as
    a literal placeholder; the dispatcher must not surface it as a real
    agent decision (XXX is not in VALID_ACTIONS).
    """
    disp = _StubDispatcher(
        runs_seq=[_run("r1", "Stub output, no ACTION")],
        comments_seq=[
            [_comment("**[트리거]** ...\n<!-- ACTION: XXX -->", "2026-05-21T00:02:09Z")],
        ] * 50,
    )
    resp = asyncio.run(
        disp.wait_for_new_action(
            "issue-1", prev_run_id="r0", timeout_seconds=0.1, poll_seconds=0.02
        )
    )
    assert resp is not None
    assert resp.action == "NO_TAG"


# --- peer review gating -----------------------------------------------------
#
# Cross-review used to run on every non-squad ACTION, including HOLD. Those
# no-ops dominate the volume, and confirming one costs a full agent run that
# cannot change the outcome: one held position produced 31 runs on a single
# issue (2026-08-31). Reviews are now spent only where an order follows.


class _PeerSpy(MulticaDispatcher):
    """Captures whether a peer run was attempted, without touching the CLI."""

    def __init__(self):
        self.assignees: list[str] = []
        self.comments: list[str] = []
        self.agent_for = _agent_for_map()
        self.peer_for = md._peer_for()

    async def update_assignee(self, issue_id, assignee):
        self.assignees.append(assignee)
        return True

    async def add_comment(self, issue_id, content):
        self.comments.append(content)
        return True

    async def latest_completed_run(self, issue_id):
        return None

    async def wait_for_new_action(self, issue_id, **kwargs):
        return md.ActionResponse(
            action="HOLD", output="<!-- ACTION: HOLD -->", run_id="r", completed_at=None
        )


def _agent_for_map():
    return md._agent_for()


def _review(action, issue_type="holding"):
    spy = _PeerSpy()
    result = asyncio.run(
        MulticaDispatcher.request_peer_review(
            spy,
            "issue-1",
            issue_type=issue_type,
            trigger_comment="trigger",
            primary_response=md.ActionResponse(
                action=action, output="x", run_id="p", completed_at=None
            ),
            timeout_seconds=1,
            poll_seconds=1,
        )
    )
    return spy, result


@pytest.mark.parametrize("action", sorted(md.CONSEQUENTIAL_ACTIONS & {"TRIM", "TAKE_PROFIT", "CUT_LOSS", "ROTATE"}))
def test_an_action_that_places_an_order_is_reviewed(action):
    spy, result = _review(action)

    assert result is not None
    assert spy.assignees, "the issue must be reassigned to the reviewer"


@pytest.mark.parametrize("action", ["HOLD", "ACKNOWLEDGE", "NO_TAG"])
def test_a_no_op_action_is_not_reviewed(action):
    spy, result = _review(action)

    assert result is None
    assert spy.assignees == [], "no reassignment means no agent run"
    assert spy.comments == []


def test_squad_routed_types_still_skip_the_peer_pass():
    """Squad leaders cross-check by delegating to members."""

    spy, result = _review("TAKE_PROFIT", issue_type="daily")

    assert result is None
    assert spy.assignees == []


def test_reviewer_is_a_different_role_than_the_primary():
    """Independence rests on the role split now that Gemini is gone.

    A reviewer equal to the primary would re-run the same agent on its own
    output: no second opinion, double the cost.
    """

    primary = md._agent_for()
    peer = md._peer_for()

    for issue_type, reviewer in peer.items():
        assert reviewer != primary[issue_type], issue_type
        assert "Gemini" not in reviewer, "the Gemini subscription has lapsed"


# --- issue rollover ---------------------------------------------------------
#
# An agent run reads the thread it answers on, so a day-scoped issue makes
# cost grow with the square of the dispatch count. On 2026-09-02 the 28th run
# re-read the 27 before it — 59 comments, 36,681 characters — and that is
# what exhausted the codex quota, not the number of decisions.


class _RollingSpy(MulticaDispatcher):
    """Tracks created issues and comment counts without touching the CLI."""

    def __init__(self):
        self._issue_cache = {}
        self._comment_counts = {}
        self.created: list[str] = []
        self.titles: dict[str, md.IssueRef] = {}
        self.remote_counts: dict[str, int] = {}
        self.comment_list_fails = False

    async def _find_by_title(self, title):
        return self.titles.get(title)

    async def _create_issue(self, *, title, description, issue_type,
                            parent_id=None, priority="medium"):
        ref = md.IssueRef(id=f"id-{len(self.created)}", title=title,
                          parent_id=parent_id)
        self.created.append(title)
        self.titles[title] = ref
        return ref

    def fill(self, ref, n=md.ISSUE_COMMENT_ROLLOVER):
        self._comment_counts[ref.id] = n
        self.remote_counts[ref.id] = n

    async def _run_async(self, args, stdin=None):
        """Answers `issue comment list` from remote_counts."""
        if args[:3] == ["issue", "comment", "list"]:
            if self.comment_list_fails:
                return 1, "", "boom"
            n = self.remote_counts.get(args[3], 0)
            return 0, json.dumps({"comments": [{"id": i} for i in range(n)]}), ""
        return 0, "{}", ""


def _roll(spy):
    return asyncio.run(
        MulticaDispatcher._ensure_rolling_issue(
            spy, base_title="[PM 코멘트] 2026-09-02 사이클 점검",
            description="d", issue_type="daily", parent_id="parent-1",
        )
    )


def test_an_ordinary_day_stays_on_one_issue():
    spy = _RollingSpy()
    first = _roll(spy)
    spy._comment_counts[first.id] = md.ISSUE_COMMENT_ROLLOVER - 1

    assert _roll(spy).id == first.id
    assert len(spy.created) == 1


def test_a_full_thread_rolls_to_a_new_part():
    spy = _RollingSpy()
    first = _roll(spy)
    spy.fill(first)

    second = _roll(spy)

    assert second.id != first.id
    assert second.title.endswith("(2)")
    assert second.parent_id == "parent-1", "history stays under the same parent"


def test_rollover_repeats_as_a_storm_continues():
    spy = _RollingSpy()
    refs = []
    for _ in range(3):
        ref = _roll(spy)
        refs.append(ref)
        spy.fill(ref)

    assert [r.title[-3:] for r in refs[1:]] == ["(2)", "(3)"]
    assert len({r.id for r in refs}) == 3


def test_a_restart_reads_the_real_count_instead_of_refilling_part_one():
    """A deploy mid-session must not send a full thread back into service.

    Per-process counting alone would reset every tally to zero and re-fill
    the very thread this exists to cap.
    """

    spy = _RollingSpy()
    first = _roll(spy)
    spy.fill(first)
    second = _roll(spy)

    spy._comment_counts.clear()          # the restart
    spy.remote_counts[first.id] = md.ISSUE_COMMENT_ROLLOVER   # ...but the broker knows

    assert _roll(spy).id == second.id, "must land on the newest part with room"


def test_the_agents_own_replies_count_toward_the_cap():
    """Half the thread is the agent answering, and a run re-reads all of it.

    On 2026-09-15 the PM thread held 41 comments — 21 posted by the
    dispatcher, 20 by the agent — while the local tally read 21 and the
    rollover at 24 never fired. Twenty-two runs re-read that thread and the
    codex daily limit was gone from 10:27 to 14:03 KST.

    Every earlier test moved both counters together via `fill`, so the two
    never disagreed and the gap stayed invisible.
    """

    spy = _RollingSpy()
    first = _roll(spy)

    # What this process wrote — on its own, still under the cap.
    spy._comment_counts[first.id] = md.ISSUE_COMMENT_ROLLOVER - 3
    # What the thread actually holds once the agent has answered each one.
    spy.remote_counts[first.id] = (md.ISSUE_COMMENT_ROLLOVER - 3) * 2

    second = _roll(spy)

    assert second.id != first.id, "the cap must measure the whole thread"
    assert second.title.endswith("(2)")


def test_a_bare_list_of_comments_is_counted():
    """The CLI returns `issue comment list` as a top-level array.

    The spy wraps it in {"comments": [...]}; production does not, and a
    parser that only understood the wrapper would silently count 0 and
    never roll over at all.
    """

    spy = _RollingSpy()
    first = _roll(spy)

    async def bare_list(args, stdin=None):
        if args[:3] == ["issue", "comment", "list"]:
            n = md.ISSUE_COMMENT_ROLLOVER
            return 0, json.dumps([{"id": i} for i in range(n)]), ""
        return 0, "{}", ""

    spy._run_async = bare_list
    assert _roll(spy).id != first.id


def test_an_unreadable_comment_count_keeps_the_issue_in_use():
    """Spurious parts lose history; a long thread only costs tokens."""

    spy = _RollingSpy()
    first = _roll(spy)
    spy._comment_counts.clear()
    spy.comment_list_fails = True

    assert _roll(spy).id == first.id


def test_comment_count_only_advances_on_a_successful_post():
    spy = _RollingSpy()

    async def failing(*args, **kwargs):
        return 1, "", "boom"

    spy._run_async = failing
    ok = asyncio.run(MulticaDispatcher.add_comment(spy, "id-0", "x"))

    assert ok is False
    assert spy._comment_counts.get("id-0", 0) == 0
