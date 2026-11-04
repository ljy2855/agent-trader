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


# --- squad verdicts ---------------------------------------------------------
#
# On a squad issue the leader can pull a member into the thread by mention,
# and both answer there. `wait_for_new_action` took the first valid tag from
# anyone, so which verdict became an order was a race: on 2026-10-27 the
# evaluator's REJECT on 한국전력 beat the screener's by 14 seconds, and on NAVER
# the screener's provisional TIER2 — posted while the evaluator it had asked
# was still working — was bought, and its REJECT two minutes later was never
# read (SWO-1105). The fixtures below are shaped like those threads: the keys
# are the ones `multica issue runs` / `issue comment list` actually return.

from datetime import datetime, timezone  # noqa: E402

SCREENER, EVALUATOR, MEMBER = "agent-screener", "agent-evaluator", "member-1"


class _SquadStub(MulticaDispatcher):
    """Scripted `list_runs` / `list_comments`, one entry per poll.

    ``assignee`` is the agent the issue is assigned to; None means a squad.
    """

    def __init__(self, polls, assignee=None):
        super().__init__(project="test-project", binary="/bin/false")
        self._polls = list(polls)
        self._current = ([], [])
        self._assignee = assignee

    async def _agent_assignee(self, issue_id):  # type: ignore[override]
        return True, self._assignee

    async def list_runs(self, issue_id):  # type: ignore[override]
        if self._polls:
            self._current = self._polls.pop(0)
        runs, _ = self._current
        return None if runs is None else list(runs)

    async def list_comments(self, issue_id):  # type: ignore[override]
        return list(self._current[1])


def _squad_run(run_id, agent, *, status="completed", completed_at=None, output="", leader=None):
    run = {
        "id": run_id,
        "agent_id": agent,
        "status": status,
        "completed_at": completed_at,
        "result": {"output": output} if status == "completed" else None,
    }
    # Multica sets the flag on the assignee's runs and leaves it out otherwise.
    if leader if leader is not None else agent == SCREENER:
        run["is_leader_task"] = True
    return run


def _squad_comment(author, created_at, content, source=None):
    comment = {
        "author_type": "agent" if author != MEMBER else "member",
        "author_id": author,
        "content": content,
        "created_at": created_at,
    }
    if source:
        comment["source_task_id"] = source
    return comment


# 2026-10-27 15:18:49 KST (06:18:49Z) NAVER new_candidate, less the slack.
SINCE = datetime(2026, 10, 27, 6, 18, 19, tzinfo=timezone.utc)
TRIGGER = _squad_comment(MEMBER, "2026-10-27T06:18:53Z", "트리거\n<!-- ACTION: XXX -->")
MENTION = _squad_comment(SCREENER, "2026-10-27T06:19:32Z", "[@투자 평가사] 추세 검증", "A")
PROVISIONAL = _squad_comment(SCREENER, "2026-10-27T06:19:59Z", "TIER2 판정\n<!-- ACTION: TIER2 -->", "B")
ADVICE = _squad_comment(EVALUATOR, "2026-10-27T06:21:47Z", "REJECT\n<!-- ACTION: REJECT -->", "E")
CORRECTION = _squad_comment(SCREENER, "2026-10-27T06:22:04Z", "REJECT로 정정\n<!-- ACTION: REJECT -->", "C")
RUN_A = _squad_run("A", SCREENER, completed_at="2026-10-27T06:19:37Z", output="평가사에게 위임했습니다.")

NAVER_POLLS = [
    # 15:20:00 — the provisional TIER2 is up, B and the evaluator still running.
    # The old wait returned here, and the watcher bought.
    (
        [RUN_A, _squad_run("B", SCREENER, status="running"), _squad_run("E", EVALUATOR, status="running")],
        [TRIGGER, MENTION, PROVISIONAL],
    ),
    # 15:20:10 — B done; the evaluator is still checking the trend.
    (
        [
            RUN_A,
            _squad_run("B", SCREENER, completed_at="2026-10-27T06:20:06Z", output="TIER2로 판정했습니다."),
            _squad_run("E", EVALUATOR, status="running"),
        ],
        [TRIGGER, MENTION, PROVISIONAL],
    ),
    # 15:22:10 — the evaluator rejected, the screener corrected, both done.
    (
        [
            RUN_A,
            _squad_run("B", SCREENER, completed_at="2026-10-27T06:20:06Z", output="TIER2로 판정했습니다."),
            _squad_run("E", EVALUATOR, completed_at="2026-10-27T06:21:53Z", output="REJECT를 게시했습니다."),
            _squad_run("C", SCREENER, completed_at="2026-10-27T06:22:09Z", output="REJECT로 정정했습니다."),
        ],
        [TRIGGER, MENTION, PROVISIONAL, ADVICE, CORRECTION],
    ),
]


def _wait(stub, timeout=1.0, since=SINCE):
    return asyncio.run(
        stub.wait_for_squad_verdict(
            "issue-1", since=since, timeout_seconds=timeout, poll_seconds=0.01
        )
    )


def test_squad_verdict_waits_for_the_thread_to_settle():
    """NAVER replayed: the screener's correction is the verdict, not its TIER2."""

    resp = _wait(_SquadStub(NAVER_POLLS))

    assert resp is not None
    assert resp.action == "REJECT"
    assert resp.run_id == "C"
    assert resp.completed_at == datetime(2026, 10, 27, 6, 22, 4, tzinfo=timezone.utc)


def test_a_members_tag_never_stands_in_for_the_leaders():
    """한국전력 replayed, with the screener disagreeing for contrast."""

    approval = _squad_comment(SCREENER, "2026-10-27T06:00:14Z", "<!-- ACTION: TIER1 -->", "C")
    advice = _squad_comment(EVALUATOR, "2026-10-27T06:00:00Z", "<!-- ACTION: REJECT -->", "E")
    evaluator_done = _squad_run("E", EVALUATOR, completed_at="2026-10-27T06:00:05Z")
    polls = [
        ([evaluator_done, _squad_run("C", SCREENER, status="running")], [advice]),
        ([evaluator_done, _squad_run("C", SCREENER, completed_at="2026-10-27T06:00:20Z")], [advice, approval]),
    ]

    # 15:56:58 KST new_candidate, less the slack.
    resp = _wait(_SquadStub(polls), since=datetime(2026, 10, 27, 5, 56, 28, tzinfo=timezone.utc))

    assert resp is not None
    assert (resp.action, resp.run_id) == ("TIER1", "C")


def test_an_unsettled_thread_yields_the_leaders_newest_verdict_at_the_deadline():
    polls = [([RUN_A, _squad_run("E", EVALUATOR, status="running")], [MENTION, PROVISIONAL])]

    resp = _wait(_SquadStub(polls), timeout=0.05)

    assert resp is not None
    assert resp.action == "TIER2"


def test_a_leader_run_without_a_tag_is_no_tag_even_if_a_member_answered():
    polls = [
        (
            [RUN_A, _squad_run("E", EVALUATOR, completed_at="2026-10-27T06:21:53Z")],
            [TRIGGER, MENTION, ADVICE],
        )
    ]

    resp = _wait(_SquadStub(polls), timeout=0.05)

    assert resp is not None
    assert (resp.action, resp.run_id) == ("NO_TAG", "A")


def test_no_leader_run_and_no_readable_runs_return_none():
    assert _wait(_SquadStub([([_squad_run("A", SCREENER, status="running")], [])]), timeout=0.05) is None
    assert _wait(_SquadStub([(None, [])]), timeout=0.05) is None


def test_squad_thread_attributes_tags_and_skips_what_came_before():
    stale = _squad_comment(SCREENER, "2026-10-27T06:10:00Z", "<!-- ACTION: TIER1 -->", "OLD")
    # A leader comment without `source_task_id` is attributed by its author.
    unsourced = _squad_comment(SCREENER, "2026-10-27T06:23:00Z", "<!-- ACTION: REJECT -->")
    # A tag only in a run's output counts — once, even if a comment repeats it.
    run_only = _squad_run("D", EVALUATOR, completed_at="2026-10-27T06:24:00Z", output="<!-- ACTION: HOLD -->")
    both = _squad_run("C", SCREENER, completed_at="2026-10-27T06:22:09Z", output="<!-- ACTION: REJECT -->")
    stub = _SquadStub([([RUN_A, both, run_only], [TRIGGER, stale, MENTION, CORRECTION, unsourced])])

    thread = asyncio.run(stub.read_squad_thread("issue-1", since=SINCE))

    assert thread is not None
    assert [(v.action, v.leader, v.run_id) for v in thread.verdicts] == [
        ("REJECT", True, "C"),
        ("REJECT", True, None),
        ("HOLD", False, "D"),
    ]
    assert thread.final_leader().action == "REJECT"
    assert thread.active_runs == 0


# -- a dispatch whose runs all fail ------------------------------------------
#
# 2026-11-04 14:14 KST, SK하이닉스 new_candidate: the codex quota was spent,
# so the assignment run and the trigger comment's run both failed within
# seconds — and the wait sat out its 300s for a verdict that could not come.

QUOTA_ERROR = (
    "You’ve hit your usage limit. Upgrade to Pro (https://chatgpt.com/explore/pro), "
    "visit https://chatgpt.com/settings/usage to purchase more credits or try again at 3:40 PM."
)
REFUSED_SINCE = datetime(2026, 11, 4, 6, 13, 38, tzinfo=timezone.utc)


def _failed_run(run_id, created_at, completed_at, agent=SCREENER):
    """A run as `multica issue runs` reports a provider refusal."""

    run = _squad_run(run_id, agent, status="failed", completed_at=completed_at)
    run.update(
        created_at=created_at,
        started_at=created_at,
        error=QUOTA_ERROR,
        failure_reason="agent_error.provider_quota_limit",
    )
    return run


ASSIGNED = _failed_run("A", "2026-11-04T06:14:10Z", "2026-11-04T06:14:17Z")
COMMENTED = _failed_run("B", "2026-11-04T06:14:12Z", "2026-11-04T06:14:21Z")
REFUSED_TRIGGER = _squad_comment(MEMBER, "2026-11-04T06:14:12Z", "트리거\n<!-- ACTION: XXX -->")


def test_the_squad_wait_gives_up_once_every_run_failed():
    stub = _SquadStub([([ASSIGNED, COMMENTED], [REFUSED_TRIGGER])] * 2)

    resp = _wait(stub, timeout=60.0, since=REFUSED_SINCE)

    assert resp is not None
    assert resp.action == md.RUN_FAILED
    assert resp.failure_reason == md.QUOTA_FAILURE_REASON
    assert resp.output == QUOTA_ERROR
    assert resp.run_id == "B"


def test_one_failed_run_does_not_end_the_wait_while_another_works():
    working = _squad_run("B", SCREENER, status="running")
    working["created_at"] = "2026-11-04T06:14:12Z"
    done = _squad_run("B", SCREENER, completed_at="2026-11-04T06:15:02Z", output="REJECT 게시")
    done["created_at"] = "2026-11-04T06:14:12Z"
    verdict = _squad_comment(SCREENER, "2026-11-04T06:15:00Z", "<!-- ACTION: REJECT -->", "B")
    stub = _SquadStub(
        [
            ([ASSIGNED, working], [REFUSED_TRIGGER]),
            ([ASSIGNED, working], [REFUSED_TRIGGER]),
            ([ASSIGNED, done], [REFUSED_TRIGGER, verdict]),
        ]
    )

    resp = _wait(stub, timeout=60.0, since=REFUSED_SINCE)

    assert resp is not None and resp.action == "REJECT"


def test_a_failure_from_before_the_trigger_is_not_this_dispatchs():
    earlier = _failed_run("Z", "2026-11-04T06:09:10Z", "2026-11-04T06:09:14Z")
    stub = _SquadStub([([earlier], [])])

    assert _wait(stub, timeout=0.05, since=REFUSED_SINCE) is None


class _RunsStub(_StubDispatcher):
    """`wait_for_new_action` stub that also answers `list_runs`."""

    def __init__(self, runs):
        super().__init__(runs_seq=[], comments_seq=[])
        self._runs = runs

    async def list_runs(self, issue_id):  # type: ignore[override]
        return list(self._runs)


def test_the_action_wait_gives_up_on_failed_runs_when_told_when_it_asked():
    """KB금융 holding_swing, 11/04 — same refusal on an evaluator issue."""

    runs = [
        _failed_run("A", "2026-11-04T05:07:45Z", "2026-11-04T05:07:51Z", agent=EVALUATOR),
        _failed_run("B", "2026-11-04T05:07:47Z", "2026-11-04T05:07:54Z", agent=EVALUATOR),
    ]
    since = datetime(2026, 11, 4, 5, 7, 12, tzinfo=timezone.utc)

    resp = asyncio.run(
        _RunsStub(runs).wait_for_new_action(
            "issue-1", prev_run_id=None, timeout_seconds=60, poll_seconds=0.01, since=since
        )
    )
    assert resp is not None and resp.action == md.RUN_FAILED and resp.run_id == "B"

    # Without `since` the wait cannot tell its runs from older ones, and
    # keeps the old contract: nothing finished, so None at the deadline.
    resp = asyncio.run(
        _RunsStub(runs).wait_for_new_action(
            "issue-1", prev_run_id=None, timeout_seconds=0.05, poll_seconds=0.01
        )
    )
    assert resp is None


# -- one run per trigger ---------------------------------------------------------
#
# An issue created assigned started a run at once, and the trigger comment a
# second later started another. Multica runs one agent's tasks on an issue in
# turn, so the second waited for the first and mostly wrote "already handled"
# (33 runs from 2026-10-13 to 11-04). Created unassigned, then assigned after
# the comment, an issue gets one run that has the trigger to read — checked
# against the live server on 11/04 (SWO-1160 agent, SWO-1161 squad).

DAY = datetime(2026, 11, 5, 9, 0, tzinfo=timezone.utc)


class _CliSpy(MulticaDispatcher):
    """Records every CLI call and answers the way the server does."""

    def __init__(self, listed=(), refuse_update=0):
        super().__init__(project="test-project", binary="/bin/false")
        self.calls = []
        self.listed = list(listed)
        self.created = 0
        self.refuse_update = refuse_update

    async def _run_async(self, args, stdin=None):  # type: ignore[override]
        self.calls.append(list(args))
        if args[:2] == ["issue", "list"]:
            return 0, json.dumps({"issues": self.listed}), ""
        if args[:2] == ["issue", "create"]:
            self.created += 1
            return 0, json.dumps({"id": f"new-{self.created}", "assignee_id": None}), ""
        if args[:2] == ["issue", "update"] and self.refuse_update:
            self.refuse_update -= 1
            return 1, "", "boom"
        if args[:3] == ["issue", "comment", "list"]:
            return 0, json.dumps({"comments": []}), ""
        return 0, "{}", ""

    def assignments(self):
        return [(c[2], c[c.index("--assignee") + 1]) for c in self.calls if c[:2] == ["issue", "update"]]


def _listed(issue_id, title, assignee=None):
    """An `issue list` row with the keys the server sends."""

    return {"id": issue_id, "title": title, "status": "todo", "parent_issue_id": None,
            "assignee_type": "agent" if assignee else None, "assignee_id": assignee}


def test_a_new_issue_is_assigned_only_after_its_trigger_comment():
    spy = _CliSpy()

    async def dispatch():
        ref = await spy.ensure_candidate_issue(code="105560", name="KB금융", now=DAY)
        assert spy.assignments() == [], "creating it must not start a run"
        await spy.add_comment(ref.id, "트리거")
        assert await spy.assign_pending(ref.id)
        assert await spy.assign_pending(ref.id), "nothing left to assign"
        again = await spy.ensure_candidate_issue(code="105560", name="KB금융", now=DAY)
        assert await spy.assign_pending(again.id)
        return ref

    ref = asyncio.run(dispatch())

    creates = [c for c in spy.calls if c[:2] == ["issue", "create"]]
    assert len(creates) == 2 and all("--assignee" not in c for c in creates)
    assert spy.assignments() == [(ref.id, "후보 스크리너 스쿼드 (실거래)")]
    order = [c[:3] for c in spy.calls if c[:2] in (["issue", "comment"], ["issue", "update"])]
    assert order == [["issue", "comment", "add"], ["issue", "update", ref.id]]


def test_the_daily_parent_is_never_assigned():
    spy = _CliSpy()

    async def dispatch():
        parent = await spy.ensure_daily_issue(now=DAY)
        assert await spy.assign_pending(parent.id)
        return parent

    asyncio.run(dispatch())

    assert spy.assignments() == []


def test_an_unassigned_issue_found_after_a_restart_is_assigned_after_its_comment():
    title = "[KB금융] (A105560) 2026-11-05 보유 분석"
    spy = _CliSpy(listed=[_listed("parent", "2026-11-05 장중 실거래"), _listed("kb", title)])

    async def dispatch():
        ref = await spy.ensure_holding_issue(code="A105560", name="KB금융", now=DAY)
        assert ref.id == "kb"
        await spy.add_comment(ref.id, "트리거")
        assert await spy.assign_pending(ref.id)

    asyncio.run(dispatch())

    assert spy.assignments() == [("kb", "투자 평가사 (실거래)")]


def test_an_assigned_issue_found_after_a_restart_is_left_alone():
    title = "[KB금융] (A105560) 2026-11-05 보유 분석"
    spy = _CliSpy(listed=[_listed("parent", "2026-11-05 장중 실거래"), _listed("kb", title, assignee="agent-evaluator")])

    async def dispatch():
        ref = await spy.ensure_holding_issue(code="A105560", name="KB금융", now=DAY)
        await spy.add_comment(ref.id, "트리거")
        assert await spy.assign_pending(ref.id)

    asyncio.run(dispatch())

    assert spy.assignments() == [], "a second assignment would start a second run"


def test_a_refused_assignment_stays_due_for_the_next_trigger():
    spy = _CliSpy(refuse_update=1)

    async def dispatch():
        ref = await spy.ensure_candidate_issue(code="105560", name="KB금융", now=DAY)
        assert not await spy.assign_pending(ref.id)
        assert await spy.assign_pending(ref.id)
        return ref

    ref = asyncio.run(dispatch())

    assert spy.assignments() == [(ref.id, "후보 스크리너 스쿼드 (실거래)")] * 2


# -- the assignee's final verdict on an issue assigned to one agent --------------
#
# 2026-10-30 10:10 KST NAVER holding_swing (SWO-1125): the evaluator said HOLD,
# re-read the quote a minute later, saw the 20-day low break and posted
# CUT_LOSS. The watcher had taken the HOLD. Holding issues are assigned to the
# evaluator directly, so Multica marks none of its runs `is_leader_task`.

RISK = "agent-risk"
HOLD_SINCE = datetime(2026, 10, 30, 1, 9, 49, tzinfo=timezone.utc)
HOLD_TRIGGER = _squad_comment(MEMBER, "2026-10-30T01:10:25Z", "트리거\n<!-- ACTION: XXX -->")
FIRST_HOLD = _squad_comment(EVALUATOR, "2026-10-30T01:11:38Z", "NAVER: HOLD\n<!-- ACTION: HOLD -->", "A")
LATER_CUT = _squad_comment(EVALUATOR, "2026-10-30T01:12:20Z", "NAVER: CUT_LOSS로 변경\n<!-- ACTION: CUT_LOSS -->", "B")
HOLD_RUN_A = _squad_run("A", EVALUATOR, completed_at="2026-10-30T01:11:45Z", output="HOLD를 남겼습니다.")


def test_on_an_agent_issue_the_assignees_newest_verdict_is_taken_once_settled():
    stub = _SquadStub(
        [
            ([HOLD_RUN_A, _squad_run("B", EVALUATOR, status="running")], [HOLD_TRIGGER, FIRST_HOLD]),
            (
                [HOLD_RUN_A, _squad_run("B", EVALUATOR, completed_at="2026-10-30T01:12:26Z", output="CUT_LOSS")],
                [HOLD_TRIGGER, FIRST_HOLD, LATER_CUT],
            ),
        ],
        assignee=EVALUATOR,
    )

    resp = _wait(stub, timeout=60.0, since=HOLD_SINCE)

    assert resp is not None and resp.action == "CUT_LOSS" and resp.run_id == "B"


def test_on_an_agent_issue_a_reviewers_tag_is_not_the_verdict():
    review = _squad_comment(RISK, "2026-10-30T01:12:40Z", "반대\n<!-- ACTION: CUT_LOSS -->", "R")
    stub = _SquadStub(
        [([HOLD_RUN_A, _squad_run("R", RISK, completed_at="2026-10-30T01:12:44Z")], [HOLD_TRIGGER, FIRST_HOLD, review])],
        assignee=EVALUATOR,
    )

    resp = _wait(stub, timeout=60.0, since=HOLD_SINCE)

    assert resp is not None and resp.action == "HOLD" and resp.run_id == "A"
